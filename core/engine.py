# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V7.1

真实数据
SQLite
历史统计
Walk-Forward
号码预测
生肖
单双
大小
波色主推 / 次推 / 双色
命中率
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from collections import Counter
from typing import Any

from .api_sync import fetch_lottery

from .database import (
    save_records,
    load_records,
)

from .metrics import (
    get_wave,
    get_size,
    get_odd_even,
    get_zodiac,
    predict_attribute,
    calculate_performance,
)


# ============================================================
# 三彩种
# ============================================================

LOTTERIES = [
    "新澳门彩",
    "老澳门彩",
    "香港彩",
]


# ============================================================
# 输出目录
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
# 号码频率
# ============================================================

def count_numbers(
    history: list[dict[str, Any]],
    window: int = 100,
) -> Counter:

    counter = Counter()

    if window <= 0:

        window = len(history)

    for row in history[-window:]:

        numbers = row.get(
            "numbers",
            [],
        )

        if not isinstance(
            numbers,
            list,
        ):

            continue

        for number in numbers:

            try:

                number = int(number)

            except Exception:

                continue

            if 1 <= number <= 49:

                counter[number] += 1

    return counter


# ============================================================
# 号码遗漏
# ============================================================

def calculate_overdue(
    history: list[dict[str, Any]],
) -> dict[int, int]:

    overdue = {}

    for number in range(
        1,
        50,
    ):

        gap = 0

        for row in reversed(history):

            numbers = set(
                row.get(
                    "numbers",
                    [],
                )
            )

            if number in numbers:

                break

            gap += 1

        overdue[number] = gap

    return overdue


# ============================================================
# 号码预测
#
# 注意：
# 不再单纯按照出现次数排序。
#
# 综合：
# 近期频率
# 总频率
# 遗漏
# ============================================================

def predict_numbers(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    if not history:

        return {
            "top5": [],
            "top10": [],
            "top12": [],
            "scores": {},
        }

    # ----------------------------------------
    # 最近100期
    # ----------------------------------------

    recent = history[-100:]

    counter = count_numbers(
        recent,
        100,
    )

    # ----------------------------------------
    # 最近30期
    # ----------------------------------------

    recent30 = history[-30:]

    counter30 = count_numbers(
        recent30,
        30,
    )

    # ----------------------------------------
    # 最近10期
    # ----------------------------------------

    recent10 = history[-10:]

    counter10 = count_numbers(
        recent10,
        10,
    )

    # ----------------------------------------
    # 遗漏
    # ----------------------------------------

    overdue = calculate_overdue(
        history
    )

    scores = {}

    for number in range(
        1,
        50,
    ):

        frequency = counter.get(
            number,
            0,
        )

        recent_frequency = counter30.get(
            number,
            0,
        )

        very_recent = counter10.get(
            number,
            0,
        )

        gap = overdue.get(
            number,
            0,
        )

        # ------------------------------------
        # 综合评分
        # ------------------------------------
        #
        # 总频率：35%
        # 30期：30%
        # 10期：20%
        # 遗漏：15%
        #
        # 遗漏不是越大越好，而是适度加分。
        # ------------------------------------

        overdue_score = min(
            gap,
            20,
        ) / 20.0

        score = (

            frequency * 0.35

            + recent_frequency * 0.30

            + very_recent * 0.20

            + overdue_score * 2.0

        )

        scores[number] = score

    ranking = sorted(
        range(1, 50),
        key=lambda number: (
            -scores[number],
            number,
        ),
    )

    return {
        "top5": ranking[:5],
        "top10": ranking[:10],
        "top12": ranking[:12],
        "scores": {
            str(k): round(
                v,
                6,
            )
            for k, v in scores.items()
        },
    }


# ============================================================
# 单次预测评价
# ============================================================

def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:

    actual_numbers = actual.get(
        "numbers",
        [],
    )

    if not actual_numbers:

        return {}

    actual_numbers = [
        int(x)
        for x in actual_numbers
    ]

    actual_set = set(
        actual_numbers
    )

    # ========================================================
    # 特别号码
    #
    # API数据的第7个号码作为特码
    # ========================================================

    actual_special = actual_numbers[-1]

    issue = str(
        actual.get(
            "issue",
            "",
        )
    )

    attrs = prediction.get(
        "attributes",
        {},
    )

    result = {}

    # ========================================================
    # 号码
    # ========================================================

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

    result[
        "number_top5"
    ] = bool(
        actual_set & top5
    )

    result[
        "number_top10"
    ] = bool(
        actual_set & top10
    )

    result[
        "number_top12"
    ] = bool(
        actual_set & top12
    )

    # ========================================================
    # 生肖
    # ========================================================

    zodiac = get_zodiac(
        actual_special,
        issue,
    )

    zodiac_attr = attrs.get(
        "zodiac",
        {},
    )

    zodiac_main = zodiac_attr.get(
        "main",
        "",
    )

    zodiac_secondary = zodiac_attr.get(
        "secondary",
        "",
    )

    zodiac_double = zodiac_attr.get(
        "double",
        [],
    )

    result[
        "zodiac_main"
    ] = (
        zodiac == zodiac_main
    )

    result[
        "zodiac_secondary"
    ] = (
        zodiac == zodiac_secondary
    )

    result[
        "zodiac_double"
    ] = (
        zodiac in zodiac_double
    )

    # ========================================================
    # 单双
    # ========================================================

    odd_even = get_odd_even(
        actual_special
    )

    odd_attr = attrs.get(
        "odd_even",
        {},
    )

    result[
        "odd_even_main"
    ] = (
        odd_even
        == odd_attr.get(
            "main",
            "",
        )
    )

    result[
        "odd_even_secondary"
    ] = (
        odd_even
        == odd_attr.get(
            "secondary",
            "",
        )
    )

    result[
        "odd_even_double"
    ] = (
        odd_even
        in odd_attr.get(
            "double",
            [],
        )
    )

    # ========================================================
    # 大小
    # ========================================================

    size = get_size(
        actual_special
    )

    size_attr = attrs.get(
        "size",
        {},
    )

    result[
        "size_main"
    ] = (
        size
        == size_attr.get(
            "main",
            "",
        )
    )

    result[
        "size_secondary"
    ] = (
        size
        == size_attr.get(
            "secondary",
            "",
        )
    )

    result[
        "size_double"
    ] = (
        size
        in size_attr.get(
            "double",
            [],
        )
    )

    # ========================================================
    # 波色
    # ========================================================

    wave = get_wave(
        actual_special
    )

    wave_attr = attrs.get(
        "wave",
        {},
    )

    result[
        "wave_main"
    ] = (
        wave
        == wave_attr.get(
            "main",
            "",
        )
    )

    result[
        "wave_secondary"
    ] = (
        wave
        == wave_attr.get(
            "secondary",
            "",
        )
    )

    result[
        "wave_double"
    ] = (
        wave
        in wave_attr.get(
            "double",
            [],
        )
    )

    return result


# ============================================================
# Walk-Forward
# ============================================================

def walk_forward(
    history: list[dict[str, Any]],
    minimum_train: int = 30,
) -> dict[str, Any]:

    evaluations = []

    if len(history) <= minimum_train:

        return {
            "method": "Walk-Forward",
            "minimum_train": minimum_train,
            "samples": 0,
            "status": "历史数据不足",
            "performance": {},
        }

    # ========================================================
    # 严格 Walk-Forward
    #
    # index之前的数据才允许参与预测
    # ========================================================

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

        number_prediction = predict_numbers(
            train
        )

        attributes = {

            "zodiac":
                predict_attribute(
                    train,
                    "zodiac",
                ),

            "odd_even":
                predict_attribute(
                    train,
                    "odd_even",
                ),

            "size":
                predict_attribute(
                    train,
                    "size",
                ),

            "wave":
                predict_attribute(
                    train,
                    "wave",
                ),
        }

        prediction = {

            "top5":
                number_prediction[
                    "top5"
                ],

            "top10":
                number_prediction[
                    "top10"
                ],

            "top12":
                number_prediction[
                    "top12"
                ],

            "attributes":
                attributes,
        }

        evaluation = evaluate_prediction(
            prediction,
            actual,
        )

        if evaluation:

            evaluation[
                "issue"
            ] = actual.get(
                "issue",
                "",
            )

            evaluations.append(
                evaluation
            )

    performance = calculate_performance(
        evaluations
    )

    # ========================================================
    # 最近20期
    # ========================================================

    recent20 = evaluations[-20:]

    recent20_performance = (
        calculate_performance(
            recent20
        )
        if recent20
        else {}
    )

    # ========================================================
    # 最近50期
    # ========================================================

    recent50 = evaluations[-50:]

    recent50_performance = (
        calculate_performance(
            recent50
        )
        if recent50
        else {}
    )

    # ========================================================
    # 最近100期
    # ========================================================

    recent100 = evaluations[-100:]

    recent100_performance = (
        calculate_performance(
            recent100
        )
        if recent100
        else {}
    )

    return {

        "method":
            "Walk-Forward",

        "minimum_train":
            minimum_train,

        "samples":
            len(evaluations),

        "status":
            "正常",

        "performance":
            performance,

        "recent20":
            recent20_performance,

        "recent50":
            recent50_performance,

        "recent100":
            recent100_performance,

    }


# ============================================================
# 分析
# ============================================================

def analyze(
    lottery_name: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    # --------------------------------------------------------
    # 排序
    # --------------------------------------------------------

    history = sorted(
        history,
        key=lambda x: int(
            x.get(
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

    # --------------------------------------------------------
    # 号码
    # --------------------------------------------------------

    number_prediction = predict_numbers(
        history
    )

    # --------------------------------------------------------
    # 属性
    # --------------------------------------------------------

    attributes = {

        "zodiac":
            predict_attribute(
                history,
                "zodiac",
            ),

        "odd_even":
            predict_attribute(
                history,
                "odd_even",
            ),

        "size":
            predict_attribute(
                history,
                "size",
            ),

        "wave":
            predict_attribute(
                history,
                "wave",
            ),
    }

    # --------------------------------------------------------
    # Walk Forward
    # --------------------------------------------------------

    walk = walk_forward(
        history
    )

    return {

        "lottery":
            lottery_name,

        "latest_issue":
            latest_issue,

        "latest_draw_issue":
            latest_issue,

        "latest_numbers":
            latest.get(
                "numbers",
                [],
            ),

        "prediction_issue":
            prediction_issue,

        "next_prediction_issue":
            prediction_issue,

        "history_size":
            len(history),

        "candidates":
            number_prediction[
                "top12"
            ],

        "top5":
            number_prediction[
                "top5"
            ],

        "top10":
            number_prediction[
                "top10"
            ],

        "top12":
            number_prediction[
                "top12"
            ],

        "scores":
            number_prediction[
                "scores"
            ],

        "attributes":
            attributes,

        "performance":
            walk.get(
                "performance",
                {},
            ),

        "backtest":
            walk,

        "success":
            bool(history),
    }


# ============================================================
# 打印属性
# ============================================================

def safe_join(
    values: Any,
) -> str:

    if not isinstance(
        values,
        list,
    ):

        return ""

    return " + ".join(
        str(x)
        for x in values
    )


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

    print(
        "最新号码："
        + " ".join(
            f"{x:02d}"
            for x in result[
                "latest_numbers"
            ]
        )
    )

    print()

    # ========================================================
    # 号码
    # ========================================================

    print(
        "【号码预测】"
    )

    print(
        "Top5："
        + " ".join(
            f"{x:02d}"
            for x in result[
                "top5"
            ]
        )
    )

    print(
        "Top10："
        + " ".join(
            f"{x:02d}"
            for x in result[
                "top10"
            ]
        )
    )

    print(
        "Top12："
        + " ".join(
            f"{x:02d}"
            for x in result[
                "top12"
            ]
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
        "【属性预测】"
    )

    zodiac = attrs.get(
        "zodiac",
        {},
    )

    print(
        "生肖："
        f"主推 {zodiac.get('main', '')} "
        f"次推 {zodiac.get('secondary', '')} "
        f"双推 {safe_join(zodiac.get('double', []))}"
    )

    odd_even = attrs.get(
        "odd_even",
        {},
    )

    print(
        "单双："
        f"主推 {odd_even.get('main', '')} "
        f"次推 {odd_even.get('secondary', '')} "
        f"双推 {safe_join(odd_even.get('double', []))}"
    )

    size = attrs.get(
        "size",
        {},
    )

    print(
        "大小："
        f"主推 {size.get('main', '')} "
        f"次推 {size.get('secondary', '')} "
        f"双推 {safe_join(size.get('double', []))}"
    )

    wave = attrs.get(
        "wave",
        {},
    )

    print(
        "波色："
        f"主推 {wave.get('main', '')} "
        f"次推 {wave.get('secondary', '')} "
        f"双色 {safe_join(wave.get('double', []))}"
    )

    print()

    # ========================================================
    # Walk Forward
    # ========================================================

    performance = result.get(
        "performance",
        {},
    )

    if performance:

        print(
            "【历史 Walk-Forward 命中率】"
        )

        numbers = performance.get(
            "numbers",
            {},
        )

        print(
            f"号码 Top5："
            f"{numbers.get('top5', 0)}%"
        )

        print(
            f"号码 Top10："
            f"{numbers.get('top10', 0)}%"
        )

        print(
            f"号码 Top12："
            f"{numbers.get('top12', 0)}%"
        )

        zodiac = performance.get(
            "zodiac",
            {},
        )

        print(
            f"生肖主推："
            f"{zodiac.get('main', 0)}%"
        )

        print(
            f"生肖次推："
            f"{zodiac.get('secondary', 0)}%"
        )

        print(
            f"生肖双推："
            f"{zodiac.get('double', 0)}%"
        )

        odd_even = performance.get(
            "odd_even",
            {},
        )

        print(
            f"单双主推："
            f"{odd_even.get('main', 0)}%"
        )

        print(
            f"单双次推："
            f"{odd_even.get('secondary', 0)}%"
        )

        print(
            f"单双双推："
            f"{odd_even.get('double', 0)}%"
        )

        size = performance.get(
            "size",
            {},
        )

        print(
            f"大小主推："
            f"{size.get('main', 0)}%"
        )

        print(
            f"大小次推："
            f"{size.get('secondary', 0)}%"
        )

        print(
            f"大小双推："
            f"{size.get('double', 0)}%"
        )

        wave = performance.get(
            "wave",
            {},
        )

        print(
            f"波色主推："
            f"{wave.get('main', 0)}%"
        )

        print(
            f"波色次推："
            f"{wave.get('secondary', 0)}%"
        )

        print(
            f"波色双色："
            f"{wave.get('double', 0)}%"
        )

    # ========================================================
    # 最近表现
    # ========================================================

    backtest = result.get(
        "backtest",
        {},
    )

    if backtest.get(
        "status"
    ) == "正常":

        print()

        print(
            "【最近历史表现】"
        )

        recent20 = backtest.get(
            "recent20",
            {},
        )

        recent50 = backtest.get(
            "recent50",
            {},
        )

        recent100 = backtest.get(
            "recent100",
            {},
        )

        print(
            "最近20期："
            f"{recent20.get('numbers', {}).get('top12', 0)}%"
        )

        print(
            "最近50期："
            f"{recent50.get('numbers', {}).get('top12', 0)}%"
        )

        print(
            "最近100期："
            f"{recent100.get('numbers', {}).get('top12', 0)}%"
        )

    print()


# ============================================================
# 主系统
# ============================================================

def run_system() -> None:

    ensure_dirs()

    all_results = {}

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
            # API同步
            # ------------------------------------------------

            records = fetch_lottery(
                lottery
            )

            if records:

                added = save_records(
                    lottery,
                    records,
                )

                print(
                    f"[{lottery}] "
                    f"本次新增：{added} 期"
                )

            # ------------------------------------------------
            # 从SQLite重新读取
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
            }

    # ========================================================
    # prediction.json
    # ========================================================

    prediction = {

        "version":
            "V7.1 REAL DATA HIT RATE",

        "generated_at":
            datetime.now().isoformat(),

        "note":
            "历史统计及严格Walk-Forward分析结果，不代表真实中奖概率。",

        "lotteries":
            all_results,
    }

    prediction_path = os.path.join(
        OUTPUT_DIR,
        "prediction.json",
    )

    with open(
        prediction_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            prediction,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        "=" * 70
    )

    print(
        f"预测结果已保存："
        f"{prediction_path}"
    )

    print(
        "=" * 70
    )

    # ========================================================
    # backtest.json
    # ========================================================

    backtest_data = {

        "version":
            "V7.1",

        "generated_at":
            datetime.now().isoformat(),

        "method":
            "Strict Walk-Forward",

        "lotteries": {

            name:
                result.get(
                    "backtest",
                    {},
                )

            for name, result
            in all_results.items()

            if result.get(
                "success",
                False,
            )
        },
    }

    backtest_path = os.path.join(
        OUTPUT_DIR,
        "backtest.json",
    )

    with open(
        backtest_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            backtest_data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"回测结果已保存："
        f"{backtest_path}"
    )

    # ========================================================
    # module_performance.json
    # ========================================================

    module_data = {

        "version":
            "V7.1",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries": {

            name:
                result.get(
                    "performance",
                    {},
                )

            for name, result
            in all_results.items()

            if result.get(
                "success",
                False,
            )
        },
    }

    module_path = os.path.join(
        OUTPUT_DIR,
        "module_performance.json",
    )

    with open(
        module_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            module_data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"模块表现已保存："
        f"{module_path}"
    )

    # ========================================================
    # 最终汇总
    # ========================================================

    print(
        "=" * 70
    )

    print(
        "三彩种分析完成"
    )

    print(
        "=" * 70
    )

    for name, result in (
        all_results.items()
    ):

        if not result.get(
            "success",
            False,
        ):

            continue

        print(
            f"{name}："
            f"最新开奖第 "
            f"{result.get('latest_issue', '')} "
            f"期"
        )

        print(
            f"{name}："
            f"预测下一期第 "
            f"{result.get('prediction_issue', '')} "
            f"期"
        )

        print(
            f"{name}："
            "候选 "
            + " ".join(
                f"{x:02d}"
                for x in result.get(
                    "top12",
                    [],
                )
            )
        )

        performance = result.get(
            "performance",
            {},
        )

        wave = performance.get(
            "wave",
            {},
        )

        print(
            f"{name}："
            f"波色主推命中率 "
            f"{wave.get('main', 0)}%"
        )

        print(
            f"{name}："
            f"波色双色命中率 "
            f"{wave.get('double', 0)}%"
        )

        print()

    print(
        "说明："
        "候选号码及属性预测来自历史统计模型；"
        "命中率来自严格Walk-Forward历史回测，"
        "不代表未来真实中奖概率。"
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
