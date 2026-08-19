# -*- coding:utf-8 -*-

"""
六合彩 AI V3.5 FINAL

智能预测核心

新增:

🔥 热号分析
❄ 冷号分析
📈 趋势分析
🎯 推荐理由

保留:

频率模型
遗漏模型
Markov
HMM
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

        "数量":count,

        "等级":level

    }







# =====================================================
# 号码频率
# =====================================================


def number_frequency(history):


    counter=Counter()


    for row in history:


        n=row.get(
            "special"
        )


        if n:

            counter[n]+=1



    return counter







# =====================================================
# 热号
# =====================================================


def hot_numbers(history):


    recent=history[-50:]


    counter=number_frequency(
        recent
    )


    ranking=sorted(

        counter.items(),

        key=lambda x:x[1],

        reverse=True

    )


    return [

        x[0]

        for x in ranking[:5]

    ]








# =====================================================
# 冷号
# =====================================================


def cold_numbers(history):


    last_seen={}



    for index,row in enumerate(history):


        n=row.get(
            "special"
        )


        if n:

            last_seen[n]=index





    result=[]


    length=len(history)



    for n in range(1,50):


        miss=length-last_seen.get(

            n,

            -1

        )


        result.append(

            (

                n,

                miss

            )

        )



    result.sort(

        key=lambda x:x[1],

        reverse=True

    )



    return [

        x[0]

        for x in result[:5]

    ]








# =====================================================
# 评分模型
# =====================================================


def score_numbers(history):


    scores={}


    freq=number_frequency(
        history
    )



    hot=hot_numbers(
        history
    )



    cold=cold_numbers(
        history
    )



    for n in range(1,50):


        score=0



        # 历史频率

        score += freq[n]*1.0



        # 热号加权

        if n in hot:

            score += 5



        # 冷号补偿

        if n in cold:

            score += 2



        scores[n]=round(

            score,

            2

        )



    return scores







# =====================================================
# 趋势分析
# =====================================================


def trend_analysis(history):


    if len(history)<10:


        return "数据不足"



    recent=[

        x["special"]

        for x in history[-10:]

    ]



    avg=sum(recent)/len(recent)



    if avg>=25:


        return "近期偏大号趋势"



    else:


        return "近期偏小号趋势"








# =====================================================
# 推荐理由
# =====================================================


def build_reason(history,number):


    reasons=[]


    if len(history)>=100:

        reasons.append(
            "历史数据充足"
        )



    if number in hot_numbers(history):

        reasons.append(
            "近期热号支持"
        )



    if number in cold_numbers(history):

        reasons.append(
            "遗漏补偿"
        )



    reasons.append(

        "综合评分最高"

    )



    return reasons








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




    markov=[]


    if len(history)>=20:


        markov=markov_predict(
            history
        )





    state={

        "状态":

        "数据不足"

    }


    if len(history)>=50:


        state=detect_state(
            history
        )






    first=top3[0]



    return {


        "模型版本":

        "V3.5 FINAL",



        "历史数量":

        len(history),



        "第一推荐":

        first,



        "重点3码":

        top3,



        "特码10码":

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

        trend_analysis(
            history
        ),



        "🎯推荐理由":

        build_reason(
            history,
            first
        ),



        "波色":

        predict_wave(
            history
        ),



        "生肖":

        [

            get_zodiac(x)

            for x in top3

        ],



        "当前状态":

        state,



        "马尔可夫":

        markov[:5],



        "置信度":

        min(

            0.8,

            len(history)/1000

        ),



        "风险等级":

        "中风险"

        if len(history)>=300

        else

        "高风险"



    }





__all__=[

    "predict"

]
