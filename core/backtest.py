# -*- coding: utf-8 -*-
"""
六合彩 AI V3.0 - Walk-Forward 回测
只使用预测时点之前的数据，输出最近 10 / 20 期命中率
"""

from __future__ import annotations

from typing import Any, Dict, List

from .config import NUMBER_TO_ZODIAC, NUMBER_TO_WAVE
from .predictor import generate_prediction


def _get_zodiac(n: int) -> str:
    return NUMBER_TO_ZODIAC.get(n, "未知")


def _get_wave(n: int) -> str:
    return NUMBER_TO_WAVE.get(n, "未知")


def _get_size(n: int) -> str:
    return "大" if n >= 25 else "小"


def _get_parity(n: int) -> str:
    return "单" if n % 2 else "双"


def empty_metric() -> Dict[str, Any]:
    return {"total": 0, "hit": 0, "rate": 0.0}


def add_hit(metric: Dict[str, Any], ok: bool) -> None:
    metric["total"] += 1
    if ok:
        metric["hit"] += 1
    metric["rate"] = metric["hit"] / metric["total"] if metric["total"] else 0.0


def test_one(train_rows: List[Dict[str, Any]], actual_row: Dict[str, Any]) -> Dict[str, bool] | None:
    try:
        actual = int(actual_row["special"])
        if not (1 <= actual <= 49):
            return None
    except Exception:
        return None

    try:
        pred = generate_prediction(train_rows)
        if pred.get("error"):
            return None
    except Exception:
        return None

    # Top10
    top10 = {item["number"] for item in pred.get("top10_numbers", [])}
    number_hit = actual in top10

    # 生肖 Top5
    actual_zodiac = _get_zodiac(actual)
    top5_z = {item["zodiac"] for item in pred.get("top5_zodiac", [])}
    zodiac_hit = actual_zodiac in top5_z

    # 平特 Top2
    top2_p = {item["zodiac"] for item in pred.get("top2_pingte_zodiac", [])}
    pingte_hit = actual_zodiac in top2_p

    # 大小
    size_hit = _get_size(actual) == pred.get("size", {}).get("prediction")

    # 单双
    parity_hit = _get_parity(actual) == pred.get("parity", {}).get("prediction")

    # 波色
    actual_wave = _get_wave(actual)
    wave_single = pred.get("wave", {}).get("single")
    wave_double = pred.get("wave", {}).get("double", [])
    wave_single_hit = actual_wave == wave_single
    wave_double_hit = actual_wave in wave_double

    return {
        "number_hit": number_hit,
        "zodiac_hit": zodiac_hit,
        "pingte_hit": pingte_hit,
        "size_hit": size_hit,
        "parity_hit": parity_hit,
        "wave_single_hit": wave_single_hit,
        "wave_double_hit": wave_double_hit,
    }


def walk_forward(rows: List[Dict[str, Any]], window: int = 20) -> Dict[str, Any]:
    """
    rows: 最新 → 最旧
    只测试最近 window 期，每期只用更旧的数据做预测
    """
    result = {
        "test_size": window,
        "valid_tests": 0,
        "number10": empty_metric(),
        "zodiac5": empty_metric(),
        "pingte2": empty_metric(),
        "size": empty_metric(),
        "parity": empty_metric(),
        "wave_single": empty_metric(),
        "wave_double": empty_metric(),
    }

    if len(rows) < 30:
        result["error"] = "历史样本不足"
        return result

    # 最多测试 window 期，且保证训练集至少 20 期
    test_count = min(window, len(rows) - 20)
    start = len(rows) - test_count   # 从较旧的位置开始往新走

    for i in range(start, len(rows)):
        train_rows = rows[i + 1:] if i + 1 < len(rows) else []
        # 注意：rows 是 新→旧，所以 train 应该是比当前更旧的部分
        # 修正：train 使用 rows[i+1 :] （更旧）
        train_rows = rows[i + 1 :]
        if len(train_rows) < 20:
            continue

        actual_row = rows[i]
        one = test_one(train_rows, actual_row)
        if one is None:
            continue

        result["valid_tests"] += 1
        add_hit(result["number10"], one["number_hit"])
        add_hit(result["zodiac5"], one["zodiac_hit"])
        add_hit(result["pingte2"], one["pingte_hit"])
        add_hit(result["size"], one["size_hit"])
        add_hit(result["parity"], one["parity_hit"])
        add_hit(result["wave_single"], one["wave_single_hit"])
        add_hit(result["wave_double"], one["wave_double_hit"])

    if result["valid_tests"] == 0:
        result["error"] = "没有有效测试"

    return result


def multi_window_backtest(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = {}
    for window in (10, 20):
        results[str(window)] = walk_forward(rows, window)
    return results
