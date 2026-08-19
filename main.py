# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V7.2

真实数据
SQLite
历史数据
Walk-Forward
特别号码预测
生肖5推
单双单推
大小单推
波色主推/次推/双色
命中率

重要规则：

号码：
    只针对第7个特别号码

生肖：
    只针对第7个特别号码
    推荐5个生肖

单双：
    只推荐1个

大小：
    只推荐1个

波色：
    主推1个
    次推1个
    双色2个
"""

from __future__ import annotations

import json
import os

from datetime import datetime
from typing import Any

from .api_sync import fetch_lottery

from .database import (
    init_db,
    save_records,
    load_records,
)

from .metrics import (
    get_special_number,
    predict_attributes,
    calculate_performance,
    evaluate_prediction,
)


# ============================================================
# 彩种
# ============================================================

LOTTERIES = [
    "新澳门彩",
    "老澳门彩",
    "香港彩",
]


# ============================================================
# 数据库
#
# 注意：
# 这里必须使用你现在 database.py 的 lottery_name 接口。
# 不再把数据库路径传给 save_records/load_records。
# ============================================================

OUTPUT_DIR = "output"


# ============================================================
# 创建目录
# ============================================================

def ensure_dirs() -> None:

    os.makedirs(
        "data",
        exist_ok=True,
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )


# ============================================================
# 下一期
# ============================================================

def next_issue(
    issue: str,
) -> str:

    try:

        return str(
            int(issue) + 1
        )

    except Exception:

        return ""


# ============================================================
# 特别号码频率
#
# 只统计第7个号码
# ============================================================

def count_special_numbers(
    history: list[dict[str, Any]],
    window: int = 100,
) -> dict[int, int]:

    counter: dict[int, int] = {}

    for row in history[-window:]:

        special = get_special_number(
            row
        )

        if special is None:
            continue

        counter[special] = (
            counter.get(
                special,
                0,
            )
            + 1
        )

    return counter


# ============================================================
# 特别号码预测
#
# 只针对第7个特别号码
# ============================================================

def predict_numbers(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = count_special_numbers(
        history,
        100,
    )

    scores = {}

    for number in range(
        1,
        50,
    ):

        scores[number] = counter.get(
            number,
            0,
        )

    ranking = sorted(

        range(1, 50),

        key=lambda number: (
            -scores[number],
            number,
        ),

    )

    return {

        "top5":
            ranking[:5],

        "top10":
            ranking[:10],

        "top12":
            ranking[:12],

        "candidates":
            ranking[:12],

        "scores":
            scores,

    }


# ============================================================
# 单期预测
# ============================================================

def build_prediction(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    number_prediction = (
        predict_numbers(
            history
        )
    )

    attributes = (
        predict_attributes(
            history
        )
    )

    return {

        "top5":
            number_prediction["top5"],

        "top10":
            number_prediction["top10"],

        "top12":
            number_prediction["top12"],

        "candidates":
            number_prediction["candidates"],

        "attributes":
            attributes,

    }


# ============================================================
# Walk-Forward
#
# 核心：
#
# index之前 = 训练数据
# index      = 真实开奖
#
# 绝不使用未来数据
# ============================================================

def walk_forward(
    history: list[dict[str, Any]],
    minimum_train: int = 30,
) -> dict[str, Any]:

    evaluations = []

    if len(history) <= minimum_train:

        return {

            "method":
                "Walk-Forward",

            "samples":
                0,

            "status":
                "历史数据不足",

            "performance":
                {},

        }

    for index in range(
        minimum_train,
        len(history),
    ):

        train = history[
            :index
        ]

        actual = history[
            index
        ]

        prediction = build_prediction(
            train
        )

        evaluation = (
            evaluate_prediction(
                prediction,
                actual,
            )
        )

        if evaluation:

            evaluations.append(
                evaluation
            )

    performance = (
        calculate_performance(
            evaluations
        )
    )

    return {

        "method":
            "Walk-Forward",

        "samples":
            len(evaluations),

        "performance":
            performance,

        "status":
            "正常",

    }


# ============================================================
# 分析一个彩种
# ============================================================

def analyze(
    lottery_name: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    history = sorted(

        history,

        key=lambda row: int(
            row.get(
                "issue",
                0,
            )
        ),

    )

    latest = (
        history[-1]
        if history
        else {}
    )

    latest_issue = str(
        latest.get(
            "issue",
            "",
        )
    )

    prediction_issue = (
        next_issue(
            latest_issue
        )
        if latest_issue
        else ""
    )

    # ========================================================
    # 下一期预测
    # ========================================================

    prediction = build_prediction(
        history
    )

    # ========================================================
    # Walk-Forward
    # ========================================================

    walk = walk_forward(
        history
    )

    # ========================================================
    # 特别号码历史命中说明
    # ========================================================

    latest_special = (
        get_special_number(
            latest
        )
    )

    return {

        "lottery":
            lottery_name,

        "success":
            bool(history),

        "latest_issue":
            latest_issue,

        "latest_draw_issue":
            latest_issue,

        "latest_numbers":
            latest.get(
                "numbers",
                [],
            ),

        "latest_special":
            latest_special,

        "prediction_issue":
            prediction_issue,

        "next_prediction_issue":
            prediction_issue,

        "history_size":
            len(history),

        # ====================================================
        # 非常重要：
        # candidates 必须存在
        # ====================================================

        "candidates":
            prediction["candidates"],

        "top5":
            prediction["top5"],

        "top10":
            prediction["top10"],

        "top12":
            prediction["top12"],

        "attributes":
            prediction["attributes"],

        "performance":
            walk.get(
                "performance",
                {},
            ),

        "backtest":
            walk,

    }


# ============================================================
# 打印结果
# ============================================================

def print_result(
    result: dict[str, Any],
) -> None:

    print(
        "=" * 70
    )

    print(
        f"【{result['lottery']}】"
    )

    print(
        "=" * 70
    )

    print(
        f"历史期数："
        f"{result['history_size']}"
    )

    print(
        f"最新开奖期数："
        f"{result['latest_issue']}"
    )

    print(
        f"预测下一期期数："
        f"{result['prediction_issue']}"
    )

    latest_numbers = result.get(
        "latest_numbers",
        [],
    )

    print(
        "最新号码："
        + " ".join(
            f"{int(x):02d}"
            for x in latest_numbers
        )
    )

    latest_special = result.get(
        "latest_special"
    )

    if latest_special is not None:

        print(
            f"特别号码："
            f"{latest_special:02d}"
        )

    print()

    # ========================================================
    # 特别号码
    # ========================================================

    print(
        "【下一期特别号码预测】"
    )

    print(
        "Top5："
        + " ".join(
            f"{x:02d}"
            for x in result["top5"]
        )
    )

    print(
        "Top10："
        + " ".join(
            f"{x:02d}"
            for x in result["top10"]
        )
    )

    print(
        "Top12："
        + " ".join(
            f"{x:02d}"
            for x in result["top12"]
        )
    )

    print()

    # ========================================================
    # 属性
    # ========================================================

    attrs = result[
        "attributes"
    ]

    print(
        "【下一期特别号属性预测】"
    )

    # 生肖
    zodiac = attrs[
        "zodiac"
    ]

    print(
        "生肖5推："
        + " ".join(
            zodiac.get(
                "top5",
                [],
            )
        )
    )

    print(
        "生肖主推："
        + zodiac.get(
            "main",
            "",
        )
    )

    # 单双
    odd_even = attrs[
        "odd_even"
    ]

    print(
        "单双："
        + odd_even.get(
            "main",
            "",
        )
    )

    # 大小
    size = attrs[
        "size"
    ]

    print(
        "大小："
        + size.get(
            "main",
            "",
        )
    )

    # 波色
    wave = attrs[
        "wave"
    ]

    print(
        "波色主推："
        + wave.get(
            "main",
            "",
        )
    )

    print(
        "波色次推："
        + wave.get(
            "secondary",
            "",
        )
    )

    print(
        "波色双色："
        + " + ".join(
            wave.get(
                "double",
                [],
            )
        )
    )

    print()

    # ========================================================
    # Walk-Forward
    # ========================================================

    performance = result.get(
        "performance",
        {},
    )

    if performance:

        print(
            "【Walk-Forward 历史命中率】"
        )

        print(
            f"验证期数："
            f"{performance.get('samples', 0)}"
        )

        # ----------------------------------------------------
        # 号码
        # ----------------------------------------------------

        numbers = performance.get(
            "numbers",
            {},
        )

        print(
            "【特别号码命中】"
        )

        print(
            f"Top5："
            f"{numbers.get('top5', 0)}%"
        )

        print(
            f"Top10："
            f"{numbers.get('top10', 0)}%"
        )

        print(
            f"Top12："
            f"{numbers.get('top12', 0)}%"
        )

        # ----------------------------------------------------
        # 生肖
        # ----------------------------------------------------

        zodiac_perf = performance.get(
            "zodiac",
            {},
        )

        print(
            "【生肖命中】"
        )

        print(
            f"主推："
            f"{zodiac_perf.get('main', 0)}%"
        )

        print(
            f"5推："
            f"{zodiac_perf.get('top5', 0)}%"
        )

        # ----------------------------------------------------
        # 单双
        # ----------------------------------------------------

        odd_perf = performance.get(
            "odd_even",
            {},
        )

        print(
            "【单双命中】"
        )

        print(
            f"单推："
            f"{odd_perf.get('main', 0)}%"
        )

        # ----------------------------------------------------
        # 大小
        # ----------------------------------------------------

        size_perf = performance.get(
            "size",
            {},
        )

        print(
            "【大小命中】"
        )

        print(
            f"单推："
            f"{size_perf.get('main', 0)}%"
        )

        # ----------------------------------------------------
        # 波色
        # ----------------------------------------------------

        wave_perf = performance.get(
            "wave",
            {},
        )

        print(
            "【波色命中】"
        )

        print(
            f"主推："
            f"{wave_perf.get('main', 0)}%"
        )

        print(
            f"次推："
            f"{wave_perf.get('secondary', 0)}%"
        )

        print(
            f"双色："
            f"{wave_perf.get('double', 0)}%"
        )

    print()


# ============================================================
# 保存 JSON
# ============================================================

def save_json(
    path: str,
    data: dict[str, Any],
) -> None:

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# 生成 backtest
# ============================================================

def build_backtest(
    results: dict[str, Any],
) -> dict[str, Any]:

    output = {}

    for lottery, result in results.items():

        output[lottery] = (
            result.get(
                "backtest",
                {},
            )
        )

    return {

        "version":
            "V7.2",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries":
            output,

    }


# ============================================================
# 模块表现
# ============================================================

def build_module_performance(
    results: dict[str, Any],
) -> dict[str, Any]:

    output = {}

    for lottery, result in results.items():

        output[lottery] = (
            result.get(
                "performance",
                {},
            )
        )

    return {

        "version":
            "V7.2",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries":
            output,

    }


# ============================================================
# 主程序
# ============================================================

def run_system() -> None:

    ensure_dirs()

    # --------------------------------------------------------
    # 初始化数据库
    # --------------------------------------------------------

    init_db()

    all_results = {}

    # ========================================================
    # 三彩种
    # ========================================================

    for lottery in LOTTERIES:

        print(
            "=" * 70
        )

        print(
            f"正在更新：{lottery}"
        )

        print(
            "=" * 70
        )

        try:

            # ------------------------------------------------
            # 获取历史
            # ------------------------------------------------

            records = fetch_lottery(
                lottery
            )

            # ------------------------------------------------
            # 保存数据库
            # ------------------------------------------------

            if records:

                save_records(
                    lottery,
                    records,
                )

            # ------------------------------------------------
            # 读取数据库
            # ------------------------------------------------

            history = load_records(
                lottery
            )

            print(
                f"[{lottery}] "
                f"当前数据库历史："
                f"{len(history)} 期"
            )

            # ------------------------------------------------
            # 分析
            # ------------------------------------------------

            result = analyze(
                lottery,
                history,
            )

            print_result(
                result
            )

            all_results[
                lottery
            ] = result

        except Exception as exc:

            print(
                f"[ERROR] "
                f"{lottery}: "
                f"{exc}"
            )

            all_results[
                lottery
            ] = {

                "lottery":
                    lottery,

                "success":
                    False,

                "error":
                    str(exc),

                "candidates":
                    [],

                "latest_issue":
                    "",

                "prediction_issue":
                    "",

            }

    # ========================================================
    # prediction.json
    # ========================================================

    prediction = {

        "version":
            "V7.2 SPECIAL NUMBER FINAL",

        "generated_at":
            datetime.now().isoformat(),

        "rules": {

            "number":
                "只针对第7个特别号码",

            "number_hit":
                "每期最多命中1个",

            "zodiac":
                "特别号码生肖推荐5个",

            "odd_even":
                "特别号码单双只推荐1个",

            "size":
                "特别号码大小只推荐1个",

            "wave":
                "特别号码波色主推/次推/双色",

        },

        "note":
            "历史Walk-Forward统计不代表未来真实中奖概率。",

        "lotteries":
            all_results,

    }

    prediction_path = os.path.join(
        OUTPUT_DIR,
        "prediction.json",
    )

    save_json(
        prediction_path,
        prediction,
    )

    print(
        "=" * 70
    )

    print(
        "预测结果已保存："
        f"{prediction_path}"
    )

    # ========================================================
    # backtest.json
    # ========================================================

    backtest = build_backtest(
        all_results
    )

    backtest_path = os.path.join(
        OUTPUT_DIR,
        "backtest.json",
    )

    save_json(
        backtest_path,
        backtest,
    )

    print(
        "回测结果已保存："
        f"{backtest_path}"
    )

    # ========================================================
    # module_performance.json
    # ========================================================

    module_performance = (
        build_module_performance(
            all_results
        )
    )

    module_path = os.path.join(
        OUTPUT_DIR,
        "module_performance.json",
    )

    save_json(
        module_path,
        module_performance,
    )

    print(
        "模块表现已保存："
        f"{module_path}"
    )

    # ========================================================
    # 最终摘要
    # ========================================================

    print(
        "=" * 70
    )

    print(
        "三彩种分析完成"
    )

    for lottery, result in (
        all_results.items()
    ):

        if not result.get(
            "success"
        ):

            continue

        print(
            f"{lottery}："
            f"最新第 "
            f"{result.get('latest_issue', '')} "
            f"期"
        )

        print(
            f"{lottery}："
            f"预测特别号第 "
            f"{result.get('prediction_issue', '')} "
            f"期"
        )

        candidates = result.get(
            "candidates",
            [],
        )

        print(
            f"{lottery}："
            "特别号候选 "
            + " ".join(
                f"{x:02d}"
                for x in candidates
            )
        )

        attrs = result.get(
            "attributes",
            {},
        )

        zodiac = attrs.get(
            "zodiac",
            {},
        )

        print(
            f"{lottery}："
            "生肖5推 "
            + " ".join(
                zodiac.get(
                    "top5",
                    [],
                )
            )
        )

        odd_even = attrs.get(
            "odd_even",
            {},
        )

        print(
            f"{lottery}："
            "单双 "
            + odd_even.get(
                "main",
                "",
            )
        )

        size = attrs.get(
            "size",
            {},
        )

        print(
            f"{lottery}："
            "大小 "
            + size.get(
                "main",
                "",
            )
        )

        wave = attrs.get(
            "wave",
            {},
        )

        print(
            f"{lottery}："
            "波色主推 "
            + wave.get(
                "main",
                "",
            )
            + " / 次推 "
            + wave.get(
                "secondary",
                "",
            )
            + " / 双色 "
            + " + ".join(
                wave.get(
                    "double",
                    [],
                )
            )
        )

    print(
        "=" * 70
    )

    print(
        "说明："
        "号码仅针对第7个特别号码；"
        "生肖仅针对特别号码；"
        "单双、大小仅推荐一个；"
        "波色提供主推、次推及双色。"
    )

    print(
        "以上命中率为历史Walk-Forward统计，"
        "不等于未来实际中奖概率。"
    )

    print(
        "=" * 70
    )

    print(
        "系统运行结束"
    )

    print(
        "=" * 70
    )


# ============================================================
# 程序入口
# ============================================================

if __name__ == "__main__":

    run_system()
