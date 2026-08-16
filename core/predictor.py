# -*- coding: utf-8 -*-

from collections import defaultdict
from itertools import combinations
import math

from .strategies import (
    combine_strategies,
    get_special,
)


# =========================================================
# 2026 生肖
# =========================================================

ZODIAC_MAP_2026 = {

    "马":
        [1, 13, 25, 37, 49],

    "蛇":
        [2, 14, 26, 38],

    "龙":
        [3, 15, 27, 39],

    "兔":
        [4, 16, 28, 40],

    "虎":
        [5, 17, 29, 41],

    "牛":
        [6, 18, 30, 42],

    "鼠":
        [7, 19, 31, 43],

    "猪":
        [8, 20, 32, 44],

    "狗":
        [9, 21, 33, 45],

    "鸡":
        [10, 22, 34, 46],

    "猴":
        [11, 23, 35, 47],

    "羊":
        [12, 24, 36, 48],
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
# 基础归一化
# =========================================================

def normalize(values):

    if not values:

        return {}

    low = min(
        values.values()
    )

    high = max(
        values.values()
    )

    if high == low:

        return {
            k: 0.5
            for k in values
        }

    return {

        k:
            (
                value - low
            )
            /
            (
                high - low
            )

        for k, value
        in values.items()
    }


# =========================================================
# 大小独立模型
# =========================================================

def calculate_size_model(rows):

    result = {
        "大": 0.5,
        "小": 0.5,
    }

    if not rows:

        return result

    scores = {}

    for window, weight in [
        (10, 0.60),
        (20, 0.40),
    ]:

        subset = rows[:window]

        big = 0
        small = 0

        for row in subset:

            n = get_special(row)

            if not 1 <= n <= 49:
                continue

            if n >= 25:
                big += 1
            else:
                small += 1

        total = big + small

        if total == 0:
            continue

        scores["大"] = (
            scores.get("大", 0)
            +
            (
                (
                    big + 1
                )
                /
                (
                    total + 2
                )
            )
            * weight
        )

        scores["小"] = (
            scores.get("小", 0)
            +
            (
                (
                    small + 1
                )
                /
                (
                    total + 2
                )
            )
            * weight
        )

    total = sum(
        scores.values()
    )

    if total <= 0:
        return result

    return {
        k: v / total
        for k, v in scores.items()
    }


# =========================================================
# 单双独立模型
# =========================================================

def calculate_parity_model(rows):

    result = {
        "单": 0.5,
        "双": 0.5,
    }

    if not rows:

        return result

    scores = {}

    for window, weight in [
        (10, 0.60),
        (20, 0.40),
    ]:

        subset = rows[:window]

        odd = 0
        even = 0

        for row in subset:

            n = get_special(row)

            if not 1 <= n <= 49:
                continue

            if n % 2:

                odd += 1

            else:

                even += 1

        total = odd + even

        if total == 0:
            continue

        scores["单"] = (
            scores.get("单", 0)
            +
            (
                (odd + 1)
                /
                (total + 2)
            )
            * weight
        )

        scores["双"] = (
            scores.get("双", 0)
            +
            (
                (even + 1)
                /
                (total + 2)
            )
            * weight
        )

    total = sum(
        scores.values()
    )

    if total <= 0:
        return result

    return {
        k: v / total
        for k, v in scores.items()
    }


# =========================================================
# 波色独立模型
# =========================================================

def calculate_wave_model(rows):

    windows = [
        (10, 0.45),
        (20, 0.30),
        (50, 0.15),
        (100, 0.10),
    ]

    scores = {
        wave: 0.0
        for wave in WAVE_MAP
    }

    for window, weight in windows:

        subset = rows[:window]

        counts = {
            wave: 1.0
            for wave in WAVE_MAP
        }

        for row in subset:

            n = get_special(row)

            wave = NUMBER_TO_WAVE.get(
                n
            )

            if wave:

                counts[wave] += 1

        total = sum(
            counts.values()
        )

        if total <= 0:
            continue

        for wave in WAVE_MAP:

            scores[wave] += (
                counts[wave]
                /
                total
            ) * weight

    total = sum(
        scores.values()
    )

    if total <= 0:

        return {
            wave: 1 / 3
            for wave in WAVE_MAP
        }

    return {
        wave:
            scores[wave] / total
        for wave in WAVE_MAP
    }


# =========================================================
# 波色连续性
# =========================================================

def calculate_wave_transition(rows):

    transition = {
        a: {
            b: 1.0
            for b in WAVE_MAP
        }
        for a in WAVE_MAP
    }

    previous = None

    for row in reversed(
        rows[:100]
    ):

        n = get_special(row)

        wave = NUMBER_TO_WAVE.get(
            n
        )

        if not wave:
            continue

        if previous is not None:

            transition[
                previous
            ][wave] += 1

        previous = wave

    latest = None

    if rows:

        latest = NUMBER_TO_WAVE.get(
            get_special(rows[0])
        )

    if latest not in WAVE_MAP:

        return {
            wave: 1 / 3
            for wave in WAVE_MAP
        }

    scores = {}

    values = transition[
        latest
    ]

    total = sum(
        values.values()
    )

    for wave in WAVE_MAP:

        scores[wave] = (
            values[wave]
            /
            total
        )

    return scores


# =========================================================
# 波色综合
# =========================================================

def final_wave_model(rows):

    frequency = calculate_wave_model(
        rows
    )

    transition = calculate_wave_transition(
        rows
    )

    scores = {}

    for wave in WAVE_MAP:

        scores[wave] = (
            frequency.get(
                wave,
                1 / 3
            )
            * 0.70
            +
            transition.get(
                wave,
                1 / 3
            )
            * 0.30
        )

    total = sum(
        scores.values()
    )

    return {
        wave:
            scores[wave] / total
        for wave in scores
    }


# =========================================================
# 波色双推
# =========================================================

def calculate_wave_pairs(
    wave_scores
):

    pairs = []

    for a, b in combinations(
        WAVE_MAP.keys(),
        2
    ):

        score = (
            wave_scores.get(
                a,
                0
            )
            +
            wave_scores.get(
                b,
                0
            )
        )

        pairs.append({

            "pair": [
                a,
                b
            ],

            "score":
                score,
        })

    pairs.sort(
        key=lambda x:
            x["score"],
        reverse=True
    )

    return pairs


# =========================================================
# 号码综合评分
# =========================================================

def calculate_number_scores(rows):

    combined, strategies = combine_strategies(
        rows
    )

    scores = {}

    for n in range(1, 50):

        base = combined.get(
            n,
            0.5
        )

        # -------------------------------------------------
        # 近期增强
        # -------------------------------------------------

        recent10 = strategies.get(
            "recent10",
            {}
        ).get(
            n,
            0.5
        )

        recent20 = strategies.get(
            "recent20",
            {}
        ).get(
            n,
            0.5
        )

        omission = strategies.get(
            "omission_decay",
            {}
        ).get(
            n,
            0.5
        )

        tail = strategies.get(
            "tail",
            {}
        ).get(
            n,
            0.5
        )

        zone = strategies.get(
            "zone",
            {}
        ).get(
            n,
            0.5
        )

        # -------------------------------------------------
        # 最终
        # -------------------------------------------------

        score = (

            base * 0.55

            +

            recent10 * 0.15

            +

            recent20 * 0.12

            +

            omission * 0.08

            +

            tail * 0.05

            +

            zone * 0.05
        )

        scores[n] = score

    return normalize(
        scores
    )


# =========================================================
# Top号码
# =========================================================

def get_number_ranking(scores):

    ranking = sorted(
        scores.items(),
        key=lambda x: (
            x[1],
            -x[0]
        ),
        reverse=True
    )

    return ranking


# =========================================================
# 生肖模型
# =========================================================

def calculate_zodiac_scores(
    rows,
    number_scores
):

    scores = {}

    for zodiac, numbers in ZODIAC_MAP_2026.items():

        # 当前号码模型
        number_component = sum(
            number_scores.get(
                n,
                0
            )
            for n in numbers
        )

        number_component /= max(
            len(numbers),
            1
        )

        # 最近20期生肖表现
        recent_count = 0

        for row in rows[:20]:

            n = get_special(row)

            if NUMBER_TO_ZODIAC.get(n) == zodiac:

                recent_count += 1

        recent_component = (
            recent_count + 1
        ) / 22

        # 最近50期
        medium_count = 0

        for row in rows[:50]:

            n = get_special(row)

            if NUMBER_TO_ZODIAC.get(n) == zodiac:

                medium_count += 1

        medium_component = (
            medium_count + 1
        ) / 52

        scores[zodiac] = (

            number_component * 0.55

            +

            recent_component * 0.30

            +

            medium_component * 0.15
        )

    return scores


# =========================================================
# 平特模型
# =========================================================

def calculate_pingte_scores(rows):

    scores = {}

    for zodiac, numbers in ZODIAC_MAP_2026.items():

        # -------------------------------------------------
        # 近期出现
        # -------------------------------------------------

        recent = 0

        for row in rows[:20]:

            n = get_special(row)

            if NUMBER_TO_ZODIAC.get(n) == zodiac:

                recent += 1

        # -------------------------------------------------
        # 遗漏
        # -------------------------------------------------

        omission = 20

        for index, row in enumerate(
            rows[:100]
        ):

            n = get_special(row)

            if NUMBER_TO_ZODIAC.get(n) == zodiac:

                omission = index
                break

        # -------------------------------------------------
        # 号码覆盖
        # -------------------------------------------------

        active = 0

        for n in numbers:

            for row in rows[:50]:

                if get_special(row) == n:

                    active += 1
                    break

        coverage = (
            active
            /
            max(len(numbers), 1)
        )

        recent_score = (
            recent + 1
        ) / 22

        omission_score = (
            omission + 1
        ) / 101

        scores[zodiac] = (

            coverage * 0.45

            +

            recent_score * 0.25

            +

            omission_score * 0.30
        )

    return scores


# =========================================================
# 属性预测
# =========================================================

def generate_attributes(rows):

    size = calculate_size_model(
        rows
    )

    parity = calculate_parity_model(
        rows
    )

    return {

        "size": {

            "prediction":
                max(
                    size,
                    key=size.get
                ),

            "probability":
                {
                    k:
                        round(v, 6)
                    for k, v
                    in size.items()
                },
        },

        "parity": {

            "prediction":
                max(
                    parity,
                    key=parity.get
                ),

            "probability":
                {
                    k:
                        round(v, 6)
                    for k, v
                    in parity.items()
                },
        },
    }


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
    # 号码
    # =====================================================

    number_scores = calculate_number_scores(
        rows
    )

    ranking = get_number_ranking(
        number_scores
    )

    top10 = ranking[:10]

    top3 = ranking[:3]

    first = ranking[0]

    # =====================================================
    # 生肖
    # =====================================================

    zodiac_scores = calculate_zodiac_scores(
        rows,
        number_scores
    )

    zodiac_ranking = sorted(
        zodiac_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # =====================================================
    # 平特
    # =====================================================

    pingte_scores = calculate_pingte_scores(
        rows
    )

    pingte_ranking = sorted(
        pingte_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # =====================================================
    # 属性
    # =====================================================

    attributes = generate_attributes(
        rows
    )

    # =====================================================
    # 波色
    # =====================================================

    wave_scores = final_wave_model(
        rows
    )

    wave_pairs = calculate_wave_pairs(
        wave_scores
    )

    wave_single = max(
        wave_scores,
        key=wave_scores.get
    )

    wave_double = wave_pairs[0]["pair"]

    # =====================================================
    # 输出
    # =====================================================

    return {

        # -------------------------------------------------
        # 号码
        # -------------------------------------------------

        "top10_numbers": [

            {
                "number":
                    n,

                "score":
                    round(
                        score,
                        6
                    ),
            }

            for n, score
            in top10
        ],

        "top3_numbers": [

            {
                "number":
                    n,

                "score":
                    round(
                        score,
                        6
                    ),
            }

            for n, score
            in top3
        ],

        "first_number": {

            "number":
                first[0],

            "score":
                round(
                    first[1],
                    6
                ),
        },

        "number_ranking": [

            {
                "number":
                    n,

                "score":
                    round(
                        score,
                        6
                    ),
            }

            for n, score
            in ranking
        ],

        # -------------------------------------------------
        # 生肖
        # -------------------------------------------------

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
            in zodiac_ranking[:5]
        ],

        # -------------------------------------------------
        # 平特
        # -------------------------------------------------

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
            in pingte_ranking[:2]
        ],

        # -------------------------------------------------
        # 大小
        # -------------------------------------------------

        "size":
            attributes["size"],

        # -------------------------------------------------
        # 单双
        # -------------------------------------------------

        "parity":
            attributes["parity"],

        # -------------------------------------------------
        # 波色
        # -------------------------------------------------

        "wave": {

            "prediction":
                wave_single,

            "single_prediction":
                wave_single,

            "double_prediction":
                wave_double,

            "probability": {

                k:
                    round(
                        v,
                        6
                    )

                for k, v
                in wave_scores.items()
            },

            "double_combinations": [

                {
                    "pair":
                        item["pair"],

                    "score":
                        round(
                            item["score"],
                            6
                        ),
                }

                for item
                in wave_pairs
            ],
        },

        # -------------------------------------------------
        # 随机基准
        # -------------------------------------------------

        "random_baseline": {

            "number_top10":
                10 / 49,

            "wave_single":
                1 / 3,

            "wave_double":
                2 / 3,
        },
    }
