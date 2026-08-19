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



OUTPUT_DIR = BASE_DIR / "output"


OUTPUT_DIR.mkdir(
    exist_ok=True
)



# =====================================================
# 数据库
# =====================================================


DATABASE_FILE = (
    BASE_DIR /
    "marksix.db"
)



# =====================================================
# 版本
# =====================================================


VERSION = "MarkSix AI V3.0 FINAL"



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
# 模型参数
# =====================================================


MAX_HISTORY = 500


TOP_NUMBER = 10


TOP_FOCUS = 3



__all__=[

    "DATABASE_FILE",

    "OUTPUT_DIR",

    "VERSION",

    "API_HISTORY",

    "API_REALTIME",

    "LOTTERIES",

    "MAX_HISTORY",

    "TOP_NUMBER",

    "TOP_FOCUS"

]
