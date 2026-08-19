# -*- coding:utf-8 -*-

"""
六合彩 AI V3.3 FINAL

系统控制引擎


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

输出JSON

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
# 保存输出
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

    print("="*70)

    print(

        "预测文件:",

        file

    )

    print("="*70)



    return file






# =====================================================
# 打印预测报告
# =====================================================


def print_prediction(name,result):


    print()

    print("="*70)

    print(

        "AI预测报告:",

        name

    )

    print("="*70)



    if "错误" in result:

        print(

            result["错误"]

        )

        return




    print()

    print(

        "第一推荐:",

        result.get(

            "第一推荐"

        )

    )


    print(

        "重点3码:",

        result.get(

            "重点3码"

        )

    )


    print(

        "特码10码:",

        result.get(

            "特码10码"

        )

    )



    print()

    print(

        "波色预测:"

    )


    print(

        json.dumps(

            result.get(

                "波色",

                {}

            ),

            ensure_ascii=False

        )

    )



    print()


    print(

        "大小:",

        result.get(

            "大小"

        )

    )


    print(

        "单双:",

        result.get(

            "单双"

        )

    )


    print(

        "置信度:",

        result.get(

            "置信度"

        )

    )


    print(

        "风险:",

        result.get(

            "风险等级"

        )

    )


    print()

    print("="*70)






# =====================================================
# 单彩种分析
# =====================================================


def analyze_lottery(key):


    name=LOTTERIES[key]



    print()

    print("="*70)

    print(

        "分析:",

        name

    )

    print("="*70)



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


            "错误":

                "无历史数据",


            "数据质量":

                quality

        }







    result=predict(

        history

    )



    # =============================
    # 输出控制台预测
    # =============================


    print_prediction(

        name,

        result

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

    print("="*70)

    print(

        "六合彩 AI V3.3 FINAL"

    )


    print(

        datetime.now()

    )


    print("="*70)





    # ------------------
    # 数据库
    # ------------------


    print()

    print(

        "【1】初始化数据库"

    )


    init_database()


    print(

        "数据库完成"

    )





    # ------------------
    # API同步
    # ------------------


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






    # ------------------
    # 预测
    # ------------------


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


            print()

            print(

                key,

                "失败:",

                e

            )



            results[key]={

                "错误":

                    str(e)

            }






    # ------------------
    # 最终JSON
    # ------------------


    final={


        "版本":

            VERSION,



        "系统":

            "六合AI V3.3 FINAL",



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

    print("="*70)

    print(

        "V3.3 FINAL运行完成"

    )

    print("="*70)



    return final





__all__=[

    "run_system"

]
