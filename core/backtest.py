# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

Walk-Forward 回测

目的：

使用过去数据预测下一期，
避免直接使用未来数据。

注意：

回测结果仅代表历史样本表现，
不能代表未来中奖概率。
"""

from __future__ import annotations

from collections import Counter

from .predictor import (
    score_numbers
)


# =====================================================
# 获取特码
# =====================================================

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


# =====================================================
# 单次预测
# =====================================================

def predict_one(
    train
):

    scores = score_numbers(
        train
    )

    ranking = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        number
        for number, score
        in ranking[:10]
    ]


# =====================================================
# Walk Forward
# =====================================================

def walk_forward(
    history,
    min_train=30,
    top_n=10
):

    specials = extract_specials(
        history
    )

    total = len(
        specials
    )

    if total <= min_train:

        return {
            "状态": "样本不足",

            "样本": total,

            "测试次数": 0
        }

    hits = 0

    tests = 0

    top3_hits = 0

    details = []

    for i in range(
        min_train,
        total
    ):

        train_specials = (
            specials[:i]
        )

        actual = specials[i]

        # 构造训练数据
        train = [
            {
                "special": n
            }
            for n
            in train_specials
        ]

        scores = score_numbers(
            train
        )

        ranking = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        prediction = [
            number
            for number, score
            in ranking[:top_n]
        ]

        tests += 1

        hit = actual in prediction

        if hit:
            hits += 1

        top3 = prediction[:3]

        if actual in top3:
            top3_hits += 1

        if len(details) < 20:

            details.append(
                {
                    "测试期":
                        i + 1,

                    "实际":
                        actual,

                    "预测":
                        prediction,

                    "命中":
                        hit
                }
            )

    top10_rate = (
        hits / tests
        if tests
        else 0.0
    )

    top3_rate = (
        top3_hits / tests
        if tests
        else 0.0
    )

    return {

        "状态": "完成",

        "样本":
            total,

        "测试次数":
            tests,

        "Top10命中次数":
            hits,

        "Top10命中率":
            round(
                top10_rate,
                4
            ),

        "Top3命中次数":
            top3_hits,

        "Top3命中率":
            round(
                top3_rate,
                4
            ),

        "最近测试":
            details
    }


__all__ = [
    "walk_forward"
]
