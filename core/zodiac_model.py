# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

zodiac_model.py

生肖智能分析模块

"""

from collections import Counter


# =====================================================
# 年份生肖顺序
# =====================================================

YEAR_ORDER = {

    2026: [

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

}



# =====================================================
# 构造号码生肖
# =====================================================

def build_zodiac_map(year=2026):


    if year not in YEAR_ORDER:

        raise ValueError(
            f"不支持年份:{year}"
        )


    zodiac_list = YEAR_ORDER[year]


    result = {}


    index = 0


    for num in range(1,50):


        result[num] = zodiac_list[index]


        index += 1


        if index >= 12:

            index = 0



    return result





# 当前2026

ZODIAC_MAP = build_zodiac_map(2026)





# =====================================================
# 查询号码生肖
# =====================================================


def get_zodiac(num,year=2026):


    try:

        num=int(num)

    except:

        return None



    mapping = build_zodiac_map(year)


    return mapping.get(num)





# =====================================================
# 获取生肖号码分组
# =====================================================


def zodiac_numbers(year=2026):


    mapping = build_zodiac_map(year)


    result={}



    for z in YEAR_ORDER[year]:


        result[z]=[]



    for num,z in mapping.items():

        result[z].append(num)



    return result





# =====================================================
# 提取历史号码
# =====================================================


def parse_numbers(rows):


    result=[]


    for row in rows:


        nums=row.get(
            "numbers",
            ""
        )


        if isinstance(nums,str):

            nums=nums.replace(
                ",",
                " "
            ).split()



        for n in nums:


            try:

                result.append(
                    int(n)
                )

            except:

                pass



    return result





# =====================================================
# 生肖频率
# =====================================================


def zodiac_frequency(
        rows,
        limit=100,
        year=2026
):


    nums=parse_numbers(
        rows[:limit]
    )


    counter=Counter()



    for n in nums:


        z=get_zodiac(
            n,
            year
        )


        if z:

            counter[z]+=1



    total=sum(
        counter.values()
    )



    if total==0:

        return {}



    return {


        k:

        round(
            v/total,
            4
        )

        for k,v in counter.items()

    }





# =====================================================
# 生肖趋势
# =====================================================


def zodiac_trend(
        rows,
        year=2026
):


    recent=zodiac_frequency(
        rows,
        20,
        year
    )


    long=zodiac_frequency(
        rows,
        100,
        year
    )



    score={}



    for z in YEAR_ORDER[year]:


        score[z]=(

            recent.get(z,0)
            *
            0.7

            +

            long.get(z,0)
            *
            0.3

        )



    total=sum(
        score.values()
    )


    if total==0:

        return score



    return {


        z:

        round(
            score[z]/total,
            4
        )

        for z in score

    }





# =====================================================
# 热冷生肖
# =====================================================


def zodiac_hot_cold(
        rows,
        year=2026
):


    freq=zodiac_frequency(
        rows,
        100,
        year
    )


    if not freq:

        return {

        }



    hot=max(
        freq,
        key=freq.get
    )


    cold=min(
        freq,
        key=freq.get
    )


    return {


        "hot":

        hot,


        "cold":

        cold,


        "frequency":

        freq

    }





# =====================================================
# 预测5肖
# =====================================================


def predict_5_zodiac(
        rows,
        year=2026
):


    trend=zodiac_trend(
        rows,
        year
    )


    ranking=sorted(

        trend.items(),

        key=lambda x:x[1],

        reverse=True

    )


    return [

        x[0]

        for x in ranking[:5]

    ]





# =====================================================
# 预测2肖
# =====================================================


def predict_2_zodiac(
        rows,
        year=2026
):


    trend=zodiac_trend(
        rows,
        year
    )


    ranking=sorted(

        trend.items(),

        key=lambda x:x[1],

        reverse=True

    )


    return [

        x[0]

        for x in ranking[:2]

    ]





# =====================================================
# 完整分析
# =====================================================


def analyze_zodiac(
        rows,
        year=2026
):


    return {


        "top5":

        predict_5_zodiac(
            rows,
            year
        ),


        "top2":

        predict_2_zodiac(
            rows,
            year
        ),


        "hot_cold":

        zodiac_hot_cold(
            rows,
            year
        ),


        "trend":

        zodiac_trend(
            rows,
            year
        )

    }





# =====================================================
# 测试
# =====================================================

if __name__=="__main__":


    print(
        zodiac_numbers()
    )


    test=[

        {

            "numbers":

            "39 41 08 09 07 14 49"

        }

    ]


    print(
        analyze_zodiac(test)
    )
