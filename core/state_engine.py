# -*- coding:utf-8 -*-

"""
V9.0 状态识别引擎

识别:
HOT 热态
COLD 冷态
NORMAL 正常
REVERSAL 反转
CHAOS 混沌
"""


import math
from collections import Counter



def entropy(values):

    if not values:
        return 0


    count=Counter(values)

    total=len(values)

    e=0


    for v in count.values():

        p=v/total

        e-=p*math.log2(p)


    return round(e,4)




def recent_trend(history, window=20):

    data=history[-window:]

    if len(data)<10:

        return {
            "state":"NORMAL",
            "entropy":0
        }



    e=entropy(data)


    counter=Counter(data)


    most=counter.most_common(1)[0][1]


    repeat_rate=most/len(data)



    if e>4.5:

        state="CHAOS"


    elif repeat_rate>0.18:

        state="HOT"


    elif repeat_rate<0.06:

        state="COLD"


    else:

        state="NORMAL"



    return {

        "state":state,

        "entropy":e,

        "repeat_rate":round(
            repeat_rate,
            3
        )

    }




def detect_reverse(history):


    if len(history)<10:

        return False


    a=history[-5:]

    b=history[-10:-5]


    if sum(a)/5 > sum(b)/5:

        return True


    return False




def analyze_state(history):


    result=recent_trend(history)



    if detect_reverse(history):

        result["state"]="REVERSAL"



    return result
