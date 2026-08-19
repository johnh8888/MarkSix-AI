# -*- coding:utf-8 -*-

"""
六合彩 AI V3.6 FINAL

特征分析模块

功能:

🔥 热号
❄ 冷号
📈 趋势分析
遗漏分析
波色趋势
大小趋势
单双趋势
区域趋势

"""


from collections import Counter

from .wave import get_wave




# =====================================================
# 基础属性
# =====================================================


def get_size(num):

    if num >= 25:
        return "大"

    return "小"



def get_odd_even(num):

    if num % 2:

        return "单"

    return "双"



def get_zone(num):

    if num <= 10:

        return "一区"

    elif num <=20:

        return "二区"

    elif num <=30:

        return "三区"

    elif num <=40:

        return "四区"

    else:

        return "五区"





# =====================================================
# 提取特码
# =====================================================


def get_numbers(history):


    return [

        x["special"]

        for x in history

        if x.get("special")

    ]





# =====================================================
# 热号分析
# =====================================================


def hot_numbers(
        history,
        recent=50
):


    nums=get_numbers(history)


    nums=nums[-recent:]


    counter=Counter(nums)



    result=[]



    for n,c in counter.items():


        if c>=5:


            result.append(

                {

                "号码":n,

                "次数":c

                }

            )



    result.sort(

        key=lambda x:x["次数"],

        reverse=True

    )


    return [

        x["号码"]

        for x in result[:10]

    ]





# =====================================================
# 冷号分析
# =====================================================


def cold_numbers(
        history,
        recent=100
):


    nums=get_numbers(history)


    recent_nums=set(

        nums[-recent:]

    )



    cold=[]



    for n in range(1,50):


        if n not in recent_nums:


            cold.append(n)



    return cold[:10]







# =====================================================
# 遗漏统计
# =====================================================


def missing_count(history):


    nums=get_numbers(history)



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
# 波色趋势
# =====================================================


def wave_trend(history):


    nums=get_numbers(history)


    recent=nums[-30:]


    counter=Counter(


        get_wave(x)

        for x in recent

    )


    if not counter:

        return "无数据"



    return counter.most_common(1)[0][0]







# =====================================================
# 大小趋势
# =====================================================


def size_trend(history):


    nums=get_numbers(history)


    recent=nums[-30:]


    counter=Counter(

        get_size(x)

        for x in recent

    )



    if counter["大"] > counter["小"]:


        return "大号增强 ↑"


    else:


        return "小号增强 ↑"







# =====================================================
# 单双趋势
# =====================================================


def odd_even_trend(history):


    nums=get_numbers(history)


    recent=nums[-30:]



    counter=Counter(

        get_odd_even(x)

        for x in recent

    )



    if counter["单"] > counter["双"]:


        return "单号增强 ↑"


    else:


        return "双号增强 ↑"








# =====================================================
# 区域趋势
# =====================================================


def zone_trend(history):


    nums=get_numbers(history)


    recent=nums[-30:]



    counter=Counter(

        get_zone(x)

        for x in recent

    )


    if not counter:

        return "无"



    return counter.most_common(1)[0][0]








# =====================================================
# 综合特征
# =====================================================


def feature_statistics(history):


    return {


        "数据量":

        len(history),



        "🔥热号":

        hot_numbers(history),



        "❄冷号":

        cold_numbers(history),



        "遗漏":

        missing_count(history),



        "📈趋势":

        {


            "波色":

            wave_trend(history),



            "大小":

            size_trend(history),



            "单双":

            odd_even_trend(history),



            "区域":

            zone_trend(history)


        }


    }





__all__=[


    "feature_statistics",

    "hot_numbers",

    "cold_numbers",

    "missing_count"

]
