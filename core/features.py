# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

features.py

功能:

号码基础特征工程

包含:

1. 特码解析
2. 波色
3. 大小
4. 单双
5. 尾数
6. 分区
7. 邻号
8. 冷热
9. 周期
10. 生肖动态映射

"""


from collections import Counter

from .config import (
    RED_NUMBERS,
    BLUE_NUMBERS,
    GREEN_NUMBERS,
    SHORT_WINDOW,
    ZODIAC_BASE_YEAR,
    ZODIAC_LIST,
)





# =====================================================
# 基础号码解析
# =====================================================


def parse_numbers(row):

    """
    解析开奖数据

    支持:

    {
        numbers:"01,02,03..."
    }

    """

    if not row:
        return []


    numbers = row.get(
        "numbers",
        ""
    )


    if isinstance(
        numbers,
        list
    ):

        return [

            int(x)

            for x in numbers

            if str(x).isdigit()

        ]


    result=[]


    for x in str(numbers).split(","):

        x=x.strip()

        if x.isdigit():

            result.append(
                int(x)
            )


    return result





# =====================================================
# 获取特码
# =====================================================


def get_special(row):

    nums=parse_numbers(row)


    if not nums:

        return None


    return nums[0]





# =====================================================
# 波色
# =====================================================


def get_wave(number):


    if number in RED_NUMBERS:

        return "红"


    if number in BLUE_NUMBERS:

        return "蓝"


    if number in GREEN_NUMBERS:

        return "绿"


    return None





# =====================================================
# 大小
# =====================================================


def get_size(number):

    if number >=25:

        return "大"


    return "小"





# =====================================================
# 单双
# =====================================================


def get_parity(number):

    if number % 2:

        return "单"


    return "双"





# =====================================================
# 尾数
# =====================================================


def get_tail(number):

    return number % 10





# =====================================================
# 七区划分
# =====================================================


def get_zone(number):


    if number <=7:

        return 1


    if number <=14:

        return 2


    if number <=21:

        return 3


    if number <=28:

        return 4


    if number <=35:

        return 5


    if number <=42:

        return 6


    return 7





# =====================================================
# 邻号
# =====================================================


def neighbor_distance(a,b):

    return abs(
        a-b
    )





def is_neighbor(a,b):


    return abs(a-b)<=2





# =====================================================
# 2026生肖动态计算
# =====================================================


def get_zodiac(number,year=2026):

    """
    根据年份计算号码生肖

    2026 = 马年

    """

    offset=(

        year

        -

        ZODIAC_BASE_YEAR

    ) % 12


    index=(

        number

        +

        offset

    ) % 12


    return ZODIAC_LIST[index]





# =====================================================
# 开奖生肖统计
# =====================================================


def zodiac_frequency(rows):


    counter=Counter()


    for row in rows:


        n=get_special(row)


        if not n:

            continue


        z=get_zodiac(n)


        counter[z]+=1



    return counter





# =====================================================
# 波色统计
# =====================================================


def wave_frequency(rows):


    counter=Counter()


    for row in rows:


        n=get_special(row)


        if not n:

            continue


        w=get_wave(n)


        if w:

            counter[w]+=1


    return counter





# =====================================================
# 大小统计
# =====================================================


def size_frequency(rows):


    counter=Counter()


    for row in rows:


        n=get_special(row)


        if not n:

            continue


        counter[
            get_size(n)
        ] +=1


    return counter





# =====================================================
# 单双统计
# =====================================================


def parity_frequency(rows):


    counter=Counter()


    for row in rows:


        n=get_special(row)


        if not n:

            continue


        counter[
            get_parity(n)
        ]+=1


    return counter





# =====================================================
# 号码频率
# =====================================================


def number_frequency(rows):


    counter=Counter()


    for row in rows:


        n=get_special(row)


        if n:

            counter[n]+=1



    return counter





# =====================================================
# 遗漏计算
# =====================================================


def omission_count(rows):


    result={}


    for n in range(1,50):


        count=0


        for row in rows:


            if get_special(row)==n:

                break


            count+=1



        result[n]=count


    return result





# =====================================================
# 尾数统计
# =====================================================


def tail_frequency(rows):


    counter=Counter()


    for row in rows:


        n=get_special(row)


        if n:

            counter[
                get_tail(n)
            ]+=1


    return counter





# =====================================================
# 分区统计
# =====================================================


def zone_frequency(rows):


    counter=Counter()


    for row in rows:


        n=get_special(row)


        if n:

            counter[
                get_zone(n)
            ]+=1


    return counter





# =====================================================
# 周期检测
# =====================================================


def cycle_gap(rows,number):


    gap=0


    for row in rows:


        n=get_special(row)


        if n==number:

            return gap


        gap+=1



    return gap





# =====================================================
# 冷热状态
# =====================================================


def hot_cold(rows):


    freq=number_frequency(
        rows[:SHORT_WINDOW]
    )


    result={}



    for n in range(1,50):


        result[n]=freq.get(
            n,
            0
        )


    return result
