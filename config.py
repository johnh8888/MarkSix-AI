# -*- coding:utf-8 -*-

"""
六合彩 AI V3.3 FINAL

系统配置文件

功能:

1. 版本管理
2. 数据库路径
3. 输出目录
4. 彩种配置
5. 系统参数

"""


from pathlib import Path





# =====================================================
# 项目目录
# =====================================================


BASE_DIR = Path(__file__).resolve().parent






# =====================================================
# 版本
# =====================================================


VERSION = "V3.3 FINAL"






# =====================================================
# 数据目录
# =====================================================


DATA_DIR = BASE_DIR / "data"



DATA_DIR.mkdir(

    exist_ok=True

)







# =====================================================
# 输出目录
# =====================================================


OUTPUT_DIR = BASE_DIR / "output"



OUTPUT_DIR.mkdir(

    exist_ok=True

)







# =====================================================
# SQLite数据库
# =====================================================


DATABASE_FILE = (

    DATA_DIR /

    "marksix_v3.db"

)








# =====================================================
# 彩种配置
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
# API配置
# =====================================================


API_CONFIG = {


    "history":

        "https://marksix6.net/index.php?api=1",



    "hk":

        "https://marksix6.net/api/lottery_api.php?type=hk",



    "newMacau":

        "https://marksix6.net/api/lottery_api.php?type=newMacau",



    "oldMacau":

        "https://marksix6.net/api/lottery_api.php?type=oldMacau"

}








# =====================================================
# 模型参数
# =====================================================


MODEL_CONFIG = {


    # 历史使用数量

    "history_limit":

        500,



    # Markov最低数据

    "markov_min":

        20,



    # HMM最低数据

    "hmm_min":

        50,



    # 高级模型最低数据

    "advanced_min":

        100

}








# =====================================================
# 输出设置
# =====================================================


OUTPUT_CONFIG = {


    "save_json":

        True,



    "json_name":

        "prediction.json"

}








__all__=[


    "VERSION",


    "DATABASE_FILE",


    "OUTPUT_DIR",


    "LOTTERIES",


    "API_CONFIG",


    "MODEL_CONFIG",


    "OUTPUT_CONFIG"

]
