# -*- coding: utf-8 -*-

"""
============================================================
六合彩综合预测系统 V7.5
MULTI-WINDOW + TREND + MISSING + WALK-FORWARD
============================================================

主要功能：

1. 香港彩 / 新澳门彩 / 老澳门彩
2. API 自动更新
3. SQLite 历史数据
4. 特别号码预测
5. Top5 / Top10 / Top12
6. 多窗口：
   - 最近10期
   - 最近30期
   - 最近100期
7. 遗漏值评分
8. 近期趋势评分
9. 号码综合评分
10. 生肖 Top5
11. 单双主推
12. 大小主推
13. 波色主推 / 次推 / 双色
14. 属性历史频率
15. Walk-Forward
16. 最近10 / 30 / 50 / 100期表现
17. 综合模型评分
18. JSON 输出
19. 与旧版接口兼容
20. 提供 run_system() 给 main.py 调用
21. 平特一肖

重要说明：

本系统用于历史统计、模型实验和 Walk-Forward 回测。
六合彩开奖属于随机事件，历史统计不能保证未来结果。
模型分数不是实际中奖概率。
============================================================
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from collections import Counter
from typing import Any


# ============================================================
# 项目模块
# ============================================================

from .api_sync import (
    fetch_lottery,
)

from .database import (
    init_db,
    save_records,
    load_records,
    count_records,
)


# ============================================================
# 彩种
# ============================================================

LOTTERIES = [
    "新澳门彩",
    "老澳门彩",
    "香港彩",
]


# ============================================================
# 输出目录
# ============================================================

OUTPUT_DIR = "output"


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
# 参数
# ============================================================

WINDOW_10 = 10
WINDOW_30 = 30
WINDOW_100 = 100

MISSING_CAP = 40

# 多窗口权重
WEIGHT_10 = 2.50
WEIGHT_30 = 1.30
WEIGHT_100 = 0.80

# 遗漏权重
WEIGHT_MISSING = 0.15

# 趋势权重
WEIGHT_TREND = 0.80


# ============================================================
# 创建目录
# ============================================================

def ensure_dirs() -> None:

    os.makedirs(
        "data",
        exist_ok=True,
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )


# ============================================================
# issue排序
# ============================================================

def issue_value(
    row: dict[str, Any],
) -> int:

    try:

        return int(
            str(
                row.get(
                    "issue",
                    "0",
                )
            )
        )

    except Exception:

        return 0


# ============================================================
# 下一期
# ============================================================

def next_issue(
    issue: str,
) -> str:

    try:

        return str(
            int(issue) + 1
        )

    except Exception:

        return ""


# ============================================================
# 波色
# ============================================================

def get_wave(
    number: int,
) -> str:

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

def get_size(
    number: int,
) -> str:

    number = int(number)

    return "大" if number >= 25 else "小"


# ============================================================
# 单双
# ============================================================

def get_odd_even(
    number: int,
) -> str:

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
# 特别号码历史
# ============================================================

def special_history(
    history: list[dict[str, Any]],
    window: int | None = None,
) -> list[int]:

    rows = (
        history[-window:]
        if window
        else history
    )

    result = []

    for row in rows:

        special = get_special_number(
            row
        )

        if special is not None:

            result.append(
                special
            )

    return result


# ============================================================
# 遗漏统计
# ============================================================

def missing_periods_all(
    history: list[dict[str, Any]],
) -> dict[int, int]:

    """
    计算1~49每个号码距离上一次作为特别号码
    出现的期数。

    只扫描一次历史。
    """

    result: dict[int, int] = {}

    found: set[int] = set()

    count = 0

    for row in reversed(history):

        if len(found) >= 49:

            break

        special = get_special_number(
            row
        )

        if (
            special is not None
            and special not in found
        ):

            result[special] = count

            found.add(
                special
            )

        count += 1

    for number in range(
        1,
        50,
    ):

        if number not in result:

            result[number] = min(
                count,
                MISSING_CAP,
            )

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

        diff = round(
            100 - sum(
                result.values()
            ),
            2,
        )

        result[
            categories[0]
        ] = round(
            result[
                categories[0]
            ] + diff,
            2,
        )

        return result

    return {
        item: round(
            counter.get(
                item,
                0,
            ) / total * 100,
            2,
        )
        for item in categories
    }


# ============================================================
# 属性预测
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
            -probability.get(
                x,
                0,
            ),
            -counter.get(
                x,
                0,
            ),
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
# 单属性预测
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
            -probability.get(
                x,
                0,
            ),
            -counter.get(
                x,
                0,
            ),
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
# 兼容旧接口
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

        return result

    result = predict_single_attribute(
        history,
        field,
        limit,
    )

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
# V7.5
# 号码趋势评分
# ============================================================

def trend_score(
    number: int,
    history: list[dict[str, Any]],
) -> float:

    """
    比较最近10期和最近30期的特别号码活跃程度。

    如果最近10期明显高于30期平均水平，
    趋势分增加。

    注意：
    只是统计评分，不代表未来概率。
    """

    recent10 = Counter(
        special_history(
            history,
            10,
        )
    )

    recent30 = Counter(
        special_history(
            history,
            30,
        )
    )

    n10 = recent10.get(
        number,
        0,
    )

    n30 = recent30.get(
        number,
        0,
    )

    if n30 <= 0:

        if n10 > 0:

            return round(
                n10 * WEIGHT_TREND,
                4,
            )

        return 0.0

    expected10 = (
        n30 / 30 * 10
    )

    trend = (
        n10 - expected10
    )

    return round(
        trend * WEIGHT_TREND,
        4,
    )


# ============================================================
# V7.5
# 号码综合评分
# ============================================================

def predict_numbers(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    """
    V7.5号码模型：

    10期频率
    + 30期频率
    + 100期频率
    + 遗漏
    + 趋势

    最终只针对特别号码。
    """

    if not history:

        return {

            "top5": [],
            "top10": [],
            "top12": [],
            "scores": {},
            "details": {},
            "frequency": {},
        }

    recent10 = Counter(
        special_history(
            history,
            WINDOW_10,
        )
    )

    recent30 = Counter(
        special_history(
            history,
            WINDOW_30,
        )
    )

    recent100 = Counter(
        special_history(
            history,
            WINDOW_100,
        )
    )

    missing_map = missing_periods_all(
        history
    )

    scores: dict[int, float] = {}

    details: dict[int, dict[str, float]] = {}

    for number in range(
        1,
        50,
    ):

        score10 = (
            recent10.get(
                number,
                0,
            )
            * WEIGHT_10
        )

        score30 = (
            recent30.get(
                number,
                0,
            )
            * WEIGHT_30
        )

        score100 = (
            recent100.get(
                number,
                0,
            )
            * WEIGHT_100
        )

        missing = min(
            missing_map.get(
                number,
                MISSING_CAP,
            ),
            MISSING_CAP,
        )

        missing_score = (
            missing
            * WEIGHT_MISSING
        )

        trend = trend_score(
            number,
            history,
        )

        total_score = (
            score10
            + score30
            + score100
            + missing_score
            + trend
        )

        scores[number] = round(
            total_score,
            4,
        )

        details[number] = {

            "window10":
                round(
                    score10,
                    4,
                ),

            "window30":
                round(
                    score30,
                    4,
                ),

            "window100":
                round(
                    score100,
                    4,
                ),

            "missing":
                round(
                    missing_score,
                    4,
                ),

            "trend":
                round(
                    trend,
                    4,
                ),

            "total":
                round(
                    total_score,
                    4,
                ),

        }

    ranking = sorted(
        range(
            1,
            50,
        ),
        key=lambda x: (
            -scores[x],
            x,
        ),
    )

    return {

        "top5":
            ranking[:5],

        "top10":
            ranking[:10],

        "top12":
            ranking[:12],

        "scores":
            scores,

        "details":
            details,

        "frequency":
            dict(
                recent100
            ),

        "windows": {

            "10":
                dict(
                    recent10
                ),

            "30":
                dict(
                    recent30
                ),

            "100":
                dict(
                    recent100
                ),

        },

        "missing":
            missing_map,

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
        hits / total * 100,
        2,
    )


# ============================================================
# 平均命中数
# ============================================================

def average_hits(
    evaluations: list[dict[str, Any]],
    key: str,
) -> float:

    if not evaluations:

        return 0.0

    hits = sum(
        1
        for item in evaluations
        if item.get(key)
    )

    return round(
        hits / len(
            evaluations
        ),
        4,
    )


# ============================================================
# 性能计算
# ============================================================

def _performance_window(
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

    return {

        "samples":
            total,

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
                average_hits(
                    evaluations,
                    "number_top5",
                ),

            "average_top10_hits":
                average_hits(
                    evaluations,
                    "number_top10",
                ),

            "average_top12_hits":
                average_hits(
                    evaluations,
                    "number_top12",
                ),

        },

        "zodiac": {

            "main":
                hit_rate(
                    count(
                        "zodiac_main"
                    ),
                    total,
                ),

            "top5":
                hit_rate(
                    count(
                        "zodiac_top5"
                    ),
                    total,
                ),

        },

        "odd_even": {

            "main":
                hit_rate(
                    count(
                        "odd_even_main"
                    ),
                    total,
                ),

        },

        "size": {

            "main":
                hit_rate(
                    count(
                        "size_main"
                    ),
                    total,
                ),

        },

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
# 最近窗口性能
# ============================================================

def calculate_performance(
    evaluations: list[dict[str, Any]],
    recent_n: int = 10,
) -> dict[str, Any]:

    if not evaluations:

        return {

            "samples": 0,

            "backtest_window":
                recent_n,

            "status":
                "历史数据不足",

        }

    evaluations = evaluations[
        -recent_n:
    ]

    result = _performance_window(
        evaluations
    )

    result[
        "backtest_window"
    ] = recent_n

    return result


# ============================================================
# 多窗口性能
# ============================================================

def calculate_multi_performance(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:

    if not evaluations:

        return {

            "status":
                "历史数据不足",

            "windows": {},

        }

    result = {}

    for window in (
        10,
        30,
        50,
        100,
    ):

        subset = evaluations[
            -window:
        ]

        data = _performance_window(
            subset
        )

        data[
            "backtest_window"
        ] = min(
            window,
            len(evaluations),
        )

        result[
            str(window)
        ] = data

    return {

        "status":
            "正常",

        "total_samples":
            len(evaluations),

        "windows":
            result,

    }


# ============================================================
# Walk-Forward
# ============================================================

def walk_forward(
    history: list[dict[str, Any]],
    minimum_train: int = 30,
) -> dict[str, Any]:

    history = sorted(
        history,
        key=issue_value,
    )

    evaluations = []

    if len(history) <= minimum_train:

        return {

            "method":
                "Walk-Forward",

            "minimum_train":
                minimum_train,

            "samples":
                0,

            "status":
                "历史数据不足",

            "performance":
                {
                    "samples": 0,
                    "status":
                        "历史数据不足",
                },

            "multi_performance":
                {
                    "status":
                        "历史数据不足",
                    "windows": {},
                },

        }

    # ========================================================
    # 滚动预测
    # ========================================================

    for index in range(
        minimum_train,
        len(history),
    ):

        train = history[
            :index
        ]

        actual = history[
            index
        ]

        number_prediction = predict_numbers(
            train
        )

        attributes = predict_attributes(
            train
        )

        prediction = {

            "candidates":
                number_prediction[
                    "top12"
                ],

            "top5":
                number_prediction[
                    "top5"
                ],

            "top10":
                number_prediction[
                    "top10"
                ],

            "top12":
                number_prediction[
                    "top12"
                ],

            "attributes":
                attributes,

        }

        evaluation = evaluate_prediction(
            prediction,
            actual,
            train,
        )

        if evaluation:

            evaluations.append(
                evaluation
            )

    performance = calculate_performance(
        evaluations,
        10,
    )

    multi_performance = calculate_multi_performance(
        evaluations
    )

    return {

        "method":
            "Walk-Forward",

        "minimum_train":
            minimum_train,

        "samples":
            len(evaluations),

        "performance":
            performance,

        "multi_performance":
            multi_performance,

        "status":
            "正常",

    }


# ============================================================
# 模型稳定性评分
# ============================================================

def calculate_model_stability(
    multi_performance: dict[str, Any],
) -> dict[str, Any]:

    windows = multi_performance.get(
        "windows",
        {},
    )

    if not windows:

        return {

            "score":
                0,

            "level":
                "数据不足",

        }

    values = []

    for window_data in windows.values():

        numbers = window_data.get(
            "numbers",
            {},
        )

        value = numbers.get(
            "top10",
            0,
        )

        values.append(
            float(value)
        )

    if not values:

        return {

            "score":
                0,

            "level":
                "数据不足",

        }

    mean_value = (
        sum(values)
        / len(values)
    )

    if len(values) > 1:

        spread = (
            max(values)
            - min(values)
        )

    else:

        spread = 0

    # 稳定性不是命中率。
    # 这里只用于观察不同窗口是否严重漂移。
    stability = max(
        0.0,
        100.0 - spread * 2.0,
    )

    return {

        "mean_top10":
            round(
                mean_value,
                2,
            ),

        "spread":
            round(
                spread,
                2,
            ),

        "score":
            round(
                stability,
                2,
            ),

        "level":
            (
                "稳定"
                if stability >= 75
                else
                "一般"
                if stability >= 50
                else
                "波动较大"
            ),

    }


# ============================================================
# 分析一个彩种
# ============================================================

def analyze(
    lottery_name: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    history = sorted(
        history,
        key=issue_value,
    )

    latest = (
        history[-1]
        if history
        else {}
    )

    latest_issue = str(
        latest.get(
            "issue",
            "",
        )
    )

    latest_numbers = latest.get(
        "numbers",
        [],
    )

    prediction_issue = (
        next_issue(
            latest_issue
        )
        if latest_issue
        else ""
    )

    number_prediction = predict_numbers(
        history
    )

    attributes = predict_attributes(
        history
    )

    walk = walk_forward(
        history
    )

    performance = walk.get(
        "performance",
        {},
    )

    multi_performance = walk.get(
        "multi_performance",
        {},
    )

    stability = calculate_model_stability(
        multi_performance
    )

    return {

        "lottery":
            lottery_name,

        "version":
            "V7.5",

        "latest_issue":
            latest_issue,

        "latest_draw_issue":
            latest_issue,

        "prediction_issue":
            prediction_issue,

        "next_prediction_issue":
            prediction_issue,

        "latest_numbers":
            latest_numbers,

        "history_size":
            len(history),

        "candidates":
            number_prediction[
                "top12"
            ],

        "top5":
            number_prediction[
                "top5"
            ],

        "top10":
            number_prediction[
                "top10"
            ],

        "top12":
            number_prediction[
                "top12"
            ],

        "number_scores":
            number_prediction[
                "scores"
            ],

        "number_details":
            number_prediction[
                "details"
            ],

        "frequency":
            number_prediction[
                "frequency"
            ],

        "windows":
            number_prediction[
                "windows"
            ],

        "missing":
            number_prediction[
                "missing"
            ],

        "attributes":
            attributes,

        "pingte_zodiac": {
            "recommend":
                attributes.get(
                    "zodiac", {}
                ).get(
                    "main", ""
                ),
            "hit_rate":
                performance.get(
                    "zodiac", {}
                ).get(
                    "main", 0
                ),
            "samples":
                performance.get(
                    "samples", 0
                ),
        },

        "performance":
            performance,

        "multi_performance":
            multi_performance,

        "model_stability":
            stability,

        "backtest":
            walk,

        "success":
            bool(history),

    }


# ============================================================
# 格式化号码
# ============================================================

def format_numbers(
    numbers: list[int],
) -> str:

    if not numbers:

        return ""

    return " ".join(
        f"{int(x):02d}"
        for x in numbers
    )


# ============================================================
# 打印属性概率
# ============================================================

def print_probability(
    name: str,
    probability: dict[str, float],
) -> None:

    if not probability:

        return

    text = " ".join(
        f"{key}:{value:.2f}%"
        for key, value
        in probability.items()
    )

    print(
        f"{name}概率：{text}"
    )


# ============================================================
# 打印结果
# ============================================================

def print_result(
    result: dict[str, Any],
) -> None:

    print(
        "=" * 70
    )

    print(
        f"【{result.get('lottery', '')}】"
    )

    print(
        "=" * 70
    )

    print(
        f"历史期数："
        f"{result.get('history_size', 0)}"
    )

    print(
        f"最新开奖期数："
        f"{result.get('latest_issue', '')}"
    )

    print(
        f"预测下一期期数："
        f"{result.get('prediction_issue', '')}"
    )

    print(
        "最新号码："
        + format_numbers(
            result.get(
                "latest_numbers",
                [],
            )
        )
    )

    print()

    # ========================================================
    # 号码
    # ========================================================

    print(
        "【V7.5 号码预测】"
    )

    print(
        "Top5："
        + format_numbers(
            result.get(
                "top5",
                [],
            )
        )
    )

    print(
        "Top10："
        + format_numbers(
            result.get(
                "top10",
                [],
            )
        )
    )

    print(
        "Top12："
        + format_numbers(
            result.get(
                "top12",
                [],
            )
        )
    )

    print()

    # ========================================================
    # 分数
    # ========================================================

    scores = result.get(
        "number_scores",
        {},
    )

    if scores:

        ranking = sorted(
            scores,
            key=lambda x: (
                -scores[x],
                x,
            ),
        )

        print(
            "【号码综合评分 Top12】"
        )

        for number in ranking[:12]:

            print(
                f"{int(number):02d}"
                f" = "
                f"{scores[number]:.4f}"
            )

        print()

    # ========================================================
    # 属性
    # ========================================================

    attrs = result.get(
        "attributes",
        {},
    )

    print(
        "【下一期属性预测】"
    )

    zodiac = attrs.get(
        "zodiac",
        {},
    )

    print(
        "生肖："
        f"主推 {zodiac.get('main', '')} "
        f"次推 {zodiac.get('secondary', '')} "
        f"Top5 "
        f"{' + '.join(zodiac.get('top5', []))}"
    )

    print_probability(
        "生肖",
        zodiac.get(
            "probability",
            {},
        ),
    )

    odd_even = attrs.get(
        "odd_even",
        {},
    )

    print(
        "单双："
        f"主推 {odd_even.get('main', '')}"
    )

    print_probability(
        "单双",
        odd_even.get(
            "probability",
            {},
        ),
    )

    size = attrs.get(
        "size",
        {},
    )

    print(
        "大小："
        f"主推 {size.get('main', '')}"
    )

    print_probability(
        "大小",
        size.get(
            "probability",
            {},
        ),
    )

    wave = attrs.get(
        "wave",
        {},
    )

    print(
        "波色："
        f"主推 {wave.get('main', '')} "
        f"次推 {wave.get('secondary', '')} "
        f"双色 "
        f"{' + '.join(wave.get('double', []))}"
    )

    print_probability(
        "波色",
        wave.get(
            "probability",
            {},
        ),
    )

    print()

    # ========================================================
    # 平特一肖
    # ========================================================

    pingte = result.get(
        "pingte_zodiac",
        {},
    )

    print(
        "【平特一肖】"
    )

    print(
        f"推荐："
        f"{pingte.get('recommend', '')}"
    )

    if pingte.get("samples", 0) > 0:

        print(
            f"历史命中率："
            f"{pingte.get('hit_rate', 0)}% "
            f"（验证{pingte.get('samples', 0)}期，"
            f"随机基准约8.33%）"
        )

    else:

        print(
            "历史数据不足，暂无命中率统计"
        )

    print()

    # ========================================================
    # 最近10期
    # ========================================================

    performance = result.get(
        "performance",
        {},
    )

    if performance.get(
        "status"
    ) == "正常":

        print(
            "【Walk-Forward 最近10期】"
        )

        print(
            f"验证期数："
            f"{performance.get('samples', 0)}"
        )

        numbers = performance.get(
            "numbers",
            {},
        )

        print(
            f"Top5："
            f"{numbers.get('top5', 0)}%"
            f" | Top10："
            f"{numbers.get('top10', 0)}%"
            f" | Top12："
            f"{numbers.get('top12', 0)}%"
        )

        print(
            f"Top5平均命中："
            f"{numbers.get('average_top5_hits', 0)}"
            f" | Top10平均命中："
            f"{numbers.get('average_top10_hits', 0)}"
            f" | Top12平均命中："
            f"{numbers.get('average_top12_hits', 0)}"
        )

        zodiac_perf = performance.get(
            "zodiac",
            {},
        )

        print(
            f"生肖主推："
            f"{zodiac_perf.get('main', 0)}%"
            f" | 生肖Top5："
            f"{zodiac_perf.get('top5', 0)}%"
        )

        print(
            f"单双主推："
            f"{performance.get('odd_even', {}).get('main', 0)}%"
            f" | 大小主推："
            f"{performance.get('size', {}).get('main', 0)}%"
        )

        wave_perf = performance.get(
            "wave",
            {},
        )

        print(
            f"波色主推："
            f"{wave_perf.get('main', 0)}%"
            f" | 次推："
            f"{wave_perf.get('secondary', 0)}%"
            f" | 双色："
            f"{wave_perf.get('double', 0)}%"
        )

    else:

        print(
            "【Walk-Forward】"
        )

        print(
            "历史数据不足"
        )

    print()

    # ========================================================
    # 多窗口表现
    # ========================================================

    multi = result.get(
        "multi_performance",
        {},
    )

    windows = multi.get(
        "windows",
        {},
    )

    if windows:

        print(
            "【多窗口 Walk-Forward】"
        )

        for window in (
            "10",
            "30",
            "50",
            "100",
        ):

            item = windows.get(
                window
            )

            if not item:

                continue

            nums = item.get(
                "numbers",
                {},
            )

            print(
                f"{window}期："
                f"Top5 "
                f"{nums.get('top5', 0)}% | "
                f"Top10 "
                f"{nums.get('top10', 0)}% | "
                f"Top12 "
                f"{nums.get('top12', 0)}%"
            )

        print()

    # ========================================================
    # 稳定性
    # ========================================================

    stability = result.get(
        "model_stability",
        {},
    )

    if stability:

        print(
            "【模型稳定性】"
        )

        print(
            f"Top10多窗口平均："
            f"{stability.get('mean_top10', 0)}%"
        )

        print(
            f"窗口差异："
            f"{stability.get('spread', 0)}%"
        )

        print(
            f"稳定性评分："
            f"{stability.get('score', 0)}/100"
        )

        print(
            f"状态："
            f"{stability.get('level', '')}"
        )

    print()


# ============================================================
# 保存JSON
# ============================================================

def save_json(
    filename: str,
    data: dict[str, Any],
) -> str:

    path = os.path.join(
        OUTPUT_DIR,
        filename,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return path


# ============================================================
# 生成简版预测
# ============================================================

def build_summary(
    all_results: dict[str, Any],
) -> dict[str, Any]:

    summary = {}

    for name, result in all_results.items():

        if not result.get(
            "success"
        ):

            summary[name] = {

                "success":
                    False,

                "error":
                    result.get(
                        "error",
                        "",
                    ),

            }

            continue

        attrs = result.get(
            "attributes",
            {},
        )

        summary[name] = {

            "success":
                True,

            "latest_issue":
                result.get(
                    "latest_issue",
                    "",
                ),

            "prediction_issue":
                result.get(
                    "prediction_issue",
                    "",
                ),

            "top5":
                result.get(
                    "top5",
                    [],
                ),

            "top10":
                result.get(
                    "top10",
                    [],
                ),

            "top12":
                result.get(
                    "top12",
                    [],
                ),

            "zodiac":
                attrs.get(
                    "zodiac",
                    {},
                ),

            "odd_even":
                attrs.get(
                    "odd_even",
                    {},
                ),

            "size":
                attrs.get(
                    "size",
                    {},
                ),

            "wave":
                attrs.get(
                    "wave",
                    {},
                ),

            "pingte_zodiac":
                result.get(
                    "pingte_zodiac",
                    {},
                ),

            "model_stability":
                result.get(
                    "model_stability",
                    {},
                ),

        }

    return summary


# ============================================================
# 主系统
# ============================================================

def run_system() -> None:

    """
    main.py 调用的核心入口。

    例如：

        from core.engine import run_system

        run_system()
    """

    ensure_dirs()

    print(
        "=" * 70
    )

    print(
        "开始运行六合彩综合预测系统 V7.5"
    )

    print(
        f"启动时间："
        f"{datetime.now().isoformat()}"
    )

    print(
        "=" * 70
    )

    # ========================================================
    # SQLite初始化
    # ========================================================

    try:

        init_db()

        print(
            "[OK] SQLite 初始化完成"
        )

    except Exception as exc:

        print(
            "[ERROR] SQLite 初始化失败："
            f"{exc}"
        )

        raise

    all_results: dict[str, Any] = {}

    # ========================================================
    # 三彩种
    # ========================================================

    for lottery in LOTTERIES:

        print()
        print(
            "=" * 70
        )

        print(
            f"正在更新：{lottery}"
        )

        print(
            "=" * 70
        )

        try:

            # =================================================
            # API
            # =================================================

            records = fetch_lottery(
                lottery
            )

            if records is None:

                records = []

            print(
                f"[{lottery}] "
                f"API返回："
                f"{len(records)} 期"
            )

            # =================================================
            # SQLite
            # =================================================

            added = save_records(
                lottery,
                records,
            )

            print(
                f"[{lottery}] "
                f"本次新增："
                f"{added} 期"
            )

            # =================================================
            # 重新读取数据库
            # =================================================

            history = load_records(
                lottery
            )

            total = count_records(
                lottery
            )

            print(
                f"[{lottery}] "
                f"当前数据库："
                f"{total} 期"
            )

            # =================================================
            # 分析
            # =================================================

            result = analyze(
                lottery,
                history,
            )

            print_result(
                result
            )

            all_results[
                lottery
            ] = result

        except Exception as exc:

            print(
                f"[ERROR] "
                f"{lottery}: "
                f"{exc}"
            )

            all_results[
                lottery
            ] = {

                "lottery":
                    lottery,

                "version":
                    "V7.5",

                "success":
                    False,

                "error":
                    str(exc),

            }

    # ========================================================
    # 总预测文件
    # ========================================================

    prediction = {

        "version":
            "V7.5",

        "generated_at":
            datetime.now().isoformat(),

        "model":
            {

                "type":
                    "Multi-Window + Missing + Trend",

                "target":
                    "特别号码",

                "windows":
                    [
                        10,
                        30,
                        100,
                    ],

                "weights":
                    {

                        "window10":
                            WEIGHT_10,

                        "window30":
                            WEIGHT_30,

                        "window100":
                            WEIGHT_100,

                        "missing":
                            WEIGHT_MISSING,

                        "trend":
                            WEIGHT_TREND,

                    },

            },

        "note":
            "历史统计和Walk-Forward模型实验，不代表未来实际中奖概率。",

        "lotteries":
            all_results,

    }

    prediction_path = save_json(
        "prediction.json",
        prediction,
    )

    # ========================================================
    # 回测
    # ========================================================

    backtest = {

        "version":
            "V7.5",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries": {

            name:
                result.get(
                    "backtest",
                    {},
                )

            for name, result
            in all_results.items()

        },

    }

    backtest_path = save_json(
        "backtest.json",
        backtest,
    )

    # ========================================================
    # 模块表现
    # ========================================================

    module_performance = {

        "version":
            "V7.5",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries": {

            name:
                {

                    "performance":
                        result.get(
                            "performance",
                            {},
                        ),

                    "multi_performance":
                        result.get(
                            "multi_performance",
                            {},
                        ),

                    "model_stability":
                        result.get(
                            "model_stability",
                            {},
                        ),

                }

            for name, result
            in all_results.items()

        },

    }

    performance_path = save_json(
        "module_performance.json",
        module_performance,
    )

    # ========================================================
    # 简版结果
    # ========================================================

    summary = {

        "version":
            "V7.5",

        "generated_at":
            datetime.now().isoformat(),

        "summary":
            build_summary(
                all_results
            ),

    }

    summary_path = save_json(
        "summary.json",
        summary,
    )

    # ========================================================
    # 最终输出
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "预测结果已保存："
        f"{prediction_path}"
    )

    print(
        "回测结果已保存："
        f"{backtest_path}"
    )

    print(
        "模块表现已保存："
        f"{performance_path}"
    )

    print(
        "简版预测已保存："
        f"{summary_path}"
    )

    print(
        "=" * 70
    )

    print(
        "【三彩种最终预测】"
    )

    print(
        "=" * 70
    )

    for name, result in (
        all_results.items()
    ):

        if not result.get(
            "success"
        ):

            print(
                f"{name}：运行失败"
                f" → "
                f"{result.get('error', '')}"
            )

            continue

        print()

        print(
            f"{name}"
        )

        print(
            f"最新："
            f"{result.get('latest_issue', '')}"
        )

        print(
            f"下一期："
            f"{result.get('prediction_issue', '')}"
        )

        print(
            f"Top5："
            f"{format_numbers(result.get('top5', []))}"
        )

        print(
            f"Top10："
            f"{format_numbers(result.get('top10', []))}"
        )

        print(
            f"Top12："
            f"{format_numbers(result.get('top12', []))}"
        )

        attrs = result.get(
            "attributes",
            {},
        )

        zodiac = attrs.get(
            "zodiac",
            {},
        )

        odd_even = attrs.get(
            "odd_even",
            {},
        )

        size = attrs.get(
            "size",
            {},
        )

        wave = attrs.get(
            "wave",
            {},
        )

        print(
            f"生肖："
            f"{' / '.join(zodiac.get('top5', []))}"
        )

        print(
            f"单双主推："
            f"{odd_even.get('main', '')}"
        )

        print(
            f"大小主推："
            f"{size.get('main', '')}"
        )

        print(
            f"波色："
            f"{wave.get('main', '')}"
            f" / "
            f"{wave.get('secondary', '')}"
            f" / "
            f"{' + '.join(wave.get('double', []))}"
        )

        pingte = result.get(
            "pingte_zodiac",
            {},
        )

        if pingte.get("recommend"):

            print(
                f"平特一肖："
                f"{pingte.get('recommend', '')}"
                f"（历史命中率 "
                f"{pingte.get('hit_rate', 0)}%）"
            )

        stability = result.get(
            "model_stability",
            {},
        )

        print(
            f"模型稳定性："
            f"{stability.get('score', 0)}/100"
            f" "
            f"{stability.get('level', '')}"
        )

        performance = result.get(
            "performance",
            {},
        )

        if performance.get(
            "status"
        ) == "正常":

            numbers = performance.get(
                "numbers",
                {},
            )

            print(
                f"最近10期："
                f"Top5 "
                f"{numbers.get('top5', 0)}% / "
                f"Top10 "
                f"{numbers.get('top10', 0)}% / "
                f"Top12 "
                f"{numbers.get('top12', 0)}%"
            )

        print()

    print(
        "=" * 70
    )

    print(
        "说明："
        "模型输出来自历史数据统计与Walk-Forward验证，"
        "不等于未来实际中奖概率。"
    )

    print(
        "=" * 70
    )

    print(
        "系统运行结束"
    )

    print(
        "=" * 70
    )


# ============================================================
# 直接执行
# ============================================================

if __name__ == "__main__":

    run_system()