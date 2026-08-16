# -*- coding: utf-8 -*-

from collections import Counter


# =========================================================
# 基础工具
# =========================================================

def get_special(row):

    """
    兼容：

    {
        "special": 27
    }

    或：

    {
        "numbers": "33,27,16,28,04,25,14"
    }
    """

    try:

        if isinstance(row, dict):

            if "special" in row:

                return int(
                    row["special"]
                )

            if "special_number" in row:

                return int(
                    row["special_number"]
                )

            numbers = row.get(
                "numbers"
            )

            if numbers:

                if isinstance(
                    numbers,
                    str
                ):

                    values = [
                        int(x.strip())
                        for x in numbers.split(",")
                        if x.strip()
                    ]

                    if values:

                        return values[1] if len(values) >= 7 else values[0]

                if isinstance(
                    numbers,
                    list
                ):

                    values = [
                        int(x)
                        for x in numbers
                    ]

                    if values:

                        return values[1] if len(values) >= 7 else values[0]

    except Exception:

        pass

    return 0


# =========================================================
# 归一化
# =========================================================

def normalize_scores(scores):

    if not scores:

        return {
            n: 0.5
            for n in range(1, 50)
        }

    values = list(
        scores.values()
    )

    low = min(values)
    high = max(values)

    if high == low:

        return {
            n: 0.5
            for n in scores
        }

    return {

        n:
            (value - low)
            /
            (high - low)

        for n, value
        in scores.items()
    }


# =========================================================
# 平滑频率
# =========================================================

def smoothed_frequency(rows):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[n] += 1

    total = sum(
        counter.values()
    )

    result = {}

    for n in range(1, 50):

        result[n] = (
            counter[n] + 1
        ) / (
            total + 49
        )

    return result


# =========================================================
# 最近频率
# =========================================================

def strategy_recent(rows):

    data = rows[:20]

    freq = smoothed_frequency(
        data
    )

    return normalize_scores(
        freq
    )


# =========================================================
# 近期增强
# =========================================================

def strategy_recent10(rows):

    data = rows[:10]

    freq = smoothed_frequency(
        data
    )

    return normalize_scores(
        freq
    )


# =========================================================
# 中短期
# =========================================================

def strategy_medium(rows):

    data = rows[:50]

    freq = smoothed_frequency(
        data
    )

    return normalize_scores(
        freq
    )


# =========================================================
# 长期基础
# =========================================================

def strategy_long(rows):

    data = rows[:200]

    freq = smoothed_frequency(
        data
    )

    return normalize_scores(
        freq
    )


# =========================================================
# 遗漏策略
# =========================================================

def strategy_omission(rows):

    omission = {}

    seen = set()

    for index, row in enumerate(rows[:200]):

        n = get_special(row)

        if not 1 <= n <= 49:
            continue

        if n not in seen:

            omission[n] = (
                index + 1
            )

            seen.add(n)

    for n in range(1, 50):

        omission.setdefault(
            n,
            201
        )

    return normalize_scores(
        omission
    )


# =========================================================
# 遗漏压缩
# =========================================================

def strategy_omission_decay(rows):

    """
    避免极端遗漏号码获得过高分。

    使用 sqrt 压缩。
    """

    import math

    omission = {}

    seen = set()

    for index, row in enumerate(rows[:100]):

        n = get_special(row)

        if not 1 <= n <= 49:
            continue

        if n not in seen:

            omission[n] = (
                index + 1
            )

            seen.add(n)

    result = {}

    for n in range(1, 50):

        value = omission.get(
            n,
            101
        )

        result[n] = math.sqrt(
            value
        )

    return normalize_scores(
        result
    )


# =========================================================
# 大小
# =========================================================

def strategy_size(rows):

    recent = rows[:20]

    big = 0
    small = 0

    for row in recent:

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

    big_prob = (
        big + 1
    ) / (
        total + 2
    )

    small_prob = (
        small + 1
    ) / (
        total + 2
    )

    result = {}

    for n in range(1, 50):

        if n >= 25:

            result[n] = big_prob

        else:

            result[n] = small_prob

    return result


# =========================================================
# 单双
# =========================================================

def strategy_parity(rows):

    recent = rows[:20]

    odd = 0
    even = 0

    for row in recent:

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

    odd_prob = (
        odd + 1
    ) / (
        total + 2
    )

    even_prob = (
        even + 1
    ) / (
        total + 2
    )

    result = {}

    for n in range(1, 50):

        if n % 2:

            result[n] = odd_prob

        else:

            result[n] = even_prob

    return result


# =========================================================
# 尾数
# =========================================================

def strategy_tail(rows):

    counter = Counter()

    for row in rows[:50]:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[n % 10] += 1

    result = {}

    for n in range(1, 50):

        result[n] = (
            counter[n % 10] + 1
        )

    return normalize_scores(
        result
    )


# =========================================================
# 分区
# =========================================================

def get_zone(n):

    if n <= 10:
        return 1

    if n <= 20:
        return 2

    if n <= 30:
        return 3

    if n <= 40:
        return 4

    return 5


def strategy_zone(rows):

    counter = Counter()

    for row in rows[:50]:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[
                get_zone(n)
            ] += 1

    result = {}

    for n in range(1, 50):

        result[n] = (
            counter[
                get_zone(n)
            ] + 1
        )

    return normalize_scores(
        result
    )


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

        "recent10":
            strategy_recent10(rows),

        "recent20":
            strategy_recent(rows),

        "medium":
            strategy_medium(rows),

        "long":
            strategy_long(rows),

        "omission":
            strategy_omission(rows),

        "omission_decay":
            strategy_omission_decay(rows),

        "size":
            strategy_size(rows),

        "parity":
            strategy_parity(rows),

        "tail":
            strategy_tail(rows),

        "zone":
            strategy_zone(rows),
    }

    # -----------------------------------------------------
    # 权重
    # -----------------------------------------------------

    weights = {

        "recent10":
            0.18,

        "recent20":
            0.18,

        "medium":
            0.12,

        "long":
            0.06,

        "omission":
            0.08,

        "omission_decay":
            0.06,

        "size":
            0.10,

        "parity":
            0.08,

        "tail":
            0.07,

        "zone":
            0.07,
    }

    final_scores = {
        n: 0.0
        for n in range(1, 50)
    }

    for name, scores in strategies.items():

        weight = weights.get(
            name,
            0.0
        )

        for n in range(1, 50):

            final_scores[n] += (
                scores.get(
                    n,
                    0.5
                )
                *
                weight
            )

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
    print("strategies.py V1.4")
    print("=" * 70)

    scores, strategy_scores = combine_strategies(
        rows
    )

    top10 = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    print()

    for index, (n, score) in enumerate(
        top10,
        1
    ):

        print(
            f"{index:02d}. "
            f"{n:02d} -> "
            f"{score:.6f}"
        )
