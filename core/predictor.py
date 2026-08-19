# -*- coding: utf-8 -*-

"""
预测模块
V6.0

注意：
这里的“预测”是历史统计评分候选，
不是对随机开奖结果作保证。
"""

from __future__ import annotations

from typing import Any, Dict, List

from .analyzer import (
    analyze_history,
    get_color,
    get_size,
    get_odd_even,
    get_tail,
    get_zone,
)


def issue_number(
    issue: str,
) -> int | None:

    digits = "".join(
        c for c in str(issue)
        if c.isdigit()
    )

    if not digits:
        return None

    try:
        return int(digits)
    except Exception:
        return None


def next_issue(
    issue: str,
) -> str:

    value = issue_number(
        issue
    )

    if value is None:
        return ""

    return str(
        value + 1
    )


def build_prediction(
    lottery_name: str,
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    if not history:

        return {
            "lottery": lottery_name,
            "latest_issue": "",
            "next_issue": "",
            "latest_numbers": [],
            "history_size": 0,
            "candidates": [],
            "hot_numbers": [],
            "cold_numbers": [],
            "attributes": {
                "sample_size": 0,
                "colors": {},
                "sizes": {},
                "odd_even": {},
                "tails": {},
                "zones": {},
            },
            "success": False,
            "status": "无历史数据",
        }

    analysis = analyze_history(
        history
    )

    latest = history[-1]

    latest_issue = str(
        latest["issue"]
    )

    latest_numbers = [
        int(x)
        for x in latest["numbers"]
    ]

    special = latest_numbers[-1]

    return {
        "lottery": lottery_name,

        "latest_issue": latest_issue,

        "next_issue": next_issue(
            latest_issue
        ),

        "latest_numbers":
            latest_numbers,

        "latest_special": special,

        "latest_attributes": {
            "color": get_color(
                special
            ),
            "size": get_size(
                special
            ),
            "odd_even": get_odd_even(
                special
            ),
            "tail": get_tail(
                special
            ),
            "zone": get_zone(
                special
            ),
        },

        "history_size":
            len(history),

        "candidates":
            analysis[
                "candidates"
            ],

        "hot_numbers":
            analysis[
                "hot_numbers"
            ],

        "cold_numbers":
            analysis[
                "cold_numbers"
            ],

        "attributes":
            analysis[
                "attributes"
            ],

        "number_frequency":
            analysis[
                "frequency"
            ],

        "overdue":
            analysis[
                "overdue"
            ],

        "status": (
            "数据充足"
            if len(history) >= 30
            else (
                "历史数据不足"
            )
        ),

        "success": True,
    }
