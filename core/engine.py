# -*- coding: utf-8 -*-

"""
============================================================
六合彩统计分析系统 V7.9
ENHANCED INDEPENDENT MODULES
============================================================

每个独立模块增强：
1. 号码预测：+间隔分析+尾数分析+连号分析
2. 生肖预测：+趋势+遗漏+周期分析
3. 单双预测：+连续趋势+交替模式
4. 大小预测：+区间分布+边界分析
5. 波色预测：+连续波色+转换矩阵

重要声明：
本系统是【统计分析工具】，不是【预测工具】。
六合彩是独立随机事件，历史统计不能改变未来概率。
============================================================
"""

from __future__ import annotations

import json
import math
import os
import random
from datetime import datetime
from collections import Counter
from typing import Any


# ============================================================
# 项目模块
# ============================================================

from .api_sync import (
    fetch_lottery,
)

from .database import (
    init_db,
    save_records,
    load_records,
    count_records,
)


# ============================================================
# 彩种
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
# 波色
# ============================================================

RED = {
    1, 2, 7, 8, 12, 13, 18, 19, 23, 24,
    29, 30, 34, 35, 40, 45, 46
}

BLUE = {
    3, 4, 9, 10, 14, 15, 20, 25, 26, 31,
    36, 37, 41, 42, 47, 48
}

GREEN = {
    5, 6, 11, 16, 17, 21, 22, 27, 28, 32,
    33, 38, 39, 43, 44, 49
}


# ============================================================
# 生肖
# ============================================================

ANIMALS = [
    "鼠", "牛", "虎", "兔", "龙", "蛇",
    "马", "羊", "猴", "鸡", "狗", "猪",
]


# ============================================================
# 参数
# ============================================================

WINDOW_10 = 10
WINDOW_30 = 30
WINDOW_100 = 100

MISSING_CAP = 40

WEIGHT_10 = 2.50
WEIGHT_30 = 1.30
WEIGHT_100 = 0.80
WEIGHT_MISSING = 0.20
WEIGHT_TREND = 0.80
WEIGHT_HOT = 1.50
WEIGHT_COLD = 1.00

# 新增权重
WEIGHT_INTERVAL = 0.50
WEIGHT_TAIL = 0.30
WEIGHT_CONSECUTIVE = 0.50


# ============================================================
# 创建目录
# ============================================================

def ensure_dirs() -> None:
    os.makedirs("data", exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "reports"), exist_ok=True)


# ============================================================
# issue排序
# ============================================================

def issue_value(row: dict[str, Any]) -> int:
    try:
        return int(str(row.get("issue", "0")))
    except Exception:
        return 0


# ============================================================
# 下一期
# ============================================================

def next_issue(issue: str) -> str:
    try:
        return str(int(issue) + 1)
    except Exception:
        return ""


# ============================================================
# 波色
# ============================================================

def get_wave(number: int) -> str:
    number = int(number)
    if number in RED:
        return "红"
    if number in BLUE:
        return "蓝"
    if number in GREEN:
        return "绿"
    return ""


# ============================================================
# 大小
# ============================================================

def get_size(number: int) -> str:
    number = int(number)
    return "大" if number >= 25 else "小"


# ============================================================
# 单双
# ============================================================

def get_odd_even(number: int) -> str:
    number = int(number)
    return "单" if number % 2 else "双"


# ============================================================
# 生肖
# ============================================================

def zodiac_by_year(number: int, year: int) -> str:
    number = int(number)
    year = int(year)
    base_index = 4
    year_index = (base_index + (year - 2024)) % 12
    return ANIMALS[(year_index - (number - 1)) % 12]


def get_zodiac(number: int, issue: str) -> str:
    try:
        year = int(str(issue)[:4])
    except Exception:
        year = 2026
    return zodiac_by_year(number, year)


# ============================================================
# 特别号码
# ============================================================

def get_special_number(record: dict[str, Any]) -> int | None:
    numbers = record.get("numbers", [])
    if not isinstance(numbers, (list, tuple)):
        return None
    if len(numbers) != 7:
        return None
    try:
        number = int(numbers[6])
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
    window: int | None = None,
) -> list[int]:
    rows = history[-window:] if window else history
    result = []
    for row in rows:
        special = get_special_number(row)
        if special is not None:
            result.append(special)
    return result


# ============================================================
# 遗漏统计
# ============================================================

def missing_periods_all(
    history: list[dict[str, Any]],
) -> dict[int, int]:
    result: dict[int, int] = {}
    found: set[int] = set()
    count = 0
    for row in reversed(history):
        if len(found) >= 49:
            break
        special = get_special_number(row)
        if special is not None and special not in found:
            result[special] = count
            found.add(special)
        count += 1
    for number in range(1, 50):
        if number not in result:
            result[number] = min(count, MISSING_CAP)
    return result


# ============================================================
# 属性计数
# ============================================================

def special_attribute_counter(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 100,
) -> Counter:
    counter = Counter()
    if not history:
        return counter
    for row in history[-limit:]:
        special = get_special_number(row)
        if special is None:
            continue
        issue = str(row.get("issue", ""))
        if field == "wave":
            value = get_wave(special)
        elif field == "size":
            value = get_size(special)
        elif field == "odd_even":
            value = get_odd_even(special)
        elif field == "zodiac":
            value = get_zodiac(special, issue)
        else:
            continue
        if value:
            counter[value] += 1
    return counter


# ============================================================
# 概率分数
# ============================================================

def probability_scores(
    counter: Counter,
    categories: list[str] | None = None,
) -> dict[str, float]:
    if categories is None:
        categories = list(counter.keys())
    total = sum(counter.get(item, 0) for item in categories)
    if total <= 0:
        if not categories:
            return {}
        equal = round(100 / len(categories), 2)
        result = {item: equal for item in categories}
        diff = round(100 - sum(result.values()), 2)
        result[categories[0]] = round(result[categories[0]] + diff, 2)
        return result
    return {
        item: round(counter.get(item, 0) / total * 100, 2)
        for item in categories
    }


# ============================================================
# 趋势评分
# ============================================================

def trend_score(
    number: int,
    history: list[dict[str, Any]],
) -> float:
    recent10 = Counter(special_history(history, 10))
    recent30 = Counter(special_history(history, 30))
    n10 = recent10.get(number, 0)
    n30 = recent30.get(number, 0)
    if n30 <= 0:
        if n10 > 0:
            return round(n10 * WEIGHT_TREND, 4)
        return 0.0
    expected10 = n30 / 30 * 10
    trend = n10 - expected10
    return round(trend * WEIGHT_TREND, 4)


# ============================================================
# 冷热号加成
# ============================================================

def hot_cold_bonus(
    number: int,
    recent30: Counter,
    recent100: Counter,
) -> float:
    freq30 = recent30.get(number, 0)
    freq100 = recent100.get(number, 0)
    if freq30 >= 3:
        return WEIGHT_HOT
    if freq30 == 0 and freq100 <= 1:
        return WEIGHT_COLD
    return 0.0


# ============================================================
# 动态权重
# ============================================================

def get_dynamic_weights(
    history_size: int,
) -> tuple[float, float, float]:
    if history_size > 500:
        return (3.00, 1.50, 0.80)
    if history_size > 300:
        return (2.50, 1.30, 0.80)
    return (2.00, 1.00, 0.50)


# ============================================================
# 间隔分析
# ============================================================

def calculate_intervals(history: list[dict[str, Any]]) -> dict[int, float]:
    """计算每个号码的平均出现间隔"""
    intervals: dict[int, list[int]] = {}
    last_seen: dict[int, int] = {}
    
    for i, row in enumerate(history):
        special = get_special_number(row)
        if special is not None:
            if special in last_seen:
                interval = i - last_seen[special]
                if special not in intervals:
                    intervals[special] = []
                intervals[special].append(interval)
            last_seen[special] = i
    
    avg_intervals: dict[int, float] = {}
    for num, int_list in intervals.items():
        avg_intervals[num] = sum(int_list) / len(int_list) if int_list else 0.0
    
    return avg_intervals


def calculate_interval_score(interval: float) -> float:
    """间隔评分：接近理论间隔（49期）的号码加分"""
    if interval <= 0:
        return 0.0
    theoretical = 49
    diff = abs(interval - theoretical)
    return round(max(0.0, 2.0 - diff * 0.05), 4)


# ============================================================
# 尾数分析
# ============================================================

def calculate_tail_frequency(
    history: list[dict[str, Any]],
    window: int = 50,
) -> Counter:
    """尾数频率统计"""
    tail_counter = Counter()
    for num in special_history(history, window):
        tail_counter[num % 10] += 1
    return tail_counter


# ============================================================
# 连号分析
# ============================================================

def calculate_consecutive_bonus(
    history: list[dict[str, Any]],
    window: int = 10,
) -> dict[int, float]:
    """连号分析：最近出现过的号码附近号码加分"""
    recent = special_history(history, window)
    bonus: dict[int, float] = {}
    
    for num in recent:
        for neighbor in [num - 1, num + 1]:
            if 1 <= neighbor <= 49:
                bonus[neighbor] = bonus.get(neighbor, 0.0) + WEIGHT_CONSECUTIVE
    
    return bonus


# ============================================================
# 号码综合评分（增强版）
# ============================================================

def predict_numbers(
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    if not history:
        return {
            "top5": [], "top10": [], "top12": [],
            "scores": {}, "details": {}, "frequency": {},
        }
    
    w10, w30, w100 = get_dynamic_weights(len(history))
    
    recent10 = Counter(special_history(history, WINDOW_10))
    recent30 = Counter(special_history(history, WINDOW_30))
    recent100 = Counter(special_history(history, WINDOW_100))
    missing_map = missing_periods_all(history)
    
    # 新增分析
    interval_map = calculate_intervals(history)
    tail_counter = calculate_tail_frequency(history)
    consecutive_bonus = calculate_consecutive_bonus(history)
    
    scores: dict[int, float] = {}
    details: dict[int, dict[str, float]] = {}
    
    for number in range(1, 50):
        score10 = recent10.get(number, 0) * w10
        score30 = recent30.get(number, 0) * w30
        score100 = recent100.get(number, 0) * w100
        
        missing = min(missing_map.get(number, MISSING_CAP), MISSING_CAP)
        missing_score = missing * WEIGHT_MISSING
        
        trend = trend_score(number, history)
        hot_cold = hot_cold_bonus(number, recent30, recent100)
        
        # 新增分数
        interval = interval_map.get(number, 0.0)
        interval_score = calculate_interval_score(interval) * WEIGHT_INTERVAL
        
        tail = number % 10
        tail_freq = tail_counter.get(tail, 0)
        tail_score = tail_freq * WEIGHT_TAIL
        
        consec = consecutive_bonus.get(number, 0.0)
        
        total_score = (
            score10 + score30 + score100 +
            missing_score + trend + hot_cold +
            interval_score + tail_score + consec
        )
        
        scores[number] = round(total_score, 4)
        details[number] = {
            "window10": round(score10, 4),
            "window30": round(score30, 4),
            "window100": round(score100, 4),
            "missing": round(missing_score, 4),
            "trend": round(trend, 4),
            "hot_cold": round(hot_cold, 4),
            "interval": round(interval_score, 4),
            "tail": round(tail_score, 4),
            "consecutive": round(consec, 4),
            "total": round(total_score, 4),
        }
    
    ranking = sorted(range(1, 50), key=lambda x: (-scores[x], x))
    
    return {
        "top5": ranking[:5],
        "top10": ranking[:10],
        "top12": ranking[:12],
        "scores": scores,
        "details": details,
        "frequency": dict(recent100),
        "windows": {
            "10": dict(recent10),
            "30": dict(recent30),
            "100": dict(recent100),
        },
        "missing": missing_map,
        "intervals": interval_map,
        "tail_frequency": dict(tail_counter),
        "weights_used": {
            "w10": w10, "w30": w30, "w100": w100,
            "missing": WEIGHT_MISSING, "trend": WEIGHT_TREND,
            "hot": WEIGHT_HOT, "cold": WEIGHT_COLD,
            "interval": WEIGHT_INTERVAL, "tail": WEIGHT_TAIL,
            "consecutive": WEIGHT_CONSECUTIVE,
        },
    }


# ============================================================
# 生肖遗漏
# ============================================================

def calculate_zodiac_missing(
    history: list[dict[str, Any]],
) -> dict[str, int]:
    missing = {animal: 0 for animal in ANIMALS}
    found: set[str] = set()
    count = 0
    
    for row in reversed(history):
        special = get_special_number(row)
        if special is None:
            continue
        issue = str(row.get("issue", ""))
        animal = get_zodiac(special, issue)
        
        if animal not in found:
            missing[animal] = count
            found.add(animal)
        
        count += 1
        if len(found) >= 12:
            break
    
    return missing


def calculate_zodiac_cycle(
    history: list[dict[str, Any]],
) -> dict[str, float]:
    """生肖周期分析：12期前出现的生肖"""
    cycle = {animal: 0.0 for animal in ANIMALS}
    
    if len(history) < 12:
        return cycle
    
    target_row = history[-12]
    target_special = get_special_number(target_row)
    
    if target_special is not None:
        issue = str(target_row.get("issue", ""))
        target_animal = get_zodiac(target_special, issue)
        cycle[target_animal] = 1.0
    
    return cycle


# ============================================================
# 生肖预测（增强版）
# ============================================================

def predict_zodiac(
    history: list[dict[str, Any]],
    limit: int = 100,
) -> dict[str, Any]:
    counter = special_attribute_counter(history, "zodiac", limit)
    probability = probability_scores(counter, ANIMALS)
    
    recent10 = special_attribute_counter(history, "zodiac", 10)
    recent30 = special_attribute_counter(history, "zodiac", 30)
    
    zodiac_missing = calculate_zodiac_missing(history)
    zodiac_cycle = calculate_zodiac_cycle(history)
    
    zodiac_scores: dict[str, float] = {}
    details: dict[str, dict[str, float]] = {}
    
    for animal in ANIMALS:
        base = probability.get(animal, 0)
        
        n10 = recent10.get(animal, 0)
        n30 = recent30.get(animal, 0)
        trend = (n10 - n30 / 3.0) * 2.0
        
        missing = zodiac_missing.get(animal, 0)
        missing_score = min(missing, 12) * 0.5
        
        cycle = zodiac_cycle.get(animal, 0.0)
        cycle_score = cycle * 0.3
        
        total = base + trend + missing_score + cycle_score
        zodiac_scores[animal] = round(total, 4)
        
        details[animal] = {
            "frequency": round(base, 4),
            "trend": round(trend, 4),
            "missing": missing,
            "cycle": round(cycle_score, 4),
            "total": round(total, 4),
        }
    
    ranking = sorted(ANIMALS, key=lambda x: -zodiac_scores[x])
    top5 = ranking[:5]
    
    return {
        "main": top5[0] if top5 else "",
        "secondary": top5[1] if len(top5) > 1 else "",
        "top5": top5,
        "double": top5,
        "probability": probability,
        "scores": zodiac_scores,
        "details": details,
    }


# ============================================================
# 单双连续趋势
# ============================================================

def calculate_consecutive_odd_even(
    history: list[dict[str, Any]],
) -> dict[str, int]:
    result = {"单": 0, "双": 0}
    
    for row in reversed(history):
        special = get_special_number(row)
        if special is None:
            continue
        oe = get_odd_even(special)
        result[oe] += 1
        if result[oe] >= 3:
            break
    
    return result


def calculate_alternation(
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    recent = special_history(history, 20)
    if len(recent) < 2:
        return {"alternating": 0, "stable": 0, "ratio": 0.0}
    
    alternating = 0
    stable = 0
    
    for i in range(1, len(recent)):
        if get_odd_even(recent[i]) != get_odd_even(recent[i-1]):
            alternating += 1
        else:
            stable += 1
    
    total = alternating + stable
    return {
        "alternating": alternating,
        "stable": stable,
        "ratio": round(alternating / total * 100, 2) if total > 0 else 0.0,
    }


# ============================================================
# 单属性预测（增强版）
# ============================================================

def predict_single_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 100,
) -> dict[str, Any]:
    counter = special_attribute_counter(history, field, limit)
    
    if field == "odd_even":
        categories = ["单", "双"]
        probability = probability_scores(counter, categories)
        
        consecutive = calculate_consecutive_odd_even(history)
        alternation = calculate_alternation(history)
        recent10 = special_attribute_counter(history, field, 10)
        
        scores = {}
        for cat in categories:
            base = probability.get(cat, 0)
            trend = recent10.get(cat, 0) - 50
            consec = consecutive.get(cat, 0)
            scores[cat] = round(base + trend * 0.5 + consec * 0.3, 4)
        
        main = max(scores, key=scores.get) if scores else ""
        
        return {
            "main": main,
            "secondary": "双" if main == "单" else "单",
            "double": [main] if main else [],
            "probability": probability,
            "scores": scores,
            "details": {
                "consecutive": consecutive,
                "alternation": alternation,
            },
        }
    
    elif field == "size":
        categories = ["小", "大"]
        probability = probability_scores(counter, categories)
        recent10 = special_attribute_counter(history, field, 10)
        
        scores = {}
        for cat in categories:
            base = probability.get(cat, 0)
            trend = recent10.get(cat, 0) - 50
            scores[cat] = round(base + trend * 0.5, 4)
        
        main = max(scores, key=scores.get) if scores else ""
        
        return {
            "main": main,
            "secondary": "大" if main == "小" else "小",
            "double": [main] if main else [],
            "probability": probability,
            "scores": scores,
            "details": {},
        }
    
    elif field == "wave":
        categories = ["红", "蓝", "绿"]
        probability = probability_scores(counter, categories)
        recent10 = special_attribute_counter(history, field, 10)
        
        scores = {}
        for cat in categories:
            base = probability.get(cat, 0)
            trend = recent10.get(cat, 0) - 100/3
            scores[cat] = round(base + trend * 0.5, 4)
        
        ranking = sorted(categories, key=lambda x: -scores[x])
        main = ranking[0] if ranking else ""
        secondary = ranking[1] if len(ranking) > 1 else ""
        
        return {
            "main": main,
            "secondary": secondary,
            "double": ranking[:2],
            "probability": probability,
            "scores": scores,
            "details": {},
        }
    
    else:
        probability = probability_scores(counter, list(counter.keys()))
        ranking = sorted(counter.keys(), key=lambda x: -counter[x])
        main = ranking[0] if ranking else ""
        
        return {
            "main": main,
            "secondary": "",
            "double": [main] if main else [],
            "probability": probability,
            "scores": {},
            "details": {},
        }


# ============================================================
# 统一属性预测
# ============================================================

def predict_attributes(
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    zodiac = predict_zodiac(history)
    odd_even = predict_single_attribute(history, "odd_even")
    size = predict_single_attribute(history, "size")
    wave = predict_single_attribute(history, "wave")
    
    return {
        "zodiac": {
            "main": zodiac["main"],
            "secondary": zodiac["secondary"],
            "top5": zodiac["top5"],
            "double": zodiac["top5"],
            "probability": zodiac["probability"],
            "scores": zodiac.get("scores", {}),
            "details": zodiac.get("details", {}),
        },
        "odd_even": {
            "main": odd_even["main"],
            "secondary": odd_even["secondary"],
            "double": odd_even["double"],
            "probability": odd_even["probability"],
            "scores": odd_even.get("scores", {}),
            "details": odd_even.get("details", {}),
        },
        "size": {
            "main": size["main"],
            "secondary": size["secondary"],
            "double": size["double"],
            "probability": size["probability"],
            "scores": size.get("scores", {}),
            "details": size.get("details", {}),
        },
        "wave": {
            "main": wave["main"],
            "secondary": wave["secondary"],
            "double": wave["double"],
            "probability": wave["probability"],
            "scores": wave.get("scores", {}),
            "details": wave.get("details", {}),
        },
    }


def predict_attribute(
    history: list[dict[str, Any]],
    field: str,
    limit: int = 100,
) -> dict[str, Any]:
    if field == "zodiac":
        return predict_zodiac(history, limit)
    return predict_single_attribute(history, field, limit)


# ============================================================
# Walk-Forward 单期评估
# ============================================================

def _evaluate_prediction_core(
    prediction: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    actual_special = get_special_number(actual)
    if actual_special is None:
        return {}
    
    issue = str(actual.get("issue", ""))
    result: dict[str, Any] = {}
    
    top5 = prediction.get("top5", [])
    top10 = prediction.get("top10", [])
    top12 = prediction.get("top12", [])
    
    result["number_top5"] = actual_special in set(top5)
    result["number_top10"] = actual_special in set(top10)
    result["number_top12"] = actual_special in set(top12)
    
    actual_zodiac = get_zodiac(actual_special, issue)
    actual_wave = get_wave(actual_special)
    actual_size = get_size(actual_special)
    actual_odd_even = get_odd_even(actual_special)
    
    attrs = prediction.get("attributes", {})
    
    zodiac = attrs.get("zodiac", {})
    result["zodiac_main"] = actual_zodiac == zodiac.get("main", "")
    result["zodiac_top5"] = actual_zodiac in set(zodiac.get("top5", []))
    
    odd_even = attrs.get("odd_even", {})
    result["odd_even_main"] = actual_odd_even == odd_even.get("main", "")
    
    size = attrs.get("size", {})
    result["size_main"] = actual_size == size.get("main", "")
    
    wave = attrs.get("wave", {})
    result["wave_main"] = actual_wave == wave.get("main", "")
    result["wave_secondary"] = actual_wave == wave.get("secondary", "")
    result["wave_double"] = actual_wave in set(wave.get("double", [])[:2])
    
    return result


def evaluate_prediction(
    prediction: dict[str, Any],
    actual: dict[str, Any],
    train: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return _evaluate_prediction_core(prediction, actual)


# ============================================================
# 命中率
# ============================================================

def hit_rate(hits: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(hits / total * 100, 2)


def average_hits(evaluations: list[dict[str, Any]], key: str) -> float:
    if not evaluations:
        return 0.0
    hits = sum(1 for item in evaluations if item.get(key))
    return round(hits / len(evaluations), 4)


# ============================================================
# 置信区间
# ============================================================

def confidence_interval(
    hit_rate_pct: float,
    samples: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    if samples <= 0:
        return (0.0, 0.0)
    p = hit_rate_pct / 100.0
    z = 1.96 if confidence == 0.95 else 1.645
    margin = z * math.sqrt(p * (1 - p) / samples)
    lower = max(0.0, (p - margin) * 100)
    upper = min(100.0, (p + margin) * 100)
    return (round(lower, 2), round(upper, 2))


# ============================================================
# 统计显著性检验
# ============================================================

def statistical_test(
    actual_hits: int,
    samples: int,
    expected_rate: float,
) -> dict[str, Any]:
    if samples <= 0:
        return {"z_score": 0, "p_value": 1.0, "significant": False}
    p_hat = actual_hits / samples
    p0 = expected_rate
    if p0 <= 0 or p0 >= 1:
        return {"z_score": 0, "p_value": 1.0, "significant": False}
    se = math.sqrt(p0 * (1 - p0) / samples)
    if se <= 0:
        return {"z_score": 0, "p_value": 1.0, "significant": False}
    z = (p_hat - p0) / se
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return {
        "z_score": round(z, 4),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "interpretation": (
            "统计显著（p<0.05），但需注意多重比较问题"
            if p_value < 0.05
            else "统计不显著（p≥0.05），与随机基准无显著差异"
        ),
    }


# ============================================================
# 性能计算
# ============================================================

def _performance_window(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(evaluations)
    if total <= 0:
        return {"samples": 0, "status": "历史数据不足"}
    
    def count(key: str) -> int:
        return sum(1 for item in evaluations if item.get(key))
    
    top10_hits = count("number_top10")
    top10_rate = hit_rate(top10_hits, total)
    top10_ci = confidence_interval(top10_rate, total)
    top10_test = statistical_test(top10_hits, total, 10/49)
    
    zodiac_hits = count("zodiac_main")
    zodiac_rate = hit_rate(zodiac_hits, total)
    zodiac_test = statistical_test(zodiac_hits, total, 1/12)
    
    return {
        "samples": total,
        "numbers": {
            "top5": hit_rate(count("number_top5"), total),
            "top10": top10_rate,
            "top10_ci_lower": top10_ci[0],
            "top10_ci_upper": top10_ci[1],
            "top10_statistical_test": top10_test,
            "top12": hit_rate(count("number_top12"), total),
            "average_top5_hits": average_hits(evaluations, "number_top5"),
            "average_top10_hits": average_hits(evaluations, "number_top10"),
            "average_top12_hits": average_hits(evaluations, "number_top12"),
        },
        "zodiac": {
            "main": zodiac_rate,
            "main_statistical_test": zodiac_test,
            "top5": hit_rate(count("zodiac_top5"), total),
        },
        "odd_even": {
            "main": hit_rate(count("odd_even_main"), total),
        },
        "size": {
            "main": hit_rate(count("size_main"), total),
        },
        "wave": {
            "main": hit_rate(count("wave_main"), total),
            "secondary": hit_rate(count("wave_secondary"), total),
            "double": hit_rate(count("wave_double"), total),
        },
        "status": "正常",
    }


def calculate_performance(
    evaluations: list[dict[str, Any]],
    recent_n: int = 10,
) -> dict[str, Any]:
    if not evaluations:
        return {"samples": 0, "backtest_window": recent_n, "status": "历史数据不足"}
    evaluations = evaluations[-recent_n:]
    result = _performance_window(evaluations)
    result["backtest_window"] = recent_n
    return result


def calculate_multi_performance(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    if not evaluations:
        return {"status": "历史数据不足", "windows": {}}
    result = {}
    for window in (10, 30, 50, 100):
        subset = evaluations[-window:]
        data = _performance_window(subset)
        data["backtest_window"] = min(window, len(evaluations))
        result[str(window)] = data
    return {
        "status": "正常",
        "total_samples": len(evaluations),
        "windows": result,
    }


# ============================================================
# Walk-Forward
# ============================================================

def walk_forward(
    history: list[dict[str, Any]],
    minimum_train: int = 30,
) -> dict[str, Any]:
    history = sorted(history, key=issue_value)
    evaluations = []
    detailed_evaluations = []
    
    if len(history) <= minimum_train:
        return {
            "method": "Walk-Forward",
            "minimum_train": minimum_train,
            "samples": 0,
            "status": "历史数据不足",
            "performance": {"samples": 0, "status": "历史数据不足"},
            "multi_performance": {"status": "历史数据不足", "windows": {}},
            "evaluations": [],
        }
    
    for index in range(minimum_train, len(history)):
        train = history[:index]
        actual = history[index]
        
        number_prediction = predict_numbers(train)
        attributes = predict_attributes(train)
        
        prediction = {
            "top5": number_prediction["top5"],
            "top10": number_prediction["top10"],
            "top12": number_prediction["top12"],
            "attributes": attributes,
        }
        
        evaluation = evaluate_prediction(prediction, actual, train)
        
        if evaluation:
            evaluations.append(evaluation)
            detailed_evaluations.append({
                "issue": str(actual.get("issue", "")),
                "actual_special": get_special_number(actual),
                "number_top5": evaluation.get("number_top5", False),
                "number_top10": evaluation.get("number_top10", False),
                "number_top12": evaluation.get("number_top12", False),
                "zodiac_main": evaluation.get("zodiac_main", False),
                "zodiac_top5": evaluation.get("zodiac_top5", False),
                "odd_even_main": evaluation.get("odd_even_main", False),
                "size_main": evaluation.get("size_main", False),
                "wave_main": evaluation.get("wave_main", False),
                "wave_secondary": evaluation.get("wave_secondary", False),
                "wave_double": evaluation.get("wave_double", False),
            })
    
    performance = calculate_performance(evaluations, 10)
    multi_performance = calculate_multi_performance(evaluations)
    
    return {
        "method": "Walk-Forward",
        "minimum_train": minimum_train,
        "samples": len(evaluations),
        "performance": performance,
        "multi_performance": multi_performance,
        "evaluations": detailed_evaluations,
        "status": "正常",
    }


# ============================================================
# 模型稳定性
# ============================================================

def calculate_model_stability(multi_performance: dict[str, Any]) -> dict[str, Any]:
    windows = multi_performance.get("windows", {})
    if not windows:
        return {"score": 0, "level": "数据不足"}
    values = []
    for window_data in windows.values():
        numbers = window_data.get("numbers", {})
        values.append(float(numbers.get("top10", 0)))
    if not values:
        return {"score": 0, "level": "数据不足"}
    mean_value = sum(values) / len(values)
    spread = max(values) - min(values) if len(values) > 1 else 0
    stability = max(0.0, 100.0 - spread * 2.0)
    return {
        "mean_top10": round(mean_value, 2),
        "spread": round(spread, 2),
        "score": round(stability, 2),
        "level": (
            "稳定" if stability >= 75
            else "一般" if stability >= 50
            else "波动较大"
        ),
    }


# ============================================================
# 蒙特卡洛模拟
# ============================================================

def monte_carlo_simulation(
    history: list[dict[str, Any]],
    n_simulations: int = 10000,
) -> dict[str, Any]:
    walk = walk_forward(history)
    performance = walk.get("performance", {})
    numbers = performance.get("numbers", {})
    actual_top10_rate = numbers.get("top10", 0) / 100.0
    
    random_hits = []
    for _ in range(n_simulations):
        random_pick = set(random.sample(range(1, 50), 10))
        actual = random.randint(1, 49)
        random_hits.append(actual in random_pick)
    
    sim_hit_rate = sum(random_hits) / n_simulations
    percentile = sum(1 for h in random_hits if h <= actual_top10_rate) / n_simulations * 100
    p_value = sum(1 for h in random_hits if h >= actual_top10_rate) / n_simulations
    
    return {
        "n_simulations": n_simulations,
        "actual_top10_rate": round(actual_top10_rate * 100, 2),
        "simulated_random_rate": round(sim_hit_rate * 100, 2),
        "theoretical_rate": round(10/49 * 100, 2),
        "percentile": round(percentile, 2),
        "p_value": round(p_value, 4),
        "interpretation": (
            f"实际命中率({actual_top10_rate*100:.2f}%)处于随机模拟的"
            f"第{percentile:.1f}百分位。p值={p_value:.4f}，"
            f"{'显著优于随机' if p_value < 0.05 else '与随机无显著差异'}"
        ),
    }


# ============================================================
# 期望值分析
# ============================================================

def expected_value_analysis() -> dict[str, Any]:
    special_ev = (1/49) * 40 - (48/49) * 1
    special_ev_pct = special_ev * 100
    return {
        "special_number": {
            "cost": 1,
            "payout": 40,
            "win_probability": round(1/49*100, 4),
            "expected_value": round(special_ev, 4),
            "expected_value_pct": round(special_ev_pct, 2),
            "interpretation": f"长期每投注1元，期望损失约{abs(round(special_ev_pct, 2))}%",
        },
        "disclaimer": "以上期望值基于假设赔率，实际赔率以彩票公司公布为准。六合彩期望值始终为负，长期投注必然亏损。",
    }


# ============================================================
# 分析一个彩种
# ============================================================

def analyze(
    lottery_name: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    history = sorted(history, key=issue_value)
    latest = history[-1] if history else {}
    latest_issue = str(latest.get("issue", ""))
    latest_numbers = latest.get("numbers", [])
    prediction_issue = next_issue(latest_issue) if latest_issue else ""
    
    number_prediction = predict_numbers(history)
    attributes = predict_attributes(history)
    walk = walk_forward(history)
    performance = walk.get("performance", {})
    multi_performance = walk.get("multi_performance", {})
    stability = calculate_model_stability(multi_performance)
    monte_carlo = monte_carlo_simulation(history)
    expected_value = expected_value_analysis()
    
    return {
        "lottery": lottery_name,
        "version": "V7.9",
        "latest_issue": latest_issue,
        "latest_draw_issue": latest_issue,
        "prediction_issue": prediction_issue,
        "next_prediction_issue": prediction_issue,
        "latest_numbers": latest_numbers,
        "history_size": len(history),
        "top5": number_prediction["top5"],
        "top10": number_prediction["top10"],
        "top12": number_prediction["top12"],
        "number_scores": number_prediction["scores"],
        "number_details": number_prediction["details"],
        "frequency": number_prediction["frequency"],
        "windows": number_prediction["windows"],
        "missing": number_prediction["missing"],
        "intervals": number_prediction.get("intervals", {}),
        "tail_frequency": number_prediction.get("tail_frequency", {}),
        "weights_used": number_prediction.get("weights_used", {}),
        "attributes": attributes,
        "pingte_zodiac": {
            "recommend": attributes.get("zodiac", {}).get("main", ""),
            "hit_rate": performance.get("zodiac", {}).get("main", 0),
            "samples": performance.get("samples", 0),
        },
        "performance": performance,
        "multi_performance": multi_performance,
        "model_stability": stability,
        "monte_carlo": monte_carlo,
        "expected_value": expected_value,
        "backtest": walk,
        "success": bool(history),
    }


# ============================================================
# 格式化号码
# ============================================================

def format_numbers(numbers: list[int]) -> str:
    if not numbers:
        return ""
    return " ".join(f"{int(x):02d}" for x in numbers)


# ============================================================
# 打印结果
# ============================================================

def print_result(result: dict[str, Any]) -> None:
    print("=" * 70)
    print(f"【{result.get('lottery', '')}】")
    print("=" * 70)
    print(f"历史期数：{result.get('history_size', 0)}")
    print(f"最新开奖期数：{result.get('latest_issue', '')}")
    print(f"下一期期数：{result.get('prediction_issue', '')}")
    print("最新号码：" + format_numbers(result.get("latest_numbers", [])))
    print()
    
    # 号码排名
    print("【号码统计分析（增强版）】")
    print("Top5：" + format_numbers(result.get("top5", [])))
    print("Top10：" + format_numbers(result.get("top10", [])))
    print("Top12：" + format_numbers(result.get("top12", [])))
    print()
    
    # 属性统计
    attrs = result.get("attributes", {})
    print("【属性统计（增强版）】")
    
    zodiac = attrs.get("zodiac", {})
    print(f"生肖：{zodiac.get('main', '')} (综合评分最高)")
    print(f"生肖Top5：{' / '.join(zodiac.get('top5', []))}")
    
    odd_even = attrs.get("odd_even", {})
    print(f"单双：{odd_even.get('main', '')}")
    
    size = attrs.get("size", {})
    print(f"大小：{size.get('main', '')}")
    
    wave = attrs.get("wave", {})
    print(f"波色：{wave.get('main', '')} / 次推 {wave.get('secondary', '')}")
    print()
    
    # 最近10期对错
    print("【最近10期预测对错情况】")
    print("-" * 70)
    
    backtest = result.get("backtest", {})
    evaluations = backtest.get("evaluations", [])
    
    if evaluations:
        recent_evals = evaluations[-10:]
        print(f"{'期数':<10} {'特别号':<8} {'Top5':<6} {'Top10':<6} {'Top12':<6} {'生肖':<6} {'单双':<6} {'大小':<6} {'波色':<6}")
        print("-" * 70)
        
        for eval_item in recent_evals:
            issue = eval_item.get("issue", "")
            actual = eval_item.get("actual_special", "")
            top5 = "✓" if eval_item.get("number_top5") else "✗"
            top10 = "✓" if eval_item.get("number_top10") else "✗"
            top12 = "✓" if eval_item.get("number_top12") else "✗"
            zodiac_hit = "✓" if eval_item.get("zodiac_main") else "✗"
            odd_even_hit = "✓" if eval_item.get("odd_even_main") else "✗"
            size_hit = "✓" if eval_item.get("size_main") else "✗"
            wave_hit = "✓" if eval_item.get("wave_main") else "✗"
            print(f"{issue:<10} {actual:<8} {top5:<6} {top10:<6} {top12:<6} {zodiac_hit:<6} {odd_even_hit:<6} {size_hit:<6} {wave_hit:<6}")
        
        print("-" * 70)
        total = len(recent_evals)
        hits = {
            "Top5": sum(1 for e in recent_evals if e.get("number_top5")),
            "Top10": sum(1 for e in recent_evals if e.get("number_top10")),
            "Top12": sum(1 for e in recent_evals if e.get("number_top12")),
            "生肖": sum(1 for e in recent_evals if e.get("zodiac_main")),
            "单双": sum(1 for e in recent_evals if e.get("odd_even_main")),
            "大小": sum(1 for e in recent_evals if e.get("size_main")),
            "波色": sum(1 for e in recent_evals if e.get("wave_main")),
        }
        print(f"{'命中':<10} {'':<8} {hits['Top5']}/{total:<5} {hits['Top10']}/{total:<5} {hits['Top12']}/{total:<5} {hits['生肖']}/{total:<5} {hits['单双']}/{total:<5} {hits['大小']}/{total:<5} {hits['波色']}/{total}")
        print(f"{'命中率':<10} {'':<8} {hits['Top5']/total*100:.1f}%{'':<3} {hits['Top10']/total*100:.1f}%{'':<3} {hits['Top12']/total*100:.1f}%{'':<3} {hits['生肖']/total*100:.1f}%{'':<3} {hits['单双']/total*100:.1f}%{'':<3} {hits['大小']/total*100:.1f}%{'':<3} {hits['波色']/total*100:.1f}%")
    else:
        print("历史数据不足")
    print()
    
    # Walk-Forward
    performance = result.get("performance", {})
    if performance.get("status") == "正常":
        print("【Walk-Forward验证】")
        print(f"验证期数：{performance.get('samples', 0)}")
        numbers = performance.get("numbers", {})
        print(f"Top5：{numbers.get('top5', 0)}% （随机基准10.20%）")
        print(f"Top10：{numbers.get('top10', 0)}% （随机基准20.41%）")
        print(f"Top12：{numbers.get('top12', 0)}% （随机基准24.49%）")
        top10_test = numbers.get("top10_statistical_test", {})
        if top10_test:
            print(f"统计检验：{top10_test.get('interpretation', '')}")
        print()
    
    # 蒙特卡洛
    monte_carlo = result.get("monte_carlo", {})
    if monte_carlo:
        print("【蒙特卡洛模拟】")
        print(f"p值：{monte_carlo.get('p_value', 1.0)}")
        print(f"结论：{monte_carlo.get('interpretation', '')}")
        print()
    
    # 期望值
    ev = result.get("expected_value", {})
    if ev:
        print(f"【期望值】{ev.get('special_number', {}).get('expected_value_pct', 0)}%")
        print()
    
    # 稳定性
    stability = result.get("model_stability", {})
    if stability:
        print(f"【稳定性】{stability.get('score', 0)}/100 {stability.get('level', '')}")
        print()
    
    # 声明
    print("=" * 70)
    print("【重要声明】本系统是统计分析工具，不是预测工具。")
    print("六合彩是独立随机事件，历史统计不能预测未来。")
    print("长期投注期望值为负，必然亏损。")
    print("=" * 70)
    print()


# ============================================================
# 保存JSON
# ============================================================

def save_json(filename: str, data: dict[str, Any]) -> str:
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


# ============================================================
# 生成简版
# ============================================================

def build_summary(all_results: dict[str, Any]) -> dict[str, Any]:
    summary = {}
    for name, result in all_results.items():
        if not result.get("success"):
            summary[name] = {"success": False, "error": result.get("error", "")}
            continue
        attrs = result.get("attributes", {})
        summary[name] = {
            "success": True,
            "latest_issue": result.get("latest_issue", ""),
            "prediction_issue": result.get("prediction_issue", ""),
            "top5": result.get("top5", []),
            "top10": result.get("top10", []),
            "top12": result.get("top12", []),
            "zodiac": attrs.get("zodiac", {}),
            "odd_even": attrs.get("odd_even", {}),
            "size": attrs.get("size", {}),
            "wave": attrs.get("wave", {}),
            "pingte_zodiac": result.get("pingte_zodiac", {}),
            "model_stability": result.get("model_stability", {}),
            "monte_carlo": result.get("monte_carlo", {}),
        }
    return summary


# ============================================================
# 主系统
# ============================================================

def run_system() -> None:
    ensure_dirs()
    
    print("=" * 70)
    print("六合彩统计分析系统 V7.9 - 增强独立模块版")
    print("=" * 70)
    print()
    print("【系统声明】")
    print("本系统是统计分析工具，用于研究六合彩的历史统计特征。")
    print("六合彩是独立随机事件，历史数据不能预测未来结果。")
    print("=" * 70)
    print()
    
    try:
        init_db()
        print("[OK] SQLite 初始化完成")
    except Exception as exc:
        print(f"[ERROR] SQLite 初始化失败：{exc}")
        raise
    
    all_results: dict[str, Any] = {}
    
    for lottery in LOTTERIES:
        print()
        print("=" * 70)
        print(f"正在分析：{lottery}")
        print("=" * 70)
        
        try:
            records = fetch_lottery(lottery)
            if records is None:
                records = []
            print(f"[{lottery}] API返回：{len(records)} 期")
            
            added = save_records(lottery, records)
            print(f"[{lottery}] 本次新增：{added} 期")
            
            history = load_records(lottery)
            total = count_records(lottery)
            print(f"[{lottery}] 当前数据库：{total} 期")
            
            result = analyze(lottery, history)
            print_result(result)
            all_results[lottery] = result
            
        except Exception as exc:
            print(f"[ERROR] {lottery}: {exc}")
            all_results[lottery] = {
                "lottery": lottery,
                "version": "V7.9",
                "success": False,
                "error": str(exc),
            }
    
    # 保存输出
    prediction = {
        "version": "V7.9",
        "generated_at": datetime.now().isoformat(),
        "disclaimer": "本系统输出仅供统计分析参考，不构成任何投注建议。",
        "lotteries": all_results,
    }
    prediction_path = save_json("prediction.json", prediction)
    
    backtest = {
        "version": "V7.9",
        "generated_at": datetime.now().isoformat(),
        "lotteries": {
            name: result.get("backtest", {})
            for name, result in all_results.items()
        },
    }
    backtest_path = save_json("backtest.json", backtest)
    
    module_performance = {
        "version": "V7.9",
        "generated_at": datetime.now().isoformat(),
        "lotteries": {
            name: {
                "performance": result.get("performance", {}),
                "multi_performance": result.get("multi_performance", {}),
                "model_stability": result.get("model_stability", {}),
                "monte_carlo": result.get("monte_carlo", {}),
            }
            for name, result in all_results.items()
        },
    }
    performance_path = save_json("module_performance.json", module_performance)
    
    summary = {
        "version": "V7.9",
        "generated_at": datetime.now().isoformat(),
        "summary": build_summary(all_results),
    }
    summary_path = save_json("summary.json", summary)
    
    print()
    print("=" * 70)
    print("分析结果已保存：")
    print(f"  - {prediction_path}")
    print(f"  - {backtest_path}")
    print(f"  - {performance_path}")
    print(f"  - {summary_path}")
    print("=" * 70)
    print()
    print("=" * 70)
    print("【最终声明】")
    print("1. 本系统是统计分析工具，不是预测工具")
    print("2. 六合彩是独立随机事件")
    print("3. 历史统计不能改变未来概率")
    print("4. 长期投注期望值为负，必然亏损")
    print("5. 请理性对待，不要将统计结果作为投注依据")
    print("=" * 70)
    print("系统运行结束")
    print("=" * 70)


if __name__ == "__main__":
    run_system()