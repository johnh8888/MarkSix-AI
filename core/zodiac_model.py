# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/zodiac_model.py

生肖模型

功能：

1. 号码 -> 生肖
2. 生肖统计
3. 生肖排名

"""


from __future__ import annotations


from typing import Dict, List



# =====================================================
# 2026生肖映射
# =====================================================


ZODIAC_MAP = {

    "马":
    [1,13,25,37,49],

    "蛇":
    [2,14,26,38],

    "龙":
    [3,15,27,39],

    "兔":
    [4,16,28,40],

    "虎":
    [5,17,29,41],

    "牛":
    [6,18,30,42],

    "鼠":
    [7,19,31,43],

    "猪":
    [8,20,32,44],

    "狗":
    [9,21,33,45],

    "鸡":
    [10,22,34,46],

    "猴":
    [11,23,35,47],

    "羊":
    [12,24,36,48]

}



NUMBER_TO_ZODIAC={}


for z,nums in ZODIAC_MAP.items():

    for n in nums:

        NUMBER_TO_ZODIAC[n]=z





# =====================================================
# 基础接口
# =====================================================


def get_zodiac(number:int)->str:


    return NUMBER_TO_ZODIAC.get(

        int(number),

        "未知"

    )





# =====================================================
# 生肖评分
# =====================================================


def zodiac_score(
        number_scores:Dict[int,float]
):


    result={}


    for z in ZODIAC_MAP:


        result[z]=0



    for n,score in number_scores.items():


        z=get_zodiac(n)


        if z!="未知":

            result[z]+=score



    return result






# =====================================================
# Top生肖
# =====================================================


def top_zodiac(
        number_scores,
        top=5
):


    scores=zodiac_score(
        number_scores
    )


    return [

        z

        for z,s

        in sorted(

            scores.items(),

            key=lambda x:x[1],

            reverse=True

        )[:top]

    ]





__all__=[

    "get_zodiac",

    "zodiac_score",

    "top_zodiac"

]
