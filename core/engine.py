# -*- coding:utf-8 -*-

"""
六合彩 AI V3.1 FINAL

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

from __future__ import annotations


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
# 保存输出
# =====================================================


def save_output(data):


    OUTPUT_DIR.mkdir(

        exist_ok=True

    )


    file=OUTPUT_DIR / "prediction.json"



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


    name=LOTTERIES[key]


    print()

    print("="*60)

    print(

        "分析:",

        name

    )

    print("="*60)



    history=load_history(

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


            "状态":

            "无历史数据"

        }





    try:


        result=predict(

            history

        )



    except Exception as e:


        return {


            "彩种":

            name,


            "状态":

            "预测失败",


            "错误":

            str(e)

        }




    result["彩种"]=name


    result["历史数量"]=len(history)



    try:


        result["回测"]=walk_forward(

            history

        )


    except Exception as e:


        result["回测异常"]=str(e)




    result["状态"]="完成"



    return result






# =====================================================
# 主运行
# =====================================================


def run_system():


    print()

    print("="*70)

    print(

        "启动六合AI",

        VERSION

    )

    print(

        datetime.now()

    )

    print("="*70)




    # -----------------------------
    # 数据库
    # -----------------------------


    print()

    print(

        "【1】初始化数据库"

    )



    init_database()




    # -----------------------------
    # API同步
    # -----------------------------


    print()

    print(

        "【2】同步在线数据"

    )



    try:


        sync_result=sync_all()



    except Exception as e:


        print(

            "API同步失败:",

            e

        )


        sync_result={


            "status":

            "failed",


            "error":

            str(e)

        }







    # -----------------------------
    # 预测
    # -----------------------------


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


            results[key]={


                "状态":

                "异常",


                "错误":

                str(e)

            }






    # -----------------------------
    # 总输出
    # -----------------------------


    final={


        "版本":

        VERSION,


        "运行时间":

        datetime.now().isoformat(),


        "系统状态":

        "completed",


        "同步":

        sync_result,


        "预测":

        results

    }



    save_output(

        final

    )



    print()

    print("="*70)

    print(

        "V3.1 FINAL运行完成"

    )

    print("="*70)



    return final





__all__=[

    "run_system"

]
