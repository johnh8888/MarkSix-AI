# -*- coding: utf-8 -*-
"""
六合彩 AI 智能预测系统 V3.0
入口：同步 → 状态识别 → 动态权重 → 预测 → Walk-Forward
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from .config import (
    BASE_DIR,
    OUTPUT_DIR,
    DB_FILES,
    LOTTERY_NAMES,
)
from .database import connect_db, init_db, load_rows, get_row_count
from .data_source import sync_all
from .predictor import generate_prediction
from .backtest import walk_forward


def fmt_num(n: int) -> str:
    return f"{int(n):02d}"


def print_prediction(key: str, prediction: dict) -> None:
    print("=" * 70)
    print(f"{LOTTERY_NAMES[key]} ({key})")
    print("=" * 70)

    if prediction.get("error"):
        print("❌", prediction["error"])
        return

    top10 = prediction.get("top10_numbers", [])
    print("【特码10码】")
    print(" ".join(fmt_num(x["number"]) for x in top10))

    print("【49码综合评分 Top10】")
    for i, item in enumerate(top10, 1):
        print(
            f"第{i:02d}名 {item['number']:02d} "
            f"评分：{item['score']:.4f} "
            f"相对概率：{item['relative_probability'] * 100:.2f}%"
        )

    print("【下一期重点推荐】")
    print(" ".join(fmt_num(n) for n in prediction.get("top3_numbers", [])))
    print(f"第一推荐：{fmt_num(prediction.get('first_number', 0))}")

    print("【特码生肖5肖】")
    print(" ".join(x["zodiac"] for x in prediction.get("top5_zodiac", [])))

    print("【平特生肖2肖】")
    print(" ".join(x["zodiac"] for x in prediction.get("top2_pingte_zodiac", [])))

    size = prediction.get("size", {})
    print("【大小】", size.get("prediction"), size.get("probability"))

    parity = prediction.get("parity", {})
    print("【单双】", parity.get("prediction"), parity.get("probability"))

    wave = prediction.get("wave", {})
    print("【波色单推】", wave.get("single"))
    print("【波色双推】", " + ".join(wave.get("double", [])))
    print("【波色概率】", wave.get("probability"))

    state = prediction.get("market_state", {})
    print("【V3.0当前市场状态】", state.get("state"), f"(置信度 {state.get('confidence', 0):.2f})")

    print("【V3.0动态模块权重】")
    for k, v in prediction.get("dynamic_weights", {}).items():
        print(f"  {k:<12} {v:.4f}")


def print_backtest(key: str, bt: dict, title: str) -> None:
    print("=" * 70)
    print(f"{LOTTERY_NAMES[key]} {title}")
    print("=" * 70)

    if bt.get("error"):
        print("错误：", bt["error"])
        return

    print(f"有效测试期数：{bt['valid_tests']}")

    labels = [
        ("number10", "特码10码命中率"),
        ("zodiac5", "生肖5肖命中率"),
        ("pingte2", "平特2肖命中率"),
        ("size", "大小命中率"),
        ("parity", "单双命中率"),
        ("wave_single", "波色单推命中率"),
        ("wave_double", "波色双推命中率"),
    ]
    for k, label in labels:
        m = bt[k]
        print(f"{label}：{m['rate'] * 100:.2f}%  ({m['hit']}/{m['total']})")

    single = bt["wave_single"]["rate"]
    double = bt["wave_double"]["rate"]
    print(f"波色双推提升：{(double - single) * 100:+.2f}%")


def main() -> None:
    print("=" * 70)
    print("六合彩AI智能预测系统 V3.0")
    print("工作流：同步 → 状态识别 → 动态权重 → 预测 → Walk-Forward")
    print(datetime.now().isoformat())
    print("=" * 70)

    # 1. 初始化数据库
    print("【步骤1】初始化数据库")
    for key, path in DB_FILES.items():
        conn = connect_db(path)
        init_db(conn)
        conn.close()
    print("✅ 数据库初始化完成")

    # 2. 同步数据
    print("=" * 70)
    print("【步骤2】同步在线数据")
    print("=" * 70)
    try:
        history_stats = sync_all()
    except Exception as exc:
        print("⚠️ 同步过程出现异常：", exc)
        history_stats = {}

    for key in DB_FILES:
        conn = connect_db(DB_FILES[key])
        count = get_row_count(conn)
        conn.close()
        print(f"{LOTTERY_NAMES[key]}: {count} 期")

    # 3. 三彩种预测 + 回测
    all_predictions = {}
    all_backtests = {}

    for key, path in DB_FILES.items():
        print("#" * 70)
        print(f"开始分析：{LOTTERY_NAMES[key]}")
        print("#" * 70)

        conn = connect_db(path)
        rows = load_rows(conn)
        conn.close()

        print(f"历史数据：{len(rows)} 期")
        print("-" * 70)
        print("【步骤3】生成下一期预测")

        prediction = generate_prediction(rows, lottery=key)
        print_prediction(key, prediction)

        if not prediction.get("error"):
            all_predictions[key] = prediction

        # 4. Walk-Forward
        print("-" * 70)
        print("【步骤4】Walk-Forward 历史回测")

        bt10 = walk_forward(rows, 10)
        bt20 = walk_forward(rows, 20)

        all_backtests[key] = {
            "recent10": bt10,
            "recent20": bt20,
        }

        print("\n【最近10期】")
        print_backtest(key, bt10, "最近10期回测")
        print("\n【最近20期】")
        print_backtest(key, bt20, "最近20期回测")

    # 5. 保存结果
    print("-" * 70)
    print("【步骤5】保存预测结果")

    prediction_path = OUTPUT_DIR / "prediction.json"
    prediction_payload = {
        "version": "V3.0",
        "generated_at": datetime.now().isoformat(),
        "note": (
            "模型评分用于排序；relative_probability 为模型内部相对分布，"
            "不代表真实中奖概率。"
        ),
        "lotteries": all_predictions,
    }
    prediction_path.write_text(
        json.dumps(prediction_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("✅ 预测结果已保存 →", prediction_path)

    print("-" * 70)
    print("【步骤6】保存回测结果")

    backtest_path = OUTPUT_DIR / "backtest.json"
    backtest_payload = {
        "version": "V3.0",
        "generated_at": datetime.now().isoformat(),
        "windows": [10, 20],
        "note": (
            "采用 Walk-Forward，每个目标期的预测只使用目标期之前的数据，"
            "避免未来数据泄漏。"
        ),
        "lotteries": all_backtests,
    }
    backtest_path.write_text(
        json.dumps(backtest_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("✅ 回测结果已保存 →", backtest_path)

    print("=" * 70)
    print("本次运行完成")
    print(f"分析彩种：{len(all_predictions)}")
    print(f"预测文件：{prediction_path}")
    print(f"回测文件：{backtest_path}")
    print("=" * 70)
    print("系统运行结束")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(130)
    except Exception as exc:
        print("\n❌ 系统异常：", exc)
        raise
