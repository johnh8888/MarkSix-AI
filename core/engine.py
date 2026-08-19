# core/engine.py
# -*- coding: utf-8 -*-

"""
六合彩综合预测系统

V6.1 REAL DATA FIXED

功能：

真实 API
SQLite
多期历史
统计分析
Walk-Forward
模块表现
预测下一期
最新开奖期数
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from .api_sync import sync_lottery


# ============================================================
# 基础配置
# ============================================================

VERSION = "V6.1 REAL DATA FIXED"

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output",
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True,
)


LOTTERIES = [
    "新澳门彩",
    "老澳门彩",
    "香港彩",
]


# ============================================================
# 日志
# ============================================================

def log(message: str = "") -> None:
    print(message, flush=True)


# ============================================================
# 波色
# ============================================================

RED = {
    1, 2, 7, 8, 12, 13, 18, 19,
    23, 24, 29, 30, 34, 35, 40,
    45, 46,
}

BLUE = {
    3, 4, 9, 10, 14, 15, 20,
    25, 26, 31, 36, 37, 41,
    42, 47, 48,
}

GREEN = {
    5, 6, 11, 16, 17, 21, 22,
    27, 28, 32, 33, 38, 39,
    43, 44, 49,
}


def get_color(
    number: int,
) -> str:

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return "未知"


def get_size(
    number: int,
) -> str:

    return "大" if number >= 25 else "小"


def get_odd_even(
    number: int,
) -> str:

    return "单" if number % 2 else "双"


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
# 期号
# ============================================================

def next_issue(
    issue: str,
) -> str:

    if not issue:
        return ""

    try:

        value = int(
            issue
        )

        return str(
            value + 1
        )

    except Exception:

        return ""


# ============================================================
# 历史号码展开
# ============================================================

def flatten_numbers(
    history: List[Dict[str, Any]],
) -> List[int]:

    numbers = []

    for row in history:

        for number in row.get(
            "numbers",
            [],
        ):

            try:

                number = int(
                    number
                )

                if 1 <= number <= 49:
                    numbers.append(
                        number
                    )

            except Exception:
                continue

    return numbers


# ============================================================
# 属性统计
# ============================================================

def attribute_statistics(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    colors = Counter()
    sizes = Counter()
    odd_even = Counter()
    tails = Counter()
    zones = Counter()

    for row in history:

        numbers = row.get(
            "numbers",
            [],
        )

        if not numbers:
            continue

        # 以特码统计
        number = int(
            numbers[-1]
        )

        colors[
            get_color(number)
        ] += 1

        sizes[
            get_size(number)
        ] += 1

        odd_even[
            get_odd_even(number)
        ] += 1

        tails[
            str(get_tail(number))
        ] += 1

        zones[
            str(get_zone(number))
        ] += 1

    return {
        "sample_size": len(history),
        "colors": dict(colors),
        "sizes": dict(sizes),
        "odd_even": dict(odd_even),
        "tails": dict(tails),
        "zones": dict(zones),
    }


# ============================================================
# 号码频率
# ============================================================

def frequency_scores(
    history: List[Dict[str, Any]],
) -> Dict[int, int]:

    counter = Counter(
        flatten_numbers(
            history
        )
    )

    return {
        number: counter.get(
            number,
            0,
        )
        for number in range(
            1,
            50,
        )
    }


# ============================================================
# 最近频率
# ============================================================

def recent_frequency(
    history: List[Dict[str, Any]],
    window: int = 10,
) -> Dict[int, int]:

    recent = history[
        -window:
    ]

    return frequency_scores(
        recent
    )


# ============================================================
# 综合候选
# ============================================================

def make_candidates(
    history: List[Dict[str, Any]],
    limit: int = 12,
) -> Dict[str, Any]:

    if not history:

        return {
            "candidates": [],
            "hot_numbers": [],
            "cold_numbers": [],
        }

    scores = frequency_scores(
        history
    )

    recent = recent_frequency(
        history
    )

    # --------------------------------------------------------
    # 综合评分
    # --------------------------------------------------------

    ranking = []

    for number in range(
        1,
        50,
    ):

        score = (
            scores.get(
                number,
                0,
            ) * 0.60
            +
            recent.get(
                number,
                0,
            ) * 0.40
        )

        ranking.append(
            (
                number,
                score,
                scores.get(
                    number,
                    0,
                ),
            )
        )

    ranking.sort(
        key=lambda x: (
            x[1],
            x[2],
            -x[0],
        ),
        reverse=True,
    )

    hot = [
        x[0]
        for x in ranking[:10]
    ]

    # --------------------------------------------------------
    # 冷号
    # --------------------------------------------------------

    cold_ranking = sorted(
        ranking,
        key=lambda x: (
            x[1],
            x[2],
            x[0],
        ),
    )

    cold = [
        x[0]
        for x in cold_ranking[:10]
    ]

    candidates = [
        x[0]
        for x in ranking[:limit]
    ]

    return {
        "candidates": candidates,
        "hot_numbers": hot,
        "cold_numbers": cold,
    }


# ============================================================
# Walk Forward
# ============================================================

def walk_forward(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    size = len(history)

    # 至少需要 11 期才有意义
    if size < 11:

        return {
            "method": "Walk-Forward",
            "history_size": size,
            "samples": 0,
            "hits": 0,
            "hit_rate": 0.0,
            "status": "历史数据不足",
        }

    samples = 0
    hits = 0

    # --------------------------------------------------------
    # 每次用前面的数据预测下一期
    # --------------------------------------------------------

    for index in range(
        10,
        size,
    ):

        train = history[
            :index
        ]

        target = history[
            index
        ]

        prediction = make_candidates(
            train,
            limit=12,
        )

        candidates = set(
            prediction[
                "candidates"
            ]
        )

        actual = set(
            int(x)
            for x in target.get(
                "numbers",
                [],
            )
        )

        if candidates & actual:
            hits += 1

        samples += 1

    hit_rate = (
        hits / samples
        if samples
        else 0.0
    )

    return {
        "method": "Walk-Forward",
        "history_size": size,
        "samples": samples,
        "hits": hits,
        "hit_rate": round(
            hit_rate,
            4,
        ),
        "status": "正常",
    }


# ============================================================
# 模块表现
# ============================================================

def module_performance(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    size = len(history)

    if size < 10:

        status = "数据不足"

    else:

        status = "可评估"

    return {
        "history_size": size,
        "modules": {
            "frequency": {
                "score": 0.0,
                "status": status,
            },
            "recent_frequency": {
                "score": 0.0,
                "status": status,
            },
            "overdue": {
                "score": 0.0,
                "status": status,
            },
        },
    }


# ============================================================
# 单彩种分析
# ============================================================

def analyze_lottery(
    lottery_name: str,
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    history = list(
        history or []
    )

    history.sort(
        key=lambda x: int(
            x.get(
                "issue",
                "0",
            )
        )
        if str(
            x.get(
                "issue",
                "0",
            )
        ).isdigit()
        else 0
    )

    latest_issue = ""

    latest_numbers: List[int] = []

    if history:

        latest = history[-1]

        latest_issue = str(
            latest.get(
                "issue",
                "",
            )
        )

        latest_numbers = [
            int(x)
            for x in latest.get(
                "numbers",
                [],
            )
        ]

    prediction_issue = next_issue(
        latest_issue
    )

    attributes = attribute_statistics(
        history
    )

    candidates = make_candidates(
        history,
        limit=12,
    )

    backtest = walk_forward(
        history
    )

    performance = module_performance(
        history
    )

    return {
        "lottery": lottery_name,

        # ----------------------------------------------------
        # 最新开奖
        # ----------------------------------------------------

        "latest_issue": latest_issue,

        "latest_draw_issue": latest_issue,

        "latest_numbers": latest_numbers,

        # ----------------------------------------------------
        # 下一期
        # ----------------------------------------------------

        "prediction_issue": prediction_issue,

        "next_prediction_issue": prediction_issue,

        # ----------------------------------------------------
        # 历史
        # ----------------------------------------------------

        "history_size": len(history),

        # ----------------------------------------------------
        # 候选
        # ----------------------------------------------------

        "candidates": candidates[
            "candidates"
        ],

        "hot_numbers": candidates[
            "hot_numbers"
        ],

        "cold_numbers": candidates[
            "cold_numbers"
        ],

        # ----------------------------------------------------
        # 属性
        # ----------------------------------------------------

        "attributes": attributes,

        # ----------------------------------------------------
        # 回测
        # ----------------------------------------------------

        "backtest": backtest,

        # ----------------------------------------------------
        # 模块
        # ----------------------------------------------------

        "module_performance": performance,

        "success": bool(
            history
        ),
    }


# ============================================================
# 保存 JSON
# ============================================================

def save_json(
    filename: str,
    data: Dict[str, Any],
) -> None:

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

    log(
        f"✅ {filename} 已保存：{path}"
    )


# ============================================================
# 文件检查
# ============================================================

def check_output_files() -> None:

    log("=" * 70)
    log("输出文件检查")
    log("=" * 70)

    files = [
        "prediction.json",
        "backtest.json",
        "module_performance.json",
    ]

    for filename in files:

        path = os.path.join(
            OUTPUT_DIR,
            filename,
        )

        if not os.path.isfile(
            path
        ):

            raise RuntimeError(
                f"输出文件不存在：{path}"
            )

        size = os.path.getsize(
            path
        )

        log(
            f"✅ {path} "
            f"({size} bytes)"
        )


# ============================================================
# 打印结果
# ============================================================

def print_results(
    results: Dict[str, Any],
) -> None:

    log("=" * 70)
    log("三彩种分析完成")
    log("=" * 70)

    for lottery_name in LOTTERIES:

        item = results.get(
            lottery_name,
            {},
        )

        latest_issue = item.get(
            "latest_issue",
            "",
        )

        prediction_issue = item.get(
            "prediction_issue",
            "",
        )

        candidates = item.get(
            "candidates",
            [],
        )

        candidate_text = " ".join(
            f"{int(x):02d}"
            for x in candidates
        )

        log(
            f"{lottery_name}："
            f"最新开奖第 {latest_issue} 期"
        )

        log(
            f"{lottery_name}："
            f"预测下一期第 {prediction_issue} 期"
        )

        log(
            f"{lottery_name}候选："
            f"{candidate_text}"
        )

    log(
        "说明：候选号码来自历史统计评分，"
        "不代表真实中奖概率。"
    )


# ============================================================
# 主系统
# ============================================================

def run_system(
    sync: bool = True,
    **kwargs,
) -> Dict[str, Any]:

    start_time = datetime.now()

    log("=" * 70)
    log("六合彩综合预测系统")
    log(
        "真实数据 + SQLite + 多期历史统计 "
        "+ Walk-Forward + 输出文件版"
    )
    log(
        f"版本：{VERSION}"
    )
    log(
        f"启动时间：{start_time.isoformat()}"
    )
    log("=" * 70)

    results: Dict[str, Any] = {}

    # ========================================================
    # 三彩种
    # ========================================================

    for lottery_name in LOTTERIES:

        try:

            if sync:

                sync_result = sync_lottery(
                    lottery_name
                )

                history = sync_result.get(
                    "history",
                    [],
                )

            else:

                # 即使不主动同步，也从 API 模块读取数据库
                from .api_sync import load_history

                history = load_history(
                    lottery_name
                )

            log("=" * 70)
            log(
                f"【{lottery_name}】"
            )
            log("=" * 70)

            result = analyze_lottery(
                lottery_name,
                history,
            )

            results[
                lottery_name
            ] = result

            # ------------------------------------------------
            # 详细输出
            # ------------------------------------------------

            log(
                f"历史期数："
                f"{result['history_size']}"
            )

            log(
                f"最新开奖期数："
                f"{result['latest_issue']}"
            )

            log(
                f"下一期预测期数："
                f"{result['prediction_issue']}"
            )

            log(
                f"最新号码："
                f"{result['latest_numbers']}"
            )

            attributes = result[
                "attributes"
            ]

            log(
                "近期开奖属性统计："
            )

            log(
                f"波色："
                f"{attributes['colors']}"
            )

            log(
                f"大小："
                f"{attributes['sizes']}"
            )

            log(
                f"单双："
                f"{attributes['odd_even']}"
            )

            log(
                f"尾数："
                f"{attributes['tails']}"
            )

            log(
                f"分区："
                f"{attributes['zones']}"
            )

            hot = " ".join(
                f"{x:02d}"
                for x in result[
                    "hot_numbers"
                ]
            )

            cold = " ".join(
                f"{x:02d}"
                for x in result[
                    "cold_numbers"
                ]
            )

            candidate = " ".join(
                f"{x:02d}"
                for x in result[
                    "candidates"
                ]
            )

            log(
                f"高频号码：{hot}"
            )

            log(
                f"低频号码：{cold}"
            )

            log(
                f"综合候选：{candidate}"
            )

            if result[
                "history_size"
            ] < 10:

                log(
                    "⚠ 当前历史数据少于10期，"
                    "统计结果仅用于程序测试，"
                    "不适合进行稳定性判断。"
                )

            log(
                "说明：以上为基于历史数据的统计分析，"
                "不代表实际开奖结果。"
            )

        except Exception as exc:

            log(
                f"[ERROR] "
                f"{lottery_name}分析失败：{exc}"
            )

            results[
                lottery_name
            ] = {
                "lottery": lottery_name,
                "latest_issue": "",
                "latest_draw_issue": "",
                "latest_numbers": [],
                "prediction_issue": "",
                "next_prediction_issue": "",
                "history_size": 0,
                "candidates": [],
                "hot_numbers": [],
                "cold_numbers": [],
                "attributes": {
                    "sample_size": 0,
                    "colors": {},
                    "sizes": {},
                    "odd_even": {},
                    "tails": {},
                    "zones": {},
                },
                "backtest": {
                    "method": "Walk-Forward",
                    "history_size": 0,
                    "samples": 0,
                    "hits": 0,
                    "hit_rate": 0.0,
                    "status": "执行失败",
                },
                "module_performance": {
                    "history_size": 0,
                    "modules": {},
                },
                "success": False,
                "error": str(exc),
            }

    # ========================================================
    # prediction.json
    # ========================================================

    prediction = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(),
        "note": (
            "历史统计分析结果，"
            "不代表真实中奖概率。"
        ),
        "lotteries": results,
    }

    log("=" * 70)
    log("保存预测结果")
    log("=" * 70)

    save_json(
        "prediction.json",
        prediction,
    )

    # ========================================================
    # backtest
    # ========================================================

    backtest = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(),
        "method": "Walk-Forward",
        "lotteries": {
            name: item.get(
                "backtest",
                {},
            )
            for name, item
            in results.items()
        },
    }

    log("=" * 70)
    log("保存 Walk-Forward 回测")
    log("=" * 70)

    save_json(
        "backtest.json",
        backtest,
    )

    # ========================================================
    # module performance
    # ========================================================

    performance = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(),
        "lotteries": {
            name: item.get(
                "module_performance",
                {},
            )
            for name, item
            in results.items()
        },
    }

    log("=" * 70)
    log("保存模块表现")
    log("=" * 70)

    save_json(
        "module_performance.json",
        performance,
    )

    # ========================================================
    # 检查
    # ========================================================

    check_output_files()

    # ========================================================
    # 最终结果
    # ========================================================

    print_results(
        results
    )

    log("=" * 70)
    log("系统运行结束")
    log("=" * 70)

    return prediction


# ============================================================
# 兼容旧入口
# ============================================================

def run(*args, **kwargs):
    return run_system(
        *args,
        **kwargs,
    )


def start(*args, **kwargs):
    return run_system(
        *args,
        **kwargs,
    )


def main(*args, **kwargs):
    return run_system(
        *args,
        **kwargs,
    )


# ============================================================
# 直接执行
# ============================================================

if __name__ == "__main__":
    run_system()
