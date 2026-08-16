# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
全局配置

核心：

1. 三彩种独立数据库
2. 动态 12 / 36 / 120 窗口
3. Walk-Forward
4. 动态策略权重
5. 波色模型
6. 大小模型
7. 单双模型
8. 尾数模型
9. 区间模型
10. 概率校准
11. API SSL fallback
"""

from pathlib import Path


# =========================================================
# 项目目录
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# 数据库
# =========================================================

DB_FILE = DATA_DIR / "lottery.db"


# =========================================================
# API
# =========================================================

API_BASE_URL = (
    "https://api3.marksix6.net/"
    "lottery_api.php"
)


API_SOURCES = {

    "hk": {
        "name": "香港六合彩",
        "url": API_BASE_URL + "?type=hk",
        "wave_field": "wave",
    },

    "newMacau": {
        "name": "新澳门六合彩",
        "url": API_BASE_URL + "?type=newMacau",
        "wave_field": "wave",
    },

    "oldMacau": {
        "name": "老澳门六合彩",
        "url": API_BASE_URL + "?type=oldMacau",
        "wave_field": "waveColors",
    },
}


LOTTERIES = {

    "hk": {
        "name": "香港六合彩",
    },

    "newMacau": {
        "name": "新澳门六合彩",
    },

    "oldMacau": {
        "name": "老澳门六合彩",
    },
}


# =========================================================
# 历史 API
# =========================================================

HISTORY_API_URL = (
    "https://api3.marksix6.net/"
    "index.php?api=1"
)


# =========================================================
# HTTP
# =========================================================

REQUEST_TIMEOUT = 30

HISTORY_TIMEOUT = 60

REQUEST_RETRIES = 3

RETRY_SLEEP = 2


# =========================================================
# SSL
# =========================================================

SSL_VERIFY = True

ALLOW_SSL_FALLBACK = True


# =========================================================
# 最大历史
# =========================================================

MAX_HISTORY = 5000


# =========================================================
# 动态窗口
# =========================================================

SHORT_WINDOW = 12

MEDIUM_WINDOW = 36

LONG_WINDOW = 120

STATE_WINDOW = 36


# =========================================================
# 输出数量
# =========================================================

TOP10_NUMBERS = 10

TOP3_NUMBERS = 3

TOP5_ZODIACS = 5

TOP2_PINGTE_ZODIACS = 2


# =========================================================
# 波色
# =========================================================

WAVES = (
    "红",
    "蓝",
    "绿",
)


# =========================================================
# Walk Forward
# =========================================================

MIN_TRAIN_SIZE = 120

WF_TEST_SIZE = 20

WF_MAX_TESTS = 20

WF_MIN_VALID_TESTS = 5


# =========================================================
# 动态模块权重
# =========================================================

MIN_MODULE_WEIGHT = 0.04

MAX_MODULE_WEIGHT = 0.30

WEIGHT_SMOOTHING = 0.15


# =========================================================
# 默认策略
# =========================================================

MODULES = (

    "recent",

    "medium",

    "long",

    "omission",

    "trend",

    "transition",

    "size",

    "parity",

    "wave",

    "tail",

    "zone",
)


DEFAULT_MODULE_WEIGHTS = {

    "recent": 0.13,

    "medium": 0.10,

    "long": 0.07,

    "omission": 0.06,

    "trend": 0.15,

    "transition": 0.12,

    "size": 0.10,

    "parity": 0.10,

    "wave": 0.08,

    "tail": 0.05,

    "zone": 0.04,
}


CATEGORY_DEFAULT_WEIGHTS = {

    "size": 1.0,

    "parity": 1.0,

    "wave": 1.0,
}


# =========================================================
# 概率校准
# =========================================================

PROBABILITY_FLOOR = 0.01

PROBABILITY_CEILING = 0.99

PROBABILITY_TEMPERATURE = 1.15


# =========================================================
# 输出
# =========================================================

PREDICTION_FILE = (
    OUTPUT_DIR / "prediction.json"
)

BACKTEST_FILE = (
    OUTPUT_DIR / "backtest.json"
)


JSON_ENSURE_ASCII = False

JSON_INDENT = 2