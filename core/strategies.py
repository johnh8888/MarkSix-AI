# -*- coding: utf-8 -*-

"""
六合彩策略模块 V1.2

功能：

1. 近期频率
2. 中期频率
3. 长期频率
4. 遗漏
5. 大小
6. 单双
7. 波色
8. 综合49码评分

重要：

数据库没有 special 字段。

特码统一：

numbers 第7个号码
"""

from collections import Counter

from .features import (
    get_special,
    special_frequency,
    special_omission,
    get_wave,
)


# =========================================================
# 分数归一化
# =========================================================

def normalize_scores(scores):

    if not scores:

        return {
            n: 0.5
            for n in range(1, 50)
        }

    values = list(scores.values())

    low = min(values)
    high = max(values)

    if high == low:

        return {
            n: 0.5
            for n in range(1, 50)
        }

    return {
        n: (
            (scores.get(n, low) - low)
            / (high - low)
        )
        for n in range(1, 50)
    }


# =========================================================
# 策略1：近期频率
# =========================================================

def strategy_recent(rows):

    freq = special_frequency(
        rows[:30]
    )

    scores = normalize_scores(freq)

    return {
        n: scores.get(n, 0.0)
        for n in range(1, 50)
    }


# =========================================================
# 策略2：中期频率
# =========================================================

def strategy_medium(rows):

    freq = special_frequency(
        rows[:100]
    )

    scores = normalize_scores(freq)

    return {
        n: scores.get(n, 0.0)
        for n in range(1, 50)
    }


# =========================================================
# 策略3：长期频率
# =========================================================

def strategy_long(rows):

    freq = special_frequency(
        rows[:300]
    )

    scores = normalize_scores(freq)

    return {
        n: scores.get(n, 0.0)
        for n in range(1, 50)
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
        for n in range(1, 50)
    }


# =========================================================
# 策略5：大小
# =========================================================

def strategy_size(rows):

    big = 0
    small = 0

    for row in rows[:100]:

        n = get_special(row)

        if not 1 <= n <= 49:
            continue

        if n >= 25:
            big += 1
        else:
            small += 1

    total = big + small

    if total == 0:

        return {
            n: 0.5
            for n in range(1, 50)
        }

    big_prob = big / total
    small_prob = small / total

    return {

        n:
            big_prob
            if n >= 25
            else small_prob

        for n in range(1, 50)
    }


# =========================================================
# 策略6：单双
# =========================================================

def strategy_parity(rows):

    odd = 0
    even = 0

    for row in rows[:100]:

        n = get_special(row)

        if not 1 <= n <= 49:
            continue

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

    return {

        n:
            odd_prob
            if n % 2
            else even_prob

        for n in range(1, 50)
    }


# =========================================================
# 策略7：波色
# =========================================================

def strategy_wave(rows):

    counter = Counter()

    for row in rows[:100]:

        n = get_special(row)

        if not 1 <= n <= 49:
            continue

        wave = get_wave(n)

        if wave in ("红", "蓝", "绿"):
            counter[wave] += 1

    total = sum(counter.values())

    if total == 0:

        return {
            n: 1 / 3
            for n in range(1, 50)
        }

    wave_probability = {

        wave:
            counter.get(wave, 0) / total

        for wave in ("红", "蓝", "绿")
    }

    return {

        n:
            wave_probability.get(
                get_wave(n),
                1 / 3
            )

        for n in range(1, 50)
    }


# =========================================================
# 综合策略
# =========================================================

def combine_strategies(rows):

    if not rows:

        empty = {
            n: 0.5
            for n in range(1, 50)
        }

        return empty, {}


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

        "wave":
            strategy_wave(rows),
    }


    # =====================================================
    # 权重
    # =====================================================

    weights = {

        "recent": 0.22,

        "medium": 0.18,

        "long": 0.12,

        "omission": 0.10,

        "size": 0.13,

        "parity": 0.10,

        "wave": 0.15,
    }


    # =====================================================
    # 综合
    # =====================================================

    final_scores = {
        n: 0.0
        for n in range(1, 50)
    }


    for strategy_name, scores in strategies.items():

        weight = weights.get(
            strategy_name,
            0.0
        )

        for n in range(1, 50):

            final_scores[n] += (
                scores.get(n, 0.0)
                * weight
            )


    # =====================================================
    # 最终归一化
    # =====================================================

    final_scores = normalize_scores(
        final_scores
    )


    return (
        final_scores,
        strategies
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
    print("六合彩策略模块 V1.2")
    print("=" * 70)

    scores, strategy_scores = combine_strategies(
        rows
    )

    print()
    print("49码综合评分 TOP10")
    print("-" * 70)

    top10 = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    for rank, (number, score) in enumerate(
        top10,
        1
    ):

        print(
            f"{rank:02d}. "
            f"{number:02d} "
            f"-> {score:.6f}"
        )
