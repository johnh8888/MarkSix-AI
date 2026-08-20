from pathlib import Path

code = r'''# -*- coding: utf-8 -*-
"""
六合彩综合预测系统 V7.5
core/engine.py

兼容：
    from core.engine import run_system

功能：
1. 第7个号码作为特别号码
2. Top5 / Top10 / Top12
3. 生肖 Top5
4. 单双主推
5. 大小主推
6. 波色主推 / 次推 / 双色
7. 属性概率
8. Walk-Forward 最近10期
9. 多窗口 Walk-Forward：10 / 30 / 50 / 100
10. 模型稳定性
11. SQLite 历史数据
12. API SSL 证书过期兼容
13. prediction.json / backtest.json / module_performance.json / summary.json
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import ssl
import time
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# 基础配置
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "marksix.db"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

API_URL = os.getenv(
    "MARKSIX_API_URL",
    "https://marksix6.net/index.php?api=1",
)

REQUEST_TIMEOUT = 20

LOTTERIES = (
    "新澳门彩",
    "老澳门彩",
    "香港彩",
)

RECENT_BACKTEST = 10
MULTI_WINDOWS = (10, 30, 50, 100)


# ============================================================
# 波色
# ============================================================

RED = {
    1, 2, 7, 8, 12, 13, 18, 19, 23, 24,
    29, 30, 34, 35, 40, 45, 46,
}

BLUE = {
    3, 4, 9, 10, 14, 15, 20, 25, 26, 31,
    36, 37, 41, 42, 47, 48,
}

GREEN = {
    5, 6, 11, 16, 17, 21, 22, 27, 28, 32,
    33, 38, 39, 43, 44, 49,
}


ANIMALS = [
    "鼠", "牛", "虎", "兔", "龙", "蛇",
    "马", "羊", "猴", "鸡", "狗", "猪",
]


# ============================================================
# 属性
# ============================================================

def get_wave(number: int) -> str:
    number = int(number)

    if number in RED:
        return "红"
    if number in BLUE:
        return "蓝"
    if number in GREEN:
        return "绿"

    return ""


def get_size(number: int) -> str:
    return "大" if int(number) >= 25 else "小"


def get_odd_even(number: int) -> str:
    return "单" if int(number) % 2 else "双"


def zodiac_by_year(number: int, year: int) -> str:
    """
    2024 = 龙
    2025 = 蛇
    2026 = 马
    """

    number = int(number)
    year = int(year)

    base_index = 4
    year_index = (base_index + (year - 2024)) % 12

    return ANIMALS[
        (year_index - (number - 1)) % 12
    ]


def get_zodiac(number: int, issue: str) -> str:
    try:
        year = int(str(issue)[:4])
    except Exception:
        year = 2026

    return zodiac_by_year(number, year)


# ============================================================
# 数据标准化
# ============================================================

def get_special_number(record: dict[str, Any]) -> int | None:
    numbers = record.get("numbers", [])

    if not isinstance(numbers, (list, tuple)):
        return None

    if len(numbers) != 7:
        return None

    try:
        number = int(numbers[6])
    except Exception:
        return None

    if not 1 <= number <= 49:
        return None

    return number


def normalize_issue(value: Any) -> str:
    text = str(value or "").strip()

    digits = "".join(ch for ch in text if ch.isdigit())

    if len(digits) >= 6:
        return digits[-6:]

    return text


def normalize_numbers(value: Any) -> list[int]:
    if isinstance(value, (list, tuple)):
        raw = list(value)
    elif isinstance(value, str):
        raw = value.replace(",", " ").replace("|", " ").split()
    else:
        return []

    result = []

    for item in raw:
        try:
            n = int(str(item).strip())
        except Exception:
            continue

        if 1 <= n <= 49:
            result.append(n)

    return result


def normalize_record(row: Any) -> dict[str, Any] | None:
    if isinstance(row, dict):
        issue = (
            row.get("issue")
            or row.get("expect")
            or row.get("period")
            or row.get("qihao")
            or row.get("期号")
            or row.get("draw")
        )

        numbers = (
            row.get("numbers")
            or row.get("nums")
            or row.get("openCode")
            or row.get("opencode")
            or row.get("result")
            or row.get("code")
            or row.get("开奖号码")
        )

        if isinstance(numbers, str):
            numbers = normalize_numbers(numbers)
        else:
            numbers = normalize_numbers(numbers)

        issue = normalize_issue(issue)

        if issue and len(numbers) == 7:
            return {
                "issue": issue,
                "numbers": numbers,
            }

        # 尝试从常见字段中重新组合
        candidates = []

        for key in (
            "red", "blue", "green",
            "n1", "n2", "n3", "n4", "n5", "n6", "special",
            "num1", "num2", "num3", "num4", "num5", "num6", "num7",
        ):
            if key in row:
                candidates.append(row[key])

        nums2 = normalize_numbers(candidates)

        if issue and len(nums2) == 7:
            return {
                "issue": issue,
                "numbers": nums2,
            }

        return None

    if isinstance(row, (list, tuple)):
        if len(row) >= 8:
            issue = normalize_issue(row[0])
            numbers = normalize_numbers(row[1:8])

            if issue and len(numbers) == 7:
                return {
                    "issue": issue,
                    "numbers": numbers,
                }

    return None


def extract_records(payload: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    if isinstance(payload, list):
        for row in payload:
            item = normalize_record(row)
            if item:
                records.append(item)
        return records

    if isinstance(payload, dict):
        # 常见列表字段
        for key in (
            "data",
            "result",
            "results",
            "list",
            "rows",
            "records",
            "history",
            "dataList",
            "lotteryData",
        ):
            value = payload.get(key)

            if isinstance(value, list):
                found = extract_records(value)
                if found:
                    return found

        # 某些 API data 是字典
        for value in payload.values():
            if isinstance(value, (list, dict)):
                found = extract_records(value)
                if found:
                    records.extend(found)

        # 单条记录
        item = normalize_record(payload)
        if item:
            records.append(item)

    return deduplicate_records(records)


def deduplicate_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}

    for row in records:
        issue = str(row.get("issue", ""))
        numbers = row.get("numbers", [])

        if not issue or len(numbers) != 7:
            continue

        unique[issue] = {
            "issue": issue,
            "numbers": [int(x) for x in numbers],
        }

    def issue_key(row: dict[str, Any]) -> tuple[int, str]:
        issue = str(row.get("issue", ""))

        try:
            return int(issue), issue
        except Exception:
            return 0, issue

    return sorted(
        unique.values(),
        key=issue_key,
    )


# ============================================================
# API
# ============================================================

def _ssl_context(verify: bool = True):
    if verify:
        return ssl.create_default_context()

    return ssl._create_unverified_context()


def fetch_api(url: str = API_URL) -> Any:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(compatible; MarkSix-AI/7.5)"
        ),
        "Accept": "application/json,text/plain,*/*",
    }

    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )

    last_error = None

    # 第一次正常验证
    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
            context=_ssl_context(True),
        ) as response:
            raw = response.read()

        text = raw.decode(
            "utf-8",
            errors="ignore",
        )

        return json.loads(text)

    except Exception as exc:
        last_error = exc

        print(
            f"[WARN] 首次请求失败（{exc}），"
            "启用SSL兼容模式（跳过证书验证）重试"
        )

    # 第二次跳过过期证书验证
    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
            context=_ssl_context(False),
        ) as response:
            raw = response.read()

        text = raw.decode(
            "utf-8",
            errors="ignore",
        )

        return json.loads(text)

    except Exception as exc:
        last_error = exc

    raise RuntimeError(
        f"API请求失败：{last_error}"
    )


# ============================================================
# SQLite
# ============================================================

def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS draws (
            lottery TEXT NOT NULL,
            issue TEXT NOT NULL,
            numbers TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (lottery, issue)
        )
        """
    )

    conn.commit()

    return conn


def save_history(
    conn: sqlite3.Connection,
    lottery: str,
    history: list[dict[str, Any]],
) -> int:
    now = datetime.now().isoformat()

    inserted = 0

    for row in history:
        issue = str(row["issue"])
        numbers = row["numbers"]

        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO draws
            (lottery, issue, numbers, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                lottery,
                issue,
                json.dumps(
                    numbers,
                    ensure_ascii=False,
                ),
                now,
            ),
        )

        inserted += cursor.rowcount

    conn.commit()

    return inserted


def load_history(
    conn: sqlite3.Connection,
    lottery: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT issue, numbers
        FROM draws
        WHERE lottery = ?
        ORDER BY CAST(issue AS INTEGER) ASC
        """,
        (lottery,),
    ).fetchall()

    result = []

    for issue, numbers in rows:
        try:
            nums = json.loads(numbers)
        except Exception:
            continue

        if len(nums) != 7:
            continue

        result.append(
            {
                "issue": str(issue),
                "numbers": [
                    int(x) for x in nums
                ],
            }
        )

    return result


# ============================================================
# 属性计数
# ============================================================

def special_attribute_counter(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 100,
) -> Counter:
    counter = Counter()

    for row in history[-limit:]:
        special = get_special_number(row)

        if special is None:
            continue

        issue = str(row.get("issue", ""))

        if field == "wave":
            value = get_wave(special)
        elif field == "size":
            value = get_size(special)
        elif field == "odd_even":
            value = get_odd_even(special)
        elif field == "zodiac":
            value = get_zodiac(special, issue)
        else:
            continue

        if value:
            counter[value] += 1

    return counter


def probability_scores(
    counter: Counter,
    categories: list[str] | None = None,
) -> dict[str, float]:
    if categories is None:
        categories = list(counter.keys())

    if not categories:
        return {}

    total = sum(
        counter.get(item, 0)
        for item in categories
    )

    if total <= 0:
        equal = round(
            100 / len(categories),
            2,
        )

        result = {
            item: equal
            for item in categories
        }

        diff = round(
            100 - sum(result.values()),
            2,
        )

        result[categories[0]] = round(
            result[categories[0]] + diff,
            2,
        )

        return result

    result = {
        item: round(
            counter.get(item, 0)
            / total
            * 100,
            2,
        )
        for item in categories
    }

    # 防止极端情况下四舍五入总和不是100
    diff = round(
        100 - sum(result.values()),
        2,
    )

    if diff:
        result[categories[0]] = round(
            result[categories[0]] + diff,
            2,
        )

    return result


def predict_zodiac(
    history: list[dict[str, Any]],
    limit: int = 100,
) -> dict[str, Any]:
    counter = special_attribute_counter(
        history,
        "zodiac",
        limit,
    )

    probability = probability_scores(
        counter,
        ANIMALS,
    )

    ranking = sorted(
        ANIMALS,
        key=lambda x: (
            -probability.get(x, 0),
            -counter.get(x, 0),
            ANIMALS.index(x),
        ),
    )

    top5 = ranking[:5]

    return {
        "main": top5[0] if top5 else "",
        "secondary": (
            top5[1]
            if len(top5) > 1
            else ""
        ),
        "top5": top5,
        "double": top5,
        "probability": probability,
    }


def predict_single_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 100,
) -> dict[str, Any]:
    counter = special_attribute_counter(
        history,
        field,
        limit,
    )

    if field == "odd_even":
        categories = ["单", "双"]
    elif field == "size":
        categories = ["小", "大"]
    elif field == "wave":
        categories = ["红", "蓝", "绿"]
    else:
        categories = list(counter.keys())

    probability = probability_scores(
        counter,
        categories,
    )

    ranking = sorted(
        categories,
        key=lambda x: (
            -probability.get(x, 0),
            -counter.get(x, 0),
            categories.index(x),
        ),
    )

    return {
        "main": ranking[0] if ranking else "",
        "secondary": (
            ranking[1]
            if len(ranking) > 1
            else ""
        ),
        "double": ranking[:2],
        "probability": probability,
    }


def predict_attributes(
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    zodiac = predict_zodiac(history)
    odd_even = predict_single_attribute(
        history,
        "odd_even",
    )
    size = predict_single_attribute(
        history,
        "size",
    )
    wave = predict_single_attribute(
        history,
        "wave",
    )

    return {
        "zodiac": {
            "main": zodiac["main"],
            "secondary": zodiac["secondary"],
            "top5": zodiac["top5"],
            "double": zodiac["top5"],
            "probability": zodiac["probability"],
        },
        "odd_even": {
            "main": odd_even["main"],
            "secondary": "",
            "double": (
                [odd_even["main"]]
                if odd_even["main"]
                else []
            ),
            "probability": odd_even["probability"],
        },
        "size": {
            "main": size["main"],
            "secondary": "",
            "double": (
                [size["main"]]
                if size["main"]
                else []
            ),
            "probability": size["probability"],
        },
        "wave": {
            "main": wave["main"],
            "secondary": wave["secondary"],
            "double": wave["double"],
            "probability": wave["probability"],
        },
    }


def predict_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 100,
) -> dict[str, Any]:
    if field == "zodiac":
        return predict_zodiac(
            history,
            limit,
        )

    result = predict_single_attribute(
        history,
        field,
        limit,
    )

    if field in ("odd_even", "size"):
        result["secondary"] = ""
        result["double"] = (
            [result["main"]]
            if result["main"]
            else []
        )

    return result


# ============================================================
# 号码评分
# ============================================================

def _recency_weight(age: int) -> float:
    """
    越新的期数权重越高。
    age=0 表示最近一期。
    """

    return math.exp(
        -age / 18.0
    )


def score_numbers(
    history: list[dict[str, Any]],
    lookback: int = 100,
) -> dict[int, float]:
    """
    号码综合评分。

    不是把历史频率直接当成中奖概率，
    而是组合：
        长期频率
        最近频率
        近期趋势
        遗漏
        属性轻量一致性

    最终只用于排序。
    """

    data = history[-lookback:]

    scores = {
        n: 0.0
        for n in range(1, 50)
    }

    if not data:
        return scores

    # --------------------------------------------------------
    # 长期频率
    # --------------------------------------------------------

    frequency = Counter()

    for row in data:
        special = get_special_number(row)
        if special is not None:
            frequency[special] += 1

    total = len(data)

    for n in range(1, 50):
        scores[n] += (
            frequency[n]
            / max(total, 1)
            * 100
            * 0.35
        )

    # --------------------------------------------------------
    # 最近30期
    # --------------------------------------------------------

    recent = data[-30:]

    recent_counter = Counter()

    for row in recent:
        special = get_special_number(row)
        if special is not None:
            recent_counter[special] += 1

    for n in range(1, 50):
        scores[n] += (
            recent_counter[n]
            / max(len(recent), 1)
            * 100
            * 0.35
        )

    # --------------------------------------------------------
    # 最近10期趋势
    # --------------------------------------------------------

    last10 = data[-10:]

    trend_counter = Counter()

    for row in last10:
        special = get_special_number(row)
        if special is not None:
            trend_counter[special] += 1

    for n in range(1, 50):
        scores[n] += (
            trend_counter[n]
            / max(len(last10), 1)
            * 100
            * 0.20
        )

    # --------------------------------------------------------
    # 遗漏修正
    # --------------------------------------------------------

    for n in range(1, 50):
        gap = len(data)

        for idx in range(
            len(data) - 1,
            -1,
            -1,
        ):
            special = get_special_number(
                data[idx]
            )

            if special == n:
                gap = (
                    len(data)
                    - 1
                    - idx
                )
                break

        # 适度奖励中等遗漏，避免无限奖励冷号
        gap_bonus = min(
            gap,
            15,
        ) / 15.0 * 100

        scores[n] += (
            gap_bonus * 0.10
        )

    # --------------------------------------------------------
    # 轻量属性一致性
    # --------------------------------------------------------

    attrs = predict_attributes(data)

    odd_main = attrs["odd_even"]["main"]
    size_main = attrs["size"]["main"]
    wave_main = attrs["wave"]["main"]

    for n in range(1, 50):
        bonus = 0.0

        if (
            odd_main
            and get_odd_even(n) == odd_main
        ):
            bonus += 0.80

        if (
            size_main
            and get_size(n) == size_main
        ):
            bonus += 0.80

        if (
            wave_main
            and get_wave(n) == wave_main
        ):
            bonus += 0.60

        scores[n] += bonus

    return scores


def rank_numbers(
    history: list[dict[str, Any]],
) -> list[int]:
    scores = score_numbers(
        history,
        100,
    )

    return sorted(
        range(1, 50),
        key=lambda n: (
            -scores[n],
            n,
        ),
    )


def build_prediction(
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    scores = score_numbers(
        history,
        100,
    )

    ranking = sorted(
        range(1, 50),
        key=lambda n: (
            -scores[n],
            n,
        ),
    )

    attributes = predict_attributes(
        history
    )

    return {
        "candidates": ranking,
        "top5": ranking[:5],
        "top10": ranking[:10],
        "top12": ranking[:12],
        "scores": {
            str(n): round(
                scores[n],
                4,
            )
            for n in ranking[:12]
        },
        "attributes": attributes,
    }


# ============================================================
# Walk-Forward
# ============================================================

def _evaluate_prediction_core(
    prediction: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    actual_special = get_special_number(
        actual
    )

    if actual_special is None:
        return {}

    issue = str(
        actual.get(
            "issue",
            "",
        )
    )

    candidates = prediction.get(
        "candidates",
        [],
    )

    top5 = prediction.get(
        "top5",
        candidates[:5],
    )

    top10 = prediction.get(
        "top10",
        candidates[:10],
    )

    top12 = prediction.get(
        "top12",
        candidates[:12],
    )

    result = {
        "issue": issue,
        "actual": actual_special,
        "number_top5": (
            actual_special in set(top5)
        ),
        "number_top10": (
            actual_special in set(top10)
        ),
        "number_top12": (
            actual_special in set(top12)
        ),
    }

    actual_zodiac = get_zodiac(
        actual_special,
        issue,
    )

    actual_wave = get_wave(
        actual_special
    )

    actual_size = get_size(
        actual_special
    )

    actual_odd_even = get_odd_even(
        actual_special
    )

    attrs = prediction.get(
        "attributes",
        {},
    )

    zodiac = attrs.get(
        "zodiac",
        {},
    )

    zodiac_main = zodiac.get(
        "main",
        "",
    )

    zodiac_top5 = zodiac.get(
        "top5",
        zodiac.get(
            "double",
            [],
        ),
    )

    result["zodiac_main"] = (
        actual_zodiac == zodiac_main
    )

    result["zodiac_top5"] = (
        actual_zodiac
        in set(zodiac_top5)
    )

    odd_even = attrs.get(
        "odd_even",
        {},
    )

    result["odd_even_main"] = (
        actual_odd_even
        == odd_even.get("main", "")
    )

    size = attrs.get(
        "size",
        {},
    )

    result["size_main"] = (
        actual_size
        == size.get("main", "")
    )

    wave = attrs.get(
        "wave",
        {},
    )

    wave_main = wave.get(
        "main",
        "",
    )

    wave_secondary = wave.get(
        "secondary",
        "",
    )

    wave_double = wave.get(
        "double",
        [],
    )[:2]

    result["wave_main"] = (
        actual_wave == wave_main
    )

    result["wave_secondary"] = (
        actual_wave == wave_secondary
    )

    result["wave_double"] = (
        actual_wave
        in set(wave_double)
    )

    return result


def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
    train: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return _evaluate_prediction_core(
        prediction,
        actual,
    )


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


def calculate_performance(
    evaluations: list[dict[str, Any]],
    recent_n: int = 10,
) -> dict[str, Any]:
    if not evaluations:
        return {
            "samples": 0,
            "backtest_window": recent_n,
            "status": "历史数据不足",
        }

    evaluations = evaluations[-recent_n:]
    total = len(evaluations)

    def count(key: str) -> int:
        return sum(
            1
            for item in evaluations
            if item.get(key)
        )

    number_top5_hits = count(
        "number_top5"
    )
    number_top10_hits = count(
        "number_top10"
    )
    number_top12_hits = count(
        "number_top12"
    )

    zodiac_main_hits = count(
        "zodiac_main"
    )
    zodiac_top5_hits = count(
        "zodiac_top5"
    )

    odd_even_hits = count(
        "odd_even_main"
    )

    size_hits = count(
        "size_main"
    )

    wave_main_hits = count(
        "wave_main"
    )
    wave_secondary_hits = count(
        "wave_secondary"
    )
    wave_double_hits = count(
        "wave_double"
    )

    return {
        "samples": total,
        "backtest_window": recent_n,
        "numbers": {
            "top5": hit_rate(
                number_top5_hits,
                total,
            ),
            "top10": hit_rate(
                number_top10_hits,
                total,
            ),
            "top12": hit_rate(
                number_top12_hits,
                total,
            ),
            "average_top5_hits": round(
                number_top5_hits / total,
                4,
            ),
            "average_top10_hits": round(
                number_top10_hits / total,
                4,
            ),
            "average_top12_hits": round(
                number_top12_hits / total,
                4,
            ),
        },
        "zodiac": {
            "main": hit_rate(
                zodiac_main_hits,
                total,
            ),
            "top5": hit_rate(
                zodiac_top5_hits,
                total,
            ),
        },
        "odd_even": {
            "main": hit_rate(
                odd_even_hits,
                total,
            ),
        },
        "size": {
            "main": hit_rate(
                size_hits,
                total,
            ),
        },
        "wave": {
            "main": hit_rate(
                wave_main_hits,
                total,
            ),
            "secondary": hit_rate(
                wave_secondary_hits,
                total,
            ),
            "double": hit_rate(
                wave_double_hits,
                total,
            ),
        },
        "status": "正常",
    }


def walk_forward(
    history: list[dict[str, Any]],
    window: int = 10,
    min_train: int = 50,
) -> list[dict[str, Any]]:
    """
    真正的滚动验证：

        train = 当前期之前的全部历史
        actual = 当前验证期
        prediction = 只使用 train

    这样避免把未来开奖数据泄漏进预测。
    """

    if len(history) <= min_train:
        return []

    evaluations = []

    start = max(
        min_train,
        len(history) - window,
    )

    for idx in range(
        start,
        len(history),
    ):
        train = history[:idx]
        actual = history[idx]

        if len(train) < min_train:
            continue

        prediction = build_prediction(
            train
        )

        result = evaluate_prediction(
            prediction,
            actual,
            train,
        )

        if result:
            evaluations.append(
                result
            )

    return evaluations


def multi_window_backtest(
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    result = {}

    for window in MULTI_WINDOWS:
        evaluations = walk_forward(
            history,
            window=window,
            min_train=50,
        )

        result[str(window)] = (
            calculate_performance(
                evaluations,
                window,
            )
        )

    return result


def calculate_stability(
    multi: dict[str, Any],
) -> dict[str, Any]:
    values = []

    for window in MULTI_WINDOWS:
        item = multi.get(str(window), {})
        numbers = item.get(
            "numbers",
            {},
        )

        value = numbers.get(
            "top10"
        )

        if isinstance(value, (int, float)):
            values.append(
                float(value)
            )

    if not values:
        return {
            "average_top10": 0.0,
            "window_difference": 0.0,
            "score": 0.0,
            "status": "历史数据不足",
        }

    average = sum(values) / len(values)
    difference = max(values) - min(values)

    # 以Top10多窗口表现和窗口稳定性综合评分
    performance_score = min(
        average * 2.0,
        60.0,
    )

    stability_score = max(
        0.0,
        40.0 - difference * 1.5,
    )

    score = round(
        min(
            100.0,
            performance_score
            + stability_score,
        ),
        2,
    )

    if score >= 80:
        status = "良好"
    elif score >= 60:
        status = "一般"
    else:
        status = "偏弱"

    return {
        "average_top10": round(
            average,
            2,
        ),
        "window_difference": round(
            difference,
            2,
        ),
        "score": score,
        "status": status,
    }


# ============================================================
# JSON
# ============================================================

def save_json(
    path: Path,
    data: Any,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as fp:
        json.dump(
            data,
            fp,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# API数据同步
# ============================================================

def sync_lottery(
    lottery: str,
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    print("=" * 70)
    print(f"正在同步：{lottery}")
    print("=" * 70)
    print(f"[API] {API_URL}")
    print("[API] 请求第 1 次")

    payload = fetch_api(API_URL)

    history = extract_records(payload)

    if not history:
        raise RuntimeError(
            f"[{lottery}] API没有解析到有效开奖数据"
        )

    # API可能同时包含多个彩种。
    # 如果没有明确彩种字段，按当前接口结果使用。
    history = deduplicate_records(history)

    print(
        f"[{lottery}] 解析有效历史："
        f"{len(history)} 期"
    )

    if history:
        print(
            f"[{lottery}] 最早期号："
            f"{history[0]['issue']}"
        )
        print(
            f"[{lottery}] 最新期号："
            f"{history[-1]['issue']}"
        )
        print(
            f"[{lottery}] 最新号码："
            + " ".join(
                f"{n:02d}"
                for n in history[-1]["numbers"]
            )
        )

    inserted = save_history(
        conn,
        lottery,
        history,
    )

    db_history = load_history(
        conn,
        lottery,
    )

    print(
        f"[{lottery}] API返回："
        f"{len(history)} 期"
    )
    print(
        f"[{lottery}] 本次新增："
        f"{inserted} 期"
    )
    print(
        f"[{lottery}] 当前数据库："
        f"{len(db_history)} 期"
    )

    return db_history


# ============================================================
# 单彩种运行
# ============================================================

def run_lottery(
    lottery: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    print("=" * 70)
    print(f"【{lottery}】")
    print("=" * 70)

    if not history:
        return {
            "lottery": lottery,
            "status": "历史数据不足",
        }

    latest = history[-1]

    try:
        next_issue = str(
            int(latest["issue"]) + 1
        )
    except Exception:
        next_issue = ""

    prediction = build_prediction(
        history
    )

    recent_eval = walk_forward(
        history,
        window=RECENT_BACKTEST,
        min_train=50,
    )

    performance = calculate_performance(
        recent_eval,
        RECENT_BACKTEST,
    )

    multi = multi_window_backtest(
        history
    )

    stability = calculate_stability(
        multi
    )

    result = {
        "lottery": lottery,
        "generated_at": datetime.now().isoformat(),
        "history_count": len(history),
        "latest_issue": latest["issue"],
        "next_issue": next_issue,
        "latest_numbers": latest["numbers"],
        "prediction": prediction,
        "performance": performance,
        "multi_window": multi,
        "stability": stability,
        "recent_evaluations": recent_eval,
    }

    print()
    print("【V7.5 号码预测】")

    print(
        "Top5："
        + " ".join(
            f"{n:02d}"
            for n in prediction["top5"]
        )
    )

    print(
        "Top10："
        + " ".join(
            f"{n:02d}"
            for n in prediction["top10"]
        )
    )

    print(
        "Top12："
        + " ".join(
            f"{n:02d}"
            for n in prediction["top12"]
        )
    )

    print()
    print("【号码综合评分 Top12】")

    for n in prediction["top12"]:
        print(
            f"{n:02d} = "
            f"{prediction['scores'][str(n)]:.4f}"
        )

    attrs = prediction["attributes"]

    zodiac = attrs["zodiac"]
    odd_even = attrs["odd_even"]
    size = attrs["size"]
    wave = attrs["wave"]

    print()
    print("【下一期属性预测】")

    print(
        "生肖：主推 "
        f"{zodiac['main']} "
        "次推 "
        f"{zodiac['secondary']} "
        "Top5 "
        "+".join(zodiac["top5"])
    )

    print(
        "生肖概率："
        + " ".join(
            f"{animal}:"
            f"{zodiac['probability'].get(animal, 0):.2f}%"
            for animal in ANIMALS
        )
    )

    print(
        f"单双：主推 {odd_even['main']}"
    )

    print(
        "单双概率："
        + " ".join(
            f"{x}:"
            f"{odd_even['probability'].get(x, 0):.2f}%"
            for x in ("单", "双")
        )
    )

    print(
        f"大小：主推 {size['main']}"
    )

    print(
        "大小概率："
        + " ".join(
            f"{x}:"
            f"{size['probability'].get(x, 0):.2f}%"
            for x in ("小", "大")
        )
    )

    print(
        "波色：主推 "
        f"{wave['main']} "
        "次推 "
        f"{wave['secondary']} "
        "双色 "
        + " + ".join(wave["double"])
    )

    print(
        "波色概率："
        + " ".join(
            f"{x}:"
            f"{wave['probability'].get(x, 0):.2f}%"
            for x in ("红", "蓝", "绿")
        )
    )

    print()
    print("【Walk-Forward 最近10期】")

    print(
        f"验证期数："
        f"{performance.get('samples', 0)}"
    )

    numbers_perf = performance.get(
        "numbers",
        {},
    )

    print(
        f"Top5：{numbers_perf.get('top5', 0):.2f}% "
        f"| Top10：{numbers_perf.get('top10', 0):.2f}% "
        f"| Top12：{numbers_perf.get('top12', 0):.2f}%"
    )

    print(
        f"Top5平均命中："
        f"{numbers_perf.get('average_top5_hits', 0):.4f} "
        f"| Top10平均命中："
        f"{numbers_perf.get('average_top10_hits', 0):.4f} "
        f"| Top12平均命中："
        f"{numbers_perf.get('average_top12_hits', 0):.4f}"
    )

    print(
        f"生肖主推："
        f"{performance.get('zodiac', {}).get('main', 0):.2f}% "
        f"| 生肖Top5："
        f"{performance.get('zodiac', {}).get('top5', 0):.2f}%"
    )

    print(
        f"单双主推："
        f"{performance.get('odd_even', {}).get('main', 0):.2f}% "
        f"| 大小主推："
        f"{performance.get('size', {}).get('main', 0):.2f}%"
    )

    print(
        f"波色主推："
        f"{performance.get('wave', {}).get('main', 0):.2f}% "
        f"| 次推："
        f"{performance.get('wave', {}).get('secondary', 0):.2f}% "
        f"| 双色："
        f"{performance.get('wave', {}).get('double', 0):.2f}%"
    )

    print()
    print("【多窗口 Walk-Forward】")

    for window in MULTI_WINDOWS:
        item = multi.get(
            str(window),
            {},
        )

        nums = item.get(
            "numbers",
            {},
        )

        print(
            f"{window}期："
            f"Top5 {nums.get('top5', 0):.2f}% "
            f"| Top10 {nums.get('top10', 0):.2f}% "
            f"| Top12 {nums.get('top12', 0):.2f}%"
        )

    print()
    print("【模型稳定性】")

    print(
        "Top10多窗口平均："
        f"{stability['average_top10']:.2f}%"
    )

    print(
        "窗口差异："
        f"{stability['window_difference']:.2f}%"
    )

    print(
        "稳定性评分："
        f"{stability['score']:.2f}/100"
    )

    print(
        f"状态：{stability['status']}"
    )

    return result


# ============================================================
# 主系统入口
# ============================================================

def run_system() -> dict[str, Any]:
    """
    main.py 唯一入口。

    兼容：
        from core.engine import run_system
        run_system()
    """

    start_time = datetime.now().isoformat()

    print("=" * 70)
    print("开始运行六合彩综合预测系统 V7.5")
    print(f"启动时间：{start_time}")
    print("=" * 70)

    conn = init_db()

    print("[OK] SQLite 初始化完成")
    print()

    all_results: dict[str, Any] = {}
    all_backtests: dict[str, Any] = {}
    all_modules: dict[str, Any] = {}
    all_summaries: dict[str, Any] = {}

    try:
        for lottery in LOTTERIES:
            print()
            print("=" * 70)
            print(f"正在更新：{lottery}")
            print("=" * 70)

            try:
                history = sync_lottery(
                    lottery,
                    conn,
                )

                result = run_lottery(
                    lottery,
                    history,
                )

                all_results[lottery] = result

                all_backtests[lottery] = {
                    "recent10": result.get(
                        "performance",
                        {},
                    ),
                    "multi_window": result.get(
                        "multi_window",
                        {},
                    ),
                }

                all_modules[lottery] = {
                    "numbers": result.get(
                        "performance",
                        {},
                    ).get(
                        "numbers",
                        {},
                    ),
                    "zodiac": result.get(
                        "performance",
                        {},
                    ).get(
                        "zodiac",
                        {},
                    ),
                    "odd_even": result.get(
                        "performance",
                        {},
                    ).get(
                        "odd_even",
                        {},
                    ),
                    "size": result.get(
                        "performance",
                        {},
                    ).get(
                        "size",
                        {},
                    ),
                    "wave": result.get(
                        "performance",
                        {},
                    ).get(
                        "wave",
                        {},
                    ),
                }

                prediction = result.get(
                    "prediction",
                    {},
                )

                attrs = prediction.get(
                    "attributes",
                    {},
                )

                all_summaries[lottery] = {
                    "latest_issue": result.get(
                        "latest_issue",
                        "",
                    ),
                    "next_issue": result.get(
                        "next_issue",
                        "",
                    ),
                    "top5": prediction.get(
                        "top5",
                        [],
                    ),
                    "top10": prediction.get(
                        "top10",
                        [],
                    ),
                    "top12": prediction.get(
                        "top12",
                        [],
                    ),
                    "zodiac": attrs.get(
                        "zodiac",
                        {},
                    ).get(
                        "top5",
                        [],
                    ),
                    "odd_even": attrs.get(
                        "odd_even",
                        {},
                    ).get(
                        "main",
                        "",
                    ),
                    "size": attrs.get(
                        "size",
                        {},
                    ).get(
                        "main",
                        "",
                    ),
                    "wave_main": attrs.get(
                        "wave",
                        {},
                    ).get(
                        "main",
                        "",
                    ),
                    "wave_secondary": attrs.get(
                        "wave",
                        {},
                    ).get(
                        "secondary",
                        "",
                    ),
                    "wave_double": attrs.get(
                        "wave",
                        {},
                    ).get(
                        "double",
                        [],
                    ),
                    "stability": result.get(
                        "stability",
                        {},
                    ),
                    "recent10": result.get(
                        "performance",
                        {},
                    ).get(
                        "numbers",
                        {},
                    ),
                }

            except Exception as exc:
                print(
                    f"[ERROR] {lottery}运行失败："
                    f"{type(exc).__name__}: {exc}"
                )

                all_results[lottery] = {
                    "lottery": lottery,
                    "status": "运行失败",
                    "error": str(exc),
                }

    finally:
        conn.close()

    save_json(
        OUTPUT_DIR / "prediction.json",
        all_results,
    )

    save_json(
        OUTPUT_DIR / "backtest.json",
        all_backtests,
    )

    save_json(
        OUTPUT_DIR / "module_performance.json",
        all_modules,
    )

    save_json(
        OUTPUT_DIR / "summary.json",
        all_summaries,
    )

    print()
    print("=" * 70)
    print("预测结果已保存：output/prediction.json")
    print("回测结果已保存：output/backtest.json")
    print("模块表现已保存：output/module_performance.json")
    print("简版预测已保存：output/summary.json")
    print("=" * 70)

    print("【三彩种最终预测】")
    print("=" * 70)

    for lottery in LOTTERIES:
        result = all_results.get(
            lottery,
            {},
        )

        if result.get("status") == "运行失败":
            print()
            print(lottery)
            print(
                f"运行失败："
                f"{result.get('error', '')}"
            )
            continue

        prediction = result.get(
            "prediction",
            {},
        )

        attrs = prediction.get(
            "attributes",
            {},
        )

        stability = result.get(
            "stability",
            {},
        )

        perf = result.get(
            "performance",
            {},
        )

        numbers_perf = perf.get(
            "numbers",
            {},
        )

        print()
        print(lottery)
        print(
            f"最新："
            f"{result.get('latest_issue', '')}"
        )
        print(
            f"下一期："
            f"{result.get('next_issue', '')}"
        )

        print(
            "Top5："
            + " ".join(
                f"{n:02d}"
                for n in prediction.get(
                    "top5",
                    [],
                )
            )
        )

        print(
            "Top10："
            + " ".join(
                f"{n:02d}"
                for n in prediction.get(
                    "top10",
                    [],
                )
            )
        )

        print(
            "Top12："
            + " ".join(
                f"{n:02d}"
                for n in prediction.get(
                    "top12",
                    [],
                )
            )
        )

        zodiac = attrs.get(
            "zodiac",
            {},
        )

        print(
            "生肖："
            + " / ".join(
                zodiac.get(
                    "top5",
                    [],
                )
            )
        )

        print(
            "单双主推："
            + str(
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
            "大小主推："
            + str(
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
            "波色："
            + " / ".join(
                [
                    str(wave.get("main", "")),
                    str(wave.get("secondary", "")),
                    " + ".join(
                        wave.get(
                            "double",
                            [],
                        )
                    ),
                ]
            )
        )

        print(
            "模型稳定性："
            f"{stability.get('score', 0):.2f}/100 "
            f"{stability.get('status', '')}"
        )

        print(
            "最近10期："
            f"Top5 "
            f"{numbers_perf.get('top5', 0):.2f}% "
            "/ Top10 "
            f"{numbers_perf.get('top10', 0):.2f}% "
            "/ Top12 "
            f"{numbers_perf.get('top12', 0):.2f}%"
        )

    print()
    print("=" * 70)
    print(
        "说明：模型输出来自历史数据统计与Walk-Forward验证，"
        "不等于未来实际中奖概率。"
    )
    print("=" * 70)
    print("系统运行结束")
    print("=" * 70)

    return {
        "generated_at": datetime.now().isoformat(),
        "results": all_results,
        "backtest": all_backtests,
        "module_performance": all_modules,
        "summary": all_summaries,
    }


# ============================================================
# 兼容别名
# ============================================================

main = run_system


if __name__ == "__main__":
    run_system()
'''

path = Path("/mnt/data/engine.py")
path.write_text(code, encoding="utf-8")

print(f"已生成完整 V7.5 engine.py：{path}")
print(f"文件大小：{path.stat().st_size:,} bytes")
