# -*- coding: utf-8 -*-

import time
import requests
import urllib3

from requests.exceptions import (
    SSLError,
    RequestException,
)

from .config import (
    API_SOURCES,
    REQUEST_TIMEOUT,
    REQUEST_RETRIES,
    RETRY_SLEEP,
    SSL_VERIFY,
    ALLOW_SSL_FALLBACK,
)

from .database import (
    insert_draw,
    insert_fetch_log,
)


# =========================================================
# SSL Warning
# =========================================================

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# =========================================================
# Session
# =========================================================

SESSION = requests.Session()

SESSION.headers.update({

    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131 Safari/537.36",

    "Accept":
        "application/json,text/plain,*/*",

    "Connection":
        "close",
})


# =========================================================
# 数字解析
# =========================================================

def normalize_number(value):

    try:

        value = str(value).strip()

        value = (
            value
            .replace("号", "")
            .replace(" ", "")
            .replace("　", "")
        )

        return int(value)

    except Exception:

        return None


# =========================================================
# 解析号码
# =========================================================

def parse_numbers(payload):

    if not isinstance(payload, dict):
        return []


    # -----------------------------------------------------
    # numbers
    # -----------------------------------------------------

    numbers = payload.get("numbers")

    if isinstance(numbers, list):

        result = []

        for value in numbers:

            number = normalize_number(value)

            if number is not None:
                result.append(number)

        if len(result) == 7:
            return result


    # -----------------------------------------------------
    # openCode
    # -----------------------------------------------------

    open_code = payload.get("openCode")

    if isinstance(open_code, str):

        parts = (
            open_code
            .replace("|", ",")
            .replace("/", ",")
            .replace(" ", ",")
            .replace("，", ",")
            .split(",")
        )

        result = []

        for value in parts:

            number = normalize_number(value)

            if number is not None:
                result.append(number)

        if len(result) == 7:
            return result


    return []


# =========================================================
# 解析波色
# =========================================================

def parse_wave(payload):

    if not isinstance(payload, dict):
        return None

    if "wave" in payload:
        return payload.get("wave")

    if "waveColors" in payload:
        return payload.get("waveColors")

    return None


# =========================================================
# 查找历史数组
# =========================================================

def extract_history(payload):

    """
    尽可能兼容不同 API 的 history 返回结构。

    支持：

    payload["history"]

    payload["lottery_data"]["history"]

    payload["data"]["history"]

    payload["result"]["history"]

    以及 history 本身直接就是 list。
    """

    if not isinstance(payload, dict):
        return []


    # -----------------------------------------------------
    # 第一层
    # -----------------------------------------------------

    history = payload.get("history")

    if isinstance(history, list):
        return history


    if isinstance(history, dict):

        for key in (
            "data",
            "list",
            "records",
            "items",
            "history",
        ):

            value = history.get(key)

            if isinstance(value, list):
                return value


    # -----------------------------------------------------
    # 第二层容器
    # -----------------------------------------------------

    for parent_key in (
        "lottery_data",
        "data",
        "result",
    ):

        parent = payload.get(parent_key)

        if not isinstance(parent, dict):
            continue


        history = parent.get("history")

        if isinstance(history, list):
            return history


        if isinstance(history, dict):

            for key in (
                "data",
                "list",
                "records",
                "items",
                "history",
            ):

                value = history.get(key)

                if isinstance(value, list):
                    return value


    return []


# =========================================================
# 解析开奖
# =========================================================

def parse_draw(
    payload,
    lottery_key,
    source
):

    if not isinstance(payload, dict):
        return None


    # -----------------------------------------------------
    # 期号
    # -----------------------------------------------------

    issue = (
        payload.get("expect")
        or payload.get("issue")
        or payload.get("issueNo")
        or payload.get("issue_no")
    )

    if issue is None:
        return None


    issue = str(issue).strip()


    # -----------------------------------------------------
    # 开奖号码
    # -----------------------------------------------------

    numbers = parse_numbers(payload)

    if len(numbers) != 7:

        return None


    # -----------------------------------------------------
    # 范围
    # -----------------------------------------------------

    if any(
        number < 1 or number > 49
        for number in numbers
    ):

        return None


    # -----------------------------------------------------
    # 不允许重复
    # -----------------------------------------------------

    if len(set(numbers)) != 7:

        return None


    # -----------------------------------------------------
    # 生肖
    # -----------------------------------------------------

    zodiac = (
        payload.get("zodiac")
        or payload.get("zodiacs")
    )


    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    wave = parse_wave(payload)


    # -----------------------------------------------------
    # 开奖时间
    # -----------------------------------------------------

    open_time = (
        payload.get("openTime")
        or payload.get("open_time")
        or payload.get("drawTime")
        or payload.get("draw_time")
    )


    return {

        "lottery":
            lottery_key,

        "issue":
            issue,

        "open_time":
            open_time,

        "numbers":
            numbers,

        "zodiac":
            zodiac,

        "wave":
            wave,

        "source":
            source["url"],
    }


# =========================================================
# 请求 API
# =========================================================

def fetch_api(
    lottery_key,
    source
):

    url = source["url"]

    last_error = None


    # =====================================================
    # 正常 SSL
    # =====================================================

    for attempt in range(
        1,
        REQUEST_RETRIES + 1
    ):

        try:

            print()

            print(
                f"[{lottery_key}] "
                f"请求API "
                f"第{attempt}次"
            )

            print(url)


            response = SESSION.get(

                url,

                timeout=
                    REQUEST_TIMEOUT,

                verify=
                    SSL_VERIFY
            )


            response.raise_for_status()


            payload = response.json()


            if not isinstance(
                payload,
                dict
            ):

                raise ValueError(
                    "API返回不是JSON对象"
                )


            return payload


        except SSLError as e:

            last_error = e

            print(
                "SSL证书错误:",
                e
            )

            break


        except (
            RequestException,
            ValueError
        ) as e:

            last_error = e

            print(
                "API请求失败:",
                e
            )


            if attempt < REQUEST_RETRIES:

                time.sleep(
                    RETRY_SLEEP
                )


    # =====================================================
    # SSL fallback
    # =====================================================

    if (
        isinstance(
            last_error,
            SSLError
        )
        and
        ALLOW_SSL_FALLBACK
    ):

        print()

        print(
            "⚠️ 正常SSL验证失败"
        )

        print(
            "尝试受控SSL fallback..."
        )


        try:

            response = SESSION.get(

                url,

                timeout=
                    REQUEST_TIMEOUT,

                verify=False
            )


            response.raise_for_status()


            payload = response.json()


            if isinstance(
                payload,
                dict
            ):

                print(
                    "✅ SSL fallback成功"
                )

                return payload


        except Exception as e:

            last_error = e

            print(
                "SSL fallback失败:",
                e
            )


    return None


# =========================================================
# 解析历史数据
# =========================================================

def parse_history(
    payload,
    lottery_key,
    source
):

    history = extract_history(payload)

    if not history:

        return []


    draws = []


    for item in history:

        # -------------------------------------------------
        # history 可能是字典
        # -------------------------------------------------

        if isinstance(item, dict):

            draw = parse_draw(
                item,
                lottery_key,
                source
            )

            if draw is not None:

                draws.append(draw)

            continue


        # -------------------------------------------------
        # 某些 API history 可能是字符串
        # -------------------------------------------------

        if isinstance(item, str):

            item = item.strip()

            if not item:
                continue


            # 暂时只接受 JSON 对象字符串

            try:

                import json

                item_payload = json.loads(item)

            except Exception:

                continue


            if isinstance(
                item_payload,
                dict
            ):

                draw = parse_draw(
                    item_payload,
                    lottery_key,
                    source
                )

                if draw is not None:

                    draws.append(draw)


    # -----------------------------------------------------
    # 按期号去重
    # -----------------------------------------------------

    unique = {}

    for draw in draws:

        unique[
            draw["issue"]
        ] = draw


    return list(
        unique.values()
    )


# =========================================================
# 更新一个彩种
# =========================================================

def update_lottery(
    lottery_key
):

    source = API_SOURCES[
        lottery_key
    ]


    print()

    print(
        "=" * 70
    )

    print(
        f"正在更新："
        f"{source['name']}"
    )

    print(
        "=" * 70
    )


    payload = fetch_api(
        lottery_key,
        source
    )


    if payload is None:

        print(
            f"❌ {source['name']} "
            f"API获取失败"
        )

        insert_fetch_log(

            lottery_key,

            False,

            error=
                "API获取失败"
        )

        return False


    # =====================================================
    # 1. 当前开奖
    # =====================================================

    current_draw = parse_draw(

        payload,

        lottery_key,

        source
    )


    # =====================================================
    # 2. 历史开奖
    # =====================================================

    history_draws = parse_history(

        payload,

        lottery_key,

        source
    )


    # =====================================================
    # 合并
    # =====================================================

    all_draws = []


    if current_draw is not None:

        all_draws.append(
            current_draw
        )


    all_draws.extend(
        history_draws
    )


    # -----------------------------------------------------
    # 按期号去重
    # -----------------------------------------------------

    unique_draws = {}

    for draw in all_draws:

        unique_draws[
            draw["issue"]
        ] = draw


    all_draws = list(
        unique_draws.values()
    )


    if not all_draws:

        print(
            f"❌ {source['name']} "
            f"没有解析到任何开奖数据"
        )

        insert_fetch_log(

            lottery_key,

            False,

            error=
                "没有解析到开奖数据"
        )

        return False


    # =====================================================
    # 写入数据库
    # =====================================================

    inserted_count = 0


    for draw in all_draws:

        inserted = insert_draw(
            draw
        )


        if inserted:

            inserted_count += 1


    # =====================================================
    # 输出结果
    # =====================================================

    print()

    print(
        f"解析开奖："
        f"{len(all_draws)} 期"
    )

    print(
        f"本次新增："
        f"{inserted_count} 期"
    )


    # -----------------------------------------------------
    # 当前期显示
    # -----------------------------------------------------

    if current_draw is not None:

        print()

        print(
            f"最新期："
            f"{current_draw['issue']}"
        )

        print(
            "开奖号码：",
            " ".join(
                f"{n:02d}"
                for n in
                current_draw["numbers"]
            )
        )

        print(
            "生肖：",
            current_draw["zodiac"]
        )

        print(
            "波色：",
            current_draw["wave"]
        )


    # =====================================================
    # 抓取日志
    # =====================================================

    insert_fetch_log(

        lottery_key,

        True,

        issue=(
            current_draw["issue"]
            if current_draw
            else None
        ),

        source=
            source["url"]
    )


    return True


# =========================================================
# 更新三个彩种
# =========================================================

def update_all():

    success = 0


    for lottery_key in API_SOURCES:

        try:

            result = update_lottery(
                lottery_key
            )


            if result:

                success += 1


        except Exception as e:

            print(
                f"{lottery_key} "
                f"更新异常：",
                e
            )


            insert_fetch_log(

                lottery_key,

                False,

                error=str(e)
            )


        time.sleep(1)


    print()

    print(
        "=" * 70
    )

    print(
        f"三个数据源更新完成："
        f"{success}/3"
    )

    print(
        "=" * 70
    )


    return success
