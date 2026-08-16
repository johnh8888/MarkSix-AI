# -*- coding: utf-8 -*-

from pathlib import Path

# =========================
# 基础目录
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# =========================
# 数据库
# =========================

DB_FILE = DATA_DIR / "lottery.db"


# =========================
# 三个彩种
# =========================

LOTTERIES = {
    "hk": {
        "name": "香港六合彩",
        "api_type": "hk",
    },

    "macau": {
        "name": "澳门六合彩",
        "api_type": "macau",
    },

    "newMacau": {
        "name": "新澳门六合彩",
        "api_type": "newMacau",
    },
}


# =========================
# 数据源
# =========================

API_URLS = [
    "https://api3.marksix6.net/lottery_api.php",
    "https://api2.marksix6.net/lottery_api.php",
    "https://marksix6.net/api/lottery_api.php",
]


# =========================
# 模型参数
# =========================

# 最近多少期用于主要趋势分析
WINDOW_SHORT = 30

# 中期
WINDOW_MEDIUM = 100

# 长期
WINDOW_LONG = 300

# 最大历史数据
MAX_HISTORY = 3000


# =========================
# 推荐数量
# =========================

TOP10_NUMBERS = 10
TOP5_ZODIACS = 5
TOP2_ZODIACS = 2


# =========================
# 回测
# =========================

BACKTEST_WINDOWS = [
    100,
    300,
    500,
    1000,
]


# =========================
# 输出文件
# =========================

PREDICTION_FILE = OUTPUT_DIR / "predictions.json"
BACKTEST_FILE = OUTPUT_DIR / "backtest.json"
