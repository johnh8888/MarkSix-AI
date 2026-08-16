# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
状态识别引擎

状态：

normal  正常
trend   趋势
chaos   混沌

注意：
状态识别只使用当前预测时刻以前的数据。
"""

from collections import Counter
import math

from .features import (
    NUMBERS,
    WAVES,
    safe_special,
    get_size,
    get_odd_even,
    get_wave,
    special_frequency,
    wave_entropy,
)


# =========================================================
# 基础概率
# =========================================================

def _distribution(
    rows,
    classifier
):

    counter = Counter()

    for row in rows:

        number = safe_special(row)

        if number is None:
            continue

        value = classifier(
            number
        )

        counter[value] += 1

    total = sum(
        counter.values()
    )

    if total <= 0:
        return {}

    return {
        key:
            value / total
        for key, value
        in counter.items()
    }


# =========================================================
# 熵
# =========================================================

def _entropy(values):

    if not values:
        return 0.0

    result = 0.0

    for value in values:

        if value <= 0:
            continue

        result -= (
            value
            * math.log(
                value,
                2
            )
        )

    return result


# =========================================================
# 分布偏离
# =========================================================

def _imbalance(
    distribution,
    expected
):

    if not distribution:
        return 0.0

    return max(
        abs(
            distribution.get(
                key,
                0
            )
            - expected
        )
        for key in distribution
    )


# =========================================================
# 数字集中度
# =========================================================

def number_concentration(
    rows,
    window=36
):

    data = rows[:window]

    frequency = special_frequency(
        data
    )

    total = sum(
        frequency.values()
    )

    if total <= 0:
        return 0.0

    top = sorted(
        frequency.values(),
        reverse=True
    )[:5]

    return sum(top) / total


# =========================================================
# 数字趋势
# =========================================================

def number_trend_strength(
    rows
):

    short = rows[:12]

    medium = rows[:36]

    if len(short) < 5:
        return 0.0

    if len(medium) < 12:
        return 0.0


    short_freq = special_frequency(
        short
    )

    medium_freq = special_frequency(
        medium
    )


    short_total = sum(
        short_freq.values()
    )

    medium_total = sum(
        medium_freq.values()
    )


    if (
        short_total <= 0
        or medium_total <= 0
    ):
        return 0.0


    differences = []


    for number in NUMBERS:

        short_rate = (
            short_freq.get(
                number,
                0
            )
            / short_total
        )

        medium_rate = (
            medium_freq.get(
                number,
                0
            )
            / medium_total
        )


        differences.append(
            abs(
                short_rate
                - medium_rate
            )
        )


    # 平均偏离程度
    value = sum(
        differences
    ) / len(
        differences
    )


    # 压缩到 0~1
    return min(
        value * 20,
        1.0
    )


# =========================================================
# 大小趋势
# =========================================================

def size_trend(
    rows
):

    short = _distribution(
        rows[:12],
        get_size
    )

    medium = _distribution(
        rows[:36],
        get_size
    )


    if not short or not medium:
        return 0.0


    difference = 0.0


    for key in (
        "大",
        "小",
    ):

        difference += abs(
            short.get(
                key,
                0
            )
            -
            medium.get(
                key,
                0
            )
        )


    return min(
        difference,
        1.0
    )


# =========================================================
# 单双趋势
# =========================================================

def parity_trend(
    rows
):

    short = _distribution(
        rows[:12],
        get_odd_even
    )

    medium = _distribution(
        rows[:36],
        get_odd_even
    )


    if not short or not medium:
        return 0.0


    difference = 0.0


    for key in (
        "单",
        "双",
    ):

        difference += abs(
            short.get(
                key,
                0
            )
            -
            medium.get(
                key,
                0
            )
        )


    return min(
        difference,
        1.0
    )


# =========================================================
# 波色趋势
# =========================================================

def wave_trend(
    rows
):

    short = _distribution(
        rows[:12],
        get_wave
    )

    medium = _distribution(
        rows[:36],
        get_wave
    )


    if not short or not medium:
        return 0.0


    difference = 0.0


    for wave in WAVES:

        difference += abs(
            short.get(
                wave,
                0
            )
            -
            medium.get(
                wave,
                0
            )
        )


    return min(
        difference,
        1.0
    )


# =========================================================
# 综合趋势强度
# =========================================================

def calculate_trend_strength(
    rows
):

    number_score = (
        number_trend_strength(
            rows
        )
    )

    size_score = (
        size_trend(
            rows
        )
    )

    parity_score = (
        parity_trend(
            rows
        )
    )

    wave_score = (
        wave_trend(
            rows
        )
    )


    result = (

        number_score * 0.40

        +

        size_score * 0.20

        +

        parity_score * 0.20

        +

        wave_score * 0.20

    )


    return min(
        max(
            result,
            0.0
        ),
        1.0
    )


# =========================================================
# 混沌程度
# =========================================================

def calculate_chaos_score(
    rows
):

    if len(rows) < 12:
        return 0.5


    wave_e = wave_entropy(
        rows[:36]
    )


    concentration = (
        number_concentration(
            rows,
            36
        )
    )


    # 波色越接近均匀，
    # 熵越高，结构越弱。
    #
    # 数字越分散，
    # 集中度越低，结构越弱。

    wave_chaos = wave_e

    number_chaos = (
        1.0
        - min(
            concentration * 2.5,
            1.0
        )
    )


    result = (

        wave_chaos * 0.45

        +

        number_chaos * 0.55

    )


    return min(
        max(
            result,
            0.0
        ),
        1.0
    )


# =========================================================
# 状态
# =========================================================

def detect_state(
    rows
):

    if len(rows) < 12:

        return {

            "state":
                "unknown",

            "label":
                "数据不足",

            "confidence":
                0.0,

            "trend_strength":
                0.0,

            "chaos_score":
                1.0,

        }


    trend_strength = (
        calculate_trend_strength(
            rows
        )
    )


    chaos_score = (
        calculate_chaos_score(
            rows
        )
    )


    # -----------------------------------------------------
    # 趋势优先
    # -----------------------------------------------------

    if (
        trend_strength >= 0.42
        and trend_strength > chaos_score
    ):

        state = "trend"

        label = "趋势增强"

        confidence = min(
            0.55
            + trend_strength * 0.45,
            0.95
        )


    elif chaos_score >= 0.62:

        state = "chaos"

        label = "混沌"

        confidence = min(
            0.55
            + chaos_score * 0.40,
            0.95
        )


    else:

        state = "normal"

        label = "正常"

        confidence = (
            1.0
            - abs(
                trend_strength
                - 0.30
            )
        )


        confidence = min(
            max(
                confidence,
                0.50
            ),
            0.90
        )


    return {

        "state":
            state,

        "label":
            label,

        "confidence":
            round(
                confidence,
                4
            ),

        "trend_strength":
            round(
                trend_strength,
                4
            ),

        "chaos_score":
            round(
                chaos_score,
                4
            ),

    }


# =========================================================
# 动态窗口权重
# =========================================================

def dynamic_window_weights(
    state
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


    # normal

    return {

        "short":
            0.35,

        "medium":
            0.35,

        "long":
            0.30,

    }


# =========================================================
# 状态完整报告
# =========================================================

def build_state_report(
    rows
):

    state = detect_state(
        rows
    )


    windows = dynamic_window_weights(
        state["state"]
    )


    return {

        **state,

        "windows":
            windows,

    }