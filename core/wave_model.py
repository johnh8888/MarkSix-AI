# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

wave_model.py

波色智能模型


功能:

1. 波色概率
2. 波色趋势
3. 波色冷热
4. 双推
5. 排除色
6. 波色状态


"""


from collections import Counter


from .features import (

    get_special,

    get_wave,

)





# =====================================================
# 基础颜色
# =====================================================


WAVES=[

    "红",

    "蓝",

    "绿"

]





# =====================================================
# 获取历史波色
# =====================================================


def get_history_wave(rows,limit=100):


    result=[]


    for row in rows[:limit]:


        n=get_special(row)


        if n:


            result.append(
                get_wave(n)
            )



    return result





# =====================================================
# 基础概率
# =====================================================


def wave_frequency(rows,limit=100):


    waves=get_history_wave(
        rows,
        limit
    )


    counter=Counter(
        waves
    )


    total=sum(
        counter.values()
    )



    if total==0:


        return {


            x:1/3

            for x in WAVES

        }



    return {


        x:

        round(

            counter[x]/total,

            4

        )


        for x in WAVES

    }





# =====================================================
# 最近趋势
# =====================================================


def wave_trend(rows):


    recent=wave_frequency(
        rows,
        20
    )


    long=wave_frequency(
        rows,
        100
    )



    score={}



    for w in WAVES:


        score[w]=(

            recent[w]*0.7

            +

            long[w]*0.3

        )



    total=sum(
        score.values()
    )


    return {


        k:

        round(
            v/total,
            4
        )


        for k,v in score.items()

    }





# =====================================================
# 冷热检测
# =====================================================


def wave_hot_cold(rows):


    prob=wave_frequency(
        rows,
        30
    )



    hot=max(

        prob,

        key=prob.get

    )


    cold=min(

        prob,

        key=prob.get

    )



    return {


        "hot":

        hot,


        "cold":

        cold,


        "prob":

        prob

    }





# =====================================================
# 连续检测
# =====================================================


def detect_wave_streak(rows):


    waves=get_history_wave(
        rows,
        20
    )


    if not waves:

        return None



    last=waves[0]


    count=0



    for w in waves:


        if w==last:

            count+=1

        else:

            break



    return {


        "wave":

        last,


        "length":

        count

    }





# =====================================================
# 反转检测
# =====================================================


def detect_wave_reverse(rows):


    waves=get_history_wave(
        rows,
        10
    )


    if len(waves)<6:

        return False



    first=waves[:3]


    second=waves[3:6]



    return (

        len(set(first))==1

        and

        len(set(second))==3

    )





# =====================================================
# 最终波色预测
# =====================================================


def predict_wave(rows):


    trend=wave_trend(
        rows
    )


    hotcold=wave_hot_cold(
        rows
    )


    streak=detect_wave_streak(
        rows
    )



    score=trend.copy()



    # 连续出现降低惯性

    if streak:


        if streak["length"]>=4:


            score[streak["wave"]] *=0.7




    # 反转提高其他颜色


    if detect_wave_reverse(rows):


        for w in score:


            score[w]*=1.2



    total=sum(
        score.values()
    )



    score={


        k:

        round(
            v/total,
            4
        )


        for k,v in score.items()

    }



    order=sorted(

        score.items(),

        key=lambda x:x[1],

        reverse=True

    )



    return {


        "single":

        order[0][0],



        "double":

        [

            order[0][0],

            order[1][0]

        ],



        "exclude":

        order[2][0],



        "probability":

        score,



        "hot":

        hotcold["hot"],



        "cold":

        hotcold["cold"],



        "streak":

        streak

    }





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    rows=[


        {

        "numbers":

        "38,26,08,06,29,18,23"

        },


        {

        "numbers":

        "33,27,16,28,04,25,14"

        }


    ]



    print(

        predict_wave(rows)

    )
