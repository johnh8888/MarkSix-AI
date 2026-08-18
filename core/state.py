# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

state.py

市场状态识别模块

负责:

1. 热态
2. 冷态
3. 平衡态
4. 混沌态
5. 波色惯性
6. 波色反转
7. 数字集中度


"""


from collections import Counter

import math


from .features import (

    get_special,

    get_wave,

)





# =====================================================
# 状态类型
# =====================================================


STATE_HOT = "热态"

STATE_COLD = "冷态"

STATE_BALANCE = "平衡态"

STATE_CHAOS = "混沌态"

STATE_REVERSE = "反转态"





# =====================================================
# 熵计算
# =====================================================


def entropy(values):


    if not values:

        return 0



    counter=Counter(values)


    total=len(values)


    result=0



    for c in counter.values():


        p=c/total


        result -= p*math.log(
            p,
            2
        )



    return round(
        result,
        4
    )





# =====================================================
# 数字集中度
# =====================================================


def number_concentration(rows,window=20):


    nums=[]


    for row in rows[:window]:


        n=get_special(row)


        if n:

            nums.append(n)



    if not nums:

        return 0



    counter=Counter(nums)


    max_count=max(
        counter.values()
    )


    return round(

        max_count /

        len(nums),

        4

    )





# =====================================================
# 波色连续检测
# =====================================================


def wave_chain(rows):


    result=[]


    for row in rows:


        n=get_special(row)


        if n:

            w=get_wave(n)

            result.append(w)



    return result





def same_wave_count(rows):


    waves=wave_chain(
        rows
    )


    if not waves:

        return 0



    first=waves[0]


    count=0


    for w in waves:


        if w==first:

            count+=1

        else:

            break



    return count





# =====================================================
# 波色反转检测
# =====================================================


def detect_reverse(rows):


    waves=wave_chain(
        rows[:10]
    )


    if len(waves)<5:

        return False



    change=0



    for i in range(
        1,
        len(waves)
    ):


        if waves[i]!=waves[i-1]:

            change+=1



    ratio=change/len(waves)



    return ratio>0.7





# =====================================================
# 市场状态分析
# =====================================================


def analyze_state(rows):


    concentration = number_concentration(
        rows
    )


    h = entropy(
        [
            get_wave(
                get_special(r)
            )

            for r in rows[:30]

            if get_special(r)
        ]
    )


    same_wave=same_wave_count(
        rows
    )


    reverse=detect_reverse(
        rows
    )



    # ==========================
    # 反转状态
    # ==========================

    if reverse:


        return {


            "state":
                STATE_REVERSE,


            "entropy":
                h,


            "concentration":
                concentration

        }



    # ==========================
    # 热态
    # ==========================

    if concentration>=0.25:


        return {


            "state":
                STATE_HOT,


            "entropy":
                h,


            "concentration":
                concentration

        }





    # ==========================
    # 冷态
    # ==========================

    if concentration<=0.08:


        return {


            "state":
                STATE_COLD,


            "entropy":
                h,


            "concentration":
                concentration

        }





    # ==========================
    # 混沌
    # ==========================

    if h>1.55:


        return {


            "state":
                STATE_CHAOS,


            "entropy":
                h,


            "concentration":
                concentration

        }




    return {


        "state":

            STATE_BALANCE,


        "entropy":

            h,


        "concentration":

            concentration


    }





# =====================================================
# 动态策略建议
# =====================================================


def strategy_adjustment(state):


    s=state.get(
        "state"
    )



    if s==STATE_HOT:


        return {


            "trend":
                0.25,


            "frequency":
                0.30,


            "omission":
                0.10

        }



    if s==STATE_COLD:


        return {


            "trend":
                0.10,


            "frequency":
                0.15,


            "omission":
                0.30

        }



    if s==STATE_REVERSE:


        return {


            "trend":
                0.15,


            "frequency":
                0.20,


            "wave":
                0.30

        }




    if s==STATE_CHAOS:


        return {


            "frequency":
                0.15,


            "trend":
                0.10,


            "size":
                0.20

        }



    return {


        "frequency":
            0.25,


        "trend":
            0.20,


        "wave":
            0.15


    }
