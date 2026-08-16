# -*- coding: utf-8 -*-

"""
六合彩 V3.0 Prediction Engine

最终负责：

香港六合彩
新澳门六合彩
老澳门六合彩

输出：

特码10码
重点Top3
特码概率
大小
单双
波色单推
波色双推
波色概率
动态权重
"""

from typing import Any, Dict, List

from .strategies import (
    build_strategy_result,
)


# =========================================================
# 状态
# =========================================================

def detect_simple_state(
    rows: List[Dict[str, Any]]
) -> Dict[str, Any]:

    """
    简化状态识别。

    如果项目已有 state_engine.py，
    后续可以再接入完整状态引擎。

    当前先保证 V3.0 主链稳定。
    """

    if len(rows) < 12:

        return {

            "state":
                "数据不足",

            "confidence":
                0.0,
        }

    # -----------------------------------------------------
    # 最近12期特码
    # -----------------------------------------------------

    numbers = []

    for row in rows[:12]:

        special = row.get(
            "special"
        )

        if special is None:

            values = row.get(
                "numbers",
                []
            )

            if isinstance(
                values,
                str
            ):

                values = (
                    values
                    .replace(
                        "，",
                        ","
                    )
                    .split(",")
                )

            try:

                values = [
                    int(x)
                    for x in values
                ]

            except Exception:

                values = []

            if len(values) >= 7:

                special = values[6]

        try:

            special = int(
                special
            )

        except Exception:

            continue

        if 1 <= special <= 49:

            numbers.append(
                special
            )

    if len(numbers) < 8:

        return {

            "state":
                "数据不足",

            "confidence":
                0.0,
        }

    # -----------------------------------------------------
    # 判断近期集中度
    # -----------------------------------------------------

    average = (
        sum(numbers)
        /
        len(numbers)
    )

    variance = (
        sum(
            (x - average) ** 2
            for x in numbers
        )
        /
        len(numbers)
    )

    # -----------------------------------------------------
    # 简单状态
    # -----------------------------------------------------

    if variance < 100:

        state = "趋势"

        confidence = 0.65

    elif variance > 250:

        state = "混沌"

        confidence = 0.65

    else:

        state = "正常"

        confidence = 0.60

    return {

        "state":
            state,

        "confidence":
            confidence,

        "average":
            round(
                average,
                3
            ),

        "variance":
            round(
                variance,
                3
            ),
    }


# =========================================================
# 生成预测
# =========================================================

def predict_lottery(
    rows: List[Dict[str, Any]],
    lottery: str = "hk",
    performance: Dict[str, float] = None
) -> Dict[str, Any]:

    if not rows:

        raise ValueError(
            f"{lottery} 没有历史数据"
        )

    # -----------------------------------------------------
    # 策略模型
    # -----------------------------------------------------

    result = build_strategy_result(
        rows,
        performance
    )

    # -----------------------------------------------------
    # 状态
    # -----------------------------------------------------

    state = detect_simple_state(
        rows
    )

    # -----------------------------------------------------
    # Top10
    # -----------------------------------------------------

    top10 = result[
        "top10"
    ]

    top3 = result[
        "top3"
    ]

    probabilities = result[
        "probabilities"
    ]

    # -----------------------------------------------------
    # Top10概率
    # -----------------------------------------------------

    top10_detail = []

    for number in top10:

        top10_detail.append({

            "number":
                number,

            "probability":
                round(
                    probabilities.get(
                        number,
                        0.0
                    ),
                    6
                ),
        })

    # -----------------------------------------------------
    # 大小
    # -----------------------------------------------------

    size_p = result[
        "size_probabilities"
    ]

    size_pick = max(
        size_p,
        key=size_p.get
    )

    # -----------------------------------------------------
    # 单双
    # -----------------------------------------------------

    parity_p = result[
        "parity_probabilities"
    ]

    parity_pick = max(
        parity_p,
        key=parity_p.get
    )

    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    wave_p = result[
        "wave_probabilities"
    ]

    wave_single = result[
        "wave_single"
    ]

    wave_double = result[
        "wave_double"
    ]

    # -----------------------------------------------------
    # 最终结果
    # -----------------------------------------------------

    return {

        "version":
            "V3.0",

        "lottery":
            lottery,

        "data_count":
            len(rows),

        "state":
            state,

        "top10":
            top10,

        "top3":
            top3,

        "top10_detail":
            top10_detail,

        "size": {

            "pick":
                size_pick,

            "probabilities":
                {
                    k:
                        round(
                            v,
                            6
                        )

                    for k, v
                    in size_p.items()
                },
        },

        "parity": {

            "pick":
                parity_pick,

            "probabilities":
                {
                    k:
                        round(
                            v,
                            6
                        )

                    for k, v
                    in parity_p.items()
                },
        },

        "wave": {

            "single":
                wave_single,

            "double":
                wave_double,

            "probabilities":
                {
                    k:
                        round(
                            v,
                            6
                        )

                    for k, v
                    in wave_p.items()
                },
        },

        "weights":
            {
                k:
                    round(
                        v,
                        6
                    )

                for k, v
                in result[
                    "weights"
                ].items()
            },
    }


# =========================================================
# 多彩种预测
# =========================================================

def predict_all(
    datasets: Dict[str, List[Dict[str, Any]]],
    performances: Dict[str, Dict[str, float]] = None
) -> Dict[str, Any]:

    output = {}

    performances = (
        performances
        or {}
    )

    for lottery, rows in datasets.items():

        try:

            output[lottery] = predict_lottery(

                rows,

                lottery,

                performances.get(
                    lottery
                ),
            )

        except Exception as e:

            output[lottery] = {

                "version":
                    "V3.0",

                "lottery":
                    lottery,

                "error":
                    str(e),
            }

    return output


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    rows = []

    for i in range(150):

        rows.append({

            "issue":
                str(2026000 + i),

            "numbers":
                [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    (i % 49) + 1
                ],
        })

    result = predict_lottery(
        rows,
        "hk"
    )

    print(
        result
    )