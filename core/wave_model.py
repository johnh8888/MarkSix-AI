# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
波色动态模型

核心：

1. 波色频率
2. 波色转移矩阵
3. 上一期波色
4. 连续波色
5. 反转概率
6. 非反转概率
7. 波色熵
8. 短/中/长期融合
9. 波色单推
10. 波色双推

仅用于统计分析和历史回测。
"""

from collections import Counter

from core.features import (
    get_special,
    get_wave,
)

from .state_engine import (
    get_windows,
)


WAVES = (
    "红",
    "蓝",
    "绿",
)


def safe_wave(row):

    try:

        number = int(
            get_special(row)
        )

        wave = get_wave(
            number
        )

        if wave in WAVES:
            return wave

    except Exception:
        pass

    return None


# =========================================================
# 波色序列
# =========================================================

def get_wave_sequence(rows):

    sequence = []

    for row in rows:

        wave = safe_wave(row)

        if wave:
            sequence.append(
                wave
            )

    return sequence


# =========================================================
# 波色频率
# =========================================================

def wave_frequency(rows):

    sequence = get_wave_sequence(
        rows
    )

    counter = Counter(
        sequence
    )

    total = len(sequence)

    if total == 0:

        return {
            wave: 1 / 3
            for wave in WAVES
        }

    return {

        wave:
            counter.get(wave, 0)
            / total

        for wave in WAVES

    }


# =========================================================
# 转移矩阵
# =========================================================

def transition_matrix(rows):

    sequence = get_wave_sequence(
        rows
    )

    matrix = {

        source: {

            target: 0.0
            for target in WAVES

        }

        for source in WAVES
    }

    counts = {

        source: {

            target: 0
            for target in WAVES

        }

        for source in WAVES
    }

    if len(sequence) < 2:

        return matrix

    for i in range(
        len(sequence) - 1
    ):

        current = sequence[i]
        next_wave = sequence[i + 1]

        counts[
            current
        ][
            next_wave
        ] += 1

    for source in WAVES:

        total = sum(
            counts[source].values()
        )

        if total == 0:

            for target in WAVES:

                matrix[
                    source
                ][
                    target
                ] = 1 / 3

        else:

            for target in WAVES:

                matrix[
                    source
                ][
                    target
                ] = (
                    counts[
                        source
                    ][
                        target
                    ]
                    / total
                )

    return matrix


# =========================================================
# 当前波色
# =========================================================

def current_wave(rows):

    sequence = get_wave_sequence(
        rows
    )

    if not sequence:
        return None

    return sequence[0]


# =========================================================
# 连续波色
# =========================================================

def current_streak(rows):

    sequence = get_wave_sequence(
        rows
    )

    if not sequence:

        return {
            "wave": None,
            "length": 0,
        }

    wave = sequence[0]

    length = 0

    for item in sequence:

        if item == wave:
            length += 1
        else:
            break

    return {

        "wave":
            wave,

        "length":
            length,

    }


# =========================================================
# 反转统计
# =========================================================

def reversal_stats(rows):

    sequence = get_wave_sequence(
        rows
    )

    if len(sequence) < 2:

        return {

            "reversal":
                0.5,

            "same":
                0.5,

        }

    reversal = 0
    same = 0

    for i in range(
        len(sequence) - 1
    ):

        if sequence[i] == sequence[i + 1]:

            same += 1

        else:

            reversal += 1

    total = (
        reversal
        + same
    )

    if total == 0:

        return {
            "reversal": 0.5,
            "same": 0.5,
        }

    return {

        "reversal":
            reversal / total,

        "same":
            same / total,

    }


# =========================================================
# 连续长度统计
# =========================================================

def streak_statistics(rows):

    sequence = get_wave_sequence(
        rows
    )

    if not sequence:

        return {
            1: 1.0,
            2: 0.0,
            3: 0.0,
            4: 0.0,
        }

    streaks = []

    current = sequence[0]
    length = 1

    for wave in sequence[1:]:

        if wave == current:

            length += 1

        else:

            streaks.append(
                length
            )

            current = wave
            length = 1

    streaks.append(
        length
    )

    counter = Counter(
        min(length, 4)
        for length in streaks
    )

    total = len(streaks)

    return {

        key:
            counter.get(key, 0)
            / total

        for key in (
            1,
            2,
            3,
            4,
        )

    }


# =========================================================
# 波色熵
# =========================================================

def entropy(rows):

    import math

    probs = wave_frequency(
        rows
    )

    value = 0.0

    for p in probs.values():

        if p > 0:

            value -= (
                p
                * math.log(p)
            )

    maximum = math.log(3)

    if maximum <= 0:
        return 0.0

    return value / maximum


# =========================================================
# 单窗口评分
# =========================================================

def score_window(rows):

    if not rows:

        return {
            wave: 1 / 3
            for wave in WAVES
        }

    frequency = wave_frequency(
        rows
    )

    matrix = transition_matrix(
        rows
    )

    current = current_wave(
        rows
    )

    # ---------------------------------------------
    # 基础频率
    # ---------------------------------------------

    scores = {

        wave:
            frequency[wave] * 0.35

        for wave in WAVES
    }

    # ---------------------------------------------
    # 转移
    # ---------------------------------------------

    if current in WAVES:

        for wave in WAVES:

            scores[wave] += (
                matrix[current][wave]
                * 0.45
            )

    # ---------------------------------------------
    # 反转
    # ---------------------------------------------

    reversal = reversal_stats(
        rows
    )

    if current in WAVES:

        if reversal["reversal"] > 0.5:

            for wave in WAVES:

                if wave != current:

                    scores[wave] += (
                        reversal["reversal"]
                        * 0.10
                        / 2
                    )

        else:

            scores[current] += (
                reversal["same"]
                * 0.10
            )

    total = sum(
        scores.values()
    )

    if total <= 0:

        return {
            wave: 1 / 3
            for wave in WAVES
        }

    return {

        wave:
            scores[wave] / total

        for wave in WAVES

    }


# =========================================================
# V3 综合波色概率
# =========================================================

def predict_wave(rows):

    windows = get_windows(
        rows
    )

    short = score_window(
        windows["short"]
    )

    medium = score_window(
        windows["medium"]
    )

    long = score_window(
        windows["long"]
    )

    # -----------------------------------------------------
    # 基础动态窗口
    # -----------------------------------------------------

    # 这里使用状态引擎给出的动态窗口。
    # 为避免循环导入，直接按照当前数据结构计算。
    from model.state_engine import detect_state

    state = detect_state(
        rows
    )

    sw = state["short_weight"]
    mw = state["medium_weight"]
    lw = state["long_weight"]

    probabilities = {}

    for wave in WAVES:

        probabilities[wave] = (

            short[wave] * sw

            +

            medium[wave] * mw

            +

            long[wave] * lw

        )

    # -----------------------------------------------------
    # 上一期转移强化
    # -----------------------------------------------------

    current = current_wave(
        rows
    )

    if current in WAVES:

        matrix = transition_matrix(
            rows
        )

        for wave in WAVES:

            probabilities[wave] = (

                probabilities[wave]
                * 0.70

                +

                matrix[current][wave]
                * 0.30

            )

    # -----------------------------------------------------
    # 归一化
    # -----------------------------------------------------

    total = sum(
        probabilities.values()
    )

    if total <= 0:

        probabilities = {
            wave: 1 / 3
            for wave in WAVES
        }

    else:

        probabilities = {

            wave:
                probabilities[wave]
                / total

            for wave in WAVES

        }

    ranking = sorted(

        probabilities.items(),

        key=lambda x: x[1],

        reverse=True

    )

    single = ranking[0][0]

    double = [
        ranking[0][0],
        ranking[1][0],
    ]

    return {

        "probabilities":
            probabilities,

        "ranking":
            ranking,

        "single":
            single,

        "double":
            double,

        "current_wave":
            current,

        "streak":
            current_streak(rows),

        "reversal":
            reversal_stats(rows),

        "entropy":
            entropy(rows),

        "transition":
            transition_matrix(rows),

    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    rows = []

    numbers = [

        23, 13, 27, 43,
        34, 8, 45, 46,
        49, 29, 12, 18,
        31, 7, 22, 40,
        15, 26, 38, 4,
        33, 16, 9, 44,

    ]

    for i, n in enumerate(
        numbers
    ):

        rows.append({

            "numbers":
                f"01,02,03,04,05,06,{n:02d}",

            "issue":
                str(2026000 + i),

        })

    result = predict_wave(
        rows
    )

    print("=" * 70)
    print("六合彩 AI V3.0 波色模型")
    print("=" * 70)

    print(
        "当前波色：",
        result["current_wave"]
    )

    print(
        "连续：",
        result["streak"]
    )

    print(
        "波色单推：",
        result["single"]
    )

    print(
        "波色双推：",
        " + ".join(
            result["double"]
        )
    )

    print(
        "\n波色概率："
    )

    for wave, probability in result[
        "ranking"
    ]:

        print(
            f"{wave}: "
            f"{probability:.4f}"
        )

    print(
        "\n转移矩阵："
    )

    for source, targets in result[
        "transition"
    ].items():

        print(
            source,
            targets
        )