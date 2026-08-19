# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

马尔可夫链模型

用于分析：

上一期特码
    ↓
下一期可能号码

注意：
这是统计排序模型，不代表真实中奖概率。
"""

from __future__ import annotations

from collections import defaultdict, Counter


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


def build_transition(
    history
):

    specials = extract_specials(
        history
    )

    transition = defaultdict(
        Counter
    )

    for i in range(
        len(specials) - 1
    ):

        current = specials[i]

        next_number = specials[i + 1]

        transition[current][
            next_number
        ] += 1

    return transition


def markov_predict(
    history,
    top_n=10
):
    """
    根据最后一期特码，
    返回下一期号码排序。
    """

    specials = extract_specials(
        history
    )

    if not specials:
        return []

    current = specials[-1]

    transition = build_transition(
        history
    )

    counter = transition.get(
        current,
        Counter()
    )

    if not counter:

        return []

    return [
        number
        for number, count
        in counter.most_common(top_n)
    ]


def markov_scores(
    history
):

    specials = extract_specials(
        history
    )

    scores = {
        n: 0.0
        for n in range(1, 50)
    }

    if not specials:
        return scores

    current = specials[-1]

    transition = build_transition(
        history
    )

    counter = transition.get(
        current,
        Counter()
    )

    total = sum(
        counter.values()
    )

    if total <= 0:
        return scores

    for number, count in counter.items():

        scores[number] = (
            count / total
        )

    return scores


__all__ = [
    "extract_specials",
    "build_transition",
    "markov_predict",
    "markov_scores"
]
