# -*- coding: utf-8 -*-

"""
六合彩 AI V2.0 Walk-Forward 回测

只使用预测时点之前的数据。

输出：
10期
20期

不再输出30/60/100。
"""

from .predictor import generate_prediction


# =========================================================
# 单期回测
# =========================================================

def test_one(
    train_rows,
    actual_row
):

    prediction = generate_prediction(
        train_rows
    )


    # -----------------------------------------------------
    # 实际特码
    # -----------------------------------------------------

    try:
        actual = int(
            actual_row["special"]
        )
    except Exception:
        return None


    # -----------------------------------------------------
    # Top10
    # -----------------------------------------------------

    top10 = {

        int(item["number"])

        for item
        in prediction.get(
            "top10_numbers",
            []
        )
    }


    number_hit = (
        actual in top10
    )


    # -----------------------------------------------------
    # 生肖
    # -----------------------------------------------------

    zodiac_map = {

        "马":
            [1, 13, 25, 37, 49],

        "蛇":
            [2, 14, 26, 38],

        "龙":
            [3, 15, 27, 39],

        "兔":
            [4, 16, 28, 40],

        "虎":
            [5, 17, 29, 41],

        "牛":
            [6, 18, 30, 42],

        "鼠":
            [7, 19, 31, 43],

        "猪":
            [8, 20, 32, 44],

        "狗":
            [9, 21, 33, 45],

        "鸡":
            [10, 22, 34, 46],

        "猴":
            [11, 23, 35, 47],

        "羊":
            [12, 24, 36, 48],
    }


    actual_zodiac = None

    for zodiac, numbers in zodiac_map.items():

        if actual in numbers:

            actual_zodiac = zodiac

            break


    top5_zodiac = {

        item["zodiac"]

        for item
        in prediction.get(
            "top5_zodiac",
            []
        )
    }


    zodiac_hit = (
        actual_zodiac
        in top5_zodiac
    )


    # -----------------------------------------------------
    # 平特
    # -----------------------------------------------------

    top2_pingte = {

        item["zodiac"]

        for item
        in prediction.get(
            "top2_pingte_zodiac",
            []
        )
    }


    pingte_hit = (
        actual_zodiac
        in top2_pingte
    )


    # -----------------------------------------------------
    # 大小
    # -----------------------------------------------------

    actual_size = (
        "大"
        if actual >= 25
        else "小"
    )


    predicted_size = (
        prediction
        .get(
            "size",
            {}
        )
        .get(
            "prediction"
        )
    )


    size_hit = (
        actual_size
        == predicted_size
    )


    # -----------------------------------------------------
    # 单双
    # -----------------------------------------------------

    actual_parity = (
        "单"
        if actual % 2
        else "双"
    )


    predicted_parity = (
        prediction
        .get(
            "parity",
            {}
        )
        .get(
            "prediction"
        )
    )


    parity_hit = (
        actual_parity
        == predicted_parity
    )


    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    wave_map = {

        "红": {
            1, 2, 7, 8, 12, 13,
            18, 19, 23, 24,
            29, 30, 34, 35,
            40, 45, 46
        },

        "蓝": {
            3, 4, 9, 10, 14, 15,
            20, 25, 26, 31,
            36, 37, 41, 42,
            47, 48
        },

        "绿": {
            5, 6, 11, 16, 17,
            21, 22, 27, 28,
            32, 33, 38, 39,
            43, 44, 49
        },
    }


    actual_wave = None

    for wave, numbers in wave_map.items():

        if actual in numbers:

            actual_wave = wave

            break


    predicted_wave = (
        prediction
        .get(
            "wave",
            {}
        )
        .get(
            "single"
        )
    )


    predicted_double = (
        prediction
        .get(
            "wave",
            {}
        )
        .get(
            "double",
            []
        )
    )


    wave_single_hit = (
        actual_wave
        == predicted_wave
    )


    wave_double_hit = (
        actual_wave
        in predicted_double
    )


    return {

        "number_hit":
            number_hit,

        "zodiac_hit":
            zodiac_hit,

        "pingte_hit":
            pingte_hit,

        "size_hit":
            size_hit,

        "parity_hit":
            parity_hit,

        "wave_single_hit":
            wave_single_hit,

        "wave_double_hit":
            wave_double_hit,
    }


# =========================================================
# Walk Forward
# =========================================================

def walk_forward(
    rows,
    window
):

    if len(rows) < window + 30:

        return {
            "error":
                "历史数据不足"
        }


    # -----------------------------------------------------
    # 只测试最近 window 期
    # -----------------------------------------------------

    test_count = min(
        window,
        len(rows) - 30
    )


    results = {

        "number_hit": 0,

        "zodiac_hit": 0,

        "pingte_hit": 0,

        "size_hit": 0,

        "parity_hit": 0,

        "wave_single_hit": 0,

        "wave_double_hit": 0,
    }


    tests = 0


    # -----------------------------------------------------
    # rows 通常是：
    #
    # 最新 → 最旧
    #
    # 因此从较旧的数据开始，
    # 每次只允许使用当时之前的数据。
    # -----------------------------------------------------

    start = len(rows) - test_count


    for i in range(
        start,
        len(rows)
    ):

        train_end = i

        train_rows = rows[
            train_end:
        ]


        if len(train_rows) < 30:
            continue


        actual_row = rows[i]


        result = test_one(
            train_rows,
            actual_row
        )


        if result is None:
            continue


        tests += 1


        for key in results:

            if result.get(
                key,
                False
            ):

                results[key] += 1


    if tests == 0:

        return {
            "error":
                "没有有效测试"
        }


    return {

        "tests":
            tests,

        "number_top10_hit_rate":
            results["number_hit"]
            / tests,

        "zodiac_top5_hit_rate":
            results["zodiac_hit"]
            / tests,

        "pingte_top2_hit_rate":
            results["pingte_hit"]
            / tests,

        "size_hit_rate":
            results["size_hit"]
            / tests,

        "parity_hit_rate":
            results["parity_hit"]
            / tests,

        "wave_single_hit_rate":
            results["wave_single_hit"]
            / tests,

        "wave_double_hit_rate":
            results["wave_double_hit"]
            / tests,

        "wave_double_improvement":
            (
                results["wave_double_hit"]
                -
                results["wave_single_hit"]
            )
            / tests,
    }


# =========================================================
# 多窗口
# =========================================================

def multi_window_backtest(
    rows
):

    results = {}

    for window in [
        10,
        20,
    ]:

        result = walk_forward(
            rows,
            window
        )

        results[str(window)] = result


    return results
