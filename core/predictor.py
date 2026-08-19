# -*- coding:utf-8 -*-

"""
六合彩 AI V3.3 FINAL

智能预测核心

功能:

1. 历史评分
2. 热冷分析
3. 遗漏补偿
4. Markov预测
5. HMM状态
6. 波色预测
7. 生肖预测
8. 大小预测
9. 单双预测
10. 置信度分析
11. 风险等级

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
# 号码评分
# =====================================================


def score_numbers(history):


    scores={}



    freq=Counter(

        x["special"]

        for x in history

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



        # 历史频率

        score += freq[n]



        # 遗漏补偿

        if n not in recent30:

            score += 2


        else:

            score -= 0.5



        # 最近热度

        if n in recent10:

            score += 3



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
# 大小预测
# =====================================================


def predict_size(numbers):


    big=0

    small=0



    for n in numbers:


        if n>=25:

            big+=1


        else:

            small+=1



    total=len(numbers)



    if total==0:

        return {}



    return {


        "大概率":

            round(
                big/total,
                3
            ),



        "小概率":

            round(
                small/total,
                3
            ),



        "推荐":

            "大"

            if big>=small

            else

            "小"

    }





# =====================================================
# 单双预测
# =====================================================


def predict_odd_even(numbers):


    odd=0

    even=0



    for n in numbers:


        if n%2:

            odd+=1

        else:

            even+=1



    total=len(numbers)



    if total==0:

        return {}



    return {


        "单概率":

            round(
                odd/total,
                3
            ),



        "双概率":

            round(
                even/total,
                3
            ),



        "推荐":

            "单"

            if odd>=even

            else

            "双"

    }





# =====================================================
# 置信度
# =====================================================


def confidence(scores):


    values=sorted(

        scores.values(),

        reverse=True

    )


    if len(values)<2:

        return 0



    gap=values[0]-values[1]



    result=round(

        min(

            gap/10,

            1

        ),

        3

    )


    return result





# =====================================================
# 风险等级
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

                "无历史数据"

        }




    quality=data_quality(history)



    scores=score_numbers(history)




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





    # Markov


    if len(history)>=20:


        markov=markov_predict(history)


    else:

        markov=[]





    # HMM


    if len(history)>=50:


        state=detect_state(history)


    else:


        state={

            "状态":

                "数据不足"

        }






    conf=confidence(scores)





    return {



        "模型版本":

            "V3.3 FINAL",



        "数据质量":

            quality,



        "模型状态":

            model_status(history),



        "当前状态":

            state,



        "特码10码":

            top10,



        "重点3码":

            top3,



        "第一推荐":

            top3[0],



        "波色":

            predict_wave(history),



        "生肖":

            [

                get_zodiac(x)

                for x in top3

            ],



        "大小":

            predict_size(top10),



        "单双":

            predict_odd_even(top10),



        "置信度":

            conf,



        "风险等级":

            risk_level(conf),



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
