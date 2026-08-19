# -*- coding:utf-8 -*-

"""
六合彩 AI V3.7 FINAL PRO

智能预测核心

融合:

历史频率
🔥热号
❄冷号
遗漏
Markov
趋势
概率评分


"""


from collections import Counter


from .features import (

    hot_numbers,

    cold_numbers,

    missing_count,

    feature_statistics

)


from .wave import predict_wave

from .zodiac import get_zodiac


try:

    from .markov import markov_predict

except:

    markov_predict=lambda x:[]



try:

    from .hmm import detect_state

except:

    detect_state=lambda x:{"状态":"未启用"}






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


        "历史数量":

        count,


        "等级":

        level

    }





# =====================================================
# 概率融合评分
# =====================================================


def fusion_score(history):


    scores={}


    nums=[

        x["special"]

        for x in history

    ]


    freq=Counter(nums)



    hot=set(

        hot_numbers(history)

    )


    cold=set(

        cold_numbers(history)

    )


    miss=missing_count(history)



    recent=set(

        nums[-20:]

    )




    for n in range(1,50):


        score=0



        # -----------------
        # 历史概率
        # -----------------

        score += freq[n] * 1.5




        # -----------------
        # 热号
        # -----------------

        if n in hot:

            score += 10




        # -----------------
        # 冷号补偿
        # -----------------

        if n in cold:

            score += 5




        # -----------------
        # 遗漏周期
        # -----------------

        score += min(

            miss[n] / 10,

            8

        )





        # -----------------
        # 最近活跃
        # -----------------

        if n in recent:

            score += 3




        scores[n]=round(

            score,

            2

        )



    return scores







# =====================================================
# 百分比转换
# =====================================================


def percent_score(

        ranking

):


    total=sum(

        x[1]

        for x in ranking

    )



    result={}



    for n,s in ranking:


        if total:


            result[n]=round(

                s /

                total *

                100,

                2

            )


        else:

            result[n]=0



    return result






# =====================================================
# 推荐理由
# =====================================================


def reason(

        n,

        history

):


    result=[]


    if n in hot_numbers(history):


        result.append(

            "🔥近期热号"

        )



    if n in cold_numbers(history):


        result.append(

            "❄遗漏补偿"

        )



    miss=missing_count(history).get(

        n,

        0

    )


    if miss>20:


        result.append(

            "遗漏周期偏高"

        )



    if not result:


        result.append(

            "综合模型评分"

        )


    return result







# =====================================================
# 主预测
# =====================================================


def predict(history):


    if not history:


        return {


            "error":

            "无历史数据"

        }




    ranking=sorted(

        fusion_score(history).items(),

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




    percent=percent_score(

        ranking

    )




    confidence=[]


    for n in top3:


        confidence.append(

            {


            "号码":

            n,


            "概率":

            percent[n],


            "理由":

            reason(

                n,

                history

            )

            }

        )






    return {


        "模型版本":

        "V3.7 FINAL PRO",



        "数据质量":

        data_quality(history),



        "🎯推荐3码":

        top3,



        "⭐10码范围":

        top10,



        "🔥热号":

        hot_numbers(history),



        "❄冷号":

        cold_numbers(history),



        "AI综合评分":

        confidence,



        "📈趋势":

        feature_statistics(history)[

            "📈趋势"

        ],



        "🎯推荐理由":

        confidence,



        "波色":

        predict_wave(history),



        "生肖":

        [

            get_zodiac(x)

            for x in top3

        ],



        "马尔可夫":

        markov_predict(history)[0:5],



        "当前状态":

        detect_state(history)


    }





__all__=[

    "predict"

]
