# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

backtest.py

Walk-Forward回测模块

"""


from collections import defaultdict


from .predictor import predict_all


from .features import (

    get_special,

    get_wave,

    get_zodiac,

)





# =====================================================
# 初始化结果
# =====================================================


def init_result():


    return {


        "count":0,


        "special10":0,


        "zodiac5":0,


        "flat2":0,


        "size":0,


        "parity":0,


        "wave_single":0,


        "wave_double":0,



    }





# =====================================================
# 百分比
# =====================================================


def percent(a,b):


    if b==0:

        return 0


    return round(

        a/b*100,

        2

    )





# =====================================================
# 单次验证
# =====================================================


def check_prediction(
        prediction,
        actual
):


    result={}


    # -----------------
    # 特码10码
    # -----------------

    special10=prediction["special10"]


    result["special10"]= (

        actual in special10

    )



    # -----------------
    # 生肖
    # -----------------

    zodiac=get_zodiac(actual)


    result["zodiac5"]=(

        zodiac

        in prediction["zodiac5"]

    )


    result["flat2"]=(

        zodiac

        in prediction["flat_zodiac2"]

    )



    # -----------------
    # 大小
    # -----------------

    size="大" if actual>=25 else "小"


    result["size"]=(

        size

        ==
        prediction["size"]["recommend"]

    )



    # -----------------
    # 单双
    # -----------------

    parity="单" if actual%2 else "双"


    result["parity"]=(

        parity

        ==
        prediction["parity"]["recommend"]

    )



    # -----------------
    # 波色
    # -----------------

    wave=get_wave(actual)



    result["wave_single"]=(

        wave

        ==
        prediction["wave"]["single"]

    )


    result["wave_double"]=(

        wave

        in prediction["wave"]["double"]

    )


    return result





# =====================================================
# Walk Forward
# =====================================================


def walk_forward(
        rows,
        test_size=20,
        name="unknown"
):


    if len(rows)<50:


        return {


            "error":

            "数据不足"

        }



    result=init_result()



    module_score=defaultdict(
        lambda:[0,0]
    )



    # 保证时间顺序

    rows=list(
        rows
    )



    rows=rows[::-1]



    start=len(rows)-test_size



    for i in range(
        start,
        len(rows)
    ):



        train=rows[:i]


        target=rows[i]



        if not train:

            continue



        prediction=predict_all(

            train,

            name

        )



        actual=get_special(
            target
        )



        if not actual:

            continue



        check=check_prediction(

            prediction,

            actual

        )



        result["count"]+=1



        for k,v in check.items():


            if v:

                result[k]+=1



            module_score[k][1]+=1



            if v:

                module_score[k][0]+=1




    # 百分比


    output={



        "name":

        name,



        "test_count":

        result["count"],



        "accuracy":{


            k:

            percent(v,result["count"])


            for k,v in result.items()

            if k!="count"

        },



        "module_score":{


            k:

            percent(v[0],v[1])


            for k,v in module_score.items()

        }



    }



    return output





# =====================================================
# 打印
# =====================================================


def print_backtest(data):


    print("="*70)

    print(

        data.get(
            "name",
            ""
        ),

        "Walk-Forward回测"

    )

    print("="*70)



    print(

        "有效测试期数:",

        data.get(
            "test_count"
        )

    )



    for k,v in data["accuracy"].items():


        print(

            f"{k:<15}",

            f"{v}%"

        )





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    demo=[


        {

        "numbers":

        "38,26,08,06,29,18,23"

        }

    ]


    r=walk_forward(

        demo,

        10,

        "测试"

    )


    print(r)
