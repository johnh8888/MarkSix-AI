# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V7.3
命中率 + 概率评分 + 最近10期回测

核心规则：

1. 号码只针对第7个特别号码
2. Top5 / Top10 / Top12 一期最多命中1次
3. 生肖只针对特别号码
4. 生肖推荐5个
5. 单双只推荐1个主推
6. 大小只推荐1个主推
7. 波色主推 / 次推 / 双色
8. 回测严格使用最近10期
9. 每种属性增加历史概率评分
10. 数据源与原系统完全兼容

注意：

这里的 probability 是基于模型历史样本计算出来的
“历史概率/概率分数”，不是保证未来开奖的真实概率。
"""

from __future__ import annotations

from collections import Counter
from typing import Any


# ============================================================
# 全局配置
# ============================================================

# 属性预测使用多少期历史
ATTRIBUTE_HISTORY_LIMIT = 100

# 回测只使用最新多少期
BACKTEST_RECENT_N = 10


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
# 历史特别号属性统计
# ============================================================

def special_attribute_counter(
    history: list[dict[str, Any]],
    field: str,
    limit: int = ATTRIBUTE_HISTORY_LIMIT,
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
# 概率计算
# ============================================================

def counter_to_probability(
    counter: Counter,
) -> dict[str, float]:

    """
    Counter
    ↓
    百分比概率

    例如：

    单：54
    双：46

    返回：

    {
        "单": 54.0,
        "双": 46.0
    }
    """

    total = sum(
        counter.values()
    )

    if total <= 0:
        return {}

    result = {}

    for key, value in counter.items():

        result[key] = round(
            value / total * 100,
            2,
        )

    return result


# ============================================================
# 排序后的概率
# ============================================================

def probability_ranking(
    counter: Counter,
) -> list[tuple[str, float]]:

    probabilities = counter_to_probability(
        counter
    )

    ranking = sorted(
        probabilities.items(),
        key=lambda x: (
            x[1],
            counter.get(x[0], 0),
        ),
        reverse=True,
    )

    return ranking


# ============================================================
# 生肖预测 + 概率
# ============================================================

def predict_zodiac(
    history: list[dict[str, Any]],
    limit: int = ATTRIBUTE_HISTORY_LIMIT,
) -> dict[str, Any]:

    counter = special_attribute_counter(
        history,
        "zodiac",
        limit,
    )

    ranking = probability_ranking(
        counter
    )

    probability_map = {
        animal: probability
        for animal, probability in ranking
    }

    ranking_names = [
        item[0]
        for item in ranking
    ]

    # ========================================================
    # Top5
    # ========================================================

    top5 = ranking_names[:5]

    # 不足5个时补齐
    for animal in ANIMALS:

        if animal not in top5:

            top5.append(animal)

        if len(top5) >= 5:
            break

    # ========================================================
    # 补齐没有出现过的生肖概率
    # ========================================================

    for animal in ANIMALS:

        if animal not in probability_map:

            probability_map[animal] = 0.0

    # ========================================================
    # 主推
    # ========================================================

    main = (
        top5[0]
        if top5
        else ""
    )

    secondary = (
        top5[1]
        if len(top5) > 1
        else ""
    )

    return {

        "main":
            main,

        "secondary":
            secondary,

        "top5":
            top5[:5],

        "double":
            top5[:5],

        # 全部生肖概率
        "probabilities":
            probability_map,

        # 主推概率
        "main_probability":
            probability_map.get(
                main,
                0.0,
            ),

        # Top5概率
        "top5_probabilities": {
            animal:
                probability_map.get(
                    animal,
                    0.0,
                )
            for animal in top5[:5]
        },

        "sample_count":
            sum(counter.values()),

    }


# ============================================================
# 单一属性预测 + 概率
# ============================================================

def predict_single_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = ATTRIBUTE_HISTORY_LIMIT,
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

            "probabilities": {},

            "main_probability": 0.0,

            "sample_count": 0,

        }

    ranking = probability_ranking(
        counter
    )

    ranking_names = [
        item[0]
        for item in ranking
    ]

    probability_map = {
        key: probability
        for key, probability in ranking
    }

    main = ranking_names[0]

    secondary = (
        ranking_names[1]
        if len(ranking_names) > 1
        else ""
    )

    return {

        "main":
            main,

        "secondary":
            secondary,

        "double":
            ranking_names[:2],

        # 所有状态概率
        "probabilities":
            probability_map,

        # 主推概率
        "main_probability":
            probability_map.get(
                main,
                0.0,
            ),

        # 次推概率
        "secondary_probability":
            probability_map.get(
                secondary,
                0.0,
            ),

        "sample_count":
            sum(counter.values()),

    }


# ============================================================
# 统一属性预测
# ============================================================

def predict_attributes(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    zodiac = predict_zodiac(
        history,
        ATTRIBUTE_HISTORY_LIMIT,
    )

    odd_even = predict_single_attribute(
        history,
        "odd_even",
        ATTRIBUTE_HISTORY_LIMIT,
    )

    size = predict_single_attribute(
        history,
        "size",
        ATTRIBUTE_HISTORY_LIMIT,
    )

    wave = predict_single_attribute(
        history,
        "wave",
        ATTRIBUTE_HISTORY_LIMIT,
    )

    wave_double = wave.get(
        "double",
        [],
    )[:2]

    # ========================================================
    # 波色双色概率
    # ========================================================

    wave_probabilities = wave.get(
        "probabilities",
        {},
    )

    wave_double_probability = round(
        sum(
            wave_probabilities.get(
                color,
                0.0,
            )
            for color in wave_double
        ),
        2,
    )

    return {

        # ====================================================
        # 生肖
        # ====================================================

        "zodiac": {

            "main":
                zodiac["main"],

            "secondary":
                zodiac["secondary"],

            "top5":
                zodiac["top5"],

            "double":
                zodiac["top5"],

            "probabilities":
                zodiac["probabilities"],

            "main_probability":
                zodiac["main_probability"],

            "top5_probabilities":
                zodiac["top5_probabilities"],

        },

        # ====================================================
        # 单双
        # ====================================================

        "odd_even": {

            # 只推荐主推
            "main":
                odd_even["main"],

            # 保留内部数据，兼容旧代码
            "secondary":
                odd_even["secondary"],

            "double":
                [odd_even["main"]]
                if odd_even["main"]
                else [],

            # 概率
            "probabilities":
                odd_even["probabilities"],

            "main_probability":
                odd_even["main_probability"],

        },

        # ====================================================
        # 大小
        # ====================================================

        "size": {

            # 只推荐主推
            "main":
                size["main"],

            # 保留内部数据
            "secondary":
                size["secondary"],

            "double":
                [size["main"]]
                if size["main"]
                else [],

            # 概率
            "probabilities":
                size["probabilities"],

            "main_probability":
                size["main_probability"],

        },

        # ====================================================
        # 波色
        # ====================================================

        "wave": {

            "main":
                wave["main"],

            "secondary":
                wave["secondary"],

            "double":
                wave_double,

            "probabilities":
                wave["probabilities"],

            "main_probability":
                wave["main_probability"],

            "secondary_probability":
                wave["secondary_probability"],

            "double_probability":
                wave_double_probability,

        },

    }


# ============================================================
# 单数版本：兼容 engine.py
# ============================================================

def predict_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = ATTRIBUTE_HISTORY_LIMIT,
) -> dict[str, Any]:

    """
    兼容：

        predict_attribute(history, "zodiac")
        predict_attribute(history, "odd_even")
        predict_attribute(history, "size")
        predict_attribute(history, "wave")
    """

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

            "probabilities":
                result["probabilities"],

            "main_probability":
                result["main_probability"],

            "top5_probabilities":
                result["top5_probabilities"],

        }

    result = predict_single_attribute(
        history,
        field,
        limit,
    )

    return {

        "main":
            result["main"],

        "secondary":
            result["secondary"],

        "double":
            result["double"],

        "probabilities":
            result["probabilities"],

        "main_probability":
            result["main_probability"],

        "secondary_probability":
            result["secondary_probability"],

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
# Walk-Forward 单期评估
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
# Walk-Forward 汇总
# ============================================================

def calculate_performance(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:

    """
    只使用最近10期进行回测。

    evaluations 必须按照开奖时间/期号从旧到新排列。
    """

    # ========================================================
    # 核心修改：
    # 只取最新10期
    # ========================================================

    recent_evaluations = evaluations[
        -BACKTEST_RECENT_N:
    ]

    total = len(
        recent_evaluations
    )

    if total <= 0:

        return {

            "samples": 0,

            "backtest_period":
                BACKTEST_RECENT_N,

            "status":
                "历史数据不足",

        }

    def count(
        key: str,
    ) -> int:

        return sum(
            1
            for item in recent_evaluations
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

    # ========================================================
    # 返回
    # ========================================================

    return {

        "samples":
            total,

        "backtest_period":
            BACKTEST_RECENT_N,

        # ====================================================
        # 号码
        # ====================================================

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

        # ====================================================
        # 生肖
        # ====================================================

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

        # ====================================================
        # 单双
        # ====================================================

        "odd_even": {

            "main":
                hit_rate(
                    odd_even_hits,
                    total,
                ),

        },

        # ====================================================
        # 大小
        # ====================================================

        "size": {

            "main":
                hit_rate(
                    size_hits,
                    total,
                ),

        },

        # ====================================================
        # 波色
        # ====================================================

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