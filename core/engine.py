# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
V7.2 IMPROVED SCORING

功能：

真实历史数据
SQLite
三彩种
号码预测（多窗口加权 + 遗漏值，目标统一为特别号码）
Top5 / Top10 / Top12
生肖
单双
大小
波色
波色主推
波色次推
波色双色
Walk-Forward
历史命中率（含平均命中数）
下一期期号
JSON输出

V7.2 相对 V7.1 的改动：

1. 号码预测模型从"单窗口原始计数"改为"多窗口加权 + 遗漏值"，
   并且统计目标从"每期全部7个号码"改为"每期特别号码"，
   与 metrics.py 的 Walk-Forward 验证目标保持一致
   （之前训练目标和验证目标不是同一个东西，命中率数字口径不一致）。

2. 诚实说明：六合彩本质上是独立随机事件，历史开奖频率不会
   改变未来任何一期的概率分布。这里的模型改进是让"能从历史
   数据里提取到的统计信息"更充分地被利用，而不是让预测本身
   获得真实的、超越随机的统计优势。如果 Walk-Forward 命中率
   长期稳定维持在随机基准附近
   （Top5≈10.2% / Top10≈20.4% / Top12≈24.5%），
   说明模型没有、也不可能有超越随机的预测能力，
   这是符合随机性假设的正常结果，不代表代码有问题。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from collections import Counter
from typing import Any

from .api_sync import (
    fetch_lottery,
)

from .database import (
    init_db,
    save_records,
    load_records,
    count_records,
)

from .metrics import (
    predict_attribute,
    evaluate_prediction,
    calculate_performance,
)


# ============================================================
# 彩种
# ============================================================

LOTTERIES = [

    "新澳门彩",

    "老澳门彩",

    "香港彩",

]


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
# 特别号码提取
# ============================================================

def get_special(
    row: dict[str, Any],
) -> int | None:

    numbers = row.get(
        "numbers",
        [],
    )

    if len(numbers) != 7:
        return None

    try:

        value = int(
            numbers[6]
        )

    except Exception:

        return None

    if not 1 <= value <= 49:
        return None

    return value


def special_history(
    history: list[dict[str, Any]],
    window: int | None = None,
) -> list[int]:

    rows = (
        history[-window:]
        if window
        else history
    )

    result = []

    for row in rows:

        special = get_special(
            row
        )

        if special is not None:

            result.append(
                special
            )

    return result


def missing_periods_all(
    history: list[dict[str, Any]],
) -> dict[int, int]:

    """
    一次遍历，算出全部1~49号码各自的遗漏期数
    （距离该号码上一次作为特别号码开出，已经过去多少期）。

    比逐个号码单独扫描历史快得多（O(n) 而不是 O(49n)）。
    """

    result: dict[int, int] = {}

    found: set[int] = set()

    count = 0

    for row in reversed(history):

        if len(found) >= 49:
            break

        special = get_special(
            row
        )

        if (
            special is not None
            and special not in found
        ):

            result[special] = count

            found.add(special)

        count += 1

    for number in range(1, 50):

        if number not in result:

            result[number] = min(
                count,
                40,
            )

    return result


# ============================================================
# 号码预测
#
# 多窗口加权 + 遗漏值评分。
# 评分只针对特别号码这一个目标，
# 与 Walk-Forward 验证口径保持一致。
# ============================================================

def predict_numbers(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    recent10 = Counter(
        special_history(history, 10)
    )

    recent30 = Counter(
        special_history(history, 30)
    )

    recent100 = Counter(
        special_history(history, 100)
    )

    missing_map = missing_periods_all(
        history
    )

    scores = {}

    for number in range(1, 50):

        frequency_score = (
            recent10.get(number, 0) * 2.5
            + recent30.get(number, 0) * 1.3
            + recent100.get(number, 0) * 0.8
        )

        missing = min(
            missing_map.get(number, 40),
            40,
        )

        missing_score = missing * 0.15

        scores[number] = round(
            frequency_score + missing_score,
            4,
        )

    ranking = sorted(
        range(1, 50),
        key=lambda x: (
            -scores[x],
            x,
        ),
    )

    return {

        "top5":
            ranking[:5],

        "top10":
            ranking[:10],

        "top12":
            ranking[:12],

        "scores":
            scores,

        "frequency":
            dict(recent100),

    }


# ============================================================
# 属性预测
# ============================================================

def predict_attributes(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    return {

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

            "method":
                "Walk-Forward",

            "minimum_train":
                minimum_train,

            "samples":
                0,

            "status":
                "历史数据不足",

            "performance":
                {
                    "samples": 0,
                    "status":
                        "历史数据不足",
                },
        }

    # --------------------------------------------------------
    # 从第31期开始滚动预测
    # --------------------------------------------------------

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

        # --------------------------------------------
        # 号码
        # --------------------------------------------

        number_prediction = (
            predict_numbers(
                train
            )
        )

        # --------------------------------------------
        # 属性
        # --------------------------------------------

        attributes = (
            predict_attributes(
                train
            )
        )

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

        evaluation = (
            evaluate_prediction(
                prediction,
                actual,
                train,
            )
        )

        if evaluation:

            evaluations.append(
                evaluation
            )

    # --------------------------------------------------------
    # 汇总
    # --------------------------------------------------------

    performance = (
        calculate_performance(
            evaluations
        )
    )

    return {

        "method":
            "Walk-Forward",

        "minimum_train":
            minimum_train,

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

    # --------------------------------------------------------
    # 最新开奖
    # --------------------------------------------------------

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

    latest_numbers = (
        latest.get(
            "numbers",
            [],
        )
    )

    # --------------------------------------------------------
    # 下一期
    # --------------------------------------------------------

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

    number_prediction = (
        predict_numbers(
            history
        )
    )

    # --------------------------------------------------------
    # 属性
    # --------------------------------------------------------

    attributes = (
        predict_attributes(
            history
        )
    )

    # --------------------------------------------------------
    # Walk Forward
    # --------------------------------------------------------

    walk = walk_forward(
        history
    )

    performance = (
        walk.get(
            "performance",
            {},
        )
    )

    # --------------------------------------------------------
    # 结果
    # --------------------------------------------------------

    return {

        "lottery":
            lottery_name,

        "latest_issue":
            latest_issue,

        "latest_draw_issue":
            latest_issue,

        "prediction_issue":
            prediction_issue,

        "next_prediction_issue":
            prediction_issue,

        "latest_numbers":
            latest_numbers,

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

        "number_scores":
            number_prediction[
                "scores"
            ],

        "frequency":
            number_prediction[
                "frequency"
            ],

        "attributes":
            attributes,

        "performance":
            performance,

        "backtest":
            walk,

        "success":
            bool(history),

    }


# ============================================================
# 格式化号码
# ============================================================

def format_numbers(
    numbers: list[int],
) -> str:

    return " ".join(
        f"{int(x):02d}"
        for x in numbers
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
        + format_numbers(
            result[
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
        + format_numbers(
            result["top5"]
        )
    )

    print(
        "Top10："
        + format_numbers(
            result["top10"]
        )
    )

    print(
        "Top12："
        + format_numbers(
            result["top12"]
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
        "【下一期属性预测】"
    )

    zodiac = attrs[
        "zodiac"
    ]

    print(
        "生肖："
        f"主推 {zodiac.get('main', '')} "
        f"次推 {zodiac.get('secondary', '')} "
        f"双推 {' + '.join(zodiac.get('double', []))}"
    )

    odd_even = attrs[
        "odd_even"
    ]

    print(
        "单双："
        f"主推 {odd_even.get('main', '')} "
        f"次推 {odd_even.get('secondary', '')} "
        f"双推 {' + '.join(odd_even.get('double', []))}"
    )

    size = attrs[
        "size"
    ]

    print(
        "大小："
        f"主推 {size.get('main', '')} "
        f"次推 {size.get('secondary', '')} "
        f"双推 {' + '.join(size.get('double', []))}"
    )

    wave = attrs[
        "wave"
    ]

    print(
        "波色："
        f"主推 {wave.get('main', '')} "
        f"次推 {wave.get('secondary', '')} "
        f"双色 {' + '.join(wave.get('double', []))}"
    )

    print()

    # ========================================================
    # 命中率
    # ========================================================

    performance = result.get(
        "performance",
        {},
    )

    if not performance:

        print(
            "【Walk-Forward】"
        )

        print(
            "暂无历史命中率"
        )

        print()

        return

    if performance.get(
        "status"
    ) == "历史数据不足":

        print(
            "【Walk-Forward】"
        )

        print(
            "历史数据不足"
        )

        print()

        return

    print(
        "【Walk-Forward 历史命中率】"
    )

    print(
        f"验证期数："
        f"{performance.get('samples', 0)}"
    )

    # --------------------------------------------------------
    # 号码
    # --------------------------------------------------------

    numbers = performance.get(
        "numbers",
        {},
    )

    print()

    print(
        "【号码命中】"
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

    print(
        f"Top5平均命中数："
        f"{numbers.get('average_top5_hits', 0)}"
    )

    print(
        f"Top10平均命中数："
        f"{numbers.get('average_top10_hits', 0)}"
    )

    print(
        f"Top12平均命中数："
        f"{numbers.get('average_top12_hits', 0)}"
    )

    # --------------------------------------------------------
    # 生肖
    # --------------------------------------------------------

    zodiac = performance.get(
        "zodiac",
        {},
    )

    print()

    print(
        "【生肖命中】"
    )

    print(
        f"主推："
        f"{zodiac.get('main', 0)}%"
    )

    print(
        f"次推："
        f"{zodiac.get('secondary', 0)}%"
    )

    print(
        f"双推："
        f"{zodiac.get('double', 0)}%"
    )

    # --------------------------------------------------------
    # 单双
    # --------------------------------------------------------

    odd_even = performance.get(
        "odd_even",
        {},
    )

    print()

    print(
        "【单双命中】"
    )

    print(
        f"主推："
        f"{odd_even.get('main', 0)}%"
    )

    print(
        f"次推："
        f"{odd_even.get('secondary', 0)}%"
    )

    print(
        f"双推："
        f"{odd_even.get('double', 0)}%"
    )

    # --------------------------------------------------------
    # 大小
    # --------------------------------------------------------

    size = performance.get(
        "size",
        {},
    )

    print()

    print(
        "【大小命中】"
    )

    print(
        f"主推："
        f"{size.get('main', 0)}%"
    )

    print(
        f"次推："
        f"{size.get('secondary', 0)}%"
    )

    print(
        f"双推："
        f"{size.get('double', 0)}%"
    )

    # --------------------------------------------------------
    # 波色
    # --------------------------------------------------------

    wave = performance.get(
        "wave",
        {},
    )

    print()

    print(
        "【波色命中】"
    )

    print(
        f"主推："
        f"{wave.get('main', 0)}%"
    )

    print(
        f"次推："
        f"{wave.get('secondary', 0)}%"
    )

    print(
        f"双色："
        f"{wave.get('double', 0)}%"
    )

    print()


# ============================================================
# 保存 JSON
# ============================================================

def save_json(
    filename: str,
    data: dict[str, Any],
) -> str:

    path = os.path.join(
        OUTPUT_DIR,
        filename,
    )

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

    return path


# ============================================================
# 主系统
# ============================================================

def run_system() -> None:

    ensure_dirs()

    init_db()

    all_results = {}

    print(
        "=" * 70
    )

    print(
        "六合彩综合预测系统"
    )

    print(
        "真实数据 + SQLite + "
        "Walk-Forward + 命中率"
    )

    print(
        "版本：V7.2 IMPROVED SCORING"
    )

    print(
        f"启动时间："
        f"{datetime.now().isoformat()}"
    )

    print(
        "=" * 70
    )

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

            # =================================================
            # API
            # =================================================

            records = fetch_lottery(
                lottery
            )

            # =================================================
            # SQLite
            # =================================================

            added = save_records(
                lottery,
                records,
            )

            print(
                f"[{lottery}] "
                f"本次新增：{added} 期"
            )

            # =================================================
            # 重新读取数据库
            # =================================================

            history = load_records(
                lottery
            )

            total = count_records(
                lottery
            )

            print(
                f"[{lottery}] "
                f"当前数据库历史："
                f"{total} 期"
            )

            # =================================================
            # 分析
            # =================================================

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
    # 总预测文件
    # ========================================================

    prediction = {

        "version":
            "V7.2 IMPROVED SCORING",

        "generated_at":
            datetime.now().isoformat(),

        "note":
            "基于历史开奖记录进行统计和Walk-Forward验证，不代表实际中奖概率。",

        "lotteries":
            all_results,

    }

    prediction_path = save_json(
        "prediction.json",
        prediction,
    )

    # ========================================================
    # 单独保存回测
    # ========================================================

    backtest = {

        "version":
            "V7.2",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries": {

            name:
                result.get(
                    "backtest",
                    {},
                )

            for name, result
            in all_results.items()

        },

    }

    backtest_path = save_json(
        "backtest.json",
        backtest,
    )

    # ========================================================
    # 模块表现
    # ========================================================

    module_performance = {

        "version":
            "V7.2",

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

        },

    }

    performance_path = save_json(
        "module_performance.json",
        module_performance,
    )

    # ========================================================
    # 输出
    # ========================================================

    print(
        "=" * 70
    )

    print(
        "预测结果已保存："
        f"{prediction_path}"
    )

    print(
        "回测结果已保存："
        f"{backtest_path}"
    )

    print(
        "模块表现已保存："
        f"{performance_path}"
    )

    print(
        "=" * 70
    )

    print(
        "三彩种分析完成"
    )

    print()

    for name, result in (
        all_results.items()
    ):

        if not result.get(
            "success"
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
            f"候选 "
            f"{format_numbers(result.get('top12', []))}"
        )

        performance = result.get(
            "performance",
            {},
        )

        if performance.get(
            "status"
        ) != "历史数据不足":

            wave = performance.get(
                "wave",
                {},
            )

            print(
                f"{name}："
                f"波色主推命中率 "
                f"{wave.get('main', 0)}% / "
                f"次推 "
                f"{wave.get('secondary', 0)}% / "
                f"双色 "
                f"{wave.get('double', 0)}%"
            )

        print()

    print(
        "=" * 70
    )

    print(
        "说明："
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
