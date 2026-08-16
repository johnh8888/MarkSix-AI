# -*- coding: utf-8 -*-

"""
六合彩 AI V2.0
自适应策略引擎

核心：
1. 近期频率
2. 中期频率
3. 长期频率
4. 遗漏
5. 趋势
6. 大小
7. 单双
8. 波色
9. 状态识别
10. 动态策略权重

注意：
本模块用于统计建模与回测，不代表开奖结果可以被确定预测。
"""

from collections import Counter
import math

from .features import (
    get_special,
    special_frequency,
    special_omission,
)


NUMBERS = range(1, 50)


# =========================================================
# 常量
# =========================================================

WAVE_MAP = {
    "红": {
        1, 2, 7, 8, 12, 13, 18, 19,
        23, 24, 29, 30, 34, 35, 40, 45, 46
    },

    "蓝": {
        3, 4, 9, 10, 14, 15, 20, 25,
        26, 31, 36, 37, 41, 42, 47, 48
    },

    "绿": {
        5, 6, 11, 16, 17, 21, 22, 27,
        28, 32, 33, 38, 39, 43, 44, 49
    }
}


NUMBER_TO_WAVE = {}

for wave, nums in WAVE_MAP.items():
    for n in nums:
        NUMBER_TO_WAVE[n] = wave


# =========================================================
# 工具
# =========================================================

def safe_number(row):

    try:
        n = get_special(row)
        n = int(n)

        if 1 <= n <= 49:
            return n

    except Exception:
        pass

    return None


def normalize_scores(scores):

    if not scores:
        return {n: 0.5 for n in NUMBERS}

    values = list(scores.values())

    low = min(values)
    high = max(values)

    if high == low:
        return {
            n: 0.5
            for n in scores
        }

    return {
        n: (value - low) / (high - low)
        for n, value in scores.items()
    }


def sigmoid(x):

    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 1.0 if x > 0 else 0.0


# =========================================================
# 策略1：近期频率
# =========================================================

def strategy_recent(rows):

    data = rows[:20]

    freq = special_frequency(data)

    scores = normalize_scores(freq)

    return {
        n: scores.get(n, 0.0)
        for n in NUMBERS
    }


# =========================================================
# 策略2：中期频率
# =========================================================

def strategy_medium(rows):

    data = rows[:80]

    freq = special_frequency(data)

    scores = normalize_scores(freq)

    return {
        n: scores.get(n, 0.0)
        for n in NUMBERS
    }


# =========================================================
# 策略3：长期频率
# =========================================================

def strategy_long(rows):

    data = rows[:300]

    freq = special_frequency(data)

    scores = normalize_scores(freq)

    return {
        n: scores.get(n, 0.0)
        for n in NUMBERS
    }


# =========================================================
# 策略4：遗漏
# =========================================================

def strategy_omission(rows):

    omission = special_omission(
        rows[:300]
    )

    scores = normalize_scores(
        omission
    )

    return {
        n: scores.get(n, 0.0)
        for n in NUMBERS
    }


# =========================================================
# 策略5：趋势
# =========================================================

def strategy_trend(rows):

    recent = rows[:20]
    medium = rows[:80]

    recent_freq = special_frequency(
        recent
    )

    medium_freq = special_frequency(
        medium
    )

    scores = {}

    for n in NUMBERS:

        r = recent_freq.get(n, 0)
        m = medium_freq.get(n, 0)

        # 当前近期表现相对于中期表现
        r_rate = r / max(len(recent), 1)
        m_rate = m / max(len(medium), 1)

        trend = (
            r_rate - m_rate
        )

        scores[n] = trend

    return normalize_scores(
        scores
    )


# =========================================================
# 策略6：大小
# =========================================================

def strategy_size(rows):

    data = rows[:80]

    big = 0
    small = 0

    for row in data:

        n = safe_number(row)

        if n is None:
            continue

        if n >= 25:
            big += 1
        else:
            small += 1

    total = big + small

    if total == 0:
        return {
            n: 0.5
            for n in NUMBERS
        }

    big_prob = big / total
    small_prob = small / total

    scores = {}

    for n in NUMBERS:

        if n >= 25:
            scores[n] = big_prob
        else:
            scores[n] = small_prob

    return normalize_scores(
        scores
    )


# =========================================================
# 策略7：单双
# =========================================================

def strategy_parity(rows):

    data = rows[:80]

    odd = 0
    even = 0

    for row in data:

        n = safe_number(row)

        if n is None:
            continue

        if n % 2:
            odd += 1
        else:
            even += 1

    total = odd + even

    if total == 0:
        return {
            n: 0.5
            for n in NUMBERS
        }

    odd_prob = odd / total
    even_prob = even / total

    scores = {}

    for n in NUMBERS:

        if n % 2:
            scores[n] = odd_prob
        else:
            scores[n] = even_prob

    return normalize_scores(
        scores
    )


# =========================================================
# 策略8：波色
# =========================================================

def strategy_wave(rows):

    data = rows[:80]

    counter = Counter()

    for row in data:

        n = safe_number(row)

        if n is None:
            continue

        wave = NUMBER_TO_WAVE.get(n)

        if wave:
            counter[wave] += 1

    total = sum(counter.values())

    if total == 0:

        probs = {
            "红": 1 / 3,
            "蓝": 1 / 3,
            "绿": 1 / 3
        }

    else:

        probs = {
            wave:
                counter.get(wave, 0) / total

            for wave in [
                "红",
                "蓝",
                "绿"
            ]
        }

    scores = {}

    for n in NUMBERS:

        wave = NUMBER_TO_WAVE.get(n)

        scores[n] = probs.get(
            wave,
            1 / 3
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 状态识别
# =========================================================

def detect_state(rows):

    data = rows[:20]

    if len(data) < 5:

        return {
            "size": "unknown",
            "parity": "unknown",
            "wave": "unknown",
            "trend": "neutral",
        }

    numbers = []

    for row in data:

        n = safe_number(row)

        if n:
            numbers.append(n)

    if not numbers:

        return {
            "size": "unknown",
            "parity": "unknown",
            "wave": "unknown",
            "trend": "neutral",
        }

    # -----------------------------------------------------
    # 大小状态
    # -----------------------------------------------------

    big = sum(
        n >= 25
        for n in numbers
    )

    small = len(numbers) - big

    if big / len(numbers) >= 0.65:
        size_state = "big_hot"

    elif small / len(numbers) >= 0.65:
        size_state = "small_hot"

    else:
        size_state = "balanced"

    # -----------------------------------------------------
    # 单双状态
    # -----------------------------------------------------

    odd = sum(
        n % 2 == 1
        for n in numbers
    )

    even = len(numbers) - odd

    if odd / len(numbers) >= 0.65:
        parity_state = "odd_hot"

    elif even / len(numbers) >= 0.65:
        parity_state = "even_hot"

    else:
        parity_state = "balanced"

    # -----------------------------------------------------
    # 波色状态
    # -----------------------------------------------------

    waves = [
        NUMBER_TO_WAVE.get(n)
        for n in numbers
    ]

    wave_counter = Counter(
        w for w in waves if w
    )

    if wave_counter:

        wave, count = wave_counter.most_common(1)[0]

        if count / len(numbers) >= 0.50:
            wave_state = f"{wave}_hot"
        else:
            wave_state = "balanced"

    else:
        wave_state = "unknown"

    # -----------------------------------------------------
    # 趋势
    # -----------------------------------------------------

    first = numbers[:10]
    second = numbers[10:20]

    if len(second) >= 5:

        first_avg = sum(first) / len(first)
        second_avg = sum(second) / len(second)

        if first_avg > second_avg + 3:
            trend_state = "up"

        elif first_avg < second_avg - 3:
            trend_state = "down"

        else:
            trend_state = "neutral"

    else:

        trend_state = "neutral"

    return {
        "size": size_state,
        "parity": parity_state,
        "wave": wave_state,
        "trend": trend_state,
    }


# =========================================================
# 状态调整
# =========================================================

def apply_state_adjustment(
    scores,
    rows
):

    state = detect_state(rows)

    result = dict(scores)

    # -----------------------------------------------------
    # 大小
    # -----------------------------------------------------

    if state["size"] == "big_hot":

        for n in NUMBERS:

            if n >= 25:
                result[n] *= 1.04
            else:
                result[n] *= 0.98

    elif state["size"] == "small_hot":

        for n in NUMBERS:

            if n < 25:
                result[n] *= 1.04
            else:
                result[n] *= 0.98

    # -----------------------------------------------------
    # 单双
    # -----------------------------------------------------

    if state["parity"] == "odd_hot":

        for n in NUMBERS:

            if n % 2:
                result[n] *= 1.03

    elif state["parity"] == "even_hot":

        for n in NUMBERS:

            if n % 2 == 0:
                result[n] *= 1.03

    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    wave_state = state["wave"]

    if wave_state.endswith("_hot"):

        hot_wave = wave_state.split("_")[0]

        for n in NUMBERS:

            if NUMBER_TO_WAVE.get(n) == hot_wave:
                result[n] *= 1.025

    return normalize_scores(
        result
    )


# =========================================================
# 动态权重
# =========================================================

DEFAULT_WEIGHTS = {

    "recent": 0.20,

    "medium": 0.16,

    "long": 0.10,

    "omission": 0.10,

    "trend": 0.18,

    "size": 0.08,

    "parity": 0.08,

    "wave": 0.10,
}


def calculate_dynamic_weights(
    rows
):

    """
    第一阶段自适应权重。

    不直接使用未来结果。

    根据当前历史结构计算权重，
    并且对极端权重进行限制。
    """

    weights = dict(
        DEFAULT_WEIGHTS
    )

    state = detect_state(
        rows
    )

    # -----------------------------------------------------
    # 趋势明显时，提高趋势模型
    # -----------------------------------------------------

    if state["trend"] != "neutral":
        weights["trend"] += 0.05

    # -----------------------------------------------------
    # 大小明显偏态
    # -----------------------------------------------------

    if state["size"] != "balanced":
        weights["size"] += 0.025

    # -----------------------------------------------------
    # 单双明显偏态
    # -----------------------------------------------------

    if state["parity"] != "balanced":
        weights["parity"] += 0.025

    # -----------------------------------------------------
    # 波色明显偏态
    # -----------------------------------------------------

    if state["wave"].endswith("_hot"):
        weights["wave"] += 0.025

    # -----------------------------------------------------
    # 近期数据优先
    # -----------------------------------------------------

    weights["recent"] += 0.025

    # -----------------------------------------------------
    # 归一化
    # -----------------------------------------------------

    total = sum(
        weights.values()
    )

    if total <= 0:

        return dict(
            DEFAULT_WEIGHTS
        )

    return {
        key: value / total
        for key, value in weights.items()
    }


# =========================================================
# 综合策略
# =========================================================

def combine_strategies(rows):

    if not rows:

        empty = {
            n: 0.5
            for n in NUMBERS
        }

        return empty, {}, {}


    strategies = {

        "recent":
            strategy_recent(rows),

        "medium":
            strategy_medium(rows),

        "long":
            strategy_long(rows),

        "omission":
            strategy_omission(rows),

        "trend":
            strategy_trend(rows),

        "size":
            strategy_size(rows),

        "parity":
            strategy_parity(rows),

        "wave":
            strategy_wave(rows),

    }


    weights = calculate_dynamic_weights(
        rows
    )


    final_scores = {
        n: 0.0
        for n in NUMBERS
    }


    for name, scores in strategies.items():

        weight = weights.get(
            name,
            0.0
        )

        for n in NUMBERS:

            final_scores[n] += (
                scores.get(n, 0.0)
                * weight
            )


    final_scores = normalize_scores(
        final_scores
    )


    final_scores = apply_state_adjustment(
        final_scores,
        rows
    )


    return (
        final_scores,
        strategies,
        weights
    )


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    rows = [

        {
            "numbers":
                "38,26,08,06,29,18,23"
        },

        {
            "numbers":
                "33,27,16,28,04,25,14"
        },

        {
            "numbers":
                "47,14,44,32,07,37,11"
        },

    ]

    print("=" * 70)
    print("V2.0 strategies.py")
    print("=" * 70)

    scores, strategy_scores, weights = (
        combine_strategies(rows)
    )

    print("\n动态权重：")

    for name, weight in weights.items():

        print(
            f"{name:<10} "
            f"{weight:.4f}"
        )

    print("\nTop10：")

    ranking = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    for i, (number, score) in enumerate(
        ranking,
        1
    ):

        print(
            f"{i:02d}. "
            f"{number:02d} "
            f"{score:.6f}"
        )
