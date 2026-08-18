# -*- coding: utf-8 -*-
"""特码特征统一接口。"""
from .engine import (
    specials, frequency_feature, omission_feature, momentum_feature,
    trend_feature, adjacency_feature, tail_feature, zone_feature,
    attribute_feature, market_state, get_wave, get_zodiac, get_size, get_parity,
)

def get_special(row):
    return int(row.get("special", 0))

def special_frequency(rows, window=36):
    return frequency_feature(specials(rows), window)

def special_omission(rows, cap=60):
    return omission_feature(specials(rows), cap)
