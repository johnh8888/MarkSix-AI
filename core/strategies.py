# -*- coding: utf-8 -*-
"""号码策略组合接口。解决旧版策略模块与新版 V3 引擎接口不一致问题。"""
from .config import SHORT_WINDOW, MEDIUM_WINDOW, LONG_WINDOW
from .engine import build_modules, combine_number_scores, dynamic_weights, market_state, specials, BASE_MODULE_WEIGHTS


def combine_strategies(rows):
    sp = specials(rows)
    if not sp:
        return {n: 0.5 for n in range(1, 50)}, {}
    state = market_state(sp)
    weights = dynamic_weights(state, None)
    scores = combine_number_scores(sp, weights)
    modules = build_modules(sp)
    return scores, modules

__all__ = ["combine_strategies", "SHORT_WINDOW", "MEDIUM_WINDOW", "LONG_WINDOW", "BASE_MODULE_WEIGHTS"]
