# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

Walk Forward 回测
"""


from .predictor import predict





def walk_forward(history,window=20):


    if len(history)<window+5:


        return {


            "状态":

            "数据不足"

        }



    total=0

    hit=0



    for i in range(

        window,

        len(history)

    ):


        train=history[:i]


        test=history[i]


        result=predict(

            train

        )


        nums=result.get(

            "特码10码",

            []

        )


        total+=1



        if test["special"] in nums:

            hit+=1




    return {


        "测试次数":

        total,


        "命中":

        hit,


        "命中率":

        round(

            hit/total,

            4

        )

    }
