# -*- coding:utf-8 -*-

"""
六合彩 AI V3.7 FINAL

状态分析引擎


功能:

1. 热冷状态
2. 趋势检测
3. 波色反转
4. 市场温度
5. 状态分类


"""


from collections import Counter



# =====================================================
# 热度
# =====================================================


def number_temperature(history):


    nums=[

        x["special"]

        for x in history

    ]



    recent20=nums[-20:]


    counter=Counter(
        recent20
    )



    result={}


    for n in range(1,50):


        value=counter[n]


        if value>=3:

            level="🔥热"


        elif value==0:

            level="❄冷"


        else:

            level="平衡"



        result[n]={

            "次数":
            value,


            "状态":
            level

        }



    return result




# =====================================================
# 遗漏
# =====================================================


def miss_analysis(history):


    nums=[

        x["special"]

        for x in history

    ]


    result={}


    for n in range(1,50):


        miss=0


        for x in reversed(nums):


            if x==n:

                break


            miss+=1



        result[n]=miss



    return result




# =====================================================
# 趋势方向
# =====================================================


def trend_detect(history):


    nums=[

        x["special"]

        for x in history

    ]



    if len(nums)<20:


        return {

            "趋势":
            "数据不足"

        }




    old=Counter(
        nums[-40:-20]
    )


    new=Counter(
        nums[-20:]
    )



    old_avg=sum(
        old.values()
    )

    new_avg=sum(
        new.values()
    )



    if new_avg>old_avg:


        trend="升温"



    elif new_avg<old_avg:


        trend="降温"



    else:

        trend="稳定"



    return {

        "趋势":

        trend

    }





# =====================================================
# 市场状态
# =====================================================


def market_state(history):


    trend=trend_detect(
        history
    )


    if len(history)<50:


        return {

            "状态":
            "数据不足"

        }



    t=trend["趋势"]



    if t=="升温":

        state="活跃期"


    elif t=="降温":

        state="冷却期"


    else:

        state="平衡期"



    return {

        "状态":

        state,


        "趋势":

        t

    }





# =====================================================
# 综合状态
# =====================================================


def analyze_state(history):


    return {


        "市场状态":

        market_state(history),



        "热度":

        number_temperature(history),



        "遗漏":

        miss_analysis(history),



        "趋势":

        trend_detect(history)

    }




__all__=[

    "analyze_state",

    "number_temperature",

    "miss_analysis",

    "trend_detect"

]
