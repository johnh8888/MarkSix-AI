# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

wave_model.py

波色智能预测模型

"""


from collections import Counter


from core.features import (
    special_list,
    get_wave,
)


from core.config import (
    WAVE_LIST,
    WAVE_SHORT_WINDOW,
    WAVE_LONG_WINDOW,
)





# =========================================================
# 波色统计
# =========================================================


def wave_counter(rows, window=None):


    if window:

        rows = rows[:window]


    nums=special_list(rows)


    counter={

        "红":0,

        "蓝":0,

        "绿":0

    }



    for n in nums:


        w=get_wave(n)


        if w:

            counter[w]+=1



    return counter





# =========================================================
# 波色概率
# =========================================================


def wave_probability(rows):


    counter=wave_counter(
        rows,
        WAVE_LONG_WINDOW
    )


    total=sum(
        counter.values()
    )


    if total==0:


        return {

            "红":0.3333,

            "蓝":0.3333,

            "绿":0.3333

        }



    return {


        k:

        round(

            v/total,

            4

        )


        for k,v in counter.items()

    }





# =========================================================
# 短期波色趋势
# =========================================================


def short_wave_probability(rows):


    counter=wave_counter(
        rows,
        WAVE_SHORT_WINDOW
    )


    total=sum(
        counter.values()
    )



    if total==0:

        return wave_probability(rows)



    return {


        k:

        round(

            v/total,

            4

        )


        for k,v in counter.items()

    }





# =========================================================
# 波色遗漏
# =========================================================


def wave_omission(rows):


    nums=special_list(rows)



    result={

        "红":0,

        "蓝":0,

        "绿":0

    }



    for color in WAVE_LIST:


        count=0



        for n in nums:


            if get_wave(n)==color:

                break


            count+=1



        result[color]=count



    return result





# =========================================================
# 连续波色压力
# =========================================================


def wave_streak(rows):


    nums=special_list(rows)


    if not nums:

        return {

            "红":0,

            "蓝":0,

            "绿":0

        }



    last=get_wave(
        nums[0]
    )


    count=0



    for n in nums:


        if get_wave(n)==last:

            count+=1

        else:

            break



    return {


        last:

        count

    }





# =========================================================
# 波色转换矩阵
# =========================================================


def wave_transition(rows):


    nums=special_list(rows)



    matrix={


        "红":
        {
            "红":0,
            "蓝":0,
            "绿":0
        },


        "蓝":
        {
            "红":0,
            "蓝":0,
            "绿":0
        },


        "绿":
        {
            "红":0,
            "蓝":0,
            "绿":0
        }

    }



    colors=[

        get_wave(n)

        for n in nums

    ]



    colors=[

        x

        for x in colors

        if x

    ]



    for i in range(
        len(colors)-1
    ):


        a=colors[i]


        b=colors[i+1]


        matrix[a][b]+=1




    # 转概率


    for a in matrix:


        total=sum(
            matrix[a].values()
        )


        if total:


            for b in matrix[a]:


                matrix[a][b]=round(

                    matrix[a][b]/total,

                    4

                )



    return matrix





# =========================================================
# V4 波色综合评分
# =========================================================


def wave_score(rows):


    long_prob=wave_probability(
        rows
    )


    short_prob=short_wave_probability(
        rows
    )


    omission=wave_omission(
        rows
    )


    streak=wave_streak(
        rows
    )



    scores={}



    for color in WAVE_LIST:


        score=0



        # 长期

        score += (

            long_prob[color]

            *

            0.35

        )



        # 短期趋势

        score += (

            short_prob[color]

            *

            0.30

        )



        # 遗漏补偿

        score += (

            min(

                omission[color],

                20

            )

            /

            20

            *

            0.25

        )



        # 连续压力

        if color in streak:


            score -= (

                streak[color]

                *

                0.03

            )



        scores[color]=round(

            score,

            6

        )



    return scores





# =========================================================
# 输出单推双推
# =========================================================


def predict_wave(rows):


    scores=wave_score(
        rows
    )



    ranking=sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )



    single=ranking[0][0]


    double=[

        ranking[0][0],

        ranking[1][0]

    ]



    exclude=ranking[-1][0]



    return {


        "single":

        single,


        "double":

        double,


        "exclude":

        exclude,


        "probability":

        scores,


        "ranking":

        ranking

    }





# =========================================================
# 测试
# =========================================================


if __name__=="__main__":


    rows=[

        {

        "numbers":

        "38,26,08,06,29,18,23"

        }

    ]


    print(
        predict_wave(rows)
    )
