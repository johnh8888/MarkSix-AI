# -*- coding: utf-8 -*-

"""
六合彩预测系统入口

V3.6

改动：
不再使用旧版单文件 V8.3.2 逻辑，
统一接入 core/engine.py（V7.1）作为真正的运行入口。
"""

from core.engine import run_system


if __name__ == "__main__":

    run_system()
