# -*- coding: utf-8 -*-

"""
六合彩 V3.0 策略层

负责：

1. 号码频率
2. 近期趋势
3. 遗漏
4. 尾数
5. 分区
6. 大小
7. 单双
8. 波色
9. 综合策略
10. 动态权重
"""

from collections import Counter
from typing import Any, Dict, List


from .wave_model import (
    RED,
    BLUE,
    GREEN,
    WAVES,
    NUMBER_TO_WAVE,
    get_wave,
    wave_probabilities,
    wave_single_pick,
    wave_double_pick,
)


# =========================================================
# 工具
# =========================================================

def extract_special(
    row: Dict[str, Any]
) -> int:

    special = row.get(
        "special"
    )

    if special is not None:

        try:

            n = int(special)

            if 1 <= n <= 49:
                return n

        except Exception:
            pass

    numbers = row.get(
        "numbers",
        []
    )

    if isinstance(
        numbers,
        str
    ):

        numbers = (
            numbers
            .replace("，", ",")
            .split(",")
        )

    try:

        numbers = [
            int(str(x).strip())
            for x in numbers
            if str(x).strip()
        ]

    except Exception:

        return 0

    if len(numbers) >= 7:

        return numbers[6]

    return 0


# =========================================================
# 提取特码
# =========================================================

def special_sequence(
    rows: List[Dict[str, Any]]
) -> List[int]:

    result = []

    for row in rows:

        n = extract_special(row)

        if 1 <= n <= 49:
            result.append(n)

    return result


# =========================================================
# 频率
# =========================================================

def frequency_scores(
    rows: List[Dict[str, Any]],
    window: int = 120
) -> Dict[int, float]:

    sequence = special_sequence(
        rows[:window]
    )

    counts = Counter(
        sequence
    )

    total = max(
        len(sequence),
        1
    )

    return {
        n:
            (
                counts.get(n, 0)
                + 1.0
            )
            /
            (
                total
                + 49.0
            )

        for n in range(1, 50)
    }


# =========================================================
# 近期趋势
# =========================================================

def trend_scores(
    rows: List[Dict[str, Any]],
    window: int = 36
) -> Dict[int, float]:

    sequence = special_sequence(
        rows[:window]
    )

    scores = {
        n: 0.0
        for n in range(1, 50)
    }

    if not sequence:
        return scores

    total = len(sequence)

    # 越近权重越高
    for index, number in enumerate(
        sequence
    ):

        weight = (
            total - index
        ) / total

        scores[number] += weight

    maximum = max(
        scores.values()
    )

    if maximum > 0:

        for n in scores:

            scores[n] /= maximum

    return scores


# =========================================================
# 遗漏
# =========================================================

def omission_scores(
    rows: List[Dict[str, Any]],
    window: int = 120
) -> Dict[int, float]:

    sequence = special_sequence(
        rows[:window]
    )

    scores = {}

    for n in range(1, 50):

        omission = window

        for index, value in enumerate(
            sequence
        ):

            if value == n:

                omission = index
                break

        scores[n] = omission

    # 适度降权极端遗漏
    maximum = max(
        scores.values()
    ) if scores else 1

    result = {}

    for n in range(1, 50):

        omission = scores[n]

        result[n] = (
            1.0
            -
            omission / max(
                maximum,
                1
            )
        )

    return result


# =========================================================
# 尾数
# =========================================================

def tail_scores(
    rows: List[Dict[str, Any]],
    window: int = 36
) -> Dict[int, float]:

    sequence = special_sequence(
        rows[:window]
    )

    counts = Counter(
        n % 10
        for n in sequence
    )

    result = {}

    for n in range(1, 50):

        result[n] = (
            counts.get(
                n % 10,
                0
            )
            + 1
        )

    maximum = max(
        result.values()
    )

    for n in result:

        result[n] /= maximum

    return result


# =========================================================
# 分区
# =========================================================

def zone(
    number: int
) -> int:

    if 1 <= number <= 10:
        return 1

    if 11 <= number <= 20:
        return 2

    if 21 <= number <= 30:
        return 3

    if 31 <= number <= 40:
        return 4

    if 41 <= number <= 49:
        return 5

    return 0


def zone_scores(
    rows: List[Dict[str, Any]],
    window: int = 36
) -> Dict[int, float]:

    sequence = special_sequence(
        rows[:window]
    )

    counts = Counter(
        zone(n)
        for n in sequence
    )

    result = {}

    for n in range(1, 50):

        result[n] = (
            counts.get(
                zone(n),
                0
            )
            + 1
        )

    maximum = max(
        result.values()
    )

    for n in result:

        result[n] /= maximum

    return result


# =========================================================
# 大小
# =========================================================

def get_size(
    number: int
) -> str:

    return "大" if number >= 25 else "小"


def size_probabilities(
    rows: List[Dict[str, Any]],
    window: int = 36
) -> Dict[str, float]:

    sequence = special_sequence(
        rows[:window]
    )

    counts = Counter(
        get_size(n)
        for n in sequence
    )

    total = sum(
        counts.values()
    )

    if total <= 0:

        return {
            "大": 0.5,
            "小": 0.5
        }

    return {

        "大":
            (
                counts.get("大", 0)
                + 1
            )
            /
            (
                total + 2
            ),

        "小":
            (
                counts.get("小", 0)
                + 1
            )
            /
            (
                total + 2
            ),
    }


# =========================================================
# 单双
# =========================================================

def get_parity(
    number: int
) -> str:

    return "单" if number % 2 else "双"


def parity_probabilities(
    rows: List[Dict[str, Any]],
    window: int = 36
) -> Dict[str, float]:

    sequence = special_sequence(
        rows[:window]
    )

    counts = Counter(
        get_parity(n)
        for n in sequence
    )

    total = sum(
        counts.values()
    )

    if total <= 0:

        return {
            "单": 0.5,
            "双": 0.5
        }

    return {

        "单":
            (
                counts.get("单", 0)
                + 1
            )
            /
            (
                total + 2
            ),

        "双":
            (
                counts.get("双", 0)
                + 1
            )
            /
            (
                total + 2
            ),
    }


# =========================================================
# 号码策略综合
# =========================================================

def combine_strategies(
    rows: List[Dict[str, Any]],
    weights: Dict[str, float] = None
) -> Dict[int, float]:

    if weights is None:

        weights = {

            "frequency": 0.22,

            "trend": 0.24,

            "omission": 0.10,

            "tail": 0.10,

            "zone": 0.08,

            "wave": 0.16,

            "size": 0.05,

            "parity": 0.05,
        }

    frequency = frequency_scores(
        rows,
        120
    )

    trend = trend_scores(
        rows,
        36
    )

    omission = omission_scores(
        rows,
        120
    )

    tail = tail_scores(
        rows,
        36
    )

    zone_s = zone_scores(
        rows,
        36
    )

    wave = wave_probabilities(
        rows
    )

    size_p = size_probabilities(
        rows
    )

    parity_p = parity_probabilities(
        rows
    )

    result = {}

    for number in range(1, 50):

        wave_p = wave.get(
            get_wave(number),
            1.0 / 3.0
        )

        size_pn = size_p.get(
            get_size(number),
            0.5
        )

        parity_pn = parity_p.get(
            get_parity(number),
            0.5
        )

        score = (

            frequency[number]
            * weights["frequency"]

            +

            trend[number]
            * weights["trend"]

            +

            omission[number]
            * weights["omission"]

            +

            tail[number]
            * weights["tail"]

            +

            zone_s[number]
            * weights["zone"]

            +

            wave_p
            * weights["wave"]

            +

            size_pn
            * weights["size"]

            +

            parity_pn
            * weights["parity"]
        )

        result[number] = score

    return result


# =========================================================
# 排名
# =========================================================

def rank_numbers(
    scores: Dict[int, float],
    top_n: int = 10
) -> List[int]:

    ordered = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        number
        for number, _ in ordered[:top_n]
    ]


# =========================================================
# 号码概率
# =========================================================

def calibrate_number_probabilities(
    scores: Dict[int, float]
) -> Dict[int, float]:

    if not scores:

        return {}

    # -----------------------------------------------------
    # 防止 1.0000
    #
    # 不把 raw score 直接当概率
    # -----------------------------------------------------

    minimum = min(
        scores.values()
    )

    shifted = {
        n:
            max(
                score - minimum,
                0.000001
            )

        for n, score in scores.items()
    }

    total = sum(
        shifted.values()
    )

    if total <= 0:

        return {
            n: 1.0 / 49.0
            for n in scores
        }

    probabilities = {

        n:
            value / total

        for n, value in shifted.items()
    }

    return probabilities


# =========================================================
# 动态模块权重
# =========================================================

def normalize_weights(
    weights: Dict[str, float]
) -> Dict[str, float]:

    total = sum(
        max(
            0.0,
            float(v)
        )
        for v in weights.values()
    )

    if total <= 0:

        equal = 1.0 / len(
            weights
        )

        return {
            k: equal
            for k in weights
        }

    return {
        k:
            max(
                0.0,
                float(v)
            )
            /
            total

        for k, v in weights.items()
    }


def dynamic_weights(
    performance: Dict[str, float] = None
) -> Dict[str, float]:

    base = {

        "frequency": 0.22,

        "trend": 0.24,

        "omission": 0.10,

        "tail": 0.10,

        "zone": 0.08,

        "wave": 0.16,

        "size": 0.05,

        "parity": 0.05,
    }

    if not performance:

        return normalize_weights(
            base
        )

    adjusted = {}

    for key, value in base.items():

        score = performance.get(
            key,
            0.5
        )

        # 历史表现只作为调整因子
        #
        # 防止某个模块因为样本少
        # 突然权重极端化

        factor = 0.70 + (
            max(
                0.0,
                min(
                    1.0,
                    score
                )
            )
            * 0.60
        )

        adjusted[key] = (
            value * factor
        )

    return normalize_weights(
        adjusted
    )


# =========================================================
# 完整策略输出
# =========================================================

def build_strategy_result(
    rows: List[Dict[str, Any]],
    performance: Dict[str, float] = None
) -> Dict[str, Any]:

    weights = dynamic_weights(
        performance
    )

    scores = combine_strategies(
        rows,
        weights
    )

    probabilities = calibrate_number_probabilities(
        scores
    )

    top10 = rank_numbers(
        probabilities,
        10
    )

    top3 = rank_numbers(
        probabilities,
        3
    )

    wave_p = wave_probabilities(
        rows
    )

    wave_single = wave_single_pick(
        wave_p
    )

    wave_double = wave_double_pick(
        wave_p
    )

    size_p = size_probabilities(
        rows
    )

    parity_p = parity_probabilities(
        rows
    )

    return {

        "scores":
            scores,

        "probabilities":
            probabilities,

        "top10":
            top10,

        "top3":
            top3,

        "weights":
            weights,

        "wave_probabilities":
            wave_p,

        "wave_single":
            wave_single,

        "wave_double":
            wave_double,

        "size_probabilities":
            size_p,

        "parity_probabilities":
            parity_p,
    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    rows = []

    for i in range(100):

        rows.append({

            "numbers":
                [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    (i % 49) + 1
                ]
        })

    result = build_strategy_result(
        rows
    )

    print(
        "Top10:",
        result["top10"]
    )

    print(
        "Top3:",
        result["top3"]
    )

    print(
        "波色单推:",
        result["wave_single"]
    )

    print(
        "波色双推:",
        result["wave_double"]
    )