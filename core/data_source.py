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

def normalize_number(
    value
):

    try:

        value = str(
            value
        ).strip()

        value = (
            value
            .replace(
                "号",
                ""
            )
            .replace(
                " ",
                ""
            )
            .replace(
                "　",
                ""
            )
        )

        return int(
            value
        )

    except Exception:

        return None


# =========================================================
# 解析号码
# =========================================================

def parse_numbers(
    payload
):

    # -----------------------------------------------------
    # 优先 numbers
    # -----------------------------------------------------

    numbers = payload.get(
        "numbers"
    )


    if isinstance(
        numbers,
        list
    ):

        result = []

        for value in numbers:

            number = normalize_number(
                value
            )

            if number is not None:

                result.append(
                    number
                )

        if len(result) == 7:

            return result


    # -----------------------------------------------------
    # fallback openCode
    # -----------------------------------------------------

    open_code = payload.get(
        "openCode"
    )


    if isinstance(
        open_code,
        str
    ):

        parts = (
            open_code
            .replace(
                "|",
                ","
            )
            .replace(
                "/",
                ","
            )
            .replace(
                " ",
                ","
            )
            .split(",")
        )


        result = []

        for value in parts:

            number = normalize_number(
                value
            )

            if number is not None:

                result.append(
                    number
                )


        if len(result) == 7:

            return result


    return []


# =========================================================
# 解析波色
# =========================================================

def parse_wave(
    payload
):

    if "wave" in payload:

        return payload.get(
            "wave"
        )

    if "waveColors" in payload:

        return payload.get(
            "waveColors"
        )

    return None


# =========================================================
# 请求API
# =========================================================

def fetch_api(
    lottery_key,
    source
):

    url = source["url"]


    last_error = None


    # =====================================================
    # 正常SSL请求
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

            print(
                url
            )


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
# 解析开奖
# =========================================================

def parse_draw(
    payload,
    lottery_key,
    source
):

    if not isinstance(
        payload,
        dict
    ):

        return None


    issue = payload.get(
        "expect"
    )


    if issue is None:

        return None


    issue = str(
        issue
    ).strip()


    numbers = parse_numbers(
        payload
    )


    if len(numbers) != 7:

        print(
            "❌ 开奖号码不是7个"
        )

        return None


    # -----------------------------------------------------
    # 号码范围
    # -----------------------------------------------------

    if any(
        number < 1
        or number > 49
        for number in numbers
    ):

        print(
            "❌ 号码超出1-49范围"
        )

        return None


    # -----------------------------------------------------
    # 号码不能重复
    # -----------------------------------------------------

    if len(
        set(numbers)
    ) != 7:

        print(
            "❌ 开奖号码出现重复"
        )

        return None


    # -----------------------------------------------------
    # 生肖
    # -----------------------------------------------------

    zodiac = payload.get(
        "zodiac"
    )


    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    wave = parse_wave(
        payload
    )


    return {

        "lottery":
            lottery_key,

        "issue":
            issue,

        "open_time":
            payload.get(
                "openTime"
            ),

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


    draw = parse_draw(

        payload,

        lottery_key,

        source
    )


    if draw is None:

        print(
            f"❌ {source['name']} "
            f"数据解析失败"
        )

        insert_fetch_log(

            lottery_key,

            False,

            error=
                "开奖数据解析失败"
        )

        return False


    # =====================================================
    # 写入数据库
    # =====================================================

    inserted = insert_draw(
        draw
    )


    if inserted:

        print(
            f"✅ 新增："
            f"{draw['issue']}"
        )

    else:

        print(
            f"ℹ️ 期号 "
            f"{draw['issue']} "
            f"已经存在"
        )


    insert_fetch_log(

        lottery_key,

        True,

        issue=
            draw["issue"],

        source=
            source["url"]
    )


    print()
    print(
        "开奖号码：",
        " ".join(
            f"{n:02d}"
            for n in draw["numbers"]
        )
    )


    print(
        "生肖：",
        draw["zodiac"]
    )


    print(
        "波色：",
        draw["wave"]
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
