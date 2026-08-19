# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

特征工程

生成:

波色
大小
单双
尾数
区域
冷热
"""



from collections import Counter



# ===============================
# 波色
# ===============================


RED = {
    1,2,7,8,12,13,18,19,
    23,24,29,30,34,35,
    40,45,46
}


BLUE = {
    3,4,9,10,14,15,
    20,25,26,31,
    36,37,41,42,47,48
}


GREEN = {
    5,6,11,16,17,
    21,22,27,28,
    32,33,38,39,
    43,44,49
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





def get_parity(n):

    return (

        "单"

        if n%2

        else

        "双"

    )





def get_tail(n):

    return n%10





def get_zone(n):


    if n<=10:

        return 1

    if n<=20:

        return 2

    if n<=30:

        return 3

    if n<=40:

        return 4


    return 5







def build_features(history):


    numbers=[

        x["special"]

        for x in history

    ]



    return {


        "wave":

        Counter(

            get_wave(x)

            for x in numbers

        ),



        "size":

        Counter(

            get_size(x)

            for x in numbers

        ),



        "parity":

        Counter(

            get_parity(x)

            for x in numbers

        ),



        "tail":

        Counter(

            get_tail(x)

            for x in numbers

        ),



        "zone":

        Counter(

            get_zone(x)

            for x in numbers

        )

    }
