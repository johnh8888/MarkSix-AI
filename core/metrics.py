# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V7.2
命中率与属性分析模块

规则：

1. 号码只针对第7个特别号码
2. Top5 / Top10 / Top12 一期最多命中1次
3. 生肖只针对特别号码
4. 生肖推荐5个
5. 单双只推荐1个
6. 大小只推荐1个
7. 波色主推 / 次推 / 双色
8. Walk-Forward 严格使用历史数据预测下一期
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

    按六合彩号码生肖轮转方式计算。
    """

    number = int(number)
    year = int(year)

    # 2024 = 龙
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
# 获取特别号
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
# 历史特别号属性
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

    ranking = [
        item[0]
        for item in counter.most_common()
    ]

    # 确保最多5个
    top5 = ranking[:5]

    # 不足5个时补齐
    for animal in ANIMALS:

        if animal not in top5:

            top5.append(animal)

        if len(top5) >= 5:
            break

    return {

        "main":
            top5[0] if top5 else "",

        "secondary":
            top5[1] if len(top5) > 1 else "",

        "top5":
            top5[:5],

        "double":
            top5[:5],

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

    if not counter:

        return {
            "main": "",
            "secondary": "",
            "double": [],
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

        "main":
            main,

        "secondary":
            secondary,

        "double":
            ranking[:2],

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

    wave_double = wave.get(
        "double",
        [],
    )[:2]

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

        },

        "odd_even": {

            "main":
                odd_even["main"],

            "secondary":
                odd_even["secondary"],

            "double":
                [odd_even["main"]]
                if odd_even["main"]
                else [],

        },

        "size": {

            "main":
                size["main"],

            "secondary":
                size["secondary"],

            "double":
                [size["main"]]
                if size["main"]
                else [],

        },

        "wave": {

            "main":
                wave["main"],

            "secondary":
                wave["secondary"],

            "double":
                wave_double,

        },

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
# Walk-Forward 单期评估
# ============================================================

def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:

    """
    注意：

    这里只允许两个参数。

    prediction:
        当前预测

    actual:
        下一期真实开奖

    特别号永远只使用 numbers[6]。
    """

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
    # 真实特别号属性
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
    # 单双
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
    # 大小
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
# Walk-Forward 汇总
# ============================================================

def calculate_performance(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(
        evaluations
    )

    if total <= 0:

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
    # ============================================================
# 兼容 core/engine.py 调用方式的补丁
# 追加到 core/metrics.py 文件末尾
# ============================================================

# 保留原始 evaluate_prediction（2参数版本）的引用，
# 下面用新的3参数版本覆盖同名函数，内部转调原始逻辑。
_original_evaluate_prediction = evaluate_prediction


def evaluate_prediction(
    prediction: dict,
    actual: dict,
    train: list | None = None,
) -> dict:

    """
    兼容 engine.py：

        evaluate_prediction(prediction, actual, train)

    train 参数当前未使用（预留给未来需要训练集上下文的评估逻辑），
    实际评估仍完全复用原始的2参数版本。
    """

    return _original_evaluate_prediction(
        prediction,
        actual,
    )


def predict_attribute(
    history: list[dict],
    field: str,
    limit: int = 100,
) -> dict:

    """
    兼容 engine.py：

        predict_attribute(history, "zodiac")
        predict_attribute(history, "odd_even")
        predict_attribute(history, "size")
        predict_attribute(history, "wave")

    单数版本，按字段名单独调用。
    内部复用已有的 predict_zodiac / predict_single_attribute。
    """

    if field == "zodiac":

        result = predict_zodiac(
            history,
            limit,
        )

        return {
            "main": result["main"],
            "secondary": result["secondary"],
            "top5": result["top5"],
            "double": result["top5"],
        }

    result = predict_single_attribute(
        history,
        field,
        limit,
    )

    return {
        "main": result["main"],
        "secondary": result["secondary"],
        "double": (
            [result["main"]]
            if result["main"]
            else []
        ),
    }

