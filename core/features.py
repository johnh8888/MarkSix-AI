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

def get_wave(n):


    if n in RED:

        return "红"


    if n in BLUE:

        return "蓝"


    if n in GREEN:

        return "绿"


    return "未知"







def get_size(n):


    return (

        "大"

        if n>=25

        else

        "小"

    )







def get_odd_even(n):


    return (

        "单"

        if n%2

        else

        "双"

    )








def get_tail(n):


    return n % 10








def get_zone(n):


    if n<=10:

        return 1


    elif n<=20:

        return 2


    elif n<=30:

        return 3


    elif n<=40:

        return 4


    else:

        return 5







# =====================================================
# 单期特征
# =====================================================


def extract_draw_feature(draw):


    nums=draw.get(

        "numbers",

        []

    )


    special=draw.get(

        "special"

    )



    if not special:


        return {}




    return {


        "special":

        special,



        "wave":

        get_wave(

            special

        ),



        "size":

        get_size(

            special

        ),



        "odd_even":

        get_odd_even(

            special

        ),



        "tail":

        get_tail(

            special

        ),



        "zone":

        get_zone(

            special

        ),



        "sum":

        sum(nums)+special

    }





# =====================================================
# 历史特征
# =====================================================


def build_features(history):


    result=[]



    for draw in history:


        f=extract_draw_feature(

            draw

        )


        if f:


            result.append(f)



    return result






# =====================================================
# 趋势统计
# =====================================================


def feature_statistics(history):


    features=build_features(

        history

    )



    if not features:


        return {}





    return {


        "波色":

        dict(

            Counter(

                x["wave"]

                for x in features

            )

        ),



        "大小":

        dict(

            Counter(

                x["size"]

                for x in features

            )

        ),



        "单双":

        dict(

            Counter(

                x["odd_even"]

                for x in features

            )

        ),



        "尾数":

        dict(

            Counter(

                x["tail"]

                for x in features

            )

        ),



        "区域":

        dict(

            Counter(

                x["zone"]

                for x in features

            )

        )

    }





__all__=[


    "extract_draw_feature",

    "build_features",

    "feature_statistics",

    "get_wave",

    "get_size",

    "get_odd_even"

]
