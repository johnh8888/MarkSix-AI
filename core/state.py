# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
状态识别引擎
"""

from collections import Counter
from typing import Dict, Any

from core.features import (
    get_special,
    get_size,
    get_odd_even,
    get_wave,
    wave_features,
)


# =========================================================
# 基础统计
# =========================================================

def _valid_numbers(rows):

    result = []

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:
            result.append(n)

    return result


# =========================================================
# 大小状态
# =========================================================

def detect_size_state(
    rows
) -> Dict[str, Any]:

    numbers = _valid_numbers(rows)

    if not numbers:

        return {
            "state": "unknown",
            "prob_big": 0.5,
            "strength": 0.0,
        }

    big = sum(
        n >= 25
        for n in numbers
    )

    total = len(numbers)

    prob_big = big / total

    deviation = abs(
        prob_big - 0.5
    ) * 2

    if prob_big >= 0.65:

        state = "big_hot"

    elif prob_big <= 0.35:

        state = "small_hot"

    else:

        state = "balanced"

    return {

        "state":
            state,

        "prob_big":
            prob_big,

        "strength":
            deviation,
    }


# =========================================================
# 单双状态
# =========================================================

def detect_parity_state(
    rows
) -> Dict[str, Any]:

    numbers = _valid_numbers(rows)

    if not numbers:

        return {
            "state": "unknown",
            "prob_odd": 0.5,
            "strength": 0.0,
        }

    odd = sum(
        n % 2 == 1
        for n in numbers
    )

    total = len(numbers)

    prob_odd = odd / total

    deviation = abs(
        prob_odd - 0.5
    ) * 2

    if prob_odd >= 0.65:

        state = "odd_hot"

    elif prob_odd <= 0.35:

        state = "even_hot"

    else:

        state = "balanced"

    return {

        "state":
            state,

        "prob_odd":
            prob_odd,

        "strength":
            deviation,
    }


# =========================================================
# 波色状态
# =========================================================

def detect_wave_state(
    rows
) -> Dict[str, Any]:

    features = wave_features(
        rows
    )

    deviation = features[
        "deviation"
    ]

    transition = features[
        "transition"
    ]

    latest = features[
        "latest"
    ]

    streak_length = features[
        "streak_length"
    ]

    strongest = max(
        deviation,
        key=deviation.get
    )

    strength = abs(
        deviation[strongest]
    )

    if strength >= 0.12:

        state = (
            f"{strongest}_trend"
        )

    elif streak_length >= 3:

        state = "streak"

    else:

        state = "balanced"

    return {

        "state":
            state,

        "latest":
            latest,

        "streak":
            streak_length,

        "strength":
            strength,

        "transition":
            transition,

        "entropy":
            features["entropy"],
    }


# =========================================================
# 数字趋势
# =========================================================

def detect_number_trend(
    rows
) -> Dict[str, Any]:

    short = _valid_numbers(
        rows[:12]
    )

    medium = _valid_numbers(
        rows[:36]
    )

    long = _valid_numbers(
        rows[:120]
    )

    if len(short) < 5:

        return {
            "state": "unknown",
            "strength": 0.0,
        }

    short_avg = (
        sum(short)
        / len(short)
    )

    medium_avg = (
        sum(medium)
        / len(medium)
        if medium
        else short_avg
    )

    long_avg = (
        sum(long)
        / len(long)
        if long
        else medium_avg
    )

    short_diff = (
        short_avg
        - medium_avg
    )

    medium_diff = (
        medium_avg
        - long_avg
    )

    score = (
        0.65 * short_diff
        + 0.35 * medium_diff
    )

    if score >= 2.5:

        state = "up"

    elif score <= -2.5:

        state = "down"

    else:

        state = "neutral"

    strength = min(
        abs(score) / 10.0,
        1.0
    )

    return {

        "state":
            state,

        "strength":
            strength,

        "score":
            score,

        "short_avg":
            short_avg,

        "medium_avg":
            medium_avg,

        "long_avg":
            long_avg,
    }


# =========================================================
# 趋势稳定性
# =========================================================

def trend_stability(
    rows
) -> float:

    short = _valid_numbers(
        rows[:12]
    )

    medium = _valid_numbers(
        rows[:36]
    )

    if len(short) < 5:
        return 0.0

    if len(medium) < 10:
        return 0.0

    short_avg = (
        sum(short)
        / len(short)
    )

    medium_avg = (
        sum(medium)
        / len(medium)
    )

    diff = abs(
        short_avg
        - medium_avg
    )

    return min(
        diff / 8.0,
        1.0
    )


# =========================================================
# 混沌程度
# =========================================================

def calculate_chaos(
    rows
) -> float:

    numbers = _valid_numbers(
        rows[:36]
    )

    if len(numbers) < 10:

        return 1.0

    # -----------------------------------------------------
    # 号码分布熵
    # -----------------------------------------------------

    counter = Counter(numbers)

    total = len(numbers)

    entropy = 0.0

    for count in counter.values():

        p = count / total

        entropy -= (
            p
            * __import__("math").log(p)
        )

    max_entropy = __import__(
        "math"
    ).log(49)

    number_entropy = (
        entropy / max_entropy
        if max_entropy > 0
        else 1.0
    )

    # -----------------------------------------------------
    # 波色熵
    # -----------------------------------------------------

    wave = wave_features(
        rows
    )

    wave_entropy_value = wave[
        "entropy"
    ]

    # -----------------------------------------------------
    # 趋势稳定性
    # -----------------------------------------------------

    stability = trend_stability(
        rows
    )

    # 越没有明显趋势，越混沌
    trend_chaos = 1.0 - stability

    chaos = (
        0.40 * number_entropy
        + 0.30 * wave_entropy_value
        + 0.30 * trend_chaos
    )

    return max(
        0.0,
        min(
            1.0,
            chaos
        )
    )


# =========================================================
# 总状态
# =========================================================

def detect_market_state(
    rows
) -> Dict[str, Any]:

    if len(rows) < 12:

        return {

            "state":
                "unknown",

            "confidence":
                0.0,

            "window_mode":
                "normal",

            "size":
                {},

            "parity":
                {},

            "wave":
                {},

            "trend":
                {},

            "chaos":
                1.0,
        }


    size = detect_size_state(
        rows
    )

    parity = detect_parity_state(
        rows
    )

    wave = detect_wave_state(
        rows
    )

    trend = detect_number_trend(
        rows
    )

    chaos = calculate_chaos(
        rows
    )


    # =====================================================
    # 趋势强度
    # =====================================================

    trend_strength = trend.get(
        "strength",
        0.0
    )

    size_strength = size.get(
        "strength",
        0.0
    )

    parity_strength = parity.get(
        "strength",
        0.0
    )

    wave_strength = wave.get(
        "strength",
        0.0
    )


    structural_strength = (
        0.25 * size_strength
        + 0.25 * parity_strength
        + 0.25 * wave_strength
        + 0.25 * trend_strength
    )


    # =====================================================
    # 最终状态
    # =====================================================

    if chaos >= 0.78:

        state = "chaos"

        confidence = chaos

        window_mode = "long"


    elif (
        trend_strength >= 0.35
        or wave_strength >= 0.15
    ):

        state = "trend"

        confidence = min(
            0.95,
            0.50
            + structural_strength
        )

        window_mode = "short"


    else:

        state = "normal"

        confidence = max(
            0.45,
            1.0 - chaos
        )

        window_mode = "balanced"


    # =====================================================
    # 动态窗口权重
    # =====================================================

    if state == "trend":

        window_weights = {

            "short": 0.50,

            "medium": 0.30,

            "long": 0.20,
        }

    elif state == "chaos":

        window_weights = {

            "short": 0.20,

            "medium": 0.35,

            "long": 0.45,
        }

    else:

        window_weights = {

            "short": 0.35,

            "medium": 0.35,

            "long": 0.30,
        }


    return {

        "state":
            state,

        "confidence":
            round(
                confidence,
                4
            ),

        "window_mode":
            window_mode,

        "window_weights":
            window_weights,

        "size":
            size,

        "parity":
            parity,

        "wave":
            wave,

        "trend":
            trend,

        "chaos":
            round(
                chaos,
                4
            ),
    }