# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/state.py

市场状态基础模型

"""


from __future__ import annotations


from collections import Counter
import math





# =====================================================
# 熵计算
# =====================================================


def entropy(values):

    if not values:

        return 0



    counter=Counter(values)


    total=len(values)


    h=0


    for c in counter.values():

        p=c/total

        h-=p*math.log(
            p,
            2
        )


    return h





# =====================================================
# 分布
# =====================================================


def distribution(values):


    counter=Counter(values)


    total=max(
        1,
        len(values)
    )


    return {

        k:

        round(
            v/total,
            4
        )

        for k,v

        in counter.items()

    }






# =====================================================
# 状态计算
# =====================================================


def analyze_state(history):


    recent=history[:12]


    medium=history[:36]



    if len(recent)<5:

        return {

            "state":
            "数据不足"

        }



    recent_entropy=entropy(
        recent
    )


    medium_entropy=entropy(
        medium
    )



    gap=(

        medium_entropy

        -

        recent_entropy

    )





    if recent_entropy < 2.5:


        state="偏态"



    elif abs(gap)>0.8:


        state="转换"



    else:


        state="平衡"





    return {


        "state":

        state,


        "recent_entropy":

        round(
            recent_entropy,
            4
        ),


        "medium_entropy":

        round(
            medium_entropy,
            4
        ),


        "entropy_gap":

        round(
            gap,
            4
        )


    }






__all__=[

"analyze_state",

"entropy",

"distribution"

]
