# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
状态识别引擎

功能：

1. 当前数据质量检查
2. 12期短期状态
3. 36期中期状态
4. 120期长期状态
5. 大小偏离
6. 单双偏离
7. 波色偏离
8. 数字波动
9. 趋势强度
10. 混沌程度
11. 自动决定 12/36/120 窗口权重

注意：

本模块只用于统计建模、回测和概率分析。
开奖结果具有随机性，不能保证预测结果。
"""

from collections import Counter
from math import log

from core.features import (
    get_special,
    get_size,
    get_odd_even,
    get_wave,
)


# =========================================================
# 常量
# =========================================================

SHORT_WINDOW = 12
MEDIUM_WINDOW = 36
LONG_WINDOW = 120


# =========================================================
# 基础工具
# =========================================================

def safe_special(row):

    try:

        n = int(
            get_special(row)
        )

        if 1 <= n <= 49:
            return n

    except Exception:
        pass

    return None


def valid_numbers(rows):

    result = []

    for row in rows:

        n = safe_special(row)

        if n is not None:
            result.append(n)

    return result


# =========================================================
# 数据质量
# =========================================================

def data_quality(rows):

    if not rows:

        return {
            "valid": False,
            "count": 0,
            "quality": 0.0,
        }

    valid = 0

    for row in rows:

        if safe_special(row) is not None:
            valid += 1

    ratio = (
        valid / len(rows)
        if rows
        else 0.0
    )

    return {
        "valid": ratio >= 0.80,
        "count": valid,
        "quality": ratio,
    }


# =========================================================
# 窗口数据
# =========================================================

def get_windows(rows):

    return {

        "short":
            rows[:SHORT_WINDOW],

        "medium":
            rows[:MEDIUM_WINDOW],

        "long":
            rows[:LONG_WINDOW],

    }


# =========================================================
# 大小偏离
# =========================================================

def size_distribution(rows):

    numbers = valid_numbers(rows)

    if not numbers:

        return {
            "big": 0.5,
            "small": 0.5,
            "deviation": 0.0,
        }

    big = sum(
        n >= 25
        for n in numbers
    )

    small = len(numbers) - big

    big_rate = big / len(numbers)
    small_rate = small / len(numbers)

    deviation = abs(
        big_rate - 0.5
    )

    return {
        "big": big_rate,
        "small": small_rate,
        "deviation": deviation,
    }


# =========================================================
# 单双偏离
# =========================================================

def parity_distribution(rows):

    numbers = valid_numbers(rows)

    if not numbers:

        return {
            "odd": 0.5,
            "even": 0.5,
            "deviation": 0.0,
        }

    odd = sum(
        n % 2 == 1
        for n in numbers
    )

    even = len(numbers) - odd

    odd_rate = odd / len(numbers)
    even_rate = even / len(numbers)

    deviation = abs(
        odd_rate - 0.5
    )

    return {
        "odd": odd_rate,
        "even": even_rate,
        "deviation": deviation,
    }


# =========================================================
# 波色分布
# =========================================================

def wave_distribution(rows):

    numbers = valid_numbers(rows)

    if not numbers:

        return {
            "红": 1 / 3,
            "蓝": 1 / 3,
            "绿": 1 / 3,
            "deviation": 0.0,
        }

    counter = Counter()

    for n in numbers:

        wave = get_wave(n)

        if wave in (
            "红",
            "蓝",
            "绿",
        ):

            counter[wave] += 1

    total = sum(
        counter.values()
    )

    if total == 0:

        return {
            "红": 1 / 3,
            "蓝": 1 / 3,
            "绿": 1 / 3,
            "deviation": 0.0,
        }

    probs = {

        wave:
            counter.get(wave, 0)
            / total

        for wave in (
            "红",
            "蓝",
            "绿",
        )
    }

    deviation = max(
        abs(
            probs[wave] - 1 / 3
        )
        for wave in probs
    )

    probs["deviation"] = deviation

    return probs


# =========================================================
# 波色熵
# =========================================================

def wave_entropy(rows):

    distribution = wave_distribution(
        rows
    )

    entropy = 0.0

    for wave in (
        "红",
        "蓝",
        "绿",
    ):

        p = distribution.get(
            wave,
            0
        )

        if p > 0:

            entropy -= (
                p * log(p)
            )

    max_entropy = log(3)

    if max_entropy <= 0:
        return 0.0

    return entropy / max_entropy


# =========================================================
# 数字平均值
# =========================================================

def average_number(rows):

    numbers = valid_numbers(rows)

    if not numbers:
        return 24.5

    return sum(numbers) / len(numbers)


# =========================================================
# 趋势强度
# =========================================================

def trend_strength(rows):

    numbers = valid_numbers(rows)

    if len(numbers) < 8:
        return 0.0

    half = len(numbers) // 2

    first = numbers[
        :half
    ]

    second = numbers[
        half:
    ]

    if not first or not second:
        return 0.0

    first_avg = (
        sum(first)
        / len(first)
    )

    second_avg = (
        sum(second)
        / len(second)
    )

    difference = (
        second_avg
        - first_avg
    )

    # 归一化
    strength = abs(
        difference
    ) / 24.5

    return min(
        strength,
        1.0
    )


# =========================================================
# 趋势方向
# =========================================================

def trend_direction(rows):

    numbers = valid_numbers(rows)

    if len(numbers) < 8:

        return "neutral"

    half = len(numbers) // 2

    first = numbers[:half]
    second = numbers[half:]

    first_avg = (
        sum(first)
        / len(first)
    )

    second_avg = (
        sum(second)
        / len(second)
    )

    difference = (
        second_avg
        - first_avg
    )

    if difference > 2.5:
        return "up"

    if difference < -2.5:
        return "down"

    return "neutral"


# =========================================================
# 波色连续状态
# =========================================================

def wave_streak(rows):

    numbers = valid_numbers(rows)

    if not numbers:

        return {
            "wave": None,
            "length": 0,
        }

    first_wave = get_wave(
        numbers[0]
    )

    if first_wave not in (
        "红",
        "蓝",
        "绿",
    ):

        return {
            "wave": None,
            "length": 0,
        }

    length = 0

    for n in numbers:

        if get_wave(n) == first_wave:
            length += 1
        else:
            break

    return {
        "wave": first_wave,
        "length": length,
    }


# =========================================================
# 综合状态
# =========================================================

def detect_state(rows):

    if not rows:

        return {

            "state": "unknown",

            "confidence": 0.0,

            "trend_strength": 0.0,

            "trend_direction": "neutral",

            "chaos": 1.0,

            "short_weight": 1 / 3,

            "medium_weight": 1 / 3,

            "long_weight": 1 / 3,

        }

    windows = get_windows(
        rows
    )

    short_rows = windows[
        "short"
    ]

    medium_rows = windows[
        "medium"
    ]

    long_rows = windows[
        "long"
    ]

    quality = data_quality(
        long_rows
    )

    # -----------------------------------------------------
    # 趋势
    # -----------------------------------------------------

    short_trend = trend_strength(
        short_rows
    )

    medium_trend = trend_strength(
        medium_rows
    )

    long_trend = trend_strength(
        long_rows
    )

    trend = (
        short_trend * 0.55
        + medium_trend * 0.30
        + long_trend * 0.15
    )

    direction = trend_direction(
        short_rows
    )

    # -----------------------------------------------------
    # 大小偏离
    # -----------------------------------------------------

    short_size = size_distribution(
        short_rows
    )

    medium_size = size_distribution(
        medium_rows
    )

    size_deviation = (
        short_size["deviation"]
        * 0.60
        +
        medium_size["deviation"]
        * 0.40
    )

    # -----------------------------------------------------
    # 单双偏离
    # -----------------------------------------------------

    short_parity = parity_distribution(
        short_rows
    )

    medium_parity = parity_distribution(
        medium_rows
    )

    parity_deviation = (
        short_parity["deviation"]
        * 0.60
        +
        medium_parity["deviation"]
        * 0.40
    )

    # -----------------------------------------------------
    # 波色偏离
    # -----------------------------------------------------

    short_wave = wave_distribution(
        short_rows
    )

    medium_wave = wave_distribution(
        medium_rows
    )

    wave_deviation = (
        short_wave["deviation"]
        * 0.60
        +
        medium_wave["deviation"]
        * 0.40
    )

    # -----------------------------------------------------
    # 波色熵
    # -----------------------------------------------------

    entropy = wave_entropy(
        short_rows
    )

    # -----------------------------------------------------
    # 混沌度
    #
    # 越接近1：
    # 越均匀、越难形成明显结构
    #
    # 越接近0：
    # 越容易发现结构
    # -----------------------------------------------------

    structure = (
        trend * 0.40
        +
        size_deviation * 0.20
        +
        parity_deviation * 0.20
        +
        wave_deviation * 0.20
    )

    chaos = 1.0 - min(
        structure,
        1.0
    )

    # 波色熵高时，提高混沌程度
    chaos = (
        chaos * 0.70
        +
        entropy * 0.30
    )

    chaos = min(
        max(
            chaos,
            0.0
        ),
        1.0
    )

    # -----------------------------------------------------
    # 状态识别
    # -----------------------------------------------------

    if trend >= 0.18:

        state = "trend"

        confidence = min(
            0.55
            + trend * 1.8,
            0.95
        )

    elif chaos >= 0.72:

        state = "chaos"

        confidence = min(
            0.55
            + (
                chaos - 0.72
            ) * 1.5,
            0.90
        )

    else:

        state = "normal"

        confidence = (
            0.55
            +
            (
                1 - abs(
                    chaos - 0.50
                )
            ) * 0.20
        )

        confidence = min(
            confidence,
            0.90
        )

    # -----------------------------------------------------
    # 动态窗口权重
    # -----------------------------------------------------

    if state == "trend":

        short_weight = 0.50
        medium_weight = 0.30
        long_weight = 0.20

    elif state == "chaos":

        short_weight = 0.20
        medium_weight = 0.35
        long_weight = 0.45

    else:

        short_weight = 0.35
        medium_weight = 0.35
        long_weight = 0.30

    # -----------------------------------------------------
    # 数据不足时自动降低长期权重
    # -----------------------------------------------------

    if len(long_rows) < LONG_WINDOW:

        short_weight += 0.10
        medium_weight += 0.05
        long_weight -= 0.15

    if len(medium_rows) < MEDIUM_WINDOW:

        short_weight += 0.05
        medium_weight -= 0.05

    # 防止负数
    short_weight = max(
        short_weight,
        0.0
    )

    medium_weight = max(
        medium_weight,
        0.0
    )

    long_weight = max(
        long_weight,
        0.0
    )

    total = (
        short_weight
        + medium_weight
        + long_weight
    )

    if total <= 0:

        short_weight = 1 / 3
        medium_weight = 1 / 3
        long_weight = 1 / 3

    else:

        short_weight /= total
        medium_weight /= total
        long_weight /= total

    # -----------------------------------------------------
    # 波色连续
    # -----------------------------------------------------

    streak = wave_streak(
        short_rows
    )

    return {

        "state":
            state,

        "confidence":
            round(
                confidence,
                4
            ),

        "quality":
            round(
                quality["quality"],
                4
            ),

        "trend_strength":
            round(
                trend,
                4
            ),

        "trend_direction":
            direction,

        "size_deviation":
            round(
                size_deviation,
                4
            ),

        "parity_deviation":
            round(
                parity_deviation,
                4
            ),

        "wave_deviation":
            round(
                wave_deviation,
                4
            ),

        "wave_entropy":
            round(
                entropy,
                4
            ),

        "chaos":
            round(
                chaos,
                4
            ),

        "wave_streak":
            streak,

        "short_weight":
            round(
                short_weight,
                4
            ),

        "medium_weight":
            round(
                medium_weight,
                4
            ),

        "long_weight":
            round(
                long_weight,
                4
            ),

    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    rows = []

    test_numbers = [
        23, 13, 27, 43,
        34, 8, 45, 46,
        49, 29, 12, 18,
        31, 7, 22, 40,
        15, 26, 38, 4,
    ]

    for index, number in enumerate(
        test_numbers
    ):

        rows.append({

            "numbers":
                f"01,02,03,04,05,06,{number:02d}",

            "issue":
                str(2026000 + index),

        })

    print("=" * 70)
    print("六合彩 AI V3.0 状态识别引擎")
    print("=" * 70)

    result = detect_state(
        rows
    )

    for key, value in result.items():

        print(
            f"{key:<20}: {value}"
        )