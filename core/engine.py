# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V7.4
属性概率 + 最近10期Walk-Forward

规则：

1. 号码只针对第7个特别号码
2. Top5 / Top10 / Top12
3. 生肖推荐5个
4. 单双只推荐1个主推
5. 大小只推荐1个主推
6. 波色主推 / 次推 / 双色
7. 所有属性增加概率分数
8. Walk-Forward 最终只统计最近10期
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


# ============================================================
# 波色
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


# ============================================================
# 大小
# ============================================================

def get_size(number: int) -> str:

    number = int(number)

    return "大" if number >= 25 else "小"


# ============================================================
# 单双
# ============================================================

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

    """
    2024 = 龙
    2025 = 蛇
    2026 = 马
    """

    number = int(number)
    year = int(year)

    base_index = 4

    year_index = (
        base_index
        + (year - 2024)
    ) % 12

    return ANIMALS[
        (year_index - (number - 1)) % 12
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
# 特别号码
# ============================================================

def get_special_number(
    record: dict[str, Any],
) -> int | None:

    numbers = record.get(
        "numbers",
        [],
    )

    if not isinstance(
        numbers,
        (list, tuple),
    ):

        return None

    if len(numbers) != 7:

        return None

    try:

        number = int(
            numbers[6]
        )

    except Exception:

        return None

    if not 1 <= number <= 49:

        return None

    return number


# ============================================================
# 属性计数
# ============================================================

def special_attribute_counter(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 100,
) -> Counter:

    counter = Counter()

    if not history:
        return counter

    for row in history[-limit:]:

        special = get_special_number(
            row
        )

        if special is None:
            continue

        issue = str(
            row.get(
                "issue",
                "",
            )
        )

        if field == "wave":

            value = get_wave(
                special
            )

        elif field == "size":

            value = get_size(
                special
            )

        elif field == "odd_even":

            value = get_odd_even(
                special
            )

        elif field == "zodiac":

            value = get_zodiac(
                special,
                issue,
            )

        else:

            continue

        if value:

            counter[value] += 1

    return counter


# ============================================================
# 概率分数
# ============================================================

def probability_scores(
    counter: Counter,
    categories: list[str] | None = None,
) -> dict[str, float]:

    """
    根据历史统计频率计算概率分数。

    例如：

        单 = 6
        双 = 4

    则：

        单 = 60%
        双 = 40%

    如果指定 categories，则没有出现过的类别也会显示0。
    """

    if categories is None:

        categories = list(
            counter.keys()
        )

    total = sum(
        counter.get(
            item,
            0,
        )
        for item in categories
    )

    if total <= 0:

        if not categories:
            return {}

        equal = round(
            100 / len(categories),
            2,
        )

        result = {
            item: equal
            for item in categories
        }

        # 修正四舍五入导致的总和不等于100
        diff = round(
            100 - sum(result.values()),
            2,
        )

        result[categories[0]] = round(
            result[categories[0]] + diff,
            2,
        )

        return result

    result = {}

    for item in categories:

        result[item] = round(
            counter.get(
                item,
                0,
            ) / total * 100,
            2,
        )

    return result


# ============================================================
# 生肖预测
# ============================================================

def predict_zodiac(
    history: list[dict[str, Any]],
    limit: int = 100,
) -> dict[str, Any]:

    counter = special_attribute_counter(
        history,
        "zodiac",
        limit,
    )

    probability = probability_scores(
        counter,
        ANIMALS,
    )

    ranking = sorted(
        ANIMALS,
        key=lambda x: (
            -probability.get(x, 0),
            -counter.get(x, 0),
            ANIMALS.index(x),
        ),
    )

    top5 = ranking[:5]

    return {

        "main":
            top5[0] if top5 else "",

        "secondary":
            top5[1] if len(top5) > 1 else "",

        "top5":
            top5,

        "double":
            top5,

        "probability":
            probability,

    }


# ============================================================
# 单一属性预测
# ============================================================

def predict_single_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 100,
) -> dict[str, Any]:

    counter = special_attribute_counter(
        history,
        field,
        limit,
    )

    if field == "odd_even":

        categories = [
            "单",
            "双",
        ]

    elif field == "size":

        categories = [
            "小",
            "大",
        ]

    elif field == "wave":

        categories = [
            "红",
            "蓝",
            "绿",
        ]

    else:

        categories = list(
            counter.keys()
        )

    probability = probability_scores(
        counter,
        categories,
    )

    ranking = sorted(
        categories,
        key=lambda x: (
            -probability.get(x, 0),
            -counter.get(x, 0),
            categories.index(x),
        ),
    )

    main = (
        ranking[0]
        if ranking
        else ""
    )

    secondary = (
        ranking[1]
        if len(ranking) > 1
        else ""
    )

    return {

        "main":
            main,

        "secondary":
            secondary,

        "double":
            ranking[:2],

        "probability":
            probability,

    }


# ============================================================
# 统一属性预测
# ============================================================

def predict_attributes(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    zodiac = predict_zodiac(
        history
    )

    odd_even = predict_single_attribute(
        history,
        "odd_even",
    )

    size = predict_single_attribute(
        history,
        "size",
    )

    wave = predict_single_attribute(
        history,
        "wave",
    )

    return {

        "zodiac": {

            "main":
                zodiac["main"],

            "secondary":
                zodiac["secondary"],

            "top5":
                zodiac["top5"],

            "double":
                zodiac["top5"],

            "probability":
                zodiac["probability"],

        },

        "odd_even": {

            "main":
                odd_even["main"],

            # 保留字段兼容旧程序，
            # 但不再作为预测结果使用
            "secondary":
                "",

            "double":
                (
                    [odd_even["main"]]
                    if odd_even["main"]
                    else []
                ),

            "probability":
                odd_even["probability"],

        },

        "size": {

            "main":
                size["main"],

            "secondary":
                "",

            "double":
                (
                    [size["main"]]
                    if size["main"]
                    else []
                ),

            "probability":
                size["probability"],

        },

        "wave": {

            "main":
                wave["main"],

            "secondary":
                wave["secondary"],

            "double":
                wave["double"],

            "probability":
                wave["probability"],

        },

    }


# ============================================================
# 单字段兼容接口
# ============================================================

def predict_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 100,
) -> dict[str, Any]:

    if field == "zodiac":

        result = predict_zodiac(
            history,
            limit,
        )

        return {

            "main":
                result["main"],

            "secondary":
                result["secondary"],

            "top5":
                result["top5"],

            "double":
                result["top5"],

            "probability":
                result["probability"],

        }

    result = predict_single_attribute(
        history,
        field,
        limit,
    )

    # 单双 / 大小只保留主推
    if field in (
        "odd_even",
        "size",
    ):

        return {

            "main":
                result["main"],

            "secondary":
                "",

            "double":
                (
                    [result["main"]]
                    if result["main"]
                    else []
                ),

            "probability":
                result["probability"],

        }

    return result


# ============================================================
# Walk-Forward 单期评估
# ============================================================

def _evaluate_prediction_core(
    prediction: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:

    actual_special = get_special_number(
        actual
    )

    if actual_special is None:

        return {}

    issue = str(
        actual.get(
            "issue",
            "",
        )
    )

    result: dict[str, Any] = {}

    # ========================================================
    # 号码
    # ========================================================

    candidates = prediction.get(
        "candidates",
        [],
    )

    top5 = prediction.get(
        "top5",
        candidates[:5],
    )

    top10 = prediction.get(
        "top10",
        candidates[:10],
    )

    top12 = prediction.get(
        "top12",
        candidates[:12],
    )

    result["number_top5"] = (
        actual_special
        in set(top5)
    )

    result["number_top10"] = (
        actual_special
        in set(top10)
    )

    result["number_top12"] = (
        actual_special
        in set(top12)
    )

    # ========================================================
    # 真实属性
    # ========================================================

    actual_zodiac = get_zodiac(
        actual_special,
        issue,
    )

    actual_wave = get_wave(
        actual_special
    )

    actual_size = get_size(
        actual_special
    )

    actual_odd_even = get_odd_even(
        actual_special
    )

    attrs = prediction.get(
        "attributes",
        {},
    )

    # ========================================================
    # 生肖
    # ========================================================

    zodiac = attrs.get(
        "zodiac",
        {},
    )

    zodiac_main = zodiac.get(
        "main",
        "",
    )

    zodiac_top5 = zodiac.get(
        "top5",
        zodiac.get(
            "double",
            [],
        ),
    )

    result["zodiac_main"] = (
        actual_zodiac
        == zodiac_main
    )

    result["zodiac_top5"] = (
        actual_zodiac
        in set(zodiac_top5)
    )

    # ========================================================
    # 单双：只有主推
    # ========================================================

    odd_even = attrs.get(
        "odd_even",
        {},
    )

    odd_even_main = odd_even.get(
        "main",
        "",
    )

    result["odd_even_main"] = (
        actual_odd_even
        == odd_even_main
    )

    # ========================================================
    # 大小：只有主推
    # ========================================================

    size = attrs.get(
        "size",
        {},
    )

    size_main = size.get(
        "main",
        "",
    )

    result["size_main"] = (
        actual_size
        == size_main
    )

    # ========================================================
    # 波色
    # ========================================================

    wave = attrs.get(
        "wave",
        {},
    )

    wave_main = wave.get(
        "main",
        "",
    )

    wave_secondary = wave.get(
        "secondary",
        "",
    )

    wave_double = wave.get(
        "double",
        [],
    )[:2]

    result["wave_main"] = (
        actual_wave
        == wave_main
    )

    result["wave_secondary"] = (
        actual_wave
        == wave_secondary
    )

    result["wave_double"] = (
        actual_wave
        in set(wave_double)
    )

    return result


# ============================================================
# 对外评估接口
# ============================================================

def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
    train: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    return _evaluate_prediction_core(
        prediction,
        actual,
    )


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
# 最近10期回测
# ============================================================

def calculate_performance(
    evaluations: list[dict[str, Any]],
    recent_n: int = 10,
) -> dict[str, Any]:

    """
    只使用最后 recent_n 个Walk-Forward验证结果。

    默认：
        最近10期

    注意：
    Walk-Forward 本身仍然是历史滚动预测，
    这里只限制最终统计窗口为最近10次验证。
    """

    if not evaluations:

        return {

            "samples": 0,

            "backtest_window":
                recent_n,

            "status":
                "历史数据不足",

        }

    # ========================================================
    # 只取最后10期
    # ========================================================

    evaluations = evaluations[
        -recent_n:
    ]

    total = len(
        evaluations
    )

    if total <= 0:

        return {

            "samples": 0,

            "backtest_window":
                recent_n,

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
    # 号码
    # ========================================================

    number_top5_hits = count(
        "number_top5"
    )

    number_top10_hits = count(
        "number_top10"
    )

    number_top12_hits = count(
        "number_top12"
    )

    # ========================================================
    # 生肖
    # ========================================================

    zodiac_main_hits = count(
        "zodiac_main"
    )

    zodiac_top5_hits = count(
        "zodiac_top5"
    )

    # ========================================================
    # 单双
    # ========================================================

    odd_even_hits = count(
        "odd_even_main"
    )

    # ========================================================
    # 大小
    # ========================================================

    size_hits = count(
        "size_main"
    )

    # ========================================================
    # 波色
    # ========================================================

    wave_main_hits = count(
        "wave_main"
    )

    wave_secondary_hits = count(
        "wave_secondary"
    )

    wave_double_hits = count(
        "wave_double"
    )

    return {

        "samples":
            total,

        "backtest_window":
            recent_n,

        "numbers": {

            "top5":
                hit_rate(
                    number_top5_hits,
                    total,
                ),

            "top10":
                hit_rate(
                    number_top10_hits,
                    total,
                ),

            "top12":
                hit_rate(
                    number_top12_hits,
                    total,
                ),

            "average_top5_hits":
                round(
                    number_top5_hits / total,
                    4,
                ),

            "average_top10_hits":
                round(
                    number_top10_hits / total,
                    4,
                ),

            "average_top12_hits":
                round(
                    number_top12_hits / total,
                    4,
                ),

        },

        "zodiac": {

            "main":
                hit_rate(
                    zodiac_main_hits,
                    total,
                ),

            "top5":
                hit_rate(
                    zodiac_top5_hits,
                    total,
                ),

        },

        "odd_even": {

            "main":
                hit_rate(
                    odd_even_hits,
                    total,
                ),

        },

        "size": {

            "main":
                hit_rate(
                    size_hits,
                    total,
                ),

        },

        "wave": {

            "main":
                hit_rate(
                    wave_main_hits,
                    total,
                ),

            "secondary":
                hit_rate(
                    wave_secondary_hits,
                    total,
                ),

            "double":
                hit_rate(
                    wave_double_hits,
                    total,
                ),

        },

        "status":
            "正常",

    }