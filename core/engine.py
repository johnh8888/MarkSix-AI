# -*- coding: utf-8 -*-

"""
============================================================
六合彩统计分析系统 V8.2
自适应权重 + 自适应短期窗口选择（调参/验证分离）
============================================================

相较 V8.1 的核心变化：
1. 新增"短期窗口自动选择"机制：不再固定用最近10期作为短期窗口，
   而是从 1~10 期候选窗口中，通过【调参阶段】+【样本外验证阶段】
   两段完全不重叠的数据，挑出真正在未见过数据上也跑赢随机基准的窗口；
   如果验证不通过，自动回退到默认10期窗口，不会因为过拟合而瞎选。
2. 该窗口选择只应用于"对下一期的实际推荐"（Top5/10/12），
   不应用于 walk_forward 历史回测——回测继续用固定10期窗口作为
   稳定基准，避免和历史版本失去可比性，也避免逐步回测时重复做
   窗口选择导致运行时间暴涨。
3. 保留 V8.1 的自适应分量权重机制（号码/生肖/单双/大小/波色）。
4. 保留 V8.1 修复后的正确蒙特卡洛验证逻辑。

相较 V8.0 的核心变化：
1. 所有模块的打分权重（号码/生肖/单双/大小/波色）不再是写死的常量，
   而是根据"最近 N 期，单独用该分量预测的命中率是否超过随机基准"
   动态计算出来的。
2. 权重会持久化到 data/adaptive_weights/{彩种}.json，
   每次运行时读取上次权重作为先验，与本次新算出的权重做指数平滑（EMA），
   避免权重大幅跳变。
3. 历史数据不足时，自动回退到 V8.0 的固定权重作为默认先验。
4. print_result 中新增【自适应权重】区块，显示当前各分量权重
   和它们各自的单分量命中率，方便你直接看到"系统认为哪个信号有效"。

重要声明：
本系统是【统计分析工具】，不是【预测工具】。
六合彩是独立随机事件，历史统计不能改变未来概率。
自适应权重只是让系统对"最近哪个统计特征更贴近历史开奖"更敏感，
不代表、也不可能真正提高中奖概率。
============================================================
"""

from __future__ import annotations

import json
import math
import os
import random
from datetime import datetime
from collections import Counter
from typing import Any, Callable


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
# 输出/数据目录
# ============================================================

OUTPUT_DIR = "output"
WEIGHTS_DIR = os.path.join("data", "adaptive_weights")


# ============================================================
# 波色 / 生肖
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

ANIMALS = [
    "鼠", "牛", "虎", "兔", "龙", "蛇",
    "马", "羊", "猴", "鸡", "狗", "猪",
]


# ============================================================
# 基础窗口参数（不参与自适应，仅定义"看多远"）
# ============================================================

WINDOW_10 = 10
WINDOW_30 = 30
WINDOW_100 = 100

MISSING_CAP = 40


# ============================================================
# 默认权重（仅作为"历史数据不足时"的先验，不再是最终值）
# ============================================================

DEFAULT_NUMBER_WEIGHTS: dict[str, float] = {
    "window_short": 2.50,   # 原 window10，现由自适应窗口选择决定具体看多少期
    "window30": 1.30,
    "window100": 0.80,
    "missing": 0.20,
    "trend": 0.80,
    "hot": 1.50,
    "cold": 1.00,
    "interval": 0.50,
    "tail": 0.30,
    "consecutive": 0.50,
}

# ============================================================
# 自适应短期窗口选择参数
# ============================================================

SHORT_WINDOW_CANDIDATES: list[int] = list(range(1, 11))  # 候选窗口：1~10期
SHORT_WINDOW_TUNE_PERIODS = 20     # 调参阶段样本数
SHORT_WINDOW_VALIDATE_PERIODS = 20  # 样本外验证阶段样本数
SHORT_WINDOW_MIN_TRAIN = 30        # 调参起点前至少要有多少期训练数据
DEFAULT_SHORT_WINDOW = 10          # 验证不通过时的回退窗口

DEFAULT_ZODIAC_WEIGHTS: dict[str, float] = {
    "frequency": 1.00,
    "trend": 2.00,
    "missing": 0.50,
    "cycle": 0.30,
}

DEFAULT_ODD_EVEN_WEIGHTS: dict[str, float] = {
    "frequency": 1.00,
    "trend": 0.50,
    "consecutive": 0.30,
}

DEFAULT_SIZE_WEIGHTS: dict[str, float] = {
    "frequency": 1.00,
    "trend": 0.50,
}

DEFAULT_WAVE_WEIGHTS: dict[str, float] = {
    "frequency": 1.00,
    "trend": 0.50,
}

# 自适应引擎参数
ADAPTIVE_LOOKBACK = 20      # 回看多少期来评估各分量的单独命中率
ADAPTIVE_MIN_TRAIN = 30     # 至少要有多少期训练数据才启用自适应
ADAPTIVE_SMOOTHING = 0.35   # 新权重的混合比例（EMA），越大越激进


# ============================================================
# 创建目录
# ============================================================

def ensure_dirs() -> None:
    os.makedirs("data", exist_ok=True)
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "reports"), exist_ok=True)


# ============================================================
# issue排序 / 下一期
# ============================================================

def issue_value(row: dict[str, Any]) -> int:
    try:
        return int(str(row.get("issue", "0")))
    except Exception:
        return 0


def next_issue(issue: str) -> str:
    try:
        return str(int(issue) + 1)
    except Exception:
        return ""


# ============================================================
# 波色 / 大小 / 单双 / 生肖
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


def get_size(number: int) -> str:
    number = int(number)
    return "大" if number >= 25 else "小"


def get_odd_even(number: int) -> str:
    number = int(number)
    return "单" if number % 2 else "双"


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
# 属性计数 / 概率分数
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
# 号码：原始（未加权）分量
# ============================================================

def calculate_intervals(history: list[dict[str, Any]]) -> dict[int, float]:
    intervals: dict[int, list[int]] = {}
    last_seen: dict[int, int] = {}

    for i, row in enumerate(history):
        special = get_special_number(row)
        if special is not None:
            if special in last_seen:
                interval = i - last_seen[special]
                intervals.setdefault(special, []).append(interval)
            last_seen[special] = i

    avg_intervals: dict[int, float] = {}
    for num, int_list in intervals.items():
        avg_intervals[num] = sum(int_list) / len(int_list) if int_list else 0.0

    return avg_intervals


def calculate_interval_score(interval: float) -> float:
    if interval <= 0:
        return 0.0
    theoretical = 49
    diff = abs(interval - theoretical)
    return round(max(0.0, 2.0 - diff * 0.05), 4)


def calculate_tail_frequency(
    history: list[dict[str, Any]],
    window: int = 50,
) -> Counter:
    tail_counter = Counter()
    for num in special_history(history, window):
        tail_counter[num % 10] += 1
    return tail_counter


def calculate_consecutive_counts(
    history: list[dict[str, Any]],
    window: int = 10,
) -> dict[int, int]:
    """连号邻居出现次数（原始计数，不乘权重）。"""
    recent = special_history(history, window)
    counts: dict[int, int] = {}

    for num in recent:
        for neighbor in [num - 1, num + 1]:
            if 1 <= neighbor <= 49:
                counts[neighbor] = counts.get(neighbor, 0) + 1

    return counts


def trend_raw(number: int, history: list[dict[str, Any]]) -> float:
    """趋势原始值（最近10期 vs 按30期比例折算的期望值之差）。"""
    recent10 = Counter(special_history(history, 10))
    recent30 = Counter(special_history(history, 30))
    n10 = recent10.get(number, 0)
    n30 = recent30.get(number, 0)
    if n30 <= 0:
        return float(n10) if n10 > 0 else 0.0
    expected10 = n30 / 30 * 10
    return round(n10 - expected10, 4)


def hot_flag(number: int, recent30: Counter) -> int:
    return 1 if recent30.get(number, 0) >= 3 else 0


def cold_flag(number: int, recent30: Counter, recent100: Counter) -> int:
    freq30 = recent30.get(number, 0)
    freq100 = recent100.get(number, 0)
    return 1 if (freq30 == 0 and freq100 <= 1) else 0


def compute_raw_number_components(
    history: list[dict[str, Any]],
    short_window: int = DEFAULT_SHORT_WINDOW,
) -> dict[int, dict[str, float]]:
    """
    计算 1~49 每个号码在各个分量上的原始（未加权）分数。
    这是自适应引擎和最终打分共用的核心函数。

    short_window: "短期窗口"分量看多少期，默认10期；
    可由 select_adaptive_short_window 选出的最优窗口覆盖。
    """
    recent_short = Counter(special_history(history, short_window))
    recent30 = Counter(special_history(history, WINDOW_30))
    recent100 = Counter(special_history(history, WINDOW_100))
    missing_map = missing_periods_all(history)
    interval_map = calculate_intervals(history)
    tail_counter = calculate_tail_frequency(history)
    consecutive_counts = calculate_consecutive_counts(history)

    raw: dict[int, dict[str, float]] = {}
    for number in range(1, 50):
        missing = min(missing_map.get(number, MISSING_CAP), MISSING_CAP)
        interval = interval_map.get(number, 0.0)
        tail = number % 10

        raw[number] = {
            "window_short": float(recent_short.get(number, 0)),
            "window30": float(recent30.get(number, 0)),
            "window100": float(recent100.get(number, 0)),
            "missing": float(missing),
            "trend": trend_raw(number, history),
            "hot": float(hot_flag(number, recent30)),
            "cold": float(cold_flag(number, recent30, recent100)),
            "interval": calculate_interval_score(interval),
            "tail": float(tail_counter.get(tail, 0)),
            "consecutive": float(consecutive_counts.get(number, 0)),
        }

    return raw


# ============================================================
# 自适应短期窗口选择（调参 / 样本外验证 两段分离）
# ============================================================

def _rank_by_single_window(train: list[dict[str, Any]], window: int, top_k: int) -> set[int]:
    counts = Counter(special_history(train, window))
    ranking = sorted(range(1, 50), key=lambda x: (-counts.get(x, 0), x))
    return set(ranking[:top_k])


def select_adaptive_short_window(
    history: list[dict[str, Any]],
    lottery_name: str,
    candidate_windows: list[int] | None = None,
    tune_periods: int = SHORT_WINDOW_TUNE_PERIODS,
    validate_periods: int = SHORT_WINDOW_VALIDATE_PERIODS,
    top_k: int = 10,
    min_train: int = SHORT_WINDOW_MIN_TRAIN,
    default_window: int = DEFAULT_SHORT_WINDOW,
) -> dict[str, Any]:
    """
    从候选窗口（默认1~10期）中挑选"只用该窗口内出现次数排名"预测效果最好的窗口。

    关键设计：调参和验证使用两段完全不重叠的历史数据。
    - 调参段（更早）：只用来比较候选窗口谁的命中率更高。
    - 验证段（更近、调参时完全没用过）：只用来检验调参选出的窗口
      是否真的跑赢随机基准。验证不通过就回退默认窗口，
      避免"矮子里面拔将军"式的过拟合选择被当真。
    """
    history = sorted(history, key=issue_value)
    n = len(history)
    candidates = candidate_windows if candidate_windows is not None else SHORT_WINDOW_CANDIDATES
    baseline = top_k / 49.0
    needed = min_train + tune_periods + validate_periods

    fallback = {
        "selected_window": default_window,
        "best_candidate_from_tuning": default_window,
        "tune_hit_rates": {},
        "tune_samples": 0,
        "validate_hit_rate": 0.0,
        "validate_samples": 0,
        "baseline": round(baseline, 4),
        "status": "历史数据不足，使用默认窗口",
    }

    if n <= needed:
        save_weights(lottery_name, "short_window", fallback)
        return fallback

    validate_start = n - validate_periods
    tune_start = max(min_train, validate_start - tune_periods)

    # === 调参阶段：只看 [tune_start, validate_start) 这一段 ===
    tune_hits = {w: 0 for w in candidates}
    tune_samples = 0

    for i in range(tune_start, validate_start):
        train = history[:i]
        actual = history[i]
        actual_special = get_special_number(actual)
        if actual_special is None:
            continue
        tune_samples += 1
        for w in candidates:
            top = _rank_by_single_window(train, w, top_k)
            if actual_special in top:
                tune_hits[w] += 1

    if tune_samples == 0:
        save_weights(lottery_name, "short_window", fallback)
        return fallback

    tune_rates = {w: tune_hits[w] / tune_samples for w in candidates}
    # 命中率并列时优先选更短的窗口（更贴近"短期"目标）
    best_window = max(candidates, key=lambda w: (tune_rates[w], -w))

    # === 验证阶段：只看 [validate_start, n) 这一段，调参时完全没碰过 ===
    validate_hits = 0
    validate_samples = 0

    for i in range(validate_start, n):
        train = history[:i]
        actual = history[i]
        actual_special = get_special_number(actual)
        if actual_special is None:
            continue
        validate_samples += 1
        top = _rank_by_single_window(train, best_window, top_k)
        if actual_special in top:
            validate_hits += 1

    validate_rate = validate_hits / validate_samples if validate_samples > 0 else 0.0

    if validate_samples > 0 and validate_rate > baseline:
        selected = best_window
        status = "正常（样本外验证通过）"
    else:
        selected = default_window
        status = "样本外验证未通过，回退默认窗口"

    result = {
        "selected_window": selected,
        "best_candidate_from_tuning": best_window,
        "tune_hit_rates": {str(w): round(r, 4) for w, r in tune_rates.items()},
        "tune_samples": tune_samples,
        "validate_hit_rate": round(validate_rate, 4),
        "validate_samples": validate_samples,
        "baseline": round(baseline, 4),
        "status": status,
    }
    save_weights(lottery_name, "short_window", result)
    return result


# ============================================================
# 权重持久化
# ============================================================

def _weights_path(lottery_name: str, category: str) -> str:
    safe_name = lottery_name.replace("/", "_")
    return os.path.join(WEIGHTS_DIR, f"{safe_name}_{category}.json")


def load_prev_weights(lottery_name: str, category: str) -> dict[str, float] | None:
    path = _weights_path(lottery_name, category)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        weights = data.get("weights")
        if isinstance(weights, dict):
            return {k: float(v) for k, v in weights.items()}
    except Exception:
        return None
    return None


def save_weights(lottery_name: str, category: str, payload: dict[str, Any]) -> None:
    path = _weights_path(lottery_name, category)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ============================================================
# 通用自适应权重核心
# ============================================================

def _edges_to_weights(
    hit_rates: dict[str, float],
    baseline: float,
    default_weights: dict[str, float],
) -> dict[str, float]:
    edges = {name: max(hit_rates.get(name, 0.0) - baseline, 0.0) for name in default_weights}
    edge_sum = sum(edges.values())
    default_total = sum(default_weights.values())

    if edge_sum > 1e-9:
        return {
            name: round((edges[name] / edge_sum) * default_total, 4)
            for name in default_weights
        }
    # 没有任何分量跑赢基准：回退到默认权重比例，避免权重全部归零
    return dict(default_weights)


def _smooth_weights(
    new_weights: dict[str, float],
    prev_weights: dict[str, float] | None,
    default_weights: dict[str, float],
    smoothing: float,
) -> dict[str, float]:
    base = prev_weights if prev_weights else default_weights
    return {
        name: round(
            base.get(name, default_weights[name]) * (1 - smoothing)
            + new_weights.get(name, default_weights[name]) * smoothing,
            4,
        )
        for name in default_weights
    }


# ============================================================
# 自适应权重：号码
# ============================================================

def adaptive_number_weights(
    history: list[dict[str, Any]],
    lottery_name: str,
    short_window: int = DEFAULT_SHORT_WINDOW,
    lookback_steps: int = ADAPTIVE_LOOKBACK,
    top_k: int = 10,
    min_train: int = ADAPTIVE_MIN_TRAIN,
    smoothing: float = ADAPTIVE_SMOOTHING,
) -> dict[str, Any]:
    history = sorted(history, key=issue_value)
    n = len(history)
    component_names = list(DEFAULT_NUMBER_WEIGHTS.keys())
    prev_weights = load_prev_weights(lottery_name, "numbers")

    if n <= min_train + 1:
        result = {
            "weights": dict(prev_weights) if prev_weights else dict(DEFAULT_NUMBER_WEIGHTS),
            "hit_rates": {},
            "baseline": round(top_k / 49.0, 4),
            "samples": 0,
            "status": "历史数据不足，使用默认/上次权重",
        }
        save_weights(lottery_name, "numbers", result)
        return result

    start = max(min_train, n - lookback_steps)
    hits = {name: 0 for name in component_names}
    samples = 0
    baseline = top_k / 49.0

    for i in range(start, n):
        train = history[:i]
        actual = history[i]
        actual_special = get_special_number(actual)
        if actual_special is None:
            continue
        raw = compute_raw_number_components(train, short_window=short_window)
        samples += 1
        for name in component_names:
            ranking = sorted(range(1, 50), key=lambda x: (-raw[x][name], x))
            top = set(ranking[:top_k])
            if actual_special in top:
                hits[name] += 1

    if samples == 0:
        result = {
            "weights": dict(prev_weights) if prev_weights else dict(DEFAULT_NUMBER_WEIGHTS),
            "hit_rates": {},
            "baseline": round(baseline, 4),
            "samples": 0,
            "status": "历史数据不足，使用默认/上次权重",
        }
        save_weights(lottery_name, "numbers", result)
        return result

    hit_rates = {name: hits[name] / samples for name in component_names}
    raw_weights = _edges_to_weights(hit_rates, baseline, DEFAULT_NUMBER_WEIGHTS)
    final_weights = _smooth_weights(raw_weights, prev_weights, DEFAULT_NUMBER_WEIGHTS, smoothing)

    result = {
        "weights": final_weights,
        "hit_rates": {k: round(v, 4) for k, v in hit_rates.items()},
        "baseline": round(baseline, 4),
        "samples": samples,
        "status": "正常",
    }
    save_weights(lottery_name, "numbers", result)
    return result


# ============================================================
# 号码综合评分（使用自适应权重）
# ============================================================

def predict_numbers(
    history: list[dict[str, Any]],
    lottery_name: str = "default",
    short_window: int | None = None,
) -> dict[str, Any]:
    """
    short_window:
      - None（默认）：会调用 select_adaptive_short_window 自动选窗口。
        用于"对下一期的实际推荐"（analyze() 的头部调用）。
      - 指定具体数值：跳过窗口选择，直接使用该窗口。
        用于 walk_forward 历史回测，保持固定10期窗口的基准可比性，
        同时避免每一步都重新做一次窗口选择导致运行时间暴涨。
    """
    if not history:
        return {
            "top5": [], "top10": [], "top12": [],
            "scores": {}, "details": {}, "frequency": {},
            "adaptive_weights": {}, "window_selection": {},
        }

    window_selection: dict[str, Any] = {}
    if short_window is None:
        window_selection = select_adaptive_short_window(history, lottery_name)
        effective_window = window_selection["selected_window"]
    else:
        effective_window = short_window

    weight_result = adaptive_number_weights(history, lottery_name, short_window=effective_window)
    weights = weight_result["weights"]

    raw = compute_raw_number_components(history, short_window=effective_window)

    scores: dict[int, float] = {}
    details: dict[int, dict[str, float]] = {}

    for number in range(1, 50):
        components = raw[number]
        weighted = {name: components[name] * weights.get(name, 0.0) for name in components}
        total_score = sum(weighted.values())

        scores[number] = round(total_score, 4)
        details[number] = {**{k: round(v, 4) for k, v in weighted.items()}, "total": round(total_score, 4)}

    ranking = sorted(range(1, 50), key=lambda x: (-scores[x], x))

    recent10 = Counter(special_history(history, WINDOW_10))
    recent30 = Counter(special_history(history, WINDOW_30))
    recent100 = Counter(special_history(history, WINDOW_100))

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
        "missing": missing_periods_all(history),
        "adaptive_weights": weight_result,
        "window_selection": window_selection,
        "effective_short_window": effective_window,
    }


# ============================================================
# 生肖：原始分量 + 自适应权重
# ============================================================

def calculate_zodiac_missing(history: list[dict[str, Any]]) -> dict[str, int]:
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


def calculate_zodiac_cycle(history: list[dict[str, Any]]) -> dict[str, float]:
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


def compute_raw_zodiac_components(
    history: list[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    counter = special_attribute_counter(history, "zodiac", 100)
    probability = probability_scores(counter, ANIMALS)

    recent10 = special_attribute_counter(history, "zodiac", 10)
    recent30 = special_attribute_counter(history, "zodiac", 30)

    zodiac_missing = calculate_zodiac_missing(history)
    zodiac_cycle = calculate_zodiac_cycle(history)

    raw: dict[str, dict[str, float]] = {}
    for animal in ANIMALS:
        n10 = recent10.get(animal, 0)
        n30 = recent30.get(animal, 0)
        raw[animal] = {
            "frequency": probability.get(animal, 0.0),
            "trend": (n10 - n30 / 3.0) * 2.0,
            "missing": float(min(zodiac_missing.get(animal, 0), 12)),
            "cycle": zodiac_cycle.get(animal, 0.0),
        }

    return raw


def adaptive_zodiac_weights(
    history: list[dict[str, Any]],
    lottery_name: str,
    lookback_steps: int = ADAPTIVE_LOOKBACK,
    min_train: int = ADAPTIVE_MIN_TRAIN,
    smoothing: float = ADAPTIVE_SMOOTHING,
) -> dict[str, Any]:
    history = sorted(history, key=issue_value)
    n = len(history)
    component_names = list(DEFAULT_ZODIAC_WEIGHTS.keys())
    prev_weights = load_prev_weights(lottery_name, "zodiac")
    baseline = 1.0 / 12.0

    if n <= min_train + 1:
        result = {
            "weights": dict(prev_weights) if prev_weights else dict(DEFAULT_ZODIAC_WEIGHTS),
            "hit_rates": {}, "baseline": round(baseline, 4),
            "samples": 0, "status": "历史数据不足，使用默认/上次权重",
        }
        save_weights(lottery_name, "zodiac", result)
        return result

    start = max(min_train, n - lookback_steps)
    hits = {name: 0 for name in component_names}
    samples = 0

    for i in range(start, n):
        train = history[:i]
        actual = history[i]
        actual_special = get_special_number(actual)
        if actual_special is None:
            continue
        issue = str(actual.get("issue", ""))
        actual_animal = get_zodiac(actual_special, issue)

        raw = compute_raw_zodiac_components(train)
        samples += 1
        for name in component_names:
            best_animal = max(ANIMALS, key=lambda a: raw[a][name])
            if best_animal == actual_animal:
                hits[name] += 1

    if samples == 0:
        result = {
            "weights": dict(prev_weights) if prev_weights else dict(DEFAULT_ZODIAC_WEIGHTS),
            "hit_rates": {}, "baseline": round(baseline, 4),
            "samples": 0, "status": "历史数据不足，使用默认/上次权重",
        }
        save_weights(lottery_name, "zodiac", result)
        return result

    hit_rates = {name: hits[name] / samples for name in component_names}
    raw_weights = _edges_to_weights(hit_rates, baseline, DEFAULT_ZODIAC_WEIGHTS)
    final_weights = _smooth_weights(raw_weights, prev_weights, DEFAULT_ZODIAC_WEIGHTS, smoothing)

    result = {
        "weights": final_weights,
        "hit_rates": {k: round(v, 4) for k, v in hit_rates.items()},
        "baseline": round(baseline, 4),
        "samples": samples,
        "status": "正常",
    }
    save_weights(lottery_name, "zodiac", result)
    return result


def predict_zodiac(
    history: list[dict[str, Any]],
    lottery_name: str = "default",
) -> dict[str, Any]:
    weight_result = adaptive_zodiac_weights(history, lottery_name)
    weights = weight_result["weights"]

    raw = compute_raw_zodiac_components(history)
    probability = probability_scores(special_attribute_counter(history, "zodiac", 100), ANIMALS)

    zodiac_scores: dict[str, float] = {}
    details: dict[str, dict[str, float]] = {}

    for animal in ANIMALS:
        components = raw[animal]
        weighted = {name: components[name] * weights.get(name, 0.0) for name in components}
        total = sum(weighted.values())
        zodiac_scores[animal] = round(total, 4)
        details[animal] = {**{k: round(v, 4) for k, v in weighted.items()}, "total": round(total, 4)}

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
        "adaptive_weights": weight_result,
    }


# ============================================================
# 单双 / 大小 / 波色：原始分量 + 自适应权重
# ============================================================

def calculate_consecutive_odd_even(history: list[dict[str, Any]]) -> dict[str, int]:
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


def calculate_alternation(history: list[dict[str, Any]]) -> dict[str, Any]:
    recent = special_history(history, 20)
    if len(recent) < 2:
        return {"alternating": 0, "stable": 0, "ratio": 0.0}

    alternating = 0
    stable = 0
    for i in range(1, len(recent)):
        if get_odd_even(recent[i]) != get_odd_even(recent[i - 1]):
            alternating += 1
        else:
            stable += 1

    total = alternating + stable
    return {
        "alternating": alternating,
        "stable": stable,
        "ratio": round(alternating / total * 100, 2) if total > 0 else 0.0,
    }


def _compute_raw_categorical_components(
    history: list[dict[str, Any]],
    field: str,
    categories: list[str],
) -> dict[str, dict[str, float]]:
    counter = special_attribute_counter(history, field, 100)
    probability = probability_scores(counter, categories)
    recent10 = special_attribute_counter(history, field, 10)
    baseline_share = 100.0 / len(categories)

    raw: dict[str, dict[str, float]] = {}
    for cat in categories:
        base = probability.get(cat, 0.0)
        trend = recent10.get(cat, 0) - baseline_share / 10.0 * len(categories)
        raw[cat] = {"frequency": base, "trend": float(trend)}

    if field == "odd_even":
        consecutive = calculate_consecutive_odd_even(history)
        for cat in categories:
            raw[cat]["consecutive"] = float(consecutive.get(cat, 0))

    return raw


def adaptive_categorical_weights(
    history: list[dict[str, Any]],
    lottery_name: str,
    field: str,
    categories: list[str],
    default_weights: dict[str, float],
    category_of_special: Callable[[int, str], str],
    lookback_steps: int = ADAPTIVE_LOOKBACK,
    min_train: int = ADAPTIVE_MIN_TRAIN,
    smoothing: float = ADAPTIVE_SMOOTHING,
) -> dict[str, Any]:
    history = sorted(history, key=issue_value)
    n = len(history)
    component_names = list(default_weights.keys())
    prev_weights = load_prev_weights(lottery_name, field)
    baseline = 1.0 / len(categories)

    if n <= min_train + 1:
        result = {
            "weights": dict(prev_weights) if prev_weights else dict(default_weights),
            "hit_rates": {}, "baseline": round(baseline, 4),
            "samples": 0, "status": "历史数据不足，使用默认/上次权重",
        }
        save_weights(lottery_name, field, result)
        return result

    start = max(min_train, n - lookback_steps)
    hits = {name: 0 for name in component_names}
    samples = 0

    for i in range(start, n):
        train = history[:i]
        actual = history[i]
        actual_special = get_special_number(actual)
        if actual_special is None:
            continue
        issue = str(actual.get("issue", ""))
        actual_cat = category_of_special(actual_special, issue)

        raw = _compute_raw_categorical_components(train, field, categories)
        samples += 1
        for name in component_names:
            best_cat = max(categories, key=lambda c: raw[c].get(name, 0.0))
            if best_cat == actual_cat:
                hits[name] += 1

    if samples == 0:
        result = {
            "weights": dict(prev_weights) if prev_weights else dict(default_weights),
            "hit_rates": {}, "baseline": round(baseline, 4),
            "samples": 0, "status": "历史数据不足，使用默认/上次权重",
        }
        save_weights(lottery_name, field, result)
        return result

    hit_rates = {name: hits[name] / samples for name in component_names}
    raw_weights = _edges_to_weights(hit_rates, baseline, default_weights)
    final_weights = _smooth_weights(raw_weights, prev_weights, default_weights, smoothing)

    result = {
        "weights": final_weights,
        "hit_rates": {k: round(v, 4) for k, v in hit_rates.items()},
        "baseline": round(baseline, 4),
        "samples": samples,
        "status": "正常",
    }
    save_weights(lottery_name, field, result)
    return result


def predict_single_attribute(
    history: list[dict[str, Any]],
    field: str,
    lottery_name: str = "default",
) -> dict[str, Any]:
    if field == "odd_even":
        categories = ["单", "双"]
        default_weights = DEFAULT_ODD_EVEN_WEIGHTS
        category_fn = lambda num, issue: get_odd_even(num)
    elif field == "size":
        categories = ["小", "大"]
        default_weights = DEFAULT_SIZE_WEIGHTS
        category_fn = lambda num, issue: get_size(num)
    elif field == "wave":
        categories = ["红", "蓝", "绿"]
        default_weights = DEFAULT_WAVE_WEIGHTS
        category_fn = lambda num, issue: get_wave(num)
    else:
        counter = special_attribute_counter(history, field, 100)
        probability = probability_scores(counter, list(counter.keys()))
        ranking = sorted(counter.keys(), key=lambda x: -counter[x])
        main = ranking[0] if ranking else ""
        return {
            "main": main, "secondary": "", "double": [main] if main else [],
            "probability": probability, "scores": {}, "details": {},
            "adaptive_weights": {},
        }

    weight_result = adaptive_categorical_weights(
        history, lottery_name, field, categories, default_weights, category_fn,
    )
    weights = weight_result["weights"]

    raw = _compute_raw_categorical_components(history, field, categories)
    probability = probability_scores(special_attribute_counter(history, field, 100), categories)

    scores: dict[str, float] = {}
    details: dict[str, dict[str, float]] = {}
    for cat in categories:
        components = raw[cat]
        weighted = {name: components.get(name, 0.0) * weights.get(name, 0.0) for name in weights}
        total = sum(weighted.values())
        scores[cat] = round(total, 4)
        details[cat] = {**{k: round(v, 4) for k, v in weighted.items()}, "total": round(total, 4)}

    ranking = sorted(categories, key=lambda x: -scores[x])
    main = ranking[0] if ranking else ""
    secondary = ranking[1] if len(ranking) > 1 else ""

    return {
        "main": main,
        "secondary": secondary,
        "double": ranking[:2] if field == "wave" else ([main] if main else []),
        "probability": probability,
        "scores": scores,
        "details": details,
        "adaptive_weights": weight_result,
    }


def predict_attributes(
    history: list[dict[str, Any]],
    lottery_name: str = "default",
) -> dict[str, Any]:
    zodiac = predict_zodiac(history, lottery_name)
    odd_even = predict_single_attribute(history, "odd_even", lottery_name)
    size = predict_single_attribute(history, "size", lottery_name)
    wave = predict_single_attribute(history, "wave", lottery_name)

    return {
        "zodiac": zodiac,
        "odd_even": odd_even,
        "size": size,
        "wave": wave,
    }


def predict_attribute(
    history: list[dict[str, Any]],
    field: str,
    lottery_name: str = "default",
) -> dict[str, Any]:
    if field == "zodiac":
        return predict_zodiac(history, lottery_name)
    return predict_single_attribute(history, field, lottery_name)


# ============================================================
# Walk-Forward 单期评估
# ============================================================

def evaluate_prediction(
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


def hit_rate(hits: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(hits / total * 100, 2)


def average_hits(evaluations: list[dict[str, Any]], key: str) -> float:
    if not evaluations:
        return 0.0
    hits = sum(1 for item in evaluations if item.get(key))
    return round(hits / len(evaluations), 4)


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


def _performance_window(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(evaluations)
    if total <= 0:
        return {"samples": 0, "status": "历史数据不足"}

    def count(key: str) -> int:
        return sum(1 for item in evaluations if item.get(key))

    top10_hits = count("number_top10")
    top10_rate = hit_rate(top10_hits, total)
    top10_ci = confidence_interval(top10_rate, total)
    top10_test = statistical_test(top10_hits, total, 10 / 49)

    zodiac_hits = count("zodiac_main")
    zodiac_rate = hit_rate(zodiac_hits, total)
    zodiac_test = statistical_test(zodiac_hits, total, 1 / 12)

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
        "odd_even": {"main": hit_rate(count("odd_even_main"), total)},
        "size": {"main": hit_rate(count("size_main"), total)},
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


def calculate_multi_performance(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
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


def walk_forward(
    history: list[dict[str, Any]],
    lottery_name: str = "default",
    minimum_train: int = 30,
) -> dict[str, Any]:
    """
    注意：为了让最终评估反映"当前这套自适应权重"的表现，
    这里在每一步用 train 数据重新预测时，权重同样是基于该步之前的历史
    自适应算出来的（predict_numbers / predict_attributes 内部会各自调用
    自适应权重函数）。这比 V8.0 用固定权重跑 walk-forward 更贴近真实使用场景，
    但计算量也更大，量力而行调整 minimum_train / lookback。
    """
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

        # 回测固定用默认短期窗口(10期)，不做样本外窗口选择：
        # 既保持和历史版本的可比性，也避免每一步都重新调参/验证导致运行时间暴涨。
        number_prediction = predict_numbers(train, lottery_name, short_window=DEFAULT_SHORT_WINDOW)
        attributes = predict_attributes(train, lottery_name)

        prediction = {
            "top5": number_prediction["top5"],
            "top10": number_prediction["top10"],
            "top12": number_prediction["top12"],
            "attributes": attributes,
        }

        evaluation = evaluate_prediction(prediction, actual)

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


def monte_carlo_simulation(
    performance: dict[str, Any],
    n_simulations: int = 10000,
) -> dict[str, Any]:
    """
    修复 V8.0 的逻辑错误：不再拿单次 0/1 抽样结果和一个比例值做逐点比较。
    改为：模拟 n_simulations 次"随机选10个号码，看特码是否落入其中"，
    得到一个模拟命中率的分布（每次模拟基于 samples 期，和真实回测期数对齐），
    再看真实命中率在这个分布里处于什么位置。
    """
    numbers = performance.get("numbers", {})
    samples = performance.get("samples", 0)
    actual_top10_rate = numbers.get("top10", 0) / 100.0

    if samples <= 0:
        return {
            "n_simulations": n_simulations,
            "actual_top10_rate": 0.0,
            "theoretical_rate": round(10 / 49 * 100, 2),
            "status": "历史数据不足",
        }

    simulated_rates = []
    for _ in range(n_simulations):
        hits = 0
        for _ in range(samples):
            random_pick = set(random.sample(range(1, 50), 10))
            actual = random.randint(1, 49)
            if actual in random_pick:
                hits += 1
        simulated_rates.append(hits / samples)

    simulated_rates.sort()
    percentile = sum(1 for r in simulated_rates if r <= actual_top10_rate) / n_simulations * 100
    p_value = sum(1 for r in simulated_rates if r >= actual_top10_rate) / n_simulations
    sim_mean = sum(simulated_rates) / len(simulated_rates)

    return {
        "n_simulations": n_simulations,
        "samples_per_simulation": samples,
        "actual_top10_rate": round(actual_top10_rate * 100, 2),
        "simulated_random_mean_rate": round(sim_mean * 100, 2),
        "theoretical_rate": round(10 / 49 * 100, 2),
        "percentile": round(percentile, 2),
        "p_value": round(p_value, 4),
        "interpretation": (
            f"实际命中率({actual_top10_rate*100:.2f}%)处于{samples}期随机模拟分布的"
            f"第{percentile:.1f}百分位。p值={p_value:.4f}，"
            f"{'显著优于随机（但仍需警惕多重比较）' if p_value < 0.05 else '与随机无显著差异'}"
        ),
        "status": "正常",
    }


def expected_value_analysis() -> dict[str, Any]:
    special_ev = (1 / 49) * 40 - (48 / 49) * 1
    special_ev_pct = special_ev * 100
    return {
        "special_number": {
            "cost": 1,
            "payout": 40,
            "win_probability": round(1 / 49 * 100, 4),
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

    number_prediction = predict_numbers(history, lottery_name)
    attributes = predict_attributes(history, lottery_name)
    walk = walk_forward(history, lottery_name)
    performance = walk.get("performance", {})
    multi_performance = walk.get("multi_performance", {})
    stability = calculate_model_stability(multi_performance)
    monte_carlo = monte_carlo_simulation(performance)
    expected_value = expected_value_analysis()

    return {
        "lottery": lottery_name,
        "version": "V8.2",
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
        "number_adaptive_weights": number_prediction.get("adaptive_weights", {}),
        "number_window_selection": number_prediction.get("window_selection", {}),
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
# 格式化 / 打印
# ============================================================

def format_numbers(numbers: list[int]) -> str:
    if not numbers:
        return ""
    return " ".join(f"{int(x):02d}" for x in numbers)


def _print_window_selection_block(window_selection: dict[str, Any]) -> None:
    if not window_selection:
        return
    print("【号码｜自适应短期窗口选择】")
    status = window_selection.get("status", "")
    selected = window_selection.get("selected_window", DEFAULT_SHORT_WINDOW)
    best_tune = window_selection.get("best_candidate_from_tuning", "-")
    tune_samples = window_selection.get("tune_samples", 0)
    validate_samples = window_selection.get("validate_samples", 0)
    validate_rate = window_selection.get("validate_hit_rate", 0.0)
    baseline = window_selection.get("baseline", 0.0)
    print(f"  状态：{status}")
    print(f"  调参段最优候选：{best_tune}期（样本数={tune_samples}）")
    print(f"  样本外验证命中率：{validate_rate*100:.2f}%（样本数={validate_samples}，基准={baseline*100:.2f}%）")
    print(f"  最终采用窗口：{selected}期")
    tune_rates = window_selection.get("tune_hit_rates", {})
    if tune_rates:
        rates_str = "  ".join(f"{w}期={r*100:.1f}%" for w, r in tune_rates.items())
        print(f"  调参段各候选命中率：{rates_str}")
    print()


def _print_weight_block(title: str, weight_result: dict[str, Any]) -> None:
    print(f"【{title}｜自适应权重】")
    status = weight_result.get("status", "")
    samples = weight_result.get("samples", 0)
    baseline = weight_result.get("baseline", 0)
    print(f"  样本数：{samples}　基准命中率：{baseline*100:.2f}%　状态：{status}")
    weights = weight_result.get("weights", {})
    hit_rates = weight_result.get("hit_rates", {})
    for name, w in sorted(weights.items(), key=lambda kv: -kv[1]):
        hr = hit_rates.get(name)
        hr_str = f"{hr*100:.2f}%" if hr is not None else "-"
        print(f"    {name:<12} 权重={w:<8} 单分量命中率={hr_str}")
    print()


def print_result(result: dict[str, Any]) -> None:
    print("=" * 70)
    print(f"【{result.get('lottery', '')}】 V8.2（自适应权重+自适应短期窗口）")
    print("=" * 70)
    print(f"历史期数：{result.get('history_size', 0)}")
    print(f"最新开奖期数：{result.get('latest_issue', '')}")
    print(f"下一期期数：{result.get('prediction_issue', '')}")
    print("最新号码：" + format_numbers(result.get("latest_numbers", [])))
    print()

    print("【号码预测】")
    print("Top5：" + format_numbers(result.get("top5", [])))
    print("Top10：" + format_numbers(result.get("top10", [])))
    print("Top12：" + format_numbers(result.get("top12", [])))
    print()

    attrs = result.get("attributes", {})
    print("【属性预测】")
    zodiac = attrs.get("zodiac", {})
    print(f"生肖主推：{zodiac.get('main', '')}")
    print(f"生肖Top5：{' / '.join(zodiac.get('top5', []))}")
    odd_even = attrs.get("odd_even", {})
    print(f"单双主推：{odd_even.get('main', '')}")
    size = attrs.get("size", {})
    print(f"大小主推：{size.get('main', '')}")
    wave = attrs.get("wave", {})
    print(f"波色主推：{wave.get('main', '')} / 次推：{wave.get('secondary', '')}")
    print()

    # 短期窗口选择展示
    _print_window_selection_block(result.get("number_window_selection", {}))

    # 自适应权重展示
    _print_weight_block("号码", result.get("number_adaptive_weights", {}))
    _print_weight_block("生肖", zodiac.get("adaptive_weights", {}))
    _print_weight_block("单双", odd_even.get("adaptive_weights", {}))
    _print_weight_block("大小", size.get("adaptive_weights", {}))
    _print_weight_block("波色", wave.get("adaptive_weights", {}))

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
        print(f"{'命中率':<10} {'':<8} {hits['Top5']/total*100:.1f}%{'':<3} {hits['Top10']/total*100:.1f}%{'':<3} {hits['Top12']/total*100:.1f}%{'':<3} {hits['生肖']/total*100:.1f}%{'':<3} {hits['单双']/total*100:.1f}%{'':<3} {hits['大小']/total*100:.1f}%{'':<3} {hits['波色']/total*100:.1f}%")
    else:
        print("历史数据不足")
    print()

    performance = result.get("performance", {})
    multi = result.get("multi_performance", {})

    if performance.get("status") == "正常":
        print("【短期表现（最近10期）】")
        numbers = performance.get("numbers", {})
        print(f"Top5：{numbers.get('top5', 0)}% | Top10：{numbers.get('top10', 0)}% | Top12：{numbers.get('top12', 0)}%")
        print()

    windows = multi.get("windows", {})
    if windows:
        print("【长期表现（多窗口）】")
        for window in ("10", "30", "50", "100"):
            item = windows.get(window)
            if item:
                nums = item.get("numbers", {})
                print(f"{window}期：Top10 {nums.get('top10', 0)}% (基准20.41%)")
        print()

    monte_carlo = result.get("monte_carlo", {})
    if monte_carlo.get("status") == "正常":
        print(f"【蒙特卡洛验证】p值：{monte_carlo.get('p_value', 1.0)} - {monte_carlo.get('interpretation', '')}")
        print()

    stability = result.get("model_stability", {})
    if stability:
        print(f"【模型稳定性】{stability.get('score', 0)}/100 {stability.get('level', '')}")
        print()

    print("=" * 70)
    print("⚠️ 自适应权重反映的是历史统计特征的相对强弱，不是真实预测能力")
    print("⚠️ 短期高命中率可能是统计波动，不代表系统学到了规律")
    print("⚠️ 本系统是统计分析工具，不是预测工具")
    print("⚠️ 长期投注期望值为负，必然亏损")
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
            "number_adaptive_weights": result.get("number_adaptive_weights", {}),
            "number_window_selection": result.get("number_window_selection", {}),
        }
    return summary


# ============================================================
# 主系统
# ============================================================

def run_system() -> None:
    ensure_dirs()

    print("=" * 70)
    print("六合彩统计分析系统 V8.2 - 自适应权重+自适应短期窗口")
    print("=" * 70)
    print()
    print("【系统声明】")
    print("本系统是统计分析工具，用于研究六合彩的历史统计特征。")
    print("所有模块权重会根据最近N期各分量的单独命中表现自动调整，")
    print("但六合彩是独立随机事件，历史数据不能预测未来结果。")
    print("短期高命中率可能是统计波动，不代表真实预测能力。")
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
                "version": "V8.2",
                "success": False,
                "error": str(exc),
            }

    prediction = {
        "version": "V8.2",
        "generated_at": datetime.now().isoformat(),
        "disclaimer": "本系统输出仅供统计分析参考，不构成任何投注建议。短期高命中率可能是统计波动。",
        "lotteries": all_results,
    }
    prediction_path = save_json("prediction.json", prediction)

    backtest = {
        "version": "V8.2",
        "generated_at": datetime.now().isoformat(),
        "lotteries": {
            name: result.get("backtest", {})
            for name, result in all_results.items()
        },
    }
    backtest_path = save_json("backtest.json", backtest)

    module_performance = {
        "version": "V8.2",
        "generated_at": datetime.now().isoformat(),
        "lotteries": {
            name: {
                "performance": result.get("performance", {}),
                "multi_performance": result.get("multi_performance", {}),
                "model_stability": result.get("model_stability", {}),
                "monte_carlo": result.get("monte_carlo", {}),
                "number_adaptive_weights": result.get("number_adaptive_weights", {}),
                "number_window_selection": result.get("number_window_selection", {}),
            }
            for name, result in all_results.items()
        },
    }
    performance_path = save_json("module_performance.json", module_performance)

    summary = {
        "version": "V8.2",
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
    print(f"  - 自适应权重状态文件：{WEIGHTS_DIR}/*.json")
    print("=" * 70)
    print()
    print("=" * 70)
    print("【最终声明】")
    print("1. 本系统是统计分析工具，不是预测工具")
    print("2. 六合彩是独立随机事件")
    print("3. 自适应权重反映的是历史数据的相对统计特征，不是真实规律")
    print("4. 短期高命中率可能是运气")
    print("5. 长期投注期望值为负，必然亏损")
    print("6. 请理性对待，不要将统计结果作为投注依据")
    print("=" * 70)
    print("系统运行结束")
    print("=" * 70)


if __name__ == "__main__":
    run_system()
