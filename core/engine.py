# -*- coding: utf-8 -*-

"""
六合AI V10.0 FINAL

系统引擎
"""

import os
import json
from datetime import datetime


from .api import (
    get_realtime
)

from .database import (
    init_db,
    save_draw,
    get_history,
    count_history
)

from .predictor import (
    predict_next
)



LOTTERIES={

    "hk":
    "香港六合彩",

    "newMacau":
    "新澳门六合彩",

    "oldMacau":
    "老澳门六合彩"

}




# ==========================
# 同步API
# ==========================

def sync_api():


    result={}


    for key in LOTTERIES:


        print(
            "实时同步:",
            key
        )


        data=get_realtime(
            key
        )


        if data:


            ok=save_draw(

                key,

                data.get(
                    "issue",
                    ""
                ),

                data.get(
                    "numbers",
                    []
                )

            )


            result[key]=ok


        else:

            result[key]=False



    return result





# ==========================
# 分析单个彩种
# ==========================

def analyze(
    key
):


    name=LOTTERIES[key]



    print(
        "分析:",
        name
    )



    history=get_history(
        key
    )



    total=count_history(
        key
    )



    if not history:


        return {

            "彩种":name,

            "error":
            "没有读取到历史号码"

        }



    prediction=predict_next(

        history,

        key

    )



    return {


        "彩种":

        name,


        "历史数量":

        total,


        "预测":

        prediction,


        "时间":

        datetime.now().isoformat()


    }





# ==========================
# 主运行
# ==========================

def run():


    print("="*60)

    print(
        "六合彩 AI 智能预测系统 V10.0 FINAL"
    )

    print(
        datetime.now()
    )

    print("="*60)



    print(
        "初始化数据库"
    )


    init_db()



    print(
        "开始API同步"
    )


    sync=sync_api()



    output={

        "version":

        "V10.0 FINAL",


        "time":

        datetime.now().isoformat(),


        "sync":

        sync,


        "lotteries":{}

    }




    for key in LOTTERIES:


        try:


            output["lotteries"][key]=analyze(
                key
            )


        except Exception as e:


            output["lotteries"][key]={

                "error":
                str(e)

            }




    os.makedirs(

        "output",

        exist_ok=True

    )



    with open(

        "output/prediction.json",

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            output,

            f,

            ensure_ascii=False,

            indent=2

        )



    print(

        "输出完成: output/prediction.json"

    )


    return output
