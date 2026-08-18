# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统

V8.0 QUANT STATE SWITCH

市场状态识别

功能:

1. 熵检测
2. 热冷切换
3. 连续波检测
4. 反转检测
5. 动态策略权重

"""


from collections import Counter
import math




RED={
1,2,7,8,12,13,
18,19,23,24,
29,30,34,35,
40,45,46
}


BLUE={
3,4,9,10,
14,15,20,
25,26,31,
36,37,41,
42,47,48
}




def get_wave(n):

    if n in RED:
        return "红"

    if n in BLUE:
        return "蓝"

    return "绿"





# =====================================================
# 熵
# =====================================================


def entropy(numbers):


    if not numbers:

        return 0



    c=Counter(numbers)


    total=len(numbers)


    e=0


    for v in c.values():

        p=v/total

        e-=p*math.log2(p)



    return round(e,3)







# =====================================================
# 连续波检测
# =====================================================


def repeat_wave(numbers):


    if len(numbers)<5:

        return False



    waves=[

        get_wave(x)

        for x in numbers[:5]

    ]



    return len(set(waves))==1






# =====================================================
# 波色反转
# =====================================================


def flip_wave(numbers):


    if len(numbers)<6:

        return False



    waves=[

        get_wave(x)

        for x in numbers[:6]

    ]


    return (

        waves[0]!=waves[1]

        and

        waves[1]!=waves[2]

    )







# =====================================================
# 市场状态
# =====================================================


def analyze_state(history):


    numbers=[

        x["special"]

        for x in history

        if "special" in x

    ]



    e=entropy(numbers[:100])




    state="正常状态"



    hot=0.6

    markov=0.35

    random=0.05




    # 高熵

    if e>3.4:


        state="混沌状态"


        hot=0.4

        markov=0.35

        random=0.25






    # 连续同波


    if repeat_wave(numbers):


        state="连续波状态"


        hot=0.45

        markov=0.25

        random=0.30






    # 反转


    if flip_wave(numbers):


        state="反转状态"


        hot=0.5

        markov=0.4

        random=0.1






    return {


        "状态":

        state,


        "entropy":

        e,


        "动态权重":{


            "hot":

            hot,


            "markov":

            markov,


            "random":

            random

        }


    }




__all__=[

"analyze_state"

]
