# -*- coding: utf-8 -*-

"""
六合彩 AI V3.5
core/backtest.py

统一 Walk-Forward 回测

支持：
10期
20期
30期

所有模型统一验证。
"""

from typing import Any, Callable, Dict, List


WINDOWS = [10, 20, 30]


def safe_numbers(draw):
    """兼容不同历史数据格式。"""

    if isinstance(draw, dict):

        numbers = (
            draw.get("numbers")
            or draw.get("openCode")
            or draw.get("opencode")
        )

        if isinstance(numbers, str):
            return [
                int(x)
                for x in numbers.replace("，", ",").split(",")
                if x.strip().isdigit()
            ]

        if isinstance(numbers, list):
            return [
                int(x)
                for x in numbers
                if str(x).isdigit()
            ]

    if isinstance(draw, (list, tuple)):
        return [
            int(x)
            for x in draw
            if str(x).isdigit()
        ]

    return []


def hit_number(prediction, actual):
    """
    号码命中：
    预测集合与实际7个号码存在交集即算命中。
    """

    if not prediction:
        return False

    predicted = set(prediction)
    actual_numbers = set(actual)

    return bool(predicted & actual_numbers)


def hit_exact(prediction, actual):
    """
    精确属性命中。
    """

    if prediction is None:
        return False

    return prediction == actual


def calc_rate(hit, total):
    if total <= 0:
        return 0.0

    return round(hit / total * 100, 1)


def validate_window(
    history: List[Any],
    predictor: Callable,
    window: int,
    mode: str = "number",
) -> Dict[str, Any]:
    """
    Walk-Forward 验证。

    predictor(history_before)：
        使用当前开奖之前的数据预测下一期。
    """

    if len(history) < window + 1:

        return {
            "窗口": window,
            "样本数": 0,
            "命中": 0,
            "命中率": 0.0,
            "状态": "数据不足",
        }

    start = len(history) - window

    hit = 0
    total = 0

    details = []

    for index in range(start, len(history)):

        train = history[:index]
        actual_draw = history[index]

        actual = safe_numbers(actual_draw)

        if not actual:
            continue

        try:
            prediction = predictor(train)
        except Exception:
            prediction = None

        if prediction is None:
            continue

        # ----------------------------------------------------
        # 普通号码模式
        # ----------------------------------------------------

        if mode == "number":

            ok = hit_number(
                prediction,
                actual,
            )

        # ----------------------------------------------------
        # 精确属性模式
        # ----------------------------------------------------

        else:

            ok = hit_exact(
                prediction,
                actual,
            )

        if ok:
            hit += 1

        total += 1

        details.append({
            "期数": (
                actual_draw.get("issue")
                if isinstance(actual_draw, dict)
                else index
            ),
            "预测": prediction,
            "实际": actual,
            "命中": ok,
        })

    return {
        "窗口": window,
        "样本数": total,
        "命中": hit,
        "命中率": calc_rate(hit, total),
        "状态": "OK" if total else "无有效数据",
        "明细": details,
    }


def validate_all(
    history: List[Any],
    predictor: Callable,
    mode: str = "number",
) -> Dict[str, Any]:
    """
    同时验证10/20/30期。
    """

    result = {}

    for window in WINDOWS:

        result[str(window)] = validate_window(
            history=history,
            predictor=predictor,
            window=window,
            mode=mode,
        )

    return result


def model_score(result):
    """
    根据10/20/30期结果计算稳定性评分。

    不是简单取最高一次，而是综合三个窗口。
    """

    rates = []

    for window in WINDOWS:

        data = result.get(str(window), {})

        if data.get("状态") != "OK":
            continue

        rates.append(
            float(data.get("命中率", 0))
        )

    if not rates:
        return 0.0

    return round(
        sum(rates) / len(rates),
        1,
    )


def best_window(result):
    """
    找出最佳验证窗口。
    """

    best = None
    best_rate = -1

    for window in WINDOWS:

        data = result.get(str(window), {})

        rate = float(
            data.get("命中率", 0)
        )

        if rate > best_rate:

            best_rate = rate
            best = window

    return best


def summarize_result(result):
    """
    简洁结果。
    """

    return {
        "10期": {
            "命中": result["10"]["命中"],
            "总数": result["10"]["样本数"],
            "命中率": result["10"]["命中率"],
        },

        "20期": {
            "命中": result["20"]["命中"],
            "总数": result["20"]["样本数"],
            "命中率": result["20"]["命中率"],
        },

        "30期": {
            "命中": result["30"]["命中"],
            "总数": result["30"]["样本数"],
            "命中率": result["30"]["命中率"],
        },

        "稳定性评分": model_score(result),
        "最佳窗口": best_window(result),
    }
