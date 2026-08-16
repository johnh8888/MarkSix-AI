# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
波色独立模型

功能：

1. 红/蓝/绿基础频率
2. 12 / 36 / 120 动态窗口
3. 波色转移矩阵
4. 上一期波色
5. 连续波色
6. 反转
7. 非反转
8. 波色熵
9. 近期偏离程度
10. 波色单推
11. 波色双推
12. 波色概率
13. 与 strategies.py 兼容

注意：

本模块用于统计建模与历史回测，
不代表下一期开奖可以被确定预测。
"""

from collections import Counter
import math
from typing import Dict, List, Any, Tuple


# =========================================================
# 常量
# =========================================================

WAVES = (
    "红",
    "蓝",
    "绿",
)


# =========================================================
# 波色号码
# =========================================================

RED = {
    1, 2, 7, 8, 12, 13,
    18, 19, 23, 24, 29,
    30, 34, 35, 40, 45,
    46
}


BLUE = {
    3, 4, 9, 10, 14, 15,
    20, 25, 26, 31, 36,
    37, 41, 42, 47, 48
}


GREEN = {
    5, 6, 11, 16, 17,
    21, 22, 27, 28, 32,
    33, 38, 39, 43, 44,
    49
}


NUMBER_TO_WAVE = {}

for n in RED:
    NUMBER_TO_WAVE[n] = "红"

for n in BLUE:
    NUMBER_TO_WAVE[n] = "蓝"

for n in GREEN:
    NUMBER_TO_WAVE[n] = "绿"


# =========================================================
# 基础工具
# =========================================================

def safe_special(row) -> int:

    """
    从数据库 row 中读取特码。

    兼容：

    numbers = [33,27,...,14]

    numbers = "33,27,...,14"

    special = 14
    """

    if row is None:
        return 0

    # -----------------------------------------------------
    # 优先读取 special
    # -----------------------------------------------------

    try:

        special = row.get("special")

        if special is not None:

            n = int(special)

            if 1 <= n <= 49:
                return n

    except Exception:
        pass

    # -----------------------------------------------------
    # numbers
    # -----------------------------------------------------

    try:
        numbers = row.get("numbers")
    except Exception:
        numbers = None

    if numbers is None:
        return 0

    if isinstance(numbers, (list, tuple)):

        if len(numbers) >= 7:

            try:

                n = int(
                    str(
                        numbers[-1]
                    ).strip()
                )

                if 1 <= n <= 49:
                    return n

            except Exception:
                pass

        return 0

    if isinstance(numbers, str):

        text = (
            numbers
            .strip()
            .replace("，", ",")
        )

        parts = [
            x.strip()
            for x in text.split(",")
            if x.strip()
        ]

        if len(parts) >= 7:

            try:

                n = int(parts[-1])

                if 1 <= n <= 49:
                    return n

            except Exception:
                pass

    return 0


# =========================================================
# 号码 → 波色
# =========================================================

def number_to_wave(
    number: int
) -> str:

    try:

        n = int(number)

    except Exception:

        return "未知"

    return NUMBER_TO_WAVE.get(
        n,
        "未知"
    )


# =========================================================
# rows → 波色序列
# =========================================================

def get_wave_sequence(
    rows
) -> List[str]:

    sequence = []

    for row in rows:

        n = safe_special(row)

        wave = number_to_wave(n)

        if wave in WAVES:

            sequence.append(wave)

    return sequence


# =========================================================
# 波色频率
# =========================================================

def wave_frequency(
    rows
) -> Dict[str, int]:

    counter = Counter(
        get_wave_sequence(rows)
    )

    return {
        wave: counter.get(wave, 0)
        for wave in WAVES
    }


# =========================================================
# 波色概率
# =========================================================

def wave_probabilities(
    rows,
    window: int = 36
) -> Dict[str, float]:

    """
    V3.0 核心接口。

    strategies.py 会直接调用：

        wave_probabilities(rows)

    返回：

        {
            "红": 0.xx,
            "蓝": 0.xx,
            "绿": 0.xx
        }
    """

    data = rows[:window]

    sequence = get_wave_sequence(data)

    if not sequence:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    counter = Counter(sequence)

    total = sum(
        counter.values()
    )

    if total <= 0:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    probabilities = {

        wave:
            counter.get(
                wave,
                0
            ) / total

        for wave in WAVES
    }

    return probabilities


# =========================================================
# 动态多窗口概率
# =========================================================

def dynamic_wave_probabilities(
    rows
) -> Dict[str, float]:

    """
    12 / 36 / 120 动态窗口。

    默认权重：

        12期  50%
        36期  30%
        120期 20%

    实际状态调整在上层模型完成。
    """

    p12 = wave_probabilities(
        rows,
        12
    )

    p36 = wave_probabilities(
        rows,
        36
    )

    p120 = wave_probabilities(
        rows,
        120
    )

    result = {}

    for wave in WAVES:

        result[wave] = (

            p12[wave] * 0.50

            +

            p36[wave] * 0.30

            +

            p120[wave] * 0.20
        )

    total = sum(
        result.values()
    )

    if total <= 0:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    return {
        wave:
            result[wave] / total

        for wave in WAVES
    }


# =========================================================
# 波色转移矩阵
# =========================================================

def wave_transition_matrix(
    rows
) -> Dict[str, Dict[str, float]]:

    """
    计算：

        红 → 红/蓝/绿
        蓝 → 红/蓝/绿
        绿 → 红/蓝/绿
    """

    sequence = get_wave_sequence(
        rows
    )

    matrix = {

        wave: {
            target: 0.0
            for target in WAVES
        }

        for wave in WAVES
    }

    counts = {

        wave: Counter()
        for wave in WAVES
    }

    if len(sequence) < 2:

        return {

            wave: {
                target: 1.0 / 3.0
                for target in WAVES
            }

            for wave in WAVES
        }

    for i in range(
        len(sequence) - 1
    ):

        current = sequence[i]

        next_wave = sequence[i + 1]

        if (
            current in WAVES
            and
            next_wave in WAVES
        ):

            counts[current][
                next_wave
            ] += 1

    for wave in WAVES:

        total = sum(
            counts[wave].values()
        )

        if total <= 0:

            matrix[wave] = {

                target: 1.0 / 3.0

                for target in WAVES
            }

        else:

            matrix[wave] = {

                target:
                    counts[wave].get(
                        target,
                        0
                    ) / total

                for target in WAVES
            }

    return matrix


# =========================================================
# 上一期波色预测
# =========================================================

def previous_wave_prediction(
    rows
) -> Dict[str, float]:

    sequence = get_wave_sequence(
        rows
    )

    if not sequence:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    previous = sequence[0]

    matrix = wave_transition_matrix(
        rows
    )

    return dict(
        matrix.get(
            previous,
            {
                wave: 1.0 / 3.0
                for wave in WAVES
            }
        )
    )


# =========================================================
# 连续波色
# =========================================================

def wave_streak(
    rows
) -> Tuple[str, int]:

    sequence = get_wave_sequence(
        rows
    )

    if not sequence:

        return (
            "未知",
            0
        )

    current = sequence[0]

    streak = 1

    for wave in sequence[1:]:

        if wave == current:

            streak += 1

        else:

            break

    return (
        current,
        streak
    )


# =========================================================
# 连续状态调整
# =========================================================

def streak_adjustment(
    rows
) -> Dict[str, float]:

    probabilities = {
        wave: 1.0 / 3.0
        for wave in WAVES
    }

    current, streak = wave_streak(
        rows
    )

    if current not in WAVES:

        return probabilities

    # -----------------------------------------------------
    # 连续2期
    # -----------------------------------------------------

    if streak == 2:

        probabilities[current] += 0.015

    # -----------------------------------------------------
    # 连续3期
    # -----------------------------------------------------

    elif streak == 3:

        probabilities[current] -= 0.025

        for wave in WAVES:

            if wave != current:
                probabilities[wave] += 0.0125

    # -----------------------------------------------------
    # 连续4期+
    # -----------------------------------------------------

    elif streak >= 4:

        probabilities[current] -= 0.045

        for wave in WAVES:

            if wave != current:
                probabilities[wave] += 0.0225

    # -----------------------------------------------------
    # 防止负数
    # -----------------------------------------------------

    probabilities = {

        wave:
            max(
                0.001,
                value
            )

        for wave, value
        in probabilities.items()
    }

    total = sum(
        probabilities.values()
    )

    return {

        wave:
            probabilities[wave] / total

        for wave in WAVES
    }


# =========================================================
# 反转模型
# =========================================================

def reversal_probabilities(
    rows
) -> Dict[str, float]:

    sequence = get_wave_sequence(
        rows
    )

    if len(sequence) < 2:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    matrix = wave_transition_matrix(
        rows
    )

    previous = sequence[0]

    transition = matrix.get(
        previous,
        {
            wave: 1.0 / 3.0
            for wave in WAVES
        }
    )

    same_probability = transition.get(
        previous,
        0.0
    )

    result = dict(
        transition
    )

    # 如果历史同色概率偏低，
    # 反转模型提高非同色结果。
    if same_probability < 0.34:

        result[previous] *= 0.85

    elif same_probability > 0.50:

        result[previous] *= 1.05

    total = sum(
        result.values()
    )

    if total <= 0:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    return {

        wave:
            result[wave] / total

        for wave in WAVES
    }


# =========================================================
# 波色熵
# =========================================================

def wave_entropy(
    rows,
    window: int = 36
) -> float:

    probabilities = wave_probabilities(
        rows,
        window
    )

    entropy = 0.0

    for probability in probabilities.values():

        if probability > 0:

            entropy -= (
                probability
                *
                math.log(
                    probability,
                    3
                )
            )

    return max(
        0.0,
        min(
            1.0,
            entropy
        )
    )


# =========================================================
# 波色偏离程度
# =========================================================

def wave_deviation(
    rows,
    window: int = 36
) -> Dict[str, float]:

    probabilities = wave_probabilities(
        rows,
        window
    )

    expected = 1.0 / 3.0

    return {

        wave:
            probabilities[wave]
            - expected

        for wave in WAVES
    }


# =========================================================
# 波色综合模型
# =========================================================

def combined_wave_model(
    rows
) -> Dict[str, Any]:

    base = dynamic_wave_probabilities(
        rows
    )

    transition = previous_wave_prediction(
        rows
    )

    streak = streak_adjustment(
        rows
    )

    reversal = reversal_probabilities(
        rows
    )

    # -----------------------------------------------------
    # 综合
    # -----------------------------------------------------

    result = {}

    for wave in WAVES:

        result[wave] = (

            base[wave] * 0.40

            +

            transition[wave] * 0.30

            +

            streak[wave] * 0.15

            +

            reversal[wave] * 0.15
        )

    # -----------------------------------------------------
    # 归一化
    # -----------------------------------------------------

    total = sum(
        result.values()
    )

    if total <= 0:

        result = {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    else:

        result = {

            wave:
                result[wave] / total

            for wave in WAVES
        }

    # -----------------------------------------------------
    # 排名
    # -----------------------------------------------------

    ranking = sorted(

        result.items(),

        key=lambda x: x[1],

        reverse=True
    )

    single_pick = ranking[0][0]

    double_pick = [
        ranking[0][0],
        ranking[1][0],
    ]

    current_wave, streak_count = wave_streak(
        rows
    )

    return {

        "probabilities":
            result,

        "ranking":
            ranking,

        "single":
            single_pick,

        "double":
            double_pick,

        "current_wave":
            current_wave,

        "streak":
            streak_count,

        "entropy":
            wave_entropy(rows),

        "deviation":
            wave_deviation(rows),

        "transition":
            transition,

        "base":
            base,
    }


# =========================================================
# 波色单推
# =========================================================

def wave_single_pick(
    rows
) -> str:

    model = combined_wave_model(
        rows
    )

    return model["single"]


# =========================================================
# 波色双推
# =========================================================

def wave_double_pick(
    rows
) -> List[str]:

    model = combined_wave_model(
        rows
    )

    return model["double"]


# =========================================================
# 波色评分
#
# 提供给 strategies.py
# =========================================================

def wave_scores(
    rows
) -> Dict[str, float]:

    return combined_wave_model(
        rows
    )["probabilities"]


# =========================================================
# 兼容旧接口
# =========================================================

def strategy_wave(
    rows
) -> Dict[int, float]:

    """
    将波色概率映射回49个号码。

    这样旧版 strategies.py 也可以继续使用。
    """

    probabilities = combined_wave_model(
        rows
    )["probabilities"]

    scores = {}

    for number in range(
        1,
        50
    ):

        wave = NUMBER_TO_WAVE.get(
            number
        )

        scores[number] = probabilities.get(
            wave,
            1.0 / 3.0
        )

    # -----------------------------------------------------
    # 归一化到 0~1
    # -----------------------------------------------------

    values = list(
        scores.values()
    )

    low = min(values)
    high = max(values)

    if high > low:

        scores = {

            n:
                (
                    value - low
                )
                /
                (
                    high - low
                )

            for n, value
            in scores.items()
        }

    else:

        scores = {
            n: 0.5
            for n in scores
        }

    return scores


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    test_rows = [

        {
            "numbers":
                "38,26,08,06,29,18,23"
        },

        {
            "numbers":
                "33,27,16,28,04,25,14"
        },

        {
            "numbers":
                "47,14,44,32,07,37,11"
        },

        {
            "numbers":
                "21,09,15,34,42,18,49"
        },

        {
            "numbers":
                "02,13,27,31,40,06,08"
        },

    ]

    print("=" * 70)

    print(
        "六合彩 AI V3.0 波色模型测试"
    )

    print("=" * 70)

    print()

    print(
        "波色序列："
    )

    print(
        get_wave_sequence(
            test_rows
        )
    )

    print()

    print(
        "基础概率："
    )

    print(
        wave_probabilities(
            test_rows,
            36
        )
    )

    print()

    print(
        "动态概率："
    )

    print(
        dynamic_wave_probabilities(
            test_rows
        )
    )

    print()

    print(
        "转移矩阵："
    )

    for wave, values in wave_transition_matrix(
        test_rows
    ).items():

        print(
            wave,
            values
        )

    print()

    model = combined_wave_model(
        test_rows
    )

    print(
        "综合概率："
    )

    for wave, probability in model[
        "probabilities"
    ].items():

        print(
            f"{wave}："
            f"{probability:.4f}"
        )

    print()

    print(
        "波色单推：",
        model["single"]
    )

    print(
        "波色双推：",
        " + ".join(
            model["double"]
        )
    )

    print()

    print(
        "当前连续：",
        model["current_wave"],
        model["streak"],
        "期"
    )

    print(
        "波色熵：",
        f"{model['entropy']:.4f}"
    )

    print("=" * 70)