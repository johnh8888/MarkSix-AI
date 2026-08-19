# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V7.2

命中率统计模块

功能：

1. 号码 Top5 / Top10 / Top12
2. 号码平均命中数
3. 至少命中1/2/3个
4. 最大命中数
5. 生肖主推/次推/双推
6. 单双主推/次推/双推
7. 大小主推/次推/双推
8. 波色主推/次推/双色
9. 全历史命中率
10. 最近50期命中率
11. 最近20期命中率
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

    return "大" if int(number) >= 25 else "小"


def get_odd_even(number: int) -> str:

    return "单" if int(number) % 2 else "双"


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
        (index - (int(number) - 1)) % 12
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
        number,
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

    if not history:
        return counter

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
        50,
    )

    if not counter:

        return {
            "main": "",
            "secondary": "",
            "double": [],
            "ranking": [],
            "scores": {},
        }

    ranking = [
        item[0]
        for item in counter.most_common()
    ]

    main = ranking[0]

    secondary = (
        ranking[1]
        if len(ranking) > 1
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
        "ranking": ranking,
        "scores": dict(counter),
    }


# ============================================================
# 命中率
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
# 计算号码命中
# ============================================================

def calculate_number_stats(
    evaluations: list[dict[str, Any]],
    key: str,
) -> dict[str, Any]:

    total = len(evaluations)

    if total <= 0:

        return {
            "hit_rate": 0.0,
            "at_least_1": 0.0,
            "at_least_2": 0.0,
            "at_least_3": 0.0,
            "average_hits": 0.0,
            "max_hits": 0,
        }

    hit_counts = []

    for item in evaluations:

        value = item.get(
            key,
            0,
        )

        try:
            value = int(value)
        except Exception:
            value = 0

        hit_counts.append(
            value
        )

    return {
        "hit_rate": hit_rate(
            sum(
                1
                for x in hit_counts
                if x > 0
            ),
            total,
        ),

        "at_least_1": hit_rate(
            sum(
                1
                for x in hit_counts
                if x >= 1
            ),
            total,
        ),

        "at_least_2": hit_rate(
            sum(
                1
                for x in hit_counts
                if x >= 2
            ),
            total,
        ),

        "at_least_3": hit_rate(
            sum(
                1
                for x in hit_counts
                if x >= 3
            ),
            total,
        ),

        "average_hits": round(
            sum(hit_counts)
            / total,
            2,
        ),

        "max_hits": max(
            hit_counts
        ),
    }


# ============================================================
# 属性命中
# ============================================================

def calculate_attribute_stats(
    evaluations: list[dict[str, Any]],
    main_key: str,
    secondary_key: str,
    double_key: str,
) -> dict[str, float]:

    total = len(evaluations)

    if total <= 0:

        return {
            "main": 0.0,
            "secondary": 0.0,
            "double": 0.0,
        }

    return {

        "main": hit_rate(
            sum(
                1
                for item in evaluations
                if item.get(main_key)
            ),
            total,
        ),

        "secondary": hit_rate(
            sum(
                1
                for item in evaluations
                if item.get(
                    secondary_key
                )
            ),
            total,
        ),

        "double": hit_rate(
            sum(
                1
                for item in evaluations
                if item.get(
                    double_key
                )
            ),
            total,
        ),
    }


# ============================================================
# 主函数
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
            "status": "历史数据不足",
        }

    # --------------------------------------------------------
    # 号码
    # --------------------------------------------------------

    number_stats = {

        "top5":
            calculate_number_stats(
                evaluations,
                "top5_hits",
            ),

        "top10":
            calculate_number_stats(
                evaluations,
                "top10_hits",
            ),

        "top12":
            calculate_number_stats(
                evaluations,
                "top12_hits",
            ),
    }

    # --------------------------------------------------------
    # 属性
    # --------------------------------------------------------

    zodiac = calculate_attribute_stats(
        evaluations,
        "zodiac_main",
        "zodiac_secondary",
        "zodiac_double",
    )

    odd_even = calculate_attribute_stats(
        evaluations,
        "odd_even_main",
        "odd_even_secondary",
        "odd_even_double",
    )

    size = calculate_attribute_stats(
        evaluations,
        "size_main",
        "size_secondary",
        "size_double",
    )

    wave = calculate_attribute_stats(
        evaluations,
        "wave_main",
        "wave_secondary",
        "wave_double",
    )

    return {

        "samples":
            total,

        "numbers":
            number_stats,

        "zodiac":
            zodiac,

        "odd_even":
            odd_even,

        "size":
            size,

        "wave":
            wave,

        "status":
            "正常",
    }
