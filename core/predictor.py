# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统

core/predictor.py

V8.0 QUANT STATE SWITCH

"""


from collections import Counter
from datetime import datetime
import random



from .state_engine import analyze_state




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





def normalize(history):


    nums=[]


    for x in history:


        if isinstance(x,dict):

            nums.append(
                int(x["special"])
            )


        else:

            nums.append(
                int(x)
            )


    return nums







def get_wave(n):


    if n in RED:

        return "红"


    if n in BLUE:

        return "蓝"


    return "绿"






def get_size(n):


    return (

        "大"

        if n>=25

        else

        "小"

    )






def get_oe(n):


    return (

        "单"

        if n%2

        else

        "双"

    )








def hot_score(numbers):


    c=Counter(numbers)


    result={}


    for n in range(1,50):

        result[n]=c.get(
            n,
            0
        )


    return result








def markov_score(numbers):


    result={

        i:0

        for i in range(1,50)

    }



    if len(numbers)<2:

        return result




    last=numbers[0]



    for n in numbers[1:]:


        if n==last:

            result[n]+=1


        last=n



    return result








def predict_next(history):


    numbers=normalize(
        history
    )


    if not numbers:


        return {

            "error":
            "无数据"

        }





    state=analyze_state(

        numbers

    )



    weights=state[
        "动态权重"
    ]



    hot=hot_score(
        numbers
    )


    markov=markov_score(
        numbers
    )



    scores={}





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





    return {


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



        "属性":{


            "波色":

            get_wave(first),



            "大小":

            get_size(first),



            "单双":

            get_oe(first)

        },



        "评分":{


            str(n):

            round(scores[n],3)

            for n in top10

        },



        "时间":

        datetime.now().isoformat()

    }





__all__=[

    "predict_next"

]
