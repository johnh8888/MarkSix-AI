# -*- coding: utf-8 -*-
"""
六合彩 AI V3.0 - 波色模型
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple

from .config import (
    ALL_WAVES,
    NUMBER_TO_WAVE,
    RED_WAVE,
    BLUE_WAVE,
    GREEN_WAVE,
)

WAVES = tuple(ALL_WAVES)


def clamp_probability(value: float, floor: float = 0.01, ceiling: float = 0.99) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    return max(floor, min(ceiling, value))


def number_to_wave(number: Any) -> str:
    try:
        number = int(number)
    except (TypeError, ValueError):
        return "未知"
    return NUMBER_TO_WAVE.get(number, "未知")


def _extract_special(draw: Dict[str, Any]) -> int | None:
    special = draw.get("special")
    if special is not None:
        try:
            n = int(special)
            if 1 <= n <= 49:
                return n
        except (TypeError, ValueError):
            pass

    numbers = draw.get("numbers", [])
    if isinstance(numbers, (list, tuple)) and len(numbers) >= 7:
        try:
            n = int(numbers[-1])
            if 1 <= n <= 49:
                return n
        except (TypeError, ValueError):
            pass
    return None


def extract_wave_history(draws: Sequence[Dict[str, Any]]) -> List[str]:
    result = []
    for draw in draws:
        wave = draw.get("wave")
        if isinstance(wave, str) and wave.strip() in WAVES:
            result.append(wave.strip())
            continue

        special = _extract_special(draw)
        if special is None:
            continue
        w = number_to_wave(special)
        if w in WAVES:
            result.append(w)
    return result


def smoothed_frequency(
    draws: Sequence[Dict[str, Any]],
    window: int = 36,
    alpha: float = 1.0,
) -> Dict[str, float]:
    history = extract_wave_history(draws[:window])
    counter = Counter(history)
    total = sum(counter.get(w, 0) for w in WAVES) + alpha * len(WAVES)
    return {
        w: (counter.get(w, 0) + alpha) / total
        for w in WAVES
    }


def transition_matrix(
    draws: Sequence[Dict[str, Any]],
    window: int = 120,
    alpha: float = 1.0,
) -> Dict[str, Dict[str, float]]:
    history = extract_wave_history(draws[:window])
    matrix = {src: {tgt: alpha for tgt in WAVES} for src in WAVES}

    if len(history) >= 2:
        # history[0] 是最新
        for i in range(len(history) - 1):
            current = history[i]       # 较新
            previous = history[i + 1]  # 较旧
            if previous in WAVES and current in WAVES:
                matrix[previous][current] += 1

    result = {}
    for src in WAVES:
        total = sum(matrix[src].values())
        result[src] = {
            w: matrix[src][w] / total if total > 0 else 1.0 / 3.0
            for w in WAVES
        }
    return result


def transition_probabilities(
    draws: Sequence[Dict[str, Any]],
    window: int = 120,
) -> Dict[str, float]:
    history = extract_wave_history(draws[:window])
    if not history:
        return {w: 1.0 / 3.0 for w in WAVES}
    current = history[0]
    matrix = transition_matrix(draws, window=window)
    return matrix.get(current, {w: 1.0 / 3.0 for w in WAVES})


def wave_probabilities(draws: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    """综合波色概率：近期30% + 中期25% + 长期15% + 转移30%"""
    if not draws:
        return {w: 1.0 / 3.0 for w in WAVES}

    recent = smoothed_frequency(draws, window=12)
    medium = smoothed_frequency(draws, window=36)
    long = smoothed_frequency(draws, window=120)
    trans = transition_probabilities(draws, window=120)

    raw = {
        w: (
            recent[w] * 0.30
            + medium[w] * 0.25
            + long[w] * 0.15
            + trans[w] * 0.30
        )
        for w in WAVES
    }
    total = sum(raw.values()) or 1.0
    result = {w: clamp_probability(raw[w] / total) for w in WAVES}

    # 再归一化
    total = sum(result.values()) or 1.0
    return {w: result[w] / total for w in WAVES}


def rank_waves(draws: Sequence[Dict[str, Any]]) -> List[Tuple[str, float]]:
    probs = wave_probabilities(draws)
    return sorted(probs.items(), key=lambda x: x[1], reverse=True)


def analyze_wave(draws: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    probs = wave_probabilities(draws)
    ranked = rank_waves(draws)
    single = ranked[0][0] if ranked else "红"
    double = [w for w, _ in ranked[:2]]

    return {
        "single": single,
        "double": double,
        "exclude": ranked[2][0] if len(ranked) > 2 else "绿",
        "probability": {w: round(p, 6) for w, p in probs.items()},
        "rank": [{"wave": w, "probability": round(p, 6)} for w, p in ranked],
        "recent": smoothed_frequency(draws, 12),
        "medium": smoothed_frequency(draws, 36),
        "long": smoothed_frequency(draws, 120),
        "transition": transition_probabilities(draws, 120),
    }


def number_wave_score(number: int, probabilities: Dict[str, float]) -> float:
    wave = number_to_wave(number)
    return float(probabilities.get(wave, 0.0)) if wave in WAVES else 0.0
