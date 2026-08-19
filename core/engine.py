# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

系统总控制引擎


流程:

main.py

 ↓

engine

 ↓

数据库

 ↓

API同步

 ↓

质量检测

 ↓

预测

 ↓

回测

 ↓

输出


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



from .quality import (

    analyze_quality

)



from .features import (

    feature_statistics

)







# =====================================================
# 输出
# =====================================================


def save_output(data):


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





    history=load_history(

        key

    )



    print(

        "历史数量:",

        len(history)

    )





    quality=analyze_quality(

        history

    )





    if not history:


        return {


            "彩种":

            name,


            "数据质量":

            quality,


            "错误":

            "无历史数据"

        }





    result=predict(

        history

    )




    result["彩种"]=name



    result["历史数量"]=len(history)



    result["数据质量"]=quality



    result["特征统计"]=feature_statistics(

        history

    )




    result["回测"]=walk_forward(

        history

    )




    return result







# =====================================================
# 主运行
# =====================================================


def run_system():


    print()

    print(

        "="*70

    )


    print(

        "六合 AI V3.2 FINAL"

    )


    print(

        datetime.now()

    )


    print(

        "="*70

    )





    # -----------------
    # 数据库
    # -----------------


    print(

        "【1】初始化数据库"

    )



    init_database()



    print(

        "数据库完成"

    )








    # -----------------
    # API
    # -----------------


    print()

    print(

        "【2】API同步"

    )



    try:


        sync_result=sync_all()



    except Exception as e:


        print(

            "API错误:",

            e

        )



        sync_result={


            "error":

            str(e)

        }









    # -----------------
    # 预测
    # -----------------


    print()

    print(

        "【3】智能预测"

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

                "失败:",

                e

            )



            results[key]={


                "error":

                str(e)

            }







    # -----------------
    # 输出
    # -----------------


    final={


        "版本":

        VERSION,



        "系统":

        "六合AI V3.2 FINAL",



        "时间":

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

        "="*70

    )


    print(

        "V3.2 FINAL运行完成"

    )


    print(

        "="*70

    )




    return final






__all__=[

    "run_system"

]
