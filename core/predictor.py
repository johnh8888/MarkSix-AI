# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

智能预测核心

功能:

历史评分
频率模型
遗漏模型
Markov
HMM状态
波色
生肖

"""


from collections import Counter


from .wave import predict_wave

from .zodiac import get_zodiac

from .markov import markov_predict

from .hmm import detect_state





# =====================================================
# 数据质量
# =====================================================


def data_quality(history):


    count=len(history)



    if count>=500:


        level="优秀"



    elif count>=100:


        level="良好"



    elif count>=30:


        level="一般"



    else:


        level="不足"



    return {


        "数量":

        count,


        "等级":

        level



    }






# =====================================================
# 特码评分
# =====================================================


def score_numbers(history):


    scores={}



    freq=Counter(


        x["special"]

        for x in history

    )




    recent=[


        x["special"]

        for x in history[-30:]

    ]




    for n in range(1,50):


        score=0



        # 历史频率

        score += freq[n]*1.0




        # 遗漏补偿


        if n not in recent:


            score+=1.5



        else:


            score-=0.5





        # 最近热度


        recent10=[


            x["special"]

            for x in history[-10:]

        ]



        if n in recent10:


            score+=2





        scores[n]=round(

            score,

            3

        )



    return scores






# =====================================================
# 模型状态
# =====================================================


def model_status(history):


    size=len(history)



    return {


        "历史数据":

        size,



        "Markov":

        "启用"

        if size>=20

        else

        "等待数据",



        "HMM":

        "启用"

        if size>=50

        else

        "等待数据",



        "高级模型":

        "启用"

        if size>=100

        else

        "等待数据"

    }





# =====================================================
# 主预测
# =====================================================


def predict(history):


    if not history:


        return {


            "error":

            "无历史数据"

        }




    quality=data_quality(

        history

    )



    scores=score_numbers(

        history

    )




    ranking=sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )





    top10=[


        x[0]

        for x in ranking[:10]

    ]




    top3=[


        x[0]

        for x in ranking[:3]

    ]





    # -------------------------
    # Markov
    # -------------------------


    if len(history)>=20:


        markov=markov_predict(

            history

        )


    else:


        markov=[]





    # -------------------------
    # HMM
    # -------------------------


    if len(history)>=50:


        state=detect_state(

            history

        )


    else:


        state={

            "状态":

            "数据不足"

        }





    return {



        "模型版本":

        "V3.2 FINAL",



        "数据质量":

        quality,



        "模型状态":

        model_status(

            history

        ),



        "当前状态":

        state,



        "特码10码":

        top10,



        "重点3码":

        top3,



        "第一推荐":

        top3[0],



        "波色":

        predict_wave(

            history

        ),



        "生肖":

        [

            get_zodiac(x)

            for x in top3

        ],



        "马尔可夫":

        markov[:5],



        "评分":

        {


            str(k):

            v

            for k,v in ranking[:10]

        }

    }





__all__=[

    "predict"

]
