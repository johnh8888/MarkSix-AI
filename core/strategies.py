# -*- coding: utf-8 -*-

from collections import Counter

from .features import (
    get_special,
    special_frequency,
    special_omission,
)


def normalize_scores(scores):

    if not scores:
        return {}

    values = list(scores.values())

    low = min(values)
    high = max(values)

    if high == low:

        return {
            k: 0.5
            for k in scores
        }

    return {
        k: (
            (v - low) /
            (high - low)
        )
        for k, v in scores.items()
    }


# =========================================
# 策略1：近期频率
# =========================================

def strategy_recent(rows):

    rows = rows[:30]

    freq = special_frequency(rows)

    return normalize_scores(freq)


# =========================================
# 策略2：中期频率
# =========================================

def strategy_medium(rows):

    rows = rows[:100]

    freq = special_frequency(rows)

    return normalize_scores(freq)


# =========================================
# 策略3：长期频率
# =========================================

def strategy_long(rows):

    rows = rows[:300]

    freq = special_frequency(rows)

    return normalize_scores(freq)


# =========================================
# 策略4：遗漏
# =========================================

def strategy_omission(rows):

    omission = special_omission(
        rows[:300]
    )

    return normalize_scores(
        omission
    )


# =========================================
# 策略5：大小
# =========================================

def strategy_size(rows):

    counter = Counter()

    for row in rows[:100]:

        n = get_special(row)

        if n >= 25:
            counter["big"] += 1
        else:
            counter["small"] += 1

    total = (
        counter["big"] +
        counter["small"]
    )

    if total == 0:
        return {
            n: 0.5
            for n in range(1, 50)
        }

    big_prob = (
        counter["big"] / total
    )

    small_prob = (
        counter["small"] / total
    )

    scores = {}

    for n in range(1, 50):

        if n >= 25:
            scores[n] = big_prob
        else:
            scores[n] = small_prob

    return scores


# =========================================
# 策略6：单双
# =========================================

def strategy_parity(rows):

    odd = 0
    even = 0

    for row in rows[:100]:

        n = get_special(row)

        if n % 2:
            odd += 1
        else:
            even += 1

    total = odd + even

    if total == 0:

        return {
            n: 0.5
            for n in range(1, 50)
        }

    odd_prob = odd / total
    even_prob = even / total

    scores = {}

    for n in range(1, 50):

        if n % 2:
            scores[n] = odd_prob
        else:
            scores[n] = even_prob

    return scores


# =========================================
# 综合策略
# =========================================

def combine_strategies(rows):

    strategies = {

        "recent":
            strategy_recent(rows),

        "medium":
            strategy_medium(rows),

        "long":
            strategy_long(rows),

        "omission":
            strategy_omission(rows),

        "size":
            strategy_size(rows),

        "parity":
            strategy_parity(rows),
    }

    # 第一版先使用保守固定权重
    weights = {

        "recent": 0.25,

        "medium": 0.20,

        "long": 0.15,

        "omission": 0.10,

        "size": 0.15,

        "parity": 0.15,
    }

    final_scores = {
        n: 0.0
        for n in range(1, 50)
    }

    for strategy_name, scores in strategies.items():

        weight = weights[strategy_name]

        for n in range(1, 50):

            final_scores[n] += (
                scores.get(n, 0.0)
                * weight
            )

    return final_scores, strategies
