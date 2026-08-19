# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

Walk Forward 回测模块

功能:

历史滚动验证
预测命中统计
模型评估

"""


from .predictor import predict





# =====================================================
# 单次命中
# =====================================================


def check_hit(prediction, actual):


    result={}


    top10 = prediction.get(

        "特码10码",

        []

    )


    top3 = prediction.get(

        "重点3码",

        []

    )



    special = actual.get(

        "special"

    )



    result["特码10码命中"] = (

        special in top10

    )



    result["重点3码命中"] = (

        special in top3

    )



    return result





# =====================================================
# Walk Forward
# =====================================================


def walk_forward(

        history,

        min_train=30,

        step=1

):


    total=len(history)



    if total < min_train + 1:


        return {


            "状态":

            "数据不足",


            "历史数量":

            total

        }





    total_test=0


    hit10=0


    hit3=0




    start=min_train




    while start < total:



        train=history[:start]


        test=history[start]




        try:


            prediction=predict(

                train

            )



            hit=check_hit(

                prediction,

                test

            )



            total_test +=1



            if hit["特码10码命中"]:


                hit10 +=1



            if hit["重点3码命中"]:


                hit3 +=1





        except Exception as e:


            print(

                "回测错误:",

                e

            )



        start += step






    if total_test==0:


        return {


            "状态":

            "无测试数据"

        }




    return {


        "状态":

        "完成",



        "测试次数":

        total_test,



        "特码10码命中":

        hit10,



        "重点3码命中":

        hit3,



        "特码10码准确率":

        round(

            hit10 / total_test,

            4

        ),



        "重点3码准确率":

        round(

            hit3 / total_test,

            4

        )

    }





__all__=[

    "walk_forward"

]
