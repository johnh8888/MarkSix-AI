# -*- coding: utf-8 -*-

"""
六合彩综合预测系统核心引擎

V6.2 REAL DATA HISTORY FIXED
"""

from __future__ import annotations

import json

from datetime import datetime

from pathlib import Path


from .api_sync import (
    API_TYPES,
    fetch_lottery,
)

from .database import (
    get_history,
    save_records,
)

from .analyzer import (
    analyze,
)


# ============================================================
# 路径
# ============================================================

ROOT = (

    Path(__file__)
    .resolve()
    .parent
    .parent

)

OUTPUT_DIR = (
    ROOT / "output"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


VERSION = (
    "V6.2 REAL DATA HISTORY FIXED"
)


# ============================================================
# 保存 JSON
# ============================================================

def save_json(
    filename: str,
    data: dict,
) -> Path:

    path = (
        OUTPUT_DIR / filename
    )

    temp_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temp_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(

            data,

            file,

            ensure_ascii=False,

            indent=2,

        )

    temp_path.replace(path)

    return path


# ============================================================
# 检查 JSON
# ============================================================

def check_json(
    path: Path,
) -> None:

    if not path.is_file():

        raise RuntimeError(
            f"输出文件不存在：{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        json.load(file)

    print(
        f"✅ {path} "
        f"({path.stat().st_size} bytes)"
    )


# ============================================================
# 主系统
# ============================================================

def run_system() -> None:

    start_time = (
        datetime.now().isoformat()
    )


    print("=" * 70)

    print(
        "六合彩综合预测系统"
    )

    print(
        "真实数据 + SQLite + "
        "多期历史统计 + "
        "Walk-Forward + "
        "输出文件版"
    )

    print(
        f"版本：{VERSION}"
    )

    print(
        f"启动时间：{start_time}"
    )

    print("=" * 70)


    results = {}


    # ========================================================
    # 三彩种
    # ========================================================

    for lottery_name in API_TYPES:

        print("=" * 70)

        print(
            f"正在更新："
            f"{lottery_name}"
        )

        print("=" * 70)


        # ----------------------------------------------------
        # API
        # ----------------------------------------------------

        records = fetch_lottery(
            lottery_name
        )


        # ----------------------------------------------------
        # SQLite
        # ----------------------------------------------------

        inserted = save_records(

            lottery_name,

            records,

        )


        # ----------------------------------------------------
        # 从数据库重新读取
        # ----------------------------------------------------

        history = get_history(
            lottery_name
        )


        print(

            f"[{lottery_name}] "
            f"本次新增："
            f"{inserted} 期"

        )

        print(

            f"[{lottery_name}] "
            f"当前数据库历史："
            f"{len(history)} 期"

        )


        # ----------------------------------------------------
        # 分析
        # ----------------------------------------------------

        result = analyze(
            history
        )


        result["lottery"] = (
            lottery_name
        )


        results[
            lottery_name
        ] = result


        # ====================================================
        # 输出
        # ====================================================

        print("=" * 70)

        print(
            f"【{lottery_name}】"
        )

        print("=" * 70)


        print(
            f"历史期数："
            f"{result['history_size']}"
        )


        print(
            f"最新开奖期数："
            f"{result['latest_draw_issue']}"
        )


        print(
            f"预测下一期期数："
            f"{result['next_prediction_issue']}"
        )


        print(
            f"最新号码："
            f"{result['latest_numbers']}"
        )


        attrs = result[
            "attributes"
        ]


        print(
            "近期开奖属性统计："
        )


        print(
            f"波色："
            f"{attrs['colors']}"
        )


        print(
            f"大小："
            f"{attrs['sizes']}"
        )


        print(
            f"单双："
            f"{attrs['odd_even']}"
        )


        print(
            f"尾数："
            f"{attrs['tails']}"
        )


        print(
            f"分区："
            f"{attrs['zones']}"
        )


        print(
            "高频号码："
            +
            " ".join(

                f"{n:02d}"

                for n in result[
                    "hot_numbers"
                ]

            )
        )


        print(
            "低频号码："
            +
            " ".join(

                f"{n:02d}"

                for n in result[
                    "cold_numbers"
                ]

            )
        )


        print(
            "综合候选："
            +
            " ".join(

                f"{n:02d}"

                for n in result[
                    "candidates"
                ]

            )
        )


        if (
            result["history_size"]
            < 10
        ):

            print(
                "⚠ 当前历史数据少于10期，"
                "统计结果仅用于程序测试，"
                "不适合进行稳定性判断。"
            )


        print(
            "说明：以上为基于历史数据的"
            "统计分析，不代表实际开奖结果。"
        )


    # ========================================================
    # prediction.json
    # ========================================================

    prediction = {

        "version":
            VERSION,

        "generated_at":
            datetime.now().isoformat(),

        "note":
            "历史统计分析结果，"
            "不代表真实中奖概率。",

        "lotteries":
            results,

    }


    print("=" * 70)

    print(
        "保存预测结果"
    )

    print("=" * 70)


    prediction_path = save_json(

        "prediction.json",

        prediction,

    )


    print(
        f"✅ prediction.json 已保存："
        f"{prediction_path}"
    )


    # ========================================================
    # backtest.json
    # ========================================================

    backtest = {

        "version":
            VERSION,

        "generated_at":
            datetime.now().isoformat(),

        "method":
            "Walk-Forward",

        "lotteries": {

            name:
                data["backtest"]

            for name, data
            in results.items()

        },

    }


    print("=" * 70)

    print(
        "保存 Walk-Forward 回测"
    )

    print("=" * 70)


    backtest_path = save_json(

        "backtest.json",

        backtest,

    )


    print(
        f"✅ backtest.json 已保存："
        f"{backtest_path}"
    )


    # ========================================================
    # module_performance.json
    # ========================================================

    module_performance = {

        "version":
            VERSION,

        "generated_at":
            datetime.now().isoformat(),

        "lotteries": {

            name:
                data[
                    "module_performance"
                ]

            for name, data
            in results.items()

        },

    }


    print("=" * 70)

    print(
        "保存模块表现"
    )

    print("=" * 70)


    module_path = save_json(

        "module_performance.json",

        module_performance,

    )


    print(
        f"✅ module_performance.json "
        f"已保存："
        f"{module_path}"
    )


    # ========================================================
    # 文件检查
    # ========================================================

    print("=" * 70)

    print(
        "输出文件检查"
    )

    print("=" * 70)


    for path in (

        prediction_path,

        backtest_path,

        module_path,

    ):

        check_json(path)


    # ========================================================
    # 最终输出
    # ========================================================

    print("=" * 70)

    print(
        "三彩种分析完成"
    )

    print("=" * 70)


    for lottery_name, result in (
        results.items()
    ):

        print(

            f"{lottery_name}："
            f"最新开奖第 "
            f"{result['latest_draw_issue']} "
            f"期"

        )

        print(

            f"{lottery_name}："
            f"预测下一期第 "
            f"{result['next_prediction_issue']} "
            f"期"

        )

        print(

            f"{lottery_name}候选："
            +
            " ".join(

                f"{n:02d}"

                for n in result[
                    "candidates"
                ]

            )

        )


    print(
        "说明：候选号码来自历史统计评分，"
        "不代表真实中奖概率。"
    )


    print("=" * 70)

    print(
        "系统运行结束"
    )

    print("=" * 70)
