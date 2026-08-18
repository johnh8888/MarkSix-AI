# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统

core/backtest.py

V7.1 BACKTEST FINAL

支持:

V5旧格式
V6属性格式
V7状态引擎格式

"""


from __future__ import annotations



from .predictor import predict_next






# =====================================================
# 属性兼容读取
# =====================================================


def get_attribute(
        prediction,
        key
):


    """
    兼容:

    V5:
        prediction["大小"]

    V6/V7:
        prediction["属性"]["大小"]

    """


    # 新格式

    attr = prediction.get(
        "属性",
        {}
    )


    if key in attr:

        return attr[key]



    # 旧格式

    return prediction.get(
        key
    )







# =====================================================
# 特码判断
# =====================================================


def hit_number(

        nums,

        target

):


    return target in nums







# =====================================================
# 大小
# =====================================================


def check_size(
        number
):


    return (

        "大"

        if number >=25

        else

        "小"

    )






# =====================================================
# 单双
# =====================================================


def check_oe(
        number
):


    return (

        "单"

        if number %2

        else

        "双"

    )







# =====================================================
# 波色
# =====================================================


RED={

1,2,7,8,12,13,
18,19,23,24,
29,30,34,35,
40,45,46

}



BLUE={

3,4,9,10,
14,15,20,
25,26,31,
36,37,41,
42,47,48

}



def check_wave(
        n
):


    if n in RED:

        return "红"


    if n in BLUE:

        return "蓝"


    return "绿"







# =====================================================
# 单次预测回测
# =====================================================


def evaluate(

        history,

        test_size=20

):


    result={



        "测试期数":

        test_size,



        "有效测试":

        0,



        "特码10码":

        {

            "total":0,

            "hit":0,

            "rate":0

        },



        "大小":

        {

            "total":0,

            "hit":0,

            "rate":0

        },



        "单双":

        {

            "total":0,

            "hit":0,

            "rate":0

        },



        "波色":

        {

            "total":0,

            "hit":0,

            "rate":0

        }



    }




    if len(history)<=test_size:

        return result







    # 最近多少期测试


    tests = history[:test_size]



    train = history[test_size:]





    for i,target in enumerate(tests):


        try:


            prediction = predict_next(

                train

            )



            result["有效测试"] +=1




            # =====================
            # 特码
            # =====================


            numbers = prediction.get(

                "特码10码",

                []

            )



            result["特码10码"]["total"] +=1



            if hit_number(

                numbers,

                target

            ):


                result["特码10码"]["hit"] +=1






            # =====================
            # 大小
            # =====================


            pred_size=get_attribute(

                prediction,

                "大小"

            )



            if pred_size:


                result["大小"]["total"] +=1



                if pred_size == check_size(target):


                    result["大小"]["hit"] +=1






            # =====================
            # 单双
            # =====================


            pred_oe=get_attribute(

                prediction,

                "单双"

            )



            if pred_oe:


                result["单双"]["total"] +=1



                if pred_oe == check_oe(target):


                    result["单双"]["hit"] +=1






            # =====================
            # 波色
            # =====================


            pred_wave=get_attribute(

                prediction,

                "波色"

            )



            if pred_wave:


                result["波色"]["total"] +=1



                if pred_wave == check_wave(target):


                    result["波色"]["hit"] +=1





            # 下一期加入训练

            train=[target]+train





        except Exception as e:


            print(
                "回测异常:",
                e
            )






    # =====================
    # 计算比例
    # =====================


    for key in [

        "特码10码",

        "大小",

        "单双",

        "波色"

    ]:


        total=result[key]["total"]


        hit=result[key]["hit"]



        if total:


            result[key]["rate"]=round(

                hit/total,

                3

            )



    return result







# =====================================================
# 外部接口
# =====================================================


def walk_forward(

        history,

        test_size=20

):


    return evaluate(

        history,

        test_size

    )





__all__=[

    "walk_forward"

]
