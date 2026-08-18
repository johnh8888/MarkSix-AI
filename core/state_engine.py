# -*- coding: utf-8 -*-
"""动态状态/权重接口。"""
from .engine import dynamic_weights, BASE_MODULE_WEIGHTS

def get_dynamic_weights(state, performance=None):
    return dynamic_weights(state, performance)
