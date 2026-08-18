# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.0

main_engine.py

系统总调度引擎


"""


import os

import json

from datetime import datetime





from .predictor import (

    full_predict,

    predict_next

)



from .backtest import (

    快速回测

)



from .state_engine import (

    状态引擎

)





# =====================================================
# 输出目录
# =====================================================


OUTPUT_DIR="output"


os.makedirs(

    OUTPUT_DIR,

    exist_ok=True

)





# =====================================================
# 保存JSON
# =====================================================


def 保存文件(

        数据,

        文件名

):


    路径=os.path.join(

        OUTPUT_DIR,

        文件名

    )


    with open(

        路径,

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            数据,

            f,

            ensure_ascii=False,

            indent=4

        )


    return 路径





# =====================================================
# 数据格式转换
# =====================================================


def 标准化数据(

        数据

):


    新数据=[]



    for item in 数据:


        if isinstance(

            item,

            dict

        ):


            新数据.append(item)



    return 新数据





# =====================================================
# 单彩种分析
# =====================================================


def 分析彩种(

        名称,

        数据

):


    print(

        "="*60

    )


    print(

        f"开始分析：{名称}"

    )


    print(

        "="*60

    )



    数据=标准化数据(

        数据

    )



    print(

        f"历史数据：{len(数据)}期"

    )





    # 状态


    状态=状态引擎(

        数据

    )



    print(

        "当前市场状态：",

        状态.get(

            "市场状态"

        )

    )





    # 预测


    预测=full_predict(

        数据

    )





    print()

    print(

        "【特码10码】"

    )



    print(

        预测["预测号码"]["特码10码"]

    )





    print()

    print(

        "【重点推荐】"

    )



    print(

        预测["预测号码"]["重点推荐"]

    )





    print()

    print(

        "【生肖5肖】"

    )



    print(

        预测["生肖"]

    )





    print()

    print(

        "【波色预测】"

    )


    print(

        预测["波色"]

    )





    print()

    print(

        "【大小】"

    )


    print(

        预测["大小"]

    )





    print()

    print(

        "【单双】"

    )


    print(

        预测["单双"]

    )





    # 回测


    print()

    print(

        "开始Walk-Forward回测"

    )



    回测=快速回测(

        数据

    )



    print(

        回测

    )





    return {


        "彩种":

        名称,


        "时间":

        str(

            datetime.now()

        ),


        "状态":

        状态,


        "预测":

        预测,


        "回测":

        回测

    }





# =====================================================
# 主运行入口
# =====================================================


def run(

        datasets

):


    print()

    print(

        "#"*60

    )



    print(

        "六合彩AI智能预测系统 V5.0"

    )



    print(

        "工作流："

        "同步 → 状态识别 → 动态权重 → 预测 → Walk-Forward"

    )



    print(

        datetime.now()

    )



    print(

        "#"*60

    )





    全部结果=[]



    for 名称,数据 in datasets.items():


        结果=分析彩种(

            名称,

            数据

        )


        全部结果.append(

            结果

        )





    文件1=保存文件(

        全部结果,

        "prediction.json"

    )



    print()

    print(

        "预测结果保存：",

        文件1

    )





    return 全部结果





if __name__=="__main__":


    print(

        "V5主引擎启动"

    )
