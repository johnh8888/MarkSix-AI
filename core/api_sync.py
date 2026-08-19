# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
真实历史数据同步模块 V8.1

修复：
1. 正确解析 index.php?api=1
2. 按 lottery_data 彩种节点分别提取历史
3. 不再把同一批数据写入三个彩种
4. 正确解析 history
5. 正确解析 expect / openCode / numbers
6. 新澳门彩 / 老澳门彩 / 香港彩分别保存
7. 自动过滤明显错误的期号
8. 最新 API 作为补充
"""

from __future__ import annotations

import json
import ssl
import time
from typing import Any

import requests


HISTORY_URL = "https://marksix6.net/index.php?api=1"

LATEST_URL = (
    "https://marksix6.net/api/lottery_api.php"
)


LOTTERY_TYPES = {
    "新澳门彩": "newMacau",
    "老澳门彩": "oldMacau",
    "香港彩": "hk",
}


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def _request_json(
    url: str,
    params: dict[str, Any] | None = None,
    retries: int = 3,
) -> Any:

    last_error = None

    for attempt in range(1, retries + 1):

        try:

            print(
                f"[API] 请求第 {attempt} 次："
                f"{url}"
            )

            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=30,
                verify=True,
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.SSLError as exc:

            last_error = exc

            print(
                "[WARN] SSL证书验证失败，"
                "启用兼容模式继续请求"
            )

            try:

                response = requests.get(
                    url,
                    params=params,
                    headers=HEADERS,
                    timeout=30,
                    verify=False,
                )

                response.raise_for_status()

                return response.json()

            except Exception as exc2:

                last_error = exc2

        except Exception as exc:

            last_error = exc

        if attempt < retries:
            time.sleep(1)

    raise RuntimeError(
        f"API请求失败：{last_error}"
    )


def _safe_int_issue(
    issue: Any,
) -> int:

    try:

        text = str(issue).strip()

        digits = "".join(
            ch
            for ch in text
            if ch.isdigit()
        )

        if not digits:
            return 0

        return int(digits)

    except Exception:

        return 0


def _parse_numbers(
    value: Any,
) -> list[int]:

    if value is None:
        return []

    if isinstance(value, list):

        result = []

        for item in value:

            try:

                number = int(
                    str(item).strip()
                )

            except Exception:
                continue

            if 1 <= number <= 49:
                result.append(number)

        return result

    if isinstance(value, str):

        text = (
            value
            .replace("，", ",")
            .replace("、", ",")
            .replace("|", ",")
            .replace(" ", ",")
        )

        result = []

        for item in text.split(","):

            item = item.strip()

            if not item:
                continue

            try:

                number = int(item)

            except Exception:
                continue

            if 1 <= number <= 49:
                result.append(number)

        return result

    return []


def _make_record(
    issue: Any,
    numbers: Any,
) -> dict[str, Any] | None:

    issue_text = str(issue).strip()

    issue_int = _safe_int_issue(
        issue_text
    )

    nums = _parse_numbers(
        numbers
    )

    if issue_int <= 0:
        return None

    if len(nums) != 7:
        return None

    return {
        "issue": issue_text,
        "numbers": nums,
    }


def _extract_history_from_node(
    node: dict[str, Any],
) -> list[dict[str, Any]]:

    records = []

    history = node.get(
        "history"
    )

    # -------------------------------------------------
    # 情况1：
    # history 本身就是 list
    # -------------------------------------------------

    if isinstance(
        history,
        list,
    ):

        for item in history:

            # -----------------------------
            # history 是 dict
            # -----------------------------

            if isinstance(
                item,
                dict,
            ):

                issue = (
                    item.get("expect")
                    or item.get("issue")
                    or item.get("period")
                    or item.get("qihao")
                )

                numbers = (
                    item.get("numbers")
                    or item.get("openCode")
                    or item.get("open_code")
                    or item.get("code")
                )

                record = _make_record(
                    issue,
                    numbers,
                )

                if record:
                    records.append(record)

                continue

            # -----------------------------
            # history 是字符串
            # -----------------------------

            if isinstance(
                item,
                str,
            ):

                text = item.strip()

                # 尝试 JSON
                try:

                    parsed = json.loads(
                        text
                    )

                    if isinstance(
                        parsed,
                        dict,
                    ):

                        issue = (
                            parsed.get("expect")
                            or parsed.get("issue")
                        )

                        numbers = (
                            parsed.get("numbers")
                            or parsed.get("openCode")
                        )

                        record = _make_record(
                            issue,
                            numbers,
                        )

                        if record:
                            records.append(
                                record
                            )

                        continue

                except Exception:
                    pass

                continue

    # -------------------------------------------------
    # 情况2：
    # history 是 dict
    # -------------------------------------------------

    elif isinstance(
        history,
        dict,
    ):

        for key, value in history.items():

            if isinstance(
                value,
                dict,
            ):

                issue = (
                    value.get("expect")
                    or value.get("issue")
                    or key
                )

                numbers = (
                    value.get("numbers")
                    or value.get("openCode")
                    or value.get("open_code")
                )

                record = _make_record(
                    issue,
                    numbers,
                )

                if record:
                    records.append(record)

    return _deduplicate_records(
        records
    )


def _extract_node_latest(
    node: dict[str, Any],
) -> list[dict[str, Any]]:

    issue = (
        node.get("expect")
        or node.get("issue")
        or node.get("period")
    )

    numbers = (
        node.get("numbers")
        or node.get("openCode")
    )

    record = _make_record(
        issue,
        numbers,
    )

    if record:
        return [record]

    return []


def _deduplicate_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    result = {}

    for record in records:

        issue = str(
            record["issue"]
        )

        nums = record[
            "numbers"
        ]

        if len(nums) != 7:
            continue

        issue_int = _safe_int_issue(
            issue
        )

        if issue_int <= 0:
            continue

        result[issue] = {
            "issue": issue,
            "numbers": nums,
        }

    return sorted(
        result.values(),
        key=lambda x: _safe_int_issue(
            x["issue"]
        ),
    )


def _name_match(
    node_name: str,
    lottery_name: str,
) -> bool:

    a = (
        str(node_name)
        .strip()
        .lower()
    )

    b = (
        str(lottery_name)
        .strip()
        .lower()
    )

    if a == b:
        return True

    aliases = {

        "新澳门彩": [
            "新澳门彩",
            "新澳彩",
            "newmacau",
            "new_macau",
            "macau_new",
            "澳门新彩",
        ],

        "老澳门彩": [
            "老澳门彩",
            "旧澳门彩",
            "oldmacau",
            "old_macau",
            "macau_old",
        ],

        "香港彩": [
            "香港彩",
            "六合彩",
            "香港六合彩",
            "hk",
            "hongkong",
            "hong kong",
        ],
    }

    for alias in aliases.get(
        lottery_name,
        [],
    ):

        if (
            a == alias.lower()
        ):
            return True

    return False


def _find_lottery_node(
    data: Any,
    lottery_name: str,
) -> dict[str, Any] | None:

    # -------------------------------------------------
    # 标准结构：
    #
    # {
    #   lottery_data: [...]
    # }
    # -------------------------------------------------

    if isinstance(
        data,
        dict,
    ):

        lottery_data = data.get(
            "lottery_data"
        )

        if isinstance(
            lottery_data,
            list,
        ):

            for node in lottery_data:

                if not isinstance(
                    node,
                    dict,
                ):
                    continue

                name = (
                    node.get("name")
                    or node.get("title")
                    or node.get("lottery")
                )

                if name and _name_match(
                    name,
                    lottery_name,
                ):

                    return node

        # 某些接口可能直接以彩种名称作为 key

        for key, value in data.items():

            if _name_match(
                key,
                lottery_name,
            ):

                if isinstance(
                    value,
                    dict,
                ):

                    return value

    # -------------------------------------------------
    # 结构直接是 list
    # -------------------------------------------------

    if isinstance(
        data,
        list,
    ):

        for node in data:

            if not isinstance(
                node,
                dict,
            ):
                continue

            name = (
                node.get("name")
                or node.get("title")
                or node.get("lottery")
            )

            if name and _name_match(
                name,
                lottery_name,
            ):

                return node

    return None


def _get_history(
    lottery_name: str,
) -> list[dict[str, Any]]:

    print(
        "[HISTORY] 请求历史总接口"
    )

    print(
        HISTORY_URL
    )

    data = _request_json(
        HISTORY_URL
    )

    node = _find_lottery_node(
        data,
        lottery_name,
    )

    if node is None:

        print(
            f"[ERROR] 未找到彩种节点："
            f"{lottery_name}"
        )

        if isinstance(
            data,
            dict,
        ):

            print(
                "[DEBUG] lottery_data类型："
                f"{type(data.get('lottery_data'))}"
            )

            lottery_data = data.get(
                "lottery_data"
            )

            if isinstance(
                lottery_data,
                list,
            ):

                print(
                    "[DEBUG] 彩种节点："
                )

                for item in lottery_data:

                    if isinstance(
                        item,
                        dict,
                    ):

                        print(
                            "  -",
                            item.get(
                                "name"
                            ),
                        )

        return []

    records = (
        _extract_history_from_node(
            node
        )
    )

    # 如果 history 没有解析出来，
    # 至少使用节点当前最新一期

    if not records:

        records = (
            _extract_node_latest(
                node
            )
        )

    print(
        f"[{lottery_name}] "
        f"历史彩种节点：1"
    )

    print(
        f"[{lottery_name}] "
        f"历史接口解析："
        f"{len(records)} 期"
    )

    return records


def _get_latest(
    lottery_name: str,
) -> list[dict[str, Any]]:

    lottery_type = (
        LOTTERY_TYPES[
            lottery_name
        ]
    )

    print(
        f"[{lottery_name}] "
        "请求最新API 第1次"
    )

    print(
        f"{LATEST_URL}"
        f"?type={lottery_type}"
    )

    data = _request_json(
        LATEST_URL,
        params={
            "type": lottery_type,
            "_": str(
                int(
                    time.time()
                )
            ),
        },
    )

    records = []

    if isinstance(
        data,
        dict,
    ):

        record_list = (
            _extract_node_latest(
                data
            )
        )

        records.extend(
            record_list
        )

    elif isinstance(
        data,
        list,
    ):

        for item in data:

            if not isinstance(
                item,
                dict,
            ):
                continue

            records.extend(
                _extract_node_latest(
                    item
                )
            )

    records = _deduplicate_records(
        records
    )

    print(
        f"[{lottery_name}] "
        f"最新API解析："
        f"{len(records)} 期"
    )

    return records


def _merge_records(
    history: list[dict[str, Any]],
    latest: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    merged = {}

    for record in history + latest:

        if not isinstance(
            record,
            dict,
        ):
            continue

        issue = str(
            record.get(
                "issue",
                "",
            )
        )

        numbers = _parse_numbers(
            record.get(
                "numbers",
                [],
            )
        )

        if (
            not issue
            or len(numbers) != 7
        ):
            continue

        issue_int = _safe_int_issue(
            issue
        )

        # 防止把明显错误数据写入数据库
        if issue_int < 2020000:
            continue

        merged[issue] = {
            "issue": issue,
            "numbers": numbers,
        }

    return sorted(
        merged.values(),
        key=lambda x: _safe_int_issue(
            x["issue"]
        ),
    )


def fetch_lottery(
    lottery_name: str,
) -> list[dict[str, Any]]:

    if lottery_name not in LOTTERY_TYPES:

        raise ValueError(
            f"未知彩种：{lottery_name}"
        )

    print(
        "=" * 70
    )

    print(
        f"正在同步：{lottery_name}"
    )

    print(
        "=" * 70
    )

    history = []

    try:

        history = _get_history(
            lottery_name
        )

    except Exception as exc:

        print(
            f"[WARN] {lottery_name} "
            f"历史接口失败：{exc}"
        )

    latest = []

    try:

        latest = _get_latest(
            lottery_name
        )

    except Exception as exc:

        print(
            f"[WARN] {lottery_name} "
            f"最新API失败：{exc}"
        )

    records = _merge_records(
        history,
        latest,
    )

    print(
        f"[{lottery_name}] "
        f"最终获得："
        f"{len(records)} 期"
    )

    if records:

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

    return records
