# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

main_engine.py

系统总控制器


流程:

1. 初始化数据库
2. 同步数据
3. 数据质量检查
4. 状态分析
5. 动态策略
6. 预测
7. 回测
8. 保存


"""


import json

from datetime import datetime


from .config import *


from .database import (

    init_database,

    save_history,

    load_history

)


from .data_source import (

    fetch_history,

    fetch_latest

)


from .data_quality import (

    quality_report

)


from .state_engine import (

    analyze_state

)


from .strategies import (

    build_strategy

)


from .predictor import (

    predict_next

)


from .backtest import (

    walk_forward_test

)





# =====================================================
# 数据同步
# =====================================================


def sync_data():


    print("="*70)

    print("开始同步数据")

    print("="*70)



    history=fetch_history()



    total=0



    for code,rows in history.items():


        print(

            "同步:",

            LOTTERY_CODES.get(

                code,

                code

            )

        )



        count=save_history(

            code,

            rows

        )



        print(

            "新增:",

            count

        )


        total+=count



    return total





# =====================================================
# 分析单彩种
# =====================================================


def analyze_lottery(code):


    print()

    print("#"*70)

    print(

        "分析:",

        LOTTERY_CODES[code]

    )

    print("#"*70)



    history=load_history(

        code

    )



    if len(history)<MIN_HISTORY:


        print(

            "历史数据不足"

        )


        return None





    numbers=[]



    for row in history:


        numbers.extend(

            row["numbers"]

        )





    # 状态


    state=analyze_state(

        numbers

    )



    print(

        "市场状态:",

        state

    )





    # 策略


    strategy=build_strategy(

        numbers,

        state

    )





    # 预测


    prediction=predict_next(

        history,

        strategy

    )





    # 回测


    backtest=walk_forward_test(

        history

    )





    result={


        "code":

        code,


        "name":

        LOTTERY_CODES[code],


        "time":

        datetime.now().isoformat(),



        "state":

        state,



        "strategy":

        strategy,



        "prediction":

        prediction,



        "backtest":

        backtest

    }



    return result





# =====================================================
# 保存
# =====================================================


def save_json(

        filename,

        data

):


    with open(

        filename,

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            data,

            f,

            ensure_ascii=False,

            indent=2

        )





# =====================================================
# 主运行
# =====================================================


def run():


    print("="*70)

    print(

        "六合彩AI智能预测系统 V4.0"

    )

    print(

        datetime.now()

    )

    print("="*70)





    # 初始化数据库


    init_database()





    # 同步


    sync_data()





    results=[]



    for code in LOTTERY_CODES:


        result=analyze_lottery(

            code

        )


        if result:


            results.append(

                result

            )





    # 保存预测


    save_json(

        PREDICTION_FILE,

        results

    )



    print()

    print(

        "预测保存完成:",

        PREDICTION_FILE

    )





    # 回测


    all_backtest={


        x["code"]:

        x["backtest"]

        for x in results

    }



    save_json(

        BACKTEST_FILE,

        all_backtest

    )



    print(

        "回测保存完成:",

        BACKTEST_FILE

    )





    print("="*70)

    print(

        "V4.0运行完成"

    )

    print("="*70)



    return results





if __name__=="__main__":


    run()
