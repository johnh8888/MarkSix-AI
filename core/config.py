# -*- coding: utf-8 -*-
"""MarkSix AI V3.2 统一配置。"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CORE_DIR = BASE_DIR / "core"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_HISTORY = "https://marksix6.net/index.php?api=1"
API_REALTIME = "https://marksix6.net/api/lottery_api.php"

DB_FILES = {
    "hk": BASE_DIR / "hk_macau.db",
    "newMacau": BASE_DIR / "new_macau.db",
    "oldMacau": BASE_DIR / "old_macau.db",
}
LOTTERY_NAMES = {
    "hk": "香港六合彩",
    "newMacau": "新澳门六合彩",
    "oldMacau": "老澳门六合彩",
}

# 预测窗口：删除旧版30/60/100回测窗口；模型内部仍可使用多尺度特征。
SHORT_WINDOW = 12
MEDIUM_WINDOW = 36
LONG_WINDOW = 120
BACKTEST_WINDOWS = (10, 20)
MIN_TRAIN_SIZE = 20

ZODIAC_MAP_2026 = {
    "马": [1, 13, 25, 37, 49], "蛇": [2, 14, 26, 38],
    "龙": [3, 15, 27, 39], "兔": [4, 16, 28, 40],
    "虎": [5, 17, 29, 41], "牛": [6, 18, 30, 42],
    "鼠": [7, 19, 31, 43], "猪": [8, 20, 32, 44],
    "狗": [9, 21, 33, 45], "鸡": [10, 22, 34, 46],
    "猴": [11, 23, 35, 47], "羊": [12, 24, 36, 48],
}
NUMBER_TO_ZODIAC = {n: z for z, nums in ZODIAC_MAP_2026.items() for n in nums}

RED_WAVE = {1,2,7,8,12,13,18,19,23,24,29,30,34,35,40,45,46}
BLUE_WAVE = {3,4,9,10,14,15,20,25,26,31,36,37,41,42,47,48}
GREEN_WAVE = {5,6,11,16,17,21,22,27,28,32,33,38,39,43,44,49}
WAVE_MAP = {"红": RED_WAVE, "蓝": BLUE_WAVE, "绿": GREEN_WAVE}
NUMBER_TO_WAVE = {n: w for w, nums in WAVE_MAP.items() for n in nums}
ALL_NUMBERS = list(range(1, 50))
ALL_WAVES = ["红", "蓝", "绿"]
