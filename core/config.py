# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

核心配置

升级:
1. 动态权重
2. 状态切换
3. Softmax评分
4. 波色双推
5. Walk Forward

"""


# =========================================================
# 基础配置
# =========================================================


VERSION = "V4.0"


NUMBER_MIN = 1

NUMBER_MAX = 49



# =========================================================
# 数据窗口
# =========================================================


# 近期趋势

SHORT_WINDOW = 20


# 中期趋势

MEDIUM_WINDOW = 50


# 长期参考

LONG_WINDOW = 200



# 回测窗口

BACKTEST_WINDOWS = [
    10,
    20,
    40
]



# =========================================================
# 号码评分模型权重
# =========================================================


MODEL_WEIGHTS = {


    # 基础频率

    "frequency":
        0.18,


    # 趋势

    "trend":
        0.15,


    # 动量

    "momentum":
        0.12,


    # 遗漏

    "omission":
        0.10,


    # 连续压力

    "pressure":
        0.08,


    # 号码距离

    "distance":
        0.08,


    # 尾数

    "tail":
        0.06,


    # 区域

    "zone":
        0.05,


    # 大小

    "size":
        0.07,


    # 单双

    "parity":
        0.06,


    # 波色

    "wave":
        0.05,

}



# =========================================================
# 市场状态
# =========================================================


STATE_LIST = [

    "NORMAL",

    "HOT",

    "COLD",

    "SHIFT",

    "CHAOS"

]



# 默认状态

DEFAULT_STATE = "NORMAL"



# 状态调整参数


STATE_BOOST = {


    "NORMAL":
    {


        "frequency":
            1.0,


        "trend":
            1.0,


        "omission":
            1.0,

    },


    "HOT":
    {


        "frequency":
            0.9,


        "trend":
            1.25,


        "momentum":
            1.25,


    },


    "COLD":
    {


        "omission":
            1.35,


        "pressure":
            1.25,


    },


    "SHIFT":
    {


        "distance":
            1.30,


        "wave":
            1.20,


        "trend":
            0.85,

    },


    "CHAOS":
    {


        "frequency":
            0.75,


        "trend":
            0.75,


        "random":
            1.20,

    }

}




# =========================================================
# Softmax评分
# =========================================================


SOFTMAX_TEMPERATURE = 0.8



# 输出数量


TOP_NUMBER_COUNT = 10


SPECIAL_RECOMMEND_COUNT = 3



# =========================================================
# 波色配置
# =========================================================


WAVE_LIST = [

    "红",

    "蓝",

    "绿"

]



# 波色输出

WAVE_SINGLE_COUNT = 1


WAVE_DOUBLE_COUNT = 2



# 波色历史窗口

WAVE_SHORT_WINDOW = 20


WAVE_LONG_WINDOW = 100



# =========================================================
# 生肖
# =========================================================


ZODIAC_COUNT = 12


ZODIAC_TOP5 = 5


ZODIAC_TOP2 = 2



# =========================================================
# 特征开关
# =========================================================


FEATURE_ENABLE = {


    "frequency":
        True,


    "trend":
        True,


    "momentum":
        True,


    "omission":
        True,


    "pressure":
        True,


    "distance":
        True,


    "tail":
        True,


    "zone":
        True,


    "size":
        True,


    "parity":
        True,


    "wave":
        True,

}



# =========================================================
# 数据库
# =========================================================


DB_FILES = {


    "hk":

        "hk.db",


    "newMacau":

        "new_macau.db",


    "oldMacau":

        "old_macau.db",

}



# =========================================================
# API
# =========================================================


API_HISTORY_URL = (

    "https://marksix6.net/index.php?api=1"

)


API_DETAIL_URL = (

    "https://marksix6.net/api/lottery_api.php"

)



# =========================================================
# 输出
# =========================================================


OUTPUT_DIR = "output"


PREDICTION_FILE = (

    "output/prediction.json"

)


BACKTEST_FILE = (

    "output/backtest.json"

)
