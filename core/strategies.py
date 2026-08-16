# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
号码策略引擎

模块：

1. recent
2. medium
3. long
4. omission
5. trend
6. transition
7. size
8. parity
9. wave
10. tail
11. zone

所有模块：

输入：
    当前时刻以前的数据

输出：
    1~49 每个号码的 0~1 相对评分
"""

from typing import Dict

from .features import (
    NUMBERS,
    safe_special,
    get_size,
    get_odd_even,
    get_wave,
    get_tail,
    get_zone,
    special_frequency,
    omission_score,
    number_trend_score,
    number_hot_score,
    tail_probability,
    zone_probability,
)

from .wave_model import (
    wave_probabilities,
)


# =========================================================
# 归一化
# =========================================================

def normalize_scores(
    scores: Dict[int, float]
):

    if not scores:

        return {

            n:
                0.5

            for n in NUMBERS

        }


    values = list(
        scores.values()
    )


    low = min(values)

    high = max(values)


    if high == low:

        return {

            n:
                0.5

            for n in scores

        }


    return {

        n:
            (
                scores[n]
                - low
            )
            / (
                high - low
            )

        for n in scores

    }


# =========================================================
# 平滑
# =========================================================

def smooth_scores(
    scores,
    alpha=0.10
):

    return {

        n:
            (
                scores.get(
                    n,
                    0
                )
                * (1 - alpha)
            )
            +
            (
                0.5
                * alpha
            )

        for n in NUMBERS

    }


# =========================================================
# 近期频率
# =========================================================

def strategy_recent(
    rows
):

    frequency = special_frequency(
        rows[:12]
    )


    scores = {

        n:
            frequency.get(
                n,
                0
            )

        for n in NUMBERS

    }


    return normalize_scores(
        scores
    )


# =========================================================
# 中期频率
# =========================================================

def strategy_medium(
    rows
):

    frequency = special_frequency(
        rows[:36]
    )


    scores = {

        n:
            frequency.get(
                n,
                0
            )

        for n in NUMBERS

    }


    return normalize_scores(
        scores
    )


# =========================================================
# 长期频率
# =========================================================

def strategy_long(
    rows
):

    frequency = special_frequency(
        rows[:120]
    )


    scores = {

        n:
            frequency.get(
                n,
                0
            )

        for n in NUMBERS

    }


    return normalize_scores(
        scores
    )


# =========================================================
# 遗漏
# =========================================================

def strategy_omission(
    rows
):

    scores = omission_score(
        rows,
        120
    )


    return normalize_scores(
        scores
    )


# =========================================================
# 趋势
# =========================================================

def strategy_trend(
    rows
):

    scores = (
        number_trend_score(
            rows,
            12,
            36
        )
    )


    # 正趋势和负趋势都保留，
    # 不直接认为“越热越好”。

    return normalize_scores(
        scores
    )


# =========================================================
# 转移
# =========================================================

def strategy_transition(
    rows
):

    # -----------------------------------------------------
    # 数字之间的直接转移：
    #
    # 上一期特码 -> 下一期特码
    #
    # 使用 Laplace smoothing
    # -----------------------------------------------------

    previous = safe_special(
        rows[0]
    ) if rows else None


    counts = {

        n:
            1.0

        for n in NUMBERS

    }


    if previous is None:

        return normalize_scores(
            counts
        )


    total = 0


    for index in range(
        len(rows) - 1
    ):

        current = safe_special(
            rows[index]
        )

        next_number = safe_special(
            rows[index + 1]
        )


        if (
            current == previous
            and next_number is not None
        ):

            counts[next_number] += 1

            total += 1


    if total <= 0:

        return normalize_scores(
            counts
        )


    return normalize_scores(
        counts
    )


# =========================================================
# 大小模型
# =========================================================

def strategy_size(
    rows
):

    data = rows[:36]


    big = 0

    small = 0


    for row in data:

        number = safe_special(
            row
        )

        if number is None:
            continue


        if number >= 25:
            big += 1

        else:
            small += 1


    total = (
        big
        + small
    )


    if total <= 0:

        return {

            n:
                0.5

            for n in NUMBERS

        }


    big_probability = (
        big + 1
    ) / (
        total + 2
    )


    small_probability = (
        small + 1
    ) / (
        total + 2
    )


    scores = {}


    for number in NUMBERS:

        if number >= 25:

            scores[number] = (
                big_probability
            )

        else:

            scores[number] = (
                small_probability
            )


    return normalize_scores(
        scores
    )


# =========================================================
# 单双模型
# =========================================================

def strategy_parity(
    rows
):

    data = rows[:36]


    odd = 0

    even = 0


    for row in data:

        number = safe_special(
            row
        )

        if number is None:
            continue


        if number % 2:

            odd += 1

        else:

            even += 1


    total = (
        odd
        + even
    )


    if total <= 0:

        return {

            n:
                0.5

            for n in NUMBERS

        }


    odd_probability = (
        odd + 1
    ) / (
        total + 2
    )


    even_probability = (
        even + 1
    ) / (
        total + 2
    )


    scores = {}


    for number in NUMBERS:

        if number % 2:

            scores[number] = (
                odd_probability
            )

        else:

            scores[number] = (
                even_probability
            )


    return normalize_scores(
        scores
    )


# =========================================================
# 波色模型
# =========================================================

def strategy_wave(
    rows
):

    probabilities = (
        wave_probabilities(
            rows
        )
    )


    scores = {}


    for number in NUMBERS:

        wave = get_wave(
            number
        )


        scores[number] = (
            probabilities.get(
                wave,
                1 / 3
            )
        )


    return normalize_scores(
        scores
    )


# =========================================================
# 尾数模型
# =========================================================

def strategy_tail(
    rows
):

    probabilities = (
        tail_probability(
            rows,
            36
        )
    )


    scores = {}


    for number in NUMBERS:

        tail = get_tail(
            number
        )


        scores[number] = (
            probabilities.get(
                tail,
                0.1
            )
        )


    return normalize_scores(
        scores
    )


# =========================================================
# 分区模型
# =========================================================

def strategy_zone(
    rows
):

    probabilities = (
        zone_probability(
            rows,
            36
        )
    )


    scores = {}


    for number in NUMBERS:

        zone = get_zone(
            number
        )


        scores[number] = (
            probabilities.get(
                zone,
                0.2
            )
        )


    return normalize_scores(
        scores
    )


# =========================================================
# 全部策略
# =========================================================

def build_strategies(
    rows
):

    return {

        "recent":
            strategy_recent(
                rows
            ),

        "medium":
            strategy_medium(
                rows
            ),

        "long":
            strategy_long(
                rows
            ),

        "omission":
            strategy_omission(
                rows
            ),

        "trend":
            strategy_trend(
                rows
            ),

        "transition":
            strategy_transition(
                rows
            ),

        "size":
            strategy_size(
                rows
            ),

        "parity":
            strategy_parity(
                rows
            ),

        "wave":
            strategy_wave(
                rows
            ),

        "tail":
            strategy_tail(
                rows
            ),

        "zone":
            strategy_zone(
                rows
            ),

    }


# =========================================================
# 融合策略
# =========================================================

def combine_strategies(
    rows,
    weights
):

    strategies = build_strategies(
        rows
    )


    final_scores = {

        n:
            0.0

        for n in NUMBERS

    }


    for module, scores in strategies.items():

        weight = weights.get(
            module,
            0.0
        )


        for number in NUMBERS:

            final_scores[number] += (

                scores.get(
                    number,
                    0.5
                )

                *

                weight

            )


    final_scores = normalize_scores(
        final_scores
    )


    final_scores = smooth_scores(
        final_scores,
        0.08
    )


    return {

        "scores":
            normalize_scores(
                final_scores
            ),

        "strategies":
            strategies,

    }