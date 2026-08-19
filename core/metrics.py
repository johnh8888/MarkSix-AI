# -*- coding: utf-8 -*-

"""
V7.0 命中率统计模块

功能：
1. 号码 Top5 / Top10 / Top12 命中
2. 生肖主推 / 双推命中
3. 单双主推 / 双推命中
4. 大小主推 / 双推命中
5. 波色主推 / 次推 / 双色命中
6. Walk-Forward 汇总
"""

from __future__ import annotations

from collections import Counter
from typing import Any


RED = {
    1, 2, 7, 8, 12, 13, 18, 19, 23, 24,
    29, 30, 34, 35, 40, 45, 46
}

BLUE = {
    3, 4, 9, 10, 14, 15, 20, 25, 26, 31,
    36, 37, 41, 42, 47, 48
}

GREEN = {
    5, 6, 11, 16, 17, 21, 22, 27, 28, 32,
    33, 38, 39, 43, 44, 49
}


def get_wave(number: int) -> str:
    if number in RED:
        return "红"
    if number in BLUE:
        return "蓝"
    if number in GREEN:
        return "绿"
    return ""


def get_size(number: int) -> str:
    return "大" if number >= 25 else "小"


def get_odd_even(number: int) -> str:
    return "单" if number % 2 else "双"


def zodiac_by_year(number: int, year: int) -> str:
    """
    根据农历年份生肖映射。

    2024 = 龙
    2025 = 蛇
    2026 = 马
    """

    animals = [
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

    # 2024 年为龙
    base_index = 4

    index = (
        base_index
        + (year - 2024)
    ) % 12

    # 1号对应生肖起点按照号码轮转
    return animals[
        (index - (number - 1)) % 12
    ]


def get_zodiac(number: int, issue: str) -> str:
    try:
        year = int(str(issue)[:4])
    except Exception:
        year = 2026

    return zodiac_by_year(
        number,
        year,
    )


def latest_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 20,
) -> Counter:

    counter = Counter()

    for row in history[-limit:]:

        numbers = row.get(
            "numbers",
            [],
        )

        issue = row.get(
            "issue",
            "",
        )

        for number in numbers:

            if field == "wave":
                value = get_wave(number)

            elif field == "size":
                value = get_size(number)

            elif field == "odd_even":
                value = get_odd_even(number)

            elif field == "zodiac":
                value = get_zodiac(
                    number,
                    issue,
                )

            else:
                continue

            if value:
                counter[value] += 1

    return counter


def predict_attribute(
    history: list[dict[str, Any]],
    field: str,
) -> dict[str, Any]:

    counter = latest_attribute(
        history,
        field,
    )

    if not counter:
        return {
            "main": "",
            "secondary": "",
            "double": [],
        }

    values = [
        x[0]
        for x in counter.most_common()
    ]

    main = values[0]

    secondary = (
        values[1]
        if len(values) > 1
        else ""
    )

    return {
        "main": main,
        "secondary": secondary,
        "double": [
            x
            for x in (
                main,
                secondary,
            )
            if x
        ],
    }


def hit_rate(
    hits: int,
    total: int,
) -> float:

    if total <= 0:
        return 0.0

    return round(
        hits / total * 100,
        2,
    )


def calculate_performance(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(evaluations)

    if total == 0:
        return {
            "samples": 0,
            "status": "历史数据不足",
        }

    def count(
        key: str,
    ) -> int:

        return sum(
            1
            for item in evaluations
            if item.get(key)
        )

    return {
        "samples": total,

        "numbers": {
            "top5": hit_rate(
                count("number_top5"),
                total,
            ),
            "top10": hit_rate(
                count("number_top10"),
                total,
            ),
            "top12": hit_rate(
                count("number_top12"),
                total,
            ),
        },

        "zodiac": {
            "main": hit_rate(
                count("zodiac_main"),
                total,
            ),
            "double": hit_rate(
                count("zodiac_double"),
                total,
            ),
        },

        "odd_even": {
            "main": hit_rate(
                count("odd_even_main"),
                total,
            ),
            "double": hit_rate(
                count("odd_even_double"),
                total,
            ),
        },

        "size": {
            "main": hit_rate(
                count("size_main"),
                total,
            ),
            "double": hit_rate(
                count("size_double"),
                total,
            ),
        },

        "wave": {
            "main": hit_rate(
                count("wave_main"),
                total,
            ),
            "secondary": hit_rate(
                count("wave_secondary"),
                total,
            ),
            "double": hit_rate(
                count("wave_double"),
                total,
            ),
        },

        "status": "正常",
    }
