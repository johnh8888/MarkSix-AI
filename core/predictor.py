# -*- coding: utf-8 -*-

"""
六合彩 AI V2.0 Predictor

功能：

49码评分
Top10
Top3
生肖5肖
平特生肖2肖
大小
单双
波色单推
波色双推
动态状态
动态权重
"""

from collections import defaultdict

from .strategies import (
    combine_strategies,
    NUMBER_TO_WAVE,
    WAVE_MAP,
)


# =========================================================
# 2026 生肖
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
# 基础概率
# =========================================================

def calculate_size_probability(rows):

    big = 0
    small = 0

    for row in rows:

        try:
            n = int(row["special"])
        except Exception:
            continue

        if n >= 25:
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


def calculate_parity_probability(rows):

    odd = 0
    even = 0

    for row in rows:

        try:
            n = int(row["special"])
        except Exception:
            continue

        if n % 2:
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


def calculate_wave_probability(rows):

    counts = {
        "红": 0,
        "蓝": 0,
        "绿": 0,
    }

    for row in rows:

        try:
            n = int(row["special"])
        except Exception:
            continue

        wave = NUMBER_TO_WAVE.get(n)

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
        key:
            value / total

        for key, value
        in counts.items()
    }


# =========================================================
# 生肖评分
# =========================================================

def calculate_zodiac_scores(
    number_scores
):

    result = defaultdict(float)

    for number, score in number_scores.items():

        zodiac = NUMBER_TO_ZODIAC.get(
            number
        )

        if zodiac:

            result[zodiac] += score

    return dict(result)


def get_top_zodiacs(
    scores,
    count
):

    ranking = sorted(
        scores.items(),
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

    for row in rows[:200]:

        try:
            n = int(row["special"])
        except Exception:
            continue

        zodiac = NUMBER_TO_ZODIAC.get(n)

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


        # 当前模型优先
        result[zodiac] = (

            number_score * 0.80

            +

            history_score * 0.20
        )


    return result


# =========================================================
# 波色双推
# =========================================================

def get_wave_predictions(
    number_scores
):

    wave_scores = {

        "红": 0.0,

        "蓝": 0.0,

        "绿": 0.0,
    }


    for number, score in number_scores.items():

        wave = NUMBER_TO_WAVE.get(
            number
        )

        if wave:

            wave_scores[wave] += score


    ranking = sorted(
        wave_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )


    single = ranking[0][0]

    double = [
        ranking[0][0],
        ranking[1][0],
    ]


    total = sum(
        wave_scores.values()
    )


    if total > 0:

        probabilities = {

            wave:
                score / total

            for wave, score
            in wave_scores.items()
        }

    else:

        probabilities = {

            "红": 1 / 3,

            "蓝": 1 / 3,

            "绿": 1 / 3,
        }


    return (
        single,
        double,
        probabilities
    )


# =========================================================
# Top号码
# =========================================================

def get_top_numbers(
    scores,
    count=10
):

    ranking = sorted(

        scores.items(),

        key=lambda x: (
            x[1],
            -x[0]
        ),

        reverse=True
    )

    return ranking[:count]


# =========================================================
# 主预测
# =========================================================

def generate_prediction(rows):

    if not rows:

        return {
            "error":
                "没有历史数据"
        }


    # =====================================================
    # 1. 49码模型
    # =====================================================

    (
        number_scores,
        strategy_scores,
        dynamic_weights
    ) = combine_strategies(
        rows
    )


    # =====================================================
    # 2. Top10
    # =====================================================

    top10 = get_top_numbers(
        number_scores,
        10
    )


    # =====================================================
    # 3. Top3
    # =====================================================

    top3 = top10[:3]


    # =====================================================
    # 4. 生肖
    # =====================================================

    zodiac_scores = (
        calculate_zodiac_scores(
            number_scores
        )
    )


    top5_zodiac = get_top_zodiacs(
        zodiac_scores,
        5
    )


    # =====================================================
    # 5. 平特
    # =====================================================

    pingte_scores = (
        calculate_pingte_zodiac_scores(
            rows,
            number_scores
        )
    )


    top2_pingte = get_top_zodiacs(
        pingte_scores,
        2
    )


    # =====================================================
    # 6. 属性概率
    # =====================================================

    size_probability = (
        calculate_size_probability(
            rows[:20]
        )
    )


    parity_probability = (
        calculate_parity_probability(
            rows[:20]
        )
    )


    # =====================================================
    # 7. 波色
    # =====================================================

    (
        wave_single,
        wave_double,
        wave_probability
    ) = get_wave_predictions(
        number_scores
    )


    # =====================================================
    # 8. 输出
    # =====================================================

    return {

        "model_version":
            "V2.0-AUTO",

        "top10_numbers": [

            {
                "number":
                    int(number),

                "score":
                    round(
                        score,
                        6
                    ),
            }

            for number, score
            in top10
        ],


        "top3_numbers": [

            {
                "number":
                    int(number),

                "score":
                    round(
                        score,
                        6
                    ),
            }

            for number, score
            in top3
        ],


        "top5_zodiac": [

            {
                "zodiac":
                    zodiac,

                "score":
                    round(
                        score,
                        6
                    ),
            }

            for zodiac, score
            in top5_zodiac
        ],


        "top2_pingte_zodiac": [

            {
                "zodiac":
                    zodiac,

                "score":
                    round(
                        score,
                        6
                    ),
            }

            for zodiac, score
            in top2_pingte
        ],


        "size": {

            "prediction":
                max(
                    size_probability,
                    key=size_probability.get
                ),

            "probability": {

                key:
                    round(
                        value,
                        6
                    )

                for key, value
                in size_probability.items()
            }
        },


        "parity": {

            "prediction":
                max(
                    parity_probability,
                    key=parity_probability.get
                ),

            "probability": {

                key:
                    round(
                        value,
                        6
                    )

                for key, value
                in parity_probability.items()
            }
        },


        "wave": {

            "prediction":
                wave_single,

            "single":
                wave_single,

            "double":
                wave_double,

            "probability": {

                key:
                    round(
                        value,
                        6
                    )

                for key, value
                in wave_probability.items()
            }
        },


        "dynamic_weights": {

            key:
                round(
                    value,
                    6
                )

            for key, value
            in dynamic_weights.items()
        },
    }
