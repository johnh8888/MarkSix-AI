# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

features.py

基础特征工程模块

功能：

1. 波色
2. 大小
3. 单双
4. 尾数
5. 分区
6. 余数
7. 距离
8. 连号
9. 生肖调用


"""


from collections import Counter


from .zodiac_model import get_zodiac





# =====================================================
# 波色定义
# =====================================================


RED = {

    1,2,7,8,
    12,13,18,19,
    23,24,29,30,
    34,35,40,45,
    46

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
# 波色
# =====================================================


def get_wave(num):


    num=int(num)


    if num in RED:

        return "红"


    elif num in BLUE:

        return "蓝"


    elif num in GREEN:

        return "绿"


    return None





# =====================================================
# 大小
# =====================================================


def get_size(num):


    num=int(num)


    return (

        "大"

        if num>=25

        else

        "小"

    )





# =====================================================
# 单双
# =====================================================


def get_parity(num):


    num=int(num)


    return (

        "单"

        if num%2

        else

        "双"

    )





# =====================================================
# 尾数
# =====================================================


def get_tail(num):


    return int(num)%10





# =====================================================
# 7余数
# =====================================================


def get_mod7(num):


    return int(num)%7





# =====================================================
# 五区
# =====================================================


def get_zone(num):


    num=int(num)



    if num<=10:

        return 1


    elif num<=20:

        return 2


    elif num<=30:

        return 3


    elif num<=40:

        return 4


    else:

        return 5





# =====================================================
# 数字距离
# =====================================================


def cross_distance(
        a,
        b
):


    return abs(

        int(a)-int(b)

    )





# =====================================================
# 连号检测
# =====================================================


def consecutive_numbers(nums):


    nums=sorted(

        [

            int(x)

            for x in nums

        ]

    )


    result=[]



    for i in range(
        len(nums)-1
    ):


        if nums[i+1]-nums[i]==1:


            result.append(

                (

                    nums[i],

                    nums[i+1]

                )

            )


    return result





# =====================================================
# 单号码完整特征
# =====================================================


def number_feature(
        num,
        year=2026
):


    num=int(num)



    return {


        "number":

        num,


        "zodiac":

        get_zodiac(

            num,

            year

        ),


        "wave":

        get_wave(num),


        "size":

        get_size(num),


        "parity":

        get_parity(num),


        "tail":

        get_tail(num),


        "mod7":

        get_mod7(num),


        "zone":

        get_zone(num)

    }





# =====================================================
# 开奖特征
# =====================================================


def draw_feature(
        numbers,
        year=2026
):


    nums=[

        int(x)

        for x in numbers

    ]



    return {


        "numbers":

        nums,


        "zodiac":

        [

            get_zodiac(
                x,
                year
            )

            for x in nums

        ],



        "wave":

        [

            get_wave(x)

            for x in nums

        ],



        "size":

        [

            get_size(x)

            for x in nums

        ],



        "parity":

        [

            get_parity(x)

            for x in nums

        ],



        "tail":

        [

            get_tail(x)

            for x in nums

        ],



        "zone":

        [

            get_zone(x)

            for x in nums

        ],



        "continue":

        consecutive_numbers(nums)

    }





# =====================================================
# 历史统计
# =====================================================


def feature_frequency(
        rows,
        key,
        limit=100
):


    counter=Counter()



    for row in rows[:limit]:


        values=row.get(
            key,
            []
        )


        for v in values:


            counter[v]+=1



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
# 号码列表解析
# =====================================================


def parse_numbers(text):


    if isinstance(
        text,
        list
    ):

        return [

            int(x)

            for x in text

        ]



    return [

        int(x)

        for x in str(text)

        .replace(","," ")

        .split()

    ]





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    nums=[

        39,
        41,
        8,
        9,
        7,
        14,
        49

    ]


    print(

        draw_feature(nums)

    )
