# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
V7.1 命中率统计模块

功能：

1. 号码 Top5 / Top10 / Top12 命中率
2. 生肖主推 / 双推命中率
3. 单双主推 / 次推 / 双推命中率
4. 大小主推 / 次推 / 双推命中率
5. 波色主推 / 次推 / 双色命中率
6. 特别号属性判断
7. Walk-Forward 历史验证
8. 当前预测结果统计
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

    try:
        number = int(number)
    except Exception:
        return ""

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return ""


def get_size(number: int) -> str:

    try:
        number = int(number)
    except Exception:
        return ""

    return "大" if number >= 25 else "小"


def get_odd_even(number: int) -> str:

    try:
        number = int(number)
    except Exception:
        return ""

    return "单" if number % 2 else "双"


# ============================================================
# 生肖
# ============================================================

ANIMALS = [
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


def zodiac_by_year(
    number: int,
    year: int,
) -> str:
    """
    根据开奖年份计算号码对应生肖。

    2024 = 龙
    2025 = 蛇
    2026 = 马

    号码按照 1~49 循环对应生肖。
    """

    try:
        number = int(number)
        year = int(year)
    except Exception:
        return ""

    if not 1 <= number <= 49:
        return ""

    # 2024 = 龙
    base_index = 4

    year_index = (
        base_index
        + (year - 2024)
    ) % 12

    animal_index = (
        year_index
        - (number - 1)
    ) % 12

    return ANIMALS[
        animal_index
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
# 获取特别号
# ============================================================

def get_special_number(
    row: dict[str, Any],
) -> int | None:

    numbers = row.get(
        "numbers",
        [],
    )

    if not numbers:
        return None

    try:

        number = int(
            numbers[-1]
        )

    except Exception:

        return None

    if not 1 <= number <= 49:
        return None

    return number


# ============================================================
# 获取特别号属性
# ============================================================

def get_special_attributes(
    row: dict[str, Any],
) -> dict[str, str]:

    number = get_special_number(
        row
    )

    if number is None:
        return {
            "number": "",
            "wave": "",
            "size": "",
            "odd_even": "",
            "zodiac": "",
        }

    issue = str(
        row.get(
            "issue",
            "",
        )
    )

    return {
        "number": str(number),

        "wave":
            get_wave(number),

        "size":
            get_size(number),

        "odd_even":
            get_odd_even(number),

        "zodiac":
            get_zodiac(
                number,
                issue,
            ),
    }


# ============================================================
# 历史属性统计
#
# 注意：
# 这里使用特别号进行属性统计。
# 这样预测和回测口径一致。
# ============================================================

def latest_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 20,
) -> Counter:

    counter = Counter()

    if not history:
        return counter

    rows = history[-limit:]

    for row in rows:

        attrs = get_special_attributes(
            row
        )

        value = attrs.get(
            field,
            "",
        )

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
        limit=20,
    )

    if not counter:

        return {
            "main": "",
            "secondary": "",
            "double": [],
            "ranking": [],
            "counts": {},
        }

    ranking = [
        item[0]
        for item in counter.most_common()
    ]

    main = (
        ranking[0]
        if len(ranking) >= 1
        else ""
    )

    secondary = (
        ranking[1]
        if len(ranking) >= 2
        else ""
    )

    double = []

    if main:
        double.append(main)

    if secondary:
        double.append(secondary)

    return {
        "main": main,

        "secondary":
            secondary,

        "double":
            double,

        "ranking":
            ranking,

        "counts":
            dict(counter),
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
# 号码命中判断
# ============================================================

def number_hits(
    prediction_numbers: list[int],
    actual_numbers: list[int],
) -> int:

    predicted = set()

    actual = set()

    for number in prediction_numbers:

        try:
            number = int(number)
        except Exception:
            continue

        if 1 <= number <= 49:
            predicted.add(number)

    for number in actual_numbers:

        try:
            number = int(number)
        except Exception:
            continue

        if 1 <= number <= 49:
            actual.add(number)

    return len(
        predicted & actual
    )


# ============================================================
# 单期开奖评价
# ============================================================

def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
    history_before: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    actual_numbers = actual.get(
        "numbers",
        [],
    )

    if not actual_numbers:
        return {}

    # --------------------------------------------------------
    # 号码
    # --------------------------------------------------------

    top5_hits = number_hits(
        prediction.get(
            "top5",
            [],
        ),
        actual_numbers,
    )

    top10_hits = number_hits(
        prediction.get(
            "top10",
            [],
        ),
        actual_numbers,
    )

    top12_hits = number_hits(
        prediction.get(
            "top12",
            [],
        ),
        actual_numbers,
    )

    # --------------------------------------------------------
    # 特别号
    # --------------------------------------------------------

    actual_special = (
        get_special_number(
            actual
        )
    )

    if actual_special is None:
        return {}

    actual_attrs = (
        get_special_attributes(
            actual
        )
    )

    predicted_attrs = prediction.get(
        "attributes",
        {},
    )

    # ========================================================
    # 生肖
    # ========================================================

    zodiac_prediction = (
        predicted_attrs.get(
            "zodiac",
            {},
        )
    )

    zodiac_main = (
        actual_attrs["zodiac"]
        ==
        zodiac_prediction.get(
            "main",
            "",
        )
    )

    zodiac_secondary = (
        actual_attrs["zodiac"]
        ==
        zodiac_prediction.get(
            "secondary",
            "",
        )
    )

    zodiac_double = (
        actual_attrs["zodiac"]
        in zodiac_prediction.get(
            "double",
            [],
        )
    )

    # ========================================================
    # 单双
    # ========================================================

    odd_prediction = (
        predicted_attrs.get(
            "odd_even",
            {},
        )
    )

    odd_main = (
        actual_attrs["odd_even"]
        ==
        odd_prediction.get(
            "main",
            "",
        )
    )

    odd_secondary = (
        actual_attrs["odd_even"]
        ==
        odd_prediction.get(
            "secondary",
            "",
        )
    )

    odd_double = (
        actual_attrs["odd_even"]
        in odd_prediction.get(
            "double",
            [],
        )
    )

    # ========================================================
    # 大小
    # ========================================================

    size_prediction = (
        predicted_attrs.get(
            "size",
            {},
        )
    )

    size_main = (
        actual_attrs["size"]
        ==
        size_prediction.get(
            "main",
            "",
        )
    )

    size_secondary = (
        actual_attrs["size"]
        ==
        size_prediction.get(
            "secondary",
            "",
        )
    )

    size_double = (
        actual_attrs["size"]
        in size_prediction.get(
            "double",
            [],
        )
    )

    # ========================================================
    # 波色
    # ========================================================

    wave_prediction = (
        predicted_attrs.get(
            "wave",
            {},
        )
    )

    wave_main = (
        actual_attrs["wave"]
        ==
        wave_prediction.get(
            "main",
            "",
        )
    )

    wave_secondary = (
        actual_attrs["wave"]
        ==
        wave_prediction.get(
            "secondary",
            "",
        )
    )

    wave_double = (
        actual_attrs["wave"]
        in wave_prediction.get(
            "double",
            [],
        )
    )

    # ========================================================
    # 返回
    # ========================================================

    return {

        "issue":
            str(
                actual.get(
                    "issue",
                    "",
                )
            ),

        "actual_special":
            actual_special,

        # ----------------------------
        # 号码
        # ----------------------------

        "number_top5":
            top5_hits > 0,

        "number_top10":
            top10_hits > 0,

        "number_top12":
            top12_hits > 0,

        "number_top5_hits":
            top5_hits,

        "number_top10_hits":
            top10_hits,

        "number_top12_hits":
            top12_hits,

        # ----------------------------
        # 生肖
        # ----------------------------

        "zodiac_main":
            zodiac_main,

        "zodiac_secondary":
            zodiac_secondary,

        "zodiac_double":
            zodiac_double,

        # ----------------------------
        # 单双
        # ----------------------------

        "odd_even_main":
            odd_main,

        "odd_even_secondary":
            odd_secondary,

        "odd_even_double":
            odd_double,

        # ----------------------------
        # 大小
        # ----------------------------

        "size_main":
            size_main,

        "size_secondary":
            size_secondary,

        "size_double":
            size_double,

        # ----------------------------
        # 波色
        # ----------------------------

        "wave_main":
            wave_main,

        "wave_secondary":
            wave_secondary,

        "wave_double":
            wave_double,
    }


# ============================================================
# Walk-Forward 性能统计
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

    # ========================================================
    # 平均号码命中数
    # ========================================================

    def average(
        key: str,
    ) -> float:

        values = []

        for item in evaluations:

            try:
                values.append(
                    float(
                        item.get(
                            key,
                            0,
                        )
                    )
                )

            except Exception:
                continue

        if not values:
            return 0.0

        return round(
            sum(values)
            / len(values),
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

            "average_top5_hits":
                average(
                    "number_top5_hits"
                ),

            "average_top10_hits":
                average(
                    "number_top10_hits"
                ),

            "average_top12_hits":
                average(
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

            "secondary":
                hit_rate(
                    count(
                        "zodiac_secondary"
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

            "secondary":
                hit_rate(
                    count(
                        "odd_even_secondary"
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

            "secondary":
                hit_rate(
                    count(
                        "size_secondary"
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


# ============================================================
# 当前预测的属性摘要
# ============================================================

def build_prediction_summary(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    return {

        "zodiac":
            predict_attribute(
                history,
                "zodiac",
            ),

        "odd_even":
            predict_attribute(
                history,
                "odd_even",
            ),

        "size":
            predict_attribute(
                history,
                "size",
            ),

        "wave":
            predict_attribute(
                history,
                "wave",
            ),
    }
