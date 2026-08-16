# -*- coding: utf-8 -*-

"""
六合彩 V3.0 波色模型

功能：

1. 基础波色概率
2. 近期波色概率
3. 波色转移矩阵
4. 连续波色
5. 反转概率
6. 波色熵
7. 波色单推
8. 波色双推

特别注意：

本模块所有函数都可以被 strategies.py 调用。
避免 V2/V3 接口不一致。
"""

from collections import Counter
from math import log2
from typing import Dict, List, Any


# =========================================================
# 波色定义
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


WAVES = ["红", "蓝", "绿"]


# =========================================================
# 获取特码
# =========================================================

def get_special(row: Any) -> int:

    if row is None:
        return 0

    try:
        numbers = row.get("numbers", [])
    except AttributeError:
        try:
            numbers = row["numbers"]
        except Exception:
            return 0

    if isinstance(numbers, str):

        numbers = (
            numbers
            .replace("，", ",")
            .replace("|", ",")
            .split(",")
        )

    try:

        numbers = [
            int(str(x).strip())
            for x in numbers
            if str(x).strip()
        ]

    except Exception:
        return 0

    if len(numbers) >= 7:
        return numbers[6]

    return 0


# =========================================================
# 获取波色
# =========================================================

def get_wave(number: int) -> str:

    try:
        number = int(number)
    except Exception:
        return "未知"

    return NUMBER_TO_WAVE.get(
        number,
        "未知"
    )


# =========================================================
# 从历史记录获取波色序列
# =========================================================

def get_wave_sequence(
    rows: List[Dict[str, Any]]
) -> List[str]:

    result = []

    for row in rows:

        number = get_special(row)

        wave = get_wave(number)

        if wave in WAVES:
            result.append(wave)

    return result


# =========================================================
# 基础波色统计
# =========================================================

def wave_frequency(
    rows: List[Dict[str, Any]],
    window: int = None
) -> Dict[str, int]:

    if window is not None:
        rows = rows[:window]

    counter = Counter()

    for wave in get_wave_sequence(rows):

        counter[wave] += 1

    return {
        wave: counter.get(wave, 0)
        for wave in WAVES
    }


# =========================================================
# 概率归一化
# =========================================================

def normalize_probabilities(
    values: Dict[str, float]
) -> Dict[str, float]:

    total = sum(
        max(0.0, float(v))
        for v in values.values()
    )

    if total <= 0:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    return {
        wave:
            max(
                0.0,
                float(values.get(wave, 0.0))
            ) / total

        for wave in WAVES
    }


# =========================================================
# 基础波色概率
# =========================================================

def base_wave_probabilities(
    rows: List[Dict[str, Any]],
    window: int = None
) -> Dict[str, float]:

    counts = wave_frequency(
        rows,
        window
    )

    # Laplace smoothing
    smoothed = {
        wave:
            counts.get(wave, 0) + 1.0

        for wave in WAVES
    }

    return normalize_probabilities(
        smoothed
    )


# =========================================================
# 近期波色概率
# =========================================================

def recent_wave_probabilities(
    rows: List[Dict[str, Any]],
    window: int = 12
) -> Dict[str, float]:

    rows = rows[:window]

    if not rows:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    counts = wave_frequency(
        rows
    )

    # 近期增加轻微权重
    weighted = {
        wave:
            counts.get(wave, 0) + 1.0

        for wave in WAVES
    }

    return normalize_probabilities(
        weighted
    )


# =========================================================
# 波色转移矩阵
# =========================================================

def wave_transition_matrix(
    rows: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:

    sequence = get_wave_sequence(rows)

    matrix = {
        source: {
            target: 1.0
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

    # rows 最新 -> 最旧
    #
    # 所以：
    #
    # sequence[i+1] = 上一期
    # sequence[i]   = 下一期

    for i in range(
        len(sequence) - 1
    ):

        current = sequence[i]

        previous = sequence[i + 1]

        if (
            current in WAVES
            and previous in WAVES
        ):

            counts[
                previous
            ][
                current
            ] += 1

    for source in WAVES:

        total = sum(
            counts[source].values()
        )

        if total <= 0:

            matrix[source] = {
                target: 1.0 / 3.0
                for target in WAVES
            }

        else:

            matrix[source] = {
                target:
                    (
                        counts[source][target]
                        + 1.0
                    )
                    /
                    (
                        total
                        + 3.0
                    )

                for target in WAVES
            }

    return matrix


# =========================================================
# 转移概率
# =========================================================

def transition_probabilities(
    rows: List[Dict[str, Any]]
) -> Dict[str, float]:

    sequence = get_wave_sequence(rows)

    if not sequence:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    last_wave = sequence[0]

    matrix = wave_transition_matrix(
        rows
    )

    return normalize_probabilities(
        matrix.get(
            last_wave,
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
    rows: List[Dict[str, Any]]
) -> Dict[str, int]:

    sequence = get_wave_sequence(rows)

    if not sequence:
        return {
            wave: 0
            for wave in WAVES
        }

    current = sequence[0]

    streak = 0

    for wave in sequence:

        if wave == current:
            streak += 1
        else:
            break

    return {
        wave:
            streak if wave == current else 0

        for wave in WAVES
    }


# =========================================================
# 反转概率
# =========================================================

def reversal_probabilities(
    rows: List[Dict[str, Any]]
) -> Dict[str, float]:

    sequence = get_wave_sequence(rows)

    if len(sequence) < 2:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    counts = Counter()

    total = 0

    for i in range(
        len(sequence) - 1
    ):

        current = sequence[i]

        previous = sequence[i + 1]

        if current != previous:

            counts[current] += 1
            total += 1

    if total == 0:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    return normalize_probabilities({
        wave:
            counts.get(wave, 0) + 1

        for wave in WAVES
    })


# =========================================================
# 波色熵
# =========================================================

def wave_entropy(
    rows: List[Dict[str, Any]],
    window: int = 36
) -> float:

    sequence = get_wave_sequence(
        rows[:window]
    )

    if not sequence:
        return 0.0

    counts = Counter(sequence)

    total = len(sequence)

    entropy = 0.0

    for wave in WAVES:

        count = counts.get(
            wave,
            0
        )

        if count <= 0:
            continue

        p = count / total

        entropy -= p * log2(p)

    # 最大熵 log2(3)
    max_entropy = log2(3)

    if max_entropy <= 0:
        return 0.0

    return entropy / max_entropy


# =========================================================
# 综合波色概率
# =========================================================

def wave_probabilities(
    rows: List[Dict[str, Any]],
    short_window: int = 12,
    medium_window: int = 36,
    long_window: int = 120
) -> Dict[str, float]:

    short = recent_wave_probabilities(
        rows,
        short_window
    )

    medium = base_wave_probabilities(
        rows,
        medium_window
    )

    long = base_wave_probabilities(
        rows,
        long_window
    )

    transition = transition_probabilities(
        rows
    )

    entropy = wave_entropy(
        rows,
        medium_window
    )

    # -----------------------------------------------------
    # 正常情况下
    # -----------------------------------------------------

    weights = {
        "short": 0.40,
        "medium": 0.30,
        "long": 0.15,
        "transition": 0.15,
    }

    # -----------------------------------------------------
    # 熵较低：
    # 波色分布比较集中
    #
    # 增加短期和转移
    # -----------------------------------------------------

    if entropy < 0.80:

        weights = {
            "short": 0.45,
            "medium": 0.25,
            "long": 0.10,
            "transition": 0.20,
        }

    # -----------------------------------------------------
    # 熵较高：
    # 接近均匀
    #
    # 增加中长期
    # -----------------------------------------------------

    elif entropy > 0.95:

        weights = {
            "short": 0.30,
            "medium": 0.30,
            "long": 0.25,
            "transition": 0.15,
        }

    result = {}

    for wave in WAVES:

        result[wave] = (

            short[wave]
            * weights["short"]

            +

            medium[wave]
            * weights["medium"]

            +

            long[wave]
            * weights["long"]

            +

            transition[wave]
            * weights["transition"]
        )

    return normalize_probabilities(
        result
    )


# =========================================================
# 波色单推
# =========================================================

def wave_single_pick(
    probabilities: Dict[str, float]
) -> str:

    return max(
        probabilities,
        key=probabilities.get
    )


# =========================================================
# 波色双推
# =========================================================

def wave_double_pick(
    probabilities: Dict[str, float]
) -> List[str]:

    ordered = sorted(
        probabilities.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        wave
        for wave, _ in ordered[:2]
    ]


# =========================================================
# 综合模型
# =========================================================

def build_wave_model(
    rows: List[Dict[str, Any]]
) -> Dict[str, Any]:

    probabilities = wave_probabilities(
        rows
    )

    single = wave_single_pick(
        probabilities
    )

    double = wave_double_pick(
        probabilities
    )

    sequence = get_wave_sequence(
        rows
    )

    streak = wave_streak(
        rows
    )

    entropy = wave_entropy(
        rows
    )

    transition = transition_probabilities(
        rows
    )

    return {

        "probabilities":
            probabilities,

        "single":
            single,

        "double":
            double,

        "sequence":
            sequence[:12],

        "streak":
            streak,

        "entropy":
            round(
                entropy,
                6
            ),

        "transition":
            transition,
    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    rows = [

        {
            "numbers":
                [23, 1, 5, 8, 12, 20, 23]
        },

        {
            "numbers":
                [12, 3, 8, 15, 22, 30, 38]
        },

        {
            "numbers":
                [8, 4, 10, 16, 21, 28, 46]
        },

    ]

    print(
        build_wave_model(rows)
    )