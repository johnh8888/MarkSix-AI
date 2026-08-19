# -*- coding: utf-8 -*-

"""
六合彩 API 同步模块

功能：

1. 主 API
2. 备用 API
3. SSL 证书异常自动处理
4. JSON 解析
5. 历史开奖提取
6. 防止重复期号
7. 兼容多种 API 数据结构
"""

from __future__ import annotations

import json
import ssl
import urllib.request

from typing import Any


# ============================================================
# API 地址
# ============================================================

PRIMARY_API = (
    "https://marksix6.net/api/lottery_api.php"
)

BACKUP_API = (
    "https://api3.marksix6.net/lottery_api.php"
)


# ============================================================
# 三彩种 API 类型
# ============================================================

API_TYPES = {

    "新澳门彩": "newMacau",

    "老澳门彩": "oldMacau",

    "香港彩": "hk",

}


# ============================================================
# HTTP Header
# ============================================================

HEADERS = {

    "User-Agent":
        "Mozilla/5.0 "
        "(compatible; MarkSix-AI/6.2)",

    "Accept":
        "application/json,text/plain,*/*",

}


# ============================================================
# SSL 备用上下文
#
# marksix6 主站当前可能出现证书过期。
#
# 优先正常 SSL。
# 如果证书验证失败，则允许备用连接继续获取数据。
# ============================================================

UNVERIFIED_CONTEXT = (
    ssl._create_unverified_context()
)


# ============================================================
# HTTP 请求
# ============================================================

def request_json(
    url: str,
    timeout: int = 20,
) -> Any:

    request = urllib.request.Request(

        url,

        headers=HEADERS,

        method="GET",

    )

    try:

        with urllib.request.urlopen(

            request,

            timeout=timeout,

        ) as response:

            raw = response.read()

    except ssl.SSLCertVerificationError:

        with urllib.request.urlopen(

            request,

            timeout=timeout,

            context=UNVERIFIED_CONTEXT,

        ) as response:

            raw = response.read()

    text = raw.decode(

        "utf-8",

        errors="replace",

    ).strip()

    text = text.lstrip("\ufeff")

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        # 尝试处理简单 JSONP
        if (
            text.startswith("(")
            and text.endswith(")")
        ):

            text = text[1:-1]

            return json.loads(text)

        raise


# ============================================================
# 期号转换
# ============================================================

def normalize_issue(
    value: Any,
) -> str | None:

    if value is None:

        return None

    text = str(value).strip()

    if not text:

        return None

    if not text.isdigit():

        return None

    # 六合期号一般为纯数字
    if not 3 <= len(text) <= 10:

        return None

    return text


# ============================================================
# 号码转换
# ============================================================

def normalize_numbers(
    value: Any,
) -> list[int] | None:

    # ------------------------------------------
    # list / tuple
    # ------------------------------------------

    if isinstance(
        value,
        (list, tuple),
    ):

        numbers = []

        for item in value:

            try:

                number = int(item)

            except (
                TypeError,
                ValueError,
            ):

                return None

            if not 1 <= number <= 49:

                return None

            numbers.append(number)

        if (
            len(numbers) == 7
            and len(set(numbers)) == 7
        ):

            return numbers

    # ------------------------------------------
    # 字符串
    # ------------------------------------------

    if isinstance(
        value,
        str,
    ):

        text = value.strip()

        for separator in (
            ",",
            " ",
            "|",
            "-",
            "/",
        ):

            if separator not in text:

                continue

            parts = [

                x.strip()

                for x in text.split(separator)

                if x.strip()

            ]

            if len(parts) != 7:

                continue

            try:

                numbers = [
                    int(x)
                    for x in parts
                ]

            except ValueError:

                continue

            if (
                all(
                    1 <= x <= 49
                    for x in numbers
                )
                and len(set(numbers)) == 7
            ):

                return numbers

    return None


# ============================================================
# 从单个 dict 提取开奖
# ============================================================

def parse_record(
    data: dict[str, Any],
) -> dict[str, Any] | None:

    issue = None

    issue_keys = (

        "expect",

        "issue",

        "issueNo",

        "period",

        "qihao",

        "drawNo",

        "drawIssue",

    )

    for key in issue_keys:

        if key not in data:

            continue

        issue = normalize_issue(
            data.get(key)
        )

        if issue:

            break

    numbers = None

    number_keys = (

        "numbers",

        "openCode",

        "open_code",

        "openNumbers",

        "code",

        "result",

    )

    for key in number_keys:

        if key not in data:

            continue

        numbers = normalize_numbers(
            data.get(key)
        )

        if numbers:

            break

    # ------------------------------------------
    # 尝试 openCode1 ~ openCode7
    # ------------------------------------------

    if not numbers:

        for prefix in (
            "openCode",
            "num",
            "number",
        ):

            values = []

            for index in range(
                1,
                8,
            ):

                key = (
                    f"{prefix}{index}"
                )

                if key not in data:

                    values = []

                    break

                try:

                    values.append(
                        int(data[key])
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    values = []

                    break

            if (
                len(values) == 7
                and all(
                    1 <= x <= 49
                    for x in values
                )
                and len(set(values)) == 7
            ):

                numbers = values

                break

    if (
        issue
        and numbers
    ):

        return {

            "issue": issue,

            "numbers": numbers,

        }

    return None


# ============================================================
# 递归解析 API
# ============================================================

def extract_records(
    node: Any,
    output: list[dict[str, Any]],
) -> None:

    if isinstance(
        node,
        dict,
    ):

        record = parse_record(node)

        if record:

            output.append(record)

        # 先处理历史数据字段
        priority = []

        normal = []

        for key, value in node.items():

            key_lower = str(
                key
            ).lower()

            if any(
                token in key_lower
                for token in (
                    "history",
                    "lottery_data",
                    "records",
                    "list",
                    "result",
                    "data",
                )
            ):

                priority.append(value)

            else:

                normal.append(value)

        for value in (
            priority + normal
        ):

            extract_records(
                value,
                output,
            )

    elif isinstance(
        node,
        list,
    ):

        for item in node:

            extract_records(
                item,
                output,
            )


# ============================================================
# 标准化全部开奖记录
# ============================================================

def normalize_records(
    payload: Any,
) -> list[dict[str, Any]]:

    records = []

    extract_records(
        payload,
        records,
    )

    unique = {}

    for record in records:

        issue = record["issue"]

        if issue not in unique:

            unique[issue] = record

    result = list(
        unique.values()
    )

    def sort_key(item):

        try:

            return int(
                item["issue"]
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0

    result.sort(
        key=sort_key
    )

    return result


# ============================================================
# 获取某个彩种
# ============================================================

def fetch_lottery(
    lottery_name: str,
) -> list[dict[str, Any]]:

    api_type = API_TYPES[
        lottery_name
    ]

    print(
        f"[{lottery_name}] "
        f"API类型：{api_type}"
    )

    urls = [

        (
            f"{PRIMARY_API}"
            f"?type={api_type}"
        ),

        (
            f"{BACKUP_API}"
            f"?type={api_type}"
        ),

    ]

    final_records = []

    for index, url in enumerate(
        urls,
        start=1,
    ):

        print(
            f"[{lottery_name}] "
            f"请求API 第{index}次"
        )

        print(url)

        try:

            payload = request_json(
                url
            )

            records = normalize_records(
                payload
            )

            print(
                f"[{lottery_name}] "
                f"API解析得到："
                f"{len(records)} 期"
            )

            # --------------------------------------
            # 非空才替换
            # --------------------------------------

            if records:

                final_records = records

                break

        except Exception as exc:

            print(
                f"[WARN] "
                f"请求失败：{exc}"
            )

    return final_records
