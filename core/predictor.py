# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

预测核心

"""


from collections import Counter



from .wave import predict_wave

from .zodiac import get_zodiac

from .markov import markov_predict

from .hmm import detect_state





def score_numbers(history):


    scores={}



    freq=Counter(

        x["special"]

        for x in history

    )



    for n in range(1,50):


        score=0



        # 历史频率

        score += freq[n]*1.0



        # 遗漏补偿

        recent=[

            x["special"]

            for x in history[-20:]

        ]


        if n not in recent:

            score +=0.5



        scores[n]=round(

            score,

            3

        )



    return scores





def predict(history):


    if not history:


        return {

            "error":

            "无历史数据"

        }



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





    markov=markov_predict(

        history

    )



    state=detect_state(

        history

    )



    return {


        "模型版本":

        "V3.0 FINAL",



        "状态":

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
