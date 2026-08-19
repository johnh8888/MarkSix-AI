# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

波色模型
"""

from __future__ import annotations

from collections import Counter


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


def extract_specials(history):

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


def predict_wave(
    history,
    top_n=2
):
    """
    根据历史特码统计波色。

    返回：

    {
        "主推": "红",
        "双推": ["红", "蓝"],
        "统计": {...}
    }
    """

    specials = extract_specials(
        history
    )

    if not specials:

        return {
            "主推": "未知",

            "双推": [],

            "统计": {}
        }

    counter = Counter(
        get_wave(n)
        for n in specials
    )

    ranking = sorted(
        counter.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top = [
        x[0]
        for x in ranking[:top_n]
    ]

    return {
        "主推": (
            top[0]
            if top
            else "未知"
        ),

        "双推": top,

        "统计": dict(
            counter
        )
    }


def wave_scores(
    history
):

    specials = extract_specials(
        history
    )

    counter = Counter(
        get_wave(n)
        for n in specials
    )

    total = sum(
        counter.values()
    )

    if total == 0:

        return {
            "红": 0.0,
            "蓝": 0.0,
            "绿": 0.0
        }

    return {
        color: round(
            counter[color] / total,
            4
        )
        for color in (
            "红",
            "蓝",
            "绿"
        )
    }


__all__ = [
    "RED",
    "BLUE",
    "GREEN",
    "get_wave",
    "predict_wave",
    "wave_scores"
]
