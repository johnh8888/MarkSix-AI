# -*- coding: utf-8 -*-
"""
六合彩 AI V3.0 - 多策略引擎
负责：各模块打分 → 动态权重 → 综合得分 → TopN + 属性概率
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Dict, List, Tuple

from .config import (
    ALL_NUMBERS,
    ALL_WAVES,
    ALL_SIZE,
    ALL_PARITY,
    DEFAULT_MODULE_WEIGHTS,
    SHORT_WINDOW,
    MEDIUM_WINDOW,
    LONG_WINDOW,
    NUMBER_TO_WAVE,
    NUMBER_TO_ZODIAC,
    ZODIAC_MAP_2026,
)
from .state_engine import detect_market_state
from .wave_model import wave_probabilities, number_wave_score


# =========================================================
# 工具
# =========================================================

def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def normalize_scores(scores: Dict[Any, float], default: float = 0.5) -> Dict[Any, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if abs(hi - lo) < 1e-12:
        return {k: default for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def softmax(scores: Dict[Any, float], temperature: float = 0.22) -> Dict[Any, float]:
    if not scores:
        return {}
    temperature = max(0.01, temperature)
    m = max(scores.values())
    exps = {k: math.exp((v - m) / temperature) for k, v in scores.items()}
    total = sum(exps.values()) or 1.0
    return {k: v / total for k, v in exps.items()}


def specials(rows: List[Dict[str, Any]]) -> List[int]:
    result = []
    for row in rows:
        try:
            n = int(row.get("special", 0))
            if 1 <= n <= 49:
                result.append(n)
        except Exception:
            continue
    return result


# =========================================================
# 各策略打分（全部返回 1~49 的分数）
# =========================================================

def recent_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    scores = {n: 0.0 for n in ALL_NUMBERS}
    for idx, row in enumerate(rows[:SHORT_WINDOW]):
        try:
            n = int(row["special"])
            if 1 <= n <= 49:
                decay = math.exp(-idx / max(SHORT_WINDOW, 1))
                scores[n] += decay
        except Exception:
            continue
    return normalize_scores(scores)


def medium_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    counter = Counter()
    for row in rows[:MEDIUM_WINDOW]:
        try:
            n = int(row["special"])
            if 1 <= n <= 49:
                counter[n] += 1
        except Exception:
            continue
    total = sum(counter.values()) or 1
    scores = {n: (counter.get(n, 0) + 0.5) / (total + 24.5) for n in ALL_NUMBERS}
    return normalize_scores(scores)


def long_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    counter = Counter()
    for row in rows[:LONG_WINDOW]:
        try:
            n = int(row["special"])
            if 1 <= n <= 49:
                counter[n] += 1
        except Exception:
            continue
    total = sum(counter.values()) or 1
    scores = {n: (counter.get(n, 0) + 0.5) / (total + 24.5) for n in ALL_NUMBERS}
    return normalize_scores(scores)


def omission_score(rows: List[Dict[str, Any]], cap: int = 60) -> Dict[int, float]:
    last_seen = {n: None for n in ALL_NUMBERS}
    for idx, row in enumerate(rows):
        try:
            n = int(row["special"])
            if 1 <= n <= 49 and last_seen[n] is None:
                last_seen[n] = idx
        except Exception:
            continue

    scores = {}
    for n in ALL_NUMBERS:
        miss = last_seen[n] if last_seen[n] is not None else min(len(rows), cap)
        scores[n] = min(miss, cap) / cap
    return normalize_scores(scores)


def trend_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    recent = recent_score(rows)
    medium = medium_score(rows)
    return {
        n: clamp(0.65 * recent.get(n, 0.5) + 0.35 * medium.get(n, 0.5))
        for n in ALL_NUMBERS
    }


def transition_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    """根据最近特码波色，给不同波色的号码加分"""
    scores = {n: 0.0 for n in ALL_NUMBERS}
    if not rows:
        return scores

    try:
        latest = int(rows[0]["special"])
    except Exception:
        return scores

    latest_wave = NUMBER_TO_WAVE.get(latest)
    if not latest_wave:
        return scores

    # 简单：同波色 continuity + 异波色切换
    for row in rows[1:MEDIUM_WINDOW]:
        try:
            n = int(row["special"])
            if 1 <= n <= 49:
                w = NUMBER_TO_WAVE.get(n)
                if w == latest_wave:
                    scores[n] += 0.6
                else:
                    scores[n] += 0.3
        except Exception:
            continue

    return normalize_scores(scores)


def size_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    state = detect_market_state(rows)
    prob_big = state.get("size", {}).get("prob_big", 0.5)
    return {
        n: (prob_big if n >= 25 else 1.0 - prob_big)
        for n in ALL_NUMBERS
    }


def parity_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    state = detect_market_state(rows)
    prob_odd = state.get("parity", {}).get("prob_odd", 0.5)
    return {
        n: (prob_odd if n % 2 == 1 else 1.0 - prob_odd)
        for n in ALL_NUMBERS
    }


def wave_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    probs = wave_probabilities(rows)
    return {
        n: number_wave_score(n, probs)
        for n in ALL_NUMBERS
    }


def tail_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    counter = Counter()
    for row in rows[:MEDIUM_WINDOW]:
        try:
            n = int(row["special"])
            if 1 <= n <= 49:
                counter[n % 10] += 1
        except Exception:
            continue
    total = sum(counter.values()) or 1
    return {
        n: (counter.get(n % 10, 0) + 1) / (total + 10)
        for n in ALL_NUMBERS
    }


def zone_score(rows: List[Dict[str, Any]]) -> Dict[int, float]:
    counter = Counter()
    for row in rows[:MEDIUM_WINDOW]:
        try:
            n = int(row["special"])
            if 1 <= n <= 49:
                zone = min(4, (n - 1) // 10)
                counter[zone] += 1
        except Exception:
            continue
    total = sum(counter.values()) or 1
    scores = {}
    for n in ALL_NUMBERS:
        zone = min(4, (n - 1) // 10)
        scores[n] = (counter.get(zone, 0) + 1) / (total + 5)
    return scores


# =========================================================
# 构建所有策略
# =========================================================

def build_all_scores(rows: List[Dict[str, Any]]) -> Dict[str, Dict[int, float]]:
    return {
        "recent": recent_score(rows),
        "medium": medium_score(rows),
        "long": long_score(rows),
        "omission": omission_score(rows),
        "trend": trend_score(rows),
        "transition": transition_score(rows),
        "size": size_score(rows),
        "parity": parity_score(rows),
        "wave": wave_score(rows),
        "tail": tail_score(rows),
        "zone": zone_score(rows),
    }


# =========================================================
# 动态权重
# =========================================================

def get_dynamic_weights(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    weights = dict(DEFAULT_MODULE_WEIGHTS)
    state = detect_market_state(rows)

    # 根据市场状态微调
    if state["state"] == "trend":
        weights["recent"] += 0.04
        weights["trend"] += 0.03
        weights["long"] -= 0.03
        weights["omission"] -= 0.02
    elif state["state"] == "chaos":
        weights["long"] += 0.04
        weights["omission"] += 0.03
        weights["recent"] -= 0.03
        weights["trend"] -= 0.02

    # 保证非负并归一化
    for k in weights:
        weights[k] = max(0.01, weights[k])
    total = sum(weights.values()) or 1.0
    return {k: v / total for k, v in weights.items()}


# =========================================================
# 综合得分
# =========================================================

def combine_scores(
    all_scores: Dict[str, Dict[int, float]],
    weights: Dict[str, float],
) -> Dict[int, float]:
    combined = {n: 0.0 for n in ALL_NUMBERS}
    total_w = 0.0

    for module, scores in all_scores.items():
        w = float(weights.get(module, 0.0))
        if w <= 0:
            continue
        total_w += w
        for n in ALL_NUMBERS:
            combined[n] += w * float(scores.get(n, 0.5))

    if total_w > 0:
        for n in combined:
            combined[n] /= total_w

    return combined


# =========================================================
# 生肖相关
# =========================================================

def zodiac_scores(number_scores: Dict[int, float]) -> Dict[str, float]:
    result = {z: 0.0 for z in ZODIAC_MAP_2026}
    for n, s in number_scores.items():
        z = NUMBER_TO_ZODIAC.get(n)
        if z:
            result[z] += s
    return normalize_scores(result, 0.5)


def pingte_zodiac_scores(
    rows: List[Dict[str, Any]],
    number_scores: Dict[int, float],
) -> Dict[str, float]:
    history = Counter()
    for row in rows[:MEDIUM_WINDOW]:
        try:
            n = int(row["special"])
            z = NUMBER_TO_ZODIAC.get(n)
            if z:
                history[z] += 1
        except Exception:
            continue

    total = max(1, sum(history.values()))
    raw = {}
    for z, nums in ZODIAC_MAP_2026.items():
        avg_num = sum(number_scores.get(n, 0.5) for n in nums) / len(nums)
        freq = history.get(z, 0) / total
        # 平特略偏冷
        raw[z] = 0.72 * avg_num + 0.18 * freq + 0.10 * (1.0 - freq)
    return normalize_scores(raw, 0.5)


# =========================================================
# 属性概率（大小 / 单双）
# =========================================================

def attr_probabilities(
    rows: List[Dict[str, Any]],
    attr: str,
    window: int = MEDIUM_WINDOW,
) -> Dict[str, float]:
    numbers = specials(rows[:window])
    if not numbers:
        if attr == "size":
            return {"大": 0.5, "小": 0.5}
        return {"单": 0.5, "双": 0.5}

    if attr == "size":
        big = sum(1 for n in numbers if n >= 25)
        p_big = (big + 1) / (len(numbers) + 2)
        return {"大": p_big, "小": 1 - p_big}
    else:
        odd = sum(1 for n in numbers if n % 2 == 1)
        p_odd = (odd + 1) / (len(numbers) + 2)
        return {"单": p_odd, "双": 1 - p_odd}


# =========================================================
# 最终策略结果（供 predictor 使用）
# =========================================================

def build_strategy_result(
    rows: List[Dict[str, Any]],
    performance: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """
    返回统一结构：
    - top10 / top3
    - probabilities（相对概率）
    - size_probabilities / parity_probabilities
    - wave_single / wave_double / wave_probabilities
    - weights
    - number_scores
    """
    if len(rows) < 20:
        raise ValueError(f"历史数据不足：{len(rows)} 期，至少需要 20 期")

    all_scores = build_all_scores(rows)
    weights = get_dynamic_weights(rows)
    number_scores = combine_scores(all_scores, weights)

    # 排序
    ranking = sorted(number_scores.items(), key=lambda x: (-x[1], x[0]))
    top10 = [n for n, _ in ranking[:10]]
    top3 = [n for n, _ in ranking[:3]]

    # 相对概率（softmax，仅作解释用）
    rank_prob = softmax({n: s for n, s in ranking}, temperature=0.22)

    # 大小 / 单双
    size_p = attr_probabilities(rows, "size")
    parity_p = attr_probabilities(rows, "parity")

    # 波色
    wave_p = wave_probabilities(rows)
    wave_ranked = sorted(wave_p.items(), key=lambda x: x[1], reverse=True)
    wave_single = wave_ranked[0][0]
    wave_double = [w for w, _ in wave_ranked[:2]]

    # 生肖
    z_scores = zodiac_scores(number_scores)
    pz_scores = pingte_zodiac_scores(rows, number_scores)

    top5_zodiac = [
        z for z, _ in sorted(z_scores.items(), key=lambda x: (-x[1], x[0]))[:5]
    ]
    top2_pingte = [
        z for z, _ in sorted(pz_scores.items(), key=lambda x: (-x[1], x[0]))[:2]
    ]

    return {
        "top10": top10,
        "top3": top3,
        "first_number": top3[0],
        "probabilities": {n: round(rank_prob.get(n, 0.0), 6) for n in top10},
        "number_scores": {n: round(s, 6) for n, s in ranking},
        "size_probabilities": {k: round(v, 6) for k, v in size_p.items()},
        "parity_probabilities": {k: round(v, 6) for k, v in parity_p.items()},
        "wave_single": wave_single,
        "wave_double": wave_double,
        "wave_probabilities": {k: round(v, 6) for k, v in wave_p.items()},
        "top5_zodiac": top5_zodiac,
        "top2_pingte_zodiac": top2_pingte,
        "weights": {k: round(v, 6) for k, v in weights.items()},
        "market_state": detect_market_state(rows),
    }
