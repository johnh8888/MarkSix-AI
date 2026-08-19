# -*- coding: utf-8 -*-

"""
六合彩统计分析模块

注意：

本模块是统计分析，不代表真实中奖概率。
"""

from __future__ import annotations

from collections import Counter

from typing import Any


# ============================================================
# 波色
# ============================================================

RED = {

    1, 2, 7, 8,
    12, 13, 18, 19,
    23, 24, 29, 30,
    34, 35, 40,
    45, 46,

}


BLUE = {

    3, 4, 9, 10,
    14, 15, 20,
    25, 26, 31,
    36, 37, 41,
    42, 47, 48,

}


GREEN = {

    5, 6, 11,
    16, 17, 21,
    22, 27, 28,
    32, 33, 38,
    39, 43, 44,
    49,

}


# ============================================================
# 属性
# ============================================================

def get_color(
    number: int,
) -> str:

    if number in RED:

        return "红"

    if number in BLUE:

        return "蓝"

    return "绿"


def get_size(
    number: int,
) -> str:

    if number >= 25:

        return "大"

    return "小"


def get_odd_even(
    number: int,
) -> str:

    if number % 2:

        return "单"

    return "双"


def get_tail(
    number: int,
) -> int:

    return number % 10


def get_zone(
    number: int,
) -> int:

    if number <= 10:

        return 1

    if number <= 20:

        return 2

    if number <= 30:

        return 3

    if number <= 40:

        return 4

    return 5


# ============================================================
# 属性统计
# ============================================================

def attribute_counter(
    history: list[dict],
    function,
) -> Counter:

    counter = Counter()

    for row in history:

        for number in row[
            "numbers"
        ]:

            counter[
                function(number)
            ] += 1

    return counter


# ============================================================
# 数字格式
# ============================================================

def format_numbers(
    numbers: list[int],
) -> str:

    return " ".join(

        f"{number:02d}"

        for number in numbers

    )


# ============================================================
# Walk Forward
# ============================================================

def walk_forward(
    history: list[dict],
) -> dict[str, Any]:

    size = len(history)

    # 至少 11 期
    if size < 11:

        return {

            "method":
                "Walk-Forward",

            "history_size":
                size,

            "samples":
                0,

            "hits":
                0,

            "hit_rate":
                0.0,

            "status":
                "历史数据不足",

        }

    samples = 0

    hits = 0

    for index in range(
        10,
        size,
    ):

        training = (
            history[:index]
        )

        actual = set(

            history[index][
                "numbers"
            ]

        )

        counter = Counter()

        for row in training:

            counter.update(
                row["numbers"]
            )

        prediction = sorted(

            range(1, 50),

            key=lambda n: (
                -counter[n],
                n,
            ),

        )[:12]

        hits += len(

            set(prediction)
            & actual

        )

        samples += 1

    denominator = (
        samples * 7
    )

    hit_rate = (

        hits / denominator

        if denominator

        else 0.0

    )

    return {

        "method":
            "Walk-Forward",

        "history_size":
            size,

        "samples":
            samples,

        "hits":
            hits,

        "hit_rate":
            round(
                hit_rate,
                6,
            ),

        "status":
            "有效",

    }


# ============================================================
# 主分析
# ============================================================

def analyze(
    history: list[dict],
    candidate_count: int = 12,
) -> dict[str, Any]:

    # ========================================================
    # 无数据
    # ========================================================

    if not history:

        return {

            "lottery":
                "",

            "latest_issue":
                "",

            "latest_draw_issue":
                "",

            "prediction_issue":
                "",

            "next_prediction_issue":
                "",

            "latest_numbers":
                [],

            "history_size":
                0,

            "candidates":
                [],

            "hot_numbers":
                [],

            "cold_numbers":
                [],

            "attributes": {

                "sample_size":
                    0,

                "colors":
                    {},

                "sizes":
                    {},

                "odd_even":
                    {},

                "tails":
                    {},

                "zones":
                    {},

            },

            "backtest": {

                "method":
                    "Walk-Forward",

                "history_size":
                    0,

                "samples":
                    0,

                "hits":
                    0,

                "hit_rate":
                    0.0,

                "status":
                    "历史数据不足",

            },

            "module_performance": {

                "history_size":
                    0,

                "modules": {

                    "frequency": {

                        "score":
                            0.0,

                        "status":
                            "数据不足",

                    },

                    "recent_frequency": {

                        "score":
                            0.0,

                        "status":
                            "数据不足",

                    },

                    "overdue": {

                        "score":
                            0.0,

                        "status":
                            "数据不足",

                    },

                },

            },

            "success":
                False,

        }


    # ========================================================
    # 最新开奖
    # ========================================================

    latest = history[-1]

    latest_issue = str(
        latest["issue"]
    )

    latest_numbers = [

        int(x)

        for x in latest[
            "numbers"
        ]

    ]


    # ========================================================
    # 下一期
    # ========================================================

    try:

        prediction_issue = str(

            int(
                latest_issue
            ) + 1

        )

    except (
        ValueError,
        TypeError,
    ):

        prediction_issue = ""


    # ========================================================
    # 全历史频率
    # ========================================================

    frequency = Counter()

    for row in history:

        frequency.update(
            row["numbers"]
        )


    # ========================================================
    # 近期频率
    # ========================================================

    recent_history = history[-20:]

    recent_frequency = Counter()

    for row in recent_history:

        recent_frequency.update(
            row["numbers"]
        )


    # ========================================================
    # 综合评分
    # ========================================================

    scores = {}

    for number in range(
        1,
        50,
    ):

        scores[number] = (

            frequency[number]
            * 1.0

            +

            recent_frequency[number]
            * 0.35

        )


    # ========================================================
    # 排序
    # ========================================================

    ranking = sorted(

        range(1, 50),

        key=lambda n: (

            -scores[n],

            -frequency[n],

            n,

        ),

    )


    # ========================================================
    # 高频
    # ========================================================

    hot_numbers = ranking[
        :10
    ]


    # ========================================================
    # 低频
    # ========================================================

    cold_numbers = sorted(

        range(1, 50),

        key=lambda n: (

            frequency[n],

            recent_frequency[n],

            n,

        ),

    )[:10]


    # ========================================================
    # 候选
    # ========================================================

    candidates = ranking[
        :candidate_count
    ]


    # ========================================================
    # 最新期开奖属性
    # ========================================================

    colors = attribute_counter(

        [latest],

        get_color,

    )

    sizes = attribute_counter(

        [latest],

        get_size,

    )

    odd_even = attribute_counter(

        [latest],

        get_odd_even,

    )

    tails = attribute_counter(

        [latest],

        get_tail,

    )

    zones = attribute_counter(

        [latest],

        get_zone,

    )


    # ========================================================
    # Walk Forward
    # ========================================================

    backtest = walk_forward(
        history
    )


    # ========================================================
    # 模块表现
    # ========================================================

    if len(history) >= 10:

        frequency_score = min(

            1.0,

            sum(
                frequency[n]
                for n in hot_numbers
            )
            /
            max(
                1,
                len(history) * 7,
            ),

        )

        recent_score = min(

            1.0,

            sum(
                recent_frequency[n]
                for n in hot_numbers
            )
            /
            max(
                1,
                len(recent_history) * 7,
            ),

        )

        module_status = "有效"

    else:

        frequency_score = 0.0

        recent_score = 0.0

        module_status = "数据不足"


    return {

        "latest_issue":
            latest_issue,

        "latest_draw_issue":
            latest_issue,

        "latest_numbers":
            latest_numbers,

        "prediction_issue":
            prediction_issue,

        "next_prediction_issue":
            prediction_issue,

        "history_size":
            len(history),

        "candidates":
            candidates,

        "hot_numbers":
            hot_numbers,

        "cold_numbers":
            cold_numbers,

        "attributes": {

            "sample_size":
                len(history),

            "colors":
                dict(colors),

            "sizes":
                dict(sizes),

            "odd_even":
                dict(odd_even),

            "tails": {

                str(k): v

                for k, v in tails.items()

            },

            "zones": {

                str(k): v

                for k, v in zones.items()

            },

        },

        "backtest":
            backtest,

        "module_performance": {

            "history_size":
                len(history),

            "modules": {

                "frequency": {

                    "score":
                        round(
                            frequency_score,
                            4,
                        ),

                    "status":
                        module_status,

                },

                "recent_frequency": {

                    "score":
                        round(
                            recent_score,
                            4,
                        ),

                    "status":
                        module_status,

                },

                "overdue": {

                    "score":
                        0.0,

                    "status":
                        module_status,

                },

            },

        },

        "success":
            True,

    }
