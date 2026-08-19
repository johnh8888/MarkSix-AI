# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
V6.0 REAL DATA MULTI HISTORY FINAL
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict

from .api import fetch_lottery
from .database import (
    get_history,
    save_records,
)
from .predictor import (
    build_prediction,
)
from .backtest import (
    walk_forward,
    module_performance,
)


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


VERSION = (
    "V6.0 REAL DATA "
    "MULTI HISTORY FINAL"
)


def log(message: str = "") -> None:
    print(
        message,
        flush=True,
    )


def save_json(
    filename: str,
    data: Dict[str, Any],
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


def check_output(
    path: str,
) -> None:

    size = os.path.getsize(
        path
    )

    log(
        f"✅ {path} "
        f"({size} bytes)"
    )


def run_system() -> Dict[str, Any]:

    start_time = (
        datetime.now()
        .isoformat()
    )

    log("=" * 70)
    log("六合彩综合预测系统")
    log(
        "真实数据 + SQLite + "
        "多期历史统计 + "
        "Walk-Forward + 输出文件版"
    )
    log(
        f"版本：{VERSION}"
    )
    log(
        f"启动时间：{start_time}"
    )
    log("=" * 70)

    prediction_data: Dict[
        str,
        Any,
    ] = {
        "version": VERSION,
        "generated_at":
            datetime.now().isoformat(),
        "note":
            "历史统计分析结果，"
            "不代表真实中奖概率。",
        "lotteries": {},
    }

    backtest_data: Dict[
        str,
        Any,
    ] = {
        "version": VERSION,
        "generated_at":
            datetime.now().isoformat(),
        "method":
            "Walk-Forward",
        "lotteries": {},
    }

    performance_data: Dict[
        str,
        Any,
    ] = {
        "version": VERSION,
        "generated_at":
            datetime.now().isoformat(),
        "lotteries": {},
    }

    for lottery in LOTTERIES:

        log("=" * 70)
        log(
            f"正在更新：{lottery}"
        )
        log("=" * 70)

        # --------------------------------------
        # API
        # --------------------------------------

        try:

            api_result = fetch_lottery(
                lottery
            )

            records = api_result.get(
                "records",
                [],
            )

            inserted = save_records(
                lottery,
                records,
            )

            log(
                f"[{lottery}] "
                f"本次API数据："
                f"{len(records)}期"
            )

            log(
                f"[{lottery}] "
                f"本次新增："
                f"{inserted}期"
            )

        except Exception as exc:

            log(
                f"[WARN] "
                f"{lottery} 数据更新失败："
                f"{exc}"
            )

        # --------------------------------------
        # SQLite历史
        # --------------------------------------

        history = get_history(
            lottery,
            limit=500,
        )

        log("=" * 70)
        log(
            f"【{lottery}】"
        )
        log("=" * 70)

        if not history:

            log(
                "❌ 没有可用历史数据"
            )

            prediction = {
                "lottery": lottery,
                "latest_issue": "",
                "next_issue": "",
                "latest_numbers": [],
                "history_size": 0,
                "candidates": [],
                "hot_numbers": [],
                "cold_numbers": [],
                "attributes": {},
                "success": False,
                "status":
                    "无历史数据",
            }

            backtest = {
                "method":
                    "Walk-Forward",
                "history_size": 0,
                "samples": 0,
                "hits": 0,
                "hit_rate": 0.0,
                "status":
                    "无历史数据",
            }

            performance = {
                "history_size": 0,
                "modules": {},
            }

        else:

            # ----------------------------------
            # 预测
            # ----------------------------------

            prediction = build_prediction(
                lottery,
                history,
            )

            # ----------------------------------
            # 回测
            # ----------------------------------

            backtest = walk_forward(
                history
            )

            # ----------------------------------
            # 模块表现
            # ----------------------------------

            performance = (
                module_performance(
                    history
                )
            )

            # ----------------------------------
            # 终端输出
            # ----------------------------------

            log(
                f"历史期数："
                f"{len(history)}"
            )

            log(
                f"最新开奖期数："
                f"{prediction.get('latest_issue')}"
            )

            log(
                f"最新开奖号码："
                f"{' '.join(f'{x:02d}' for x in prediction.get('latest_numbers', []))}"
            )

            log(
                f"预测下一期期数："
                f"{prediction.get('next_issue')}"
            )

            log(
                f"特码："
                f"{prediction.get('latest_special')}"
            )

            attrs = prediction.get(
                "latest_attributes",
                {},
            )

            log(
                f"波色："
                f"{attrs.get('color', '')}"
            )

            log(
                f"大小："
                f"{attrs.get('size', '')}"
            )

            log(
                f"单双："
                f"{attrs.get('odd_even', '')}"
            )

            log(
                f"尾数："
                f"{attrs.get('tail', '')}"
            )

            log(
                f"分区："
                f"第{attrs.get('zone', '')}区"
            )

            log(
                "高频号码："
                + " ".join(
                    f"{x:02d}"
                    for x in prediction.get(
                        "hot_numbers",
                        [],
                    )
                )
            )

            log(
                "低频号码："
                + " ".join(
                    f"{x:02d}"
                    for x in prediction.get(
                        "cold_numbers",
                        [],
                    )
                )
            )

            log(
                "预测候选："
                + " ".join(
                    f"{x:02d}"
                    for x in prediction.get(
                        "candidates",
                        [],
                    )
                )
            )

            if len(history) < 10:

                log(
                    "⚠ 当前历史数据少于10期，"
                    "统计结果仅用于程序测试。"
                )

            elif len(history) < 30:

                log(
                    "⚠ 当前历史数据少于30期，"
                    "Walk-Forward样本有限。"
                )

            else:

                log(
                    "✅ 当前历史数据达到30期以上，"
                    "可以进行基础统计与回测。"
                )

            log(
                "说明：以上为基于历史数据"
                "的统计分析，不代表实际开奖结果。"
            )

        prediction[
            "backtest"
        ] = backtest

        prediction[
            "module_performance"
        ] = performance

        prediction_data[
            "lotteries"
        ][lottery] = prediction

        backtest_data[
            "lotteries"
        ][lottery] = backtest

        performance_data[
            "lotteries"
        ][lottery] = performance

    # ======================================================
    # 保存
    # ======================================================

    log("=" * 70)
    log("保存预测结果")
    log("=" * 70)

    prediction_path = save_json(
        "prediction.json",
        prediction_data,
    )

    log(
        f"✅ 预测结果已保存："
        f"{prediction_path}"
    )

    log("=" * 70)
    log("保存 Walk-Forward 回测")
    log("=" * 70)

    backtest_path = save_json(
        "backtest.json",
        backtest_data,
    )

    log(
        f"✅ 回测结果已保存："
        f"{backtest_path}"
    )

    log("=" * 70)
    log("保存模块表现")
    log("=" * 70)

    performance_path = save_json(
        "module_performance.json",
        performance_data,
    )

    log(
        f"✅ 模块表现已保存："
        f"{performance_path}"
    )

    # ======================================================
    # 文件检查
    # ======================================================

    log("=" * 70)
    log("输出文件检查")
    log("=" * 70)

    check_output(
        prediction_path
    )

    check_output(
        backtest_path
    )

    check_output(
        performance_path
    )

    # ======================================================
    # 三彩种最终汇总
    # ======================================================

    log("=" * 70)
    log("三彩种分析完成")
    log("=" * 70)

    for lottery in LOTTERIES:

        item = prediction_data[
            "lotteries"
        ].get(
            lottery,
            {},
        )

        candidates = item.get(
            "candidates",
            [],
        )

        latest_issue = item.get(
            "latest_issue",
            "",
        )

        next_issue = item.get(
            "next_issue",
            "",
        )

        log(
            f"{lottery}："
            f"最新{latest_issue} → "
            f"预测下一期{next_issue}："
            f"{' '.join(f'{x:02d}' for x in candidates)}"
        )

    log(
        "说明：候选号码来自历史统计评分，"
        "不代表真实中奖概率。"
    )

    log("=" * 70)
    log("系统运行结束")
    log("=" * 70)

    return {
        "prediction": prediction_data,
        "backtest": backtest_data,
        "module_performance":
            performance_data,
    }
