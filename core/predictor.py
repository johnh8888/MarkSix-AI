# -*- coding:utf-8 -*-

"""
六合彩 AI V3.6 FINAL

智能预测核心

功能：

🎯 特码评分
🔥 热号
❄ 冷号
📈 趋势
🐉 特别生肖
🌊 波色
📊 大小
⚖ 单双
Markov
HMM
"""

from collections import Counter

from .wave import predict_wave
from .zodiac_predict import (
    get_zodiac,
    predict_zodiac,
)
from .markov import markov_predict
from .hmm import detect_state
from .features import (
    hot_numbers,
    cold_numbers,
    feature_statistics,
)


# =====================================================
# 数据质量
# =====================================================

def data_quality(history):

    count = len(history)

    if count >= 500:
        level = "优秀"

    elif count >= 300:
        level = "良好"

    elif count >= 100:
        level = "一般"

    elif count >= 30:
        level = "较低"

    else:
        level = "不足"

    return {
        "历史数量": count,
        "等级": level,
    }


# =====================================================
# 号码评分
# =====================================================

def score_numbers(history):

    scores = {}

    specials = [
        int(x["special"])
        for x in history
        if isinstance(x, dict)
        and x.get("special") is not None
    ]

    freq = Counter(
        specials
    )

    recent30 = specials[-30:]
    recent10 = specials[-10:]

    for number in range(1, 50):

        score = 0.0

        # -----------------------------
        # 历史频率
        # -----------------------------

        score += (
            freq[number] * 1.0
        )

        # -----------------------------
        # 最近30期
        # -----------------------------

        recent30_count = (
            recent30.count(number)
        )

        score += (
            recent30_count * 1.5
        )

        # -----------------------------
        # 最近10期
        # -----------------------------

        recent10_count = (
            recent10.count(number)
        )

        score += (
            recent10_count * 2.0
        )

        # -----------------------------
        # 遗漏补偿
        # -----------------------------

        missing = 0

        for value in reversed(
            specials
        ):

            if value == number:
                break

            missing += 1

        # 适度遗漏补偿
        score += min(
            missing * 0.08,
            3.0
        )

        scores[number] = round(
            score,
            3
        )

    return scores


# =====================================================
# 模型状态
# =====================================================

def model_status(history):

    size = len(history)

    return {

        "历史数据": size,

        "Markov":
            "启用"
            if size >= 20
            else "等待",

        "HMM":
            "启用"
            if size >= 50
            else "等待",

        "高级模型":
            "启用"
            if size >= 100
            else "等待",

    }


# =====================================================
# 大小预测
# =====================================================

def predict_size(history):

    numbers = [
        int(x["special"])
        for x in history
        if isinstance(x, dict)
        and x.get("special") is not None
    ]

    if not numbers:

        return {
            "大概率": 0.5,
            "小概率": 0.5,
            "推荐": "大",
        }

    big = sum(
        1
        for x in numbers
        if x >= 25
    )

    small = len(numbers) - big

    total = len(numbers)

    big_probability = round(
        big / total,
        3
    )

    small_probability = round(
        small / total,
        3
    )

    return {

        "大概率":
            big_probability,

        "小概率":
            small_probability,

        "推荐":
            "大"
            if big_probability >= small_probability
            else "小",

    }


# =====================================================
# 单双预测
# =====================================================

def predict_odd_even(history):

    numbers = [
        int(x["special"])
        for x in history
        if isinstance(x, dict)
        and x.get("special") is not None
    ]

    if not numbers:

        return {
            "单概率": 0.5,
            "双概率": 0.5,
            "推荐": "单",
        }

    odd = sum(
        1
        for x in numbers
        if x % 2 == 1
    )

    even = len(numbers) - odd

    total = len(numbers)

    odd_probability = round(
        odd / total,
        3
    )

    even_probability = round(
        even / total,
        3
    )

    return {

        "单概率":
            odd_probability,

        "双概率":
            even_probability,

        "推荐":
            "单"
            if odd_probability >= even_probability
            else "双",

    }


# =====================================================
# 置信度
# =====================================================

def calculate_confidence(
    history,
    scores,
    wave,
):

    size = len(history)

    if size < 30:
        return 0.15

    if size < 100:
        base = 0.30

    elif size < 300:
        base = 0.45

    else:
        base = 0.55

    wave_probability = (
        wave.get(
            "概率",
            0
        )
        if isinstance(wave, dict)
        else 0
    )

    if wave_probability >= 0.40:
        base += 0.05

    elif wave_probability < 0.34:
        base -= 0.05

    return round(
        min(
            max(base, 0.05),
            0.85
        ),
        2
    )


# =====================================================
# 主预测
# =====================================================

def predict(history):

    if not history:

        return {
            "error": "无历史数据"
        }

    # =================================================
    # 基础
    # =================================================

    quality = data_quality(
        history
    )

    scores = score_numbers(
        history
    )

    ranking = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # =================================================
    # 推荐号码
    # =================================================

    top10 = [
        x[0]
        for x in ranking[:10]
    ]

    top3 = [
        x[0]
        for x in ranking[:3]
    ]

    # =================================================
    # 热号
    # =================================================

    hot = hot_numbers(
        history
    )

    # =================================================
    # 冷号
    # =================================================

    cold = cold_numbers(
        history
    )

    # =================================================
    # 波色
    # =================================================

    wave = predict_wave(
        history
    )

    # =================================================
    # 生肖
    # =================================================

    zodiac = predict_zodiac(
        history
    )

    # =================================================
    # 大小
    # =================================================

    size = predict_size(
        history
    )

    # =================================================
    # 单双
    # =================================================

    odd_even = predict_odd_even(
        history
    )

    # =================================================
    # Markov
    # =================================================

    if len(history) >= 20:

        markov = markov_predict(
            history
        )

    else:

        markov = []

    # =================================================
    # HMM
    # =================================================

    if len(history) >= 50:

        state = detect_state(
            history
        )

    else:

        state = {
            "状态": "数据不足"
        }

    # =================================================
    # 模型状态
    # =================================================

    models = model_status(
        history
    )

    # =================================================
    # 置信度
    # =================================================

    confidence = calculate_confidence(
        history,
        scores,
        wave,
    )

    # =================================================
    # 风险
    # =================================================

    if confidence >= 0.60:

        risk = "中风险"

    elif confidence >= 0.40:

        risk = "中高风险"

    else:

        risk = "高风险"

    # =================================================
    # 趋势
    # =================================================

    features = feature_statistics(
        history
    )

    trend = features.get(
        "📈趋势",
        {}
    )

    # =================================================
    # 推荐理由
    # =================================================

    reasons = []

    if len(history) >= 100:

        reasons.append(
            "历史数据充足"
        )

    if hot:

        reasons.append(
            "热号模型参与"
        )

    if cold:

        reasons.append(
            "遗漏模型参与"
        )

    if wave:

        reasons.append(
            "波色趋势参与"
        )

    if len(history) >= 20:

        reasons.append(
            "Markov模型参与"
        )

    if len(history) >= 50:

        reasons.append(
            "HMM状态参与"
        )

    reasons.append(
        "综合评分排序"
    )

    # =================================================
    # 最终结果
    # =================================================

    return {

        "模型版本":
            "V3.6 FINAL",

        "数据质量":
            quality,

        "模型状态":
            models,

        "当前状态":
            state,

        "🎯推荐3码":
            top3,

        "⭐10码范围":
            top10,

        "🔥热号":
            hot,

        "❄冷号":
            cold,

        "📈趋势":
            trend,

        "🐉特别生肖":
            zodiac,

        "第一推荐":
            top3[0]
            if top3
            else None,

        "波色":
            wave,

        "大小":
            size,

        "单双":
            odd_even,

        "置信度":
            confidence,

        "风险等级":
            risk,

        "🎯推荐理由":
            reasons,

        "马尔可夫":
            markov[:5]
            if isinstance(
                markov,
                list
            )
            else markov,

        "评分":
            {
                str(k): v
                for k, v
                in ranking[:10]
            },

        "生肖":
            [
                get_zodiac(x)
                for x in top3
            ],

    }


__all__ = [
    "predict",
]
