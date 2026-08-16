# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
波色独立模型

核心：

1. 波色频率
2. 波色转移矩阵
3. 连续状态
4. 反转
5. 非反转
6. 波色熵
7. 近期偏离
8. 动态窗口
9. 单推
10. 双推
"""

from collections import Counter

from .features import (
    WAVES,
    get_wave,
    safe_special,
    wave_sequence,
    wave_transition_probability,
    current_wave_streak,
    wave_entropy,
    wave_deviation,
)


# =========================================================
# 基础频率
# =========================================================

def wave_frequency(
    rows,
    window
):

    sequence = wave_sequence(
        rows[:window]
    )


    counter = Counter(
        sequence
    )


    total = sum(
        counter.values()
    )


    if total <= 0:

        return {

            wave:
                1 / 3

            for wave in WAVES

        }


    return {

        wave:
            (
                counter.get(
                    wave,
                    0
                ) + 1
            )
            / (
                total + 3
            )

        for wave in WAVES

    }


# =========================================================
# 上一期波色
# =========================================================

def previous_wave(
    rows
):

    sequence = wave_sequence(
        rows
    )


    if not sequence:
        return None


    return sequence[0]


# =========================================================
# 连续状态评分
# =========================================================

def streak_adjustment(
    rows
):

    streak = current_wave_streak(
        rows
    )


    current = streak[
        "wave"
    ]

    length = streak[
        "length"
    ]


    result = {

        wave:
            0.0

        for wave in WAVES

    }


    if current not in WAVES:
        return result


    # -----------------------------------------------------
    # 1次：没有明显调整
    # -----------------------------------------------------

    if length <= 1:

        return result


    # -----------------------------------------------------
    # 2次：
    # 非当前色略微增加
    # -----------------------------------------------------

    if length == 2:

        result[current] -= 0.03

        for wave in WAVES:

            if wave != current:
                result[wave] += 0.015


    # -----------------------------------------------------
    # 3次
    # -----------------------------------------------------

    elif length == 3:

        result[current] -= 0.06

        for wave in WAVES:

            if wave != current:
                result[wave] += 0.03


    # -----------------------------------------------------
    # 4次+
    # -----------------------------------------------------

    else:

        result[current] -= 0.10

        for wave in WAVES:

            if wave != current:
                result[wave] += 0.05


    return result


# =========================================================
# 反转模型
# =========================================================

def reversal_model(
    rows
):

    sequence = wave_sequence(
        rows
    )


    result = {

        wave:
            0.0

        for wave in WAVES

    }


    if len(sequence) < 3:

        return result


    current = sequence[0]


    # 统计：
    #
    # 当前色之后，
    # 下一期是否发生变化

    changed = Counter()

    total = Counter()


    for index in range(
        len(sequence) - 1
    ):

        source = sequence[
            index
        ]

        target = sequence[
            index + 1
        ]


        total[source] += 1


        if target != source:

            changed[source] += 1


    if current not in total:

        return result


    reversal_rate = (
        changed[current]
        + 1
    ) / (
        total[current]
        + 2
    )


    # 如果反转概率高，
    # 当前色降低，
    # 其他颜色增加。

    result[current] -= (
        0.12
        * reversal_rate
    )


    for wave in WAVES:

        if wave != current:

            result[wave] += (
                0.06
                * reversal_rate
            )


    return result


# =========================================================
# 非反转模型
# =========================================================

def continuation_model(
    rows
):

    sequence = wave_sequence(
        rows
    )


    result = {

        wave:
            0.0

        for wave in WAVES

    }


    if len(sequence) < 3:
        return result


    current = sequence[0]


    total = 0

    same = 0


    for index in range(
        len(sequence) - 1
    ):

        source = sequence[
            index
        ]

        target = sequence[
            index + 1
        ]


        if source == current:

            total += 1

            if target == source:

                same += 1


    if total <= 0:
        return result


    rate = (
        same + 1
    ) / (
        total + 2
    )


    result[current] += (
        0.12
        * rate
    )


    return result


# =========================================================
# 转移模型
# =========================================================

def transition_model(
    rows
):

    transition = (
        wave_transition_probability(
            rows[:120]
        )
    )


    current = previous_wave(
        rows
    )


    result = {

        wave:
            1 / 3

        for wave in WAVES

    }


    if current not in transition:

        return result


    return dict(
        transition[current]
    )


# =========================================================
# 综合波色概率
# =========================================================

def wave_probabilities(
    rows
):

    if not rows:

        return {

            wave:
                1 / 3

            for wave in WAVES

        }


    # -----------------------------------------------------
    # 12 / 36 / 120
    # -----------------------------------------------------

    short = wave_frequency(
        rows,
        12
    )


    medium = wave_frequency(
        rows,
        36
    )


    long = wave_frequency(
        rows,
        120
    )


    # -----------------------------------------------------
    # 转移
    # -----------------------------------------------------

    transition = transition_model(
        rows
    )


    # -----------------------------------------------------
    # 连续
    # -----------------------------------------------------

    streak = streak_adjustment(
        rows
    )


    # -----------------------------------------------------
    # 反转
    # -----------------------------------------------------

    reversal = reversal_model(
        rows
    )


    # -----------------------------------------------------
    # 非反转
    # -----------------------------------------------------

    continuation = continuation_model(
        rows
    )


    # -----------------------------------------------------
    # 动态权重
    # -----------------------------------------------------

    result = {}


    for wave in WAVES:

        score = (

            short[wave]
            * 0.25

            +

            medium[wave]
            * 0.20

            +

            long[wave]
            * 0.10

            +

            transition[wave]
            * 0.30

            +

            0.10

        )


        score += (
            streak[wave]
            * 0.50
        )


        score += (
            reversal[wave]
            * 0.50
        )


        score += (
            continuation[wave]
            * 0.50
        )


        result[wave] = max(
            score,
            0.0001
        )


    # -----------------------------------------------------
    # 近期偏离修正
    # -----------------------------------------------------

    deviation = wave_deviation(
        rows,
        12
    )


    for wave in WAVES:

        # 偏离越大，
        # 对短期过热适度降权。

        result[wave] *= (
            1.0
            -
            max(
                deviation[wave],
                0
            )
            * 0.20
        )


    # -----------------------------------------------------
    # 归一化
    # -----------------------------------------------------

    total = sum(
        result.values()
    )


    if total <= 0:

        return {

            wave:
                1 / 3

            for wave in WAVES

        }


    return {

        wave:
            result[wave]
            / total

        for wave in WAVES

    }


# =========================================================
# 双推
# =========================================================

def wave_double_pick(
    probabilities
):

    ranking = sorted(

        probabilities.items(),

        key=lambda item:
            item[1],

        reverse=True

    )


    if len(ranking) < 2:

        return []


    return [

        ranking[0][0],

        ranking[1][0],

    ]


# =========================================================
# 单推
# =========================================================

def wave_single_pick(
    probabilities
):

    if not probabilities:

        return None


    return max(

        probabilities,

        key=probabilities.get

    )


# =========================================================
# 完整波色报告
# =========================================================

def build_wave_report(
    rows
):

    probabilities = (
        wave_probabilities(
            rows
        )
    )


    single = wave_single_pick(
        probabilities
    )


    double = wave_double_pick(
        probabilities
    )


    streak = current_wave_streak(
        rows
    )


    return {

        "probabilities":
            probabilities,

        "single":
            single,

        "double":
            double,

        "previous":
            previous_wave(
                rows
            ),

        "streak":
            streak,

        "entropy":
            wave_entropy(
                rows[:36]
            ),

        "transition":
            wave_transition_probability(
                rows[:120]
            ),

    }