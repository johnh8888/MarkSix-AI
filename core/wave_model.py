# -*- coding: utf-8 -*-

"""
六合彩 V3.0 波色模型

功能：

1. 波色基础统计
2. 动态 12 / 36 / 120 窗口
3. 波色转移矩阵
4. 连续波色
5. 反转概率
6. 波色熵
7. 近期偏离程度
8. 波色单推
9. 波色双推
10. 兼容 strategies.py / predictor.py

红 / 蓝 / 绿采用香港六合彩标准波色。
"""

from collections import Counter
from math import log2
from typing import Any, Dict, List, Tuple


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


WAVES = (
    "红",
    "蓝",
    "绿",
)


# =========================================================
# 号码 → 波色
# =========================================================

NUMBER_TO_WAVE = {}

for n in RED:
    NUMBER_TO_WAVE[n] = "红"

for n in BLUE:
    NUMBER_TO_WAVE[n] = "蓝"

for n in GREEN:
    NUMBER_TO_WAVE[n] = "绿"


# =========================================================
# 获取波色
# =========================================================

def get_wave(number: int) -> str:

    try:
        number = int(number)
    except (TypeError, ValueError):
        return "未知"

    return NUMBER_TO_WAVE.get(
        number,
        "未知"
    )


# =========================================================
# 从 row 获取特码
# =========================================================

def get_special(row: Any) -> int:

    if row is None:
        return 0

    # -----------------------------------------------------
    # 优先 special
    # -----------------------------------------------------

    try:

        value = row.get("special")

        if value is not None:

            n = int(value)

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

        try:
            numbers = row["numbers"]
        except Exception:
            return 0

    if numbers is None:
        return 0

    if isinstance(numbers, str):

        text = (
            numbers
            .replace("，", ",")
            .replace("|", ",")
            .replace(" ", ",")
        )

        parts = [
            x.strip()
            for x in text.split(",")
            if x.strip()
        ]

        numbers = parts

    if isinstance(numbers, (list, tuple)):

        if len(numbers) >= 7:

            try:
                n = int(numbers[6])

                if 1 <= n <= 49:
                    return n

            except Exception:
                pass

    return 0


# =========================================================
# 获取历史波色序列
#
# rows:
# 最新 → 最旧
# =========================================================

def extract_wave_history(
    rows: List[Dict[str, Any]],
    limit: int = None
) -> List[str]:

    if not rows:
        return []

    if limit is not None:
        rows = rows[:limit]

    result = []

    for row in rows:

        n = get_special(row)

        wave = get_wave(n)

        if wave in WAVES:
            result.append(wave)

    return result


# =========================================================
# 基础波色统计
# =========================================================

def wave_counts(
    rows: List[Dict[str, Any]],
    limit: int = None
) -> Dict[str, int]:

    waves = extract_wave_history(
        rows,
        limit
    )

    counter = Counter(waves)

    return {
        wave: counter.get(wave, 0)
        for wave in WAVES
    }


# =========================================================
# 平滑概率
# =========================================================

def smoothed_probabilities(
    counts: Dict[str, int],
    alpha: float = 1.0
) -> Dict[str, float]:

    total = sum(
        counts.get(w, 0)
        for w in WAVES
    )

    denominator = (
        total +
        alpha * len(WAVES)
    )

    if denominator <= 0:
        return {
            w: 1.0 / 3.0
            for w in WAVES
        }

    return {
        w:
        (
            counts.get(w, 0) +
            alpha
        ) / denominator

        for w in WAVES
    }


# =========================================================
# 单纯历史概率
# =========================================================

def wave_frequency(
    rows: List[Dict[str, Any]],
    limit: int = None
) -> Dict[str, float]:

    counts = wave_counts(
        rows,
        limit
    )

    return smoothed_probabilities(
        counts
    )


# =========================================================
# 动态窗口波色概率
# =========================================================

def dynamic_wave_probabilities(
    rows: List[Dict[str, Any]]
) -> Dict[str, Any]:

    windows = {
        "short": 12,
        "medium": 36,
        "long": 120,
    }

    result = {}

    for name, window in windows.items():

        result[name] = wave_frequency(
            rows,
            window
        )

    # -----------------------------------------------------
    # 默认状态权重
    # -----------------------------------------------------

    weights = {
        "short": 0.35,
        "medium": 0.35,
        "long": 0.30,
    }

    final = {
        wave: 0.0
        for wave in WAVES
    }

    for window, probability in result.items():

        weight = weights[window]

        for wave in WAVES:

            final[wave] += (
                probability[wave] *
                weight
            )

    return {
        "windows": result,
        "weights": weights,
        "probabilities": normalize_probability(
            final
        ),
    }


# =========================================================
# 概率归一化
# =========================================================

def normalize_probability(
    values: Dict[str, float]
) -> Dict[str, float]:

    cleaned = {}

    for key in WAVES:

        try:
            value = float(
                values.get(key, 0)
            )
        except Exception:
            value = 0.0

        if value < 0:
            value = 0.0

        cleaned[key] = value

    total = sum(
        cleaned.values()
    )

    if total <= 0:

        return {
            w: 1.0 / 3.0
            for w in WAVES
        }

    return {
        w:
        cleaned[w] / total

        for w in WAVES
    }


# =========================================================
# 波色转移矩阵
#
# 当前 → 下一期
# =========================================================

def transition_matrix(
    rows: List[Dict[str, Any]],
    limit: int = 120
) -> Dict[str, Dict[str, float]]:

    waves = extract_wave_history(
        rows,
        limit
    )

    result = {}

    for current in WAVES:

        counter = Counter()

        for i in range(
            len(waves) - 1
        ):

            # rows 是最新 → 最旧
            # 因此 i+1 是上一期
            newer = waves[i]
            older = waves[i + 1]

            if older == current:

                counter[newer] += 1

        total = sum(
            counter.values()
        )

        if total <= 0:

            result[current] = {
                w: 1.0 / 3.0
                for w in WAVES
            }

        else:

            result[current] = {
                w:
                (
                    counter.get(w, 0) + 1
                ) / (
                    total + 3
                )

                for w in WAVES
            }

    return result


# =========================================================
# 上一期波色
# =========================================================

def latest_wave(
    rows: List[Dict[str, Any]]
) -> str:

    if not rows:
        return "未知"

    n = get_special(
        rows[0]
    )

    return get_wave(n)


# =========================================================
# 连续长度
# =========================================================

def wave_streak(
    rows: List[Dict[str, Any]]
) -> int:

    waves = extract_wave_history(
        rows,
        120
    )

    if not waves:
        return 0

    first = waves[0]

    count = 0

    for wave in waves:

        if wave == first:
            count += 1
        else:
            break

    return count


# =========================================================
# 反转概率
# =========================================================

def reversal_probability(
    rows: List[Dict[str, Any]],
    limit: int = 120
) -> float:

    waves = extract_wave_history(
        rows,
        limit
    )

    if len(waves) < 2:
        return 1.0 / 3.0

    reverse_count = 0
    total = 0

    for i in range(
        len(waves) - 1
    ):

        if waves[i] != waves[i + 1]:

            reverse_count += 1

        total += 1

    return (
        reverse_count / total
        if total
        else 1.0 / 3.0
    )


# =========================================================
# 波色熵
# =========================================================

def wave_entropy(
    rows: List[Dict[str, Any]],
    limit: int = 36
) -> float:

    probabilities = wave_frequency(
        rows,
        limit
    )

    entropy = 0.0

    for wave in WAVES:

        p = probabilities[wave]

        if p > 0:

            entropy -= (
                p *
                log2(p)
            )

    # 最大熵 = log2(3)
    max_entropy = log2(3)

    if max_entropy <= 0:
        return 0.0

    return entropy / max_entropy


# =========================================================
# 近期偏离
# =========================================================

def wave_deviation(
    rows: List[Dict[str, Any]],
    limit: int = 12
) -> Dict[str, float]:

    probability = wave_frequency(
        rows,
        limit
    )

    baseline = 1.0 / 3.0

    return {
        wave:
        probability[wave] -
        baseline

        for wave in WAVES
    }


# =========================================================
# 核心波色预测
# =========================================================

def wave_probabilities(
    rows: List[Dict[str, Any]]
) -> Dict[str, float]:

    """
    V3.0 对外统一接口。

    这个函数专门解决：

        strategies.py
            ↓
        wave_model.py

    的接口问题。
    """

    dynamic = dynamic_wave_probabilities(
        rows
    )

    probabilities = dict(
        dynamic["probabilities"]
    )

    # -----------------------------------------------------
    # 转移矩阵
    # -----------------------------------------------------

    last_wave = latest_wave(
        rows
    )

    matrix = transition_matrix(
        rows
    )

    transition = matrix.get(
        last_wave
    )

    if transition:

        # 历史概率 70%
        # 转移概率 30%
        for wave in WAVES:

            probabilities[wave] = (
                probabilities[wave] * 0.70
                +
                transition[wave] * 0.30
            )

    return normalize_probability(
        probabilities
    )


# =========================================================
# 波色单推
# =========================================================

def wave_single_pick(
    rows: List[Dict[str, Any]]
) -> str:

    probabilities = wave_probabilities(
        rows
    )

    return max(
        probabilities,
        key=probabilities.get
    )


# =========================================================
# 波色双推
# =========================================================

def wave_double_pick(
    rows: List[Dict[str, Any]]
) -> List[str]:

    probabilities = wave_probabilities(
        rows
    )

    ordered = sorted(
        WAVES,
        key=lambda x:
        probabilities[x],
        reverse=True
    )

    return ordered[:2]


# =========================================================
# 完整波色模型
# =========================================================

def analyze_wave(
    rows: List[Dict[str, Any]]
) -> Dict[str, Any]:

    probabilities = wave_probabilities(
        rows
    )

    ordered = sorted(
        WAVES,
        key=lambda x:
        probabilities[x],
        reverse=True
    )

    return {

        "probabilities":
            probabilities,

        "single":
            ordered[0],

        "double":
            ordered[:2],

        "latest":
            latest_wave(rows),

        "streak":
            wave_streak(rows),

        "reversal_probability":
            reversal_probability(rows),

        "entropy":
            wave_entropy(rows),

        "deviation":
            wave_deviation(rows),

        "transition":
            transition_matrix(rows),

        "dynamic":
            dynamic_wave_probabilities(
                rows
            ),
    }


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
                "01,12,19,24,30,35,46"
        },

        {
            "numbers":
                "05,11,17,22,38,43,49"
        },

    ]

    print(
        "=" * 70
    )

    print(
        "V3.0 波色模型测试"
    )

    print(
        "=" * 70
    )

    print(
        "NUMBER_TO_WAVE：",
        len(NUMBER_TO_WAVE)
    )

    print(
        "波色概率：",
        wave_probabilities(
            test_rows
        )
    )

    print(
        "波色单推：",
        wave_single_pick(
            test_rows
        )
    )

    print(
        "波色双推：",
        wave_double_pick(
            test_rows
        )
    )

    print(
        "完整分析：",
        analyze_wave(
            test_rows
        )
    )