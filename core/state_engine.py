# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
状态识别引擎

功能：

1. 动态 12 / 36 / 120 窗口
2. 识别：
   - 正常
   - 趋势
   - 混沌
3. 计算短 / 中 / 长期权重
4. 分析号码集中度
5. 分析大小趋势
6. 分析单双趋势
7. 分析波色趋势
8. 分析遗漏波动
9. 输出统一状态结构

注意：

本模块只负责“市场状态识别”，
不直接生成特码预测。

六合彩本质上是随机开奖过程，
以下状态只用于模型权重调整，
不是对下一期结果的确定性判断。
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Dict, List


# =========================================================
# V3 动态窗口
# =========================================================

SHORT_WINDOW = 12
MEDIUM_WINDOW = 36
LONG_WINDOW = 120

STATE_WINDOW = 36


# =========================================================
# 波色映射
# =========================================================

WAVES = (
    "红",
    "蓝",
    "绿",
)


# 香港六合彩常用49码波色
# 这里统一供 V3 内部使用
NUMBER_TO_WAVE = {

    # 红波
    1: "红",
    2: "红",
    7: "红",
    8: "红",
    12: "红",
    13: "红",
    18: "红",
    19: "红",
    23: "红",
    24: "红",
    29: "红",
    30: "红",
    34: "红",
    35: "红",
    40: "红",
    45: "红",
    46: "红",

    # 蓝波
    3: "蓝",
    4: "蓝",
    9: "蓝",
    10: "蓝",
    14: "蓝",
    15: "蓝",
    20: "蓝",
    25: "蓝",
    26: "蓝",
    31: "蓝",
    36: "蓝",
    37: "蓝",
    41: "蓝",
    42: "蓝",
    47: "蓝",
    48: "蓝",

    # 绿波
    5: "绿",
    6: "绿",
    11: "绿",
    16: "绿",
    17: "绿",
    21: "绿",
    22: "绿",
    27: "绿",
    28: "绿",
    32: "绿",
    33: "绿",
    38: "绿",
    39: "绿",
    43: "绿",
    44: "绿",
    49: "绿",
}


# =========================================================
# 基础工具
# =========================================================

def clamp(
    value: float,
    low: float,
    high: float,
) -> float:

    return max(
        low,
        min(
            high,
            value,
        ),
    )


# =========================================================
# 安全转换
# =========================================================

def safe_int(
    value: Any,
) -> int | None:

    try:

        number = int(
            str(value).strip()
        )

        if 1 <= number <= 49:

            return number

    except (
        TypeError,
        ValueError,
    ):

        pass

    return None


# =========================================================
# 获取号码
# =========================================================

def get_numbers(
    row: Dict[str, Any],
) -> List[int]:

    numbers = row.get(
        "numbers",
        [],
    )

    if not isinstance(
        numbers,
        (list, tuple),
    ):

        return []

    result = []

    for value in numbers:

        number = safe_int(
            value
        )

        if number is not None:

            result.append(
                number
            )

    return result


# =========================================================
# 获取特码
# =========================================================

def get_special(
    row: Dict[str, Any],
) -> int | None:

    special = safe_int(
        row.get("special")
    )

    if special is not None:

        return special

    numbers = get_numbers(
        row
    )

    if len(numbers) >= 7:

        return numbers[-1]

    return None


# =========================================================
# 有效历史
# =========================================================

def valid_rows(
    rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    result = []

    for row in rows:

        if not isinstance(
            row,
            dict,
        ):

            continue

        special = get_special(
            row
        )

        if special is None:

            continue

        result.append(
            row
        )

    return result


# =========================================================
# 最近窗口
#
# rows 默认：
# 最新 → 最旧
# =========================================================

def get_window(
    rows: List[Dict[str, Any]],
    size: int,
) -> List[Dict[str, Any]]:

    data = valid_rows(
        rows
    )

    return data[
        :max(1, size)
    ]


# =========================================================
# 号码频率
# =========================================================

def number_frequency(
    rows: List[Dict[str, Any]],
) -> Counter:

    counter = Counter()

    for row in rows:

        special = get_special(
            row
        )

        if special is not None:

            counter[special] += 1

    return counter


# =========================================================
# 大小
#
# 1-24 = 小
# 25-49 = 大
# =========================================================

def classify_size(
    number: int,
) -> str:

    return (
        "小"
        if number <= 24
        else "大"
    )


# =========================================================
# 单双
# =========================================================

def classify_parity(
    number: int,
) -> str:

    return (
        "单"
        if number % 2 == 1
        else "双"
    )


# =========================================================
# 波色
# =========================================================

def classify_wave(
    number: int,
) -> str:

    return NUMBER_TO_WAVE.get(
        number,
        "未知",
    )


# =========================================================
# 分类比例
# =========================================================

def category_ratio(
    rows: List[Dict[str, Any]],
    classifier,
) -> Dict[str, float]:

    counter = Counter()

    total = 0

    for row in rows:

        special = get_special(
            row
        )

        if special is None:

            continue

        category = classifier(
            special
        )

        if category == "未知":

            continue

        counter[category] += 1

        total += 1

    if total == 0:

        return {}

    return {
        key: value / total
        for key, value in counter.items()
    }


# =========================================================
# 熵
#
# 越接近1：
# 分布越均匀 / 越混沌
#
# 越接近0：
# 越集中 / 趋势越明显
# =========================================================

def normalized_entropy(
    probabilities: List[float],
) -> float:

    probabilities = [
        p
        for p in probabilities
        if p > 0
    ]

    if len(probabilities) <= 1:

        return 0.0

    entropy = 0.0

    for probability in probabilities:

        entropy -= (
            probability
            * math.log(
                probability
            )
        )

    maximum = math.log(
        len(probabilities)
    )

    if maximum <= 0:

        return 0.0

    return clamp(
        entropy / maximum,
        0.0,
        1.0,
    )


# =========================================================
# 号码集中度
# =========================================================

def calculate_number_concentration(
    rows: List[Dict[str, Any]],
) -> float:

    counter = number_frequency(
        rows
    )

    total = sum(
        counter.values()
    )

    if total <= 0:

        return 0.0

    probabilities = [
        counter[number] / total
        for number in counter
    ]

    entropy = normalized_entropy(
        probabilities
    )

    return clamp(
        1.0 - entropy,
        0.0,
        1.0,
    )


# =========================================================
# 分类集中度
# =========================================================

def category_concentration(
    rows: List[Dict[str, Any]],
    classifier,
) -> float:

    ratios = category_ratio(
        rows,
        classifier,
    )

    if not ratios:

        return 0.0

    entropy = normalized_entropy(
        list(
            ratios.values()
        )
    )

    return clamp(
        1.0 - entropy,
        0.0,
        1.0,
    )


# =========================================================
# 最近连续趋势
# =========================================================

def consecutive_same_category(
    rows: List[Dict[str, Any]],
    classifier,
) -> int:

    data = valid_rows(
        rows
    )

    if not data:

        return 0

    first = get_special(
        data[0]
    )

    if first is None:

        return 0

    target = classifier(
        first
    )

    count = 0

    for row in data:

        special = get_special(
            row
        )

        if special is None:

            break

        category = classifier(
            special
        )

        if category != target:

            break

        count += 1

    return count


# =========================================================
# 波色连续
# =========================================================

def wave_streak(
    rows: List[Dict[str, Any]],
) -> int:

    return consecutive_same_category(
        rows,
        classify_wave,
    )


# =========================================================
# 大小连续
# =========================================================

def size_streak(
    rows: List[Dict[str, Any]],
) -> int:

    return consecutive_same_category(
        rows,
        classify_size,
    )


# =========================================================
# 单双连续
# =========================================================

def parity_streak(
    rows: List[Dict[str, Any]],
) -> int:

    return consecutive_same_category(
        rows,
        classify_parity,
    )


# =========================================================
# 短期与长期偏离
#
# 判断：
#
# 短期状态是否明显偏离长期平均
# =========================================================

def distribution_deviation(
    short_ratio: Dict[str, float],
    long_ratio: Dict[str, float],
) -> float:

    keys = set(
        short_ratio
    ) | set(
        long_ratio
    )

    if not keys:

        return 0.0

    difference = 0.0

    for key in keys:

        short_value = short_ratio.get(
            key,
            0.0,
        )

        long_value = long_ratio.get(
            key,
            0.0,
        )

        difference += abs(
            short_value
            - long_value
        )

    return clamp(
        difference / 2.0,
        0.0,
        1.0,
    )


# =========================================================
# 趋势分数
# =========================================================

def calculate_trend_score(
    rows: List[Dict[str, Any]],
) -> float:

    short_rows = get_window(
        rows,
        SHORT_WINDOW,
    )

    medium_rows = get_window(
        rows,
        MEDIUM_WINDOW,
    )

    long_rows = get_window(
        rows,
        LONG_WINDOW,
    )

    if not short_rows:

        return 0.0

    scores = []

    # -----------------------------------------------------
    # 大小趋势
    # -----------------------------------------------------

    short_size = category_ratio(
        short_rows,
        classify_size,
    )

    medium_size = category_ratio(
        medium_rows,
        classify_size,
    )

    long_size = category_ratio(
        long_rows,
        classify_size,
    )

    scores.append(
        distribution_deviation(
            short_size,
            long_size,
        )
    )

    scores.append(
        distribution_deviation(
            medium_size,
            long_size,
        )
    )

    # -----------------------------------------------------
    # 单双趋势
    # -----------------------------------------------------

    short_parity = category_ratio(
        short_rows,
        classify_parity,
    )

    medium_parity = category_ratio(
        medium_rows,
        classify_parity,
    )

    long_parity = category_ratio(
        long_rows,
        classify_parity,
    )

    scores.append(
        distribution_deviation(
            short_parity,
            long_parity,
        )
    )

    scores.append(
        distribution_deviation(
            medium_parity,
            long_parity,
        )
    )

    # -----------------------------------------------------
    # 波色趋势
    # -----------------------------------------------------

    short_wave = category_ratio(
        short_rows,
        classify_wave,
    )

    medium_wave = category_ratio(
        medium_rows,
        classify_wave,
    )

    long_wave = category_ratio(
        long_rows,
        classify_wave,
    )

    scores.append(
        distribution_deviation(
            short_wave,
            long_wave,
        )
    )

    scores.append(
        distribution_deviation(
            medium_wave,
            long_wave,
        )
    )

    if not scores:

        return 0.0

    return clamp(
        sum(scores) / len(scores),
        0.0,
        1.0,
    )


# =========================================================
# 混沌分数
# =========================================================

def calculate_chaos_score(
    rows: List[Dict[str, Any]],
) -> float:

    data = get_window(
        rows,
        STATE_WINDOW,
    )

    if len(data) < 6:

        return 0.5

    # -----------------------------------------------------
    # 波色熵
    # -----------------------------------------------------

    wave_ratio = category_ratio(
        data,
        classify_wave,
    )

    wave_entropy = normalized_entropy(
        list(
            wave_ratio.values()
        )
    ) if wave_ratio else 0.5

    # -----------------------------------------------------
    # 大小熵
    # -----------------------------------------------------

    size_ratio = category_ratio(
        data,
        classify_size,
    )

    size_entropy = normalized_entropy(
        list(
            size_ratio.values()
        )
    ) if size_ratio else 0.5

    # -----------------------------------------------------
    # 单双熵
    # -----------------------------------------------------

    parity_ratio = category_ratio(
        data,
        classify_parity,
    )

    parity_entropy = normalized_entropy(
        list(
            parity_ratio.values()
        )
    ) if parity_ratio else 0.5

    # -----------------------------------------------------
    # 号码集中度
    # -----------------------------------------------------

    concentration = calculate_number_concentration(
        data
    )

    # 号码越分散，混沌分数越高
    number_chaos = 1.0 - concentration

    chaos = (
        wave_entropy * 0.30
        + size_entropy * 0.20
        + parity_entropy * 0.20
        + number_chaos * 0.30
    )

    return clamp(
        chaos,
        0.0,
        1.0,
    )


# =========================================================
# 动态窗口权重
# =========================================================

def calculate_window_weights(
    state: str,
) -> Dict[str, float]:

    state = (
        state
        or "正常"
    )

    # -----------------------------------------------------
    # 趋势
    # -----------------------------------------------------

    if state == "趋势":

        return {

            "short":
                0.50,

            "medium":
                0.30,

            "long":
                0.20,
        }

    # -----------------------------------------------------
    # 混沌
    # -----------------------------------------------------

    if state == "混沌":

        return {

            "short":
                0.20,

            "medium":
                0.35,

            "long":
                0.45,
        }

    # -----------------------------------------------------
    # 正常
    # -----------------------------------------------------

    return {

        "short":
            0.35,

        "medium":
            0.35,

        "long":
            0.30,
    }


# =========================================================
# 主状态识别
# =========================================================

def detect_market_state(
    rows: List[Dict[str, Any]],
) -> Dict[str, Any]:

    data = valid_rows(
        rows
    )

    if len(data) < 12:

        return {

            "state":
                "正常",

            "confidence":
                0.35,

            "trend_score":
                0.0,

            "chaos_score":
                0.5,

            "window_weights":
                calculate_window_weights(
                    "正常"
                ),

            "sample_size":
                len(data),
        }

    trend_score = calculate_trend_score(
        data
    )

    chaos_score = calculate_chaos_score(
        data
    )

    # -----------------------------------------------------
    # 状态判定
    # -----------------------------------------------------

    if chaos_score >= 0.72:

        state = "混沌"

        confidence = (
            0.50
            + (
                chaos_score
                - 0.72
            )
            * 1.5
        )

    elif trend_score >= 0.32:

        state = "趋势"

        confidence = (
            0.50
            + (
                trend_score
                - 0.32
            )
            * 1.6
        )

    else:

        state = "正常"

        confidence = (
            0.55
            + (
                0.32
                - trend_score
            )
            * 0.8
        )

    confidence = clamp(
        confidence,
        0.35,
        0.90,
    )

    window_weights = calculate_window_weights(
        state
    )

    # -----------------------------------------------------
    # 附加状态信息
    # -----------------------------------------------------

    short_rows = get_window(
        data,
        SHORT_WINDOW,
    )

    medium_rows = get_window(
        data,
        MEDIUM_WINDOW,
    )

    long_rows = get_window(
        data,
        LONG_WINDOW,
    )

    result = {

        "state":
            state,

        "confidence":
            round(
                confidence,
                4,
            ),

        "trend_score":
            round(
                trend_score,
                4,
            ),

        "chaos_score":
            round(
                chaos_score,
                4,
            ),

        "window_weights":
            {
                key:
                    round(
                        value,
                        4,
                    )
                for key, value
                in window_weights.items()
            },

        "windows": {

            "short":
                len(short_rows),

            "medium":
                len(medium_rows),

            "long":
                len(long_rows),
        },

        "streak": {

            "wave":
                wave_streak(
                    data
                ),

            "size":
                size_streak(
                    data
                ),

            "parity":
                parity_streak(
                    data
                ),
        },

        "wave_ratio":
            category_ratio(
                short_rows,
                classify_wave,
            ),

        "size_ratio":
            category_ratio(
                short_rows,
                classify_size,
            ),

        "parity_ratio":
            category_ratio(
                short_rows,
                classify_parity,
            ),

        "sample_size":
            len(data),
    }

    return result


# =========================================================
# 兼容接口
#
# predictor / strategies 可以直接调用
# =========================================================

def analyze_state(
    rows: List[Dict[str, Any]],
) -> Dict[str, Any]:

    return detect_market_state(
        rows
    )


# =========================================================
# 获取窗口权重
# =========================================================

def get_dynamic_window_weights(
    rows: List[Dict[str, Any]],
) -> Dict[str, float]:

    state = detect_market_state(
        rows
    )

    return state[
        "window_weights"
    ]


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    import random

    test_rows = []

    for index in range(150):

        numbers = random.sample(
            range(1, 50),
            7,
        )

        test_rows.append({

            "issue":
                str(
                    2026000
                    + index
                ),

            "numbers":
                numbers,

            "special":
                numbers[-1],
        })

    result = detect_market_state(
        test_rows
    )

    print(
        "=" * 70
    )

    print(
        "V3.0 状态识别引擎测试"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "状态：",
        result["state"]
    )

    print(
        "置信度：",
        result["confidence"]
    )

    print(
        "趋势分数：",
        result["trend_score"]
    )

    print(
        "混沌分数：",
        result["chaos_score"]
    )

    print(
        "动态窗口：",
        result["window_weights"]
    )

    print(
        "样本数量：",
        result["sample_size"]
    )

    print()

    print(
        "测试完成"
    )