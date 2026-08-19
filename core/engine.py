# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V7.0

真实数据
SQLite
历史统计
Walk-Forward
号码预测
生肖
单双
大小
波色主推/次推/双色
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
    init_db,
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


LOTTERIES = [
    "新澳门彩",
    "老澳门彩",
    "香港彩",
]


DB_FILES = {
    "新澳门彩": "data/new_macau.db",
    "老澳门彩": "data/old_macau.db",
    "香港彩": "data/hk.db",
}


OUTPUT_DIR = "output"


def ensure_dirs() -> None:

    os.makedirs(
        "data",
        exist_ok=True,
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )


def next_issue(issue: str) -> str:

    try:
        return str(
            int(issue) + 1
        )
    except Exception:
        return ""


def count_numbers(
    history: list[dict[str, Any]],
    window: int = 100,
) -> Counter:

    counter = Counter()

    for row in history[-window:]:

        for number in row.get(
            "numbers",
            [],
        ):

            try:
                number = int(number)
            except Exception:
                continue

            if 1 <= number <= 49:
                counter[number] += 1

    return counter


def predict_numbers(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = count_numbers(
        history,
        100,
    )

    # 所有号码基础分
    scores = {}

    for number in range(
        1,
        50,
    ):

        frequency = counter.get(
            number,
            0,
        )

        scores[number] = (
            frequency
        )

    ranking = sorted(
        scores,
        key=lambda x: (
            -scores[x],
            x,
        ),
    )

    top5 = ranking[:5]
    top10 = ranking[:10]
    top12 = ranking[:12]

    return {
        "top5": top5,
        "top10": top10,
        "top12": top12,
    }


def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
    history_before: list[dict[str, Any]],
) -> dict[str, Any]:

    actual_numbers = set(
        actual.get(
            "numbers",
            [],
        )
    )

    if not actual_numbers:
        return {}

    actual_special = (
        actual.get(
            "numbers",
            [],
        )[-1]
    )

    issue = actual.get(
        "issue",
        "",
    )

    result = {}

    result[
        "number_top5"
    ] = bool(
        actual_numbers
        & set(
            prediction["top5"]
        )
    )

    result[
        "number_top10"
    ] = bool(
        actual_numbers
        & set(
            prediction["top10"]
        )
    )

    result[
        "number_top12"
    ] = bool(
        actual_numbers
        & set(
            prediction["top12"]
        )
    )

    attrs = prediction[
        "attributes"
    ]

    zodiac = get_zodiac(
        actual_special,
        issue,
    )

    wave = get_wave(
        actual_special
    )

    size = get_size(
        actual_special
    )

    odd_even = get_odd_even(
        actual_special
    )

    result[
        "zodiac_main"
    ] = (
        zodiac
        == attrs["zodiac"]["main"]
    )

    result[
        "zodiac_double"
    ] = (
        zodiac
        in attrs["zodiac"]["double"]
    )

    result[
        "odd_even_main"
    ] = (
        odd_even
        == attrs["odd_even"]["main"]
    )

    result[
        "odd_even_double"
    ] = (
        odd_even
        in attrs["odd_even"]["double"]
    )

    result[
        "size_main"
    ] = (
        size
        == attrs["size"]["main"]
    )

    result[
        "size_double"
    ] = (
        size
        in attrs["size"]["double"]
    )

    result[
        "wave_main"
    ] = (
        wave
        == attrs["wave"]["main"]
    )

    result[
        "wave_secondary"
    ] = (
        wave
        == attrs["wave"]["secondary"]
    )

    result[
        "wave_double"
    ] = (
        wave
        in attrs["wave"]["double"]
    )

    return result


def walk_forward(
    history: list[dict[str, Any]],
    minimum_train: int = 30,
) -> dict[str, Any]:

    evaluations = []

    if len(history) <= minimum_train:
        return {
            "method": "Walk-Forward",
            "samples": 0,
            "status": "历史数据不足",
            "performance": {},
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

        number_prediction = (
            predict_numbers(
                train
            )
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

    performance = (
        calculate_performance(
            evaluations
        )
    )

    return {
        "method": "Walk-Forward",
        "samples": len(
            evaluations
        ),
        "performance":
            performance,
        "status": "正常",
    }


def analyze(
    lottery_name: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:

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

    number_prediction = (
        predict_numbers(
            history
        )
    )

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

    print(
        "【号码预测】"
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

    attrs = result[
        "attributes"
    ]

    print(
        "【属性预测】"
    )

    print(
        "生肖："
        f"主推 {attrs['zodiac']['main']} "
        f"次推 {attrs['zodiac']['secondary']} "
        f"双推 {' + '.join(attrs['zodiac']['double'])}"
    )

    print(
        "单双："
        f"主推 {attrs['odd_even']['main']} "
        f"次推 {attrs['odd_even']['secondary']} "
        f"双推 {' + '.join(attrs['odd_even']['double'])}"
    )

    print(
        "大小："
        f"主推 {attrs['size']['main']} "
        f"次推 {attrs['size']['secondary']} "
        f"双推 {' + '.join(attrs['size']['double'])}"
    )

    print(
        "波色："
        f"主推 {attrs['wave']['main']} "
        f"次推 {attrs['wave']['secondary']} "
        f"双色 {' + '.join(attrs['wave']['double'])}"
    )

    print()

    performance = result[
        "performance"
    ]

    if performance:

        print(
            "【Walk-Forward 命中率】"
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

    print()


def run_system() -> None:

    ensure_dirs()

    init_db()

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

            records = fetch_lottery(
                lottery
            )

            if records:

                save_records(
                    DB_FILES[
                        lottery
                    ],
                    records,
                )

            history = load_records(
                DB_FILES[
                    lottery
                ]
            )

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

    prediction = {

        "version":
            "V7.0 REAL DATA HIT RATE",

        "generated_at":
            datetime.now().isoformat(),

        "note":
            "历史统计及Walk-Forward分析结果，不代表真实中奖概率。",

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
        "预测结果已保存："
        f"{prediction_path}"
    )

    print(
        "=" * 70
    )

    print(
        "三彩种分析完成"
    )

    for name, result in (
        all_results.items()
    ):

        if result.get(
            "success"
        ):

            print(
                f"{name}："
                f"最新第 "
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

    print(
        "=" * 70
    )

    print(
        "系统运行结束"
    )

    print(
        "=" * 70
    )
