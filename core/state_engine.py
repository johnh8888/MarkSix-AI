# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

state_engine.py

市场状态识别引擎

"""


from collections import Counter

from core.config import (
    SHORT_WINDOW,
    MEDIUM_WINDOW,
    STATE_LIST,
)



from core.features import (
    special_list,
    special_frequency,
    get_wave,
)





# =========================================================
# 熵计算
# =========================================================


def entropy(values):


    if not values:

        return 0



    counter = Counter(
        values
    )


    total=len(values)


    result=0



    for count in counter.values():


        p=count/total


        result -= p * (
            __import__(
                "math"
            ).log(
                p
            )
        )



    return result





# =========================================================
# 热度检测
# =========================================================


def detect_hot(rows):


    nums=special_list(
        rows[:SHORT_WINDOW]
    )


    if not nums:

        return False



    freq=Counter(nums)


    max_count=max(
        freq.values()
    )



    # 最近20期出现超过3次

    if max_count>=3:

        return True



    return False





# =========================================================
# 冷态检测
# =========================================================


def detect_cold(rows):


    nums=special_list(
        rows[:SHORT_WINDOW]
    )


    if not nums:

        return False



    freq=Counter(nums)



    cold=0



    for n in range(1,50):


        if freq.get(n,0)==0:

            cold+=1



    # 冷号过多

    if cold>30:

        return True



    return False





# =========================================================
# 趋势变化检测
# =========================================================


def detect_shift(rows):


    short=special_frequency(
        rows[:SHORT_WINDOW]
    )


    medium=special_frequency(
        rows[:MEDIUM_WINDOW]
    )



    change=0



    for n in range(1,50):


        change += abs(

            short[n]

            -

            medium[n]

        )



    # 变化明显

    if change>80:

        return True



    return False





# =========================================================
# 混乱检测
# =========================================================


def detect_chaos(rows):


    nums=special_list(
        rows[:SHORT_WINDOW]
    )


    if len(nums)<10:

        return False



    e=entropy(nums)



    # 高熵

    if e>3.0:

        return True



    return False





# =========================================================
# 波色状态
# =========================================================


def wave_state(rows):


    nums=special_list(
        rows[:SHORT_WINDOW]
    )


    counter={

        "红":0,

        "蓝":0,

        "绿":0

    }



    for n in nums:


        w=get_wave(n)


        if w:

            counter[w]+=1



    return counter





# =========================================================
# 主状态判断
# =========================================================


def detect_market_state(rows):


    """

    返回:

    NORMAL
    HOT
    COLD
    SHIFT
    CHAOS

    """



    if detect_chaos(rows):


        return "CHAOS"



    if detect_shift(rows):


        return "SHIFT"



    if detect_hot(rows):


        return "HOT"



    if detect_cold(rows):


        return "COLD"



    return "NORMAL"





# =========================================================
# 动态权重
# =========================================================


def dynamic_weights(
        base_weights,
        state
):


    """

    根据状态调整模型权重


    """


    weights=dict(
        base_weights
    )



    if state=="HOT":


        if "trend" in weights:

            weights["trend"]*=1.25


        if "momentum" in weights:

            weights["momentum"]*=1.25



    elif state=="COLD":


        if "omission" in weights:

            weights["omission"]*=1.35


        if "pressure" in weights:

            weights["pressure"]*=1.25



    elif state=="SHIFT":


        if "distance" in weights:

            weights["distance"]*=1.30


        if "wave" in weights:

            weights["wave"]*=1.20



    elif state=="CHAOS":


        if "frequency" in weights:

            weights["frequency"]*=0.75


        if "trend" in weights:

            weights["trend"]*=0.75



    # 重新归一化


    total=sum(
        weights.values()
    )



    if total>0:


        for k in weights:


            weights[k]=round(

                weights[k]/total,

                4

            )



    return weights





# =========================================================
# 状态报告
# =========================================================


def analyze_state(rows):


    state=detect_market_state(
        rows
    )



    return {


        "state":

        state,



        "wave":

        wave_state(rows),



        "entropy":

        round(

            entropy(

                special_list(
                    rows[:SHORT_WINDOW]
                )

            ),

            4

        )

    }





if __name__=="__main__":


    test=[

        {

            "numbers":

            "38,26,08,06,29,18,23"

        }

    ]


    print(
        analyze_state(test)
    )
