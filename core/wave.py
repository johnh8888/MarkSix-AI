# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

波色分析模块


功能:

红蓝绿判断

历史波色统计

连续波分析

冷热分析

趋势预测


"""


from collections import Counter





# =====================================================
# 波色表
# =====================================================


RED = {

    1,2,7,8,
    12,13,18,19,
    23,24,29,30,
    34,35,40,45,46

}



BLUE = {

    3,4,9,10,
    14,15,20,25,
    26,31,36,37,
    41,42,47,48

}



GREEN = {

    5,6,11,16,
    17,21,22,27,
    28,32,33,38,
    39,43,44,49

}





# =====================================================
# 单号波色
# =====================================================


def get_wave(number):


    if number in RED:

        return "红"



    if number in BLUE:

        return "蓝"



    if number in GREEN:

        return "绿"



    return "未知"







# =====================================================
# 历史波色
# =====================================================


def history_wave(history):


    result=[]


    for row in history:


        special=row.get(

            "special"

        )


        if special:


            result.append(

                get_wave(

                    special

                )

            )


    return result






# =====================================================
# 波色统计
# =====================================================


def wave_statistics(history):


    waves=history_wave(

        history

    )



    if not waves:


        return {}




    counter=Counter(

        waves

    )



    total=len(waves)



    return {


        "红":

        {

        "数量":

        counter["红"],

        "比例":

        round(

            counter["红"]/total,

            3

        )

        },



        "蓝":

        {

        "数量":

        counter["蓝"],

        "比例":

        round(

            counter["蓝"]/total,

            3

        )

        },



        "绿":

        {

        "数量":

        counter["绿"],

        "比例":

        round(

            counter["绿"]/total,

            3

        )

        }

    }







# =====================================================
# 连续波检测
# =====================================================


def detect_streak(history):


    waves=history_wave(

        history

    )



    if len(waves)<2:


        return {


            "连续":

            0

        }





    last=waves[-1]


    count=1



    for x in reversed(

        waves[:-1]

    ):


        if x==last:


            count+=1


        else:


            break





    return {


        "当前波":

        last,



        "连续次数":

        count

    }







# =====================================================
# 波色预测
# =====================================================


def predict_wave(history):


    stats=wave_statistics(

        history

    )


    streak=detect_streak(

        history

    )



    if not stats:


        return {


            "状态":

            "数据不足"

        }




    ranking=sorted(

        [

            (

            k,

            v["比例"]

            )

            for k,v in stats.items()

        ],

        key=lambda x:x[1],

        reverse=True

    )




    return {


        "推荐波色":

        ranking[0][0],



        "概率":

        ranking[0][1],



        "统计":

        stats,



        "连续":

        streak

    }





__all__=[

    "get_wave",

    "predict_wave",

    "wave_statistics",

    "history_wave"

]
