# -*- coding:utf-8 -*-

"""
六合彩 AI V4.0 FINAL

智能预测核心

升级:

1. 综合评分模型
2. 热冷分析
3. 波色融合
4. 大小单双
5. AI信心
6. 风险评估

"""


from collections import Counter


from .score import number_score

from .wave import predict_wave

from .zodiac import get_zodiac

from .markov import markov_predict

from .hmm import detect_state




# =====================================================
# 数据质量
# =====================================================


def data_quality(history):


    total=len(history)



    if total>=500:

        level="优秀"


    elif total>=300:

        level="良好"


    elif total>=100:

        level="一般"


    else:

        level="不足"



    return {


        "历史数量":

        total,


        "等级":

        level


    }





# =====================================================
# 大小分析
# =====================================================


def analyze_size(history):


    big=0

    small=0



    for x in history:


        n=x["special"]


        if n>=25:

            big+=1

        else:

            small+=1



    total=max(
        big+small,
        1
    )



    big_p=round(
        big/total,
        3
    )


    small_p=round(
        small/total,
        3
    )



    return {


        "大概率":

        big_p,


        "小概率":

        small_p,


        "推荐":

        "大"
        if big_p>small_p
        else
        "小"


    }




# =====================================================
# 单双
# =====================================================


def analyze_odd_even(history):


    odd=0

    even=0



    for x in history:


        if x["special"]%2:

            odd+=1

        else:

            even+=1



    total=max(
        odd+even,
        1
    )



    odd_p=round(
        odd/total,
        3
    )


    even_p=round(
        even/total,
        3
    )



    return {


        "单概率":

        odd_p,


        "双概率":

        even_p,


        "推荐":

        "单"
        if odd_p>even_p
        else
        "双"


    }





# =====================================================
# AI信心
# =====================================================


def confidence(history,scores):


    if len(history)<50:

        return 0.15



    values=sorted(

        scores.values(),

        reverse=True

    )



    diff=values[0]-values[9]



    c=min(

        round(
            diff/50,
            2
        ),

        0.95

    )


    return c





# =====================================================
# 风险
# =====================================================


def risk_level(conf):


    if conf>=0.7:

        return "低风险"


    elif conf>=0.4:

        return "中风险"


    else:

        return "高风险"





# =====================================================
# 主预测
# =====================================================


def predict(history):


    if not history:


        return {


            "错误":

            "没有数据"


        }



    scores=number_score(
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



    # markov

    if len(history)>=20:


        markov=markov_predict(
            history
        )

    else:

        markov=[]



    # HMM

    if len(history)>=50:


        state=detect_state(
            history
        )


    else:


        state={

            "状态":

            "数据不足"

        }





    conf=confidence(

        history,

        scores

    )





    return {


        "模型版本":

        "V4.0 FINAL",



        "数据质量":

        data_quality(
            history
        ),



        "当前状态":

        state,



        "重点3码":

        top3,



        "特码10码":

        top10,



        "第一推荐":

        top3[0],



        "生肖":

        [

            get_zodiac(n)

            for n in top3

        ],



        "波色":

        predict_wave(
            history
        ),



        "大小":

        analyze_size(
            history
        ),



        "单双":

        analyze_odd_even(
            history
        ),



        "置信度":

        conf,



        "风险等级":

        risk_level(
            conf
        ),



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
