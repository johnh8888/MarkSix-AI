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


# =========================================================
# 号码 → 生肖
# =========================================================

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


# =========================================================
# 号码 → 波色
# =========================================================

NUMBER_TO_WAVE = {}

for wave, numbers in WAVE_MAP.items():

    for number in numbers:

        NUMBER_TO_WAVE[number] = wave


# =========================================================
# 工具：Min-Max
# =========================================================

def minmax_normalize(scores):

    if not scores:

        return {}

    values = list(
        scores.values()
    )

    low = min(values)

    high = max(values)

    if high == low:

        return {
            key: 0.5
            for key in scores
        }

    return {

        key:
            (
                value - low
            )
            /
            (
                high - low
            )

        for key, value in scores.items()
    }


# =========================================================
# Softmax
# =========================================================

def softmax(
    scores,
    temperature=1.0
):

    if not scores:

        return {}

    temperature = max(
        float(temperature),
        0.0001
    )

    maximum = max(
        scores.values()
    )

    import math

    exp_values = {}

    total = 0.0

    for key, value in scores.items():

        x = (
            value - maximum
        ) / temperature

        e = math.exp(x)

        exp_values[key] = e

        total += e

    if total <= 0:

        return {
            key: 0.0
            for key in scores
        }

    return {

        key:
            value / total

        for key, value
        in exp_values.items()
    }


# =========================================================
# 安全获取特码
# =========================================================

def _get_special_from_row(row):

    # -----------------------------------------------------
    # 优先使用 features.py
    # -----------------------------------------------------

    try:

        from .features import get_special

        number = get_special(row)

        number = int(number)

        if 1 <= number <= 49:

            return number

    except Exception:

        pass

    # -----------------------------------------------------
    # fallback：special
    # -----------------------------------------------------

    if "special" in row:

        try:

            number = int(
                row["special"]
            )

            if 1 <= number <= 49:

                return number

        except Exception:

            pass

    # -----------------------------------------------------
    # fallback：numbers
    # -----------------------------------------------------

    numbers = row.get(
        "numbers"
    )

    if numbers:

        if isinstance(
            numbers,
            str
        ):

            parts = [
                x.strip()
                for x in numbers.split(",")
                if x.strip()
            ]

        elif isinstance(
            numbers,
            (list, tuple)
        ):

            parts = list(
                numbers
            )

        else:

            parts = []

        if len(parts) >= 7:

            try:

                number = int(
                    parts[6]
                )

                if 1 <= number <= 49:

                    return number

            except Exception:

                pass

    raise ValueError(
        f"无法获取有效特码：{row}"
    )


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

        try:

            number = _get_special_from_row(
                row
            )

        except Exception:

            continue

        if number >= 25:

            big += 1

        else:

            small += 1

    total = (
        big +
        small
    )

    if total == 0:

        return {
            "大": 0.5,
            "小": 0.5
        }

    return {

        "大":
            big / total,

        "小":
            small / total
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

        try:

            number = _get_special_from_row(
                row
            )

        except Exception:

            continue

        if number % 2:

            odd += 1

        else:

            even += 1

    total = (
        odd +
        even
    )

    if total == 0:

        return {
            "单": 0.5,
            "双": 0.5
        }

    return {

        "单":
            odd / total,

        "双":
            even / total
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

        try:

            number = _get_special_from_row(
                row
            )

        except Exception:

            continue

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

            "红":
                1 / 3,

            "蓝":
                1 / 3,

            "绿":
                1 / 3
        }

    return {

        key:
            value / total

        for key, value
        in counts.items()
    }


# =========================================================
# 波色多窗口综合概率
#
# 30期：50%
# 60期：30%
# 100期：20%
#
# 不直接使用300期，
# 避免长期历史把近期状态冲淡。
# =========================================================

def calculate_wave_probability_multi_window(
    rows
):

    recent30 = calculate_wave_probability(
        rows[:30]
    )

    recent60 = calculate_wave_probability(
        rows[:60]
    )

    recent100 = calculate_wave_probability(
        rows[:100]
    )

    result = {}

    for wave in [
        "红",
        "蓝",
        "绿"
    ]:

        result[wave] = (

            recent30.get(
                wave,
                1 / 3
            )
            * 0.50

            +

            recent60.get(
                wave,
                1 / 3
            )
            * 0.30

            +

            recent100.get(
                wave,
                1 / 3
            )
            * 0.20
        )

    total = sum(
        result.values()
    )

    if total <= 0:

        return {
            "红": 1 / 3,
            "蓝": 1 / 3,
            "绿": 1 / 3
        }

    return {

        key:
            value / total

        for key, value in result.items()
    }


# =========================================================
# 号码综合评分
# =========================================================

def calculate_number_scores(rows):

    combined_scores, strategy_scores = (
        combine_strategies(rows)
    )

    base = minmax_normalize(
        combined_scores
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

    for number in range(
        1,
        50
    ):

        score = base.get(
            number,
            0.5
        )

        # -------------------------------------------------
        # 大小
        # -------------------------------------------------

        if number >= 25:

            size_score = (

                recent_size["大"]
                * 0.7

                +

                medium_size["大"]
                * 0.3
            )

        else:

            size_score = (

                recent_size["小"]
                * 0.7

                +

                medium_size["小"]
                * 0.3
            )

        # -------------------------------------------------
        # 单双
        # -------------------------------------------------

        if number % 2:

            parity_score = (

                recent_parity["单"]
                * 0.7

                +

                medium_parity["单"]
                * 0.3
            )

        else:

            parity_score = (

                recent_parity["双"]
                * 0.7

                +

                medium_parity["双"]
                * 0.3
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
            )
            * 0.7

            +

            medium_wave.get(
                wave,
                1 / 3
            )
            * 0.3
        )

        # -------------------------------------------------
        # 综合
        # -------------------------------------------------

        final_score = (

            score
            * 0.60

            +

            size_score
            * 0.15

            +

            parity_score
            * 0.10

            +

            wave_score
            * 0.15
        )

        scores[number] = final_score

    return scores


# =========================================================
# Top 号码
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
# 生肖评分
# =========================================================

def calculate_zodiac_scores(
    number_scores
):

    zodiac_scores = defaultdict(
        float
    )

    for number, score in number_scores.items():

        zodiac = NUMBER_TO_ZODIAC.get(
            number
        )

        if zodiac:

            zodiac_scores[zodiac] += score

    return dict(
        zodiac_scores
    )


# =========================================================
# Top 5 生肖
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
# 平特生肖评分
# =========================================================

def calculate_pingte_zodiac_scores(
    rows,
    number_scores
):

    zodiac_scores = defaultdict(
        float
    )

    history_count = defaultdict(
        int
    )

    for row in rows[:300]:

        try:

            number = _get_special_from_row(
                row
            )

        except Exception:

            continue

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

        numbers = ZODIAC_MAP_2026[
            zodiac
        ]

        number_score = 0.0

        for number in numbers:

            number_score += (
                number_scores.get(
                    number,
                    0.0
                )
            )

        number_score /= max(
            len(numbers),
            1
        )

        history_score = (
            history_count[zodiac]
            /
            total
        )

        zodiac_scores[zodiac] = (

            number_score
            * 0.70

            +

            history_score
            * 0.30
        )

    return dict(
        zodiac_scores
    )


# =========================================================
# 生成预测
# =========================================================

def generate_prediction(rows):

    if not rows:

        return {
            "error":
                "没有历史数据"
        }

    # =====================================================
    # 号码
    # =====================================================

    number_scores = calculate_number_scores(
        rows
    )

    top10 = get_top_numbers(
        number_scores,
        10
    )

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
    # 大小
    # =====================================================

    size_probability = (
        calculate_size_probability(
            rows[:100]
        )
    )

    size_prediction = max(
        size_probability,
        key=size_probability.get
    )

    # =====================================================
    # 单双
    # =====================================================

    parity_probability = (
        calculate_parity_probability(
            rows[:100]
        )
    )

    parity_prediction = max(
        parity_probability,
        key=parity_probability.get
    )

    # =====================================================
    # ⭐ 波色
    # =====================================================

    wave_probability = (
        calculate_wave_probability_multi_window(
            rows
        )
    )

    # -----------------------------------------------------
    # 波色排名
    # -----------------------------------------------------

    wave_ranking = sorted(

        wave_probability.items(),

        key=lambda x: (
            x[1],
            x[0]
        ),

        reverse=True
    )

    # -----------------------------------------------------
    # 波色单推
    # -----------------------------------------------------

    wave_prediction = (
        wave_ranking[0][0]
    )

    # -----------------------------------------------------
    # ⭐ 波色双推
    # -----------------------------------------------------

    top2_wave = wave_ranking[:2]

    # =====================================================
    # 输出
    # =====================================================

    return {

        # -------------------------------------------------
        # 特码10码
        # -------------------------------------------------

        "top10_numbers": [

            {
                "number":
                    number,

                "score":
                    round(
                        score,
                        6
                    )
            }

            for number, score
            in top10
        ],

        # -------------------------------------------------
        # 生肖5肖
        # -------------------------------------------------

        "top5_zodiac": [

            {
                "zodiac":
                    zodiac,

                "score":
                    round(
                        score,
                        6
                    )
            }

            for zodiac, score
            in top5_zodiac
        ],

        # -------------------------------------------------
        # 平特2肖
        # -------------------------------------------------

        "top2_pingte_zodiac": [

            {
                "zodiac":
                    zodiac,

                "score":
                    round(
                        score,
                        6
                    )
            }

            for zodiac, score
            in top2_pingte
        ],

        # -------------------------------------------------
        # 大小
        # -------------------------------------------------

        "size": {

            "prediction":
                size_prediction,

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

        # -------------------------------------------------
        # 单双
        # -------------------------------------------------

        "parity": {

            "prediction":
                parity_prediction,

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

        # -------------------------------------------------
        # ⭐ 波色
        # -------------------------------------------------

        "wave": {

            # 单推
            "prediction":
                wave_prediction,

            # 双推
            "top2": [

                {
                    "wave":
                        wave,

                    "probability":
                        round(
                            probability,
                            6
                        )
                }

                for wave, probability
                in top2_wave
            ],

            # 完整概率
            "probability": {

                key:
                    round(
                        value,
                        6
                    )

                for key, value
                in wave_probability.items()
            }
        }
    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "predictor.py 测试"
    )

    print("=" * 70)

    print()

    print(
        "2026生肖映射：",
        len(NUMBER_TO_ZODIAC)
    )

    print(
        "波色映射：",
        len(NUMBER_TO_WAVE)
    )
