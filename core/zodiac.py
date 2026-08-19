# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

生肖映射模块

以 2026 年为基准：
2026 = 马年

生肖每年向前循环。
"""

from __future__ import annotations


# =====================================================
# 2026 马年
# =====================================================

ZODIAC_2026 = [
    "马",
    "蛇",
    "龙",
    "兔",
    "虎",
    "牛",
    "鼠",
    "猪",
    "狗",
    "鸡",
    "猴",
    "羊"
]


def get_zodiac(
    number,
    year=2026
):
    """
    根据号码和年份返回生肖。

    这里采用：

    1号 = 当年生肖

    然后顺时针循环。

    例如：
    2026年：
    1 = 马
    2 = 蛇
    3 = 龙
    ...
    """

    try:

        number = int(number)
        year = int(year)

    except Exception:

        return "未知"

    if not 1 <= number <= 49:

        return "未知"

    # 2026是马年
    zodiac_index = (
        number - 1
    ) % 12

    # 年份相对于2026的偏移
    year_offset = (
        2026 - year
    ) % 12

    index = (
        zodiac_index
        +
        year_offset
    ) % 12

    return ZODIAC_2026[index]


def zodiac_numbers(
    year=2026
):
    """
    返回生肖对应号码。
    """

    result = {
        zodiac: []
        for zodiac
        in ZODIAC_2026
    }

    for number in range(
        1,
        50
    ):

        zodiac = get_zodiac(
            number,
            year
        )

        result.setdefault(
            zodiac,
            []
        ).append(
            number
        )

    return result


def zodiac_rank(
    numbers,
    year=2026
):
    """
    对号码对应生肖进行统计。
    """

    from collections import Counter

    counter = Counter()

    for number in numbers:

        zodiac = get_zodiac(
            number,
            year
        )

        if zodiac != "未知":

            counter[zodiac] += 1

    return [
        zodiac
        for zodiac, count
        in counter.most_common()
    ]


__all__ = [
    "ZODIAC_2026",
    "get_zodiac",
    "zodiac_numbers",
    "zodiac_rank"
]
