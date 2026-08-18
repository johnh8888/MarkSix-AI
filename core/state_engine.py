# -*- coding: utf-8 -*-
"""
六合彩 AI V3.0 - 统一状态识别引擎
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Dict, List

from .config import ALL_WAVES, NUMBER_TO_WAVE, SHORT_WINDOW, MEDIUM_WINDOW, LONG_WINDOW
from .wave_model import extract_wave_history, smoothed_frequency


def _specials(rows: List[Dict[str, Any]], window: int | None = None) -> List[int]:
    subset = rows[:window] if window else rows
    result = []
    for row in subset:
        try:
            n = int(row.get("special", 0))
            if 1 <= n <= 49:
                result.append(n)
        except Exception:
            continue
    return result


def detect_size_state(rows: List[Dict[str, Any]], window: int = MEDIUM_WINDOW) -> Dict[str, Any]:
    numbers = _specials(rows, window)
    if not numbers:
        return {"state": "unknown", "prob_big": 0.5, "strength": 0.0}

    big = sum(1 for n in numbers if n >= 25)
    total = len(numbers)
    prob_big = big / total
    deviation = abs(prob_big - 0.5) * 2

    if prob_big >= 0.65:
        state = "big_hot"
    elif prob_big <= 0.35:
        state = "small_hot"
    else:
        state = "balanced"

    return {
        "state": state,
        "prob_big": round(prob_big, 4),
        "prob_small": round(1 - prob_big, 4),
        "strength": round(deviation, 4),
    }


def detect_parity_state(rows: List[Dict[str, Any]], window: int = MEDIUM_WINDOW) -> Dict[str, Any]:
    numbers = _specials(rows, window)
    if not numbers:
        return {"state": "unknown", "prob_odd": 0.5, "strength": 0.0}

    odd = sum(1 for n in numbers if n % 2 == 1)
    total = len(numbers)
    prob_odd = odd / total
    deviation = abs(prob_odd - 0.5) * 2

    if prob_odd >= 0.65:
        state = "odd_hot"
    elif prob_odd <= 0.35:
        state = "even_hot"
    else:
        state = "balanced"

    return {
        "state": state,
        "prob_odd": round(prob_odd, 4),
        "prob_even": round(1 - prob_odd, 4),
        "strength": round(deviation, 4),
    }


def detect_wave_state(rows: List[Dict[str, Any]], window: int = MEDIUM_WINDOW) -> Dict[str, Any]:
    history = extract_wave_history(rows[:window])
    if len(history) < 5:
        return {
            "state": "unknown",
            "latest": None,
            "streak": 0,
            "strength": 0.0,
            "entropy": 1.0,
        }

    latest = history[0]
    streak = 0
    for w in history:
        if w == latest:
            streak += 1
        else:
            break

    freq = smoothed_frequency(rows, window)
    # 简单偏离强度
    strength = max(abs(freq[w] - 1 / 3) for w in ALL_WAVES)

    # 熵
    total = sum(freq.values()) or 1.0
    entropy = 0.0
    for p in freq.values():
        if p > 0:
            entropy -= (p / total) * math.log(p / total + 1e-12)
    max_entropy = math.log(3)
    norm_entropy = entropy / max_entropy if max_entropy > 0 else 1.0

    if strength >= 0.12:
        state = f"{max(freq, key=freq.get)}_trend"
    elif streak >= 3:
        state = "streak"
    else:
        state = "balanced"

    return {
        "state": state,
        "latest": latest,
        "streak": streak,
        "strength": round(strength, 4),
        "entropy": round(norm_entropy, 4),
        "frequency": {k: round(v, 4) for k, v in freq.items()},
    }


def detect_number_trend(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    short = _specials(rows, SHORT_WINDOW)
    medium = _specials(rows, MEDIUM_WINDOW)
    long = _specials(rows, LONG_WINDOW)

    if len(short) < 5:
        return {"state": "unknown", "strength": 0.0, "score": 0.0}

    short_avg = sum(short) / len(short)
    medium_avg = sum(medium) / len(medium) if medium else short_avg
    long_avg = sum(long) / len(long) if long else medium_avg

    short_diff = short_avg - medium_avg
    medium_diff = medium_avg - long_avg
    score = 0.65 * short_diff + 0.35 * medium_diff

    if score >= 2.5:
        state = "up"
    elif score <= -2.5:
        state = "down"
    else:
        state = "neutral"

    strength = min(abs(score) / 10.0, 1.0)

    return {
        "state": state,
        "strength": round(strength, 4),
        "score": round(score, 3),
        "short_avg": round(short_avg, 2),
        "medium_avg": round(medium_avg, 2),
        "long_avg": round(long_avg, 2),
    }


def calculate_chaos(rows: List[Dict[str, Any]]) -> float:
    numbers = _specials(rows, MEDIUM_WINDOW)
    if len(numbers) < 10:
        return 1.0

    # 号码熵
    counter = Counter(numbers)
    total = len(numbers)
    entropy = 0.0
    for c in counter.values():
        p = c / total
        entropy -= p * math.log(p + 1e-12)
    max_entropy = math.log(49)
    number_entropy = entropy / max_entropy if max_entropy > 0 else 1.0

    # 波色熵
    wave_state = detect_wave_state(rows)
    wave_entropy = wave_state.get("entropy", 1.0)

    # 趋势稳定性（越稳定 chaos 越低）
    trend = detect_number_trend(rows)
    trend_chaos = 1.0 - trend.get("strength", 0.0)

    chaos = 0.40 * number_entropy + 0.30 * wave_entropy + 0.30 * trend_chaos
    return max(0.0, min(1.0, chaos))


def detect_market_state(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """统一市场状态出口"""
    if len(rows) < 12:
        return {
            "state": "unknown",
            "confidence": 0.0,
            "window_mode": "normal",
            "window_weights": {"short": 0.35, "medium": 0.35, "long": 0.30},
            "size": {},
            "parity": {},
            "wave": {},
            "trend": {},
            "chaos": 1.0,
        }

    size = detect_size_state(rows)
    parity = detect_parity_state(rows)
    wave = detect_wave_state(rows)
    trend = detect_number_trend(rows)
    chaos = calculate_chaos(rows)

    trend_strength = trend.get("strength", 0.0)
    wave_strength = wave.get("strength", 0.0)
    size_strength = size.get("strength", 0.0)
    parity_strength = parity.get("strength", 0.0)

    structural = (
        0.25 * size_strength
        + 0.25 * parity_strength
        + 0.25 * wave_strength
        + 0.25 * trend_strength
    )

    if chaos >= 0.78:
        state = "chaos"
        confidence = chaos
        window_mode = "long"
        window_weights = {"short": 0.20, "medium": 0.35, "long": 0.45}
    elif trend_strength >= 0.35 or wave_strength >= 0.15:
        state = "trend"
        confidence = min(0.95, 0.50 + structural)
        window_mode = "short"
        window_weights = {"short": 0.50, "medium": 0.30, "long": 0.20}
    else:
        state = "normal"
        confidence = max(0.45, 1.0 - chaos)
        window_mode = "balanced"
        window_weights = {"short": 0.35, "medium": 0.35, "
