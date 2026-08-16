# -*- coding: utf-8 -*-

from .predictor import (
    generate_prediction,
    NUMBER_TO_ZODIAC,
)


# =========================================================
# 从数据库 row 获取特码
# =========================================================
#
# 数据库没有 special 字段。
#
# numbers:
# 38,26,08,06,29,18,23
#
# 第7个号码就是特码：
# 23
#
# =========================================================

def get_special_from_row(row):

    # -----------------------------------------
    # 优先兼容旧数据库
    # -----------------------------------------

    if row.get("special") is not None:

        try:
            return int(row["special"])
        except Exception:
            pass

    # -----------------------------------------
    # 从 numbers 获取
    # -----------------------------------------

    numbers = row.get(
        "numbers",
        ""
    )

    if numbers is None:
        return None

    # 如果已经是 list
    if isinstance(numbers, list):

        values = numbers

    else:

        values = str(
            numbers
        ).replace(
            "，",
            ","
        ).split(",")

    values = [
        str(x).strip()
        for x in values
        if str(x).strip()
    ]

    # 必须至少7个号码
    if len(values) < 7:
        return None

    try:

        return int(
            values[6]
        )

    except Exception:

        return None


# =========================================================
# 获取波色
# =========================================================

def get_wave(number):

    # 香港六合彩标准波色
    #
    # 红波：
    # 1 2 7 8 12 13 18 19 23 24
    # 29 30 34 35 40 45 46
    #
    # 蓝波：
    # 3 4 9 10 14 15 20 25 26
    # 31 36 37 41 42 47 48
    #
    # 绿波：
    # 5 6 11 16 17 21 22 27 28
    # 32 33 38 39 43 44 49

    red = {
        1, 2, 7, 8,
        12, 13, 18, 19,
        23, 24, 29, 30,
        34, 35, 40,
        45, 46
    }

    blue = {
        3, 4, 9, 10,
        14, 15, 20,
        25, 26, 31,
        36, 37, 41,
        42, 47, 48
    }

    green = {
        5, 6, 11,
        16, 17, 21,
        22, 27, 28,
        32, 33, 38,
        39, 43, 44,
        49
    }

    if number in red:
        return "红"

    if number in blue:
        return "蓝"

    if number in green:
        return "绿"

    return None


# =========================================================
# 获取实际开奖结果
# =========================================================

def get_actual_result(row):

    number = get_special_from_row(
        row
    )

    if number is None:

        raise ValueError(
            f"无法获取特码: "
            f"issue={row.get('issue')}"
        )

    zodiac = NUMBER_TO_ZODIAC.get(
        number
    )

    # -----------------------------------------
    # 大小
    # -----------------------------------------

    if number >= 25:
        size = "大"
    else:
        size = "小"

    # -----------------------------------------
    # 单双
    # -----------------------------------------

    if number % 2:
        parity = "单"
    else:
        parity = "双"

    # -----------------------------------------
    # 波色
    # -----------------------------------------

    wave = get_wave(
        number
    )

    return {

        "number":
            number,

        "zodiac":
            zodiac,

        "size":
            size,

        "parity":
            parity,

        "wave":
            wave,
    }


# =========================================================
# 测试单期预测
# =========================================================

def test_one_prediction(
    prediction,
    actual
):

    # -----------------------------------------
    # 特码10码
    # -----------------------------------------

    top10 = [

        item["number"]

        for item in prediction.get(
            "top10_numbers",
            []
        )

    ]

    # -----------------------------------------
    # 特码生肖5肖
    # -----------------------------------------

    top5_zodiac = [

        item["zodiac"]

        for item in prediction.get(
            "top5_zodiac",
            []
        )

    ]

    # -----------------------------------------
    # 平特生肖2肖
    # -----------------------------------------

    top2_pingte = [

        item["zodiac"]

        for item in prediction.get(
            "top2_pingte_zodiac",
            []
        )

    ]

    # -----------------------------------------
    # 大小
    # -----------------------------------------

    size_prediction = (
        prediction
        .get(
            "size",
            {}
        )
        .get(
            "prediction"
        )
    )

    # -----------------------------------------
    # 单双
    # -----------------------------------------

    parity_prediction = (
        prediction
        .get(
            "parity",
            {}
        )
        .get(
            "prediction"
        )
    )

    # -----------------------------------------
    # 波色
    # -----------------------------------------

    wave_prediction = (
        prediction
        .get(
            "wave",
            {}
        )
        .get(
            "prediction"
        )
    )

    # -----------------------------------------
    # 统计
    # -----------------------------------------

    result = {

        "number_hit":
            actual["number"]
            in top10,

        "zodiac_hit":
            actual["zodiac"]
            in top5_zodiac,

        "pingte_zodiac_hit":
            actual["zodiac"]
            in top2_pingte,

        "size_hit":
            size_prediction
            == actual["size"],

        "parity_hit":
            parity_prediction
            == actual["parity"],

        "wave_hit":
            wave_prediction
            == actual["wave"],
    }

    return result


# =========================================================
# 百分比
# =========================================================

def rate(
    hits,
    total
):

    if total <= 0:
        return 0.0

    return round(
        hits / total,
        6
    )


# =========================================================
# 回测指定期数
# =========================================================
#
# 重要：
#
# target_row 是未来一期
#
# train_rows 只能使用 target_row 之前的数据
#
# 因此不会把未来开奖数据泄漏进去。
#
# =========================================================

def backtest_window(
    rows,
    window
):

    # -----------------------------------------
    # 数据按照：
    #
    # 最新 → 最旧
    #
    # -----------------------------------------

    rows = list(
        rows
    )

    # -----------------------------------------
    # 转成：
    #
    # 最旧 → 最新
    #
    # -----------------------------------------

    chronological = list(
        reversed(rows)
    )

    total_available = len(
        chronological
    )

    # -----------------------------------------
    # 至少需要：
    #
    # 训练50期
    # +
    # 回测window期
    #
    # -----------------------------------------

    min_train = 50

    required = (
        min_train +
        window
    )

    if total_available < required:

        return {

            "window":
                window,

            "error":
                "数据不足",

            "required":
                required,

            "available":
                total_available,
        }

    # -----------------------------------------
    # 只测试最后 window 期
    # -----------------------------------------

    start_index = (
        total_available -
        window
    )

    # 至少保留50期训练数据
    if start_index < min_train:

        start_index = min_train

    # -----------------------------------------
    # 统计
    # -----------------------------------------

    stats = {

        "tests":
            0,

        "number_hits":
            0,

        "zodiac_hits":
            0,

        "pingte_zodiac_hits":
            0,

        "size_hits":
            0,

        "parity_hits":
            0,

        "wave_hits":
            0,
    }

    details = []

    # =====================================================
    # Walk-Forward
    # =====================================================

    for i in range(
        start_index,
        total_available
    ):

        # -----------------------------------------
        # 训练数据
        #
        # 不包含当前目标期
        # -----------------------------------------

        train_rows = (
            chronological[:i]
        )

        # -----------------------------------------
        # 当前实际开奖
        # -----------------------------------------

        target_row = (
            chronological[i]
        )

        try:

            # -------------------------------------
            # 生成预测
            # -------------------------------------

            prediction = (
                generate_prediction(
                    train_rows
                )
            )

            # -------------------------------------
            # 获取真实结果
            # -------------------------------------

            actual = (
                get_actual_result(
                    target_row
                )
            )

            # -------------------------------------
            # 判断命中
            # -------------------------------------

            result = (
                test_one_prediction(
                    prediction,
                    actual
                )
            )

        except Exception as e:

            print(
                "回测错误:",
                target_row.get(
                    "issue"
                ),
                repr(e)
            )

            continue

        # -----------------------------------------
        # 总测试次数
        # -----------------------------------------

        stats["tests"] += 1

        # -----------------------------------------
        # 特码10码
        # -----------------------------------------

        if result["number_hit"]:

            stats[
                "number_hits"
            ] += 1

        # -----------------------------------------
        # 特码5肖
        # -----------------------------------------

        if result["zodiac_hit"]:

            stats[
                "zodiac_hits"
            ] += 1

        # -----------------------------------------
        # 平特2肖
        # -----------------------------------------

        if result[
            "pingte_zodiac_hit"
        ]:

            stats[
                "pingte_zodiac_hits"
            ] += 1

        # -----------------------------------------
        # 大小
        # -----------------------------------------

        if result["size_hit"]:

            stats[
                "size_hits"
            ] += 1

        # -----------------------------------------
        # 单双
        # -----------------------------------------

        if result["parity_hit"]:

            stats[
                "parity_hits"
            ] += 1

        # -----------------------------------------
        # 波色
        # -----------------------------------------

        if result["wave_hit"]:

            stats[
                "wave_hits"
            ] += 1

        # -----------------------------------------
        # 保存单期结果
        # -----------------------------------------

        details.append({

            "issue":
                target_row[
                    "issue"
                ],

            "actual_number":
                actual[
                    "number"
                ],

            "actual_zodiac":
                actual[
                    "zodiac"
                ],

            "actual_size":
                actual[
                    "size"
                ],

            "actual_parity":
                actual[
                    "parity"
                ],

            "actual_wave":
                actual[
                    "wave"
                ],

            **result
        })

    # =====================================================
    # 统计最终命中率
    # =====================================================

    total = stats[
        "tests"
    ]

    return {

        "window":
            window,

        "tests":
            total,

        # -------------------------------------
        # 特码10码
        # -------------------------------------

        "number_top10_hits":
            stats[
                "number_hits"
            ],

        "number_top10_hit_rate":
            rate(
                stats[
                    "number_hits"
                ],
                total
            ),

        # -------------------------------------
        # 特码5肖
        # -------------------------------------

        "zodiac_top5_hits":
            stats[
                "zodiac_hits"
            ],

        "zodiac_top5_hit_rate":
            rate(
                stats[
                    "zodiac_hits"
                ],
                total
            ),

        # -------------------------------------
        # 平特2肖
        # -------------------------------------

        "pingte_top2_hits":
            stats[
                "pingte_zodiac_hits"
            ],

        "pingte_top2_hit_rate":
            rate(
                stats[
                    "pingte_zodiac_hits"
                ],
                total
            ),

        # -------------------------------------
        # 大小
        # -------------------------------------

        "size_hits":
            stats[
                "size_hits"
            ],

        "size_hit_rate":
            rate(
                stats[
                    "size_hits"
                ],
                total
            ),

        # -------------------------------------
        # 单双
        # -------------------------------------

        "parity_hits":
            stats[
                "parity_hits"
            ],

        "parity_hit_rate":
            rate(
                stats[
                    "parity_hits"
                ],
                total
            ),

        # -------------------------------------
        # 波色
        # -------------------------------------

        "wave_hits":
            stats[
                "wave_hits"
            ],

        "wave_hit_rate":
            rate(
                stats[
                    "wave_hits"
                ],
                total
            ),

        # -------------------------------------
        # 最近单期明细
        # -------------------------------------

        "details":
            details,
    }


# =========================================================
# 多窗口回测
# =========================================================
#
# 你要求：
#
# 10期
# 20期
# 30期
# 60期
# 100期
#
# =========================================================

def multi_window_backtest(
    rows
):

    results = {}

    windows = [
        10,
        20,
        30,
        60,
        100,
    ]

    total = len(
        rows
    )

    for window in windows:

        print()
        print(
            "=" * 60
        )

        print(
            f"正在回测最近 "
            f"{window} 期"
        )

        print(
            "=" * 60
        )

        # -----------------------------------------
        # 至少需要：
        #
        # 50期训练
        # + window期测试
        #
        # -----------------------------------------

        if total < (
            50 + window
        ):

            results[
                str(window)
            ] = {

                "window":
                    window,

                "error":
                    "数据不足",

                "required":
                    50 + window,

                "available":
                    total,
            }

            print(
                f"数据不足："
                f"需要至少 "
                f"{50 + window} 期，"
                f"当前 {total} 期"
            )

            continue

        result = (
            backtest_window(
                rows,
                window
            )
        )

        results[
            str(window)
        ] = result

        # -----------------------------------------
        # 控制台打印
        # -----------------------------------------

        if "error" not in result:

            tests = result[
                "tests"
            ]

            print(
                f"测试期数："
                f"{tests}"
            )

            print(
                "特码10码："
                f"{result['number_top10_hits']}"
                f"/{tests} "
                f"{result['number_top10_hit_rate'] * 100:.2f}%"
            )

            print(
                "特码5肖："
                f"{result['zodiac_top5_hits']}"
                f"/{tests} "
                f"{result['zodiac_top5_hit_rate'] * 100:.2f}%"
            )

            print(
                "平特2肖："
                f"{result['pingte_top2_hits']}"
                f"/{tests} "
                f"{result['pingte_top2_hit_rate'] * 100:.2f}%"
            )

            print(
                "大小："
                f"{result['size_hits']}"
                f"/{tests} "
                f"{result['size_hit_rate'] * 100:.2f}%"
            )

            print(
                "单双："
                f"{result['parity_hits']}"
                f"/{tests} "
                f"{result['parity_hit_rate'] * 100:.2f}%"
            )

            print(
                "波色："
                f"{result['wave_hits']}"
                f"/{tests} "
                f"{result['wave_hit_rate'] * 100:.2f}%"
            )

    return results
