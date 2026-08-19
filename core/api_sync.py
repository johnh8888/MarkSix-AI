# -*- coding: utf-8 -*-

"""
六合彩 API 同步模块 V8.1

修复重点：

1. 修复 20260623 被错误识别为期号的问题
2. 严格识别六合彩期号 YYYYNNN
3. 历史接口优先
4. 最新 API 作为补充
5. 三彩种独立解析
6. 自动去重
7. SSL证书过期兼容
8. 支持多种 API 数据结构
9. 第7个号码保留为特别号码
"""

from __future__ import annotations

import json
import ssl
import urllib.request
import urllib.error

from typing import Any


# ============================================================
# API
# ============================================================

HISTORY_API = (
    "https://marksix6.net/index.php?api=1"
)

PRIMARY_API = (
    "https://marksix6.net/api/lottery_api.php"
)

BACKUP_API = (
    "https://api3.marksix6.net/lottery_api.php"
)


# ============================================================
# 彩种映射
# ============================================================

API_TYPES = {

    "新澳门彩": "newMacau",

    "老澳门彩": "oldMacau",

    "香港彩": "hk",

}


# ============================================================
# 请求头
# ============================================================

HEADERS = {

    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36",

    "Accept":
        "application/json,"
        "text/plain,"
        "*/*",

    "Connection":
        "close",

}


# ============================================================
# SSL兼容
# ============================================================

UNVERIFIED_CONTEXT = (
    ssl._create_unverified_context()
)


# ============================================================
# 请求 JSON
# ============================================================

def request_json(
    url: str,
    timeout: int = 25,
) -> Any:

    request = urllib.request.Request(
        url,
        headers=HEADERS,
        method="GET",
    )

    raw = None

    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            raw = response.read()

    except ssl.SSLCertVerificationError:

        print(
            "[WARN] SSL证书验证失败，"
            "启用兼容模式继续请求"
        )

        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=UNVERIFIED_CONTEXT,
        ) as response:

            raw = response.read()

    except urllib.error.URLError as exc:

        reason = getattr(
            exc,
            "reason",
            None,
        )

        if isinstance(
            reason,
            ssl.SSLCertVerificationError,
        ):

            print(
                "[WARN] SSL证书验证失败，"
                "启用兼容模式继续请求"
            )

            with urllib.request.urlopen(
                request,
                timeout=timeout,
                context=UNVERIFIED_CONTEXT,
            ) as response:

                raw = response.read()

        else:

            raise

    if raw is None:
        raise RuntimeError(
            "API没有返回数据"
        )

    text = raw.decode(
        "utf-8",
        errors="replace",
    ).strip()

    text = text.lstrip(
        "\ufeff"
    )

    # --------------------------------------------
    # 普通 JSON
    # --------------------------------------------

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        pass

    # --------------------------------------------
    # JSONP
    # --------------------------------------------

    json_text = text

    if (
        "(" in json_text
        and json_text.endswith(")")
    ):

        start = json_text.find("(")

        if start >= 0:

            json_text = (
                json_text[
                    start + 1:
                    -1
                ]
            )

            return json.loads(
                json_text
            )

    raise ValueError(
        "API返回内容不是有效JSON"
    )


# ============================================================
# 严格期号判断
# ============================================================

def normalize_issue(
    value: Any,
) -> str | None:

    if value is None:
        return None

    text = str(
        value
    ).strip()

    if not text:
        return None

    # --------------------------------------------------------
    # 六合正常期号：
    #
    # 2026231
    #
    # 年份4位 + 期次3位
    #
    # --------------------------------------------------------

    if not text.isdigit():
        return None

    if len(text) != 7:
        return None

    year = int(
        text[:4]
    )

    sequence = int(
        text[4:]
    )

    # 年份合理范围
    if year < 2000 or year > 2100:
        return None

    # 期次不能是日期月份/日期
    if sequence < 1 or sequence > 366:
        return None

    return text


# ============================================================
# 号码解析
# ============================================================

def normalize_numbers(
    value: Any,
) -> list[int] | None:

    # --------------------------------------------------------
    # list
    # --------------------------------------------------------

    if isinstance(
        value,
        (list, tuple),
    ):

        result = []

        for item in value:

            try:

                number = int(
                    item
                )

            except (
                TypeError,
                ValueError,
            ):

                return None

            if not 1 <= number <= 49:
                return None

            result.append(
                number
            )

        if (
            len(result) == 7
            and len(set(result)) == 7
        ):

            return result

        return None

    # --------------------------------------------------------
    # 字符串
    # --------------------------------------------------------

    if isinstance(
        value,
        str,
    ):

        text = value.strip()

        # 常见分隔符
        separators = (
            ",",
            " ",
            "|",
            "-",
            "/",
            ";",
        )

        for separator in separators:

            if separator not in text:
                continue

            parts = [
                x.strip()
                for x in text.split(
                    separator
                )
                if x.strip()
            ]

            if len(parts) != 7:
                continue

            try:

                result = [
                    int(x)
                    for x in parts
                ]

            except ValueError:

                continue

            if (
                all(
                    1 <= x <= 49
                    for x in result
                )
                and len(
                    set(result)
                ) == 7
            ):

                return result

    return None


# ============================================================
# 从 dict 提取期号
# ============================================================

def get_issue_from_dict(
    data: dict[str, Any],
) -> str | None:

    keys = (

        "expect",

        "issue",

        "issueNo",

        "period",

        "qihao",

        "drawNo",

        "drawIssue",

        "expectNo",

        "issue_id",

    )

    for key in keys:

        if key not in data:
            continue

        issue = normalize_issue(
            data.get(key)
        )

        if issue:
            return issue

    return None


# ============================================================
# 从 dict 提取号码
# ============================================================

def get_numbers_from_dict(
    data: dict[str, Any],
) -> list[int] | None:

    keys = (

        "numbers",

        "openCode",

        "open_code",

        "openNumbers",

        "code",

        "result",

        "openResult",

        "lotteryNumber",

    )

    for key in keys:

        if key not in data:
            continue

        numbers = normalize_numbers(
            data.get(key)
        )

        if numbers:
            return numbers

    # --------------------------------------------------------
    # openCode1 ~ openCode7
    # --------------------------------------------------------

    for prefix in (
        "openCode",
        "num",
        "number",
        "ball",
    ):

        values = []

        valid = True

        for index in range(
            1,
            8,
        ):

            key = (
                f"{prefix}{index}"
            )

            if key not in data:

                valid = False
                break

            try:

                number = int(
                    data[key]
                )

            except (
                TypeError,
                ValueError,
            ):

                valid = False
                break

            if not 1 <= number <= 49:

                valid = False
                break

            values.append(
                number
            )

        if (
            valid
            and len(values) == 7
            and len(set(values)) == 7
        ):

            return values

    return None


# ============================================================
# 判断是否是真实开奖记录
# ============================================================

def parse_record(
    data: Any,
) -> dict[str, Any] | None:

    if not isinstance(
        data,
        dict,
    ):
        return None

    issue = get_issue_from_dict(
        data
    )

    if not issue:
        return None

    numbers = get_numbers_from_dict(
        data
    )

    if not numbers:
        return None

    return {

        "issue": issue,

        "numbers": numbers,

    }


# ============================================================
# 递归寻找开奖记录
# ============================================================

def extract_records(
    node: Any,
    output: list[dict[str, Any]],
) -> None:

    if isinstance(
        node,
        dict,
    ):

        record = parse_record(
            node
        )

        if record:

            output.append(
                record
            )

        # ----------------------------------------------------
        # 优先遍历历史字段
        # ----------------------------------------------------

        priority_keys = []

        normal_keys = []

        for key in node:

            key_lower = str(
                key
            ).lower()

            if any(
                word in key_lower
                for word in (
                    "history",
                    "lottery_data",
                    "records",
                    "list",
                    "data",
                )
            ):

                priority_keys.append(
                    key
                )

            else:

                normal_keys.append(
                    key
                )

        visited = set()

        for key in (
            priority_keys
            + normal_keys
        ):

            if key in visited:
                continue

            visited.add(key)

            value = node.get(
                key
            )

            # ------------------------------------------------
            # 防止把普通日期字符串继续当成记录
            # ------------------------------------------------

            if isinstance(
                value,
                str,
            ):

                continue

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
# 标准化记录
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

        issue = record.get(
            "issue"
        )

        if not issue:
            continue

        # 再次严格过滤
        normalized = normalize_issue(
            issue
        )

        if not normalized:
            continue

        numbers = normalize_numbers(
            record.get(
                "numbers"
            )
        )

        if not numbers:
            continue

        unique[
            normalized
        ] = {

            "issue": normalized,

            "numbers": numbers,

        }

    result = list(
        unique.values()
    )

    result.sort(
        key=lambda x: int(
            x["issue"]
        )
    )

    return result


# ============================================================
# 从历史接口寻找指定彩种
# ============================================================

def find_lottery_nodes(
    payload: Any,
    lottery_name: str,
) -> list[Any]:

    targets = {

        "新澳门彩": (
            "newmacau",
            "new_macau",
            "新澳门",
            "澳门新",
            "xinmacau",
        ),

        "老澳门彩": (
            "oldmacau",
            "old_macau",
            "老澳门",
            "澳门老",
            "laomacau",
        ),

        "香港彩": (
            "hk",
            "hongkong",
            "hong_kong",
            "香港",
        ),

    }

    wanted = targets.get(
        lottery_name,
        (),
    )

    found = []

    def walk(
        node: Any,
    ):

        if isinstance(
            node,
            dict,
        ):

            # ------------------------------------------------
            # 当前节点彩种名称
            # ------------------------------------------------

            name_values = []

            for key in (
                "name",
                "type",
                "lottery",
                "lotteryType",
                "code",
                "id",
                "key",
            ):

                value = node.get(
                    key
                )

                if value is not None:

                    name_values.append(
                        str(value).lower()
                    )

            text = " ".join(
                name_values
            )

            matched = any(
                token.lower()
                in text
                for token in wanted
            )

            if matched:

                found.append(
                    node
                )

            for value in node.values():

                if isinstance(
                    value,
                    (dict, list),
                ):

                    walk(value)

        elif isinstance(
            node,
            list,
        ):

            for item in node:

                walk(item)

    walk(payload)

    return found


# ============================================================
# 历史接口
# ============================================================

def fetch_history(
    lottery_name: str,
) -> list[dict[str, Any]]:

    print(
        "[HISTORY] 请求历史总接口"
    )

    print(
        HISTORY_API
    )

    try:

        payload = request_json(
            HISTORY_API
        )

    except Exception as exc:

        print(
            f"[WARN] 历史接口失败：{exc}"
        )

        return []

    print(
        f"[HISTORY] {lottery_name} "
        f"开始筛选对应彩种"
    )

    # --------------------------------------------------------
    # 方案1：寻找对应彩种节点
    # --------------------------------------------------------

    nodes = find_lottery_nodes(
        payload,
        lottery_name,
    )

    if nodes:

        print(
            f"[{lottery_name}] "
            f"找到彩种节点："
            f"{len(nodes)}"
        )

        records = []

        for node in nodes:

            extract_records(
                node,
                records,
            )

        records = normalize_records(
            records
        )

        if records:

            print(
                f"[{lottery_name}] "
                f"历史接口解析："
                f"{len(records)} 期"
            )

            return records

    # --------------------------------------------------------
    # 方案2：如果接口本身已经只返回该彩种
    # --------------------------------------------------------

    records = normalize_records(
        payload
    )

    if records:

        print(
            f"[{lottery_name}] "
            f"历史接口通用解析："
            f"{len(records)} 期"
        )

    else:

        print(
            f"[{lottery_name}] "
            "历史接口没有解析到有效开奖记录"
        )

    return records


# ============================================================
# 最新 API
# ============================================================

def fetch_latest(
    lottery_name: str,
) -> list[dict[str, Any]]:

    api_type = API_TYPES[
        lottery_name
    ]

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

    for index, url in enumerate(
        urls,
        start=1,
    ):

        print(
            f"[{lottery_name}] "
            f"请求最新API 第{index}次"
        )

        print(url)

        try:

            payload = request_json(
                url
            )

            records = normalize_records(
                payload
            )

            if records:

                # 最新接口原则上只保留最近数据
                records.sort(
                    key=lambda x:
                    int(x["issue"])
                )

                latest = records[-1:]

                print(
                    f"[{lottery_name}] "
                    f"最新API解析："
                    f"{len(latest)} 期"
                )

                return latest

            print(
                f"[{lottery_name}] "
                "最新API没有有效记录"
            )

        except Exception as exc:

            print(
                f"[WARN] "
                f"{lottery_name} "
                f"最新API失败：{exc}"
            )

    return []


# ============================================================
# 合并记录
# ============================================================

def merge_records(
    history: list[dict[str, Any]],
    latest: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    unique = {}

    for record in (
        history + latest
    ):

        issue = normalize_issue(
            record.get(
                "issue"
            )
        )

        numbers = normalize_numbers(
            record.get(
                "numbers"
            )
        )

        if not issue:
            continue

        if not numbers:
            continue

        unique[
            issue
        ] = {

            "issue": issue,

            "numbers": numbers,

        }

    result = list(
        unique.values()
    )

    result.sort(
        key=lambda x:
        int(x["issue"])
    )

    return result


# ============================================================
# 对外接口
# ============================================================

def fetch_lottery(
    lottery_name: str,
) -> list[dict[str, Any]]:

    if lottery_name not in API_TYPES:

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

    # --------------------------------------------------------
    # 历史数据
    # --------------------------------------------------------

    history = fetch_history(
        lottery_name
    )

    # --------------------------------------------------------
    # 最新数据
    # --------------------------------------------------------

    latest = fetch_latest(
        lottery_name
    )

    # --------------------------------------------------------
    # 合并
    # --------------------------------------------------------

    final_records = merge_records(
        history,
        latest,
    )

    print(
        f"[{lottery_name}] "
        f"最终获得："
        f"{len(final_records)} 期"
    )

    if final_records:

        print(
            f"[{lottery_name}] "
            f"最早期号："
            f"{final_records[0]['issue']}"
        )

        print(
            f"[{lottery_name}] "
            f"最新期号："
            f"{final_records[-1]['issue']}"
        )

    else:

        print(
            f"[{lottery_name}] "
            "没有获得有效开奖数据"
        )

    return final_records
