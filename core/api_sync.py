# -*- coding: utf-8 -*-

"""
六合彩数据同步模块 V8.2
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from typing import Any


API_URL = "https://marksix6.net/index.php?api=1"

CODE_MAP = {
    "新澳门彩": "newMacau",
    "老澳门彩": "oldMacau",
    "香港彩": "hk",
}

MIN_HISTORY = 20


def http_get(url: str, timeout: int = 20) -> Any:

    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/131 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
    }

    request = urllib.request.Request(url, headers=headers)

    try:

        context = ssl.create_default_context()

        with urllib.request.urlopen(
            request, timeout=timeout, context=context
        ) as response:

            raw = response.read()

    except Exception as exc:

        print(
            f"[WARN] 首次请求失败（{exc}），"
            "启用SSL兼容模式（跳过证书验证）重试"
        )

        context = ssl._create_unverified_context()

        with urllib.request.urlopen(
            request, timeout=timeout, context=context
        ) as response:

            raw = response.read()

    text = raw.decode("utf-8", errors="ignore")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        text = text.lstrip("\ufeff")
        try:
            return json.loads(text)
        except Exception:
            raise RuntimeError(
                "API返回内容不是合法JSON：" + text[:500]
            )


def parse_numbers(code: Any) -> list[int]:

    if isinstance(code, list):
        result = []
        for x in code:
            try:
                result.append(int(x))
            except Exception:
                pass
        return result[:7]

    if not code:
        return []

    result = []
    for x in str(code).split(","):
        x = x.strip()
        if x.isdigit():
            result.append(int(x))

    return result[:7]


def parse_records(raw: Any, lottery_name: str) -> list[dict[str, Any]]:

    if lottery_name not in CODE_MAP:
        raise ValueError(f"未知彩种：{lottery_name}")

    target_code = CODE_MAP[lottery_name]

    if not raw:
        return []

    lottery_data = raw.get("lottery_data", [])

    records = []

    for item in lottery_data:

        if item.get("code") != target_code:
            continue

        numbers = parse_numbers(item.get("openCode", ""))

        if len(numbers) == 7:

            issue = str(item.get("expect", "")).strip()

            if issue:
                records.append({
                    "lottery": lottery_name,
                    "issue": issue,
                    "numbers": numbers,
                    "special_number": numbers[6],
                    "open_time": str(item.get("openTime", "")),
                    "source": "marksix6.net",
                })

        for h in item.get("history", []):

            if not isinstance(h, str):
                continue

            try:
                issue, code = h.split("期：", 1)
                numbers = parse_numbers(code)

                if len(numbers) != 7:
                    continue

                issue = issue.strip()

                if not issue:
                    continue

                records.append({
                    "lottery": lottery_name,
                    "issue": issue,
                    "numbers": numbers,
                    "special_number": numbers[6],
                    "open_time": "",
                    "source": "marksix6.net",
                })

            except Exception:
                continue

    unique = {}
    for row in records:
        unique[row["issue"]] = row

    result = list(unique.values())
    result.sort(key=lambda x: int(x["issue"]))

    return result


def validate_records(records: list[dict[str, Any]], lottery_name: str) -> None:

    if not records:
        raise RuntimeError(f"{lottery_name}：API没有解析到有效开奖数据")

    valid = []

    for row in records:

        issue = row.get("issue", "")
        numbers = row.get("numbers", [])

        if not issue:
            continue
        if len(numbers) != 7:
            continue
        if any(not (isinstance(x, int) and 1 <= x <= 49) for x in numbers):
            continue
        if len(set(numbers)) != 7:
            continue

        valid.append(row)

    if not valid:
        raise RuntimeError(f"{lottery_name}：没有通过数据完整性检查")

    if len(valid) < MIN_HISTORY:
        raise RuntimeError(
            f"{lottery_name}：API只解析出 {len(valid)} 期，"
            f"少于最低要求 {MIN_HISTORY} 期，拒绝覆盖数据库"
        )


def fetch_lottery(lottery_name: str) -> list[dict[str, Any]]:

    print("=" * 70)
    print(f"正在同步：{lottery_name}")
    print("=" * 70)
    print(f"[API] {API_URL}")

    last_error = None

    for attempt in range(1, 4):

        try:

            print(f"[API] 请求第 {attempt} 次")

            raw = http_get(API_URL)

            records = parse_records(raw, lottery_name)

            print(f"[{lottery_name}] 解析有效历史：{len(records)} 期")

            validate_records(records, lottery_name)

            print(f"[{lottery_name}] 最早期号：{records[0]['issue']}")
            print(f"[{lottery_name}] 最新期号：{records[-1]['issue']}")
            print(
                f"[{lottery_name}] 最新号码："
                + " ".join(f"{x:02d}" for x in records[-1]["numbers"])
            )

            return records

        except Exception as exc:

            last_error = exc

            print(f"[ERROR] {lottery_name}：{exc}")

            if attempt < 3:
                time.sleep(2)

    raise RuntimeError(f"{lottery_name} API同步失败：{last_error}")
