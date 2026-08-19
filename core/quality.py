# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

数据质量检测模块
"""

from __future__ import annotations


def check_history(history):

    if not history:

        return {
            "质量": 0.0,

            "等级": "无数据",

            "样本": 0
        }

    total = len(
        history
    )

    valid = 0

    for row in history:

        if not isinstance(row, dict):
            continue

        try:

            numbers = row.get(
                "numbers",
                []
            )

            special = int(
                row.get("special")
            )

            if len(numbers) != 6:
                continue

            if len(set(numbers)) != 6:
                continue

            if any(
                int(x) < 1
                or int(x) > 49
                for x in numbers
            ):
                continue

            if not 1 <= special <= 49:
                continue

            if special in numbers:
                continue

            valid += 1

        except Exception:

            continue

    score = (
        valid / total
        if total
        else 0.0
    )

    if score >= 0.95:

        level = "优秀"

    elif score >= 0.80:

        level = "良好"

    elif score >= 0.60:

        level = "一般"

    else:

        level = "较差"

    return {

        "质量":
            round(score, 4),

        "等级":
            level,

        "样本":
            total,

        "有效":
            valid,

        "无效":
            total - valid
    }


def quality_score(history):

    return check_history(
        history
    )["质量"]


__all__ = [
    "check_history",
    "quality_score"
]
