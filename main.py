# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V8.0

============================================================
核心规则
============================================================

1. 真实 API 数据
2. marksix6.net SSL 证书异常自动兼容
3. 历史开奖完整同步
4. SQLite 本地历史
5. 特别号码 = 每期开奖第 7 个号码
6. 号码预测只针对特别号码
7. 特别号码每期只能命中 1 个
8. 生肖：特别号码生肖，推荐 5 个
9. 单双：特别号码单双，只推 1 个
10. 大小：特别号码大小，只推 1 个
11. 波色：主推 / 次推 / 双色
12. Walk-Forward 历史回测
13. prediction.json
14. backtest.json
15. module_performance.json
16. 兼容 python main.py 直接运行

============================================================
"""

from __future__ import annotations

import json
import os
import ssl
import sqlite3
import urllib.request
import urllib.error

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# 基础目录
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 三彩种
# ============================================================

LOTTERIES = [
    "新澳门彩",
    "老澳门彩",
    "香港彩",
]


DB_FILES = {
    "新澳门彩": DATA_DIR / "new_macau.db",
    "老澳门彩": DATA_DIR / "old_macau.db",
    "香港彩": DATA_DIR / "hk.db",
}


# ============================================================
# API
# ============================================================

PRIMARY_HISTORY_API = (
    "https://marksix6.net/index.php?api=1"
)

PRIMARY_API = (
    "https://marksix6.net/api/lottery_api.php"
)

BACKUP_API = (
    "https://api3.marksix6.net/lottery_api.php"
)


API_TYPES = {
    "新澳门彩": "newMacau",
    "老澳门彩": "oldMacau",
    "香港彩": "hk",
}


HEADERS = {
    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36",

    "Accept":
        "application/json,text/plain,*/*",

    "Connection":
        "close",
}


# ============================================================
# SSL
# ============================================================

UNVERIFIED_CONTEXT = ssl._create_unverified_context()


# ============================================================
# 波色
# ============================================================

RED = {
    1, 2, 7, 8, 12, 13, 18, 19,
    23, 24, 29, 30, 34, 35, 40,
    45, 46,
}

BLUE = {
    3, 4, 9, 10, 14, 15, 20,
    25, 26, 31, 36, 37, 41,
    42, 47, 48,
}

GREEN = {
    5, 6, 11, 16, 17, 21, 22,
    27, 28, 32, 33, 38, 39,
    43, 44, 49,
}


WAVES = [
    "红",
    "蓝",
    "绿",
]


# ============================================================
# 生肖
# ============================================================

ANIMALS = [
    "鼠",
    "牛",
    "虎",
    "兔",
    "龙",
    "蛇",
    "马",
    "羊",
    "猴",
    "鸡",
    "狗",
    "猪",
]


# ============================================================
# HTTP JSON
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

    # --------------------------------------------------------
    # 第一阶段：正常 SSL
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # 第二阶段：忽略证书验证
        # ----------------------------------------------------

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

    text = text.lstrip("\ufeff")

    if not text:
        raise RuntimeError(
            "API返回空数据"
        )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        pass

    # --------------------------------------------------------
    # 简单 JSONP
    # --------------------------------------------------------

    candidates = [
        text,
        text[text.find("(") + 1:text.rfind(")")]
        if "(" in text and ")" in text
        else "",
    ]

    for candidate in candidates:

        candidate = candidate.strip()

        if not candidate:
            continue

        try:
            return json.loads(candidate)
        except Exception:
            continue

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

    text = str(value).strip()

    if not text:
        return None

    # 有些接口可能返回浮点字符串
    if text.endswith(".0"):
        text = text[:-2]

    if not text.isdigit():
        return None

    if not 3 <= len(text) <= 10:
        return None

    return text


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

        numbers = []

        for item in value:

            try:
                number = int(item)
            except Exception:
                return None

            if not 1 <= number <= 49:
                return None

            numbers.append(number)

        if (
            len(numbers) == 7
            and len(set(numbers)) == 7
        ):
            return numbers

    # --------------------------------------------------------
    # 字符串
    # --------------------------------------------------------

    if isinstance(value, str):

        text = value.strip()

        # 统一常见分隔符
        for separator in (
            ",",
            " ",
            "|",
            "-",
            "/",
            "_",
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

            except Exception:
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
# 波色
# ============================================================

def get_wave(
    number: int,
) -> str:

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return ""


# ============================================================
# 大小
# ============================================================

def get_size(
    number: int,
) -> str:

    return "大" if number >= 25 else "小"


# ============================================================
# 单双
# ============================================================

def get_odd_even(
    number: int,
) -> str:

    return "单" if number % 2 else "双"


# ============================================================
# 生肖
# ============================================================

def zodiac_by_year(
    number: int,
    year: int,
) -> str:

    # 2024 = 龙
    #
    # animals index:
    # 鼠0 牛1 虎2 兔3 龙4 蛇5 马6 ...
    #
    # 每年整体顺移一位
    # 号码按 1~49 循环对应生肖

    year_index = (
        4 + (year - 2024)
    ) % 12

    number_index = (
        number - 1
    ) % 12

    return ANIMALS[
        (year_index - number_index) % 12
    ]


def get_zodiac(
    number: int,
    issue: str,
) -> str:

    try:

        year = int(
            str(issue)[:4]
        )

    except Exception:

        year = 2026

    return zodiac_by_year(
        number,
        year,
    )


# ============================================================
# 从单条记录解析
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

    numbers = None

    number_keys = (
        "numbers",
        "openCode",
        "open_code",
        "openNumbers",
        "code",
        "result",
        "openNumber",
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
    # --------------------------------------------------------

    if not numbers:

        for prefix in (
            "openCode",
            "open_code",
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

                except Exception:

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

    if issue and numbers:

        return {
            "issue": issue,
            "numbers": numbers,
        }

    return None


# ============================================================
# 递归解析
# ============================================================

def extract_records(
    node: Any,
    output: list[dict[str, Any]],
) -> None:

    if isinstance(node, dict):

        record = parse_record(node)

        if record:
            output.append(record)

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
                    "rows",
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

    elif isinstance(node, list):

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

        if issue not in unique:

            unique[issue] = {
                "issue": issue,
                "numbers": record[
                    "numbers"
                ],
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
# 历史 API
# ============================================================

def fetch_history_api(
    lottery_name: str,
) -> list[dict[str, Any]]:

    print(
        "[HISTORY] 请求历史总接口"
    )

    print(
        PRIMARY_HISTORY_API
    )

    try:

        payload = request_json(
            PRIMARY_HISTORY_API
        )

    except Exception as exc:

        print(
            f"[WARN] 历史接口失败：{exc}"
        )

        return []

    records = normalize_records(
        payload
    )

    print(
        f"[{lottery_name}] "
        f"历史接口解析："
        f"{len(records)} 期"
    )

    return records


# ============================================================
# 最新 API
# ============================================================

def fetch_latest_api(
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

            print(
                f"[{lottery_name}] "
                f"最新API解析："
                f"{len(records)} 期"
            )

            if records:
                return records

        except Exception as exc:

            print(
                f"[WARN] "
                f"最新API失败：{exc}"
            )

    return []


# ============================================================
# 获取完整开奖历史
# ============================================================

def fetch_lottery(
    lottery_name: str,
) -> list[dict[str, Any]]:

    print(
        "=" * 70
    )

    print(
        f"正在同步：{lottery_name}"
    )

    print(
        "=" * 70
    )

    history_records = (
        fetch_history_api(
            lottery_name
        )
    )

    latest_records = (
        fetch_latest_api(
            lottery_name
        )
    )

    merged = {}

    for record in history_records:
        merged[
            record["issue"]
        ] = record

    for record in latest_records:
        merged[
            record["issue"]
        ] = record

    result = list(
        merged.values()
    )

    result.sort(
        key=lambda x: int(
            x["issue"]
        )
    )

    print(
        f"[{lottery_name}] "
        f"最终获得："
        f"{len(result)} 期"
    )

    if result:

        print(
            f"[{lottery_name}] "
            f"最早期号："
            f"{result[0]['issue']}"
        )

        print(
            f"[{lottery_name}] "
            f"最新期号："
            f"{result[-1]['issue']}"
        )

    return result


# ============================================================
# SQLite
# ============================================================

def get_connection(
    lottery_name: str,
):

    db_path = DB_FILES[
        lottery_name
    ]

    conn = sqlite3.connect(
        str(db_path)
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS draws (
            issue TEXT PRIMARY KEY,
            numbers TEXT NOT NULL
        )
        """
    )

    conn.commit()

    return conn


def init_db() -> None:

    for lottery in LOTTERIES:

        conn = get_connection(
            lottery
        )

        conn.close()


def save_records(
    lottery_name: str,
    records: list[dict[str, Any]],
) -> int:

    if not records:
        return 0

    conn = get_connection(
        lottery_name
    )

    added = 0

    try:

        for record in records:

            issue = str(
                record["issue"]
            )

            numbers = record[
                "numbers"
            ]

            if len(numbers) != 7:
                continue

            numbers_text = ",".join(
                str(x)
                for x in numbers
            )

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO draws
                (
                    issue,
                    numbers
                )
                VALUES (?, ?)
                """,
                (
                    issue,
                    numbers_text,
                ),
            )

            if cursor.rowcount > 0:
                added += 1

        conn.commit()

    finally:

        conn.close()

    return added


def load_records(
    lottery_name: str,
) -> list[dict[str, Any]]:

    conn = get_connection(
        lottery_name
    )

    try:

        rows = conn.execute(
            """
            SELECT
                issue,
                numbers
            FROM draws
            ORDER BY
                CAST(issue AS INTEGER)
            """
        ).fetchall()

    finally:

        conn.close()

    result = []

    for issue, numbers in rows:

        try:

            nums = [
                int(x)
                for x in numbers.split(",")
            ]

        except Exception:

            continue

        if len(nums) != 7:
            continue

        if len(set(nums)) != 7:
            continue

        if not all(
            1 <= x <= 49
            for x in nums
        ):
            continue

        result.append(
            {
                "issue": str(issue),
                "numbers": nums,
            }
        )

    return result


# ============================================================
# 特别号码历史统计
#
# 重要：
# 这里只使用第7个号码。
# ============================================================

def special_number_counter(
    history: list[dict[str, Any]],
    window: int = 100,
) -> Counter:

    counter = Counter()

    rows = history[
        -window:
    ]

    for row in rows:

        numbers = row.get(
            "numbers",
            [],
        )

        if len(numbers) != 7:
            continue

        special = numbers[6]

        if 1 <= special <= 49:
            counter[special] += 1

    return counter


# ============================================================
# 特别号码预测
# ============================================================

def predict_special_numbers(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    # 最近100期
    counter100 = (
        special_number_counter(
            history,
            100,
        )
    )

    # 最近50期
    counter50 = (
        special_number_counter(
            history,
            50,
        )
    )

    # 最近20期
    counter20 = (
        special_number_counter(
            history,
            20,
        )
    )

    scores = {}

    for number in range(
        1,
        50,
    ):

        score = (

            counter100.get(
                number,
                0,
            )
            * 1.0

            +

            counter50.get(
                number,
                0,
            )
            * 1.5

            +

            counter20.get(
                number,
                0,
            )
            * 2.0

        )

        scores[number] = score

    ranking = sorted(
        range(1, 50),
        key=lambda x: (
            -scores[x],
            -counter20.get(
                x,
                0,
            ),
            -counter50.get(
                x,
                0,
            ),
            x,
        ),
    )

    return {

        "top5":
            ranking[:5],

        "top10":
            ranking[:10],

        "top12":
            ranking[:12],

        "scores":
            scores,

    }


# ============================================================
# 属性统计
# ============================================================

def attribute_counter(
    history: list[dict[str, Any]],
    field: str,
    window: int = 50,
) -> Counter:

    counter = Counter()

    for row in history[
        -window:
    ]:

        numbers = row.get(
            "numbers",
            [],
        )

        issue = row.get(
            "issue",
            "",
        )

        if len(numbers) != 7:
            continue

        # 只看第7个特别号码
        special = numbers[6]

        if field == "wave":

            value = get_wave(
                special
            )

        elif field == "size":

            value = get_size(
                special
            )

        elif field == "odd_even":

            value = get_odd_even(
                special
            )

        elif field == "zodiac":

            value = get_zodiac(
                special,
                issue,
            )

        else:

            value = ""

        if value:
            counter[value] += 1

    return counter


# ============================================================
# 生肖预测
#
# 必须推荐5个
# ============================================================

def predict_zodiac(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = attribute_counter(
        history,
        "zodiac",
        100,
    )

    ranking = [
        item[0]
        for item in counter.most_common()
    ]

    # 防止历史数据异常导致不足5个
    for animal in ANIMALS:

        if animal not in ranking:
            ranking.append(animal)

    top5 = ranking[:5]

    return {

        "main":
            top5[0],

        "secondary":
            top5[1],

        "top5":
            top5,

        "double":
            top5,

    }


# ============================================================
# 单双预测
#
# 只推一个
# ============================================================

def predict_single_attribute(
    history: list[dict[str, Any]],
    field: str,
) -> dict[str, Any]:

    counter = attribute_counter(
        history,
        field,
        100,
    )

    if not counter:

        return {
            "main": "",
            "secondary": "",
            "double": [],
        }

    ranking = [
        item[0]
        for item in counter.most_common()
    ]

    main = ranking[0]

    secondary = (
        ranking[1]
        if len(ranking) > 1
        else ""
    )

    return {

        "main":
            main,

        "secondary":
            secondary,

        # 这里不再作为预测双推
        "double":
            [main],

    }


# ============================================================
# 波色预测
#
# 主推 / 次推 / 双色
# ============================================================

def predict_wave(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = attribute_counter(
        history,
        "wave",
        100,
    )

    ranking = [
        item[0]
        for item in counter.most_common()
    ]

    for wave in WAVES:

        if wave not in ranking:
            ranking.append(wave)

    main = ranking[0]
    secondary = ranking[1]

    return {

        "main":
            main,

        "secondary":
            secondary,

        "double":
            [
                main,
                secondary,
            ],

    }


# ============================================================
# 属性预测总函数
# ============================================================

def predict_attributes(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    return {

        "zodiac":
            predict_zodiac(
                history
            ),

        "odd_even":
            predict_single_attribute(
                history,
                "odd_even",
            ),

        "size":
            predict_single_attribute(
                history,
                "size",
            ),

        "wave":
            predict_wave(
                history
            ),

    }


# ============================================================
# 下一期期号
# ============================================================

def next_issue(
    issue: str,
) -> str:

    try:

        return str(
            int(issue) + 1
        )

    except Exception:

        return ""


# ============================================================
# 单次预测评价
#
# 注意：
# actual 第7个号码 = 唯一特别号码
# ============================================================

def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:

    numbers = actual.get(
        "numbers",
        [],
    )

    if len(numbers) != 7:
        return {}

    issue = actual.get(
        "issue",
        "",
    )

    # --------------------------------------------------------
    # 第7个号码才是特别号码
    # --------------------------------------------------------

    special = numbers[6]

    result = {}

    special_top5 = set(
        prediction.get(
            "top5",
            [],
        )
    )

    special_top10 = set(
        prediction.get(
            "top10",
            [],
        )
    )

    special_top12 = set(
        prediction.get(
            "top12",
            [],
        )
    )

    # --------------------------------------------------------
    # 特别号码
    #
    # 每期只有一个特别号码
    # 因此命中数只能是 0 或 1
    # --------------------------------------------------------

    result[
        "special_top5_hit"
    ] = int(
        special in special_top5
    )

    result[
        "special_top10_hit"
    ] = int(
        special in special_top10
    )

    result[
        "special_top12_hit"
    ] = int(
        special in special_top12
    )

    # --------------------------------------------------------
    # 特别号码属性
    # --------------------------------------------------------

    zodiac = get_zodiac(
        special,
        issue,
    )

    odd_even = get_odd_even(
        special
    )

    size = get_size(
        special
    )

    wave = get_wave(
        special
    )

    attrs = prediction[
        "attributes"
    ]

    # --------------------------------------------------------
    # 生肖5推
    # --------------------------------------------------------

    zodiac_top5 = attrs[
        "zodiac"
    ].get(
        "top5",
        [],
    )

    result[
        "zodiac_main"
    ] = int(
        zodiac
        ==
        attrs["zodiac"].get(
            "main",
            "",
        )
    )

    result[
        "zodiac_top5"
    ] = int(
        zodiac
        in zodiac_top5
    )

    # --------------------------------------------------------
    # 单双：只推一个
    # --------------------------------------------------------

    result[
        "odd_even_main"
    ] = int(
        odd_even
        ==
        attrs["odd_even"].get(
            "main",
            "",
        )
    )

    # --------------------------------------------------------
    # 大小：只推一个
    # --------------------------------------------------------

    result[
        "size_main"
    ] = int(
        size
        ==
        attrs["size"].get(
            "main",
            "",
        )
    )

    # --------------------------------------------------------
    # 波色
    # --------------------------------------------------------

    result[
        "wave_main"
    ] = int(
        wave
        ==
        attrs["wave"].get(
            "main",
            "",
        )
    )

    result[
        "wave_secondary"
    ] = int(
        wave
        ==
        attrs["wave"].get(
            "secondary",
            "",
        )
    )

    result[
        "wave_double"
    ] = int(
        wave
        in attrs["wave"].get(
            "double",
            [],
        )
    )

    return result


# ============================================================
# 百分比
# ============================================================

def hit_rate(
    hits: int,
    total: int,
) -> float:

    if total <= 0:
        return 0.0

    return round(
        hits / total * 100,
        2,
    )


# ============================================================
# Walk-Forward
# ============================================================

def walk_forward(
    history: list[dict[str, Any]],
    minimum_train: int = 30,
) -> dict[str, Any]:

    evaluations = []

    if len(history) <= minimum_train:

        return {

            "method":
                "Walk-Forward",

            "samples":
                0,

            "status":
                "历史数据不足",

            "performance":
                {},

        }

    for index in range(
        minimum_train,
        len(history),
    ):

        train = history[
            :index
        ]

        actual = history[
            index
        ]

        special_prediction = (
            predict_special_numbers(
                train
            )
        )

        attributes = (
            predict_attributes(
                train
            )
        )

        prediction = {

            "top5":
                special_prediction[
                    "top5"
                ],

            "top10":
                special_prediction[
                    "top10"
                ],

            "top12":
                special_prediction[
                    "top12"
                ],

            "attributes":
                attributes,

        }

        evaluation = (
            evaluate_prediction(
                prediction,
                actual,
            )
        )

        if evaluation:
            evaluations.append(
                evaluation
            )

    performance = (
        calculate_performance(
            evaluations
        )
    )

    return {

        "method":
            "Walk-Forward",

        "samples":
            len(evaluations),

        "performance":
            performance,

        "status":
            "正常",

    }


# ============================================================
# 命中率计算
# ============================================================

def calculate_performance(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(evaluations)

    if total == 0:

        return {

            "samples":
                0,

            "status":
                "历史数据不足",

        }

    def count(
        key: str,
    ) -> int:

        return sum(
            int(
                item.get(
                    key,
                    0,
                )
            )
            for item in evaluations
        )

    # --------------------------------------------------------
    # 特别号码平均命中数
    #
    # 最大只能为1
    # --------------------------------------------------------

    top5_hits = count(
        "special_top5_hit"
    )

    top10_hits = count(
        "special_top10_hit"
    )

    top12_hits = count(
        "special_top12_hit"
    )

    return {

        "samples":
            total,

        "special_number": {

            "top5":
                hit_rate(
                    top5_hits,
                    total,
                ),

            "top10":
                hit_rate(
                    top10_hits,
                    total,
                ),

            "top12":
                hit_rate(
                    top12_hits,
                    total,
                ),

            "top5_average_hits":
                round(
                    top5_hits / total,
                    4,
                ),

            "top10_average_hits":
                round(
                    top10_hits / total,
                    4,
                ),

            "top12_average_hits":
                round(
                    top12_hits / total,
                    4,
                ),

        },

        "zodiac": {

            "main":
                hit_rate(
                    count(
                        "zodiac_main"
                    ),
                    total,
                ),

            "top5":
                hit_rate(
                    count(
                        "zodiac_top5"
                    ),
                    total,
                ),

        },

        "odd_even": {

            "main":
                hit_rate(
                    count(
                        "odd_even_main"
                    ),
                    total,
                ),

        },

        "size": {

            "main":
                hit_rate(
                    count(
                        "size_main"
                    ),
                    total,
                ),

        },

        "wave": {

            "main":
                hit_rate(
                    count(
                        "wave_main"
                    ),
                    total,
                ),

            "secondary":
                hit_rate(
                    count(
                        "wave_secondary"
                    ),
                    total,
                ),

            "double":
                hit_rate(
                    count(
                        "wave_double"
                    ),
                    total,
                ),

        },

        "status":
            "正常",

    }


# ============================================================
# 单个彩种分析
# ============================================================

def analyze(
    lottery_name: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    history = sorted(
        history,
        key=lambda x: int(
            x.get(
                "issue",
                0,
            )
        ),
    )

    if not history:

        return {

            "lottery":
                lottery_name,

            "success":
                False,

            "history_size":
                0,

            "candidates":
                [],

        }

    latest = history[-1]

    latest_issue = str(
        latest.get(
            "issue",
            "",
        )
    )

    prediction_issue = (
        next_issue(
            latest_issue
        )
    )

    # --------------------------------------------------------
    # 特别号码预测
    # --------------------------------------------------------

    special_prediction = (
        predict_special_numbers(
            history
        )
    )

    # --------------------------------------------------------
    # 属性预测
    # --------------------------------------------------------

    attributes = (
        predict_attributes(
            history
        )
    )

    # --------------------------------------------------------
    # Walk Forward
    # --------------------------------------------------------

    walk = walk_forward(
        history
    )

    performance = walk.get(
        "performance",
        {},
    )

    top5 = special_prediction[
        "top5"
    ]

    top10 = special_prediction[
        "top10"
    ]

    top12 = special_prediction[
        "top12"
    ]

    return {

        "lottery":
            lottery_name,

        "success":
            True,

        "latest_issue":
            latest_issue,

        "latest_draw_issue":
            latest_issue,

        "latest_numbers":
            latest.get(
                "numbers",
                [],
            ),

        "special_number":
            latest.get(
                "numbers",
                [],
            )[-1],

        "prediction_issue":
            prediction_issue,

        "next_prediction_issue":
            prediction_issue,

        "history_size":
            len(history),

        # ----------------------------------------------------
        # candidates 必须保留
        # ----------------------------------------------------

        "candidates":
            top12,

        "special_candidates":
            top12,

        "top5":
            top5,

        "top10":
            top10,

        "top12":
            top12,

        "attributes":
            attributes,

        "performance":
            performance,

        "backtest":
            walk,

    }


# ============================================================
# 打印
# ============================================================

def print_result(
    result: dict[str, Any],
) -> None:

    print(
        "=" * 70
    )

    print(
        f"【{result['lottery']}】"
    )

    print(
        "=" * 70
    )

    print(
        f"历史期数："
        f"{result['history_size']}"
    )

    print(
        f"最新开奖期数："
        f"{result['latest_issue']}"
    )

    print(
        f"预测下一期期数："
        f"{result['prediction_issue']}"
    )

    latest_numbers = result.get(
        "latest_numbers",
        [],
    )

    print(
        "最新开奖号码："
        +
        " ".join(
            f"{x:02d}"
            for x in latest_numbers
        )
    )

    if latest_numbers:

        print(
            f"特别号码："
            f"{latest_numbers[-1]:02d}"
        )

    print()

    # ========================================================
    # 特别号码
    # ========================================================

    print(
        "【下一期特别号码预测】"
    )

    print(
        "Top5："
        +
        " ".join(
            f"{x:02d}"
            for x in result["top5"]
        )
    )

    print(
        "Top10："
        +
        " ".join(
            f"{x:02d}"
            for x in result["top10"]
        )
    )

    print(
        "Top12："
        +
        " ".join(
            f"{x:02d}"
            for x in result["top12"]
        )
    )

    print(
        "说明："
        "以上号码只针对第7个特别号码，"
        "每期开奖最多命中1个。"
    )

    print()

    # ========================================================
    # 属性
    # ========================================================

    attrs = result[
        "attributes"
    ]

    print(
        "【下一期特别号码属性预测】"
    )

    zodiac = attrs[
        "zodiac"
    ]

    print(
        "生肖："
        f"推荐5个 "
        f"{' + '.join(zodiac['top5'])}"
    )

    odd_even = attrs[
        "odd_even"
    ]

    print(
        "单双："
        f"主推 {odd_even['main']}"
    )

    size = attrs[
        "size"
    ]

    print(
        "大小："
        f"主推 {size['main']}"
    )

    wave = attrs[
        "wave"
    ]

    print(
        "波色："
        f"主推 {wave['main']} "
        f"次推 {wave['secondary']} "
        f"双色 {' + '.join(wave['double'])}"
    )

    print()

    # ========================================================
    # 命中率
    # ========================================================

    performance = result.get(
        "performance",
        {},
    )

    if performance:

        print(
            "【Walk-Forward 历史命中率】"
        )

        print(
            f"验证期数："
            f"{performance.get('samples', 0)}"
        )

        special = performance.get(
            "special_number",
            {},
        )

        print(
            "【特别号码命中】"
        )

        print(
            f"Top5："
            f"{special.get('top5', 0)}%"
        )

        print(
            f"Top10："
            f"{special.get('top10', 0)}%"
        )

        print(
            f"Top12："
            f"{special.get('top12', 0)}%"
        )

        print(
            f"Top5平均命中数："
            f"{special.get('top5_average_hits', 0)}"
        )

        print(
            f"Top10平均命中数："
            f"{special.get('top10_average_hits', 0)}"
        )

        print(
            f"Top12平均命中数："
            f"{special.get('top12_average_hits', 0)}"
        )

        zodiac_perf = performance.get(
            "zodiac",
            {},
        )

        print(
            "【生肖命中】"
        )

        print(
            f"5生肖："
            f"{zodiac_perf.get('top5', 0)}%"
        )

        odd_perf = performance.get(
            "odd_even",
            {},
        )

        print(
            "【单双命中】"
        )

        print(
            f"主推："
            f"{odd_perf.get('main', 0)}%"
        )

        size_perf = performance.get(
            "size",
            {},
        )

        print(
            "【大小命中】"
        )

        print(
            f"主推："
            f"{size_perf.get('main', 0)}%"
        )

        wave_perf = performance.get(
            "wave",
            {},
        )

        print(
            "【波色命中】"
        )

        print(
            f"主推："
            f"{wave_perf.get('main', 0)}%"
        )

        print(
            f"次推："
            f"{wave_perf.get('secondary', 0)}%"
        )

        print(
            f"双色："
            f"{wave_perf.get('double', 0)}%"
        )

    print()


# ============================================================
# 保存 JSON
# ============================================================

def save_json(
    filename: str,
    data: Any,
) -> None:

    path = OUTPUT_DIR / filename

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"✅ {filename} 已保存："
        f"{path}"
    )


# ============================================================
# 主程序
# ============================================================

def run_system() -> None:

    print(
        "=" * 70
    )

    print(
        "六合彩综合预测系统"
    )

    print(
        "真实数据 + SQLite + "
        "特别号码 + 生肖5推 + "
        "单双大小单推 + 波色双推"
    )

    print(
        "版本：V8.0 REAL DATA SPECIAL HIT FINAL"
    )

    print(
        f"启动时间："
        f"{datetime.now().isoformat()}"
    )

    print(
        "=" * 70
    )

    init_db()

    all_results = {}

    all_backtests = {}

    all_modules = {}

    # ========================================================
    # 三彩种
    # ========================================================

    for lottery in LOTTERIES:

        print(
            "=" * 70
        )

        print(
            f"正在更新：{lottery}"
        )

        print(
            "=" * 70
        )

        try:

            records = fetch_lottery(
                lottery
            )

            added = save_records(
                lottery,
                records,
            )

            print(
                f"[{lottery}] "
                f"本次新增："
                f"{added} 期"
            )

            history = load_records(
                lottery
            )

            print(
                f"[{lottery}] "
                f"当前数据库历史："
                f"{len(history)} 期"
            )

            result = analyze(
                lottery,
                history,
            )

            print_result(
                result
            )

            all_results[
                lottery
            ] = result

            all_backtests[
                lottery
            ] = result.get(
                "backtest",
                {},
            )

            all_modules[
                lottery
            ] = result.get(
                "performance",
                {},
            )

        except Exception as exc:

            print(
                f"[ERROR] "
                f"{lottery}: "
                f"{exc}"
            )

            all_results[
                lottery
            ] = {

                "lottery":
                    lottery,

                "success":
                    False,

                "error":
                    str(exc),

                "candidates":
                    [],

                "latest_issue":
                    "",

                "prediction_issue":
                    "",

            }

    # ========================================================
    # prediction.json
    # ========================================================

    prediction = {

        "version":
            "V8.0 REAL DATA SPECIAL HIT FINAL",

        "generated_at":
            datetime.now().isoformat(),

        "rules": {

            "number":
                "只预测第7个特别号码，每期最多命中1个",

            "zodiac":
                "特别号码生肖推荐5个",

            "odd_even":
                "特别号码单双只推1个",

            "size":
                "特别号码大小只推1个",

            "wave":
                "特别号码波色主推+次推+双色",

        },

        "note":
            "历史Walk-Forward统计，不代表未来真实中奖概率。",

        "lotteries":
            all_results,

    }

    save_json(
        "prediction.json",
        prediction,
    )

    # ========================================================
    # backtest.json
    # ========================================================

    backtest = {

        "version":
            "V8.0",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries":
            all_backtests,

    }

    save_json(
        "backtest.json",
        backtest,
    )

    # ========================================================
    # module_performance.json
    # ========================================================

    module_performance = {

        "version":
            "V8.0",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries":
            all_modules,

    }

    save_json(
        "module_performance.json",
        module_performance,
    )

    # ========================================================
    # 最终摘要
    # ========================================================

    print(
        "=" * 70
    )

    print(
        "三彩种分析完成"
    )

    for name, result in (
        all_results.items()
    ):

        if not result.get(
            "success",
            False,
        ):
            continue

        print(
            f"{name}："
            f"最新开奖第 "
            f"{result.get('latest_issue', '')} "
            f"期"
        )

        print(
            f"{name}："
            f"预测下一期第 "
            f"{result.get('prediction_issue', '')} "
            f"期"
        )

        candidates = result.get(
            "candidates",
            [],
        )

        print(
            f"{name}："
            "特别号码候选 "
            +
            " ".join(
                f"{x:02d}"
                for x in candidates
            )
        )

        attrs = result.get(
            "attributes",
            {},
        )

        zodiac = attrs.get(
            "zodiac",
            {},
        )

        print(
            f"{name}："
            "生肖5推 "
            +
            " ".join(
                zodiac.get(
                    "top5",
                    [],
                )
            )
        )

        print(
            f"{name}："
            "单双主推 "
            +
            str(
                attrs.get(
                    "odd_even",
                    {},
                ).get(
                    "main",
                    "",
                )
            )
        )

        print(
            f"{name}："
            "大小主推 "
            +
            str(
                attrs.get(
                    "size",
                    {},
                ).get(
                    "main",
                    "",
                )
            )
        )

        wave = attrs.get(
            "wave",
            {},
        )

        print(
            f"{name}："
            f"波色主推 "
            f"{wave.get('main', '')} "
            f"/ 次推 "
            f"{wave.get('secondary', '')} "
            f"/ 双色 "
            f"{' + '.join(wave.get('double', []))}"
        )

        performance = result.get(
            "performance",
            {},
        )

        special = performance.get(
            "special_number",
            {},
        )

        print(
            f"{name}："
            f"特别号码Top5命中率 "
            f"{special.get('top5', 0)}%"
        )

        print(
            f"{name}："
            f"特别号码Top10命中率 "
            f"{special.get('top10', 0)}%"
        )

        print(
            f"{name}："
            f"特别号码Top12命中率 "
            f"{special.get('top12', 0)}%"
        )

    print(
        "=" * 70
    )

    print(
        "说明："
        "号码预测仅针对每期第7个特别号码；"
        "生肖仅针对特别号码；"
        "单双、大小仅针对特别号码。"
    )

    print(
        "以上历史命中率来自Walk-Forward，"
        "不等于未来实际中奖概率。"
    )

    print(
        "=" * 70
    )

    print(
        "系统运行结束"
    )

    print(
        "=" * 70
    )


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":

    try:

        run_system()

    except KeyboardInterrupt:

        print(
            "\n用户中断程序"
        )

    except Exception as exc:

        print(
            "=" * 70
        )

        print(
            "[FATAL ERROR]"
        )

        print(
            str(exc)
        )

        print(
            "=" * 70
        )

        raise
