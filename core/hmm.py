# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

HMM状态识别模块

功能:

开奖状态检测

状态:

HOT     高频状态
COLD    冷却状态
STABLE  稳定状态
CHAOS   混沌状态

"""


from collections import Counter





# =====================================================
# 状态计算
# =====================================================


def calculate_entropy(values):


    if not values:

        return 0



    total=len(values)



    counter=Counter(

        values

    )



    entropy=0



    import math



    for v in counter.values():


        p=v/total


        entropy -= p*math.log(

            p

        )



    return round(

        entropy,

        4

    )






# =====================================================
# 热冷分析
# =====================================================


def analyze_hot_cold(history):


    specials=[


        x.get("special")

        for x in history

        if x.get("special")

    ]



    if len(specials)<10:


        return {


            "状态":

            "数据不足"

        }






    recent=specials[-20:]



    counter=Counter(

        recent

    )



    most=counter.most_common(

        1

    )[0]



    freq=most[1]/len(recent)



    if freq>=0.2:


        state="HOT"



    elif freq<=0.05:


        state="COLD"



    else:


        state="STABLE"





    return {


        "状态":

        state,



        "高频号码":

        most[0],



        "频率":

        round(

            freq,

            3

        )

    }








# =====================================================
# 趋势检测
# =====================================================


def detect_trend(history):


    if len(history)<20:


        return "数据不足"



    nums=[


        x["special"]

        for x in history[-20:]

    ]



    first=sum(

        nums[:10]

    )



    second=sum(

        nums[10:]

    )



    if second>first*1.15:


        return "上升"



    elif second<first*0.85:


        return "下降"



    else:


        return "平稳"







# =====================================================
# HMM主接口
# =====================================================


def detect_state(history):


    if len(history)<20:


        return {


            "状态":

            "数据不足",



            "趋势":

            "未知"

        }




    specials=[


        x["special"]

        for x in history

        if x.get("special")

    ]




    entropy=calculate_entropy(

        specials[-50:]

    )



    hot=analyze_hot_cold(

        history

    )



    trend=detect_trend(

        history

    )





    if entropy>3.5:


        state="CHAOS"



    else:


        state=hot.get(

            "状态",

            "STABLE"

        )





    return {


        "HMM状态":

        state,



        "趋势":

        trend,



        "熵":

        entropy,



        "详细":

        hot

    }





__all__=[

    "detect_state",

    "calculate_entropy"

]
