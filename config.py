# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

全局配置
"""


from pathlib import Path



# =====================================================
# 项目路径
# =====================================================


BASE_DIR = Path(__file__).resolve().parent


DATA_DIR = BASE_DIR / "data"


OUTPUT_DIR = BASE_DIR / "output"



DATA_DIR.mkdir(
    exist_ok=True
)


OUTPUT_DIR.mkdir(
    exist_ok=True
)



# =====================================================
# SQLite
# =====================================================


DATABASE_FILE = (
    DATA_DIR /
    "lottery.db"
)



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
# 预测参数
# =====================================================


FEATURE_WINDOWS = {


    "short":

    12,


    "medium":

    36,


    "long":

    120

}



TOP_NUMBER_COUNT = 10


TOP_MAIN_COUNT = 3



BACKTEST_WINDOWS = [

    10,

    20

]



VERSION = (

    "V3.0 FINAL"

)
