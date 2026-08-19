# -*- coding: utf-8 -*-

"""
统计分析模块
V6.0

不负责所谓“预测中奖概率”。
只进行历史统计评分。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


RED = {
    1, 2, 7, 8, 12, 13, 18, 19,
    23, 24, 29, 30, 34, 35, 40,
    45, 46,
}

BLUE = {
    3, 4, 9, 10, 14, 15, 20,
    25, 26, 31, 36, 37, 41, 42,
    47, 48,
}

GREEN = {
    5, 6, 11, 16, 17, 21, 22,
    27, 28, 32, 33, 38, 39, 43,
    44, 49,
}


def get_color(
    number: int,
) -> str:

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return "未知"


def get_size(
    number: int,
) -> str:

    return (
        "大"
        if number >= 25
        else "小"
    )


def get_odd_even(
    number: int,
) -> str:

    return (
        "单"
        if number % 2
        else "双"
    )


def get_tail(
    number: int,
) -> int:

    return number % 10


def get_zone(
    number: int,
) -> int:

    if number <= 10:
        return 1

    if number <= 20:
        return 2

    if number <= 30:
        return 3

    if number <= 40:
        return 4

    return 5


def attribute_statistics(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    colors = Counter()
    sizes = Counter()
    odd_even = Counter()
    tails = Counter()
    zones = Counter()

    for draw in history:

        numbers = draw[
            "numbers"
        ]

        if not numbers:
            continue

        special = numbers[-1]

        colors[
            get_color(special)
        ] += 1

        sizes[
            get_size(special)
        ] += 1

        odd_even[
            get_odd_even(special)
        ] += 1

        tails[
            str(get_tail(special))
        ] += 1

        zones[
            str(get_zone(special))
        ] += 1

    return {
        "sample_size": len(history),
        "colors": dict(colors),
        "sizes": dict(sizes),
        "odd_even": dict(odd_even),
        "tails": dict(tails),
        "zones": dict(zones),
    }


def number_frequency(
    history: List[Dict[str, Any]],
) -> Counter:

    counter = Counter()

    for draw in history:

        for number in draw[
            "numbers"
        ]:

            if (
                isinstance(
                    number,
                    int,
                )
                and 1 <= number <= 49
            ):
                counter[number] += 1

    return counter


def weighted_frequency(
    history: List[Dict[str, Any]],
) -> Dict[int, float]:

    """
    越新的期数权重越高。
    """

    scores = {
        number: 0.0
        for number in range(
            1,
            50,
        )
    }

    total = len(history)

    if total == 0:
        return scores

    for index, draw in enumerate(
        history
    ):

        age = (
            total
            - index
        )

        weight = (
            0.5
            + age / total
        )

        for number in draw[
            "numbers"
        ]:

            if 1 <= number <= 49:
                scores[number] += weight

    return scores


def overdue_scores(
    history: List[Dict[str, Any]],
) -> Dict[int, int]:

    result = {}

    reversed_history = list(
        reversed(history)
    )

    for number in range(
        1,
        50,
    ):

        overdue = len(
            history
        )

        for index, draw in enumerate(
            reversed_history
        ):

            if number in draw[
                "numbers"
            ]:
                overdue = index
                break

        result[number] = overdue

    return result


def analyze_numbers(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    frequency = number_frequency(
        history
    )

    weighted = weighted_frequency(
        history
    )

    overdue = overdue_scores(
        history
    )

    total = len(history)

    # ------------------------------------------
    # 高频
    # ------------------------------------------

    if total > 0:

        hot = sorted(
            range(1, 50),
            key=lambda n: (
                -frequency[n],
                -weighted[n],
                n,
            ),
        )

        hot_numbers = hot[:10]

    else:

        hot_numbers = []

    # ------------------------------------------
    # 低频
    # ------------------------------------------

    if total > 0:

        cold = sorted(
            range(1, 50),
            key=lambda n: (
                frequency[n],
                -overdue[n],
                n,
            ),
        )

        cold_numbers = cold[:10]

    else:

        cold_numbers = []

    # ------------------------------------------
    # 综合评分
    # ------------------------------------------

    combined_scores = {}

    max_frequency = max(
        frequency.values(),
        default=1,
    )

    max_weighted = max(
        weighted.values(),
        default=1.0,
    )

    max_overdue = max(
        overdue.values(),
        default=1,
    )

    for number in range(
        1,
        50,
    ):

        freq_score = (
            frequency[number]
            / max_frequency
            if max_frequency
            else 0
        )

        recent_score = (
            weighted[number]
            / max_weighted
            if max_weighted
            else 0
        )

        overdue_score = (
            overdue[number]
            / max_overdue
            if max_overdue
            else 0
        )

        score = (
            freq_score * 0.45
            + recent_score * 0.35
            + overdue_score * 0.20
        )

        combined_scores[
            number
        ] = score

    candidates = sorted(
        range(1, 50),
        key=lambda n: (
            -combined_scores[n],
            n,
        ),
    )

    # 有历史才输出候选。
    # 不再人工填充。
    candidates = candidates[:12]

    return {
        "frequency": dict(
            frequency
        ),
        "weighted_frequency": {
            str(k): round(
                v,
                4,
            )
            for k, v in weighted.items()
        },
        "overdue": overdue,
        "hot_numbers": hot_numbers,
        "cold_numbers": cold_numbers,
        "candidates": candidates,
        "scores": {
            str(k): round(
                v,
                6,
            )
            for k, v in combined_scores.items()
        },
    }


def analyze_history(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    attributes = attribute_statistics(
        history
    )

    numbers = analyze_numbers(
        history
    )

    return {
        "history_size": len(
            history
        ),
        "attributes": attributes,
        **numbers,
    }
