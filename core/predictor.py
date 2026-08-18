# -*- coding: utf-8 -*-
"""
六合彩 AI V3.0 - 统一预测入口
"""

from __future__ import annotations

from typing import Any, Dict, List

from .strategies import build_strategy_result


def generate_prediction(
    rows: List[Dict[str, Any]],
    lottery: str = "hk",
    performance: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """
    统一预测接口。
    返回结构与 strategies.build_strategy_result 一致，并补充元信息。
    """
    if not rows:
        return {
            "version": "V3.0",
            "lottery": lottery,
            "error": "没有历史数据",
        }

    try:
        result = build_strategy_result(rows, performance)
    except Exception as e:
        return {
            "version": "V3.0",
            "lottery": lottery,
            "error": str(e),
            "data_count": len(rows),
        }

    # 大小 / 单双最终推荐
    size_p = result["size_probabilities"]
    parity_p = result["parity_probabilities"]

    return {
        "version": "V3.0",
        "lottery": lottery,
        "data_count": len(rows),
        "market_state": result["market_state"],
        "dynamic_weights": result["weights"],
        "top10_numbers": [
            {
                "number": n,
                "score": result["number_scores"].get(n, 0.0),
                "relative_probability": result["probabilities"].get(n, 0.0),
            }
            for n in result["top10"]
        ],
        "top3_numbers": result["top3"],
        "first_number": result["first_number"],
        "top5_zodiac": [
            {"zodiac": z, "score": 0.0}  # 分数可后续补
            for z in result["top5_zodiac"]
        ],
        "top2_pingte_zodiac": [
            {"zodiac": z, "score": 0.0}
            for z in result["top2_pingte_zodiac"]
        ],
        "size": {
            "prediction": max(size_p, key=size_p.get),
            "probability": size_p,
        },
        "parity": {
            "prediction": max(parity_p, key=parity_p.get),
            "probability": parity_p,
        },
        "wave": {
            "single": result["wave_single"],
            "double": result["wave_double"],
            "probability": result["wave_probabilities"],
        },
        # 兼容旧字段
        "top10": result["top10"],
        "top3": result["top3"],
        "weights": result["weights"],
    }


def predict_lottery(
    rows: List[Dict[str, Any]],
    lottery: str = "hk",
    performance: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """兼容旧名称"""
    return generate_prediction(rows, lottery, performance)


def predict_all(
    datasets: Dict[str, List[Dict[str, Any]]],
    performances: Dict[str, Dict[str, float]] | None = None,
) -> Dict[str, Any]:
    performances = performances or {}
    output = {}
    for lottery, rows in datasets.items():
        try:
            output[lottery] = generate_prediction(
                rows, lottery, performances.get(lottery)
            )
        except Exception as e:
            output[lottery] = {
                "version": "V3.0",
                "lottery": lottery,
                "error": str(e),
            }
    return output
