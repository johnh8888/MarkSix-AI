# -*- coding: utf-8 -*-

"""
Walk-Forward 回测
V6.0
"""

from __future__ import annotations

from typing import Any, Dict, List

from .analyzer import analyze_numbers


MIN_TRAIN = 20


def walk_forward(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    total_history = len(
        history
    )

    if total_history <= MIN_TRAIN:

        return {
            "method": "Walk-Forward",
            "history_size":
                total_history,
            "samples": 0,
            "hits": 0,
            "hit_rate": 0.0,
            "status":
                "历史数据不足",
        }

    samples = 0
    hits = 0

    detail = []

    # ------------------------------------------
    # 每次只使用过去的数据
    # 预测下一期
    # ------------------------------------------

    for index in range(
        MIN_TRAIN,
        total_history,
    ):

        train = history[
            :index
        ]

        actual = history[
            index
        ]

        analysis = analyze_numbers(
            train
        )

        candidates = set(
            analysis[
                "candidates"
            ]
        )

        actual_numbers = set(
            actual["numbers"]
        )

        hit_count = len(
            candidates
            & actual_numbers
        )

        samples += 1

        if hit_count > 0:
            hits += 1

        detail.append(
            {
                "issue":
                    actual["issue"],
                "candidate_count":
                    len(candidates),
                "hit_count":
                    hit_count,
                "hit":
                    hit_count > 0,
            }
        )

    hit_rate = (
        hits / samples
        if samples
        else 0.0
    )

    return {
        "method":
            "Walk-Forward",

        "history_size":
            total_history,

        "train_minimum":
            MIN_TRAIN,

        "samples":
            samples,

        "hits":
            hits,

        "hit_rate":
            round(
                hit_rate,
                6,
            ),

        "status":
            "完成",

        "details":
            detail[-50:],
    }


def module_performance(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    size = len(history)

    if size < MIN_TRAIN:

        return {
            "history_size":
                size,

            "modules": {
                "frequency": {
                    "score": 0.0,
                    "status":
                        "数据不足",
                },

                "recent_frequency": {
                    "score": 0.0,
                    "status":
                        "数据不足",
                },

                "overdue": {
                    "score": 0.0,
                    "status":
                        "数据不足",
                },
            },
        }

    # ------------------------------------------
    # 用最近一段历史进行简单模块质量评估
    # ------------------------------------------

    recent = history[-20:]

    full_analysis = analyze_numbers(
        history
    )

    recent_analysis = analyze_numbers(
        recent
    )

    frequency_set = set(
        full_analysis[
            "hot_numbers"
        ]
    )

    recent_set = set(
        recent_analysis[
            "hot_numbers"
        ]
    )

    overlap = len(
        frequency_set
        & recent_set
    )

    overlap_score = (
        overlap
        / 10.0
    )

    return {
        "history_size":
            size,

        "modules": {
            "frequency": {
                "score":
                    round(
                        overlap_score,
                        6,
                    ),
                "status":
                    "已计算",
            },

            "recent_frequency": {
                "score":
                    round(
                        overlap_score,
                        6,
                    ),
                "status":
                    "已计算",
            },

            "overdue": {
                "score":
                    round(
                        overlap_score,
                        6,
                    ),
                "status":
                    "已计算",
            },
        },
    }
