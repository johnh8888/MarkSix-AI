# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import Counter
from typing import Any


RED = {
    1, 2, 7, 8, 12, 13,
    18, 19, 23, 24, 29, 30,
    34, 35, 40, 45, 46
}

BLUE = {
    3, 4, 9, 10, 14, 15,
    20, 25, 26, 31, 36, 37,
    41, 42, 47, 48
}

GREEN = {
    5, 6, 11, 16, 17, 21,
    22, 27, 28, 32, 33, 38,
    39, 43, 44, 49
}


ZODIAC = [
    "鼠",
    "牛",
    "虎",
    "兔",
    "龙",
    "蛇",
    "马",
    "羊",
    "猴",
    "鸡",
    "狗",
    "猪",
]


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


def get_tail(
    number: int,
) -> int:

    return number % 10


def zodiac_for_number(
    number: int,
    year: int,
) -> str:

    # 2026 = 马年
    base_year = 2026
    base_index = 6

    offset = (
        (year - base_year) % 12
    )

    year_index = (
        base_index + offset
    ) % 12

    # 49号生肖映射：
    # 根据当前年生肖倒推号码生肖
    #
    # 这里采用：
    # 1号对应当前年生肖，依次循环
    #
    # 实际系统可继续替换为你的
    # 固定六合彩生肖表。

    index = (
        year_index
        - (number - 1)
    ) % 12

    return ZODIAC[index]


def analyze_attributes(
    numbers: list[int],
) -> dict[str, Any]:

    colors = Counter()
    sizes = Counter()
    odd_even = Counter()
    tails = Counter()
    zones = Counter()

    for number in numbers:

        colors[
            get_color(number)
        ] += 1

        sizes[
            get_size(number)
        ] += 1

        odd_even[
            get_odd_even(number)
        ] += 1

        tails[
            str(get_tail(number))
        ] += 1

        zones[
            str(get_zone(number))
        ] += 1

    return {
        "colors": dict(colors),
        "sizes": dict(sizes),
        "odd_even": dict(odd_even),
        "tails": dict(tails),
        "zones": dict(zones),
    }


def number_frequency(
    history: list[dict[str, Any]],
) -> Counter:

    counter = Counter()

    for record in history:

        for number in record[
            "numbers"
        ]:

            counter[number] += 1

    return counter


def recent_frequency(
    history: list[dict[str, Any]],
    window: int = 30,
) -> Counter:

    counter = Counter()

    recent = history[-window:]

    for record in recent:

        for number in record[
            "numbers"
        ]:

            counter[number] += 1

    return counter


def overdue_score(
    history: list[dict[str, Any]],
) -> dict[int, int]:

    seen = {}

    for number in range(1, 50):

        seen[number] = len(history)

    for index in range(
        len(history) - 1,
        -1,
        -1,
    ):

        numbers = history[
            index
        ]["numbers"]

        distance = (
            len(history)
            - 1
            - index
        )

        for number in numbers:

            if (
                seen[number]
                == len(history)
            ):

                seen[number] = distance

    return seen


def rank_numbers(
    history: list[dict[str, Any]],
) -> list[int]:

    if not history:

        return list(
            range(1, 50)
        )

    freq = number_frequency(
        history
    )

    recent = recent_frequency(
        history
    )

    overdue = overdue_score(
        history
    )

    scores = {}

    for number in range(
        1,
        50,
    ):

        score = 0.0

        score += (
            freq.get(number, 0)
            * 1.0
        )

        score += (
            recent.get(number, 0)
            * 2.0
        )

        # 轻微考虑遗漏
        score += min(
            overdue.get(number, 0),
            20,
        ) * 0.15

        scores[number] = score

    ranked = sorted(
        scores,
        key=lambda x: (
            -scores[x],
            x,
        ),
    )

    return ranked


def predict_numbers(
    history: list[dict[str, Any]],
) -> dict[str, list[int]]:

    ranked = rank_numbers(
        history
    )

    return {
        "top5": ranked[:5],
        "top7": ranked[:7],
        "top12": ranked[:12],
    }


def predict_size(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = Counter()

    for record in history:

        numbers = record[
            "numbers"
        ]

        # 特码
        value = numbers[-1]

        counter[
            get_size(value)
        ] += 1

    if not counter:

        return {
            "primary": "大",
            "secondary": "小",
        }

    ranked = [
        x
        for x, _ in counter.most_common()
    ]

    primary = ranked[0]

    secondary = (
        "小"
        if primary == "大"
        else "大"
    )

    return {
        "primary": primary,
        "secondary": secondary,
    }


def predict_odd_even(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = Counter()

    for record in history:

        value = record[
            "numbers"
        ][-1]

        counter[
            get_odd_even(value)
        ] += 1

    if not counter:

        return {
            "primary": "单",
            "secondary": "双",
        }

    primary = counter.most_common(
        1
    )[0][0]

    secondary = (
        "双"
        if primary == "单"
        else "单"
    )

    return {
        "primary": primary,
        "secondary": secondary,
    }


def predict_color(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = Counter()

    for record in history:

        value = record[
            "numbers"
        ][-1]

        counter[
            get_color(value)
        ] += 1

    ranked = [
        x
        for x, _ in counter.most_common()
    ]

    all_colors = [
        "红",
        "蓝",
        "绿",
    ]

    for color in all_colors:

        if color not in ranked:
            ranked.append(color)

    return {
        "primary": ranked[0],
        "secondary": ranked[1],
        "double": ranked[:2],
        "ranking": ranked,
    }


def predict_zodiac(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = Counter()

    for record in history:

        issue = record[
            "issue"
        ]

        try:

            year = int(issue[:4])

        except Exception:

            year = 2026

        value = record[
            "numbers"
        ][-1]

        zodiac = zodiac_for_number(
            value,
            year,
        )

        counter[zodiac] += 1

    ranked = [
        x
        for x, _ in counter.most_common()
    ]

    for zodiac in ZODIAC:

        if zodiac not in ranked:
            ranked.append(zodiac)

    return {
        "primary": ranked[0],
        "secondary": ranked[1],
        "ranking": ranked,
    }


def build_prediction(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    number_prediction = (
        predict_numbers(history)
    )

    color = predict_color(
        history
    )

    size = predict_size(
        history
    )

    odd_even = predict_odd_even(
        history
    )

    zodiac = predict_zodiac(
        history
    )

    return {
        "number_prediction":
            number_prediction,

        "attributes_prediction": {
            "color": color,
            "size": size,
            "odd_even": odd_even,
            "zodiac": zodiac,
        },
    }
