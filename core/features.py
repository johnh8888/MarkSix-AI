# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/features.py

特征工程模块

功能：

1. 高频统计
2. 遗漏统计
3. 最近趋势
4. 波色特征
5. 大小单双特征
6. 综合评分

输出：

号码 -> 特征评分


注意：
评分不是中奖概率
只是模型排序依据

"""


from __future__ import annotations


from collections import Counter


from typing import List, Dict





NUMBERS=list(range(1,50))



RED={
1,2,7,8,12,13,18,19,
23,24,29,30,34,35,
40,45,46
}


BLUE={
3,4,9,10,14,15,
20,25,26,31,
36,37,41,42,47,48
}


GREEN={
5,6,11,16,17,
21,22,27,28,
32,33,38,39,43,44,49
}





# =====================================================
# 基础属性
# =====================================================


def get_wave(n):

    if n in RED:
        return "红"

    if n in BLUE:
        return "蓝"

    if n in GREEN:
        return "绿"

    return "未知"





def get_size(n):

    return "大" if n>=25 else "小"





def get_parity(n):

    return "单" if n%2 else "双"





# =====================================================
# 频率
# =====================================================


def frequency_score(history):


    count=Counter(
        history[:120]
    )


    total=max(
        1,
        len(history[:120])
    )


    return {

        n:
        count[n]/total

        for n in NUMBERS

    }






# =====================================================
# 遗漏
# =====================================================


def omission_score(history):


    result={}



    for n in NUMBERS:


        miss=120


        for i,x in enumerate(history):

            if x==n:

                miss=i

                break



        result[n]=min(
            miss,
            120
        )/120



    return result





# =====================================================
# 最近趋势
# =====================================================


def trend_score(history):


    short=Counter(
        history[:12]
    )


    medium=Counter(
        history[:36]
    )


    result={}



    for n in NUMBERS:


        result[n]=(

            short[n]*0.6

            +

            medium[n]*0.4

        )



    maxv=max(
        result.values()
    )



    if maxv==0:

        return result



    return {

        n:v/maxv

        for n,v in result.items()

    }





# =====================================================
# 属性评分
# =====================================================


def attribute_score(history,n):


    score=0



    recent=history[:36]



    wave=get_wave(n)

    size=get_size(n)

    parity=get_parity(n)



    for x in recent:


        if get_wave(x)==wave:

            score+=0.4



        if get_size(x)==size:

            score+=0.3



        if get_parity(x)==parity:

            score+=0.3



    return score/max(
        1,
        len(recent)
    )





# =====================================================
# 综合特征
# =====================================================


def build_feature_score(

        history:List[int]

)->Dict[int,float]:


    if not history:


        return {}



    freq=frequency_score(
        history
    )


    omit=omission_score(
        history
    )


    trend=trend_score(
        history
    )



    result={}



    for n in NUMBERS:


        result[n]=(


            freq[n]*0.35


            +


            omit[n]*0.15


            +


            trend[n]*0.30


            +


            attribute_score(
                history,
                n
            )*0.20


        )



    return result





# =====================================================
# 兼容接口
# =====================================================


def extract_features(history):

    return build_feature_score(
        history
    )





__all__=[

"build_feature_score",

"extract_features"

]
