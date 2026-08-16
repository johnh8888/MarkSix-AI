# -*- coding: utf-8 -*-

from .predictor import (
    generate_prediction,
    NUMBER_TO_WAVE,
    NUMBER_TO_ZODIAC,
)


# =========================================================
# 安全获取特码
# =========================================================

def get_special(row):

    try:

        if isinstance(row, dict):

            if "special" in row:

                return int(
                    row["special"]
                )

            if "special_number" in row:

                return int(
                    row["special_number"]
                )

            numbers = row.get(
                "numbers"
            )

            if isinstance(
                numbers,
                str
            ):

                values = [
                    int(x.strip())
                    for x in numbers.split(",")
                    if x.strip()
                ]

                if values:

                    return (
                        values[1]
                        if len(values) >= 7
                        else values[0]
                    )

            if isinstance(
                numbers,
                list
            ):

                values = [
                    int(x)
                    for x in numbers
                ]

                if values:

                    return (
                        values[1]
                        if len(values) >= 7
                        else values[0]
                    )

    except Exception:

        pass

    return 0


# =========================================================
# 安全命中
# =========================================================

def safe_hit(
    numerator,
    denominator
):

    if denominator <= 0:

        return 0.0

    return numerator / denominator


# =========================================================
# 单次回测
# =========================================================

def backtest_window(
    rows,
    window
):

    if len(rows) < window + 100:

        return {

            "error":
                f"数据不足，至少需要{window + 100}期",

            "tests":
                0,
        }

    # -----------------------------------------------------
    # 命中计数
    # -----------------------------------------------------

    number_hits = 0

    zodiac_hits = 0

    pingte_hits = 0

    size_hits = 0

    parity_hits = 0

    wave_single_hits = 0

    wave_double_hits = 0

    # -----------------------------------------------------
    # 波色三组合
    # -----------------------------------------------------

    pair_hits = {

        "红+蓝":
            0,

        "红+绿":
            0,

        "蓝+绿":
            0,
    }

    tests = 0

    # -----------------------------------------------------
    # Walk Forward
    #
    # rows[0] = 最新
    #
    # target_index:
    # 当前要预测的历史开奖结果
    #
    # history:
    # 只能使用更早的数据
    # -----------------------------------------------------

    max_tests = min(
        window,
        len(rows) - 100
    )

    for target_index in range(
        max_tests,
        0,
        -1
    ):

        history = rows[
            target_index:
        ]

        target = rows[
            target_index - 1
        ]

        if len(history) < 100:

            continue

        try:

            prediction = generate_prediction(
                history
            )

        except Exception:

            continue

        special = get_special(
            target
        )

        if not 1 <= special <= 49:

            continue

        tests += 1

        # =================================================
        # 特码10码
        # =================================================

        top10 = {

            int(item["number"])

            for item
            in prediction.get(
                "top10_numbers",
                []
            )
        }

        if special in top10:

            number_hits += 1

        # =================================================
        # 生肖5肖
        # =================================================

        target_zodiac = NUMBER_TO_ZODIAC.get(
            special
        )

        top5_zodiac = {

            item["zodiac"]

            for item
            in prediction.get(
                "top5_zodiac",
                []
            )
        }

        if target_zodiac in top5_zodiac:

            zodiac_hits += 1

        # =================================================
        # 平特2肖
        # =================================================

        pingte = {

            item["zodiac"]

            for item
            in prediction.get(
                "top2_pingte_zodiac",
                []
            )
        }

        if target_zodiac in pingte:

            pingte_hits += 1

        # =================================================
        # 大小
        # =================================================

        target_size = (
            "大"
            if special >= 25
            else "小"
        )

        predicted_size = prediction.get(
            "size",
            {}
        ).get(
            "prediction"
        )

        if target_size == predicted_size:

            size_hits += 1

        # =================================================
        # 单双
        # =================================================

        target_parity = (
            "单"
            if special % 2
            else "双"
        )

        predicted_parity = prediction.get(
            "parity",
            {}
        ).get(
            "prediction"
        )

        if target_parity == predicted_parity:

            parity_hits += 1

        # =================================================
        # 波色
        # =================================================

        target_wave = NUMBER_TO_WAVE.get(
            special
        )

        wave = prediction.get(
            "wave",
            {}
        )

        single_wave = wave.get(
            "single_prediction"
        )

        double_wave = set(
            wave.get(
                "double_prediction",
                []
            )
        )

        if target_wave == single_wave:

            wave_single_hits += 1

        if target_wave in double_wave:

            wave_double_hits += 1

        # =================================================
        # 三种组合
        # =================================================

        pair_definitions = {

            "红+蓝":
                {"红", "蓝"},

            "红+绿":
                {"红", "绿"},

            "蓝+绿":
                {"蓝", "绿"},
        }

        for name, pair in pair_definitions.items():

            if target_wave in pair:

                pair_hits[name] += 1

    # =====================================================
    # 结果
    # =====================================================

    number_rate = safe_hit(
        number_hits,
        tests
    )

    zodiac_rate = safe_hit(
        zodiac_hits,
        tests
    )

    pingte_rate = safe_hit(
        pingte_hits,
        tests
    )

    size_rate = safe_hit(
        size_hits,
        tests
    )

    parity_rate = safe_hit(
        parity_hits,
        tests
    )

    wave_single_rate = safe_hit(
        wave_single_hits,
        tests
    )

    wave_double_rate = safe_hit(
        wave_double_hits,
        tests
    )

    # -----------------------------------------------------
    # 随机基准
    # -----------------------------------------------------

    wave_single_baseline = 1 / 3

    wave_double_baseline = 2 / 3

    return {

        "tests":
            tests,

        # -------------------------------------------------
        # 特码
        # -------------------------------------------------

        "number_top10_hit_rate":
            number_rate,

        "number_top10_random_baseline":
            10 / 49,

        "number_top10_edge":
            number_rate - (10 / 49),

        # -------------------------------------------------
        # 生肖
        # -------------------------------------------------

        "zodiac_top5_hit_rate":
            zodiac_rate,

        "zodiac_top5_random_baseline":
            5 / 12,

        # -------------------------------------------------
        # 平特
        # -------------------------------------------------

        "pingte_top2_hit_rate":
            pingte_rate,

        "pingte_top2_random_baseline":
            2 / 12,

        # -------------------------------------------------
        # 大小
        # -------------------------------------------------

        "size_hit_rate":
            size_rate,

        # -------------------------------------------------
        # 单双
        # -------------------------------------------------

        "parity_hit_rate":
            parity_rate,

        # -------------------------------------------------
        # 波色
        # -------------------------------------------------

        "wave_single_hit_rate":
            wave_single_rate,

        "wave_double_hit_rate":
            wave_double_rate,

        "wave_single_random_baseline":
            wave_single_baseline,

        "wave_double_random_baseline":
            wave_double_baseline,

        "wave_single_edge":
            wave_single_rate
            -
            wave_single_baseline,

        "wave_double_edge":
            wave_double_rate
            -
            wave_double_baseline,

        # -------------------------------------------------
        # 三组合
        # -------------------------------------------------

        "wave_pair_rates": {

            name:
                safe_hit(
                    count,
                    tests
                )

            for name, count
            in pair_hits.items()
        },
    }


# =========================================================
# 多窗口回测
# =========================================================

def multi_window_backtest(rows):

    results = {}

    # =====================================================
    # 只保留10和20
    # =====================================================

    for window in [
        10,
        20,
    ]:

        try:

            result = backtest_window(
                rows,
                window
            )

            results[str(window)] = result

        except Exception as e:

            results[str(window)] = {

                "error":
                    repr(e),

                "tests":
                    0,
            }

    return results


# =========================================================
# 单独测试
# =========================================================

if __name__ == "__main__":

    print(
        "backtest.py V1.4"
    )

    print(
        "仅执行10期和20期Walk-Forward回测"
    )
