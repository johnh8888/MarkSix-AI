# -*- coding: utf-8 -*-

"""
六合彩预测模块 V1.2

核心流程：

49码评分
    ↓
TOP10
    ↓
TOP5
    ↓
TOP3
    ↓
第一推荐

同时计算：

大小
单双
波色
生肖
平特生肖

注意：

特码来自 numbers 第7个号码。
"""

from collections import defaultdict

from .strategies import combine_strategies

from .features import (
    get_special,
    get_size,
    get_odd_even,
    get_wave,
)


# =========================================================
# 2026 生肖号码
# =========================================================

ZODIAC_MAP_2026 = {

    "马": [1, 13, 25, 37, 49],

    "蛇": [2, 14, 26, 38],

    "龙": [3, 15, 27, 39],

    "兔": [4, 16, 28, 40],

    "虎": [5, 17, 29, 41],

    "牛": [6, 18, 30, 42],

    "鼠": [7, 19, 31, 43],

    "猪": [8, 20, 32, 44],

    "狗": [9, 21, 33, 45],

    "鸡": [10, 22, 34, 46],

    "猴": [11, 23, 35, 47],

    "羊": [12, 24, 36, 48],
}


NUMBER_TO_ZODIAC = {}

for zodiac, numbers in ZODIAC_MAP_2026.items():

    for number in numbers:

        NUMBER_TO_ZODIAC[number] = zodiac


# =========================================================
# 波色
# =========================================================

WAVE_MAP = {

    "红": [
        1, 2, 7, 8, 12, 13,
        18, 19, 23, 24,
        29, 30, 34, 35,
        40, 45, 46
    ],

    "蓝": [
        3, 4, 9, 10, 14, 15,
        20, 25, 26, 31,
        36, 37, 41, 42,
        47, 48
    ],

    "绿": [
        5, 6, 11, 16, 17,
        21, 22, 27, 28,
        32, 33, 38, 39,
        43, 44, 49
    ],
}


NUMBER_TO_WAVE = {}

for wave, numbers in WAVE_MAP.items():

    for number in numbers:

        NUMBER_TO_WAVE[number] = wave


# =========================================================
# 概率：大小
# =========================================================

def calculate_size_probability(rows):

    big = 0
    small = 0

    for row in rows:

        number = get_special(row)

        if not 1 <= number <= 49:
            continue

        if number >= 25:
            big += 1
        else:
            small += 1

    total = big + small

    if total == 0:

        return {
            "大": 0.5,
            "小": 0.5
        }

    return {

        "大":
            big / total,

        "小":
            small / total,
    }


# =========================================================
# 概率：单双
# =========================================================

def calculate_parity_probability(rows):

    odd = 0
    even = 0

    for row in rows:

        number = get_special(row)

        if not 1 <= number <= 49:
            continue

        if number % 2:
            odd += 1
        else:
            even += 1

    total = odd + even

    if total == 0:

        return {
            "单": 0.5,
            "双": 0.5
        }

    return {

        "单":
            odd / total,

        "双":
            even / total,
    }


# =========================================================
# 概率：波色
# =========================================================

def calculate_wave_probability(rows):

    counts = {

        "红": 0,
        "蓝": 0,
        "绿": 0,
    }

    for row in rows:

        number = get_special(row)

        wave = NUMBER_TO_WAVE.get(
            number
        )

        if wave:

            counts[wave] += 1

    total = sum(
        counts.values()
    )

    if total == 0:

        return {

            "红": 1 / 3,
            "蓝": 1 / 3,
            "绿": 1 / 3,
        }

    return {

        wave:
            counts[wave] / total

        for wave in (
            "红",
            "蓝",
            "绿",
        )
    }


# =========================================================
# 49码综合评分
# =========================================================

def calculate_number_scores(rows):

    combined_scores, strategy_scores = (
        combine_strategies(rows)
    )

    recent = rows[:30]
    medium = rows[:100]

    recent_size = calculate_size_probability(
        recent
    )

    medium_size = calculate_size_probability(
        medium
    )

    recent_parity = calculate_parity_probability(
        recent
    )

    medium_parity = calculate_parity_probability(
        medium
    )

    recent_wave = calculate_wave_probability(
        recent
    )

    medium_wave = calculate_wave_probability(
        medium
    )

    scores = {}

    for number in range(1, 50):

        base = combined_scores.get(
            number,
            0.5
        )

        # -------------------------------------------------
        # 大小
        # -------------------------------------------------

        if number >= 25:

            size_score = (
                recent_size["大"] * 0.7
                +
                medium_size["大"] * 0.3
            )

        else:

            size_score = (
                recent_size["小"] * 0.7
                +
                medium_size["小"] * 0.3
            )

        # -------------------------------------------------
        # 单双
        # -------------------------------------------------

        if number % 2:

            parity_score = (
                recent_parity["单"] * 0.7
                +
                medium_parity["单"] * 0.3
            )

        else:

            parity_score = (
                recent_parity["双"] * 0.7
                +
                medium_parity["双"] * 0.3
            )

        # -------------------------------------------------
        # 波色
        # -------------------------------------------------

        wave = NUMBER_TO_WAVE.get(
            number
        )

        wave_score = (

            recent_wave.get(
                wave,
                1 / 3
            ) * 0.7

            +

            medium_wave.get(
                wave,
                1 / 3
            ) * 0.3
        )

        # -------------------------------------------------
        # 最终评分
        # -------------------------------------------------

        final_score = (

            base * 0.60

            +

            size_score * 0.15

            +

            parity_score * 0.10

            +

            wave_score * 0.15
        )

        scores[number] = final_score

    return scores


# =========================================================
# 排名
# =========================================================

def get_ranked_numbers(scores):

    return sorted(
        scores.items(),
        key=lambda x: (
            x[1],
            -x[0]
        ),
        reverse=True
    )


# =========================================================
# 生肖评分
# =========================================================

def calculate_zodiac_scores(
    number_scores
):

    zodiac_scores = defaultdict(float)

    for number, score in number_scores.items():

        zodiac = NUMBER_TO_ZODIAC.get(
            number
        )

        if zodiac:

            zodiac_scores[zodiac] += score

    return dict(zodiac_scores)


# =========================================================
# 生肖排名
# =========================================================

def get_top_zodiacs(
    zodiac_scores,
    count
):

    ranking = sorted(
        zodiac_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return ranking[:count]


# =========================================================
# 平特生肖
# =========================================================

def calculate_pingte_zodiac_scores(
    rows,
    number_scores
):

    history_count = defaultdict(int)

    for row in rows[:300]:

        number = get_special(row)

        zodiac = NUMBER_TO_ZODIAC.get(
            number
        )

        if zodiac:

            history_count[zodiac] += 1

    total = max(
        sum(history_count.values()),
        1
    )

    result = {}

    for zodiac, numbers in ZODIAC_MAP_2026.items():

        number_score = sum(

            number_scores.get(
                n,
                0.0
            )

            for n in numbers
        )

        number_score /= max(
            len(numbers),
            1
        )

        history_score = (
            history_count[zodiac]
            / total
        )

        result[zodiac] = (

            number_score * 0.70

            +

            history_score * 0.30
        )

    return result


# =========================================================
# 当前属性预测
# =========================================================

def get_attribute_prediction(rows):

    size_probability = calculate_size_probability(
        rows[:100]
    )

    parity_probability = calculate_parity_probability(
        rows[:100]
    )

    wave_probability = calculate_wave_probability(
        rows[:100]
    )

    return {

        "size": {

            "prediction":
                max(
                    size_probability,
                    key=size_probability.get
                ),

            "probability":
                {
                    k: round(v, 6)
                    for k, v
                    in size_probability.items()
                },
        },

        "parity": {

            "prediction":
                max(
                    parity_probability,
                    key=parity_probability.get
                ),

            "probability":
                {
                    k: round(v, 6)
                    for k, v
                    in parity_probability.items()
                },
        },

        "wave": {

            "prediction":
                max(
                    wave_probability,
                    key=wave_probability.get
                ),

            "probability":
                {
                    k: round(v, 6)
                    for k, v
                    in wave_probability.items()
                },
        },
    }


# =========================================================
# 生成预测
# =========================================================

def generate_prediction(rows):

    if not rows:

        return {
            "error": "没有历史数据"
        }

    # =====================================================
    # 49码评分
    # =====================================================

    number_scores = calculate_number_scores(
        rows
    )

    ranking = get_ranked_numbers(
        number_scores
    )

    # =====================================================
    # TOP
    # =====================================================

    top10 = ranking[:10]

    top5 = ranking[:5]

    top3 = ranking[:3]

    first = top3[0] if top3 else None

    second = top3[1] if len(top3) > 1 else None

    third = top3[2] if len(top3) > 2 else None

    # =====================================================
    # 生肖
    # =====================================================

    zodiac_scores = calculate_zodiac_scores(
        number_scores
    )

    top5_zodiac = get_top_zodiacs(
        zodiac_scores,
        5
    )

    # =====================================================
    # 平特
    # =====================================================

    pingte_scores = calculate_pingte_zodiac_scores(
        rows,
        number_scores
    )

    top2_pingte = get_top_zodiacs(
        pingte_scores,
        2
    )

    # =====================================================
    # 属性
    # =====================================================

    attributes = get_attribute_prediction(
        rows
    )

    # =====================================================
    # 输出
    # =====================================================

    result = {

        # -------------------------------------------------
        # 第一推荐
        # -------------------------------------------------

        "recommendation": {

            "first": (
                {
                    "number": first[0],
                    "score": round(
                        first[1],
                        6
                    ),
                }
                if first
                else None
            ),

            "second": (
                {
                    "number": second[0],
                    "score": round(
                        second[1],
                        6
                    ),
                }
                if second
                else None
            ),

            "third": (
                {
                    "number": third[0],
                    "score": round(
                        third[1],
                        6
                    ),
                }
                if third
                else None
            ),
        },

        # -------------------------------------------------
        # TOP10
        # -------------------------------------------------

        "top10_numbers": [

            {
                "rank": rank,
                "number": number,
                "score": round(
                    score,
                    6
                ),
            }

            for rank, (
                number,
                score
            ) in enumerate(
                top10,
                1
            )
        ],

        # -------------------------------------------------
        # TOP5
        # -------------------------------------------------

        "top5_numbers": [

            {
                "rank": rank,
                "number": number,
                "score": round(
                    score,
                    6
                ),
            }

            for rank, (
                number,
                score
            ) in enumerate(
                top5,
                1
            )
        ],

        # -------------------------------------------------
        # TOP3
        # -------------------------------------------------

        "top3_numbers": [

            {
                "rank": rank,
                "number": number,
                "score": round(
                    score,
                    6
                ),
            }

            for rank, (
                number,
                score
            ) in enumerate(
                top3,
                1
            )
        ],

        # -------------------------------------------------
        # 生肖
        # -------------------------------------------------

        "top5_zodiac": [

            {
                "zodiac": zodiac,
                "score": round(
                    score,
                    6
                ),
            }

            for zodiac, score
            in top5_zodiac
        ],

        # -------------------------------------------------
        # 平特
        # -------------------------------------------------

        "top2_pingte_zodiac": [

            {
                "zodiac": zodiac,
                "score": round(
                    score,
                    6
                ),
            }

            for zodiac, score
            in top2_pingte
        ],

        # -------------------------------------------------
        # 属性
        # -------------------------------------------------

        **attributes,
    }

    return result
