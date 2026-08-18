# -*- coding: utf-8 -*-
"""统一 Walk-Forward 回测入口。只测试最近10/20期，不再输出30/60/100。"""
from .engine import walk_forward, predict_from_history

__all__ = ["walk_forward", "predict_from_history"]
