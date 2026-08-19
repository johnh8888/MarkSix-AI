# -*- coding:utf-8 -*-

"""
六合彩 AI V3.4 QUANT FINAL

智能预测核心


模型:

1. 历史频率
2. 遗漏补偿
3. 最近趋势
4. 热冷平衡
5. 波色趋势
6. Markov
7. HMM状态


输出:

第一推荐
重点3码
特码10码
置信度
AI评分

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


    elif count>=200:

        level="良好"


    elif count>=50:

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
# 号码评分
# =====================================================


def score_numbers(history):


    scores={}


    values=[

        x["special"]

        for x in history

    ]


    freq=Counter(values)



    recent30=set(values[-30:])


    recent10=set(values[-10:])



    for n in range(1,50):


        score=0



        # 历史热度

        score += freq[n]*0.8



        # 最近出现

        if n in recent10:

            score += 4


        elif n in recent30:

            score += 2



        # 遗漏

        if n not in recent30:

            score += 2



        # 频率修正

        avg=len(values)/49



        if freq[n] < avg:

            score += 1



        scores[n]=round(
            score,
            3
        )



    return scores






# =====================================================
# 置信度计算
# =====================================================


def confidence_score(history,ranking):


    size=len(history)


    if size<50:

        base=0.15


    elif size<200:

        base=0.35


    else:

        base=0.5



    if ranking:


        diff=(

            ranking[0][1]

            -

            ranking[1][1]

        )


        base += min(

            diff/20,

            0.25

        )



    if base>0.85:

        base=0.85


    return round(
        base,
        2
    )






# =====================================================
# 大小分析
# =====================================================


def predict_size(history):


    big=0

    small=0



    for row in history:


        n=row["special"]


        if n>=25:

            big+=1

        else:

            small+=1



    total=big+small



    if total==0:

        return {}



    bp=big/total

    sp=small/total



    return {


        "大概率":
            round(bp,3),


        "小概率":
            round(sp,3),


        "推荐":

            "大"

            if bp>sp

            else

            "小"

    }







# =====================================================
# 单双分析
# =====================================================


def predict_odd_even(history):


    odd=0

    even=0



    for row in history:


        if row["special"]%2:

            odd+=1

        else:

            even+=1



    total=odd+even



    if total==0:

        return {}



    op=odd/total

    ep=even/total



    return {


        "单概率":
            round(op,3),


        "双概率":
            round(ep,3),


        "推荐":

            "单"

            if op>ep

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

            "无历史数据"

        }



    quality=data_quality(history)



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



    confidence=confidence_score(

        history,

        ranking

    )



    result={



        "模型版本":

            "V3.4 QUANT FINAL",



        "数据质量":

            quality,



        "模型状态":{


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



        "第一推荐":

            top3[0],



        "重点3码":

            top3,



        "特码10码":

            top10,



        "波色":

            predict_wave(history),



        "大小":

            predict_size(history),



        "单双":

            predict_odd_even(history),



        "生肖":

            [

                get_zodiac(x)

                for x in top3

            ],



        "置信度":

            confidence,



        "AI评分":

            int(confidence*100),



        "风险等级":

            "低"

            if confidence>=0.7

            else

            "中"

            if confidence>=0.4

            else

            "高"

    }





    if len(history)>=20:


        result["马尔可夫"]=markov_predict(

            history

        )[:5]


    else:


        result["马尔可夫"]=[]



    if len(history)>=50:


        result["状态"]=detect_state(

            history

        )


    else:


        result["状态"]={

            "状态":

            "数据不足"

        }



    return result





__all__=[

    "predict"

]
