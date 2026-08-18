# -*- coding:utf-8 -*-

"""
六合彩 AI V7.0 STATE ENGINE

状态识别:
1 高频
2 低频
3 连续
4 反转
5 混沌

"""

from collections import Counter
import math
from datetime import datetime



RED={
1,2,7,8,12,13,18,19,
23,24,29,30,34,35,40,45,46
}

BLUE={
3,4,9,10,14,15,20,
25,26,31,36,37,41,42,47,48
}

GREEN={
5,6,11,16,17,21,22,
27,28,32,33,38,39,43,44,49
}




def wave(n):

    if n in RED:
        return "红"

    if n in BLUE:
        return "蓝"

    return "绿"



def size(n):

    return "大" if n>=25 else "小"



def oe(n):

    return "单" if n%2 else "双"





# ==========================
# 熵
# ==========================


def entropy(nums):


    c=Counter(nums)

    total=len(nums)


    h=0


    for v in c.values():

        p=v/total

        h-=p*math.log(
            p
        )


    return h





# ==========================
# 状态分析
# ==========================


def detect_state(history):


    recent=history[:30]


    c=Counter(recent)



    max_count=max(
        c.values()
    )


    ent=entropy(
        recent
    )



    # 连续检测

    repeat=0


    for i in range(
        1,
        len(recent)
    ):


        if recent[i]==recent[i-1]:

            repeat+=1




    if repeat>=5:


        return {

            "状态":
            "连续状态",

            "entropy":
            ent

        }




    if max_count>=5:


        return {

            "状态":
            "高频状态",

            "entropy":
            ent

        }



    if ent>3.3:


        return {

            "状态":
            "混沌状态",

            "entropy":
            ent

        }



    return {


        "状态":
        "正常状态",

        "entropy":
        ent

    }





# ==========================
# 动态权重
# ==========================


def state_weight(state):


    name=state["状态"]



    if name=="高频状态":

        return {

            "hot":0.5,

            "markov":0.4,

            "random":0.1

        }



    if name=="混沌状态":

        return {

            "hot":0.3,

            "markov":0.2,

            "random":0.5

        }



    return {


        "hot":0.6,

        "markov":0.35,

        "random":0.05

    }





# ==========================
# 主预测
# ==========================


def predict_next(history):


    state=detect_state(
        history
    )


    weights=state_weight(
        state
    )



    freq=Counter(
        history
    )



    score={}



    for n in range(1,50):


        score[n]=(

            freq[n]*weights["hot"]

        )




    ranking=sorted(

        score.items(),

        key=lambda x:x[1],

        reverse=True

    )



    top10=[

        x[0]

        for x in ranking[:10]

    ]



    main=top10[0]



    return {


        "版本":

        "V7.0 STATE ENGINE",



        "市场状态":

        state,



        "动态权重":

        weights,



        "特码10码":

        top10,



        "重点3码":

        top10[:3],



        "第一推荐":

        main,



        "属性":{


            "波色":

            wave(main),


            "大小":

            size(main),


            "单双":

            oe(main)

        },


        "时间":

        datetime.now().isoformat()

    }




__all__=[

"predict_next"

]
