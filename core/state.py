# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
状态识别引擎
"""

from collections import Counter
from typing import Dict

from core.config import (
    SHORT_WINDOW,
    MEDIUM_WINDOW,
    LONG_WINDOW,
)

from core.features import (
    get_special,
    get_size,
    get_odd_even,
    get_wave,
    wave_entropy,
)


# =========================================================
# 基础比例
# =========================================================

def ratio(
    value,
    total
):

    if total <= 0:
        return 0.0

    return value / total


# =========================================================
# 状态识别
# =========================================================

def detect_state(
    rows
) -> Dict:

    if not rows:

        return {

            "state":
                "chaos",

            "confidence":
                0.0,

            "size":
                "unknown",

            "parity":
                "unknown",

            "wave":
                "unknown",

            "trend":
                "neutral",
        }

    short = rows[
        :SHORT_WINDOW
    ]

    medium = rows[
        :MEDIUM_WINDOW
    ]

    # =====================================================
    # 大小
    # =====================================================

    size_counter = Counter()

    for row in short:

        n = get_special(row)

        if 1 <= n <= 49:

            size_counter[
                get_size(n)
            ] += 1

    size_total = sum(
        size_counter.values()
    )

    if size_total:

        big_ratio = ratio(
            size_counter["大"],
            size_total
        )

        small_ratio = ratio(
            size_counter["小"],
            size_total
        )

        if big_ratio >= 0.67:
            size_state = "big"

        elif small_ratio >= 0.67:
            size_state = "small"

        else:
            size_state = "balanced"

    else:

        size_state = "unknown"


    # =====================================================
    # 单双
    # =====================================================

    parity_counter = Counter()

    for row in short:

        n = get_special(row)

        if 1 <= n <= 49:

            parity_counter[
                get_odd_even(n)
            ] += 1

    parity_total = sum(
        parity_counter.values()
    )

    if parity_total:

        odd_ratio = ratio(
            parity_counter["单"],
            parity_total
        )

        even_ratio = ratio(
            parity_counter["双"],
            parity_total
        )

        if odd_ratio >= 0.67:
            parity_state = "odd"

        elif even_ratio >= 0.67:
            parity_state = "even"

        else:
            parity_state = "balanced"

    else:

        parity_state = "unknown"


    # =====================================================
    # 波色
    # =====================================================

    wave_counter = Counter()

    for row in short:

        n = get_special(row)

        if 1 <= n <= 49:

            wave = get_wave(n)

            if wave != "未知":

                wave_counter[
                    wave
                ] += 1

    wave_total = sum(
        wave_counter.values()
    )

    if wave_total:

        wave, count = (
            wave_counter
            .most_common(1)[0]
        )

        if count / wave_total >= 0.50:

            wave_state = (
                f"{wave}_hot"
            )

        else:

            wave_state = "balanced"

    else:

        wave_state = "unknown"


    # =====================================================
    # 数值趋势
    # =====================================================

    short_numbers = []

    medium_numbers = []

    for row in short:

        n = get_special(row)

        if 1 <= n <= 49:
            short_numbers.append(n)

    for row in medium:

        n = get_special(row)

        if 1 <= n <= 49:
            medium_numbers.append(n)

    if short_numbers and medium_numbers:

        short_avg = (
            sum(short_numbers)
            / len(short_numbers)
        )

        medium_avg = (
            sum(medium_numbers)
            / len(medium_numbers)
        )

        delta = (
            short_avg
            - medium_avg
        )

        if delta >= 3:
            trend_state = "up"

        elif delta <= -3:
            trend_state = "down"

        else:
            trend_state = "neutral"

    else:

        trend_state = "neutral"


    # =====================================================
    # 波色熵
    # =====================================================

    entropy = wave_entropy(
        short
    )


    # =====================================================
    # 综合状态
    # =====================================================

    signals = 0

    strong_signals = 0

    if size_state != "balanced":
        signals += 1

    if parity_state != "balanced":
        signals += 1

    if wave_state != "balanced":
        signals += 1

    if trend_state != "neutral":
        signals += 1

    if entropy < 0.88:
        strong_signals += 1


    # =====================================================
    # 状态判断
    # =====================================================

    if strong_signals >= 1 and signals >= 2:

        state = "trend"

    elif signals == 0 or entropy >= 0.96:

        state = "chaos"

    else:

        state = "normal"


    # =====================================================
    # 置信度
    # =====================================================

    confidence = (
        0.35
        + signals * 0.10
        + strong_signals * 0.10
    )

    confidence = min(
        max(confidence, 0.0),
        0.95
    )


    return {

        "state":
            state,

        "confidence":
            round(
                confidence,
                4
            ),

        "size":
            size_state,

        "parity":
            parity_state,

        "wave":
            wave_state,

        "trend":
            trend_state,

        "wave_entropy":
            round(
                entropy,
                4
            ),
    }


# =========================================================
# 动态窗口权重
# =========================================================

def get_window_weights(
    state: str
):

    if state == "trend":

        return {

            "short":
                0.50,

            "medium":
                0.30,

            "long":
                0.20,
        }

    if state == "chaos":

        return {

            "short":
                0.20,

            "medium":
                0.35,

            "long":
                0.45,
        }

    return {

        "short":
            0.35,

        "medium":
            0.35,

        "long":
            0.30,
    }


# =========================================================
# 状态完整信息
# =========================================================

def analyze_state(
    rows
):

    state_info = detect_state(
        rows
    )

    window_weights = (
        get_window_weights(
            state_info["state"]
        )
    )

    state_info[
        "window_weights"
    ] = window_weights

    return state_info