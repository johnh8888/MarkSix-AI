# -*- coding:utf-8 -*-

"""
六合彩 AI V3.6 FINAL

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

预测

 ↓

报告输出


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



from .quality import (

    analyze_quality

)



from .features import (

    feature_statistics

)



from .backtest import (

    walk_forward

)



from .report import (

    generate_reports

)





# =====================================================
# JSON输出
# =====================================================


def save_json(data):


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
# 显示摘要
# =====================================================


def show_summary(

        name,

        result

):


    print()

    print(

        "🎲",

        name

    )

    print(

        "-"*50

    )



    print(

        "🎯 推荐3码:",

        result.get(

            "🎯推荐3码",

            []

        )

    )



    print(

        "⭐ 10码范围:",

        result.get(

            "⭐10码范围",

            []

        )

    )



    print()




    print(

        "🔥 热号:",

        result.get(

            "🔥热号",

            []

        )

    )


    print(

        "❄ 冷号:",

        result.get(

            "❄冷号",

            []

        )

    )


    print()



    print(

        "📈 趋势:"

    )


    trend=result.get(

        "📈趋势",

        {}

    )


    for k,v in trend.items():

        print(

            " ",

            k,

            ":",

            v

        )



    print()


    print(

        "🎯 推荐理由:"

    )


    for r in result.get(

        "🎯推荐理由",

        []

    ):


        if isinstance(

            r,

            dict

        ):


            print(

                " ",

                r.get(

                    "号码"

                ),

                ":",

                " / ".join(

                    r.get(

                        "理由",

                        []

                    )

                )

            )



    print()







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



    if not history:


        return {


            "彩种":

            name,


            "error":

            "无历史数据"

        }




    result=predict(

        history

    )



    result["彩种"]=name



    result["历史数量"]=len(history)



    result["数据质量"]=analyze_quality(

        history

    )



    result["特征统计"]=feature_statistics(

        history

    )



    result["回测"]=walk_forward(

        history

    )




    # 立即显示

    show_summary(

        name,

        result

    )



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

        "六合彩 AI V3.6 FINAL"

    )


    print(

        datetime.now()

    )


    print(

        "="*70

    )





    # 数据库


    print()

    print(

        "【1】初始化数据库"

    )


    init_database()



    print(

        "数据库完成"

    )






    # API


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








    # 预测


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





    final={


        "版本":

        "V3.6 FINAL",



        "系统":

        "六合彩 AI V3.6 FINAL",



        "时间":

        datetime.now().isoformat(),



        "同步":

        sync_result,



        "预测":

        results


    }





    save_json(

        final

    )



    generate_reports(

        final

    )





    print()

    print(

        "="*70

    )


    print(

        "V3.6 FINAL运行完成"

    )


    print(

        "="*70

    )



    return final





__all__=[

    "run_system"

]
