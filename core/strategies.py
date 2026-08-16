# -*- coding: utf-8 -*-

from collections import Counter

from .features import (
    get_special,
    special_frequency,
    special_omission,
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
            k: 0.5
            for k in scores
        }

    return {

        k:
            (v - low) /
            (high - low)

        for k, v in scores.items()

    }


# =========================================================
# 策略1：近期频率
# =========================================================

def strategy_recent(rows):

    rows = rows[:30]

    freq = special_frequency(rows)

    scores = normalize_scores(freq)

    return {

        n:
            scores.get(n, 0.0)

        for n in range(1, 50)

    }


# =========================================================
# 策略2：中期频率
# =========================================================

def strategy_medium(rows):

    rows = rows[:100]

    freq = special_frequency(rows)

    scores = normalize_scores(freq)

    return {

        n:
            scores.get(n, 0.0)

        for n in range(1, 50)

    }


# =========================================================
# 策略3：长期频率
# =========================================================

def strategy_long(rows):

    rows = rows[:300]

    freq = special_frequency(rows)

    scores = normalize_scores(freq)

    return {

        n:
            scores.get(n, 0.0)

        for n in range(1, 50)

    }


# =========================================================
# 策略4：遗漏
# =========================================================

def strategy_omission(rows):

    omission = special_omission(
        rows[:300]
    )

    # -----------------------------------------------------
    # 遗漏越大，理论上分数越高
    #
    # 这里只作为统计特征，
    # 不代表真实概率。
    # -----------------------------------------------------

    scores = normalize_scores(
        omission
    )

    return {

        n:
            scores.get(n, 0.0)

        for n in range(1, 50)

    }


# =========================================================
# 策略5：大小
# =========================================================

def strategy_size(rows):

    counter = Counter()

    for row in rows[:100]:

        n = get_special(row)

        if not 1 <= n <= 49:
            continue

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
        counter["big"] /
        total
    )

    small_prob = (
        counter["small"] /
        total
    )

    scores = {}

    for n in range(1, 50):

        if n >= 25:

            scores[n] = big_prob

        else:

            scores[n] = small_prob

    return scores


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

    scores = {}

    for n in range(1, 50):

        if n % 2:

            scores[n] = odd_prob

        else:

            scores[n] = even_prob

    return scores


# =========================================================
# 综合策略
# =========================================================

def combine_strategies(rows):

    # -----------------------------------------------------
    # 防止空数据
    # -----------------------------------------------------

    if not rows:

        empty = {
            n: 0.5
            for n in range(1, 50)
        }

        return empty, {}


    # -----------------------------------------------------
    # 六个策略
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # 固定初始权重
    # -----------------------------------------------------

    weights = {

        "recent":
            0.25,

        "medium":
            0.20,

        "long":
            0.15,

        "omission":
            0.10,

        "size":
            0.15,

        "parity":
            0.15,

    }


    # -----------------------------------------------------
    # 综合分数
    # -----------------------------------------------------

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

                scores.get(
                    n,
                    0.0
                )

                * weight

            )


    # -----------------------------------------------------
    # 最终归一化
    # -----------------------------------------------------

    final_scores = normalize_scores(
        final_scores
    )


    # -----------------------------------------------------
    # 保证 1~49 全部存在
    # -----------------------------------------------------

    for n in range(1, 50):

        final_scores.setdefault(
            n,
            0.0
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
    print("strategies.py 测试")
    print("=" * 70)

    print()

    print(
        "第一期特码：",
        get_special(rows[0])
    )

    print(
        "第二期特码：",
        get_special(rows[1])
    )

    print(
        "第三期特码：",
        get_special(rows[2])
    )

    scores, strategy_scores = combine_strategies(
        rows
    )

    print()

    print("综合分数 Top10：")

    top10 = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    for number, score in top10:

        print(
            f"{number:02d} -> {score:.6f}"
        )
