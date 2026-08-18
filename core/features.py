# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

features.py

高级特征模块

"""


from collections import Counter
import math


from core.config import (
    NUMBER_MIN,
    NUMBER_MAX,
    SHORT_WINDOW,
    MEDIUM_WINDOW,
)



# =========================================================
# 基础解析
# =========================================================


def get_special(row):

    """
    获取特码

    row:
    {
        numbers:
        "01,02,03..."
    }

    """

    try:

        nums = row["numbers"]

        if isinstance(nums,str):

            nums = nums.replace(
                " ",
                ","
            )

            nums = [

                int(x)

                for x in nums.split(",")

                if x.strip()

            ]


        if len(nums) >= 7:

            return nums[-1]


    except:

        pass


    return 0





# =========================================================
# 号码颜色
# =========================================================


RED = {

1,2,7,8,
12,13,18,19,
23,24,29,30,
34,35,40,45,
46

}


BLUE = {

3,4,9,10,
14,15,20,
25,26,31,
36,37,41,
42,47,48

}



GREEN = {

5,6,11,
16,17,21,
22,27,28,
32,33,38,
39,43,44,
49

}




def get_wave(num):

    if num in RED:

        return "红"


    if num in BLUE:

        return "蓝"


    if num in GREEN:

        return "绿"


    return None





# =========================================================
# 大小
# =========================================================


def get_size(num):

    if num >= 25:

        return "大"

    return "小"





# =========================================================
# 单双
# =========================================================


def get_parity(num):

    if num % 2:

        return "单"

    return "双"





# =========================================================
# 尾数
# =========================================================


def get_tail(num):

    return num % 10





# =========================================================
# 区域
# =========================================================


def get_zone(num):

    if num <= 10:

        return 1


    if num <=20:

        return 2


    if num <=30:

        return 3


    if num <=40:

        return 4


    return 5





# =========================================================
# 特码历史
# =========================================================


def special_list(rows):

    result=[]


    for row in rows:

        n=get_special(row)


        if NUMBER_MIN <= n <= NUMBER_MAX:

            result.append(n)


    return result





# =========================================================
# 频率
# =========================================================


def special_frequency(rows):


    nums=special_list(rows)


    c=Counter(nums)


    return {

        i:c.get(i,0)

        for i in range(
            NUMBER_MIN,
            NUMBER_MAX+1
        )

    }





# =========================================================
# 遗漏
# =========================================================


def special_omission(rows):


    nums=special_list(rows)


    result={}


    for n in range(
        NUMBER_MIN,
        NUMBER_MAX+1
    ):


        miss=0


        for x in nums:


            if x==n:

                break


            miss+=1


        else:

            miss=len(nums)



        result[n]=miss



    return result





# =========================================================
# 热冷状态
# =========================================================


def hot_cold_feature(rows):


    nums=special_list(
        rows[:SHORT_WINDOW]
    )


    freq=Counter(nums)


    result={}



    for n in range(
        NUMBER_MIN,
        NUMBER_MAX+1
    ):


        result[n]=freq.get(
            n,
            0
        )



    return result





# =========================================================
# 动量趋势
# =========================================================


def trend_feature(rows):


    short=special_frequency(
        rows[:SHORT_WINDOW]
    )


    medium=special_frequency(
        rows[:MEDIUM_WINDOW]
    )


    result={}


    for n in range(
        NUMBER_MIN,
        NUMBER_MAX+1
    ):


        result[n]=(

            short[n]*0.7

            +

            medium[n]*0.3

        )



    return result





# =========================================================
# 连续压力
# =========================================================


def pressure_feature(rows):


    nums=special_list(rows)


    result={}


    for n in range(
        NUMBER_MIN,
        NUMBER_MAX+1
    ):


        count=0


        for x in nums:


            if x==n:

                count+=1

            else:

                break



        result[n]=count



    return result





# =========================================================
# 号码距离
# =========================================================


def distance_feature(rows):


    nums=special_list(rows)


    result={

        n:0

        for n in range(
            NUMBER_MIN,
            NUMBER_MAX+1
        )

    }


    if len(nums)<2:

        return result



    last=nums[0]



    for n in result:


        result[n]=abs(
            n-last
        )


    return result





# =========================================================
# 尾数趋势
# =========================================================


def tail_feature(rows):


    nums=special_list(rows)


    tails=[

        get_tail(x)

        for x in nums

    ]


    counter=Counter(
        tails
    )


    result={}


    for n in range(
        NUMBER_MIN,
        NUMBER_MAX+1
    ):


        result[n]=counter.get(

            get_tail(n),

            0

        )


    return result





# =========================================================
# 区域趋势
# =========================================================


def zone_feature(rows):


    nums=special_list(rows)


    zones=[

        get_zone(x)

        for x in nums

    ]


    counter=Counter(
        zones
    )


    result={}



    for n in range(
        NUMBER_MIN,
        NUMBER_MAX+1
    ):


        result[n]=counter.get(

            get_zone(n),

            0

        )


    return result





# =========================================================
# 波色趋势
# =========================================================


def wave_feature(rows):


    nums=special_list(rows)


    result={

        "红":0,

        "蓝":0,

        "绿":0

    }



    for n in nums:


        w=get_wave(n)


        if w:

            result[w]+=1



    total=sum(
        result.values()
    )



    if total==0:

        return {

            k:0.33

            for k in result

        }



    return {

        k:

        round(
            v/total,
            4
        )

        for k,v in result.items()

    }





# =========================================================
# 综合特征
# =========================================================


def build_features(rows):


    return {


        "frequency":

        special_frequency(rows),



        "trend":

        trend_feature(rows),



        "omission":

        special_omission(rows),



        "momentum":

        hot_cold_feature(rows),



        "pressure":

        pressure_feature(rows),



        "distance":

        distance_feature(rows),



        "tail":

        tail_feature(rows),



        "zone":

        zone_feature(rows),



        "wave":

        wave_feature(rows),


    }


