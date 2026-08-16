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


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# =========================================================
# Session
# =========================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/151.0 Safari/537.36",

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
):

    last_error = None

    # -----------------------------------------------------
    # 正常 SSL
    # -----------------------------------------------------

    for attempt in range(
        1,
        retries + 1
    ):

        try:

            print(
                f"API请求 {attempt}/{retries}: {url}"
            )

            response = SESSION.get(
                url,
                timeout=timeout,
                verify=SSL_VERIFY,
                allow_redirects=True,
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):

                raise ValueError(
                    "API返回不是JSON对象"
                )

            return data

        except requests.exceptions.SSLError as e:

            last_error = e

            print(
                "SSL错误：",
                e
            )

            break

        except Exception as e:

            last_error = e

            print(
                "请求失败：",
                e
            )

            if attempt < retries:

                time.sleep(
                    RETRY_SLEEP
                )

    # -----------------------------------------------------
    # SSL fallback
    # -----------------------------------------------------

    if ALLOW_SSL_FALLBACK:

        print(
            "⚠️ 启用 SSL fallback"
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
                    "fallback失败：",
                    e
                )

                if attempt < retries:

                    time.sleep(
                        RETRY_SLEEP
                    )

    raise RuntimeError(
        f"API最终失败：{url} | {last_error}"
    )


# =========================================================
# 清洗文本
# =========================================================

def clean_text(
    value: Any
) -> Optional[str]:

    if value is None:
        return None

    text = str(value).strip()

    return text if text else None


# =========================================================
# 号码
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

        return [
            str(x).strip().zfill(2)
            for x in numbers
            if str(x).strip()
        ]

    text = str(numbers).strip()

    if not text:
        return []

    for separator in (
        "，",
        "|",
        "/",
        " ",
        ";",
    ):

        text = text.replace(
            separator,
            ","
        )

    return [
        x.strip().zfill(2)
        for x in text.split(",")
        if x.strip()
    ]


def numbers_to_string(
    numbers: Any
) -> str:

    return ",".join(
        normalize_numbers(numbers)
    )


# =========================================================
# 历史行
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
        .replace("期", "")
        .strip()
    )

    numbers = normalize_numbers(
        parts[1]
    )

    if not issue:
        return None

    if len(numbers) != 7:
        return None

    return {
        "issue": issue,
        "numbers": ",".join(numbers),
    }


# =========================================================
# 历史 API
# =========================================================

def fetch_history_api():

    print()
    print("=" * 70)
    print("获取历史数据")
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
            "lottery_data不是list"
        )

    return lottery_data


# =========================================================
# 彩种识别
# =========================================================

def resolve_lottery_code(
    item: Dict[str, Any]
):

    code = clean_text(
        item.get("code")
    )

    if code in LOTTERIES:
        return code

    name = clean_text(
        item.get("name")
    )

    mapping = {

        "香港彩": "hk",

        "香港六合彩": "hk",

        "新澳门彩": "newMacau",

        "新澳门六合彩": "newMacau",

        "老澳门彩": "oldMacau",

        "老澳门六合彩": "oldMacau",
    }

    return mapping.get(name)


# =========================================================
# 历史同步
# =========================================================

def sync_history() -> int:

    lottery_data = fetch_history_api()

    total = 0

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

            continue

        name = LOTTERIES[
            lottery
        ]["name"]

        history = item.get(
            "history",
            []
        )

        if not isinstance(
            history,
            list
        ):
            continue

        history = history[
            :MAX_HISTORY
        ]

        print(
            f"{name}：API返回 {len(history)} 期"
        )

        for row in history:

            parsed = parse_history_row(
                row
            )

            if parsed is None:
                continue

            if insert_draw(
                lottery=lottery,
                name=name,
                issue=parsed["issue"],
                numbers=parsed["numbers"],
                source="history_api",
            ):

                total += 1

        print(
            f"{name}：数据库 {count_draws(lottery)} 期"
        )

    return total


# =========================================================
# 实时
# =========================================================

def fetch_realtime(
    lottery: str
):

    config = API_SOURCES.get(
        lottery
    )

    if not config:

        raise ValueError(
            f"未知彩种：{lottery}"
        )

    return request_json(
        config["url"],
        timeout=REQUEST_TIMEOUT,
        retries=REQUEST_RETRIES,
    )


def sync_realtime(
    lottery: str
) -> int:

    config = API_SOURCES[
        lottery
    ]

    data = fetch_realtime(
        lottery
    )

    issue = clean_text(
        data.get("expect")
        or data.get("issue")
        or data.get("expectNum")
    )

    open_time = clean_text(
        data.get("openTime")
        or data.get("open_time")
    )

    numbers = numbers_to_string(
        data.get("numbers")
        or data.get("openCode")
        or data.get("open_code")
    )

    zodiac = clean_text(
        data.get("zodiac")
    )

    wave = clean_text(
        data.get(
            config["wave_field"]
        )
        or data.get("wave")
        or data.get("waveColors")
    )

    print(
        f"{config['name']}："
        f"期号={issue}"
    )

    print(
        f"号码={numbers}"
    )

    if not issue:
        return 0

    upsert_draw(
        lottery=lottery,
        name=config["name"],
        issue=issue,
        numbers=numbers,
        open_time=open_time,
        zodiac=zodiac,
        wave=wave,
        source="realtime_api",
    )

    return 1


# =========================================================
# 全部
# =========================================================

def update_all() -> int:

    init_database()

    print()
    print("=" * 70)
    print("开始同步数据")
    print("=" * 70)

    total = 0

    # -----------------------------------------------------
    # 历史
    # -----------------------------------------------------

    try:

        total += sync_history()

    except Exception as e:

        print(
            "⚠️ 历史同步失败：",
            repr(e)
        )

    # -----------------------------------------------------
    # 实时
    # -----------------------------------------------------

    success = 0

    for lottery in API_SOURCES:

        try:

            success += sync_realtime(
                lottery
            )

        except Exception as e:

            print(
                f"⚠️ {lottery}实时同步失败：",
                repr(e)
            )

    # -----------------------------------------------------
    # 状态
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("同步完成")
    print("=" * 70)

    for lottery, config in API_SOURCES.items():

        print(
            config["name"],
            count_draws(lottery),
            "期"
        )

    print(
        f"历史新增：{total}"
    )

    print(
        f"实时成功：{success}/{len(API_SOURCES)}"
    )

    return total


if __name__ == "__main__":

    update_all()