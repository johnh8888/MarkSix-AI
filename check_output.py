# -*- coding: utf-8 -*-

"""
CI 输出结果检查
"""

from __future__ import annotations

import json

import os

import sys


FILES = [

    "output/prediction.json",

    "output/backtest.json",

    "output/module_performance.json",

]


REQUIRED_LOTTERIES = [

    "新澳门彩",

    "老澳门彩",

    "香港彩",

]


print(
    "=============================="
)

print(
    "检查预测结果"
)

print(
    "=============================="
)


# ============================================================
# 检查文件
# ============================================================

for path in FILES:

    print(
        f"检查：{path}"
    )


    if not os.path.isfile(path):

        print(
            f"❌ 文件不存在：{path}"
        )

        sys.exit(1)


    try:

        with open(

            path,

            "r",

            encoding="utf-8",

        ) as file:

            data = json.load(file)


    except Exception as exc:

        print(
            f"❌ JSON解析失败："
            f"{exc}"
        )

        sys.exit(1)


    if not isinstance(
        data,
        dict,
    ):

        print(
            "❌ JSON顶层必须是object"
        )

        sys.exit(1)


    print(
        "✅ JSON正常"
    )


# ============================================================
# prediction
# ============================================================

with open(

    "output/prediction.json",

    "r",

    encoding="utf-8",

) as file:

    prediction = json.load(file)


lotteries = prediction.get(
    "lotteries"
)


if not isinstance(
    lotteries,
    dict,
):

    print(
        "❌ prediction.json "
        "缺少lotteries"
    )

    sys.exit(1)


# ============================================================
# 三彩种
# ============================================================

for lottery_name in (
    REQUIRED_LOTTERIES
):

    if lottery_name not in lotteries:

        print(
            f"❌ 缺少："
            f"{lottery_name}"
        )

        sys.exit(1)


    item = lotteries[
        lottery_name
    ]


    if not isinstance(
        item,
        dict,
    ):

        print(
            f"❌ {lottery_name}"
            f"数据结构错误"
        )

        sys.exit(1)


    required_keys = [

        "candidates",

        "latest_draw_issue",

        "next_prediction_issue",

        "latest_numbers",

        "history_size",

    ]


    for key in required_keys:

        if key not in item:

            print(

                f"❌ {lottery_name}"
                f"缺少：{key}"

            )

            sys.exit(1)


    if not isinstance(
        item["candidates"],
        list,
    ):

        print(

            f"❌ {lottery_name}"
            ".candidates必须是数组"

        )

        sys.exit(1)


    print(
        f"✅ {lottery_name}"
    )


    print(

        f"   最新期："
        f"{item['latest_draw_issue']}"

    )


    print(

        f"   预测期："
        f"{item['next_prediction_issue']}"

    )


print(
    "=============================="
)

print(
    "预测结果检查通过"
)

print(
    "=============================="
)
