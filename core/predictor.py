# -*- coding: utf-8 -*-

from collections import defaultdict

from .strategies import combine_strategies


# =========================================================
# 2026 年生肖号码
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
# 2026 波色
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
    ]
}


NUMBER_TO_WAVE = {}

for wave, numbers in WAVE_MAP.items():

    for number in numbers:
        NUMBER_TO_WAVE[number] = wave


# =========================================================
# 工具函数
# =========================================================

def minmax_normalize(scores):

    if not scores:
        return {}

    values = list(scores.values())

    low = min(values)
    high = max(values)

    if high == low:

        return {
            key: 0.5
            for key in scores
        }

    return {
        key: (
            (value - low) /
            (high - low)
        )
        for key, value in scores.items()
    }


def softmax(scores, temperature=1.0):

    if not scores:
        return {}

    temperature = max(
        float(temperature),
        0.0001
    )

    maximum = max(scores.values())

    exp_values = {}

    total = 0.0

    import math

    for key, value in scores.items():

        x = (
            (value - maximum)
            / temperature
        )

        e = math.exp(x)

        exp_values[key] = e

        total += e

    if total <= 0:
        return {
            key: 0.0
            for key in scores
        }

    return {
        key: value / total
        for key, value in exp_values.items()
    }


# =========================================================
# 大小概率
# =========================================================

def calculate_size_probability(rows):

    if not rows:

        return {
            "大": 0.5,
            "小": 0.5
        }

    big = 0
    small = 0

    for row in rows:

        number = int(row["special"])

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
        "大": big / total,
        "小": small / total
    }


# =========================================================
# 单双概率
# =========================================================

def calculate_parity_probability(rows):

    if not rows:

        return {
            "单": 0.5,
            "双": 0.5
        }

    odd = 0
    even = 0

    for row in rows:

        number = int(row["special"])

        if number % 2 == 1:
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
        "单": odd / total,
        "双": even / total
    }


# =========================================================
# 波色概率
# =========================================================

def calculate_wave_probability(rows):

    counts = {
        "红": 0,
        "蓝": 0,
        "绿": 0
    }

    for row in rows:

        number = int(row["special"])

        wave = NUMBER_TO_WAVE.get(number)

        if wave:
            counts[wave] += 1

    total = sum(counts.values())

    if total == 0:

        return {
            "红": 1 / 3,
            "蓝": 1 / 3,
            "绿": 1 / 3
        }

    return {
        key: value / total
        for key, value in counts.items()
    }


# =========================================================
# 号码综合评分
# =========================================================

def calculate_number_scores(rows):

    combined_scores, strategy_scores = combine_strategies(
        rows
    )

    # =====================================================
    # 基础模型评分
    # =====================================================

    base = minmax_normalize(
        combined_scores
    )

    # =====================================================
    # 最近30期 / 100期 / 300期
    # =====================================================

    recent = rows[:30]
    medium = rows[:100]
    long = rows[:300]

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

        score = base.get(
            number,
            0.5
        )

        # ---------------------------------------------
        # 大小
        # ---------------------------------------------

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

        # ---------------------------------------------
        # 单双
        # ---------------------------------------------

        if number % 2 == 1:

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

        # ---------------------------------------------
        # 波色
        # ---------------------------------------------

        wave = NUMBER_TO_WAVE.get(
            number
        )

        wave_score = (
            recent_wave.get(wave, 1 / 3)
            * 0.7
            +
            medium_wave.get(wave, 1 / 3)
            * 0.3
        )

        # ---------------------------------------------
        # 综合
        # ---------------------------------------------

        final_score = (

            score * 0.60

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
# Top 10 特码
# =========================================================

def get_top_numbers(scores, count=10):

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
# 生肖评分
# =========================================================

def calculate_zodiac_scores(number_scores):

    zodiac_scores = defaultdict(float)

    for number, score in number_scores.items():

        zodiac = NUMBER_TO_ZODIAC.get(
            number
        )

        if zodiac:

            zodiac_scores[zodiac] += score

    return dict(zodiac_scores)


# =========================================================
# 特码生肖 Top 5
# =========================================================

def get_top_zodiacs(
    zodiac_scores,
    count=5
):

    ranking = sorted(
        zodiac_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return ranking[:count]


# =========================================================
# 平特生肖模型
# =========================================================

def calculate_pingte_zodiac_scores(
    rows,
    number_scores
):

    # ---------------------------------------------
    # 平特生肖不能简单等同于特码生肖
    #
    # 第一版采用：
    #
    # 号码综合评分
    # +
    # 生肖覆盖能力
    # +
    # 历史出现频率
    #
    # 后续回测后再优化
    # ---------------------------------------------

    zodiac_scores = defaultdict(float)

    # 历史生肖出现次数
    history_count = defaultdict(int)

    for row in rows[:300]:

        number = int(row["special"])

        zodiac = NUMBER_TO_ZODIAC.get(
            number
        )

        if zodiac:
            history_count[zodiac] += 1

    total = max(
        sum(history_count.values()),
        1
    )

    for zodiac in ZODIAC_MAP_2026:

        numbers = ZODIAC_MAP_2026[zodiac]

        # 当前号码模型得分
        number_score = 0.0

        for number in numbers:

            number_score += number_scores.get(
                number,
                0.0
            )

        # 归一化
        number_score /= max(
            len(numbers),
            1
        )

        # 历史频率
        history_score = (
            history_count[zodiac]
            / total
        )

        # 综合
        zodiac_scores[zodiac] = (

            number_score * 0.70

            +

            history_score * 0.30
        )

    return dict(zodiac_scores)


# =========================================================
# 预测结果
# =========================================================

def generate_prediction(rows):

    if not rows:

        return {
            "error": "没有历史数据"
        }

    # ---------------------------------------------
    # 号码
    # ---------------------------------------------

    number_scores = calculate_number_scores(
        rows
    )

    top10 = get_top_numbers(
        number_scores,
        10
    )

    # ---------------------------------------------
    # 特码生肖
    # ---------------------------------------------

    zodiac_scores = calculate_zodiac_scores(
        number_scores
    )

    top5_zodiac = get_top_zodiacs(
        zodiac_scores,
        5
    )

    # ---------------------------------------------
    # 平特生肖
    # ---------------------------------------------

    pingte_scores = calculate_pingte_zodiac_scores(
        rows,
        number_scores
    )

    top2_pingte = get_top_zodiacs(
        pingte_scores,
        2
    )

    # ---------------------------------------------
    # 属性
    # ---------------------------------------------

    size_probability = calculate_size_probability(
        rows[:100]
    )

    parity_probability = calculate_parity_probability(
        rows[:100]
    )

    wave_probability = calculate_wave_probability(
        rows[:100]
    )

    size_prediction = max(
        size_probability,
        key=size_probability.get
    )

    parity_prediction = max(
        parity_probability,
        key=parity_probability.get
    )

    wave_prediction = max(
        wave_probability,
        key=wave_probability.get
    )

    # ---------------------------------------------
    # 输出
    # ---------------------------------------------

    return {

        "top10_numbers": [
            {
                "number": number,
                "score": round(
                    score,
                    6
                )
            }

            for number, score
            in top10
        ],

        "top5_zodiac": [
            {
                "zodiac": zodiac,
                "score": round(
                    score,
                    6
                )
            }

            for zodiac, score
            in top5_zodiac
        ],

        "top2_pingte_zodiac": [
            {
                "zodiac": zodiac,
                "score": round(
                    score,
                    6
                )
            }

            for zodiac, score
            in top2_pingte
        ],

        "size": {
            "prediction": size_prediction,
            "probability": {
                key: round(
                    value,
                    6
                )

                for key, value
                in size_probability.items()
            }
        },

        "parity": {
            "prediction": parity_prediction,
            "probability": {
                key: round(
                    value,
                    6
                )

                for key, value
                in parity_probability.items()
            }
        },

        "wave": {
            "prediction": wave_prediction,
            "probability": {
                key: round(
                    value,
                    6
                )

                for key, value
                in wave_probability.items()
            }
        }
    }
