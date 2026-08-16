# -*- coding: utf-8 -*-

"""
六合彩回测模块 V1.2

功能：

1. 第一推荐命中率
2. TOP3 命中率
3. TOP5 命中率
4. TOP10 命中率
5. 生肖5肖
6. 平特2肖
7. 大小
8. 单双
9. 波色

窗口：

10 / 20 / 30 / 60 / 100期

严格 Walk-Forward：

预测某一期时，
绝不使用该期及之后的数据。
"""

from .features import (
    get_special,
    get_wave,
)

from .predictor import (
    generate_prediction,
    NUMBER_TO_ZODIAC,
)


# =========================================================
# 获取实际结果
# =========================================================

def get_actual_result(row):

    number = get_special(row)

    if not 1 <= number <= 49:

        raise ValueError(
            f"无法获取有效特码：{number}"
        )

    return {

        "number":
            number,

        "zodiac":
            NUMBER_TO_ZODIAC.get(
                number
            ),

        "size":
            "大"
            if number >= 25
            else "小",

        "parity":
            "单"
            if number % 2
            else "双",

        "wave":
            get_wave(number),
    }


# =========================================================
# 单期比较
# =========================================================

def test_one_prediction(
    prediction,
    actual
):

    recommendation = (
        prediction
        .get("recommendation", {})
    )

    first = recommendation.get(
        "first"
    )

    first_number = (
        first["number"]
        if first
        else None
    )

    top3 = [

        item["number"]

        for item in prediction.get(
            "top3_numbers",
            []
        )
    ]

    top5 = [

        item["number"]

        for item in prediction.get(
            "top5_numbers",
            []
        )
    ]

    top10 = [

        item["number"]

        for item in prediction.get(
            "top10_numbers",
            []
        )
    ]

    top5_zodiac = [

        item["zodiac"]

        for item in prediction.get(
            "top5_zodiac",
            []
        )
    ]

    top2_pingte = [

        item["zodiac"]

        for item in prediction.get(
            "top2_pingte_zodiac",
            []
        )
    ]

    predicted_size = (
        prediction
        .get("size", {})
        .get("prediction")
    )

    predicted_parity = (
        prediction
        .get("parity", {})
        .get("prediction")
    )

    predicted_wave = (
        prediction
        .get("wave", {})
        .get("prediction")
    )

    return {

        "first_hit":
            actual["number"]
            == first_number,

        "top3_hit":
            actual["number"]
            in top3,

        "top5_hit":
            actual["number"]
            in top5,

        "top10_hit":
            actual["number"]
            in top10,

        "zodiac_hit":
            actual["zodiac"]
            in top5_zodiac,

        "pingte_hit":
            actual["zodiac"]
            in top2_pingte,

        "size_hit":
            predicted_size
            == actual["size"],

        "parity_hit":
            predicted_parity
            == actual["parity"],

        "wave_hit":
            predicted_wave
            == actual["wave"],
    }


# =========================================================
# Walk-Forward 回测
# =========================================================

def backtest(
    rows,
    max_tests=100
):

    rows = list(rows)

    if len(rows) < 60:

        return {

            "tests": 0,

            "error":
                "历史数据不足60期",
        }

    # -----------------------------------------------------
    # 最新 -> 最旧
    # 转成：
    # 最旧 -> 最新
    # -----------------------------------------------------

    chronological = list(
        reversed(rows)
    )

    total_available = len(
        chronological
    )

    test_count = min(
        max_tests,
        total_available - 50
    )

    if test_count <= 0:

        return {

            "tests": 0,

            "error":
                "没有足够的数据进行回测",
        }

    start_index = (
        total_available
        - test_count
    )

    stats = {

        "first_hits": 0,

        "top3_hits": 0,

        "top5_hits": 0,

        "top10_hits": 0,

        "zodiac_hits": 0,

        "pingte_hits": 0,

        "size_hits": 0,

        "parity_hits": 0,

        "wave_hits": 0,
    }

    details = []

    for i in range(
        start_index,
        total_available
    ):

        if i < 50:
            continue

        train_rows = chronological[:i]

        target_row = chronological[i]

        try:

            prediction = generate_prediction(
                train_rows
            )

            actual = get_actual_result(
                target_row
            )

            result = test_one_prediction(
                prediction,
                actual
            )

        except Exception as e:

            print(
                f"回测错误：{e}"
            )

            continue

        for key, stat_key in [

            ("first_hit", "first_hits"),

            ("top3_hit", "top3_hits"),

            ("top5_hit", "top5_hits"),

            ("top10_hit", "top10_hits"),

            ("zodiac_hit", "zodiac_hits"),

            ("pingte_hit", "pingte_hits"),

            ("size_hit", "size_hits"),

            ("parity_hit", "parity_hits"),

            ("wave_hit", "wave_hits"),

        ]:

            if result[key]:

                stats[stat_key] += 1

        details.append({

            "issue":
                target_row.get(
                    "issue"
                ),

            "actual_number":
                actual["number"],

            "actual_zodiac":
                actual["zodiac"],

            "actual_size":
                actual["size"],

            "actual_parity":
                actual["parity"],

            "actual_wave":
                actual["wave"],

            **result,
        })

    total = len(details)

    if total == 0:

        return {

            "tests": 0,

            "error":
                "没有成功完成回测",
        }

    def rate(key):

        return round(
            stats[key] / total,
            6
        )

    return {

        "tests":
            total,

        "first_hit_rate":
            rate("first_hits"),

        "top3_hit_rate":
            rate("top3_hits"),

        "top5_hit_rate":
            rate("top5_hits"),

        "top10_hit_rate":
            rate("top10_hits"),

        "zodiac_top5_hit_rate":
            rate("zodiac_hits"),

        "pingte_top2_hit_rate":
            rate("pingte_hits"),

        "size_hit_rate":
            rate("size_hits"),

        "parity_hit_rate":
            rate("parity_hits"),

        "wave_hit_rate":
            rate("wave_hits"),

        "details":
            details[-100:],
    }


# =========================================================
# 多窗口
# =========================================================

def multi_window_backtest(rows):

    results = {}

    windows = [
        10,
        20,
        30,
        60,
        100,
    ]

    total = len(rows)

    for window in windows:

        required = (
            window + 50
        )

        if total < required:

            results[str(window)] = {

                "window":
                    window,

                "tests":
                    0,

                "error":
                    (
                        f"数据不足，需要至少"
                        f"{required}期，"
                        f"当前只有{total}期"
                    ),
            }

            continue

        subset = rows[
            :required
        ]

        result = backtest(
            subset,
            max_tests=window
        )

        result["window"] = window

        results[str(window)] = result

    return results
