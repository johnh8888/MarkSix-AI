# -*- coding: utf-8 -*-

"""
六合AI V10.0 FINAL

预测核心

HMM + Markov + Bayes结构接口
"""

import math
import random
from collections import Counter

from .zodiac import (
    get_zodiac,
    get_5_zodiac
)



# ==========================
# 波色
# ==========================

RED={
1,2,7,8,12,13,18,19,
23,24,29,30,34,35,
40,45,46
}


BLUE={
3,4,9,10,14,15,
20,25,26,31,36,
37,41,42,47,48
}


GREEN={
5,6,11,16,17,
21,22,27,28,32,
33,38,39,43,44,49
}



def get_color(n):

    if n in RED:
        return "红"

    if n in BLUE:
        return "蓝"

    if n in GREEN:
        return "绿"

    return "未知"




def get_size(n):

    return (
        "大"
        if n>=25
        else
        "小"
    )




def get_even(n):

    return (
        "单"
        if n%2
        else
        "双"
    )





# ==========================
# 熵
# ==========================

def entropy(numbers):

    if not numbers:

        return 0


    c=Counter(numbers)


    total=sum(c.values())


    e=0


    for v in c.values():

        p=v/total

        e-=p*math.log2(p)



    return round(e,4)




# ==========================
# 热度模型
# ==========================

def hot_score(history):

    nums=[]


    for h in history:

        nums.extend(h)



    count=Counter(nums)



    result={}


    for i in range(1,50):

        result[i]=count[i]


    return result




# ==========================
# Markov简单模型
# ==========================

def markov_score(history):


    score={
        i:0
        for i in range(1,50)
    }


    for row in history:


        if row:

            last=row[-1]

            for n in range(1,50):

                distance=abs(
                    n-last
                )


                score[n]+=(
                    1/
                    (distance+1)
                )


    return score





# ==========================
# 主预测
# ==========================

def predict_next(
    history,
    lottery=""
):


    if not history:

        raise ValueError(
            "没有读取到历史号码"
        )



    hot=hot_score(
        history
    )


    markov=markov_score(
        history
    )



    final={}



    for n in range(1,50):


        final[n]=round(

            hot[n]*0.6

            +

            markov[n]*0.4,

            3

        )



    ranking=sorted(

        final.items(),

        key=lambda x:x[1],

        reverse=True

    )



    top10=[

        x[0]

        for x in ranking[:10]

    ]


    top3=top10[:3]


    first=top3[0]



    state={

        "状态":
        (
            "混沌状态"
            if entropy(
                top10
            )>3.5

            else

            "正常状态"
        ),

        "entropy":
        entropy(top10)

    }




    result={


        "版本":

        "V10.0 FINAL",



        "市场状态":

        state,



        "特码10码":

        top10,



        "重点3码":

        top3,



        "第一推荐":

        first,



        "生肖5肖":

        get_5_zodiac(
            top10
        ),



        "属性":

        {

            "波色":

            get_color(first),


            "大小":

            get_size(first),


            "单双":

            get_even(first)

        },



        "评分":

        dict(
            ranking[:10]
        )

    }



    return result
