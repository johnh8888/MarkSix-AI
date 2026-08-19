# -*- coding:utf-8 -*-

"""
六合彩 AI V3.4 FINAL

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

特征分析

↓

AI预测

↓

回测

↓

JSON输出

↓

TXT/HTML报告


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



from .report import (

    create_txt_report,

    create_html_report

)





# =====================================================
# 保存JSON
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
        "JSON输出:",
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





    quality = analyze_quality(

        history

    )






    if not history:


        return {


            "彩种":

            name,


            "错误":

            "无历史数据",


            "数据质量":

            quality

        }





    try:


        result = predict(

            history

        )


    except Exception as e:



        return {


            "彩种":

            name,


            "预测错误":

            str(e)


        }





    result["彩种"] = name



    result["历史数量"] = len(history)



    result["数据质量"] = quality



    try:


        result["特征统计"] = feature_statistics(

            history

        )


    except Exception:


        result["特征统计"] = {}






    try:


        result["回测"] = walk_forward(

            history

        )


    except Exception as e:


        result["回测"] = {


            "状态":

            "失败",


            "原因":

            str(e)

        }





    return result







# =====================================================
# 主程序
# =====================================================


def run_system():


    print()

    print(
        "="*70
    )


    print(
        "六合彩 AI V3.4 FINAL"
    )


    print(
        datetime.now()
    )


    print(
        "="*70
    )






    # ==============================
    # 初始化数据库
    # ==============================


    print()

    print(
        "【1】初始化数据库"
    )



    init_database()



    print(
        "数据库完成"
    )








    # ==============================
    # API同步
    # ==============================


    print()

    print(
        "【2】API同步"
    )



    try:


        sync_result = sync_all()



    except Exception as e:



        print(

            "API同步失败:",

            e

        )


        sync_result = {


            "status":

            "error",


            "message":

            str(e)

        }








    # ==============================
    # AI预测
    # ==============================


    print()

    print(
        "【3】智能预测"
    )



    results = {}





    for key in LOTTERIES:



        try:


            results[key] = analyze_lottery(

                key

            )



        except Exception as e:



            print(

                key,

                "分析失败:",

                e

            )



            results[key] = {


                "彩种":

                LOTTERIES[key],


                "error":

                str(e)

            }









    # ==============================
    # 总结果
    # ==============================


    final = {



        "版本":

        VERSION,



        "系统":

        "六合彩 AI V3.4 FINAL",



        "时间":

        datetime.now().isoformat(),



        "同步":

        sync_result,



        "预测":

        results



    }






    # JSON

    save_output(

        final

    )






    # TXT

    try:


        txt=create_txt_report(

            results

        )


        print(

            "文字报告:",

            txt

        )



    except Exception as e:



        print(

            "TXT报告失败:",

            e

        )








    # HTML

    try:


        html=create_html_report(

            results

        )


        print(

            "网页报告:",

            html

        )



    except Exception as e:



        print(

            "HTML报告失败:",

            e

        )








    print()

    print(
        "="*70
    )


    print(
        "V3.4 FINAL运行完成"
    )


    print(
        "="*70
    )



    return final





__all__=[

    "run_system"

]
