# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

state.py

市场状态识别模块


功能:

1. 熵值计算
2. 热度检测
3. 趋势检测
4. 连续模式检测
5. 市场状态分类
6. 动态策略建议

"""


from collections import Counter

import math


from .features import (

    get_wave,

    get_size,

    get_parity

)





# =====================================================
# 号码解析
# =====================================================


def parse_numbers(rows):


    result=[]


    for row in rows:


        nums=row.get(

            "numbers",

            ""

        )


        if isinstance(nums,str):


            nums=nums.replace(

                ",",

                " "

            ).split()



        for n in nums:


            try:

                result.append(

                    int(n)

                )

            except:

                pass



    return result





# =====================================================
# 熵计算
# =====================================================


def entropy(values):


    counter=Counter(values)


    total=len(values)



    if total==0:

        return 0



    result=0



    for count in counter.values():


        p=count/total


        result -= p * math.log(

            p,

            2

        )



    return round(

        result,

        4

    )





# =====================================================
# 波色熵
# =====================================================


def wave_entropy(numbers):


    waves=[

        get_wave(n)

        for n in numbers

    ]


    return entropy(

        waves

    )





# =====================================================
# 大小熵
# =====================================================


def size_entropy(numbers):


    values=[

        get_size(n)

        for n in numbers

    ]


    return entropy(

        values

    )





# =====================================================
# 单双熵
# =====================================================


def parity_entropy(numbers):


    values=[

        get_parity(n)

        for n in numbers

    ]


    return entropy(

        values

    )





# =====================================================
# 热号比例
# =====================================================


def hot_ratio(numbers,limit=20):


    recent=numbers[:limit]


    counter=Counter(

        recent

    )


    if not counter:

        return 0



    max_value=max(

        counter.values()

    )


    return round(

        max_value/limit,

        4

    )





# =====================================================
# 连续波检测
# =====================================================


def detect_wave_streak(numbers):


    if len(numbers)<3:

        return False



    waves=[

        get_wave(n)

        for n in numbers[:3]

    ]



    return len(set(waves))==1





# =====================================================
# 反转检测
# =====================================================


def detect_flip(numbers):


    if len(numbers)<6:

        return False



    first=[

        get_wave(n)

        for n in numbers[:3]

    ]


    second=[

        get_wave(n)

        for n in numbers[3:6]

    ]



    return (

        len(set(first))==1

        and

        len(set(second))==1

        and

        first[0]!=second[0]

    )





# =====================================================
# 趋势强度
# =====================================================


def trend_strength(numbers):


    recent=numbers[:20]


    old=numbers[20:40]



    if len(old)==0:

        return 0



    r=Counter(recent)

    o=Counter(old)



    score=0



    for n in range(1,50):


        score += abs(

            r[n]-o[n]

        )



    return round(

        score/20,

        4

    )





# =====================================================
# 市场状态判断
# =====================================================


def analyze_state(rows):


    numbers=parse_numbers(

        rows

    )



    if len(numbers)<20:


        return {


            "state":

            "数据不足",


            "entropy":

            None

        }



    e=wave_entropy(

        numbers[:50]

    )


    hot=hot_ratio(

        numbers

    )


    trend=trend_strength(

        numbers

    )


    streak=detect_wave_streak(

        numbers

    )


    flip=detect_flip(

        numbers

    )




    # -------------------------
    # 状态判断
    # -------------------------


    if streak:


        state="连续波状态"



    elif flip:


        state="波色反转状态"



    elif e < 1.2:


        state="集中趋势状态"



    elif e > 1.55:


        state="混沌状态"



    elif trend>2:


        state="趋势变化状态"



    else:


        state="平衡状态"





    return {


        "state":

        state,


        "entropy":

        e,


        "hot_ratio":

        hot,


        "trend":

        trend,


        "wave_streak":

        streak,


        "flip":

        flip

    }





# =====================================================
# 动态权重建议
# =====================================================


def dynamic_weight(state):


    weights={


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



    mode=state.get(

        "state",

        ""

    )



    if mode=="连续波状态":


        weights["wave"]+=0.08

        weights["trend"]+=0.05



    elif mode=="波色反转状态":


        weights["wave"]+=0.05

        weights["momentum"]+=0.05



    elif mode=="集中趋势状态":


        weights["frequency"]+=0.08

        weights["trend"]+=0.08



    elif mode=="混沌状态":


        weights["frequency"]-=0.05

        weights["trend"]-=0.05

        weights["omission"]+=0.08



    total=sum(

        weights.values()

    )


    return {


        k:

        round(

            v/total,

            4

        )

        for k,v in weights.items()

    }





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    data=[

        {

        "numbers":

        "39 41 08 09 07 14 49"

        }

    ]*10



    s=analyze_state(data)


    print(s)


    print(

        dynamic_weight(s)

    )
