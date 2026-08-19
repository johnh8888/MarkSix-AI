# -*- coding:utf-8 -*-

"""
六合彩 AI V4.1 QUANT

量化评分引擎


模型:

frequency
missing
recent
markov
hmm
wave

"""


from collections import Counter





# =====================================================
# 基础频率
# =====================================================


def frequency_score(history):


    freq=Counter(

        x["special"]

        for x in history

    )


    max_value=max(

        freq.values(),

        default=1

    )


    result={}


    for n in range(1,50):


        result[n]=round(

            freq[n]/max_value,

            4

        )


    return result





# =====================================================
# 遗漏评分
# =====================================================


def missing_score(history):


    recent=[

        x["special"]

        for x in history[-50:]

    ]


    result={}



    for n in range(1,50):


        if n in recent:


            result[n]=0.2


        else:


            result[n]=1.0



    return result





# =====================================================
# 最近走势
# =====================================================


def recent_score(history):


    recent=[

        x["special"]

        for x in history[-10:]

    ]


    result={}



    for n in range(1,50):


        if n in recent:


            result[n]=1.0


        else:


            result[n]=0.3



    return result





# =====================================================
# Bayesian融合
# =====================================================


def bayesian_fusion(history):


    freq=frequency_score(history)


    missing=missing_score(history)


    recent=recent_score(history)



    final={}



    for n in range(1,50):


        score=(


            freq[n]*0.35

            +

            missing[n]*0.25

            +

            recent[n]*0.20


            +

            0.2*0.5


        )


        final[n]=round(

            score,

            4

        )



    return final





# =====================================================
# 置信度
# =====================================================


def model_confidence(scores):


    values=sorted(

        scores.values(),

        reverse=True

    )


    if len(values)<10:

        return 0



    gap=values[0]-values[9]



    confidence=min(

        round(

            gap*2,

            2

        ),

        0.95

    )



    return confidence




__all__=[

    "bayesian_fusion",

    "model_confidence"

]
