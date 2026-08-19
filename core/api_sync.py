# -*- coding: utf-8 -*-

"""
MarkSix-AI V7.0
六合彩历史数据同步模块

功能：

1. 历史 API：
   https://marksix6.net/index.php?api=1

2. 最新 API：
   https://api3.marksix6.net/lottery_api.php?type=xxx

3. SSL 证书过期自动处理

4. 自动解析：
   lottery_data
   history
   records
   data
   list

5. 支持：
   新澳门彩
   老澳门彩
   香港彩

6. 自动去重期号

7. 自动补充最新一期

8. 返回完整历史记录

注意：
api3 单彩接口目前主要返回最新一期。
历史数据优先从 index.php?api=1 获取。
"""


from __future__ import annotations

import json
import re
import ssl
import urllib.request

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
# 三彩种
# ============================================================

API_TYPES = {

    "新澳门彩": "newMacau",

    "老澳门彩": "oldMacau",

    "香港彩": "hk",

}


# ============================================================
# 历史接口可能出现的名称
# ============================================================

LOTTERY_NAME_ALIASES = {

    "新澳门彩": {
        "新澳门彩",
        "新澳门六合彩",
        "新澳彩",
        "newMacau",
        "newmacau",
    },

    "老澳门彩": {
        "老澳门彩",
        "老澳门六合彩",
        "老澳彩",
        "oldMacau",
        "oldmacau",
    },

    "香港彩": {
        "香港彩",
        "香港六合彩",
        "hk",
        "hongkong",
        "hongkonglottery",
    },

}


# ============================================================
# HTTP Header
# ============================================================

HEADERS = {

    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36 "
        "MarkSix-AI/7.0",

    "Accept":
        "application/json,text/plain,*/*",

    "Cache-Control":
        "no-cache",

    "Pragma":
        "no-cache",

}


# ============================================================
# SSL
# ============================================================

UNVERIFIED_CONTEXT = (
    ssl._create_unverified_context()
)


# ============================================================
# HTTP 请求
# ============================================================

def request_bytes(
    url: str,
    timeout: int = 30,
) -> bytes:

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

            return response.read()

    except (
        ssl.SSLCertVerificationError,
        urllib.error.URLError,
    ) as exc:

        message = str(exc).lower()

        ssl_error = (

            isinstance(
                exc,
                ssl.SSLCertVerificationError,
            )

            or

            "certificate" in message

            or

            "ssl" in message

        )

        if not ssl_error:

            raise

        print(
            "[WARN] SSL证书验证失败，"
            "启用兼容模式继续请求"
        )

        with urllib.request.urlopen(

            request,

            timeout=timeout,

            context=UNVERIFIED_CONTEXT,

        ) as response:

            return response.read()


# ============================================================
# JSON 请求
# ============================================================

def request_json(
    url: str,
    timeout: int = 30,
) -> Any:

    raw = request_bytes(

        url,

        timeout=timeout,

    )

    text = raw.decode(

        "utf-8",

        errors="replace",

    ).strip()

    text = text.lstrip(
        "\ufeff"
    )

    if not text:

        raise ValueError(
            "API返回空内容"
        )

    # --------------------------------------------------------
    # 正常 JSON
    # --------------------------------------------------------

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        pass

    # --------------------------------------------------------
    # JSONP
    # --------------------------------------------------------

    jsonp_match = re.search(

        r"\((.*)\)\s*;?\s*$",

        text,

        flags=re.S,

    )

    if jsonp_match:

        try:

            return json.loads(
                jsonp_match.group(1)
            )

        except json.JSONDecodeError:

            pass

    # --------------------------------------------------------
    # 尝试截取 JSON
    # --------------------------------------------------------

    first_obj = text.find("{")
    last_obj = text.rfind("}")

    if (
        first_obj >= 0
        and last_obj > first_obj
    ):

        candidate = text[
            first_obj:last_obj + 1
        ]

        try:

            return json.loads(
                candidate
            )

        except json.JSONDecodeError:

            pass

    first_arr = text.find("[")
    last_arr = text.rfind("]")

    if (
        first_arr >= 0
        and last_arr > first_arr
    ):

        candidate = text[
            first_arr:last_arr + 1
        ]

        try:

            return json.loads(
                candidate
            )

        except json.JSONDecodeError:

            pass

    raise ValueError(
        "API返回内容不是有效JSON"
    )


# ============================================================
# 期号
# ============================================================

def normalize_issue(
    value: Any,
) -> str | None:

    if value is None:

        return None

    if isinstance(
        value,
        bool,
    ):

        return None

    text = str(
        value
    ).strip()

    if not text:

        return None

    # --------------------------------------------------------
    # 处理：
    # 2026231
    # 2026231期
    # 第2026231期
    # --------------------------------------------------------

    match = re.search(
        r"(\d{3,10})",
        text,
    )

    if not match:

        return None

    issue = match.group(1)

    if not (
        3 <= len(issue) <= 10
    ):

        return None

    return issue


# ============================================================
# 号码
# ============================================================

def normalize_numbers(
    value: Any,
) -> list[int] | None:

    # --------------------------------------------------------
    # list / tuple
    # --------------------------------------------------------

    if isinstance(
        value,
        (list, tuple),
    ):

        values = []

        for item in value:

            # 字典情况
            if isinstance(
                item,
                dict,
            ):

                for key in (
                    "number",
                    "num",
                    "value",
                ):

                    if key in item:

                        item = item[key]

                        break

            try:

                number = int(
                    str(item).strip()
                )

            except (
                TypeError,
                ValueError,
            ):

                return None

            if not (
                1 <= number <= 49
            ):

                return None

            values.append(
                number
            )

        if (
            len(values) == 7
            and len(set(values)) == 7
        ):

            return values

        return None

    # --------------------------------------------------------
    # 字符串
    # --------------------------------------------------------

    if isinstance(
        value,
        str,
    ):

        text = value.strip()

        if not text:

            return None

        # 找出所有数字
        matches = re.findall(
            r"\d{1,2}",
            text,
        )

        if len(matches) == 7:

            try:

                values = [
                    int(x)
                    for x in matches
                ]

            except ValueError:

                return None

            if (
                all(
                    1 <= x <= 49
                    for x in values
                )
                and len(
                    set(values)
                ) == 7
            ):

                return values

    return None


# ============================================================
# 判断是否像开奖号码
# ============================================================

def looks_like_numbers(
    value: Any,
) -> bool:

    return (
        normalize_numbers(value)
        is not None
    )


# ============================================================
# 从单条记录解析
# ============================================================

def parse_record(
    data: dict[str, Any],
) -> dict[str, Any] | None:

    issue = None

    # --------------------------------------------------------
    # 期号
    # --------------------------------------------------------

    issue_keys = (

        "expect",

        "issue",

        "issueNo",

        "issue_no",

        "period",

        "periodNo",

        "qihao",

        "drawNo",

        "drawIssue",

        "draw_issue",

        "lotteryNo",

        "number",

    )

    for key in issue_keys:

        if key not in data:

            continue

        issue = normalize_issue(
            data.get(key)
        )

        if issue:

            break

    # --------------------------------------------------------
    # 开奖号码
    # --------------------------------------------------------

    numbers = None

    number_keys = (

        "numbers",

        "openCode",

        "open_code",

        "openNumbers",

        "open_numbers",

        "code",

        "codes",

        "result",

        "results",

        "number",

        "nums",

    )

    for key in number_keys:

        if key not in data:

            continue

        numbers = normalize_numbers(
            data.get(key)
        )

        if numbers:

            break

    # --------------------------------------------------------
    # openCode1 ~ openCode7
    # num1 ~ num7
    # number1 ~ number7
    # --------------------------------------------------------

    if not numbers:

        for prefix in (
            "openCode",
            "open_code",
            "num",
            "number",
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
                        str(
                            data[key]
                        ).strip()
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    valid = False

                    break

                values.append(
                    number
                )

            if (
                valid
                and len(values) == 7
                and all(
                    1 <= x <= 49
                    for x in values
                )
                and len(
                    set(values)
                ) == 7
            ):

                numbers = values

                break

    if (
        issue
        and numbers
    ):

        result = {

            "issue": issue,

            "numbers": numbers,

        }

        # 可选字段
        for key in (
            "openTime",
            "open_time",
            "time",
            "drawTime",
        ):

            if key in data:

                result[
                    "open_time"
                ] = data[key]

                break

        return result

    return None


# ============================================================
# 从 history 字符串解析
#
# 支持：
#
# 2026231期：39 46 23 11 08 13 20
#
# 2026231:39,46,23,11,08,13,20
# ============================================================

def parse_history_text(
    text: str,
) -> list[dict[str, Any]]:

    records = []

    if not text:

        return records

    # --------------------------------------------------------
    # 每一期单独匹配
    # --------------------------------------------------------

    pattern = re.compile(

        r"(?P<issue>\d{3,10})"

        r"(?:\s*期)?"

        r"\s*[:：=\-]\s*"

        r"(?P<numbers>"

        r"(?:\d{1,2}"

        r"[\s,，|/\-]+"

        r"){6}"

        r"\d{1,2}"

        r")",

        flags=re.I,

    )

    for match in pattern.finditer(
        text
    ):

        issue = normalize_issue(
            match.group("issue")
        )

        numbers = normalize_numbers(
            match.group("numbers")
        )

        if (
            issue
            and numbers
        ):

            records.append({

                "issue": issue,

                "numbers": numbers,

            })

    return records


# ============================================================
# history 数组解析
# ============================================================

def parse_history_value(
    value: Any,
) -> list[dict[str, Any]]:

    records = []

    # --------------------------------------------------------
    # 字符串
    # --------------------------------------------------------

    if isinstance(
        value,
        str,
    ):

        # 先尝试 JSON
        try:

            parsed = json.loads(
                value
            )

            return parse_history_value(
                parsed
            )

        except Exception:

            pass

        records.extend(
            parse_history_text(
                value
            )
        )

        return records

    # --------------------------------------------------------
    # list
    # --------------------------------------------------------

    if isinstance(
        value,
        list,
    ):

        for item in value:

            if isinstance(
                item,
                dict,
            ):

                record = parse_record(
                    item
                )

                if record:

                    records.append(
                        record
                    )

                else:

                    # 继续递归
                    records.extend(
                        parse_any_node(
                            item
                        )
                    )

            elif isinstance(
                item,
                str,
            ):

                records.extend(
                    parse_history_text(
                        item
                    )
                )

        return records

    # --------------------------------------------------------
    # dict
    # --------------------------------------------------------

    if isinstance(
        value,
        dict,
    ):

        record = parse_record(
            value
        )

        if record:

            records.append(
                record
            )

        else:

            records.extend(
                parse_any_node(
                    value
                )
            )

    return records


# ============================================================
# 解析任意节点
# ============================================================

def parse_any_node(
    node: Any,
) -> list[dict[str, Any]]:

    records = []

    # --------------------------------------------------------
    # dict
    # --------------------------------------------------------

    if isinstance(
        node,
        dict,
    ):

        # 先自己尝试
        record = parse_record(
            node
        )

        if record:

            records.append(
                record
            )

        # history 优先
        priority_keys = []

        normal_keys = []

        for key in node.keys():

            key_lower = str(
                key
            ).lower()

            if any(
                token in key_lower
                for token in (
                    "history",
                    "lottery_data",
                    "records",
                    "record",
                    "list",
                    "data",
                    "result",
                )
            ):

                priority_keys.append(
                    key
                )

            else:

                normal_keys.append(
                    key
                )

        for key in (
            priority_keys
            + normal_keys
        ):

            # 自身已经作为记录解析
            # 就不要重复
            if key in (
                "numbers",
                "openCode",
                "open_code",
            ):

                continue

            value = node[key]

            if (
                "history"
                in str(key).lower()
            ):

                records.extend(
                    parse_history_value(
                        value
                    )
                )

            else:

                records.extend(
                    parse_any_node(
                        value
                    )
                )

    # --------------------------------------------------------
    # list
    # --------------------------------------------------------

    elif isinstance(
        node,
        list,
    ):

        for item in node:

            records.extend(
                parse_any_node(
                    item
                )
            )

    return records


# ============================================================
# 去重
# ============================================================

def deduplicate_records(
    records: list[
        dict[str, Any]
    ],
) -> list[
    dict[str, Any]
]:

    unique = {}

    for record in records:

        issue = normalize_issue(
            record.get("issue")
        )

        numbers = normalize_numbers(
            record.get("numbers")
        )

        if (
            not issue
            or not numbers
        ):

            continue

        # 后出现的数据覆盖前面的
        unique[issue] = {

            "issue": issue,

            "numbers": numbers,

        }

        if "open_time" in record:

            unique[
                issue
            ][
                "open_time"
            ] = record[
                "open_time"
            ]

    result = list(
        unique.values()
    )

    result.sort(

        key=lambda x:
        int(x["issue"])

    )

    return result


# ============================================================
# 获取历史总接口
# ============================================================

def fetch_all_history() -> Any:

    print(
        "[HISTORY] 请求历史总接口"
    )

    print(
        HISTORY_API
    )

    try:

        payload = request_json(

            HISTORY_API,

            timeout=40,

        )

        print(
            "[HISTORY] 历史接口请求成功"
        )

        return payload

    except Exception as exc:

        print(
            "[WARN] 历史接口失败："
            f"{exc}"
        )

        return None


# ============================================================
# 找到指定彩种
# ============================================================

def find_lottery_nodes(
    payload: Any,
    lottery_name: str,
) -> list[Any]:

    result = []

    aliases = {
        x.lower()
        for x in LOTTERY_NAME_ALIASES.get(
            lottery_name,
            {lottery_name},
        )
    }

    api_type = API_TYPES[
        lottery_name
    ].lower()

    # --------------------------------------------------------
    # 递归搜索
    # --------------------------------------------------------

    def walk(node: Any):

        if isinstance(
            node,
            dict,
        ):

            # 当前节点名称
            names = []

            for key in (
                "name",
                "lottery",
                "lotteryName",
                "type",
                "code",
                "key",
                "id",
            ):

                if key in node:

                    names.append(
                        str(
                            node[key]
                        ).strip().lower()
                    )

            matched = False

            for name in names:

                if (
                    name in aliases
                    or name == api_type
                    or api_type in name
                ):

                    matched = True

                    break

            if matched:

                result.append(
                    node
                )

            for value in node.values():

                walk(value)

        elif isinstance(
            node,
            list,
        ):

            for item in node:

                walk(item)

    walk(payload)

    return result


# ============================================================
# 从历史总接口提取指定彩种
# ============================================================

def extract_history_for_lottery(
    payload: Any,
    lottery_name: str,
) -> list[
    dict[str, Any]
]:

    records = []

    nodes = find_lottery_nodes(

        payload,

        lottery_name,

    )

    print(
        f"[{lottery_name}] "
        f"历史彩种节点："
        f"{len(nodes)}"
    )

    # --------------------------------------------------------
    # 正常情况
    # lottery_data:
    # [
    #   {
    #      name: 新澳门彩,
    #      history: [...]
    #   }
    # ]
    # --------------------------------------------------------

    for node in nodes:

        record = parse_record(
            node
        )

        if record:

            records.append(
                record
            )

        # history
        for key, value in node.items():

            key_lower = str(
                key
            ).lower()

            if (
                "history"
                in key_lower
            ):

                records.extend(
                    parse_history_value(
                        value
                    )
                )

    # --------------------------------------------------------
    # 如果名称匹配不到
    # 对整个 payload 再搜索
    # --------------------------------------------------------

    if not records:

        print(
            f"[{lottery_name}] "
            "名称节点未直接匹配，"
            "尝试全局解析"
        )

        all_records = parse_any_node(
            payload
        )

        records.extend(
            all_records
        )

    records = deduplicate_records(
        records
    )

    print(
        f"[{lottery_name}] "
        f"历史接口解析："
        f"{len(records)} 期"
    )

    return records


# ============================================================
# 获取最新一期
# ============================================================

def fetch_latest(
    lottery_name: str,
) -> list[
    dict[str, Any]
]:

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

            records = deduplicate_records(

                parse_any_node(
                    payload
                )

            )

            print(
                f"[{lottery_name}] "
                f"最新API解析："
                f"{len(records)} 期"
            )

            if records:

                return records

        except Exception as exc:

            print(
                "[WARN] 最新API失败："
                f"{exc}"
            )

    return []


# ============================================================
# 主函数
# ============================================================

def fetch_lottery(
    lottery_name: str,
) -> list[
    dict[str, Any]
]:

    if lottery_name not in API_TYPES:

        raise ValueError(
            f"不支持的彩种："
            f"{lottery_name}"
        )

    print(
        "=" * 70
    )

    print(
        f"正在同步："
        f"{lottery_name}"
    )

    print(
        "=" * 70
    )

    # ========================================================
    # 第一阶段
    # 历史 API
    # ========================================================

    history_records = []

    history_payload = (
        fetch_all_history()
    )

    if history_payload is not None:

        history_records = (
            extract_history_for_lottery(

                history_payload,

                lottery_name,

            )
        )

    # ========================================================
    # 第二阶段
    # 最新 API
    # ========================================================

    latest_records = fetch_latest(
        lottery_name
    )

    # ========================================================
    # 第三阶段
    # 合并
    # ========================================================

    combined = (
        history_records
        + latest_records
    )

    combined = deduplicate_records(
        combined
    )

    # ========================================================
    # 输出
    # ========================================================

    print(
        f"[{lottery_name}] "
        f"最终获得："
        f"{len(combined)} 期"
    )

    if combined:

        print(
            f"[{lottery_name}] "
            f"最早期号："
            f"{combined[0]['issue']}"
        )

        print(
            f"[{lottery_name}] "
            f"最新期号："
            f"{combined[-1]['issue']}"
        )

    else:

        print(
            f"[{lottery_name}] "
            "未获得有效开奖数据"
        )

    return combined


# ============================================================
# 三彩种批量同步
# ============================================================

def fetch_all_lotteries() -> dict[
    str,
    list[
        dict[str, Any]
    ]
]:

    result = {}

    for lottery_name in API_TYPES:

        result[
            lottery_name
        ] = fetch_lottery(
            lottery_name
        )

    return result


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "MarkSix-AI API历史同步测试"
    )

    print(
        "=" * 70
    )

    all_data = (
        fetch_all_lotteries()
    )

    for lottery_name, records in (
        all_data.items()
    ):

        print()
        print(
            lottery_name
        )

        print(
            f"记录数："
            f"{len(records)}"
        )

        if records:

            print(
                f"最新："
                f"{records[-1]['issue']}"
            )

            print(
                f"号码："
                f"{records[-1]['numbers']}"
            )

            print(
                "前5期："
            )

            for record in records[
                -5:
            ]:

                print(
                    record
                )

    print()
    print(
        "=" * 70
    )
