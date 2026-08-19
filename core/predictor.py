# -*- coding:utf-8 -*-

"""
六合彩 AI V4.1 QUANT FINAL

智能预测核心

模型:

Bayesian Fusion
Frequency
Missing
Recent
Markov
HMM
Wave
Size
OddEven

"""


from .quant import (

    bayesian_fusion,

    model_confidence

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


    elif count>=300:

        level="良好"


    elif count>=100:

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
# 大小
# =====================================================


def analyze_size(history):


    big=sum(

        1

        for x in history

        if x["special"]>=25

    )


    small=len(history)-big



    total=max(

        len(history),

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


def analyze_even(history):


    odd=sum(

        1

        for x in history

        if x["special"]%2

    )


    even=len(history)-odd



    total=max(

        len(history),

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
# 风险
# =====================================================


def risk(conf):


    if conf>=0.7:

        return "低风险"


    if conf>=0.4:

        return "中风险"


    return "高风险"







# =====================================================
# 主预测
# =====================================================


def predict(history):


    if not history:


        return {


            "错误":

            "没有历史数据"

        }



    # ======================
    # Bayesian评分
    # ======================


    scores=bayesian_fusion(

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





    # ======================
    # Markov
    # ======================


    if len(history)>=20:


        markov=markov_predict(

            history

        )


    else:

        markov=[]





    # ======================
    # HMM
    # ======================


    if len(history)>=50:


        hmm=detect_state(

            history

        )


    else:


        hmm={

            "状态":

            "数据不足"

        }





    # ======================
    # 信心
    # ======================


    confidence=model_confidence(

        scores

    )






    return {



        "模型版本":

        "V4.1 QUANT FINAL",



        "数据质量":

        data_quality(

            history

        ),



        "重点3码":

        top3,



        "特码10码":

        top10,



        "第一推荐":

        top3[0],



        "生肖":

        [

            get_zodiac(x)

            for x in top3

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

        analyze_even(

            history

        ),



        "AI信心":

        confidence,



        "风险":

        risk(

            confidence

        ),



        "HMM状态":

        hmm,



        "Markov":

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
