# -*- coding:utf-8 -*-

"""
V9.5 属性融合引擎

分析:

波色
大小
单双
生肖
"""


from collections import Counter



RED={
1,2,7,8,12,13,18,19,
23,24,29,30,34,35,
40,45,46
}


BLUE={
3,4,9,10,14,15,
20,25,26,31,
36,37,41,42,47,48
}


GREEN={
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

    if n>=25:

        return "大"

    return "小"





def get_oe(n):

    if n%2:

        return "单"

    return "双"






def attribute_analyze(numbers):


    waves=[]

    sizes=[]

    oes=[]


    for n in numbers:


        waves.append(
            get_wave(n)
        )


        sizes.append(
            get_size(n)
        )


        oes.append(
            get_oe(n)
        )



    return {


        "波色趋势":

        Counter(waves).most_common(1)[0][0],



        "大小趋势":

        Counter(sizes).most_common(1)[0][0],



        "单双趋势":

        Counter(oes).most_common(1)[0][0]

    }
