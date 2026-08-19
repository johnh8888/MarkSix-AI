# -*- coding: utf-8 -*-

"""
六合彩数据同步模块 V8.1

核心规则：

1. 三个彩种分别请求独立 API
2. 不再使用历史总接口作为主数据源
3. 自动解析历史数据
4. 自动识别期号
5. 自动识别 7 个开奖号码
6. 第 7 个号码 = 特别号码
7. 数据不足时禁止覆盖数据库
8. 防止三个彩种错误获得同一份数据
"""

from __future__ import annotations

import json
import re
import time
import ssl
import urllib.request
from typing import Any


API_URLS = {
    "新澳门彩":
        "https://api3.marksix6.net/lottery_api.php?type=newMacau",

    "老澳门彩":
        "https://api3.marksix6.net/lottery_api.php?type=oldMacau",

    "香港彩":
        "https://api3.marksix6.net/lottery_api.php?type=hk",
}


MIN_HISTORY = 20


def http_get(
    url: str,
    timeout: int = 20,
) -> Any:

    headers = {
        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/131 Safari/537.36",

        "Accept":
            "application/json,text/plain,*/*",
    }

    request = urllib.request.Request(
        url,
        headers=headers,
    )

    try:

        context = ssl.create_default_context()

        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=context,
        ) as response:

            raw = response.read()

    except ssl.SSLCertVerificationError:

        print(
            "[WARN] SSL证书验证失败，"
            "启用兼容模式继续请求"
        )

        context = ssl._create_unverified_context()

        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=context,
        ) as response:

            raw = response.read()

    text = raw.decode(
        "utf-8",
        errors="ignore",
    )

    try:
        return json.loads(text)

    except json.JSONDecodeError:

        # 有些接口可能带 BOM
        text = text.lstrip("\ufeff")

        try:
            return json.loads(text)

        except Exception:

            raise RuntimeError(
                "API返回内容不是合法JSON："
                + text[:500]
            )


def normalize_number(value: Any) -> int | None:

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:

        number = int(
            str(value).strip()
        )

    except Exception:

        return None

    if 1 <= number <= 49:
        return number

    return None


def normalize_issue(value: Any) -> str:

    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    # 只保留数字
    digits = re.sub(
        r"\D",
        "",
        text,
    )

    # 六合常见期号
    if len(digits) >= 7:

        return digits

    return ""


def extract_numbers(
    item: dict[str, Any],
) -> list[int]:

    candidates = []

    # 优先寻找 numbers
    for key in (
        "numbers",
        "openCode",
        "open_code",
        "code",
        "codes",
        "result",
        "balls",
    ):

        value = item.get(key)

        if value is None:
            continue

        if isinstance(
            value,
            str,
        ):

            parts = re.findall(
                r"\d{1,2}",
                value,
            )

        elif isinstance(
            value,
            list,
        ):

            parts = value

        else:

            continue

        parsed = []

        for x in parts:

            number = normalize_number(x)

            if number is not None:
                parsed.append(number)

        if len(parsed) >= 7:

            candidates = parsed[:7]

            break

    if len(candidates) != 7:
        return []

    return candidates


def extract_issue(
    item: dict[str, Any],
) -> str:

    for key in (
        "expect",
        "issue",
        "period",
        "draw",
        "drawNo",
        "drawNumber",
        "qihao",
    ):

        if key not in item:
            continue

        issue = normalize_issue(
            item.get(key)
        )

        if issue:
            return issue

    return ""


def find_records(
    data: Any,
) -> list[dict[str, Any]]:

    result = []

    if isinstance(
        data,
        list,
    ):

        for item in data:

            if isinstance(
                item,
                dict,
            ):

                result.append(item)

        return result

    if isinstance(
        data,
        dict,
    ):

        # 常见历史字段
        for key in (
            "history",
            "data",
            "list",
            "records",
            "lottery_data",
            "result",
        ):

            value = data.get(key)

            if isinstance(
                value,
                list,
            ):

                for item in value:

                    if isinstance(
                        item,
                        dict,
                    ):

                        result.append(item)

                if result:
                    return result

            if isinstance(
                value,
                dict,
            ):

                nested = find_records(
                    value
                )

                if nested:
                    return nested

        # 单条记录
        if (
            extract_issue(data)
            and extract_numbers(data)
        ):

            return [data]

        # 深度扫描
        for value in data.values():

            if isinstance(
                value,
                (dict, list),
            ):

                nested = find_records(
                    value
                )

                if nested:
                    result.extend(
                        nested
                    )

        return result

    return []


def parse_records(
    raw: Any,
    lottery_name: str,
) -> list[dict[str, Any]]:

    raw_records = find_records(
        raw
    )

    records = []

    seen = set()

    for item in raw_records:

        issue = extract_issue(
            item
        )

        numbers = extract_numbers(
            item
        )

        if not issue:
            continue

        if len(numbers) != 7:
            continue

        key = (
            issue,
            tuple(numbers),
        )

        if key in seen:
            continue

        seen.add(key)

        records.append(
            {
                "lottery":
                    lottery_name,

                "issue":
                    issue,

                "numbers":
                    numbers,

                "special_number":
                    numbers[6],

                "open_time":
                    str(
                        item.get(
                            "openTime",
                            item.get(
                                "open_time",
                                "",
                            ),
                        )
                    ),

                "source":
                    "api3.marksix6.net",
            }
        )

    # 去重期号
    unique = {}

    for row in records:

        issue = row["issue"]

        if issue not in unique:

            unique[issue] = row

    records = list(
        unique.values()
    )

    records.sort(
        key=lambda x: int(
            x["issue"]
        )
    )

    return records


def validate_records(
    records: list[dict[str, Any]],
    lottery_name: str,
) -> None:

    if not records:

        raise RuntimeError(
            f"{lottery_name}："
            "API没有解析到有效开奖数据"
        )

    valid = []

    for row in records:

        issue = row.get(
            "issue",
            "",
        )

        numbers = row.get(
            "numbers",
            [],
        )

        if not issue:
            continue

        if len(numbers) != 7:
            continue

        if any(
            not (
                isinstance(x, int)
                and 1 <= x <= 49
            )
            for x in numbers
        ):
            continue

        # 同一期不能出现重复号码
        if len(set(numbers)) != 7:
            continue

        valid.append(row)

    if not valid:

        raise RuntimeError(
            f"{lottery_name}："
            "没有通过数据完整性检查"
        )

    if len(valid) < MIN_HISTORY:

        raise RuntimeError(
            f"{lottery_name}："
            f"API只解析出 {len(valid)} 期，"
            f"少于最低要求 {MIN_HISTORY} 期，"
            "拒绝覆盖数据库"
        )


def fetch_lottery(
    lottery_name: str,
) -> list[dict[str, Any]]:

    if lottery_name not in API_URLS:

        raise ValueError(
            f"未知彩种：{lottery_name}"
        )

    url = API_URLS[
        lottery_name
    ]

    print(
        "=" * 70
    )

    print(
        f"正在同步：{lottery_name}"
    )

    print(
        "=" * 70
    )

    print(
        f"[API] {url}"
    )

    last_error = None

    for attempt in range(
        1,
        4,
    ):

        try:

            print(
                f"[API] 请求第 {attempt} 次"
            )

            raw = http_get(
                url
            )

            records = parse_records(
                raw,
                lottery_name,
            )

            print(
                f"[{lottery_name}] "
                f"解析有效历史："
                f"{len(records)} 期"
            )

            validate_records(
                records,
                lottery_name,
            )

            if not records:

                raise RuntimeError(
                    "没有有效数据"
                )

            print(
                f"[{lottery_name}] "
                f"最早期号："
                f"{records[0]['issue']}"
            )

            print(
                f"[{lottery_name}] "
                f"最新期号："
                f"{records[-1]['issue']}"
            )

            print(
                f"[{lottery_name}] "
                f"最新号码："
                + " ".join(
                    f"{x:02d}"
                    for x in records[-1][
                        "numbers"
                    ]
                )
            )

            print(
                f"[{lottery_name}] "
                f"特别号码："
                f"{records[-1]['special_number']:02d}"
            )

            return records

        except Exception as exc:

            last_error = exc

            print(
                f"[ERROR] "
                f"{lottery_name}："
                f"{exc}"
            )

            if attempt < 3:
                time.sleep(2)

    raise RuntimeError(
        f"{lottery_name} API同步失败："
        f"{last_error}"
    )
