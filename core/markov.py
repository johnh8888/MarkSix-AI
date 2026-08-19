# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

Markov状态预测模块


支持:

特码状态
波色状态
大小状态
单双状态


"""


from collections import defaultdict, Counter



from .features import (

    extract_draw_feature

)





# =====================================================
# 构造状态链
# =====================================================


def build_chain(

        history,

        key="special"

):


    chain=defaultdict(

        Counter

    )



    states=[]



    for row in history:


        if key=="special":


            value=row.get(

                "special"

            )



        else:


            feature=extract_draw_feature(

                row

            )


            value=feature.get(

                key

            )





        if value is not None:


            states.append(

                value

            )





    for i in range(

        len(states)-1

    ):


        current=states[i]


        nxt=states[i+1]



        chain[current][nxt]+=1




    return chain





# =====================================================
# 概率计算
# =====================================================


def transition_probability(

        chain,

        current

):


    counter=chain.get(

        current,

        {}

    )



    if not counter:


        return {}




    total=sum(

        counter.values()

    )



    result={}



    for k,v in counter.items():


        result[k]=round(

            v/total,

            4

        )



    return result






# =====================================================
# Markov预测
# =====================================================


def markov_predict(

        history,

        key="special"

):


    if len(history)<5:


        return []





    chain=build_chain(

        history,

        key

    )



    if not chain:


        return []




    features=[]



    if key=="special":


        current=history[-1].get(

            "special"

        )



    else:


        current=extract_draw_feature(

            history[-1]

        ).get(

            key

        )




    probs=transition_probability(

        chain,

        current

    )



    if not probs:


        return []




    ranking=sorted(

        probs.items(),

        key=lambda x:x[1],

        reverse=True

    )



    return ranking







# =====================================================
# 多状态预测
# =====================================================


def markov_all(history):


    return {


        "特码":

        markov_predict(

            history,

            "special"

        ),



        "波色":

        markov_predict(

            history,

            "wave"

        ),



        "大小":

        markov_predict(

            history,

            "size"

        ),



        "单双":

        markov_predict(

            history,

            "odd_even"

        )

    }





__all__=[

    "markov_predict",

    "markov_all",

    "build_chain"

]
