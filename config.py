# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

全局配置
"""

from pathlib import Path


# =====================================================
# 项目路径
# =====================================================

BASE_DIR = Path(
    __file__
).resolve().parent


CORE_DIR = BASE_DIR / "core"


OUTPUT_DIR = BASE_DIR / "output"


DATA_DIR = BASE_DIR / "data"


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =====================================================
# 数据库
# =====================================================

DATABASE_FILE = (
    DATA_DIR / "marksix_v3.db"
)


# =====================================================
# 系统版本
# =====================================================

VERSION = "V3.0 FINAL"


# =====================================================
# 历史数据
# =====================================================

HISTORY_LIMIT = 500


# =====================================================
# 彩种
# =====================================================

LOTTERIES = {

    "hk":
        "香港六合彩",

    "newMacau":
        "新澳门六合彩",

    "oldMacau":
        "老澳门六合彩"
}


# =====================================================
# API
# =====================================================

API_HISTORY = (
    "https://marksix6.net/index.php?api=1"
)


API_REALTIME = (
    "https://marksix6.net/api/lottery_api.php"
)


# =====================================================
# 预测参数
# =====================================================

TOP10 = 10

TOP3 = 3


# =====================================================
# 回测参数
# =====================================================

BACKTEST_MIN_TRAIN = 30


__all__ = [
    "BASE_DIR",
    "CORE_DIR",
    "OUTPUT_DIR",
    "DATA_DIR",
    "DATABASE_FILE",
    "VERSION",
    "HISTORY_LIMIT",
    "LOTTERIES",
    "API_HISTORY",
    "API_REALTIME",
    "TOP10",
    "TOP3",
    "BACKTEST_MIN_TRAIN"
]
