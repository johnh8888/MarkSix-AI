# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

特征工程模块

提取:

波色
大小
单双
尾数
区域
和值


用于:

Markov
HMM
预测模型

"""


from collections import Counter





# =====================================================
# 基础属性
# =====================================================


RED = {

    1,2,7,8,12,13,18,19,
    23,24,29,30,34,35,
    40,45,46

}


BLUE = {

    3,4,9,10,14,15,
    20,25,26,31,36,
    37,41,42,47,48

}


GREEN = {

    5,6,11,16,17,21,
    22,27,28,32,33,
    38,39,43,44,49

}





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
