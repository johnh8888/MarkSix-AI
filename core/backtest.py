# -*- coding: utf-8 -*-

from collections import defaultdict

from .predictor import (
    generate_prediction,
    NUMBER_TO_ZODIAC,
)


def get_actual_result(row):

    number = int(row["special"])

    zodiac = NUMBER_TO_ZODIAC.get(
        number
    )

    if number >= 25:
        size = "大"
    else:
        size = "小"

    if number % 2:
        parity = "单"
    else:
        parity = "双"

    return {
        "number": number,
        "zodiac": zodiac,
        "size": size,
        "parity": parity,
    }


def test_one_prediction(
    prediction,
    actual
):

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

    result = {

        "number_hit": (
            actual["number"]
            in top10
        ),

        "zodiac_hit": (
            actual["zodiac"]
            in top5_zodiac
        ),

        "pingte_zodiac_hit": (
            actual["zodiac"]
            in top2_pingte
        ),

        "size_hit": (
            prediction["size"]["prediction"]
            == actual["size"]
        ),

        "parity_hit": (
            prediction["parity"]["prediction"]
            == actual["parity"]
        ),
    }

    return result


def backtest(
    rows,
    max_tests=1000
):

    # 数据按照最新在前
    # 回测时反过来
    rows = list(rows)

    if len(rows) < 100:

        return {
            "error": "历史数据不足100期"
        }

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

    start_index = (
        total_available
        - test_count
    )

    stats = {

        "tests": 0,

        "number_hits": 0,

        "zodiac_hits": 0,

        "pingte_zodiac_hits": 0,

        "size_hits": 0,

        "parity_hits": 0,
    }

    details = []

    for i in range(
        start_index,
        total_available
    ):

        # 至少需要一些训练数据
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
                "回测错误:",
                e
            )

            continue

        stats["tests"] += 1

        if result["number_hit"]:
            stats["number_hits"] += 1

        if result["zodiac_hit"]:
            stats["zodiac_hits"] += 1

        if result["pingte_zodiac_hit"]:
            stats["pingte_zodiac_hits"] += 1

        if result["size_hit"]:
            stats["size_hits"] += 1

        if result["parity_hit"]:
            stats["parity_hits"] += 1

        details.append({

            "issue": target_row["issue"],

            "actual_number":
                actual["number"],

            **result
        })

    total = max(
        stats["tests"],
        1
    )

    return {

        "tests":
            stats["tests"],

        "number_top10_hit_rate":
            round(
                stats["number_hits"]
                / total,
                6
            ),

        "zodiac_top5_hit_rate":
            round(
                stats["zodiac_hits"]
                / total,
                6
            ),

        "pingte_top2_hit_rate":
            round(
                stats["pingte_zodiac_hits"]
                / total,
                6
            ),

        "size_hit_rate":
            round(
                stats["size_hits"]
                / total,
                6
            ),

        "parity_hit_rate":
            round(
                stats["parity_hits"]
                / total,
                6
            ),

        "details":
            details[-100:]
    }


def multi_window_backtest(rows):

    results = {}

    total = len(rows)

    for window in [
        100,
        300,
        500,
        1000
    ]:

        if total < window + 50:

            results[str(window)] = {
                "error":
                    "数据不足"
            }

            continue

        # 使用最近 window+50 条
        subset = rows[
            :window + 50
        ]

        results[str(window)] = backtest(
            subset,
            max_tests=window
        )

    return results
