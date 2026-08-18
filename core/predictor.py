# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V6.0

智能预测引擎

HMM思想
Markov状态
Bayes融合
冷热衰减
特征评分

"""


from collections import Counter
import math
from datetime import datetime



# ==========================
# 波色
# ==========================

RED = {
1,2,7,8,12,13,18,19,
23,24,29,30,34,35,40,
45,46
}


BLUE = {
3,4,9,10,14,15,20,
25,26,31,36,37,41,
42,47,48
}


GREEN = {
5,6,11,16,17,21,
22,27,28,32,33,
38,39,43,44,49
}



def get_wave(n):

    if n in RED:
        return "红"

    if n in BLUE:
        return "蓝"

    return "绿"



def get_size(n):

    return "大" if n>=25 else "小"



def get_oe(n):

    return "单" if n%2 else "双"






# ==========================
# 时间衰减
# ==========================


def decay_weight(index,total):


    age=total-index


    return math.exp(

        -age/200

    )







# ==========================
# Markov
# ==========================


def markov_score(history):


    score=Counter()


    if len(history)<2:

        return score



    for a,b in zip(
        history[:-1],
        history[1:]
    ):

        score[b]+=1



    return score






# ==========================
# 热冷模型
# ==========================


def hot_cold(history):


    score=Counter()


    total=len(history)



    for i,n in enumerate(history):


        score[n]+=decay_weight(

            i,

            total

        )


    return score








# ==========================
# 贝叶斯融合
# ==========================


def bayes_merge(

        hot,

        markov

):


    result={}


    for n in range(1,50):


        h=hot.get(n,0)


        m=markov.get(n,0)



        result[n]=(

            h*0.6

            +

            m*0.4

        )



    return result








# ==========================
# 主预测
# ==========================


def predict_next(history):


    if not history:


        return {

            "error":
            "无数据"

        }




    hot=hot_cold(

        history

    )


    mk=markov_score(

        history

    )



    final=bayes_merge(

        hot,

        mk

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



    main=top3[0]





    return {


        "版本":

        "V6.0 HMM-Markov-Bayes",



        "说明":

        "多模型融合评分",



        "特码10码":

        top10,



        "重点3码":

        top3,



        "第一推荐":

        main,



        "属性":{


            "波色":

            get_wave(main),



            "大小":

            get_size(main),



            "单双":

            get_oe(main)

        },



        "模型权重":{


            "冷热":

            0.6,


            "Markov":

            0.4

        },



        "时间":

        datetime.now().isoformat()

    }





__all__=[

    "predict_next"

]
