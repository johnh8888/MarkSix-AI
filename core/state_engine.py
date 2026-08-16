# -*- coding: utf-8 -*-

"""
V3.0 状态识别引擎

用于判断近期：

- 热冷状态
- 大小状态
- 单双状态
- 波色状态
- 趋势状态

注意：
状态只是历史统计特征，不代表未来结果。
"""

from collections import Counter

from typing import Any, Dict, List


# =========================================================
# 安全取数字
# =========================================================

def get_numbers(
    rows: List[Dict[str, Any]]
):

    result = []

    for row in rows:

        numbers = row.get(
            "numbers",
            []
        )

        if not isinstance(
            numbers,
            list
        ):
            continue

        for n in numbers:

            try:

                n = int(n)

                if 1 <= n <= 49:
                    result.append(n)

            except Exception:
                continue

    return result


# =========================================================
# 统计
# =========================================================

def frequency_state(
    rows,
    window=36
):

    subset = rows[:window]

    counter = Counter()

    for row in subset:

        special = row.get(
            "special"
        )

        if special:

            counter[int(special)] += 1

    return counter


# =========================================================
# 大小
# =========================================================

def size_state(
    rows,
    window=36
):

    subset = rows[:window]

    big = 0

    small = 0

    for row in subset:

        n = row.get("special")

        if not n:
            continue

        if int(n) >= 25:
            big += 1
        else:
            small += 1

    total = big + small

    if total == 0:

        return {
            "big": 0.5,
            "small": 0.5,
        }

    return {
        "big": big / total,
        "small": small / total,
    }


# =========================================================
# 单双
# =========================================================

def parity_state(
    rows,
    window=36
):

    subset = rows[:window]

    odd = 0

    even = 0

    for row in subset:

        n = row.get("special")

        if not n:
            continue

        if int(n) % 2:
            odd += 1
        else:
            even += 1

    total = odd + even

    if total == 0:

        return {
            "单": 0.5,
            "双": 0.5,
        }

    return {
        "单": odd / total,
        "双": even / total,
    }


# =========================================================
# 综合状态
# =========================================================

def analyze_state(
    rows,
    window=36
):

    size = size_state(
        rows,
        window
    )

    parity = parity_state(
        rows,
        window
    )

    frequency = frequency_state(
        rows,
        window
    )

    hot = [
        n
        for n, _ in
        frequency.most_common(10)
    ]

    cold = [
        n
        for n in range(1, 50)
        if n not in frequency
    ]

    return {

        "window": window,

        "size": size,

        "parity": parity,

        "hot_numbers": hot,

        "cold_numbers": cold,

        "frequency": dict(frequency),
    }