# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

特征工程模块

提供：

1. 大小
2. 单双
3. 波色
4. 尾数
5. 分区
6. 遗漏
7. 热冷
"""

from __future__ import annotations

from collections import Counter


# =====================================================
# 波色
# =====================================================

RED = {
    1, 2, 7, 8, 12, 13,
    18, 19, 23, 24, 29, 30,
    34, 35, 40, 45, 46
}

BLUE = {
    3, 4, 9, 10, 14, 15,
    20, 25, 26, 31,
    36, 37, 41, 42, 47, 48
}

GREEN = {
    5, 6, 11, 16, 17,
    21, 22, 27, 28,
    32, 33, 38, 39, 43, 44, 49
}


def get_wave(number):

    n = int(number)

    if n in RED:
        return "红"

    if n in BLUE:
        return "蓝"

    if n in GREEN:
        return "绿"

    return "未知"


# =====================================================
# 大小
# =====================================================

def get_size(number):

    return "大" if int(number) >= 25 else "小"


# =====================================================
# 单双
# =====================================================

def get_parity(number):

    return "单" if int(number) % 2 else "双"


# =====================================================
# 尾数
# =====================================================

def get_tail(number):

    return int(number) % 10


# =====================================================
# 分区
# =====================================================

def get_zone(number):

    n = int(number)

    if 1 <= n <= 10:
        return "一区"

    if 11 <= n <= 20:
        return "二区"

    if 21 <= n <= 30:
        return "三区"

    if 31 <= n <= 40:
        return "四区"

    if 41 <= n <= 49:
        return "五区"

    return "未知"


# =====================================================
# 号码属性
# =====================================================

def number_features(number):

    return {
        "号码": int(number),

        "波色": get_wave(number),

        "大小": get_size(number),

        "单双": get_parity(number),

        "尾数": get_tail(number),

        "分区": get_zone(number)
    }


# =====================================================
# 历史特码
# =====================================================

def get_specials(history):

    result = []

    for row in history:

        if not isinstance(row, dict):
            continue

        try:

            n = int(
                row["special"]
            )

        except Exception:

            continue

        if 1 <= n <= 49:

            result.append(n)

    return result


# =====================================================
# 号码频率
# =====================================================

def frequency(history):

    specials = get_specials(
        history
    )

    return Counter(
        specials
    )


# =====================================================
# 遗漏
# =====================================================

def omission(history):

    specials = get_specials(
        history
    )

    result = {}

    for number in range(1, 50):

        gap = len(specials)

        for i, value in enumerate(
            reversed(specials)
        ):

            if value == number:

                gap = i
                break

        result[number] = gap

    return result


# =====================================================
# 热冷
# =====================================================

def hot_cold(
    history,
    window=30
):

    specials = get_specials(
        history
    )

    recent = specials[-window:]

    counter = Counter(
        recent
    )

    result = {}

    for n in range(1, 50):

        result[n] = counter[n]

    return result


# =====================================================
# 综合特征
# =====================================================

def build_features(history):

    freq = frequency(
        history
    )

    gap = omission(
        history
    )

    hot = hot_cold(
        history
    )

    result = {}

    for n in range(1, 50):

        result[n] = {
            **number_features(n),

            "频率": freq[n],

            "遗漏": gap[n],

            "近期频率": hot[n]
        }

    return result


__all__ = [
    "RED",
    "BLUE",
    "GREEN",
    "get_wave",
    "get_size",
    "get_parity",
    "get_tail",
    "get_zone",
    "number_features",
    "get_specials",
    "frequency",
    "omission",
    "hot_cold",
    "build_features"
]
