# -*- coding: utf-8 -*-
"""市场状态接口。"""
from .engine import market_state

def analyze_market_state(rows):
    from .engine import specials
    return market_state(specials(rows))
