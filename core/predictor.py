# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

预测核心模块

功能：

1. 号码频率
2. 遗漏
3. 马尔可夫
4. 状态识别
5. 波色
6. 生肖
7. 综合评分
8. Top10
9. Top3

注意：

本系统输出的是统计排序结果，
不是保证中奖概率。
"""

from __future__ import annotations

from collections import Counter

from .features import (
    get_wave,
    get_size,
    get_parity,
    get_tail,
    get_zone
)

from .wave import (
    predict_wave
)

from .zodiac import (
    get_zodiac
)

from .markov import (
    markov_scores,
    markov_predict
)

from .hmm import (
    detect_state
)


# =====================================================
# 提取特码
# =====================================================

def extract_specials(history):

    result = []

    for row in history:

        if not isinstance(row, dict):
            continue

        try:

            n = int(
                row.get("special")
            )

        except Exception:

            continue

        if 1 <= n <= 49:

            result.append(n)

    return result


# =====================================================
# 号码综合评分
# =====================================================

def score_numbers(history):

    specials = extract_specials(
        history
    )

    scores = {
        n: 0.0
        for n in range(1, 50)
    }

    if not specials:

        return scores

    # -------------------------------------------------
    # 历史频率
    # -------------------------------------------------

    freq = Counter(
        specials
    )

    # -------------------------------------------------
    # 最近20期
    # -------------------------------------------------

    recent20 = specials[-20:]

    recent10 = specials[-10:]

    recent36 = specials[-36:]

    # -------------------------------------------------
    # 马尔可夫
    # -------------------------------------------------

    markov = markov_scores(
        history
    )

    # -------------------------------------------------
    # 计算
    # -------------------------------------------------

    for n in range(1, 50):

        score = 0.0

        # 历史频率
        score += (
            freq[n] * 1.0
        )

        # 最近20期
        score += (
            recent20.count(n)
            * 0.8
        )

        # 最近10期
        score += (
            recent10.count(n)
            * 0.5
        )

        # 最近36期
        score += (
            recent36.count(n)
            * 0.2
        )

        # 遗漏
        if n not in recent10:

            score += 0.5

        # 马尔可夫
        score += (
            markov.get(n, 0.0)
            * 3.0
        )

        scores[n] = round(
            score,
            4
        )

    return scores


# =====================================================
# 大小预测
# =====================================================

def predict_size(history):

    specials = extract_specials(
        history
    )

    recent = specials[-36:]

    if not recent:

        return {
            "主推": "未知",
            "统计": {}
        }

    counter = Counter(
        get_size(n)
        for n in recent
    )

    ranking = counter.most_common()

    return {
        "主推": ranking[0][0],

        "统计": dict(counter)
    }


# =====================================================
# 单双预测
# =====================================================

def predict_parity(history):

    specials = extract_specials(
        history
    )

    recent = specials[-36:]

    if not recent:

        return {
            "主推": "未知",
            "统计": {}
        }

    counter = Counter(
        get_parity(n)
        for n in recent
    )

    ranking = counter.most_common()

    return {
        "主推": ranking[0][0],

        "统计": dict(counter)
    }


# =====================================================
# 尾数统计
# =====================================================

def predict_tail(history):

    specials = extract_specials(
        history
    )

    recent = specials[-36:]

    counter = Counter(
        get_tail(n)
        for n in recent
    )

    ranking = [
        x[0]
        for x in counter.most_common()
    ]

    return {
        "主推": ranking[:3],

        "统计": dict(counter)
    }


# =====================================================
# 分区统计
# =====================================================

def predict_zone(history):

    specials = extract_specials(
        history
    )

    recent = specials[-36:]

    counter = Counter(
        get_zone(n)
        for n in recent
    )

    ranking = [
        x[0]
        for x in counter.most_common()
    ]

    return {
        "主推": ranking[:2],

        "统计": dict(counter)
    }


# =====================================================
# 生肖预测
# =====================================================

def predict_zodiac(
    ranking
):

    counter = Counter()

    for number, score in ranking:

        zodiac = get_zodiac(
            number
        )

        if zodiac != "未知":

            counter[zodiac] += score

    ranking = sorted(
        counter.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        zodiac
        for zodiac, score
        in ranking[:5]
    ]


# =====================================================
# 主预测
# =====================================================

def predict(history):

    if not history:

        return {
            "错误": "无历史数据"
        }

    specials = extract_specials(
        history
    )

    if not specials:

        return {
            "错误": "没有有效特码数据"
        }

    scores = score_numbers(
        history
    )

    ranking = sorted(
        scores.items(),
        key=lambda x: (
            x[1],
            -x[0]
        ),
        reverse=True
    )

    top10 = [
        number
        for number, score
        in ranking[:10]
    ]

    top3 = [
        number
        for number, score
        in ranking[:3]
    ]

    state = detect_state(
        history
    )

    wave = predict_wave(
        history
    )

    markov = markov_predict(
        history,
        10
    )

    return {

        "模型版本": "V3.0 FINAL",

        "说明":
            "统计模型仅用于排序，不代表真实中奖概率",

        "样本数量":
            len(specials),

        "状态":
            state,

        "特码10码":
            top10,

        "重点3码":
            top3,

        "第一推荐":
            top3[0] if top3 else None,

        "生肖5肖":
            predict_zodiac(
                ranking
            ),

        "波色":
            wave,

        "大小":
            predict_size(
                history
            ),

        "单双":
            predict_parity(
                history
            ),

        "尾数":
            predict_tail(
                history
            ),

        "分区":
            predict_zone(
                history
            ),

        "马尔可夫":
            markov,

        "评分":
            {
                str(number):
                    round(score, 4)
                for number, score
                in ranking[:10]
            }
    }


__all__ = [
    "predict",
    "score_numbers",
    "extract_specials"
]
