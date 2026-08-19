# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

系统总控制引擎

流程：

main.py
   ↓
engine
   ↓
数据库初始化
   ↓
API同步
   ↓
读取历史
   ↓
质量检测
   ↓
预测
   ↓
Walk Forward
   ↓
JSON输出
"""

from __future__ import annotations

import json

from datetime import datetime


from config import (
    LOTTERIES,
    OUTPUT_DIR,
    VERSION
)


from .database import (
    init_database,
    load_history
)


from .api_sync import (
    sync_all
)


from .predictor import (
    predict
)


from .backtest import (
    walk_forward
)


from .quality import (
    check_history
)


# =====================================================
# 保存JSON
# =====================================================

def save_output(data):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file = (
        OUTPUT_DIR
        / "prediction.json"
    )

    file.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print(
        "输出文件:",
        file
    )

    return file


# =====================================================
# 单彩种分析
# =====================================================

def analyze_lottery(
    key
):

    name = LOTTERIES[key]

    print()
    print(
        "=" * 70
    )

    print(
        "分析:",
        name
    )

    print(
        "=" * 70
    )

    history = load_history(
        key
    )

    print(
        "历史数量:",
        len(history)
    )

    quality = check_history(
        history
    )

    print(
        "数据质量:",
        quality["质量"]
    )

    if not history:

        return {

            "彩种":
                name,

            "错误":
                "没有历史数据",

            "数据质量":
                quality
        }

    try:

        prediction = predict(
            history
        )

    except Exception as e:

        prediction = {
            "错误":
                f"预测失败: {e}"
        }

    try:

        backtest = walk_forward(
            history
        )

    except Exception as e:

        backtest = {
            "错误":
                f"回测失败: {e}"
        }

    return {

        "彩种":
            name,

        "历史数量":
            len(history),

        "数据质量":
            quality,

        "预测":
            prediction,

        "回测":
            backtest
    }


# =====================================================
# 系统主流程
# =====================================================

def run_system():

    print()
    print(
        "=" * 70
    )

    print(
        "          六合 AI 智能预测系统 V3.0 FINAL"
    )

    print(
        "  API真实数据 + SQLite数据库"
    )

    print(
        "  马尔可夫链 + HMM状态识别"
    )

    print(
        "  波色 + 生肖 + 综合评分"
    )

    print(
        "  Walk-Forward 防过拟合回测"
    )

    print(
        datetime.now()
    )

    print(
        "=" * 70
    )

    # =================================================
    # 1 数据库
    # =================================================

    print()
    print(
        "【1】初始化数据库"
    )

    try:

        init_database()

    except Exception as e:

        print(
            "数据库初始化失败:",
            e
        )

        raise

    # =================================================
    # 2 API
    # =================================================

    print()
    print(
        "【2】同步在线数据"
    )

    try:

        sync_result = sync_all()

    except Exception as e:

        print(
            "API同步失败:",
            e
        )

        sync_result = {
            "status": "failed",

            "error": str(e)
        }

    # =================================================
    # 3 预测
    # =================================================

    print()
    print(
        "【3】开始智能预测"
    )

    results = {}

    for key in LOTTERIES:

        try:

            results[key] = (
                analyze_lottery(
                    key
                )
            )

        except Exception as e:

            print(
                LOTTERIES[key],
                "分析失败:",
                e
            )

            results[key] = {

                "彩种":
                    LOTTERIES[key],

                "错误":
                    str(e)
            }

    # =================================================
    # 4 总输出
    # =================================================

    final = {

        "版本":
            VERSION,

        "运行时间":
            datetime.now().isoformat(),

        "同步":
            sync_result,

        "预测":
            results
    }

    save_output(
        final
    )

    print()
    print(
        "=" * 70
    )

    print(
        "V3.0 FINAL运行完成"
    )

    print(
        "=" * 70
    )

    return final


__all__ = [
    "run_system",
    "analyze_lottery",
    "save_output"
]
