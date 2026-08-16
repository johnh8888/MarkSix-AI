# -*- coding: utf-8 -*-

"""
V3.0 多策略引擎
"""

import math

from collections import Counter

from typing import Any, Dict, List

from core.config import (
    SHORT_WINDOW,
    MEDIUM_WINDOW,
    LONG_WINDOW,
    DEFAULT_MODULE_WEIGHTS,
)

from .wave_model import (
    NUMBER_TO_WAVE,
    wave_probabilities,
    combined_wave_probabilities,
)

from .state_engine import (
    analyze_state,
)


# =========================================================
# 工具
# =========================================================

def clamp(
    value,
    low=0.0,
    high=1.0
):

    return max(
        low,
        min(high, value)
    )


def normalize_scores(
    scores
):

    if not scores:
        return {}

    values = list(
        scores.values()
    )

    low = min(values)

    high = max(values)

    if abs(high - low) < 1e-12:

        return {
            n: 0.5
            for n in scores
        }

    return {

        n:
            (value - low)
            / (high - low)

        for n, value in scores.items()
    }


# =========================================================
# 特码历史
# =========================================================

def special_numbers(
    rows
):

    result = []

    for row in rows:

        n = row.get(
            "special"
        )

        if n is not None:

            try:

                n = int(n)

                if 1 <= n <= 49:
                    result.append(n)

            except Exception:
                pass

    return result


# =========================================================
# 近期频率
# =========================================================

def recent_score(
    rows
):

    scores = {
        n: 0.0
        for n in range(1, 50)
    }

    subset = rows[
        :SHORT_WINDOW
    ]

    for index, row in enumerate(
        subset
    ):

        n = row.get("special")

        if n is None:
            continue

        decay = math.exp(
            -index / max(
                SHORT_WINDOW,
                1
            )
        )

        scores[int(n)] += decay

    return normalize_scores(
        scores
    )


# =========================================================
# 中期
# =========================================================

def medium_score(
    rows
):

    scores = {
        n: 0.0
        for n in range(1, 50)
    }

    subset = rows[
        :MEDIUM_WINDOW
    ]

    for row in subset:

        n = row.get("special")

        if n is not None:

            scores[int(n)] += 1

    return normalize_scores(
        scores
    )


# =========================================================
# 长期
# =========================================================

def long_score(
    rows
):

    scores = {
        n: 0.0
        for n in range(1, 50)
    }

    subset = rows[
        :LONG_WINDOW
    ]

    for row in subset:

        n = row.get("special")

        if n is not None:

            scores[int(n)] += 1

    return normalize_scores(
        scores
    )


# =========================================================
# 遗漏
# =========================================================

def omission_score(
    rows
):

    scores = {}

    last_seen = {}

    for n in range(1, 50):

        last_seen[n] = None

    for index, row in enumerate(rows):

        n = row.get("special")

        if n is None:
            continue

        n = int(n)

        if last_seen[n] is None:

            last_seen[n] = index

    max_omission = max(
        [
            x
            for x in last_seen.values()
            if x is not None
        ] or [1]
    )

    for n in range(1, 50):

        omission = last_seen[n]

        if omission is None:

            omission = len(rows)

        scores[n] = (
            omission / max(
                len(rows),
                1
            )
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 趋势
# =========================================================

def trend_score(
    rows
):

    recent = recent_score(
        rows
    )

    medium = medium_score(
        rows
    )

    return {

        n:
            clamp(
                recent[n] * 0.65
                +
                medium[n] * 0.35
            )

        for n in range(1, 50)
    }


# =========================================================
# 转移
# =========================================================

def transition_score(
    rows
):

    scores = {
        n: 0.0
        for n in range(1, 50)
    }

    if not rows:
        return scores

    latest = rows[0].get(
        "special"
    )

    if latest is None:
        return scores

    latest = int(latest)

    latest_wave = NUMBER_TO_WAVE.get(
        latest
    )

    if latest_wave is None:
        return scores

    historical = rows[
        1:MEDIUM_WINDOW
    ]

    for row in historical:

        n = row.get("special")

        if n is None:
            continue

        wave = NUMBER_TO_WAVE.get(
            int(n)
        )

        if wave != latest_wave:

            scores[int(n)] += 1

    return normalize_scores(
        scores
    )


# =========================================================
# 大小
# =========================================================

def size_score(
    rows
):

    state = analyze_state(
        rows,
        MEDIUM_WINDOW
    )

    big_probability = state[
        "size"
    ]["big"]

    scores = {}

    for n in range(1, 50):

        number_is_big = (
            n >= 25
        )

        target = (
            big_probability
            if number_is_big
            else
            1 - big_probability
        )

        scores[n] = target

    return scores


# =========================================================
# 单双
# =========================================================

def parity_score(
    rows
):

    state = analyze_state(
        rows,
        MEDIUM_WINDOW
    )

    odd_probability = state[
        "parity"
    ]["单"]

    scores = {}

    for n in range(1, 50):

        if n % 2:

            scores[n] = odd_probability

        else:

            scores[n] = (
                1 - odd_probability
            )

    return scores


# =========================================================
# 波色
# =========================================================

def wave_score(
    rows
):

    probabilities = combined_wave_probabilities(
        rows,
        MEDIUM_WINDOW
    )

    scores = {}

    for n in range(1, 50):

        wave = NUMBER_TO_WAVE.get(
            n
        )

        scores[n] = probabilities.get(
            wave,
            1 / 3
        )

    return scores


# =========================================================
# 尾数
# =========================================================

def tail_score(
    rows
):

    counter = Counter()

    for row in rows[
        :MEDIUM_WINDOW
    ]:

        n = row.get("special")

        if n is not None:

            counter[
                int(n) % 10
            ] += 1

    total = sum(
        counter.values()
    )

    if total == 0:

        return {
            n: 0.5
            for n in range(1, 50)
        }

    return {

        n:
            (
                counter.get(
                    n % 10,
                    0
                ) + 1
            )
            /
            (
                total + 10
            )

        for n in range(1, 50)
    }


# =========================================================
# 区间
# =========================================================

def zone_score(
    rows
):

    counter = Counter()

    for row in rows[
        :MEDIUM_WINDOW
    ]:

        n = row.get("special")

        if n is None:
            continue

        n = int(n)

        if n <= 16:
            zone = 1
        elif n <= 33:
            zone = 2
        else:
            zone = 3

        counter[zone] += 1

    total = sum(
        counter.values()
    )

    scores = {}

    for n in range(1, 50):

        if n <= 16:
            zone = 1
        elif n <= 33:
            zone = 2
        else:
            zone = 3

        if total:

            scores[n] = (
                counter.get(
                    zone,
                    0
                ) + 1
            ) / (
                total + 3
            )

        else:

            scores[n] = 1 / 3

    return scores


# =========================================================
# 所有策略
# =========================================================

def build_strategy_result(
    rows
):

    return {

        "recent":
            recent_score(rows),

        "medium":
            medium_score(rows),

        "long":
            long_score(rows),

        "omission":
            omission_score(rows),

        "trend":
            trend_score(rows),

        "transition":
            transition_score(rows),

        "size":
            size_score(rows),

        "parity":
            parity_score(rows),

        "wave":
            wave_score(rows),

        "tail":
            tail_score(rows),

        "zone":
            zone_score(rows),
    }


# =========================================================
# 动态权重
# =========================================================

def get_dynamic_weights(
    rows
):

    weights = dict(
        DEFAULT_MODULE_WEIGHTS
    )

    if len(rows) < 20:

        return weights

    # -----------------------------------------------------
    # 最近数据作为轻度自适应依据
    # -----------------------------------------------------

    numbers = special_numbers(
        rows[:MEDIUM_WINDOW]
    )

    if not numbers:
        return weights

    counter = Counter(
        numbers
    )

    # 最近频率离散度
    values = list(
        counter.values()
    )

    if values:

        average = (
            sum(values)
            /
            len(values)
        )

        if average > 0:

            concentration = (
                max(values)
                /
                average
            )

            if concentration > 2:

                weights["recent"] += 0.02

                weights["trend"] += 0.02

                weights["long"] -= 0.01

                weights["omission"] -= 0.01

    # -----------------------------------------------------
    # 重新归一化
    # -----------------------------------------------------

    for key in weights:

        weights[key] = max(
            0.01,
            weights[key]
        )

    total = sum(
        weights.values()
    )

    return {
        key:
            value / total
        for key, value in weights.items()
    }


# =========================================================
# 综合策略
# =========================================================

def combine_strategies(
    strategy_result,
    weights=None
):

    if weights is None:

        weights = dict(
            DEFAULT_MODULE_WEIGHTS
        )

    combined = {
        n: 0.0
        for n in range(1, 50)
    }

    total_weight = 0.0

    for module, scores in strategy_result.items():

        weight = float(
            weights.get(
                module,
                0
            )
        )

        if weight <= 0:
            continue

        total_weight += weight

        for n in range(1, 50):

            combined[n] += (
                weight
                *
                float(
                    scores.get(
                        n,
                        0.0
                    )
                )
            )

    if total_weight > 0:

        for n in combined:

            combined[n] /= total_weight

    return combined