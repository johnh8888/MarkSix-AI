# -*- coding: utf-8 -*-

import time
from typing import Any, Dict, List, Optional

import requests
import urllib3

from core.config import (
    API_SOURCES,
    HISTORY_API_URL,
    REQUEST_TIMEOUT,
    HISTORY_TIMEOUT,
    REQUEST_RETRIES,
    RETRY_SLEEP,
    SSL_VERIFY,
    ALLOW_SSL_FALLBACK,
    MAX_HISTORY,
    LOTTERIES,
)

from core.database import (
    init_database,
    insert_draw,
    upsert_draw,
    count_draws,
)


# =========================================================
# SSL 警告关闭
# =========================================================

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# =========================================================
# HTTP Session
# =========================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent":
            (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/151.0 Safari/537.36"
            ),

        "Accept":
            "application/json,text/plain,*/*",
    }
)


# =========================================================
# 请求 JSON
# =========================================================

def request_json(
    url: str,
    timeout: int = REQUEST_TIMEOUT,
    retries: int = REQUEST_RETRIES,
) -> Dict[str, Any]:

    last_error = None


    # =====================================================
    # 第一阶段：正常 SSL
    # =====================================================

    for attempt in range(
        1,
        retries + 1
    ):

        try:

            print(
                f"请求API 第{attempt}次"
            )

            print(
                url
            )


            response = SESSION.get(

                url,

                timeout=timeout,

                verify=SSL_VERIFY,

                allow_redirects=True,
            )


            response.raise_for_status()


            data = response.json()


            if not isinstance(
                data,
                dict
            ):

                raise ValueError(
                    "API返回不是JSON对象"
                )


            return data


        except requests.exceptions.SSLError as e:

            last_error = e

            print(
                "SSL证书错误:",
                e
            )

            break


        except Exception as e:

            last_error = e

            print(
                f"请求失败：{e}"
            )


            if attempt < retries:

                time.sleep(
                    RETRY_SLEEP
                )


    # =====================================================
    # 第二阶段：受控 SSL fallback
    # =====================================================

    if ALLOW_SSL_FALLBACK:

        print(
            "⚠️ 正常SSL验证失败"
        )

        print(
            "尝试受控SSL fallback..."
        )


        for attempt in range(
            1,
            retries + 1
        ):

            try:

                response = SESSION.get(

                    url,

                    timeout=timeout,

                    verify=False,

                    allow_redirects=True,
                )


                response.raise_for_status()


                data = response.json()


                if not isinstance(
                    data,
                    dict
                ):

                    raise ValueError(
                        "API返回不是JSON对象"
                    )


                print(
                    "✅ SSL fallback成功"
                )


                return data


            except Exception as e:

                last_error = e

                print(
                    f"fallback失败：{e}"
                )


                if attempt < retries:

                    time.sleep(
                        RETRY_SLEEP
                    )


    raise RuntimeError(
        f"API请求最终失败：{url} | {last_error}"
    )


# =========================================================
# 清洗号码
# =========================================================

def normalize_numbers(
    numbers: Any
) -> List[str]:

    if numbers is None:

        return []


    if isinstance(
        numbers,
        list
    ):

        result = []

        for number in numbers:

            value = str(
                number
            ).strip()


            if value:

                result.append(
                    value.zfill(2)
                )


        return result


    if isinstance(
        numbers,
        str
    ):

        text = numbers.strip()


        if not text:

            return []


        for separator in (
            ",",
            "，",
            " ",
            "|",
            "/",
        ):

            if separator in text:

                parts = (
                    text
                    .replace(
                        "，",
                        ","
                    )
                    .split(
                        separator
                    )
                )

                return [

                    str(x).strip().zfill(2)

                    for x in parts

                    if str(x).strip()
                ]


        return [
            text.zfill(2)
        ]


    return []


# =========================================================
# 号码字符串
# =========================================================

def numbers_to_string(
    numbers: Any
) -> str:

    normalized = normalize_numbers(
        numbers
    )


    return ",".join(
        normalized
    )


# =========================================================
# 字段转字符串
# =========================================================

def clean_text(
    value: Any
) -> Optional[str]:

    if value is None:

        return None


    text = str(
        value
    ).strip()


    if not text:

        return None


    return text


# =========================================================
# 历史行解析
#
# 例如：
#
# 2026089 期：33,27,16,28,04,25,14
# =========================================================

def parse_history_row(
    row: Any
):

    if not isinstance(
        row,
        str
    ):

        return None


    text = row.strip()


    if not text:

        return None


    # -----------------------------------------------------
    # 处理中文期号
    # -----------------------------------------------------

    if "期：" in text:

        parts = text.split(
            "期：",
            1
        )

    elif "期:" in text:

        parts = text.split(
            "期:",
            1
        )

    else:

        return None


    if len(parts) != 2:

        return None


    issue = (
        parts[0]
        .replace(
            "期",
            ""
        )
        .strip()
    )


    numbers_text = (
        parts[1]
        .strip()
    )


    if not issue:

        return None


    numbers = normalize_numbers(
        numbers_text
    )


    if len(numbers) != 7:

        return None


    return {

        "issue":
            issue,

        "numbers":
            ",".join(numbers),
    }


# =========================================================
# 读取历史 API
# =========================================================

def fetch_history_api():

    print()
    print("=" * 70)

    print(
        "正在获取历史数据"
    )

    print(
        HISTORY_API_URL
    )

    print("=" * 70)


    data = request_json(

        HISTORY_API_URL,

        timeout=HISTORY_TIMEOUT,

        retries=REQUEST_RETRIES,
    )


    lottery_data = data.get(
        "lottery_data",
        []
    )


    if not isinstance(
        lottery_data,
        list
    ):

        raise ValueError(
            "history API 的 lottery_data 不是list"
        )


    print(
        "历史API彩种数量：",
        len(lottery_data)
    )


    return lottery_data


# =========================================================
# 彩种历史代码识别
# =========================================================

def resolve_lottery_code(
    item: Dict[str, Any]
) -> Optional[str]:

    code = clean_text(
        item.get("code")
    )


    if code in LOTTERIES:

        return code


    name = clean_text(
        item.get("name")
    )


    if name == "香港彩":

        return "hk"


    if name == "香港六合彩":

        return "hk"


    if name == "新澳门彩":

        return "newMacau"


    if name == "新澳门六合彩":

        return "newMacau"


    if name == "老澳门彩":

        return "oldMacau"


    if name == "老澳门六合彩":

        return "oldMacau"


    return None


# =========================================================
# 同步历史
# =========================================================

def sync_history() -> int:

    lottery_data = fetch_history_api()


    total_inserted = 0


    for item in lottery_data:

        if not isinstance(
            item,
            dict
        ):

            continue


        lottery = resolve_lottery_code(
            item
        )


        if lottery is None:

            print(
                "⚠️ 无法识别历史彩种：",
                item.get("name"),
                item.get("code")
            )

            continue


        name = (
            LOTTERIES
            .get(
                lottery,
                {}
            )
            .get(
                "name",
                item.get("name")
            )
        )


        history = item.get(
            "history",
            []
        )


        if not isinstance(
            history,
            list
        ):

            continue


        # -------------------------------------------------
        # 限制最大历史
        # -------------------------------------------------

        history = history[
            :MAX_HISTORY
        ]


        print()
        print(
            f"同步历史：{name}"
        )

        print(
            f"API返回：{len(history)}期"
        )


        for row in history:

            parsed = parse_history_row(
                row
            )


            if parsed is None:

                print(
                    "⚠️ 历史数据解析失败：",
                    row
                )

                continue


            inserted = insert_draw(

                lottery=lottery,

                name=name,

                issue=parsed["issue"],

                numbers=parsed["numbers"],

                open_time=None,

                zodiac=None,

                wave=None,

                source="history_api",
            )


            if inserted:

                total_inserted += 1


        print(
            f"{name} "
            f"数据库现有："
            f"{count_draws(lottery)}期"
        )


    return total_inserted


# =========================================================
# 获取实时 API
# =========================================================

def fetch_realtime(
    lottery: str
) -> Dict[str, Any]:

    config = API_SOURCES.get(
        lottery
    )


    if not config:

        raise ValueError(
            f"不存在彩种配置：{lottery}"
        )


    url = config["url"]


    print()
    print("=" * 70)

    print(
        f"正在更新："
        f"{config['name']}"
    )

    print("=" * 70)


    data = request_json(

        url,

        timeout=REQUEST_TIMEOUT,

        retries=REQUEST_RETRIES,
    )


    return data


# =========================================================
# 同步实时数据
# =========================================================

def sync_realtime(
    lottery: str
) -> int:

    data = fetch_realtime(
        lottery
    )


    config = API_SOURCES[
        lottery
    ]


    name = config[
        "name"
    ]


    issue = clean_text(
        data.get("expect")
    )


    open_time = clean_text(
        data.get("openTime")
    )


    numbers = numbers_to_string(
        data.get("numbers")
        or data.get("openCode")
    )


    zodiac = clean_text(
        data.get("zodiac")
    )


    wave_field = config[
        "wave_field"
    ]


    wave = clean_text(
        data.get(
            wave_field
        )
    )


    # -----------------------------------------------------
    # 如果 numbers 没有
    # -----------------------------------------------------

    if not numbers:

        numbers = numbers_to_string(
            data.get(
                "openCode"
            )
        )


    print(
        f"解析开奖："
        f"{1 if issue else 0} 期"
    )


    print(
        "期号：",
        issue
    )


    print(
        "开奖号码：",
        numbers.replace(
            ",",
            " "
        )
    )


    print(
        "生肖：",
        zodiac
    )


    print(
        "波色：",
        wave
    )


    if not issue:

        print(
            "⚠️ API没有返回期号"
        )

        return 0


    # -----------------------------------------------------
    # 更新数据库
    # -----------------------------------------------------

    upsert_draw(

        lottery=lottery,

        name=name,

        issue=issue,

        numbers=numbers,

        open_time=open_time,

        zodiac=zodiac,

        wave=wave,

        source="realtime_api",
    )


    print(
        "数据库现有：",
        count_draws(lottery),
        "期"
    )


    return 1


# =========================================================
# 更新单个彩种
# =========================================================

def update_lottery(
    lottery: str
) -> int:

    # -----------------------------------------------------
    # 先历史
    # -----------------------------------------------------

    # 历史统一在 update_all() 中完成
    # 这里负责实时数据


    return sync_realtime(
        lottery
    )


# =========================================================
# 更新全部数据
# =========================================================

def update_all() -> int:

    print()
    print("=" * 70)

    print(
        "开始同步六合彩数据"
    )

    print("=" * 70)


    # -----------------------------------------------------
    # 初始化数据库
    # -----------------------------------------------------

    init_database()


    total_inserted = 0


    # =====================================================
    # 第一阶段：历史
    # =====================================================

    try:

        total_inserted += sync_history()

    except Exception as e:

        print()
        print(
            "❌ 历史数据同步失败：",
            e
        )


    # =====================================================
    # 第二阶段：实时
    # =====================================================

    realtime_success = 0


    for lottery in API_SOURCES:

        try:

            sync_realtime(
                lottery
            )

            realtime_success += 1


        except Exception as e:

            print()
            print(
                f"❌ {lottery} "
                f"实时数据同步失败："
                f"{e}"
            )


    # =====================================================
    # 最终统计
    # =====================================================

    print()
    print("=" * 70)

    print(
        "数据同步完成"
    )

    print("=" * 70)


    for lottery, config in API_SOURCES.items():

        print(
            f"{config['name']}: "
            f"{count_draws(lottery)}期"
        )


    print()
    print(
        f"实时API成功："
        f"{realtime_success}/"
        f"{len(API_SOURCES)}"
    )


    print(
        f"历史新增："
        f"{total_inserted}"
    )


    print("=" * 70)


    return total_inserted


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    print()
    print(
        "=" * 70
    )

    print(
        "MarkSix 数据源测试"
    )

    print(
        "=" * 70
    )


    try:

        inserted = update_all()


        print()
        print(
            "测试完成"
        )

        print(
            "本次新增：",
            inserted
        )


    except Exception as e:

        print()
        print(
            "❌ 测试失败：",
            e
        )
