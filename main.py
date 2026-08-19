# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V7.2

真实数据
SQLite
特别号码预测
生肖 TOP5
单双单推
大小单推
波色主推 / 次推 / 双色
Walk-Forward 历史命中率

重要规则：

1. 号码预测只针对第7个号码（特别号码）
2. 每期实际特别号码只有1个，因此号码最多只能命中1个
3. 生肖针对特别号码推荐5个生肖
4. 单双只推荐1个
5. 大小只推荐1个
6. 波色：
   - 主推1个
   - 次推1个
   - 双色2个
7. Walk-Forward 完全按照上述规则计算
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime
from typing import Any


# ============================================================
# 兼容两种启动方式
#
# 1. python main.py
# 2. python -m package.main
# ============================================================

try:

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
    )

except ImportError:

    from api_sync import fetch_lottery
    from database import (
        save_records,
        load_records,
    )
    from metrics import (
        get_wave,
        get_size,
        get_odd_even,
        get_zodiac,
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
# 配置
# ============================================================

# 号码特别号预测数量
SPECIAL_NUMBER_TOP_N = 10

# 生肖推荐数量
ZODIAC_TOP_N = 5

# Walk-Forward 最少训练期数
MINIMUM_TRAIN = 30


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
# 下一期期号
# ============================================================

def next_issue(issue: str) -> str:

    try:

        return str(
            int(issue) + 1
        )

    except Exception:

        return ""


# ============================================================
# 安全排序
# ============================================================

def sort_history(
    history: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    def sort_key(row):

        try:

            return int(
                str(
                    row.get(
                        "issue",
                        "0",
                    )
                )
            )

        except Exception:

            return 0

    return sorted(
        history,
        key=sort_key,
    )


# ============================================================
# 获取特别号码
#
# 第7个号码 = 特别号码
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

    if len(numbers) < 7:

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
# 特别号码历史
# ============================================================

def special_history(
    history: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    result = []

    for row in history:

        number = get_special_number(
            row
        )

        if number is None:

            continue

        result.append(
            {
                "issue":
                    str(
                        row.get(
                            "issue",
                            "",
                        )
                    ),

                "number":
                    number,
            }
        )

    return result


# ============================================================
# 特别号码频率
# ============================================================

def special_number_counter(
    history: list[dict[str, Any]],
    window: int = 100,
) -> Counter:

    counter = Counter()

    rows = special_history(
        history
    )

    for row in rows[-window:]:

        counter[
            row["number"]
        ] += 1

    return counter


# ============================================================
# 特别号码预测
#
# 只针对第7个号码
#
# 注意：
# 这里虽然推荐多个号码，
# 但每期开奖只有一个特别号码，
# 因此一期开奖结果最多命中1个。
# ============================================================

def predict_special_numbers(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = special_number_counter(
        history,
        100,
    )

    scores = {}

    for number in range(
        1,
        50,
    ):

        scores[number] = (
            counter.get(
                number,
                0,
            )
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

    }


# ============================================================
# 生肖特别号统计
# ============================================================

def special_zodiac_counter(
    history: list[dict[str, Any]],
    window: int = 100,
) -> Counter:

    counter = Counter()

    rows = special_history(
        history
    )

    for row in rows[-window:]:

        zodiac = get_zodiac(
            row["number"],
            row["issue"],
        )

        if zodiac:

            counter[zodiac] += 1

    return counter


# ============================================================
# 生肖预测 TOP5
# ============================================================

def predict_zodiac(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = special_zodiac_counter(
        history,
        100,
    )

    all_zodiacs = [
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
        all_zodiacs,
        key=lambda x: (
            -counter.get(
                x,
                0,
            ),
            x,
        ),
    )

    top5 = ranking[:ZODIAC_TOP_N]

    return {

        "top5":
            top5,

        "main":
            top5[0]
            if top5
            else "",

        "secondary":
            top5[1]
            if len(top5) > 1
            else "",

        "double":
            top5[:2],

        "counts":
            {
                x:
                    counter.get(
                        x,
                        0,
                    )
                for x in all_zodiacs
            },

    }


# ============================================================
# 特别号属性统计
# ============================================================

def special_attribute_counter(
    history: list[dict[str, Any]],
    field: str,
    window: int = 100,
) -> Counter:

    counter = Counter()

    rows = special_history(
        history
    )

    for row in rows[-window:]:

        number = row[
            "number"
        ]

        issue = row[
            "issue"
        ]

        if field == "wave":

            value = get_wave(
                number
            )

        elif field == "size":

            value = get_size(
                number
            )

        elif field == "odd_even":

            value = get_odd_even(
                number
            )

        elif field == "zodiac":

            value = get_zodiac(
                number,
                issue,
            )

        else:

            continue

        if value:

            counter[value] += 1

    return counter


# ============================================================
# 单属性单推
#
# 单双、大小：
# 只推荐一个
# ============================================================

def predict_single_attribute(
    history: list[dict[str, Any]],
    field: str,
) -> dict[str, Any]:

    counter = special_attribute_counter(
        history,
        field,
        100,
    )

    if not counter:

        return {

            "main":
                "",

            "secondary":
                "",

            "double":
                [],

            "counts":
                {},

        }

    ranking = [
        item[0]
        for item in counter.most_common()
    ]

    main = ranking[0]

    return {

        "main":
            main,

        "secondary":
            ranking[1]
            if len(ranking) > 1
            else "",

        # 这里单双/大小不再作为双推输出
        "double":
            [main],

        "counts":
            dict(counter),

    }


# ============================================================
# 波色预测
#
# 主推1
# 次推1
# 双色2
# ============================================================

def predict_wave(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    counter = special_attribute_counter(
        history,
        "wave",
        100,
    )

    all_waves = [
        "红",
        "蓝",
        "绿",
    ]

    ranking = sorted(
        all_waves,
        key=lambda x: (
            -counter.get(
                x,
                0,
            ),
            x,
        ),
    )

    main = (
        ranking[0]
        if ranking
        else ""
    )

    secondary = (
        ranking[1]
        if len(ranking) > 1
        else ""
    )

    double = [
        x
        for x in (
            main,
            secondary,
        )
        if x
    ]

    return {

        "main":
            main,

        "secondary":
            secondary,

        "double":
            double,

        "counts":
            {
                x:
                    counter.get(
                        x,
                        0,
                    )
                for x in all_waves
            },

    }


# ============================================================
# 预测全部属性
# ============================================================

def predict_attributes(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    return {

        "zodiac":
            predict_zodiac(
                history
            ),

        "odd_even":
            predict_single_attribute(
                history,
                "odd_even",
            ),

        "size":
            predict_single_attribute(
                history,
                "size",
            ),

        "wave":
            predict_wave(
                history
            ),

    }


# ============================================================
# 单次预测
# ============================================================

def make_prediction(
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    numbers = predict_special_numbers(
        history
    )

    attributes = predict_attributes(
        history
    )

    return {

        "top5":
            numbers["top5"],

        "top10":
            numbers["top10"],

        "top12":
            numbers["top12"],

        "zodiac_top5":
            attributes[
                "zodiac"
            ]["top5"],

        "attributes":
            attributes,

    }


# ============================================================
# 评估单期预测
#
# 注意：
# actual 只取第7个特别号码。
# ============================================================

def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:

    actual_special = get_special_number(
        actual
    )

    if actual_special is None:

        return {}

    issue = str(
        actual.get(
            "issue",
            "",
        )
    )

    result = {}

    # ========================================================
    # 特别号码命中
    # 每期开奖最多命中1个
    # ========================================================

    result[
        "number_top5"
    ] = (
        actual_special
        in prediction.get(
            "top5",
            [],
        )
    )

    result[
        "number_top10"
    ] = (
        actual_special
        in prediction.get(
            "top10",
            [],
        )
    )

    result[
        "number_top12"
    ] = (
        actual_special
        in prediction.get(
            "top12",
            [],
        )
    )

    # ========================================================
    # 实际生肖
    # ========================================================

    actual_zodiac = get_zodiac(
        actual_special,
        issue,
    )

    zodiac_prediction = (
        prediction[
            "attributes"
        ][
            "zodiac"
        ]
    )

    zodiac_top5 = (
        zodiac_prediction.get(
            "top5",
            [],
        )
    )

    result[
        "zodiac_main"
    ] = (
        actual_zodiac
        == zodiac_prediction.get(
            "main",
            "",
        )
    )

    result[
        "zodiac_top5"
    ] = (
        actual_zodiac
        in zodiac_top5
    )

    # ========================================================
    # 实际单双
    # ========================================================

    actual_odd_even = get_odd_even(
        actual_special
    )

    odd_even_prediction = (
        prediction[
            "attributes"
        ][
            "odd_even"
        ]
    )

    result[
        "odd_even_main"
    ] = (
        actual_odd_even
        == odd_even_prediction.get(
            "main",
            "",
        )
    )

    # ========================================================
    # 实际大小
    # ========================================================

    actual_size = get_size(
        actual_special
    )

    size_prediction = (
        prediction[
            "attributes"
        ][
            "size"
        ]
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

    # ========================================================
    # 实际波色
    # ========================================================

    actual_wave = get_wave(
        actual_special
    )

    wave_prediction = (
        prediction[
            "attributes"
        ][
            "wave"
        ]
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
# 命中数量统计
# ============================================================

def calculate_average_hits(
    history: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> dict[str, float]:

    if not predictions:

        return {
            "top5": 0.0,
            "top10": 0.0,
            "top12": 0.0,
        }

    total_top5 = 0
    total_top10 = 0
    total_top12 = 0

    total = 0

    for prediction, actual in predictions:

        special = get_special_number(
            actual
        )

        if special is None:
            continue

        total += 1

        if special in prediction.get(
            "top5",
            [],
        ):
            total_top5 += 1

        if special in prediction.get(
            "top10",
            [],
        ):
            total_top10 += 1

        if special in prediction.get(
            "top12",
            [],
        ):
            total_top12 += 1

    if total == 0:

        return {
            "top5": 0.0,
            "top10": 0.0,
            "top12": 0.0,
        }

    return {

        "top5":
            round(
                total_top5 / total,
                4,
            ),

        "top10":
            round(
                total_top10 / total,
                4,
            ),

        "top12":
            round(
                total_top12 / total,
                4,
            ),

    }


# ============================================================
# 百分比
# ============================================================

def percentage(
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
# Walk-Forward
#
# 每一次：
#
# train = 之前所有历史
# actual = 当前一期
# prediction = train 预测
#
# 绝不使用未来数据
# ============================================================

def walk_forward(
    history: list[dict[str, Any]],
    minimum_train: int = MINIMUM_TRAIN,
) -> dict[str, Any]:

    history = sort_history(
        history
    )

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

    evaluations = []

    prediction_actual_pairs = []

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

        prediction = make_prediction(
            train
        )

        evaluation = evaluate_prediction(
            prediction,
            actual,
        )

        if evaluation:

            evaluations.append(
                evaluation
            )

            prediction_actual_pairs.append(
                (
                    prediction,
                    actual,
                )
            )

    total = len(
        evaluations
    )

    if total == 0:

        return {

            "method":
                "Walk-Forward",

            "samples":
                0,

            "status":
                "没有有效验证数据",

            "performance":
                {},

        }

    def count(key: str) -> int:

        return sum(
            1
            for item in evaluations
            if item.get(key)
        )

    # ========================================================
    # 号码平均命中
    #
    # 因为特别号码只有1个，
    # 所以平均命中数 = 命中率
    # ========================================================

    number_avg = (
        calculate_average_hits(
            history,
            prediction_actual_pairs,
        )
    )

    performance = {

        "samples":
            total,

        "numbers": {

            "top5":
                percentage(
                    count(
                        "number_top5"
                    ),
                    total,
                ),

            "top10":
                percentage(
                    count(
                        "number_top10"
                    ),
                    total,
                ),

            "top12":
                percentage(
                    count(
                        "number_top12"
                    ),
                    total,
                ),

            "average_hit": {

                "top5":
                    number_avg[
                        "top5"
                    ],

                "top10":
                    number_avg[
                        "top10"
                    ],

                "top12":
                    number_avg[
                        "top12"
                    ],

            },

        },

        "zodiac": {

            "main":
                percentage(
                    count(
                        "zodiac_main"
                    ),
                    total,
                ),

            "top5":
                percentage(
                    count(
                        "zodiac_top5"
                    ),
                    total,
                ),

        },

        "odd_even": {

            "main":
                percentage(
                    count(
                        "odd_even_main"
                    ),
                    total,
                ),

        },

        "size": {

            "main":
                percentage(
                    count(
                        "size_main"
                    ),
                    total,
                ),

        },

        "wave": {

            "main":
                percentage(
                    count(
                        "wave_main"
                    ),
                    total,
                ),

            "secondary":
                percentage(
                    count(
                        "wave_secondary"
                    ),
                    total,
                ),

            "double":
                percentage(
                    count(
                        "wave_double"
                    ),
                    total,
                ),

        },

        "status":
            "正常",

    }

    return {

        "method":
            "Walk-Forward",

        "samples":
            total,

        "status":
            "正常",

        "performance":
            performance,

    }


# ============================================================
# 分析单个彩种
# ============================================================

def analyze(
    lottery_name: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:

    history = sort_history(
        history
    )

    if not history:

        return {

            "lottery":
                lottery_name,

            "success":
                False,

            "error":
                "没有历史数据",

            "candidates":
                [],

        }

    latest = history[-1]

    latest_issue = str(
        latest.get(
            "issue",
            "",
        )
    )

    prediction_issue = next_issue(
        latest_issue
    )

    prediction = make_prediction(
        history
    )

    attributes = prediction[
        "attributes"
    ]

    walk = walk_forward(
        history
    )

    performance = walk.get(
        "performance",
        {},
    )

    return {

        "lottery":
            lottery_name,

        "success":
            True,

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
            get_special_number(
                latest
            ),

        "prediction_issue":
            prediction_issue,

        "next_prediction_issue":
            prediction_issue,

        "history_size":
            len(history),

        # ====================================================
        # 保留 CI 检查需要的 candidates
        # ====================================================

        "candidates":
            prediction[
                "top12"
            ],

        "top5":
            prediction[
                "top5"
            ],

        "top10":
            prediction[
                "top10"
            ],

        "top12":
            prediction[
                "top12"
            ],

        # ====================================================
        # 生肖
        # ====================================================

        "zodiac_top5":
            attributes[
                "zodiac"
            ][
                "top5"
            ],

        # ====================================================
        # 属性
        # ====================================================

        "attributes":
            attributes,

        # ====================================================
        # 回测
        # ====================================================

        "performance":
            performance,

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

    print(
        f"特别号码："
        f"{result.get('latest_special', ''):02d}"
        if result.get(
            "latest_special"
        ) is not None
        else "特别号码："
    )

    print()

    # ========================================================
    # 特别号码预测
    # ========================================================

    print(
        "【下一期特别号码预测】"
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

    print(
        "说明：以上号码只针对第7个特别号码，"
        "每期开奖最多命中1个。"
    )

    print()

    # ========================================================
    # 属性
    # ========================================================

    attrs = result[
        "attributes"
    ]

    zodiac = attrs[
        "zodiac"
    ]

    print(
        "【下一期特别生肖预测】"
    )

    print(
        "推荐5个："
        + " ".join(
            zodiac[
                "top5"
            ]
        )
    )

    print(
        f"主推："
        f"{zodiac.get('main', '')}"
    )

    odd_even = attrs[
        "odd_even"
    ]

    print(
        "【下一期单双】"
    )

    print(
        f"单推："
        f"{odd_even.get('main', '')}"
    )

    size = attrs[
        "size"
    ]

    print(
        "【下一期大小】"
    )

    print(
        f"单推："
        f"{size.get('main', '')}"
    )

    wave = attrs[
        "wave"
    ]

    print(
        "【下一期波色】"
    )

    print(
        f"主推："
        f"{wave.get('main', '')}"
    )

    print(
        f"次推："
        f"{wave.get('secondary', '')}"
    )

    print(
        "双色："
        + " + ".join(
            wave.get(
                "double",
                [],
            )
        )
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
            "【Walk-Forward 历史命中率】"
        )

        print(
            f"验证期数："
            f"{performance.get('samples', 0)}"
        )

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

        average_hit = numbers.get(
            "average_hit",
            {},
        )

        print(
            f"Top5平均命中数："
            f"{average_hit.get('top5', 0):.2f}"
        )

        print(
            f"Top10平均命中数："
            f"{average_hit.get('top10', 0):.2f}"
        )

        print(
            f"Top12平均命中数："
            f"{average_hit.get('top12', 0):.2f}"
        )

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
            f"5生肖："
            f"{zodiac_perf.get('top5', 0)}%"
        )

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
# 生成 backtest.json
# ============================================================

def build_backtest(
    all_results: dict[str, Any],
) -> dict[str, Any]:

    result = {

        "version":
            "V7.2 SPECIAL NUMBER WALK-FORWARD",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries":
            {},

    }

    for lottery, item in (
        all_results.items()
    ):

        result[
            "lotteries"
        ][lottery] = item.get(
            "backtest",
            {},
        )

    return result


# ============================================================
# 生成 module_performance.json
# ============================================================

def build_module_performance(
    all_results: dict[str, Any],
) -> dict[str, Any]:

    result = {

        "version":
            "V7.2",

        "generated_at":
            datetime.now().isoformat(),

        "lotteries":
            {},

    }

    for lottery, item in (
        all_results.items()
    ):

        result[
            "lotteries"
        ][lottery] = item.get(
            "performance",
            {},
        )

    return result


# ============================================================
# 主系统
# ============================================================

def run_system() -> None:

    ensure_dirs()

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
        "版本：V7.2 SPECIAL NUMBER FINAL"
    )

    print(
        f"启动时间："
        f"{datetime.now().isoformat()}"
    )

    print(
        "=" * 70
    )

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

            # =================================================
            # API 获取
            # =================================================

            records = fetch_lottery(
                lottery
            )

            print(
                f"[{lottery}] API获取："
                f"{len(records)} 期"
            )

            # =================================================
            # SQLite 保存
            #
            # 注意：
            # database.py 接收的是彩种名称，
            # 不是 db 文件路径。
            # =================================================

            if records:

                added = save_records(
                    lottery,
                    records,
                )

                print(
                    f"[{lottery}] "
                    f"本次新增：{added} 期"
                )

            # =================================================
            # 从数据库重新加载
            # =================================================

            history = load_records(
                lottery
            )

            print(
                f"[{lottery}] "
                f"当前数据库："
                f"{len(history)} 期"
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
                "只预测第7个特别号码，每期开奖最多命中1个",

            "zodiac":
                "特别生肖推荐5个",

            "odd_even":
                "特别号码单双只推1个",

            "size":
                "特别号码大小只推1个",

            "wave":
                "特别号码波色主推1个、次推1个、双色2个",

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
        f"预测结果已保存："
        f"{prediction_path}"
    )

    print(
        "=" * 70
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
        f"回测结果已保存："
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
        f"模块表现已保存："
        f"{module_path}"
    )

    # ========================================================
    # 汇总
    # ========================================================

    print(
        "=" * 70
    )

    print(
        "三彩种分析完成"
    )

    for name, result in (
        all_results.items()
    ):

        if not result.get(
            "success",
            False,
        ):

            print(
                f"{name}：分析失败"
            )

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
            "特别号码候选 "
            + " ".join(
                f"{x:02d}"
                for x in result.get(
                    "top12",
                    [],
                )
            )
        )

        zodiac = (
            result
            .get(
                "zodiac_top5",
                [],
            )
        )

        print(
            f"{name}："
            "特别生肖5个 "
            + " ".join(
                zodiac
            )
        )

        attrs = result.get(
            "attributes",
            {},
        )

        print(
            f"{name}："
            f"单双单推 "
            f"{attrs.get('odd_even', {}).get('main', '')}"
        )

        print(
            f"{name}："
            f"大小单推 "
            f"{attrs.get('size', {}).get('main', '')}"
        )

        wave = attrs.get(
            "wave",
            {},
        )

        print(
            f"{name}："
            f"波色主推 "
            f"{wave.get('main', '')} / "
            f"次推 "
            f"{wave.get('secondary', '')} / "
            f"双色 "
            f"{' + '.join(wave.get('double', []))}"
        )

    print(
        "=" * 70
    )

    print(
        "说明："
        "号码仅针对第7个特别号码；"
        "生肖仅针对特别号码；"
        "单双、大小仅针对特别号码；"
        "命中率采用严格Walk-Forward历史验证。"
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
