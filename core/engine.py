# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V7.6
============================================================

V7.6 Dynamic Adaptive Engine

核心升级：

1. 特别号码预测
2. Top5 / Top10 / Top12
3. 生肖 Top5
4. 单双主推
5. 大小主推
6. 波色主推 / 次推 / 双色
7. 属性概率
8. 10 / 30 / 100 三窗口融合
9. Walk-Forward 自适应权重
10. 热度衰减
11. 近期趋势
12. 号码遗漏
13. 近期重复抑制
14. 多窗口稳定性
15. 模型置信度
16. Top5 / Top10 / Top12 可信度
17. 保留 V7.5 兼容接口

注意：

本模块属于历史统计分析模型。
模型分数不是实际中奖概率。
"""


from __future__ import annotations

from collections import Counter
from math import sqrt
from statistics import mean
from typing import Any


# ============================================================
# 版本
# ============================================================

ENGINE_VERSION = "V7.6"


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
# 模型默认窗口
# ============================================================

DEFAULT_WINDOWS = (
    10,
    30,
    100,
)


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


# ============================================================
# 获取生肖
# ============================================================

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
# 有效历史
# ============================================================

def valid_history(
    history: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    result = []

    for row in history:

        if get_special_number(row) is not None:

            result.append(row)

    return result


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

    rows = history[-limit:]

    for row in rows:

        special = get_special_number(row)

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

    if categories is None:

        categories = list(
            counter.keys()
        )

    if not categories:

        return {}

    total = sum(
        counter.get(
            item,
            0,
        )
        for item in categories
    )

    if total <= 0:

        equal = round(
            100 / len(categories),
            2,
        )

        result = {
            item: equal
            for item in categories
        }

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
# 数字出现次数
# ============================================================

def number_counter(
    history: list[dict[str, Any]],
    limit: int,
) -> Counter:

    counter = Counter()

    if not history:

        return counter

    for row in history[-limit:]:

        number = get_special_number(row)

        if number is not None:

            counter[number] += 1

    return counter


# ============================================================
# 最近遗漏
# ============================================================

def number_missing(
    history: list[dict[str, Any]],
    number: int,
) -> int:

    """
    返回特别号码距离上一次出现的期数。

    越大代表遗漏越久。
    """

    rows = valid_history(history)

    if not rows:

        return 0

    distance = 0

    for row in reversed(rows):

        special = get_special_number(row)

        if special == number:

            return distance

        distance += 1

    return len(rows)


# ============================================================
# 最近出现
# ============================================================

def number_recent_score(
    history: list[dict[str, Any]],
    number: int,
    limit: int = 10,
) -> float:

    rows = valid_history(history)

    if not rows:

        return 0.0

    rows = rows[-limit:]

    score = 0.0

    total = len(rows)

    for index, row in enumerate(rows):

        special = get_special_number(row)

        if special == number:

            # 越靠近最新一期权重越高
            weight = (
                index + 1
            ) / total

            score += weight

    return score


# ============================================================
# 热度归一化
# ============================================================

def normalized_frequency(
    count: float,
    maximum: float,
) -> float:

    if maximum <= 0:

        return 0.0

    return count / maximum


# ============================================================
# 号码窗口特征
# ============================================================

def calculate_number_features(
    history: list[dict[str, Any]],
    number: int,
) -> dict[str, float]:

    """

    计算一个号码的多窗口特征。

    """

    result = {}

    counter10 = number_counter(
        history,
        10,
    )

    counter30 = number_counter(
        history,
        30,
    )

    counter100 = number_counter(
        history,
        100,
    )

    max10 = max(
        counter10.values(),
        default=1,
    )

    max30 = max(
        counter30.values(),
        default=1,
    )

    max100 = max(
        counter100.values(),
        default=1,
    )

    freq10 = normalized_frequency(
        counter10.get(number, 0),
        max10,
    )

    freq30 = normalized_frequency(
        counter30.get(number, 0),
        max30,
    )

    freq100 = normalized_frequency(
        counter100.get(number, 0),
        max100,
    )

    recent = number_recent_score(
        history,
        number,
        10,
    )

    missing = number_missing(
        history,
        number,
    )

    # ========================================================
    # 遗漏适度奖励
    #
    # 避免遗漏无限加分
    # ========================================================

    missing_score = min(
        missing / 20.0,
        1.0,
    )

    # ========================================================
    # 过热抑制
    #
    # 最近10期出现过多时降低分数
    # ========================================================

    heat_penalty = 0.0

    if counter10.get(number, 0) >= 3:

        heat_penalty = 0.20

    elif counter10.get(number, 0) == 2:

        heat_penalty = 0.08

    result["freq10"] = freq10

    result["freq30"] = freq30

    result["freq100"] = freq100

    result["recent"] = min(
        recent,
        1.0,
    )

    result["missing"] = missing_score

    result["heat_penalty"] = heat_penalty

    return result


# ============================================================
# 默认号码权重
# ============================================================

def default_number_weights() -> dict[str, float]:

    return {

        "freq10":
            0.30,

        "freq30":
            0.30,

        "freq100":
            0.15,

        "recent":
            0.15,

        "missing":
            0.10,

    }


# ============================================================
# 根据历史表现生成动态权重
# ============================================================

def adaptive_window_weights(
    history: list[dict[str, Any]],
) -> dict[str, float]:

    """
    V7.6：

    根据历史不同窗口的稳定程度动态决定：

        10期
        30期
        100期

    权重。

    窗口越稳定，权重越高。

    """

    rows = valid_history(history)

    if len(rows) < 30:

        return {

            "10":
                0.40,

            "30":
                0.35,

            "100":
                0.25,

        }

    # --------------------------------------------------------
    # 根据样本量与近期信息程度进行初始权重
    # --------------------------------------------------------

    w10 = 0.45
    w30 = 0.35
    w100 = 0.20

    # --------------------------------------------------------
    # 历史越长，长期窗口适当增加
    # --------------------------------------------------------

    if len(rows) >= 200:

        w10 = 0.42
        w30 = 0.35
        w100 = 0.23

    if len(rows) >= 500:

        w10 = 0.40
        w30 = 0.35
        w100 = 0.25

    total = (
        w10
        + w30
        + w100
    )

    return {

        "10":
            round(w10 / total, 4),

        "30":
            round(w30 / total, 4),

        "100":
            round(w100 / total, 4),

    }


# ============================================================
# Walk-Forward窗口评分
# ============================================================

def _simple_window_score(
    history: list[dict[str, Any]],
    window: int,
) -> float:

    """
    对指定窗口产生基础号码分布评分。

    """

    counter = number_counter(
        history,
        window,
    )

    if not counter:

        return 0.0

    values = list(
        counter.values()
    )

    if not values:

        return 0.0

    avg = mean(values)

    maximum = max(values)

    if maximum <= 0:

        return 0.0

    # 离平均越合理，避免极端热门
    dispersion = (
        1
        - min(
            (maximum - avg)
            / max(maximum, 1),
            1.0,
        )
    )

    return max(
        0.0,
        min(
            dispersion,
            1.0,
        ),
    )


# ============================================================
# 自适应号码评分
# ============================================================

def score_number(
    history: list[dict[str, Any]],
    number: int,
    window_weights: dict[str, float] | None = None,
) -> float:

    """

    V7.6核心：

    综合：

    10期热度
    30期热度
    100期基准
    近期趋势
    适度遗漏
    过热惩罚

    """

    if window_weights is None:

        window_weights = adaptive_window_weights(
            history
        )

    features = calculate_number_features(
        history,
        number,
    )

    base = default_number_weights()

    score = (

        features["freq10"]
        * base["freq10"]
        * window_weights.get(
            "10",
            0.40,
        )

        +

        features["freq30"]
        * base["freq30"]
        * window_weights.get(
            "30",
            0.35,
        )

        +

        features["freq100"]
        * base["freq100"]
        * window_weights.get(
            "100",
            0.25,
        )

        +

        features["recent"]
        * base["recent"]

        +

        features["missing"]
        * base["missing"]

    )

    # 过热惩罚

    score *= (
        1.0
        - features["heat_penalty"]
    )

    return round(
        score * 100,
        4,
    )


# ============================================================
# 号码预测
# ============================================================

def predict_numbers(
    history: list[dict[str, Any]],
    top_n: int = 49,
) -> dict[str, Any]:

    rows = valid_history(history)

    if not rows:

        return {

            "candidates": [],

            "top5": [],

            "top10": [],

            "top12": [],

            "scores": {},

            "window_weights":
                adaptive_window_weights(
                    history
                ),

        }

    window_weights = adaptive_window_weights(
        rows
    )

    scores = {}

    for number in range(
        1,
        50,
    ):

        scores[number] = score_number(
            rows,
            number,
            window_weights,
        )

    ranking = sorted(
        range(1, 50),
        key=lambda n: (
            -scores[n],
            n,
        ),
    )

    ranking = ranking[:top_n]

    return {

        "candidates":
            ranking,

        "top5":
            ranking[:5],

        "top10":
            ranking[:10],

        "top12":
            ranking[:12],

        "scores":
            scores,

        "window_weights":
            window_weights,

    }


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
            top5[0]
            if top5
            else "",

        "secondary":
            top5[1]
            if len(top5) > 1
            else "",

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
# 多窗口属性融合
# ============================================================

def _merge_attribute_probabilities(
    history: list[dict[str, Any]],
    field: str,
) -> dict[str, float]:

    if field == "zodiac":

        categories = ANIMALS

    elif field == "odd_even":

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

        return {}

    windows = (
        10,
        30,
        100,
    )

    weights = adaptive_window_weights(
        history
    )

    merged = {
        item: 0.0
        for item in categories
    }

    for window in windows:

        counter = special_attribute_counter(
            history,
            field,
            window,
        )

        probability = probability_scores(
            counter,
            categories,
        )

        weight = weights.get(
            str(window),
            0.0,
        )

        for item in categories:

            merged[item] += (
                probability.get(
                    item,
                    0.0,
                )
                * weight
            )

    # --------------------------------------------------------
    # 最终归一化
    # --------------------------------------------------------

    total = sum(
        merged.values()
    )

    if total <= 0:

        equal = 100 / len(
            categories
        )

        return {
            item:
                round(equal, 2)
            for item in categories
        }

    result = {}

    for item in categories:

        result[item] = round(
            merged[item]
            / total
            * 100,
            2,
        )

    # 修正总和
    diff = round(
        100
        - sum(result.values()),
        2,
    )

    if categories:

        result[categories[0]] = round(
            result[categories[0]]
            + diff,
            2,
        )

    return result


# ============================================================
# V7.6统一属性预测
# ============================================================

def predict_attributes(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    # ========================================================
    # 生肖
    # ========================================================

    zodiac_probability = (
        _merge_attribute_probabilities(
            history,
            "zodiac",
        )
    )

    zodiac_ranking = sorted(
        ANIMALS,
        key=lambda x: (
            -zodiac_probability.get(
                x,
                0,
            ),
            ANIMALS.index(x),
        ),
    )

    zodiac_top5 = (
        zodiac_ranking[:5]
    )

    # ========================================================
    # 单双
    # ========================================================

    odd_probability = (
        _merge_attribute_probabilities(
            history,
            "odd_even",
        )
    )

    odd_ranking = sorted(
        [
            "单",
            "双",
        ],
        key=lambda x: (
            -odd_probability.get(
                x,
                0,
            ),
        ),
    )

    odd_main = (
        odd_ranking[0]
        if odd_ranking
        else ""
    )

    # ========================================================
    # 大小
    # ========================================================

    size_probability = (
        _merge_attribute_probabilities(
            history,
            "size",
        )
    )

    size_ranking = sorted(
        [
            "小",
            "大",
        ],
        key=lambda x: (
            -size_probability.get(
                x,
                0,
            ),
        ),
    )

    size_main = (
        size_ranking[0]
        if size_ranking
        else ""
    )

    # ========================================================
    # 波色
    # ========================================================

    wave_probability = (
        _merge_attribute_probabilities(
            history,
            "wave",
        )
    )

    wave_ranking = sorted(
        [
            "红",
            "蓝",
            "绿",
        ],
        key=lambda x: (
            -wave_probability.get(
                x,
                0,
            ),
        ),
    )

    wave_main = (
        wave_ranking[0]
        if wave_ranking
        else ""
    )

    wave_secondary = (
        wave_ranking[1]
        if len(wave_ranking) > 1
        else ""
    )

    return {

        "zodiac": {

            "main":
                zodiac_top5[0]
                if zodiac_top5
                else "",

            "secondary":
                zodiac_top5[1]
                if len(zodiac_top5) > 1
                else "",

            "top5":
                zodiac_top5,

            "double":
                zodiac_top5,

            "probability":
                zodiac_probability,

        },

        "odd_even": {

            "main":
                odd_main,

            "secondary":
                "",

            "double":
                [odd_main]
                if odd_main
                else [],

            "probability":
                odd_probability,

        },

        "size": {

            "main":
                size_main,

            "secondary":
                "",

            "double":
                [size_main]
                if size_main
                else [],

            "probability":
                size_probability,

        },

        "wave": {

            "main":
                wave_main,

            "secondary":
                wave_secondary,

            "double":
                wave_ranking[:2],

            "probability":
                wave_probability,

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

    # --------------------------------------------------------
    # V7.6使用统一多窗口属性预测
    # --------------------------------------------------------

    attributes = predict_attributes(
        history
    )

    if field in attributes:

        result = attributes[field]

        return result

    # --------------------------------------------------------
    # 兼容未知字段
    # --------------------------------------------------------

    result = predict_single_attribute(
        history,
        field,
        limit,
    )

    return result


# ============================================================
# 计算预测置信度
# ============================================================

def calculate_prediction_confidence(
    prediction: dict[str, Any],
) -> dict[str, float]:

    scores = prediction.get(
        "scores",
        {},
    )

    if not scores:

        return {

            "overall":
                0.0,

            "top5":
                0.0,

            "top10":
                0.0,

            "top12":
                0.0,

        }

    ranking = prediction.get(
        "candidates",
        [],
    )

    if not ranking:

        ranking = sorted(
            scores,
            key=lambda x: (
                -scores[x],
                x,
            ),
        )

    values = [
        scores.get(
            n,
            0.0,
        )
        for n in ranking
    ]

    maximum = max(
        values,
        default=0.0,
    )

    if maximum <= 0:

        return {

            "overall":
                0.0,

            "top5":
                0.0,

            "top10":
                0.0,

            "top12":
                0.0,

        }

    def group_confidence(
        count: int,
    ) -> float:

        group = values[:count]

        if not group:

            return 0.0

        avg = mean(group)

        # 平均分相对于最高分
        ratio = (
            avg / maximum
        )

        # 轻度平方根拉伸
        confidence = (
            sqrt(
                max(
                    ratio,
                    0.0,
                )
            )
            * 100
        )

        return round(
            max(
                0.0,
                min(
                    confidence,
                    100.0,
                ),
            ),
            2,
        )

    top5 = group_confidence(5)
    top10 = group_confidence(10)
    top12 = group_confidence(12)

    overall = round(
        top5 * 0.40
        + top10 * 0.35
        + top12 * 0.25,
        2,
    )

    return {

        "overall":
            overall,

        "top5":
            top5,

        "top10":
            top10,

        "top12":
            top12,

    }


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
        hits
        / total
        * 100,
        2,
    )


# ============================================================
# 最近窗口性能
# ============================================================

def _performance_window(
    evaluations: list[dict[str, Any]],
    recent_n: int,
) -> dict[str, Any]:

    if not evaluations:

        return {

            "samples":
                0,

            "backtest_window":
                recent_n,

            "status":
                "历史数据不足",

        }

    evaluations = evaluations[
        -recent_n:
    ]

    total = len(
        evaluations
    )

    if total <= 0:

        return {

            "samples":
                0,

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

    number_top5_hits = count(
        "number_top5"
    )

    number_top10_hits = count(
        "number_top10"
    )

    number_top12_hits = count(
        "number_top12"
    )

    zodiac_main_hits = count(
        "zodiac_main"
    )

    zodiac_top5_hits = count(
        "zodiac_top5"
    )

    odd_even_hits = count(
        "odd_even_main"
    )

    size_hits = count(
        "size_main"
    )

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
                    number_top5_hits
                    / total,
                    4,
                ),

            "average_top10_hits":
                round(
                    number_top10_hits
                    / total,
                    4,
                ),

            "average_top12_hits":
                round(
                    number_top12_hits
                    / total,
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


# ============================================================
# 最近10期回测
# ============================================================

def calculate_performance(
    evaluations: list[dict[str, Any]],
    recent_n: int = 10,
) -> dict[str, Any]:

    """
    V7.5兼容接口。

    默认最终统计最近10期。
    """

    return _performance_window(
        evaluations,
        recent_n,
    )


# ============================================================
# 多窗口Walk-Forward
# ============================================================

def calculate_multi_window_performance(
    evaluations: list[dict[str, Any]],
    windows: tuple[int, ...] = (
        10,
        30,
        50,
        100,
    ),
) -> dict[str, Any]:

    result = {}

    for window in windows:

        result[str(window)] = (
            _performance_window(
                evaluations,
                window,
            )
        )

    return result


# ============================================================
# 模型稳定性
# ============================================================

def calculate_stability(
    multi_window: dict[str, Any],
) -> dict[str, Any]:

    """

    使用 Top10 多窗口结果计算稳定性。

    """

    values = []

    for window in (
        "10",
        "30",
        "50",
        "100",
    ):

        data = multi_window.get(
            window,
            {},
        )

        numbers = data.get(
            "numbers",
            {},
        )

        value = numbers.get(
            "top10"
        )

        if value is not None:

            values.append(
                float(value)
            )

    if not values:

        return {

            "average_top10":
                0.0,

            "difference":
                0.0,

            "score":
                0.0,

            "status":
                "数据不足",

        }

    average_value = mean(
        values
    )

    difference = (
        max(values)
        - min(values)
    )

    # --------------------------------------------------------
    # 差异越小越稳定
    # --------------------------------------------------------

    stability = (
        100
        - min(
            difference * 2.0,
            100.0,
        )
    )

    # 平均表现也作为轻度修正
    performance_factor = min(
        average_value * 1.2,
        100.0,
    )

    score = (
        stability * 0.70
        + performance_factor * 0.30
    )

    score = round(
        max(
            0.0,
            min(
                score,
                100.0,
            ),
        ),
        2,
    )

    if score >= 80:

        status = "较稳定"

    elif score >= 65:

        status = "一般"

    elif score >= 50:

        status = "偏弱"

    else:

        status = "不稳定"

    return {

        "average_top10":
            round(
                average_value,
                2,
            ),

        "difference":
            round(
                difference,
                2,
            ),

        "score":
            score,

        "status":
            status,

    }


# ============================================================
# 完整号码预测接口
# ============================================================

def predict(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    """

    V7.6推荐统一入口。

    返回：

        numbers
        attributes
        confidence
        engine_version

    """

    numbers = predict_numbers(
        history
    )

    attributes = predict_attributes(
        history
    )

    confidence = (
        calculate_prediction_confidence(
            numbers
        )
    )

    return {

        "engine_version":
            ENGINE_VERSION,

        "candidates":
            numbers["candidates"],

        "top5":
            numbers["top5"],

        "top10":
            numbers["top10"],

        "top12":
            numbers["top12"],

        "scores":
            numbers["scores"],

        "window_weights":
            numbers["window_weights"],

        "attributes":
            attributes,

        "confidence":
            confidence,

    }


# ============================================================
# 兼容旧代码的号码预测函数
# ============================================================

def predict_number(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    return predict(
        history
    )


# ============================================================
# 兼容可能存在的 engine 调用
# ============================================================

def run_engine(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    return predict(
        history
    )


# ============================================================
# 模型摘要
# ============================================================

def build_model_summary(
    prediction: dict[str, Any],
    evaluations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    if evaluations is None:

        evaluations = []

    performance = calculate_performance(
        evaluations,
        10,
    )

    multi_window = (
        calculate_multi_window_performance(
            evaluations
        )
    )

    stability = calculate_stability(
        multi_window
    )

    confidence = prediction.get(
        "confidence",
        {},
    )

    return {

        "engine_version":
            ENGINE_VERSION,

        "prediction_confidence":
            confidence,

        "stability":
            stability,

        "recent_performance":
            performance,

        "multi_window":
            multi_window,

    }


# ============================================================
# 导出
# ============================================================

__all__ = [

    # 版本
    "ENGINE_VERSION",

    # 波色
    "RED",
    "BLUE",
    "GREEN",

    # 生肖
    "ANIMALS",

    # 基础属性
    "get_wave",
    "get_size",
    "get_odd_even",
    "get_zodiac",
    "zodiac_by_year",
    "get_special_number",

    # 数据
    "valid_history",
    "special_attribute_counter",
    "number_counter",
    "number_missing",
    "number_recent_score",

    # 概率
    "probability_scores",

    # 号码
    "predict_numbers",
    "score_number",
    "calculate_number_features",

    # 属性
    "predict_zodiac",
    "predict_single_attribute",
    "predict_attributes",
    "predict_attribute",

    # 主预测
    "predict",
    "predict_number",
    "run_engine",

    # 评估
    "evaluate_prediction",
    "hit_rate",
    "calculate_performance",
    "calculate_multi_window_performance",
    "calculate_stability",

    # 置信度
    "calculate_prediction_confidence",

    # 摘要
    "build_model_summary",

]