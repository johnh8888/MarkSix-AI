# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

strategies.py

10模型融合策略

"""


from collections import Counter


from .features import (

    get_special,

    get_wave,

)


from .state_engine import get_weights





# =====================================================
# 通用归一化
# =====================================================


def normalize(scores):


    if not scores:

        return {
            i:0.5
            for i in range(1,50)
        }


    values=list(
        scores.values()
    )


    low=min(values)

    high=max(values)



    if high==low:

        return {
            k:0.5
            for k in scores
        }


    return {


        k:

        (v-low)/(high-low)


        for k,v in scores.items()

    }





# =====================================================
# 1 频率模型
# =====================================================


def model_frequency(rows):


    counter=Counter()



    for row in rows[:100]:


        n=get_special(row)


        if n:

            counter[n]+=1



    return normalize(

        {

        n:

        counter.get(n,0)

        for n in range(1,50)

        }

    )





# =====================================================
# 2 趋势模型
# =====================================================


def model_trend(rows):


    score={}



    for n in range(1,50):

        s=0


        for i,row in enumerate(rows[:50]):


            if get_special(row)==n:


                s+=50-i



        score[n]=s



    return normalize(score)





# =====================================================
# 3 动量模型
# =====================================================


def model_momentum(rows):


    score={}



    recent=[]


    for row in rows[:20]:

        n=get_special(row)

        if n:

            recent.append(n)



    for n in range(1,50):


        score[n]=recent.count(n)*2



    return normalize(score)





# =====================================================
# 4 遗漏模型
# =====================================================


def model_omission(rows):


    score={}



    for n in range(1,50):


        miss=0


        for row in rows:


            if get_special(row)==n:

                break


            miss+=1



        score[n]=miss



    return normalize(score)





# =====================================================
# 5 邻号模型
# =====================================================


def model_adjacency(rows):


    score={

        n:0

        for n in range(1,50)

    }



    for row in rows[:100]:


        n=get_special(row)


        if not n:

            continue



        for x in (

            n-1,

            n+1

        ):


            if 1<=x<=49:

                score[x]+=1



    return normalize(score)





# =====================================================
# 6 尾数模型
# =====================================================


def model_tail(rows):


    tails=Counter()



    for row in rows[:100]:

        n=get_special(row)

        if n:

            tails[n%10]+=1



    score={}



    for n in range(1,50):


        score[n]=tails[n%10]



    return normalize(score)





# =====================================================
# 7 分区模型
# =====================================================


def model_zone(rows):


    zones=Counter()



    for row in rows[:100]:


        n=get_special(row)


        if n:


            zones[
                (n-1)//10
            ]+=1



    score={}



    for n in range(1,50):


        score[n]=zones[
            (n-1)//10
        ]



    return normalize(score)





# =====================================================
# 8 大小
# =====================================================


def model_size(rows):


    big=0

    small=0



    for row in rows[:100]:


        n=get_special(row)


        if n>=25:

            big+=1

        elif n:

            small+=1



    total=big+small


    if total==0:

        return {
            n:0.5
            for n in range(1,50)
        }



    return {


        n:

        (
            big/total
            if n>=25
            else
            small/total
        )


        for n in range(1,50)

    }





# =====================================================
# 9 单双
# =====================================================


def model_parity(rows):


    odd=0

    even=0



    for row in rows[:100]:


        n=get_special(row)


        if n:


            if n%2:

                odd+=1

            else:

                even+=1



    total=odd+even


    if total==0:

        return {
            n:0.5
            for n in range(1,50)
        }



    return {


        n:

        (
            odd/total
            if n%2
            else even/total
        )


        for n in range(1,50)

    }





# =====================================================
# 10 波色
# =====================================================


def model_wave(rows):


    counter=Counter()



    for row in rows[:100]:


        n=get_special(row)


        if n:

            counter[
                get_wave(n)
            ]+=1



    total=sum(
        counter.values()
    )


    score={}



    for n in range(1,50):


        if total:


            score[n]=counter[
                get_wave(n)
            ]/total


        else:

            score[n]=0.5



    return score





# =====================================================
# 主融合
# =====================================================


def combine_models(rows):


    models={


        "frequency":

            model_frequency(rows),


        "trend":

            model_trend(rows),


        "momentum":

            model_momentum(rows),


        "omission":

            model_omission(rows),


        "adjacency":

            model_adjacency(rows),


        "tail":

            model_tail(rows),


        "zone":

            model_zone(rows),


        "size":

            model_size(rows),


        "parity":

            model_parity(rows),


        "wave":

            model_wave(rows),

    }



    weights=get_weights(rows)



    final={

        n:0

        for n in range(1,50)

    }



    for name,data in models.items():


        w=weights.get(
            name,
            0
        )


        for n in range(1,50):


            final[n]+=data[n]*w



    final=normalize(final)



    return final,models,weights
