# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统

core/state_engine.py

V8.0 QUANT STATE SWITCH

状态检测模块

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




def normalize_history(history):

    """
    兼容:

    [
      49,
      16,
      22
    ]


    和:

    [
      {"special":49}
    ]

    """

    numbers=[]


    for x in history:


        if isinstance(x,dict):

            if "special" in x:

                numbers.append(
                    int(x["special"])
                )


        else:

            numbers.append(
                int(x)
            )


    return numbers






def get_wave(n):


    if n in RED:

        return "红"


    if n in BLUE:

        return "蓝"


    return "绿"







def entropy(numbers):


    if not numbers:

        return 0



    counter=Counter(numbers)


    total=len(numbers)


    value=0



    for c in counter.values():


        p=c/total


        value-=p*math.log2(p)



    return round(value,4)








def repeat_wave(numbers):


    if len(numbers)<5:

        return False



    waves=[

        get_wave(x)

        for x in numbers[:5]

    ]


    return len(set(waves))==1







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








def analyze_state(history):


    numbers=normalize_history(
        history
    )


    e=entropy(
        numbers[:100]
    )



    state="正常状态"



    hot=0.6

    markov=0.35

    random=0.05





    if e>3.4:


        state="混沌状态"


        hot=0.4

        markov=0.35

        random=0.25






    if repeat_wave(numbers):


        state="连续波状态"


        hot=0.45

        markov=0.25

        random=0.30






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
