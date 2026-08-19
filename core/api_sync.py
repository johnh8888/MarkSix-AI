# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

API 在线数据同步模块

流程：

API
 ↓
解析
 ↓
数据验证
 ↓
SQLite

支持：

香港六合彩
新澳门六合彩
老澳门六合彩
"""

from __future__ import annotations

import re
import time

import requests
import urllib3


# =====================================================
# 配置
# =====================================================

try:
    from config import (
        API_HISTORY,
        API_REALTIME,
        LOTTERIES
    )
except ImportError:
    from ..config import (
        API_HISTORY,
        API_REALTIME,
        LOTTERIES
    )


from .database import (
    save_draw
)


# =====================================================
# SSL警告
# =====================================================

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# =====================================================
# HTTP配置
# =====================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),

    "Accept": (
        "application/json,"
        "text/plain,"
        "*/*"
    )
}


# =====================================================
# HTTP请求
# =====================================================

def request_api(
    url,
    retries=2
):
    """
    请求API。

    第一策略：
    SSL验证关闭。

    原因：
    marksix6 当前证书存在过期问题，
    GitHub Actions 会直接拒绝连接。

    如果失败：
    自动重试。
    """

    print()
    print(
        "正在请求API:"
    )
    print(
        url
    )

    for attempt in range(
        1,
        retries + 1
    ):

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30,
                verify=False
            )

            response.raise_for_status()

            text = response.text

            if not text.strip():

                raise ValueError(
                    "API返回空内容"
                )

            try:

                data = response.json()

            except Exception:

                # 某些API可能返回BOM
                text = text.lstrip(
                    "\ufeff"
                )

                import json

                data = json.loads(
                    text
                )

            print(
                "API请求成功"
            )

            return data

        except Exception as e:

            print(
                f"第 {attempt} 次请求失败:",
                e
            )

            if attempt < retries:

                time.sleep(2)

    print(
        "API请求最终失败:",
        url
    )

    return {}


# =====================================================
# 数字解析
# =====================================================

def parse_numbers(value):
    """
    从字符串、列表、字典等内容中提取1~49数字。
    """

    if value is None:

        return []

    result = []

    if isinstance(
        value,
        list
    ):

        values = value

    else:

        values = [value]

    for item in values:

        matches = re.findall(
            r"(?<!\d)(\d{1,2})(?!\d)",
            str(item)
        )

        for value in matches:

            number = int(value)

            if 1 <= number <= 49:

                result.append(
                    number
                )

    return result


# =====================================================
# 期号解析
# =====================================================

def parse_issue(value):
    """
    从开奖记录中提取期号。
    """

    text = str(value)

    patterns = [
        r"(\d{4,})\s*期",
        r"第\s*(\d{4,})\s*期",
        r"expect[\"'\s:]+(\d+)",
        r"issue[\"'\s:]+(\d+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return match.group(1)

    return None


# =====================================================
# 彩种识别
# =====================================================

def identify_lottery(
    item
):
    """
    根据名称识别彩种。
    """

    if not isinstance(
        item,
        dict
    ):

        return None

    text = " ".join(
        str(item.get(key, ""))
        for key in (
            "name",
            "type",
            "lottery",
            "title"
        )
    )

    # 注意顺序：
    # 新澳门必须先判断
    if "新澳门" in text:

        return "newMacau"

    if "老澳门" in text:

        return "oldMacau"

    if "澳门" in text:

        # 无法明确新/老时不猜
        return None

    if "香港" in text:

        return "hk"

    if "HK" in text.upper():

        return "hk"

    return None


# =====================================================
# 解析单条历史记录
# =====================================================

def parse_history_row(
    row
):
    """
    解析单条历史开奖。

    支持：

    字符串
    dict
    list
    """

    issue = None
    numbers = []

    # -----------------------------
    # dict
    # -----------------------------

    if isinstance(
        row,
        dict
    ):

        issue = (
            row.get("issue")
            or row.get("expect")
            or row.get("period")
            or row.get("qihao")
        )

        candidates = [

            row.get("numbers"),

            row.get("openCode"),

            row.get("open_code"),

            row.get("result"),

            row.get("code"),

            row.get("data")

        ]

        for value in candidates:

            if value is not None:

                numbers = parse_numbers(
                    value
                )

                if len(numbers) >= 7:

                    break

        if not numbers:

            numbers = parse_numbers(
                row
            )

    # -----------------------------
    # list
    # -----------------------------

    elif isinstance(
        row,
        list
    ):

        numbers = parse_numbers(
            row
        )

    # -----------------------------
    # string
    # -----------------------------

    else:

        text = str(row)

        issue = parse_issue(
            text
        )

        numbers = parse_numbers(
            text
        )

    # -----------------------------
    # 期号
    # -----------------------------

    if issue is None:

        issue = parse_issue(
            row
        )

    if issue is None:

        return None

    # -----------------------------
    # 开奖号码
    # -----------------------------

    if len(numbers) < 7:

        return None

    # 只取前7个
    numbers = numbers[:7]

    # 去重
    if len(
        set(numbers)
    ) != 7:

        return None

    return {
        "issue": str(issue),

        "numbers": numbers[:6],

        "special": numbers[6]
    }


# =====================================================
# 历史数据同步
# =====================================================

def sync_history():

    print()
    print(
        "=" * 70
    )
    print(
        "正在同步历史开奖"
    )
    print(
        "=" * 70
    )

    data = request_api(
        API_HISTORY
    )

    if not data:

        return {}

    result = {
        key: 0
        for key in LOTTERIES
    }

    items = data.get(
        "lottery_data",
        []
    )

    if not isinstance(
        items,
        list
    ):

        print(
            "API lottery_data 格式异常"
        )

        return result

    for item in items:

        key = identify_lottery(
            item
        )

        if not key:

            continue

        history = item.get(
            "history",
            []
        )

        if not isinstance(
            history,
            list
        ):

            continue

        count = 0

        for row in history:

            parsed = parse_history_row(
                row
            )

            if not parsed:

                continue

            ok = save_draw(
                lottery=key,

                issue=parsed["issue"],

                numbers=parsed["numbers"],

                special=parsed["special"],

                source="history_api"
            )

            if ok:

                count += 1

        result[key] = count

        print(
            LOTTERIES[key],
            "新增:",
            count,
            "期"
        )

    return result


# =====================================================
# 实时数据同步
# =====================================================

def sync_realtime():

    print()
    print(
        "=" * 70
    )
    print(
        "正在同步最新开奖"
    )
    print(
        "=" * 70
    )

    result = {}

    for key in LOTTERIES:

        url = (
            API_REALTIME
            + "?type="
            + key
        )

        try:

            data = request_api(
                url
            )

            if not data:

                result[key] = False
                continue

            # -------------------------
            # 提取数据
            # -------------------------

            issue = None
            numbers = []

            if isinstance(
                data,
                dict
            ):

                issue = (
                    data.get("expect")
                    or data.get("issue")
                    or data.get("period")
                )

                numbers = parse_numbers(
                    data.get("numbers")
                    or data.get("openCode")
                    or data.get("open_code")
                    or data.get("result")
                )

                if len(numbers) < 7:

                    numbers = parse_numbers(
                        data
                    )

            else:

                numbers = parse_numbers(
                    data
                )

                issue = parse_issue(
                    data
                )

            if not issue:

                result[key] = False
                continue

            if len(numbers) < 7:

                result[key] = False
                continue

            numbers = numbers[:7]

            if len(
                set(numbers)
            ) != 7:

                result[key] = False
                continue

            ok = save_draw(

                lottery=key,

                issue=str(issue),

                numbers=numbers[:6],

                special=numbers[6],

                source="realtime_api"
            )

            result[key] = ok

            print(
                LOTTERIES[key],
                "最新期:",
                issue,
                "保存:",
                ok
            )

        except Exception as e:

            print(
                LOTTERIES[key],
                "实时同步失败:",
                e
            )

            result[key] = False

    return result


# =====================================================
# 总同步
# =====================================================

def sync_all():

    print()
    print(
        "=" * 70
    )
    print(
        "开始API同步"
    )
    print(
        "=" * 70
    )

    history = {}

    realtime = {}

    try:

        history = sync_history()

    except Exception as e:

        print(
            "历史同步失败:",
            e
        )

    try:

        realtime = sync_realtime()

    except Exception as e:

        print(
            "实时同步失败:",
            e
        )

    return {
        "history": history,

        "realtime": realtime,

        "status": "completed"
    }


# =====================================================
# 导出
# =====================================================

__all__ = [
    "request_api",
    "parse_numbers",
    "parse_issue",
    "identify_lottery",
    "parse_history_row",
    "sync_history",
    "sync_realtime",
    "sync_all"
]
