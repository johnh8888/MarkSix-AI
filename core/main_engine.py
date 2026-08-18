# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.0 FINAL

core/main_engine.py

系统总入口

流程:

API同步
 ↓
SQLite
 ↓
历史数据
 ↓
状态分析
 ↓
预测
 ↓
Walk Forward
 ↓
JSON输出

"""


from __future__ import annotations


import json

from datetime import datetime

from pathlib import Path





# =====================================================
# 核心模块
# =====================================================


from .sqlite_manager import (
    init_database,
    load_history
)



from .api_sync import (
    sync_all
)



from .predictor import (
    predict_next
)



try:

    from .backtest import (
        walk_forward
    )

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
# 中文标题
# =====================================================


def show_title():

    print()

    print("="*70)

    print(
        "        六合 AI 智能预测系统 V5.0 FINAL"
    )

    print()

    print(
        "  API真实数据 + SQLite数据库"
    )

    print()

    print(
        "  状态识别 + 贝叶斯融合 + 动态策略"
    )

    print()

    print(
        "  Walk-Forward 防过拟合回测"
    )

    print()

    print(
        datetime.now()
    )

    print("="*70)






# =====================================================
# 单彩种分析
# =====================================================


def analyze_lottery(
        key:str
):


    name=LOTTERIES[key]


    print()

    print("#"*70)

    print(
        "分析:",
        name
    )

    print("#"*70)




    history=load_history(key)



    if not history:


        return {

            "error":

            "暂无历史数据"

        }





    print(
        "历史期数:",
        len(history)
    )



    # -----------------------------
    # 提取特码
    # -----------------------------


    specials=[]


    for row in history:


        if isinstance(row,dict):

            if "special" in row:

                specials.append(
                    int(row["special"])
                )



    if not specials:


        #兼容旧数据库

        specials=history





    prediction=predict_next(
        specials
    )



    result={

        "彩种":
        name,


        "生成时间":
        datetime.now().isoformat(),


        "预测":
        prediction,


        "历史数量":
        len(history)

    }




    # -----------------------------
    # 回测
    # -----------------------------


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
# 保存JSON
# =====================================================


def save_json(
        filename,
        data
):


    path=OUTPUT_DIR/filename



    path.write_text(

        json.dumps(

            data,

            ensure_ascii=False,

            indent=2

        ),

        encoding="utf-8"

    )


    print(
        "保存:",
        path
    )



    return path






# =====================================================
# 主运行函数
# =====================================================


def run():


    show_title()



    # ----------------------------------
    # 1 数据库
    # ----------------------------------


    print()

    print(
        "【1】初始化数据库"
    )


    init_database()


    print(
        "数据库完成"
    )





    # ----------------------------------
    # 2 API同步
    # ----------------------------------


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

            "error":
            str(e)

        }






    # ----------------------------------
    # 3预测
    # ----------------------------------


    print()

    print(
        "【3】开始预测"
    )



    all_result={}



    for key in LOTTERIES:


        try:


            all_result[key]=analyze_lottery(
                key
            )


        except Exception as e:


            print(
                key,
                "失败:",
                e
            )


            all_result[key]={

                "error":
                str(e)

            }







    # ----------------------------------
    # 输出
    # ----------------------------------


    final={


        "版本":

        "V5.0 FINAL",



        "时间":

        datetime.now().isoformat(),



        "同步":

        sync_result,



        "结果":

        all_result

    }



    save_json(

        "prediction.json",

        final

    )



    print()

    print("="*70)

    print(
        "V5运行完成"
    )

    print("="*70)



    return final






__all__=[

    "run"

]
