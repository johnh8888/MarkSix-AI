# -*- coding:utf-8 -*-

"""
六合彩 AI V3.6 FINAL

2026年生肖模块

2026年为马年

特别生肖:
每次固定推荐5个生肖
"""


from collections import Counter


# =====================================================
# 2026生肖
# =====================================================

ZODIACS = [
    "马",
    "蛇",
    "龙",
    "兔",
    "虎",
    "牛",
    "鼠",
    "猪",
    "狗",
    "鸡",
    "猴",
    "羊",
]


# =====================================================
# 2026六合彩号码生肖
# =====================================================

ZODIAC_NUMBERS = {

    "马": [
        1, 13, 25, 37, 49
    ],

    "蛇": [
        2, 14, 26, 38
    ],

    "龙": [
        3, 15, 27, 39
    ],

    "兔": [
        4, 16, 28, 40
    ],

    "虎": [
        5, 17, 29, 41
    ],

    "牛": [
        6, 18, 30, 42
    ],

    "鼠": [
        7, 19, 31, 43
    ],

    "猪": [
        8, 20, 32, 44
    ],

    "狗": [
        9, 21, 33, 45
    ],

    "鸡": [
        10, 22, 34, 46
    ],

    "猴": [
        11, 23, 35, 47
    ],

    "羊": [
        12, 24, 36, 48
    ],
}


# =====================================================
# 自动生成号码 -> 生肖
# =====================================================

ZODIAC_MAP = {}

for zodiac, numbers in ZODIAC_NUMBERS.items():

    for number in numbers:

        ZODIAC_MAP[number] = zodiac


# =====================================================
# 获取生肖
# =====================================================

def get_zodiac(number):

    try:

        number = int(number)

    except (
        TypeError,
        ValueError
    ):

        return "未知"

    return ZODIAC_MAP.get(
        number,
        "未知"
    )


# =====================================================
# 提取特码
# =====================================================

def get_specials(history):

    result = []

    for row in history or []:

        if not isinstance(
            row,
            dict
        ):
            continue

        value = row.get(
            "special"
        )

        try:

            value = int(value)

        except (
            TypeError,
            ValueError
        ):

            continue

        if 1 <= value <= 49:

            result.append(
                value
            )

    return result


# =====================================================
# 历史生肖统计
# =====================================================

def zodiac_statistics(history):

    counter = Counter()

    for number in get_specials(history):

        zodiac = get_zodiac(
            number
        )

        if zodiac != "未知":

            counter[zodiac] += 1

    return {
        zodiac: counter.get(
            zodiac,
            0
        )
        for zodiac in ZODIACS
    }


# =====================================================
# 最近30期生肖统计
# =====================================================

def recent_zodiac_statistics(
    history,
    limit=30
):

    numbers = get_specials(
        history
    )

    recent = numbers[-limit:]

    counter = Counter()

    for number in recent:

        zodiac = get_zodiac(
            number
        )

        if zodiac != "未知":

            counter[zodiac] += 1

    return {
        zodiac: counter.get(
            zodiac,
            0
        )
        for zodiac in ZODIACS
    }


# =====================================================
# 生肖遗漏
# =====================================================

def zodiac_missing(history):

    numbers = get_specials(
        history
    )

    result = {}

    for zodiac in ZODIACS:

        missing = 0

        for number in reversed(
            numbers
        ):

            if get_zodiac(
                number
            ) == zodiac:

                break

            missing += 1

        result[zodiac] = missing

    return result


# =====================================================
# 生肖对应号码
# =====================================================

def zodiac_numbers(
    zodiac
):

    return ZODIAC_NUMBERS.get(
        zodiac,
        []
    )


# =====================================================
# 特别生肖预测
# =====================================================

def predict_zodiac(history):

    if not history:

        return {

            "推荐生肖": [],

            "特别生肖": [],

            "生肖评分": {},

            "对应号码": {},

            "历史统计": {},

            "近期统计": {},

            "遗漏": {},

            "状态": "数据不足",

        }


    history_stats = (
        zodiac_statistics(
            history
        )
    )


    recent_stats = (
        recent_zodiac_statistics(
            history,
            30
        )
    )


    missing = (
        zodiac_missing(
            history
        )
    )


    scores = {}


    for zodiac in ZODIACS:

        history_score = (
            history_stats[zodiac]
        )


        recent_score = (
            recent_stats[zodiac]
        )


        missing_score = min(

            missing[zodiac] / 5,

            10

        )


        score = (

            history_score * 1.0

            +

            recent_score * 2.0

            +

            missing_score

        )


        scores[zodiac] = round(
            score,
            3
        )


    ranking = sorted(

        scores.items(),

        key=lambda x: (

            x[1],

            recent_stats[x[0]],

            history_stats[x[0]],

        ),

        reverse=True

    )


    top5 = [

        zodiac

        for zodiac, score

        in ranking[:5]

    ]


    return {

        "推荐生肖": top5,

        "特别生肖": top5,

        "生肖评分": {

            zodiac:

            scores[zodiac]

            for zodiac in top5

        },

        "对应号码": {

            zodiac:

            zodiac_numbers(
                zodiac
            )

            for zodiac in top5

        },

        "历史统计": {

            zodiac:

            history_stats[zodiac]

            for zodiac in ZODIACS

        },

        "近期统计": {

            zodiac:

            recent_stats[zodiac]

            for zodiac in ZODIACS

        },

        "遗漏": {

            zodiac:

            missing[zodiac]

            for zodiac in ZODIACS

        },

        "状态": "正常",

    }


__all__ = [

    "get_zodiac",

    "predict_zodiac",

    "zodiac_statistics",

    "recent_zodiac_statistics",

    "zodiac_missing",

    "zodiac_numbers",

]
