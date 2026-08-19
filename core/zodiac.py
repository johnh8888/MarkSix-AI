# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

生肖模型

"""


# 香港六合彩生肖循环

ZODIAC = [

"鼠",

"牛",

"虎",

"兔",

"龙",

"蛇",

"马",

"羊",

"猴",

"鸡",

"狗",

"猪"

]





def get_zodiac(num):


    return ZODIAC[

        (num-1)%12

    ]





def zodiac_rank(numbers):


    result={}



    for n in numbers:


        z=get_zodiac(n)


        result[z]=result.get(

            z,

            0

        )+1



    return sorted(

        result.items(),

        key=lambda x:x[1],

        reverse=True

    )
