# -*- coding:utf-8 -*-

"""
六合彩 AI V3.6 FINAL

智能预测核心

功能:

🔥 热号评分
❄ 冷号补偿
📈 趋势分析
Markov
HMM
波色
生肖
AI推荐理由

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


        "历史数量":

        count,


        "等级":

        level


    }





# =====================================================
# AI评分模型
# =====================================================


def score_numbers(history):


    scores={}


    nums=[

        x["special"]

        for x in history

    ]



    freq=Counter(nums)


    hot=hot_numbers(history)


    cold=cold_numbers(history)


    missing=missing_count(history)





    for n in range(1,50):


        score=0



        # 历史频率

        score += freq[n]*1.2



        # 热号奖励

        if n in hot:

            score += 8



        # 冷号遗漏补偿

        if n in cold:

            score += 3



        # 遗漏周期

        score += min(

            missing.get(n,0)/20,

            5

        )



        # 最近出现降低

        if nums[-5:].count(n):

            score-=2




        scores[n]=round(

            score,

            2

        )



    return scores





# =====================================================
# 推荐理由
# =====================================================


def build_reason(

        number,

        history

):


    reasons=[]



    hot=hot_numbers(history)


    cold=cold_numbers(history)


    missing=missing_count(history)



    if number in hot:


        reasons.append(

            "🔥近期热度提升"

        )



    if number in cold:


        reasons.append(

            "❄遗漏周期补偿"

        )



    if missing.get(number,0)>20:


        reasons.append(

            "遗漏超过平均周期"

        )



    if not reasons:


        reasons.append(

            "综合评分最高"

        )



    return reasons







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

        "等待",



        "HMM":

        "启用"

        if size>=50

        else

        "等待",



        "高级模型":

        "启用"

        if size>=100

        else

        "等待"


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





    if len(history)>=20:


        markov=markov_predict(

            history

        )


    else:


        markov=[]





    if len(history)>=50:


        state=detect_state(

            history

        )


    else:


        state={

            "状态":

            "数据不足"

        }





    reasons=[]



    for n in top3:


        reasons.append(

            {

                "号码":

                n,


                "理由":

                build_reason(

                    n,

                    history

                )

            }

        )





    return {


        "模型版本":

        "V3.6 FINAL",



        "数据质量":

        data_quality(

            history

        ),



        "模型状态":

        model_status(

            history

        ),



        "当前状态":

        state,



        "🎯推荐3码":

        top3,



        "⭐10码范围":

        top10,



        "🔥热号":

        hot_numbers(

            history

        ),



        "❄冷号":

        cold_numbers(

            history

        ),



        "📈趋势":

        feature_statistics(

            history

        )["📈趋势"],



        "🎯推荐理由":

        reasons,



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
