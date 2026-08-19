# -*- coding: utf-8 -*-

"""
六合彩 V7.2 命中率统计模块

核心规则：

1. 号码只针对第7个特别号码
2. 每期开奖最多命中1个特别号码
3. 生肖针对特别号码推荐5个
4. 单双只推荐1个
5. 大小只推荐1个
6. 波色：
   - 主推1个
   - 次推1个
   - 双色2个
7. Walk-Forward 使用历史数据逐期验证
"""

from __future__ import annotations

from collections import Counter
from typing import Any


# ============================================================
# 波色
# ============================================================

RED = {
    1, 2, 7, 8, 12, 13, 18, 19, 23, 24,
    29, 30, 34, 35, 40, 45, 46
}

BLUE = {
    3, 4, 9, 10, 14, 15, 20, 25, 26, 31,
    36, 37, 41, 42, 47, 48
}

GREEN = {
    5, 6, 11, 16, 17, 21, 22, 27, 28, 32,
    33, 38, 39, 43, 44, 49
}


# ============================================================
# 基础属性
# ============================================================

def get_wave(number: int) -> str:

    number = int(number)

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return ""


def get_size(number: int) -> str:

    return "大" if int(number) >= 25 else "小"


def get_odd_even(number: int) -> str:

    return "单" if int(number) % 2 else "双"


# ============================================================
# 生肖
# ============================================================

def zodiac_by_year(
    number: int,
    year: int,
) -> str:

    animals = [
        "鼠",
        "牛",
        "虎",
        "兔",
        "龙",
        "蛇",
        "马",
        "羊",
        "猴",
        "鸡",
        "狗",
        "猪",
    ]

    # 2024 = 龙
    base_index = 4

    index = (
        base_index
        + (year - 2024)
    ) % 12

    return animals[
        (index - (int(number) - 1)) % 12
    ]


def get_zodiac(
    number: int,
    issue: str,
) -> str:

    try:

        year = int(
            str(issue)[:4]
        )

    except Exception:

        year = 2026

    return zodiac_by_year(
        int(number),
        year,
    )


# ============================================================
# 特别号码
# ============================================================

def get_special_number(
    record: dict[str, Any],
) -> int | None:

    numbers = record.get(
        "numbers",
        [],
    )

    if not isinstance(
        numbers,
        (list, tuple),
    ):
        return None

    if len(numbers) != 7:
        return None

    try:

        number = int(
            numbers[6]
        )

    except Exception:

        return None

    if not 1 <= number <= 49:
        return None

    return number


# ============================================================
# 历史特别号码属性统计
# ============================================================

def latest_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 50,
) -> Counter:

    counter = Counter()

    for row in history[-limit:]:

        special = get_special_number(
            row
        )

        if special is None:
            continue

        issue = str(
            row.get(
                "issue",
                "",
            )
        )

        if field == "wave":

            value = get_wave(
                special
            )

        elif field == "size":

            value = get_size(
                special
            )

        elif field == "odd_even":

            value = get_odd_even(
                special
            )

        elif field == "zodiac":

            value = get_zodiac(
                special,
                issue,
            )

        else:

            continue

        if value:
            counter[value] += 1

    return counter


# ============================================================
# 生肖预测：5个
# ============================================================

def predict_zodiac(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = latest_attribute(
        history,
        "zodiac",
        50,
    )

    animals = [
        "鼠",
        "牛",
        "虎",
        "兔",
        "龙",
        "蛇",
        "马",
        "羊",
        "猴",
        "鸡",
        "狗",
        "猪",
    ]

    ranking = sorted(
        animals,
        key=lambda x: (
            -counter.get(x, 0),
            animals.index(x),
        ),
    )

    top5 = ranking[:5]

    return {
        "main": top5[0] if top5 else "",
        "secondary": (
            top5[1]
            if len(top5) > 1
            else ""
        ),
        "top5": top5,
        "double": top5,
    }


# ============================================================
# 单双预测：只推一个
# ============================================================

def predict_odd_even(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = latest_attribute(
        history,
        "odd_even",
        50,
    )

    if not counter:

        return {
            "main": "",
        }

    main = sorted(
        ["单", "双"],
        key=lambda x: (
            -counter.get(x, 0),
            x,
        ),
    )[0]

    return {
        "main": main,
    }


# ============================================================
# 大小预测：只推一个
# ============================================================

def predict_size(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = latest_attribute(
        history,
        "size",
        50,
    )

    if not counter:

        return {
            "main": "",
        }

    main = sorted(
        ["大", "小"],
        key=lambda x: (
            -counter.get(x, 0),
            x,
        ),
    )[0]

    return {
        "main": main,
    }


# ============================================================
# 波色预测
# ============================================================

def predict_wave(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = latest_attribute(
        history,
        "wave",
        50,
    )

    colors = [
        "红",
        "蓝",
        "绿",
    ]

    ranking = sorted(
        colors,
        key=lambda x: (
            -counter.get(x, 0),
            colors.index(x),
        ),
    )

    main = ranking[0]

    secondary = (
        ranking[1]
        if len(ranking) > 1
        else ""
    )

    return {
        "main": main,
        "secondary": secondary,
        "double": [
            main,
            secondary,
        ],
    }


# ============================================================
# 统一属性预测
# ============================================================

def predict_attribute(
    history: list[dict[str, Any]],
    field: str,
) -> dict[str, Any]:

    if field == "zodiac":

        return predict_zodiac(
            history
        )

    if field == "odd_even":

        return predict_odd_even(
            history
        )

    if field == "size":

        return predict_size(
            history
        )

    if field == "wave":

        return predict_wave(
            history
        )

    return {
        "main": "",
    }


# ============================================================
# 命中率
# ============================================================

def hit_rate(
    hits: int,
    total: int,
) -> float:

    if total <= 0:
        return 0.0

    return round(
        hits / total * 100,
        2,
    )


# ============================================================
# Walk-Forward 单期评估
# ============================================================

def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:

    special = get_special_number(
        actual
    )

    if special is None:
        return {}

    issue = str(
        actual.get(
            "issue",
            "",
        )
    )

    # --------------------------------------------------------
    # 号码
    # --------------------------------------------------------

    top5 = set(
        prediction.get(
            "top5",
            [],
        )
    )

    top10 = set(
        prediction.get(
            "top10",
            [],
        )
    )

    top12 = set(
        prediction.get(
            "top12",
            [],
        )
    )

    result = {

        # 特别号码只能命中一次
        "number_top5":
            special in top5,

        "number_top10":
            special in top10,

        "number_top12":
            special in top12,
    }

    # --------------------------------------------------------
    # 生肖
    # --------------------------------------------------------

    actual_zodiac = get_zodiac(
        special,
        issue,
    )

    zodiac_prediction = prediction.get(
        "attributes",
        {},
    ).get(
        "zodiac",
        {},
    )

    zodiac_top5 = zodiac_prediction.get(
        "top5",
        [],
    )

    result[
        "zodiac_top5"
    ] = (
        actual_zodiac
        in zodiac_top5
    )

    # --------------------------------------------------------
    # 单双
    # --------------------------------------------------------

    actual_odd_even = get_odd_even(
        special
    )

    odd_prediction = prediction.get(
        "attributes",
        {},
    ).get(
        "odd_even",
        {},
    )

    result[
        "odd_even_main"
    ] = (
        actual_odd_even
        == odd_prediction.get(
            "main",
            "",
        )
    )

    # --------------------------------------------------------
    # 大小
    # --------------------------------------------------------

    actual_size = get_size(
        special
    )

    size_prediction = prediction.get(
        "attributes",
        {},
    ).get(
        "size",
        {},
    )

    result[
        "size_main"
    ] = (
        actual_size
        == size_prediction.get(
            "main",
            "",
        )
    )

    # --------------------------------------------------------
    # 波色
    # --------------------------------------------------------

    actual_wave = get_wave(
        special
    )

    wave_prediction = prediction.get(
        "attributes",
        {},
    ).get(
        "wave",
        {},
    )

    result[
        "wave_main"
    ] = (
        actual_wave
        == wave_prediction.get(
            "main",
            "",
        )
    )

    result[
        "wave_secondary"
    ] = (
        actual_wave
        == wave_prediction.get(
            "secondary",
            "",
        )
    )

    result[
        "wave_double"
    ] = (
        actual_wave
        in wave_prediction.get(
            "double",
            [],
        )
    )

    return result


# ============================================================
# Walk-Forward 性能汇总
# ============================================================

def calculate_performance(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(
        evaluations
    )

    if total == 0:

        return {
            "samples": 0,
            "status": "历史数据不足",
        }

    def count(
        key: str,
    ) -> int:

        return sum(
            1
            for item in evaluations
            if item.get(key)
        )

    return {

        "samples":
            total,

        # ----------------------------------------------------
        # 特别号码
        # ----------------------------------------------------

        "numbers": {

            "top5":
                hit_rate(
                    count(
                        "number_top5"
                    ),
                    total,
                ),

            "top10":
                hit_rate(
                    count(
                        "number_top10"
                    ),
                    total,
                ),

            "top12":
                hit_rate(
                    count(
                        "number_top12"
                    ),
                    total,
                ),
        },

        # ----------------------------------------------------
        # 生肖5推
        # ----------------------------------------------------

        "zodiac": {

            "top5":
                hit_rate(
                    count(
                        "zodiac_top5"
                    ),
                    total,
                ),
        },

        # ----------------------------------------------------
        # 单双单推
        # ----------------------------------------------------

        "odd_even": {

            "main":
                hit_rate(
                    count(
                        "odd_even_main"
                    ),
                    total,
                ),
        },

        # ----------------------------------------------------
        # 大小单推
        # ----------------------------------------------------

        "size": {

            "main":
                hit_rate(
                    count(
                        "size_main"
                    ),
                    total,
                ),
        },

        # ----------------------------------------------------
        # 波色
        # ----------------------------------------------------

        "wave": {

            "main":
                hit_rate(
                    count(
                        "wave_main"
                    ),
                    total,
                ),

            "secondary":
                hit_rate(
                    count(
                        "wave_secondary"
                    ),
                    total,
                ),

            "double":
                hit_rate(
                    count(
                        "wave_double"
                    ),
                    total,
                ),
        },

        "status":
            "正常",
    }
