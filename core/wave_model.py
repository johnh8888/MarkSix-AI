# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

wave_model.py

波色智能模型

功能:

1. 波色概率
2. 波色趋势
3. 主波预测
4. 双波预测
5. 排除波
6. 波色评分

"""


from collections import Counter

from .features import (
    get_special,
    get_wave,
)





# =====================================================
# 波色基础
# =====================================================


WAVES = [

    "红",

    "蓝",

    "绿"

]





# =====================================================
# 波色统计
# =====================================================


def wave_count(rows, window=50):


    counter=Counter()


    for row in rows[:window]:


        n=get_special(row)


        if n is None:

            continue


        w=get_wave(n)


        if w:

            counter[w]+=1



    return counter





# =====================================================
# 概率计算
# =====================================================


def wave_probability(rows,window=50):


    counter=wave_count(
        rows,
        window
    )


    total=sum(
        counter.values()
    )


    if total==0:


        return {

            "红":0.333,

            "蓝":0.333,

            "绿":0.333

        }



    result={}



    for w in WAVES:


        result[w]=round(

            counter.get(w,0)

            /

            total,

            6

        )


    return result





# =====================================================
# 波色趋势
# =====================================================


def wave_trend(rows):


    short=wave_probability(
        rows,
        20
    )


    long=wave_probability(
        rows,
        100
    )


    trend={}



    for w in WAVES:


        trend[w]=round(

            short[w]

            -

            long[w],

            6

        )


    return trend





# =====================================================
# 波色综合评分
# =====================================================


def wave_score(rows):


    prob=wave_probability(
        rows,
        50
    )


    trend=wave_trend(
        rows
    )


    score={}



    for w in WAVES:


        score[w]=round(

            prob[w]*0.7

            +

            max(
                trend[w],
                0
            )*0.3,


            6

        )


    return score





# =====================================================
# 主波
# =====================================================


def predict_main_wave(rows):


    scores=wave_score(
        rows
    )


    return max(

        scores,

        key=scores.get

    )





# =====================================================
# 双波推荐
# =====================================================


def predict_double_wave(rows):


    scores=wave_score(
        rows
    )


    result=sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )


    return [

        result[0][0],

        result[1][0]

    ]





# =====================================================
# 排除波
# =====================================================


def predict_exclude_wave(rows):


    scores=wave_score(
        rows
    )


    return min(

        scores,

        key=scores.get

    )





# =====================================================
# 波色覆盖率
# =====================================================


def coverage(rows,waves,window=100):


    hit=0

    total=0


    for row in rows[:window]:


        n=get_special(row)


        if n is None:

            continue


        total+=1


        w=get_wave(n)


        if w in waves:

            hit+=1



    if total==0:

        return 0



    return round(

        hit/total*100,

        2

    )





# =====================================================
# 输出完整波色分析
# =====================================================


def analyze_wave(rows):


    probability=wave_probability(
        rows
    )


    main=predict_main_wave(
        rows
    )


    double=predict_double_wave(
        rows
    )


    exclude=predict_exclude_wave(
        rows
    )


    return {


        "probability":

            probability,


        "main":

            main,


        "double":

            double,


        "exclude":

            exclude,


        "double_coverage":

            coverage(
                rows,
                double
            )

    }





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    test=[

        {
            "numbers":
            "38,26,08,06,29,18,23"
        },

        {
            "numbers":
            "33,27,16,28,04,25,14"
        },

    ]


    print(

        analyze_wave(test)

    )
