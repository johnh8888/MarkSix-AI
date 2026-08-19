# -*- coding:utf-8 -*-

"""
六合彩 AI V3.6 FINAL

智能预测核心

融合:

1. 历史频率
2. 最近趋势
3. 遗漏补偿
4. 热冷分析
5. 波色趋势
6. Markov
7. HMM状态


输出:

推荐号码
热号
冷号
趋势
理由

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


    n=len(history)


    if n>=500:

        level="优秀"

    elif n>=100:

        level="良好"

    elif n>=30:

        level="一般"

    else:

        level="不足"



    return {

        "数量":n,

        "等级":level

    }



# =====================================================
# 评分模型
# =====================================================


def score_numbers(history):


    scores={}


    all_nums=[

        x["special"]

        for x in history

    ]



    freq=Counter(
        all_nums
    )



    recent30=[

        x["special"]

        for x in history[-30:]

    ]



    recent10=[

        x["special"]

        for x in history[-10:]

    ]



    for n in range(1,50):


        score=0



        # -----------------
        # 历史频率
        # -----------------

        score += freq[n]*0.25



        # -----------------
        # 最近趋势
        # -----------------

        if n in recent30:

            score+=3



        if n in recent10:

            score+=5



        # -----------------
        # 遗漏补偿
        # -----------------

        miss=0


        for x in reversed(all_nums):

            if x==n:

                break

            miss+=1



        if miss>=20:

            score+=4


        elif miss>=10:

            score+=2



        # -----------------
        # 热冷平衡
        # -----------------

        if freq[n]>=10:

            score+=2


        if freq[n]<=3:

            score+=1



        scores[n]=round(
            score,
            3
        )



    return scores



# =====================================================
# 大小
# =====================================================


def size_predict(scores):


    big=0
    small=0


    for n,s in scores.items():


        if n>=25:

            big+=s

        else:

            small+=s



    total=big+small


    return {

        "大概率":
        round(big/total,3),


        "小概率":
        round(small/total,3),


        "推荐":

        "大"
        if big>small
        else
        "小"

    }



# =====================================================
# 单双
# =====================================================


def odd_even_predict(scores):


    odd=0
    even=0


    for n,s in scores.items():


        if n%2:

            odd+=s

        else:

            even+=s



    total=odd+even


    return {

        "单概率":
        round(odd/total,3),


        "双概率":
        round(even/total,3),


        "推荐":

        "单"
        if odd>even
        else
        "双"

    }



# =====================================================
# 主预测
# =====================================================


def predict(history):


    if not history:

        return {

            "error":
            "无数据"

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

        n

        for n,s in ranking[:10]

    ]



    top3=[

        n

        for n,s in ranking[:3]

    ]



    # Markov

    markov=[]


    if len(history)>=20:

        markov=markov_predict(
            history
        )



    # HMM

    state={}


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

        "V3.6 FINAL",



        "数据质量":

        data_quality(history),



        "模型状态":

        {

        "历史数据":
        len(history),


        "Markov":
        "启用"
        if len(history)>=20
        else
        "等待",


        "HMM":
        "启用"
        if len(history)>=50
        else
        "等待"

        },



        "当前状态":

        state,



        "特码10码":

        top10,



        "重点3码":

        top3,



        "第一推荐":

        top3[0],



        "评分":

        {

            str(k):v

            for k,v in ranking

        },



        "波色":

        predict_wave(history),



        "大小":

        size_predict(scores),



        "单双":

        odd_even_predict(scores),



        "生肖":

        [

            get_zodiac(x)

            for x in top3

        ],



        "马尔可夫":

        markov[:5]

    }



__all__=[

    "predict"

]
