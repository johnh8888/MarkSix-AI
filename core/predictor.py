# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统

core/predictor.py

V8.0 QUANT STATE SWITCH


功能:

1. 热冷分析
2. Markov趋势
3. 状态切换
4. 熵调整
5. 动态权重


"""


from __future__ import annotations


from collections import Counter
from datetime import datetime
import random



from .state_engine import analyze_state





# =====================================================
# 属性
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







# =====================================================
# 热冷评分
# =====================================================


def hot_score(history):


    nums=[

        x["special"]

        for x in history

    ]


    counter=Counter(nums)



    scores={}



    for n in range(1,50):


        freq=counter.get(

            n,

            0

        )


        scores[n]=freq



    return scores







# =====================================================
# Markov趋势
# =====================================================


def markov_score(history):


    scores={

        i:0

        for i in range(1,50)

    }



    nums=[

        x["special"]

        for x in history

    ]



    if len(nums)<2:

        return scores



    last=nums[0]



    for i,n in enumerate(nums[1:]):


        if n==last:

            scores[n]+=1


        last=n



    return scores







# =====================================================
# V8预测
# =====================================================


def predict_next(history):



    if not history:


        return {

            "error":

            "无数据"

        }




    # 状态

    state=analyze_state(

        history

    )



    weights=state[

        "动态权重"

    ]





    hot=hot_score(

        history

    )



    markov=markov_score(

        history

    )





    scores={}





    # =====================
    # 综合评分
    # =====================


    for n in range(1,50):


        scores[n]=(


            hot[n]

            *

            weights["hot"]


            +

            markov[n]

            *

            weights["markov"]


            +

            random.random()

            *

            weights["random"]


        )





    # =====================
    # 熵高降趋势
    # =====================


    if state["状态"]=="混沌状态":


        for n in scores:


            scores[n]*=0.85





    ranked=sorted(

        scores,

        key=scores.get,

        reverse=True

    )



    top10=ranked[:10]



    top3=top10[:3]



    first=top3[0]





    result={


        "版本":

        "V8.0 QUANT STATE SWITCH",



        "市场状态":

        state,



        "特码10码":

        top10,



        "重点3码":

        top3,



        "第一推荐":

        first,



        "属性":

        {


            "波色":

            get_wave(first),



            "大小":

            get_size(first),



            "单双":

            get_oe(first)


        },



        "评分":{


            str(k):

            round(scores[k],3)

            for k in top10

        },



        "时间":

        datetime.now().isoformat()


    }



    return result







__all__=[

"predict_next"

]
