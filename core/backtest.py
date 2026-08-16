# -*- coding: utf-8 -*-

"""
六合彩回测模块

功能：

1. 特码10码命中率
2. 特码生肖5肖命中率
3. 平特生肖2肖命中率
4. 大小命中率
5. 单双命中率

同时计算：

10期
20期
30期
60期
100期

滚动命中率。

重要：

数据库没有 special 字段。

特码统一通过：

    get_special(row)

从 numbers 第7个号码获取。
"""

from typing import Dict, Any, List

from .predictor import (
    generate_prediction,
    NUMBER_TO_ZODIAC,
)

from .features import (
    get_special,
)


# =========================================================
# 获取真实开奖结果
# =========================================================

def get_actual_result(row):

    number = get_special(row)

    if not (1 <= number <= 49):
        raise ValueError(
            f"无法获取有效特码：{row}"
        )

    zodiac = NUMBER_TO_ZODIAC.get(
        number
    )

    # -----------------------------------------------------
    # 大小
    # -----------------------------------------------------

    if number >= 25:
        size = "大"
    else:
        size = "小"

    # -----------------------------------------------------
    # 单双
    # -----------------------------------------------------

    if number % 2:
        parity = "单"
    else:
        parity = "双"

    return {

        "number":
            number,

        "zodiac":
            zodiac,

        "size":
            size,

        "parity":
            parity,
    }


# =========================================================
# 检查一次预测
# =========================================================

def test_one_prediction(
    prediction,
    actual
):

    # -----------------------------------------------------
    # 特码10码
    # -----------------------------------------------------

    top10 = [

        int(item["number"])

        for item in prediction.get(
            "top10_numbers",
            []
        )

        if isinstance(item, dict)
        and "number" in item
    ]

    # -----------------------------------------------------
    # 生肖5肖
    # -----------------------------------------------------

    top5_zodiac = [

        item["zodiac"]

        for item in prediction.get(
            "top5_zodiac",
            []
        )

        if isinstance(item, dict)
        and "zodiac" in item
    ]

    # -----------------------------------------------------
    # 平特2肖
    # -----------------------------------------------------

    top2_pingte = [

        item["zodiac"]

        for item in prediction.get(
            "top2_pingte_zodiac",
            []
        )

        if isinstance(item, dict)
        and "zodiac" in item
    ]

    # -----------------------------------------------------
    # 大小
    # -----------------------------------------------------

    size_prediction = (
        prediction
        .get("size", {})
        .get("prediction")
    )

    # -----------------------------------------------------
    # 单双
    # -----------------------------------------------------

    parity_prediction = (
        prediction
        .get("parity", {})
        .get("prediction")
    )

    return {

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
    }


# =========================================================
# 空统计
# =========================================================

def empty_stats():

    return {

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
    }


# =========================================================
# 计算命中率
# =========================================================

def stats_to_result(stats):

    tests = stats["tests"]

    if tests <= 0:

        return {

            "tests":
                0,

            "number_top10_hit_rate":
                0.0,

            "zodiac_top5_hit_rate":
                0.0,

            "pingte_top2_hit_rate":
                0.0,

            "size_hit_rate":
                0.0,

            "parity_hit_rate":
                0.0,
        }

    return {

        "tests":
            tests,

        "number_top10_hit_rate":
            round(
                stats["number_hits"]
                / tests,
                6
            ),

        "zodiac_top5_hit_rate":
            round(
                stats["zodiac_hits"]
                / tests,
                6
            ),

        "pingte_top2_hit_rate":
            round(
                stats["pingte_zodiac_hits"]
                / tests,
                6
            ),

        "size_hit_rate":
            round(
                stats["size_hits"]
                / tests,
                6
            ),

        "parity_hit_rate":
            round(
                stats["parity_hits"]
                / tests,
                6
            ),
    }


# =========================================================
# 单个滚动回测
# =========================================================

def backtest(
    rows,
    max_tests=100
):

    if not rows:

        return {
            "error":
                "没有历史数据"
        }

    # -----------------------------------------------------
    # 数据库返回：
    #
    # 最新 -> 最旧
    #
    # 回测需要：
    #
    # 最旧 -> 最新
    # -----------------------------------------------------

    rows = list(rows)

    chronological = list(
        reversed(rows)
    )

    total_available = len(
        chronological
    )

    # -----------------------------------------------------
    # 至少需要50期训练数据
    # -----------------------------------------------------

    min_train = 50

    if total_available <= min_train:

        return {

            "error":
                f"历史数据不足{min_train + 1}期",

            "available":
                total_available,
        }

    # -----------------------------------------------------
    # 最多测试 max_tests 期
    # -----------------------------------------------------

    test_count = min(
        int(max_tests),
        total_available - min_train
    )

    start_index = (
        total_available
        - test_count
    )

    stats = empty_stats()

    details = []

    # -----------------------------------------------------
    # 滚动回测
    # -----------------------------------------------------

    for i in range(
        start_index,
        total_available
    ):

        # ---------------------------------------------
        # 至少保留50期训练数据
        # ---------------------------------------------

        if i < min_train:
            continue

        # ---------------------------------------------
        # 训练数据
        #
        # 注意：
        # chronological[:i]
        #
        # 不包含当前目标期
        #
        # 所以不会偷看未来
        # ---------------------------------------------

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

            print()
            print(
                "回测单期错误：",
                target_row.get("issue"),
                repr(e)
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

            "issue":
                target_row["issue"],

            "actual_number":
                actual["number"],

            "actual_zodiac":
                actual["zodiac"],

            "actual_size":
                actual["size"],

            "actual_parity":
                actual["parity"],

            **result,
        })

    result = stats_to_result(
        stats
    )

    result["details"] = details

    return result


# =========================================================
# 最近N期回测
# =========================================================

def rolling_window_backtest(
    rows,
    window,
    min_train=50
):

    rows = list(rows)

    if len(rows) <= min_train:

        return {

            "window":
                window,

            "error":
                "历史数据不足",

            "available":
                len(rows),
        }

    # -----------------------------------------------------
    # 数据：
    #
    # 最新 -> 最旧
    # -----------------------------------------------------

    chronological = list(
        reversed(rows)
    )

    total = len(
        chronological
    )

    # -----------------------------------------------------
    # 实际测试期数
    # -----------------------------------------------------

    actual_window = min(
        window,
        total - min_train
    )

    start_index = (
        total - actual_window
    )

    stats = empty_stats()

    details = []

    # -----------------------------------------------------
    # 最近N期逐期回测
    # -----------------------------------------------------

    for i in range(
        start_index,
        total
    ):

        if i < min_train:
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
                f"回测 {window} 期错误：",
                target_row.get("issue"),
                repr(e)
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

            "issue":
                target_row["issue"],

            "actual_number":
                actual["number"],

            "actual_zodiac":
                actual["zodiac"],

            "actual_size":
                actual["size"],

            "actual_parity":
                actual["parity"],

            **result,
        })

    result = stats_to_result(
        stats
    )

    result["window"] = window

    result["available"] = len(rows)

    result["details"] = details

    return result


# =========================================================
# 多窗口回测
# =========================================================

def multi_window_backtest(rows):

    windows = [
        10,
        20,
        30,
        60,
        100,
    ]

    results = {}

    for window in windows:

        print()
        print(
            f"正在进行最近 {window} 期回测..."
        )

        result = rolling_window_backtest(
            rows,
            window
        )

        results[str(window)] = result

        # -------------------------------------------------
        # 控制台显示
        # -------------------------------------------------

        if "error" not in result:

            print(
                f"最近{window}期："
            )

            print(
                "  特码10码："
                f"{result['number_top10_hit_rate']:.2%}"
            )

            print(
                "  生肖5肖："
                f"{result['zodiac_top5_hit_rate']:.2%}"
            )

            print(
                "  平特2肖："
                f"{result['pingte_top2_hit_rate']:.2%}"
            )

            print(
                "  大小："
                f"{result['size_hit_rate']:.2%}"
            )

            print(
                "  单双："
                f"{result['parity_hit_rate']:.2%}"
            )

        else:

            print(
                "  ",
                result["error"]
            )

    return results


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "六合彩回测模块"
    )

    print(
        "支持：10 / 20 / 30 / 60 / 100期"
    )

    print(
        "=" * 70
    )
