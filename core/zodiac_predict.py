# -*- coding: utf-8 -*-

"""
六合彩生肖预测模块
V3.6 FINAL

说明：
2026 为马年。

本模块负责：

1. 号码 -> 生肖
2. 生肖 -> 号码
3. 统计生肖历史频率
4. 统计近期生肖趋势
5. 计算生肖遗漏
6. 计算生肖综合评分
7. 输出特别生肖 Top 5
"""

from collections import Counter


# ============================================================
# 2026 马年生肖号码
# ============================================================
#
# 2026 年为马年：
#
# 马：01 13 25 37 49
# 蛇：02 14 26 38
# 龙：03 15 27 39
# 兔：04 16 28 40
# 虎：05 17 29 41
# 牛：06 18 30 42
# 鼠：07 19 31 43
# 猪：08 20 32 44
# 狗：09 21 33 45
# 鸡：10 22 34 46
# 猴：11 23 35 47
# 羊：12 24 36 48
#
# ============================================================

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


# ============================================================
# 反向映射
# ============================================================

NUMBER_TO_ZODIAC = {}

for zodiac, numbers in ZODIAC_MAP_2026.items():

    for number in numbers:

        NUMBER_TO_ZODIAC[number] = zodiac


# ============================================================
# 基础校验
# ============================================================

def validate_mapping():

    numbers = sorted(
        NUMBER_TO_ZODIAC.keys()
    )

    expected = list(
        range(1, 50)
    )

    if numbers != expected:

        raise RuntimeError(
            "生肖号码映射错误："
            "1~49 不完整或存在重复"
        )

    return True


validate_mapping()


# ============================================================
# 号码 -> 生肖
# ============================================================

def get_zodiac(number):

    try:

        number = int(number)

    except (
        TypeError,
        ValueError,
    ):

        return "未知"

    if number < 1 or number > 49:

        return "未知"

    return NUMBER_TO_ZODIAC.get(
        number,
        "未知"
    )


# ============================================================
# 生肖 -> 号码
# ============================================================

def get_numbers_by_zodiac(
    zodiac
):

    return list(
        ZODIAC_MAP_2026.get(
            zodiac,
            []
        )
    )


# ============================================================
# 提取特码
# ============================================================

def _extract_specials(history):

    result = []

    for row in history:

        if not isinstance(
            row,
            dict
        ):

            continue

        value = row.get(
            "special"
        )

        if value is None:

            value = row.get(
                "special_number"
            )

        if value is None:

            value = row.get(
                "specialNumber"
            )

        try:

            value = int(value)

        except (
            TypeError,
            ValueError,
        ):

            continue

        if 1 <= value <= 49:

            result.append(
                value
            )

    return result


# ============================================================
# 生肖历史统计
# ============================================================

def zodiac_statistics(
    history
):

    specials = _extract_specials(
        history
    )

    counter = Counter()

    for number in specials:

        zodiac = get_zodiac(
            number
        )

        if zodiac != "未知":

            counter[zodiac] += 1

    total = len(
        specials
    )

    result = {}

    for zodiac in ZODIAC_MAP_2026:

        count = counter.get(
            zodiac,
            0
        )

        result[zodiac] = {

            "数量": count,

            "比例":
                round(
                    count / total,
                    4
                )
                if total
                else 0,

            "号码":
                get_numbers_by_zodiac(
                    zodiac
                ),
        }

    return result


# ============================================================
# 最近 N 期生肖统计
# ============================================================

def recent_zodiac_rate(
    history,
    periods=30
):

    specials = _extract_specials(
        history
    )

    recent = specials[
        -periods:
    ]

    counter = Counter()

    for number in recent:

        zodiac = get_zodiac(
            number
        )

        if zodiac != "未知":

            counter[zodiac] += 1

    total = len(
        recent
    )

    result = {}

    for zodiac in ZODIAC_MAP_2026:

        count = counter.get(
            zodiac,
            0
        )

        result[zodiac] = round(
            count / total,
            4
        ) if total else 0

    return result


# ============================================================
# 生肖遗漏
# ============================================================

def zodiac_missing(
    history
):

    specials = _extract_specials(
        history
    )

    result = {}

    for zodiac in ZODIAC_MAP_2026:

        missing = 0

        for number in reversed(
            specials
        ):

            if get_zodiac(
                number
            ) == zodiac:

                break

            missing += 1

        else:

            missing = len(
                specials
            )

        result[zodiac] = missing

    return result


# ============================================================
# 生肖评分
# ============================================================

def zodiac_scores(
    history
):

    statistics = zodiac_statistics(
        history
    )

    recent10 = recent_zodiac_rate(
        history,
        10
    )

    recent30 = recent_zodiac_rate(
        history,
        30
    )

    missing = zodiac_missing(
        history
    )

    scores = {}

    for zodiac in ZODIAC_MAP_2026:

        history_rate = statistics[
            zodiac
        ]["比例"]

        recent10_rate = recent10[
            zodiac
        ]

        recent30_rate = recent30[
            zodiac
        ]

        missing_count = missing[
            zodiac
        ]

        # ----------------------------------------------------
        # 综合评分
        # ----------------------------------------------------
        #
        # 历史频率       35%
        # 最近10期       25%
        # 最近30期       25%
        # 适度遗漏       15%
        #
        # ----------------------------------------------------

        score = (

            history_rate * 35

            +

            recent10_rate * 25

            +

            recent30_rate * 25

            +

            min(
                missing_count / 30,
                1
            ) * 15

        )

        scores[zodiac] = round(
            score,
            4
        )

    return scores


# ============================================================
# 特别生肖 Top 5
# ============================================================

def predict_zodiac(
    history
):

    statistics = zodiac_statistics(
        history
    )

    recent10 = recent_zodiac_rate(
        history,
        10
    )

    recent30 = recent_zodiac_rate(
        history,
        30
    )

    missing = zodiac_missing(
        history
    )

    scores = zodiac_scores(
        history
    )

    ranking = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top5 = ranking[:5]

    result = []

    for rank, (
        zodiac,
        score
    ) in enumerate(
        top5,
        start=1
    ):

        result.append({

            "排名":
                rank,

            "生肖":
                zodiac,

            "评分":
                score,

            "对应号码":
                get_numbers_by_zodiac(
                    zodiac
                ),

            "历史次数":
                statistics[
                    zodiac
                ]["数量"],

            "历史比例":
                statistics[
                    zodiac
                ]["比例"],

            "最近10期":
                recent10[
                    zodiac
                ],

            "最近30期":
                recent30[
                    zodiac
                ],

            "遗漏期数":
                missing[
                    zodiac
                ],

        })

    # ========================================================
    # 所有生肖完整评分
    # ========================================================

    all_zodiac = []

    for zodiac, score in ranking:

        all_zodiac.append({

            "生肖":
                zodiac,

            "评分":
                score,

            "对应号码":
                get_numbers_by_zodiac(
                    zodiac
                ),

            "历史次数":
                statistics[
                    zodiac
                ]["数量"],

            "最近10期":
                recent10[
                    zodiac
                ],

            "最近30期":
                recent30[
                    zodiac
                ],

            "遗漏期数":
                missing[
                    zodiac
                ],

        })

    # ========================================================
    # 简洁输出
    # ========================================================

    return {

        "特别生肖":
            [
                item["生肖"]
                for item in result
            ],

        "特别生肖Top5":
            result,

        "完整生肖评分":
            all_zodiac,

        "号码对应生肖":
            {
                str(number):
                    get_zodiac(number)
                for number in range(
                    1,
                    50
                )
            },

    }


# ============================================================
# 简洁版
# ============================================================

def predict_zodiac_simple(
    history
):

    data = predict_zodiac(
        history
    )

    return {

        "特别生肖":
            data[
                "特别生肖"
            ],

        "对应号码":
            {
                item["生肖"]:
                    item["对应号码"]
                for item in data[
                    "特别生肖Top5"
                ]
            },

    }


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "2026六合彩生肖映射检查"
    )

    print("=" * 60)

    for number in range(
        1,
        50
    ):

        print(
            f"{number:02d} -> "
            f"{get_zodiac(number)}"
        )

    print()

    print(
        "验证结果:",
        validate_mapping()
    )
