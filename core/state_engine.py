# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.0

state_engine.py

动态市场状态引擎


功能:

1. 熵计算
2. 状态切换检测
3. 高频低频转换
4. 动态权重调整
5. 混沌检测


"""


import math


from collections import Counter


from .state import (

    MarketState,

    分析市场状态,

    状态名称

)





# =====================================================
# 信息熵计算
# =====================================================


def 计算熵(numbers):


    if not numbers:


        return 0



    counter=Counter(

        numbers

    )



    total=sum(

        counter.values()

    )



    entropy=0



    for value in counter.values():


        p=value/total


        entropy -= p * math.log(

            p,

            2

        )



    return round(

        entropy,

        4

    )





# =====================================================
# 历史熵变化
# =====================================================


def 熵变化检测(

        历史数据,

        周期=20

):


    if len(历史数据)<周期*2:


        return {


            "状态":

            "数据不足"

        }





    前=[]


    后=[]



    for item in 历史数据[-周期*2:-周期]:


        前.extend(

            item.get(

                "号码",

                []

            )

        )



    for item in 历史数据[-周期:]:


        后.extend(

            item.get(

                "号码",

                []

            )

        )



    e1=计算熵(

        前

    )


    e2=计算熵(

        后

    )



    差值=round(

        e2-e1,

        4

    )



    if 差值>0.3:


        状态="混沌增加"



    elif 差值<-0.3:


        状态="规律增强"



    else:


        状态="稳定"



    return {


        "前期熵":

        e1,


        "近期熵":

        e2,


        "变化":

        差值,


        "状态":

        状态

    }





# =====================================================
# 高频低频转换检测
# =====================================================


def 高频低频检测(

        历史数据,

        周期=30

):


    if len(历史数据)<周期:


        return {}





    最近=历史数据[-周期:]



    counter=Counter()



    for item in 最近:


        for num in item.get(

            "号码",

            []

        ):


            counter[num]+=1





    排序=counter.most_common()



    高频=[

        x[0]

        for x in 排序[:10]

    ]



    低频=[

        x[0]

        for x in 排序[-10:]

    ]



    return {


        "高频号码":

        高频,


        "低频号码":

        低频

    }





# =====================================================
# 状态变化检测
# =====================================================


def 状态变化检测(

        历史数据

):


    if len(历史数据)<40:


        return {


            "变化":

            False

        }





    当前=分析市场状态(

        历史数据

    )



    上一期=分析市场状态(

        历史数据[:-10]

    )



    if 当前 != 上一期:


        return {


            "变化":

            True,


            "之前":

            状态名称(

                上一期

            ),


            "现在":

            状态名称(

                当前

            )

        }





    return {


        "变化":

        False,


        "状态":

        状态名称(

            当前

        )

    }





# =====================================================
# 动态权重
# =====================================================


def 动态权重(

        历史数据

):


    state=分析市场状态(

        历史数据

    )



    权重={


        "frequency":0.20,


        "trend":0.15,


        "momentum":0.12,


        "omission":0.10,


        "wave":0.10,


        "zodiac":0.10,


        "size":0.08,


        "parity":0.05,


        "random":0.10

    }





    if state==MarketState.热态:


        权重["frequency"]+=0.08


        权重["momentum"]+=0.05





    elif state==MarketState.冷态:


        权重["omission"]+=0.08


        权重["trend"]+=0.05





    elif state==MarketState.连续状态:


        权重["wave"]+=0.08


        权重["trend"]+=0.05





    elif state==MarketState.混沌状态:


        权重["frequency"]-=0.05


        权重["random"]+=0.08





    总=sum(

        权重.values()

    )



    for k in 权重:


        权重[k]=round(

            权重[k]/总,

            4

        )



    return 权重





# =====================================================
# 综合状态报告
# =====================================================


def 状态引擎(

        历史数据

):


    state=分析市场状态(

        历史数据

    )


    return {


        "市场状态":

        状态名称(

            state

        ),



        "熵变化":

        熵变化检测(

            历史数据

        ),



        "高低频":

        高频低频检测(

            历史数据

        ),



        "状态切换":

        状态变化检测(

            历史数据

        ),



        "动态权重":

        动态权重(

            历史数据

        )

    }





if __name__=="__main__":


    print(

        "V5状态引擎启动"

    )
