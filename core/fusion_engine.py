# -*- coding:utf-8 -*-

"""
六合彩 AI V3.8 FINAL

模型融合引擎

功能:

1. 多模型评分
2. 动态权重
3. 状态调整
4. 置信度


"""


from math import log2



# =====================================================
# 权重
# =====================================================


def model_weights(history):


    size=len(history)



    if size>=500:


        return {


            "frequency":

            0.25,


            "trend":

            0.20,


            "markov":

            0.20,


            "state":

            0.20,


            "balance":

            0.15

        }



    elif size>=100:


        return {


            "frequency":

            0.35,


            "trend":

            0.25,


            "markov":

            0.15,


            "state":

            0.15,


            "balance":

            0.10

        }



    else:


        return {


            "frequency":

            0.60,


            "trend":

            0.20,


            "markov":

            0,


            "state":

            0.10,


            "balance":

            0.10

        }





# =====================================================
# 熵计算
# =====================================================


def entropy(values):


    total=sum(values)


    if total==0:

        return 0



    result=0



    for x in values:


        p=x/total


        if p>0:

            result-=p*log2(p)



    return round(
        result,
        4
    )





# =====================================================
# 市场混乱度
# =====================================================


def market_entropy(history):


    nums=[

        x["special"]

        for x in history

    ]



    count=[0]*49



    for n in nums:


        count[n-1]+=1



    return entropy(count)





# =====================================================
# 融合评分
# =====================================================


def fusion_score(

        base_scores,

        history,

        markov=None,

        state=None

):



    weights=model_weights(
        history
    )



    result={}



    entropy_value=market_entropy(
        history
    )



    for n,score in base_scores.items():



        value=0



        # 基础模型

        value += (

            score *

            weights["frequency"]

        )



        # 趋势

        if n in [

            x["special"]

            for x in history[-20:]

        ]:


            value += (

                5 *

                weights["trend"]

            )




        # 状态调整

        if entropy_value<5:


            value += (

                2 *

                weights["state"]

            )



        else:


            value -= (

                1 *

                weights["state"]

            )




        result[n]=round(

            value,

            4

        )



    return {


        "scores":

        result,


        "weights":

        weights,


        "entropy":

        entropy_value

    }




# =====================================================
# 置信度
# =====================================================


def confidence(ranking):


    if len(ranking)<3:

        return 0



    first=ranking[0][1]


    second=ranking[1][1]



    gap=first-second



    value=min(

        gap/10,

        1

    )



    return round(

        value,

        3

    )



__all__=[

"fusion_score",

"confidence",

"model_weights"

]
