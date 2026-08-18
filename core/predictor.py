# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0
核心预测引擎

功能:

1. 动态模块融合
2. 49码评分
3. 概率归一化
4. 生肖修正
5. 波色双推
6. 大小单双预测

"""


from collections import defaultdict


from core.features import (
    get_special,
    get_color,
    get_size,
    get_parity,
)


from core.strategies import (
    combine_strategies
)


from core.config import (
    NUMBER_MAX,
    TOP_N,
)


# =====================================================
# 2026生肖系统
# =====================================================


ZODIAC_2026 = [

    "马",
    "羊",
    "猴",
    "鸡",
    "狗",
    "猪",
    "鼠",
    "牛",
    "虎",
    "兔",
    "龙",
    "蛇"

]


# 澳门六合彩生肖号码
# 2026 马年

ZODIAC_MAP = {

1:"马",
2:"蛇",
3:"龙",
4:"兔",
5:"虎",
6:"牛",
7:"鼠",
8:"猪",
9:"狗",
10:"鸡",
11:"猴",
12:"羊",

13:"马",
14:"蛇",
15:"龙",
16:"兔",
17:"虎",
18:"牛",
19:"鼠",
20:"猪",
21:"狗",
22:"鸡",
23:"猴",
24:"羊",

25:"马",
26:"蛇",
27:"龙",
28:"兔",
29:"虎",
30:"牛",
31:"鼠",
32:"猪",
33:"狗",
34:"鸡",
35:"猴",
36:"羊",

37:"马",
38:"蛇",
39:"龙",
40:"兔",
41:"虎",
42:"牛",
43:"鼠",
44:"猪",
45:"狗",
46:"鸡",
47:"猴",
48:"羊",

49:"马"

}



# =====================================================
# 号码生肖
# =====================================================

def get_zodiac(num):

    return ZODIAC_MAP.get(
        int(num),
        "未知"
    )



# =====================================================
# TOP号码
# =====================================================

def get_top_numbers(scores,n=10):

    return sorted(
        scores.items(),
        key=lambda x:x[1],
        reverse=True
    )[:n]




# =====================================================
# 生肖预测
# =====================================================


def predict_zodiac(scores):


    zodiac_score = defaultdict(float)


    for num,score in scores.items():

        z = get_zodiac(num)

        zodiac_score[z]+=score



    result = sorted(
        zodiac_score.items(),
        key=lambda x:x[1],
        reverse=True
    )


    return [
        x[0]
        for x in result[:5]
    ]




# =====================================================
# 平特生肖
# =====================================================

def predict_pingte(zodiac):

    return zodiac[:2]




# =====================================================
# 大小预测
# =====================================================


def predict_size(rows):


    big=0
    small=0


    for row in rows[:50]:

        n=get_special(row)


        if n>=25:
            big+=1

        else:
            small+=1


    total=big+small


    if total==0:

        return (
            "未知",
            {
                "大":0.5,
                "小":0.5
            }
        )


    p_big=round(
        big/total,
        3
    )


    p_small=round(
        small/total,
        3
    )


    return (

        "大"
        if p_big>=p_small
        else "小",

        {
            "大":p_big,
            "小":p_small
        }

    )




# =====================================================
# 单双
# =====================================================

def predict_parity(rows):


    odd=0
    even=0


    for row in rows[:50]:


        n=get_special(row)


        if n%2:
            odd+=1

        else:
            even+=1


    total=odd+even


    if total==0:

        return (
            "未知",
            {
                "单":0.5,
                "双":0.5
            }
        )


    po=round(
        odd/total,
        3
    )

    pe=round(
        even/total,
        3
    )


    return (

        "单"
        if po>=pe
        else "双",

        {
            "单":po,
            "双":pe
        }

    )




# =====================================================
# 波色预测
# =====================================================


def predict_wave(scores):


    wave={

        "红":0,
        "蓝":0,
        "绿":0

    }


    for num,score in scores.items():

        c=get_color(num)

        wave[c]+=score



    total=sum(
        wave.values()
    )


    if total:

        for k in wave:

            wave[k]=round(
                wave[k]/total,
                4
            )


    order=sorted(
        wave.items(),
        key=lambda x:x[1],
        reverse=True
    )


    return (

        order[0][0],

        order[:2],

        wave

    )




# =====================================================
# 主预测函数
# =====================================================


def predict(rows):


    scores,modules = combine_strategies(
        rows
    )


    # top10

    top10=get_top_numbers(
        scores,
        10
    )


    # 三码

    recommend=[

        x[0]
        for x in top10[:3]

    ]


    #生肖

    zodiac=predict_zodiac(
        scores
    )


    pingte=predict_pingte(
        zodiac
    )


    size,size_prob=predict_size(
        rows
    )


    parity,parity_prob=predict_parity(
        rows
    )


    wave_single,wave_double,wave_prob=predict_wave(
        scores
    )


    return {


        "top10":

        top10,


        "recommend":

        recommend,


        "first":

        top10[0],


        "zodiac":

        zodiac,


        "pingte":

        pingte,


        "size":

        size,


        "size_prob":

        size_prob,


        "parity":

        parity,


        "parity_prob":

        parity_prob,


        "wave_single":

        wave_single,


        "wave_double":

        [
            x[0]
            for x in wave_double
        ],


        "wave_prob":

        wave_prob,


        "modules":

        modules

    }






if __name__=="__main__":


    test=[

        {
            "numbers":
            "39,41,08,09,07,14,49"
        }

    ]


    print(
        predict(test)
    )
