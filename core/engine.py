# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.2 FINAL

core/engine.py


系统总控制器


流程:

初始化
 ↓
数据库
 ↓
API同步
 ↓
质量检测
 ↓
状态分析
 ↓
策略选择
 ↓
预测
 ↓
回测
 ↓
JSON输出


"""


from __future__ import annotations


import json


from datetime import datetime


from pathlib import Path



from .sqlite_manager import (

    init_database,

    load_history

)



from .api_sync import (

    sync_all

)



from .data_quality import (

    quality_report

)



from .predictor import (

    predict_next

)



try:

    from .backtest import walk_forward


except Exception:


    walk_forward=None







# =====================================================
# 路径
# =====================================================


BASE_DIR=Path(__file__).resolve().parent.parent


OUTPUT_DIR=BASE_DIR/"output"


OUTPUT_DIR.mkdir(

    exist_ok=True

)







# =====================================================
# 彩种
# =====================================================


LOTTERIES={


    "hk":

    "香港六合彩",



    "newMacau":

    "新澳门六合彩",



    "oldMacau":

    "老澳门六合彩"

}







# =====================================================
# 输出
# =====================================================


def save_json(

        name,

        data

):


    path=OUTPUT_DIR/name



    path.write_text(

        json.dumps(

            data,

            ensure_ascii=False,

            indent=2

        ),

        encoding="utf-8"

    )


    print(

        "输出:",

        path

    )


    return path







# =====================================================
# 单彩种运行
# =====================================================


def run_lottery(

        key:str

):


    print()

    print("="*70)

    print(

        "分析:",

        LOTTERIES[key]

    )

    print("="*70)





    history=load_history(

        key

    )



    quality=quality_report(

        history

    )



    print(

        "数据质量:",

        quality["质量评分"]

    )





    if not quality["可以预测"]:


        return {


            "error":

            "数据质量不足",


            "quality":

            quality

        }






    specials=[]



    for row in history:


        if isinstance(row,dict):


            specials.append(

                int(

                    row["special"]

                )

            )





    prediction=predict_next(

        specials

    )





    result={


        "彩种":

        LOTTERIES[key],



        "历史数量":

        len(history),



        "数据质量":

        quality,



        "预测":

        prediction,



        "时间":

        datetime.now().isoformat()

    }






    if walk_forward:


        try:


            result["回测"]=walk_forward(

                specials,

                20

            )


        except Exception as e:


            result["回测异常"]=str(e)






    return result







# =====================================================
# 总运行
# =====================================================


def run():



    print("="*70)

    print(

        "六合彩 AI 智能预测系统 V5.2 FINAL"

    )

    print(

        datetime.now()

    )

    print("="*70)






    # 1 数据库


    print(

        "【1】初始化数据库"

    )


    init_database()







    # 2 同步


    print(

        "【2】API同步"

    )


    try:


        sync_result=sync_all()


    except Exception as e:


        sync_result={

            "error":

            str(e)

        }





    # 3预测


    print(

        "【3】开始预测"

    )



    results={}



    for key in LOTTERIES:


        try:


            results[key]=run_lottery(

                key

            )


        except Exception as e:


            results[key]={

                "error":

                str(e)

            }





    final={


        "version":

        "V5.2 FINAL",



        "time":

        datetime.now().isoformat(),



        "sync":

        sync_result,



        "lotteries":

        results

    }





    save_json(

        "prediction.json",

        final

    )





    print()

    print("="*70)

    print(

        "系统运行完成"

    )

    print("="*70)



    return final







__all__=[

    "run"

]
