# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

strategies.py

动态策略模块

负责:

1. 状态策略
2. 权重调整
3. 特征增强
4. 属性预测


"""


from collections import Counter


from .features import (

    get_wave,

    get_size,

    get_parity

)





# =====================================================
# 基础策略权重
# =====================================================


BASE_WEIGHTS = {


    "frequency":0.20,


    "trend":0.15,


    "momentum":0.12,


    "omission":0.10,


    "wave":0.10,


    "size":0.08,


    "parity":0.08,


    "zodiac":0.07,


    "zone":0.05,


    "tail":0.05

}





# =====================================================
# 状态策略
# =====================================================


def state_strategy(state):


    weights=BASE_WEIGHTS.copy()



    if state=="连续波状态":


        weights["wave"] += 0.08

        weights["trend"] += 0.05



    elif state=="波色反转状态":


        weights["momentum"] += 0.08

        weights["wave"] += 0.03



    elif state=="集中趋势状态":


        weights["frequency"] += 0.08

        weights["trend"] += 0.06



    elif state=="趋势变化状态":


        weights["trend"] += 0.10

        weights["momentum"] += 0.05



    elif state=="混沌状态":


        weights["frequency"] -= 0.05

        weights["trend"] -= 0.05

        weights["omission"] += 0.10



    return normalize(weights)





# =====================================================
# 权重归一化
# =====================================================


def normalize(data):


    total=sum(

        data.values()

    )



    if total<=0:

        return data



    return {


        k:

        round(

            v/total,

            4

        )

        for k,v in data.items()

    }





# =====================================================
# 热冷号码策略
# =====================================================


def hot_cold_strategy(numbers):


    recent=numbers[:50]


    counter=Counter(

        recent

    )



    hot=[]

    cold=[]



    for n in range(1,50):


        c=counter.get(

            n,

            0

        )



        if c>=3:


            hot.append(n)


        elif c==0:


            cold.append(n)



    return {


        "hot":

        hot,


        "cold":

        cold

    }





# =====================================================
# 波色策略
# =====================================================


def wave_strategy(numbers):


    counter=Counter()



    for n in numbers[:50]:


        counter[

            get_wave(n)

        ]+=1



    ranking=counter.most_common()



    return {


        "single":

        ranking[0][0]

        if ranking

        else None,


        "double":

        [

            x[0]

            for x in ranking[:2]

        ]

    }





# =====================================================
# 大小策略
# =====================================================


def size_strategy(numbers):


    counter=Counter()



    for n in numbers[:50]:


        counter[

            get_size(n)

        ]+=1



    total=sum(

        counter.values()

    )



    if total==0:

        return {}



    return {


        k:

        round(

            v/total,

            4

        )

        for k,v in counter.items()

    }





# =====================================================
# 单双策略
# =====================================================


def parity_strategy(numbers):


    counter=Counter()



    for n in numbers[:50]:


        counter[

            get_parity(n)

        ]+=1



    total=sum(

        counter.values()

    )



    return {


        k:

        round(

            v/total,

            4

        )

        for k,v in counter.items()

    }





# =====================================================
# 号码增强
# =====================================================


def enhance_score(

        scores,

        strategy

):


    result=scores.copy()



    hot=strategy.get(

        "hot",

        []

    )



    cold=strategy.get(

        "cold",

        []

    )



    for n in hot:


        if n in result:


            result[n]*=1.08



    for n in cold:


        if n in result:


            result[n]*=0.95



    return result





# =====================================================
# 完整策略输出
# =====================================================


def build_strategy(

        numbers,

        state="平衡状态"

):


    return {


        "state":

        state,


        "weights":

        state_strategy(

            state

        ),



        "hot_cold":

        hot_cold_strategy(

            numbers

        ),



        "wave":

        wave_strategy(

            numbers

        ),



        "size":

        size_strategy(

            numbers

        ),



        "parity":

        parity_strategy(

            numbers

        )

    }





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    nums=[

        39,41,8,9,7,14,49

    ]*20



    print(

        build_strategy(

            nums

        )

    )
