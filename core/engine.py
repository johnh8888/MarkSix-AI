# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

系统总控制引擎


流程:

main.py

 ↓

engine

 ↓

数据库初始化

 ↓

API同步

 ↓

读取历史

 ↓

预测

 ↓

回测

 ↓

JSON输出

"""


from datetime import datetime

import json



from config import (

    LOTTERIES,

    OUTPUT_DIR,

    VERSION

)



from .database import (

    init_database,

    load_history

)



from .api_sync import (

    sync_all

)



from .predictor import (

    predict

)



from .backtest import (

    walk_forward

)







# =====================================================
# 保存结果
# =====================================================


def save_output(data):


    file = OUTPUT_DIR / "prediction.json"



    file.write_text(

        json.dumps(

            data,

            ensure_ascii=False,

            indent=2

        ),

        encoding="utf-8"

    )


    print()

    print(

        "输出文件:",

        file

    )



    return file







# =====================================================
# 单彩种分析
# =====================================================


def analyze_lottery(key):


    name = LOTTERIES[key]



    print()

    print(

        "="*60

    )


    print(

        "分析:",

        name

    )


    print(

        "="*60

    )




    history = load_history(

        key

    )



    print(

        "历史数量:",

        len(history)

    )



    if not history:


        return {


            "彩种":

            name,


            "错误":

            "没有历史数据"

        }





    result = predict(

        history

    )



    result["彩种"]=name



    result["历史数量"]=len(history)



    result["回测"]=walk_forward(

        history

    )



    return result







# =====================================================
# 主流程
# =====================================================


def run_system():


    print()

    print(

        "启动六合AI V3.0系统"

    )



    # ----------------------------

    # 1 数据库

    # ----------------------------


    print()

    print(

        "【1】初始化数据库"

    )



    init_database()



    print(

        "数据库完成"

    )





    # ----------------------------

    # 2 API

    # ----------------------------


    print()

    print(

        "【2】同步在线数据"

    )



    try:


        sync_result = sync_all()



    except Exception as e:


        print(

            "同步失败:",

            e

        )


        sync_result={

            "error":

            str(e)

        }







    # ----------------------------

    # 3预测

    # ----------------------------


    print()

    print(

        "【3】开始智能预测"

    )



    results={}



    for key in LOTTERIES:


        try:


            results[key]=analyze_lottery(

                key

            )



        except Exception as e:


            print(

                key,

                "错误:",

                e

            )



            results[key]={

                "error":

                str(e)

            }





    # ----------------------------

    # 总输出

    # ----------------------------


    final={


        "版本":

        VERSION,



        "运行时间":

        datetime.now().isoformat(),



        "同步":

        sync_result,



        "预测":

        results

    }





    save_output(

        final

    )



    print()

    print(

        "V3.0 FINAL运行完成"

    )



    return final





__all__=[

    "run_system"

]
