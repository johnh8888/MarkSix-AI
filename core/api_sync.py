# -*- coding: utf-8 -*-

"""
六合彩 API 数据层
V6.0 REAL DATA MULTI HISTORY

功能：

1. 获取最新开奖
2. 获取历史开奖
3. 双 API fallback
4. SSL 异常自动切换
5. 兼容多种 JSON 结构
6. 自动去重
7. 自动排序
"""

from __future__ import annotations

import json
import ssl
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


PRIMARY_BASE = "https://marksix6.net/api/lottery_api.php"
BACKUP_BASE = "https://api3.marksix6.net/lottery_api.php"


LOTTERY_CONFIG = {
    "新澳门彩": "newMacau",
    "老澳门彩": "oldMacau",
    "香港彩": "hk",
}


def log(message: str) -> None:
    print(message, flush=True)


def _request_json(url: str, timeout: int = 20) -> Any:
    """
    请求 JSON。

    不关闭 SSL 验证。
    如果证书异常，直接交给上层 fallback。
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "Chrome/120 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Connection": "close",
    }

    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )

    context = ssl.create_default_context()

    with urllib.request.urlopen(
        request,
        timeout=timeout,
        context=context,
    ) as response:

        raw = response.read()

        if not raw:
            raise ValueError("API返回空内容")

        text = raw.decode(
            "utf-8",
            errors="replace",
        )

        return json.loads(text)


def _extract_number(value: Any) -> Optional[int]:
    try:
        number = int(str(value).strip())

        if 1 <= number <= 49:
            return number

    except Exception:
        pass

    return None


def _parse_numbers(value: Any) -> List[int]:
    """
    兼容：

    [1,2,3]
    ["01","02"]
    "01,02,03"
    "01 02 03"
    {"numbers":[...]}
    """

    result: List[int] = []

    if value is None:
        return result

    if isinstance(value, dict):

        for key in (
            "numbers",
            "openCode",
            "open_code",
            "code",
            "result",
        ):

            if key in value:

                result = _parse_numbers(
                    value[key]
                )

                if result:
                    return result

        return result

    if isinstance(value, (list, tuple)):

        for item in value:

            number = _extract_number(item)

            if number is not None:
                result.append(number)

        return result[:7]

    if isinstance(value, str):

        text = value.strip()

        for separator in (
            ",",
            "|",
            " ",
            "/",
            "-",
        ):
            text = text.replace(
                separator,
                ",",
            )

        for part in text.split(","):

            number = _extract_number(part)

            if number is not None:
                result.append(number)

        return result[:7]

    return result


def _normalize_record(
    item: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    if not isinstance(item, dict):
        return None

    issue = (
        item.get("expect")
        or item.get("issue")
        or item.get("period")
        or item.get("qihao")
        or item.get("draw")
        or item.get("drawNo")
    )

    if issue is None:
        return None

    issue = str(issue).strip()

    if not issue:
        return None

    numbers = _parse_numbers(
        item.get("numbers")
        or item.get("openCode")
        or item.get("open_code")
        or item.get("code")
    )

    if len(numbers) < 7:
        return None

    open_time = (
        item.get("openTime")
        or item.get("open_time")
        or item.get("date")
        or item.get("drawTime")
        or ""
    )

    return {
        "issue": issue,
        "numbers": numbers[:7],
        "open_time": str(open_time),
        "raw": item,
    }


def _looks_like_record(
    value: Any,
) -> bool:

    if not isinstance(value, dict):
        return False

    issue_keys = {
        "expect",
        "issue",
        "period",
        "qihao",
        "draw",
        "drawNo",
    }

    number_keys = {
        "numbers",
        "openCode",
        "open_code",
        "code",
    }

    return bool(
        issue_keys.intersection(value.keys())
    ) and bool(
        number_keys.intersection(value.keys())
    )


def _collect_records(
    obj: Any,
    output: List[Dict[str, Any]],
) -> None:
    """
    递归寻找历史记录。
    """

    if obj is None:
        return

    if isinstance(obj, dict):

        if _looks_like_record(obj):

            record = _normalize_record(obj)

            if record:
                output.append(record)

        for key, value in obj.items():

            key_lower = str(key).lower()

            if key_lower in {
                "history",
                "historical",
                "records",
                "data",
                "lottery_data",
                "result",
                "list",
            }:
                _collect_records(
                    value,
                    output,
                )

            elif isinstance(
                value,
                (dict, list),
            ):
                _collect_records(
                    value,
                    output,
                )

        return

    if isinstance(obj, list):

        for item in obj:

            _collect_records(
                item,
                output,
            )


def _deduplicate_records(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    unique: Dict[str, Dict[str, Any]] = {}

    for record in records:

        issue = str(
            record["issue"]
        )

        unique[issue] = record

    def sort_key(item: Dict[str, Any]):
        issue = str(item["issue"])

        digits = "".join(
            c for c in issue
            if c.isdigit()
        )

        try:
            return int(digits)
        except Exception:
            return digits

    result = list(
        unique.values()
    )

    result.sort(
        key=sort_key
    )

    return result


def fetch_lottery(
    lottery_name: str,
    max_retries: int = 2,
) -> Dict[str, Any]:

    if lottery_name not in LOTTERY_CONFIG:
        raise ValueError(
            f"未知彩种：{lottery_name}"
        )

    lottery_type = LOTTERY_CONFIG[
        lottery_name
    ]

    query = urllib.parse.urlencode(
        {
            "type": lottery_type,
        }
    )

    urls = [
        f"{PRIMARY_BASE}?{query}",
        f"{BACKUP_BASE}?{query}",
    ]

    all_records: List[
        Dict[str, Any]
    ] = []

    latest_payload = None

    for index, url in enumerate(
        urls,
        start=1,
    ):

        log(
            f"[{lottery_name}] "
            f"请求API 第{index}次"
        )

        log(url)

        try:

            payload = _request_json(
                url
            )

            latest_payload = payload

            records: List[
                Dict[str, Any]
            ] = []

            _collect_records(
                payload,
                records,
            )

            records = _deduplicate_records(
                records
            )

            if records:

                log(
                    f"[{lottery_name}] "
                    f"API解析得到："
                    f"{len(records)} 期"
                )

                all_records.extend(
                    records
                )

                break

            log(
                f"[{lottery_name}] "
                "API没有解析到有效历史记录"
            )

        except Exception as exc:

            log(
                f"[WARN] 请求失败：{exc}"
            )

    all_records = _deduplicate_records(
        all_records
    )

    return {
        "lottery": lottery_name,
        "type": lottery_type,
        "records": all_records,
        "payload": latest_payload,
    }
