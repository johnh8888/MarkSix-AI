# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
波色独立模型

核心：

1. 红 / 蓝 / 绿基础概率
2. 波色转移矩阵
3. 连续波色
4. 反转
5. 非反转
6. 波色熵
7. 近期波色趋势
8. 波色单推
9. 波色双推

特别注意：

波色预测与号码预测分离。

最终：

单推 = 概率最高颜色

双推 = 概率最高两个颜色
"""

from collections import Counter

from .features import (
    get_special,
    get_wave,
)

from .state_engine import (
    wave_entropy,
    wave_streak,
)


WAVES = (
    "红",
    "蓝",
    "绿",
)


# =========================================================
# 获取波色
# =========================================================

def safe_wave(row):

    try:

        n = int(
            get_special(row)
        )

        if 1 <= n <= 49:

            wave = get_wave(n)

            if wave in WAVES:
                return wave

    except Exception:
        pass

    return None


# =========================================================
# 波色序列
# =========================================================

def get_wave_sequence(rows):

    result = []

    for row in rows:

        wave = safe_wave(row)

        if wave:
            result.append(wave)

    return result


# =========================================================
# 基础波色概率
# =========================================================

def base_wave_probability(rows):

    sequence = get_wave_sequence(
        rows
    )

    if not sequence:

        return {
            wave: 1 / 3
            for wave in WAVES
        }

    counter = Counter(
        sequence
    )

    total = len(sequence)

    # Laplace smoothing
    alpha = 1.0

    denominator = (
        total
        + alpha * 3
    )

    return {

        wave:
            (
                counter.get(
                    wave,
                    0
                )
                + alpha
            )
            / denominator

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

        current: {
            target: 1 / 3
            for target in WAVES
        }

        for current in WAVES
    }

    counts = {

        current: {
            target: 0
            for target in WAVES
        }

        for current in WAVES
    }

    if len(sequence) < 2:
        return matrix

    for i in range(
        len(sequence) - 1
    ):

        current = sequence[i]
        target = sequence[i + 1]

        counts[
            current
        ][
            target
        ] += 1

    for current in WAVES:

        total = sum(
            counts[current].values()
        )

        denominator = (
            total + 3
        )

        for target in WAVES:

            matrix[current][target] = (
                counts[current][target]
                + 1
            ) / denominator

    return matrix


# =========================================================
# 当前波色
# =========================================================

def latest_wave(rows):

    sequence = get_wave_sequence(
        rows
    )

    if not sequence:
        return None

    return sequence[0]


# =========================================================
# 反转概率
# =========================================================

def reversal_probability(rows):

    sequence = get_wave_sequence(
        rows
    )

    if len(sequence) < 2:
        return 0.5

    reversal = 0
    total = 0

    for i in range(
        len(sequence) - 1
    ):

        total += 1

        if sequence[i] != sequence[i + 1]:
            reversal += 1

    if total <= 0:
        return 0.5

    return reversal / total


# =========================================================
# 连续调整
# =========================================================

def streak_adjustment(
    rows
):

    streak_info = wave_streak(
        rows
    )

    wave = streak_info.get(
        "wave"
    )

    streak = streak_info.get(
        "streak",
        0
    )

    adjustment = {
        w: 1.0
        for w in WAVES
    }

    if wave not in WAVES:
        return adjustment

    # 连续越长，降低继续连续的权重
    if streak >= 4:

        adjustment[wave] *= 0.88

    elif streak == 3:

        adjustment[wave] *= 0.93

    elif streak == 2:

        adjustment[wave] *= 0.97

    return adjustment


# =========================================================
# 波色趋势
# =========================================================

def wave_trend(rows):

    short = get_wave_sequence(
        rows[:12]
    )

    medium = get_wave_sequence(
        rows[:36]
    )

    if not short or not medium:

        return {
            wave: 0.0
            for wave in WAVES
        }

    short_counter = Counter(
        short
    )

    medium_counter = Counter(
        medium
    )

    short_total = len(short)
    medium_total = len(medium)

    result = {}

    for wave in WAVES:

        short_rate = (
            short_counter.get(
                wave,
                0
            )
            / short_total
        )

        medium_rate = (
            medium_counter.get(
                wave,
                0
            )
            / medium_total
        )

        result[wave] = (
            short_rate
            - medium_rate
        )

    return result


# =========================================================
# 波色预测
# =========================================================

def predict_wave(
    rows
):

    rows = rows or []

    short_rows = rows[:12]
    medium_rows = rows[:36]
    long_rows = rows[:120]

    short_prob = base_wave_probability(
        short_rows
    )

    medium_prob = base_wave_probability(
        medium_rows
    )

    long_prob = base_wave_probability(
        long_rows
    )

    current = latest_wave(
        rows
    )

    matrix = transition_matrix(
        rows[:120]
    )

    reversal_prob = reversal_probability(
        rows[:120]
    )

    trend = wave_trend(
        rows
    )

    streak_adj = streak_adjustment(
        rows
    )

    # -----------------------------------------------------
    # 基础权重
    # -----------------------------------------------------

    scores = {}

    for wave in WAVES:

        score = (

            short_prob[wave]
            * 0.35

            +

            medium_prob[wave]
            * 0.30

            +

            long_prob[wave]
            * 0.20

            +

            max(
                0.0,
                0.5
                + trend[wave]
            )
            * 0.15
        )

        scores[wave] = score

    # -----------------------------------------------------
    # 转移
    # -----------------------------------------------------

    if current in WAVES:

        for wave in WAVES:

            transition = matrix[
                current
            ][
                wave
            ]

            scores[wave] = (
                scores[wave] * 0.70
                +
                transition * 0.30
            )

    # -----------------------------------------------------
    # 反转
    # -----------------------------------------------------

    if current in WAVES:

        for wave in WAVES:

            if wave != current:

                scores[wave] *= (
                    0.90
                    + 0.20
                    * reversal_prob
                )

            else:

                scores[wave] *= (
                    1.10
                    - 0.20
                    * reversal_prob
                )

    # -----------------------------------------------------
    # 连续调整
    # -----------------------------------------------------

    for wave in WAVES:

        scores[wave] *= (
            streak_adj[wave]
        )

    # -----------------------------------------------------
    # 归一化
    # -----------------------------------------------------

    total = sum(
        scores.values()
    )

    if total <= 0:

        probabilities = {
            wave: 1 / 3
            for wave in WAVES
        }

    else:

        probabilities = {

            wave:
                scores[wave] / total

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

        "single":
            single,

        "double":
            double,

        "ranking":
            ranking,

        "current":
            current,

        "reversal_probability":
            round(
                reversal_prob,
                4
            ),

        "streak":
            wave_streak(rows),

        "entropy":
            round(
                wave_entropy(
                    short_rows
                ),
                4
            ),

        "transition":
            matrix,
    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    print(
        predict_wave([])
    )