# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

生肖分析模块


功能:

号码生肖映射

历史生肖统计

冷热生肖

趋势分析


"""



from collections import Counter





# =====================================================
# 生肖表
# =====================================================


ZODIAC_ORDER = [

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



# 49号码生肖映射
# 按六合传统生肖循环


ZODIAC_MAP={}



for i in range(1,50):


    ZODIAC_MAP[i]=ZODIAC_ORDER[

        (i-1)%12

    ]







# =====================================================
# 单号码生肖
# =====================================================


def get_zodiac(number):


    return ZODIAC_MAP.get(

        int(number),

        "未知"

    )







# =====================================================
# 历史生肖
# =====================================================


def history_zodiac(history):


    result=[]



    for row in history:


        special=row.get(

            "special"

        )


        if special:


            result.append(

                get_zodiac(

                    special

                )

            )



    return result






# =====================================================
# 生肖统计
# =====================================================


def zodiac_statistics(history):


    values=history_zodiac(

        history

    )



    if not values:


        return {}





    counter=Counter(

        values

    )



    total=len(values)



    result={}



    for z in ZODIAC_ORDER:


        result[z]={


            "数量":

            counter[z],



            "比例":

            round(

                counter[z]/total,

                3

            )

        }



    return result






# =====================================================
# 热冷生肖
# =====================================================


def hot_cold_zodiac(history):


    stats=zodiac_statistics(

        history

    )



    if not stats:


        return {}




    ranking=sorted(

        stats.items(),

        key=lambda x:

        x[1]["数量"],

        reverse=True

    )




    return {


        "热门生肖":

        [

            x[0]

            for x in ranking[:3]

        ],



        "冷门生肖":

        [

            x[0]

            for x in ranking[-3:]

        ]

    }






# =====================================================
# 生肖预测
# =====================================================


def predict_zodiac(history):


    stats=zodiac_statistics(

        history

    )



    if not stats:


        return {


            "状态":

            "数据不足"

        }





    ranking=sorted(

        stats.items(),

        key=lambda x:

        x[1]["比例"],

        reverse=True

    )




    return {


        "推荐生肖":

        ranking[0][0],



        "概率":

        ranking[0][1]["比例"],



        "统计":

        stats,



        "冷热":

        hot_cold_zodiac(

            history

        )

    }






__all__=[

    "get_zodiac",

    "predict_zodiac",

    "zodiac_statistics",

    "history_zodiac"

]
