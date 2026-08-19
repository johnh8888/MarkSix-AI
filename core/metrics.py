# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
V7.1 命中率统计模块

功能：

1. 号码 Top5 / Top10 / Top12
2. 号码实际命中数量
3. 号码至少命中1个概率
4. 生肖主推 / 双推
5. 单双主推 / 双推
6. 大小主推 / 双推
7. 波色主推 / 次推 / 双色
8. Walk-Forward历史命中率
"""

from __future__ import annotations

from collections import Counter
from typing import Any


# ============================================================
# 波色
# ============================================================

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


# ============================================================
# 基础属性
# ============================================================

def get_wave(number: int) -> str:

    number = int(number)

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return ""


def get_size(number: int) -> str:

    number = int(number)

    return "大" if number >= 25 else "小"


def get_odd_even(number: int) -> str:

    number = int(number)

    return "单" if number % 2 else "双"


# ============================================================
# 生肖
# ============================================================

def zodiac_by_year(
    number: int,
    year: int,
) -> str:

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

    # 2024 = 龙
    base_index = 4

    index = (
        base_index
        + (year - 2024)
    ) % 12

    return animals[
        (index - (number - 1)) % 12
    ]


def get_zodiac(
    number: int,
    issue: str,
) -> str:

    try:

        year = int(
            str(issue)[:4]
        )

    except Exception:

        year = 2026

    return zodiac_by_year(
        int(number),
        year,
    )


# ============================================================
# 历史属性统计
# ============================================================

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

            try:
                number = int(number)
            except Exception:
                continue

            if field == "wave":

                value = get_wave(
                    number
                )

            elif field == "size":

                value = get_size(
                    number
                )

            elif field == "odd_even":

                value = get_odd_even(
                    number
                )

            elif field == "zodiac":

                value = get_zodiac(
                    number,
                    issue,
                )

            else:

                value = ""

            if value:

                counter[value] += 1

    return counter


# ============================================================
# 属性预测
# ============================================================

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
            "ranking": [],
        }

    values = [
        item[0]
        for item in counter.most_common()
    ]

    main = values[0]

    secondary = (
        values[1]
        if len(values) > 1
        else ""
    )

    double = [
        x
        for x in (
            main,
            secondary,
        )
        if x
    ]

    return {

        "main": main,

        "secondary": secondary,

        "double": double,

        "ranking": [
            {
                "value": value,
                "count": count,
            }
            for value, count
            in counter.most_common()
        ],
    }


# ============================================================
# 百分比
# ============================================================

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


# ============================================================
# 命中率统计
# ============================================================

def calculate_performance(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(
        evaluations
    )

    if total == 0:

        return {

            "samples": 0,

            "status":
                "历史数据不足",

        }

    def count(
        key: str,
    ) -> int:

        return sum(

            1

            for item in evaluations

            if item.get(key)

        )

    # --------------------------------------------------------
    # 号码平均命中数量
    # --------------------------------------------------------

    def average_hits(
        key: str,
    ) -> float:

        values = [

            item.get(
                key,
                0,
            )

            for item in evaluations

        ]

        if not values:

            return 0.0

        return round(
            sum(values) / len(values),
            2,
        )

    return {

        "samples":
            total,

        # ====================================================
        # 号码
        # ====================================================

        "numbers": {

            "top5":
                hit_rate(
                    count(
                        "number_top5"
                    ),
                    total,
                ),

            "top10":
                hit_rate(
                    count(
                        "number_top10"
                    ),
                    total,
                ),

            "top12":
                hit_rate(
                    count(
                        "number_top12"
                    ),
                    total,
                ),

            "top5_average_hits":
                average_hits(
                    "number_top5_hits"
                ),

            "top10_average_hits":
                average_hits(
                    "number_top10_hits"
                ),

            "top12_average_hits":
                average_hits(
                    "number_top12_hits"
                ),

        },

        # ====================================================
        # 生肖
        # ====================================================

        "zodiac": {

            "main":
                hit_rate(
                    count(
                        "zodiac_main"
                    ),
                    total,
                ),

            "double":
                hit_rate(
                    count(
                        "zodiac_double"
                    ),
                    total,
                ),

        },

        # ====================================================
        # 单双
        # ====================================================

        "odd_even": {

            "main":
                hit_rate(
                    count(
                        "odd_even_main"
                    ),
                    total,
                ),

            "double":
                hit_rate(
                    count(
                        "odd_even_double"
                    ),
                    total,
                ),

        },

        # ====================================================
        # 大小
        # ====================================================

        "size": {

            "main":
                hit_rate(
                    count(
                        "size_main"
                    ),
                    total,
                ),

            "double":
                hit_rate(
                    count(
                        "size_double"
                    ),
                    total,
                ),

        },

        # ====================================================
        # 波色
        # ====================================================

        "wave": {

            "main":
                hit_rate(
                    count(
                        "wave_main"
                    ),
                    total,
                ),

            "secondary":
                hit_rate(
                    count(
                        "wave_secondary"
                    ),
                    total,
                ),

            "double":
                hit_rate(
                    count(
                        "wave_double"
                    ),
                    total,
                ),

        },

        "status":
            "正常",
    }
