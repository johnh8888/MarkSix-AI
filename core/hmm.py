# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

HMM风格状态识别模块

状态：

HOT
NORMAL
COLD
CHAOS

说明：
V3.0 不依赖 hmmlearn，
避免 GitHub Actions 因第三方依赖导致失败。
"""

from __future__ import annotations

from collections import Counter


STATES = (
    "HOT",
    "NORMAL",
    "COLD",
    "CHAOS"
)


def extract_specials(history):

    result = []

    for row in history:

        if not isinstance(row, dict):
            continue

        try:
            n = int(row["special"])
        except Exception:
            continue

        if 1 <= n <= 49:
            result.append(n)

    return result


def entropy(values):

    if not values:
        return 0.0

    counter = Counter(
        values
    )

    total = len(values)

    result = 0.0

    import math

    for count in counter.values():

        p = count / total

        if p > 0:

            result -= (
                p * math.log(
                    p,
                    2
                )
            )

    return result


def detect_state(
    history,
    window=20
):
    """
    判断当前市场状态。

    返回：

    {
        "状态": "HOT",
        "熵": ...,
        "波动": ...,
        "样本": ...
    }
    """

    specials = extract_specials(
        history
    )

    if len(specials) < 5:

        return {
            "状态": "NORMAL",

            "熵": 0.0,

            "波动": 0.0,

            "样本": len(specials)
        }

    recent = specials[-window:]

    counter = Counter(
        recent
    )

    max_count = max(
        counter.values()
    )

    unique_count = len(
        counter
    )

    ent = entropy(
        recent
    )

    # 重复率
    repeat_ratio = (
        1
        -
        unique_count / len(recent)
    )

    # 最近号码变化程度
    changes = 0

    for i in range(
        1,
        len(recent)
    ):

        if recent[i] != recent[i - 1]:

            changes += 1

    volatility = (
        changes
        /
        max(
            1,
            len(recent) - 1
        )
    )

    if repeat_ratio >= 0.35:

        state = "HOT"

    elif ent >= 3.8 and volatility >= 0.9:

        state = "CHAOS"

    elif max_count <= 1:

        state = "COLD"

    else:

        state = "NORMAL"

    return {
        "状态": state,

        "熵": round(
            ent,
            4
        ),

        "波动": round(
            volatility,
            4
        ),

        "样本": len(recent),

        "重复率": round(
            repeat_ratio,
            4
        )
    }


__all__ = [
    "STATES",
    "entropy",
    "detect_state"
]
