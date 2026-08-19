# -*- coding:utf-8 -*-

"""
六合彩 AI V3.1 FINAL

API 数据解析模块

功能:

1. 解析开奖号码
2. 解析期号
3. 解析彩种
4. 统一数据格式

"""

from __future__ import annotations


import re



# =====================================================
# 号码解析
# =====================================================


def parse_numbers(value):

    """
    任意格式解析号码

    支持:

    [
        1,2,3
    ]

    "01 02 03"

    "01,02,03"

    {
        numbers:[]
    }

    """



    if value is None:

        return []



    # -----------------------------
    # list
    # -----------------------------

    if isinstance(
        value,
        list
    ):


        result=[]


        for x in value:


            nums=parse_numbers(x)


            result.extend(nums)



        return clean_numbers(
            result
        )



    # -----------------------------
    # dict
    # -----------------------------

    if isinstance(
        value,
        dict
    ):


        for key in [

            "numbers",

            "openCode",

            "code",

            "special"

        ]:


            if key in value:


                return parse_numbers(
                    value[key]
                )



        return []



    # -----------------------------
    # 字符串
    # -----------------------------


    nums=re.findall(

        r"\d+",

        str(value)

    )



    return clean_numbers(

        [

            int(x)

            for x in nums

        ]

    )



# =====================================================
# 清洗号码
# =====================================================


def clean_numbers(numbers):


    result=[]


    for n in numbers:


        try:


            n=int(n)



        except:


            continue



        if 1 <= n <= 49:


            result.append(n)



    return result



# =====================================================
# 提取特码
# =====================================================


def extract_special(numbers):


    nums=parse_numbers(
        numbers
    )


    if len(nums)>=7:


        return nums[6]


    return None



# =====================================================
# 提取前六正码
# =====================================================


def extract_main_numbers(numbers):


    nums=parse_numbers(
        numbers
    )


    if len(nums)>=7:


        return nums[:6]


    return nums



# =====================================================
# 期号解析
# =====================================================


def parse_issue(item):


    if not isinstance(
        item,
        dict
    ):


        return None



    for key in [

        "expect",

        "issue",

        "period",

        "no"

    ]:


        if key in item:


            return str(
                item[key]
            )



    return None



# =====================================================
# 彩种解析
# =====================================================


def parse_lottery_name(item):


    if not isinstance(
        item,
        dict
    ):


        return ""



    return str(

        item.get(

            "name",

            ""

        )

    )



# =====================================================
# 单条开奖解析
# =====================================================


def parse_draw(item):


    if not isinstance(
        item,
        dict
    ):


        return None



    numbers=[]



    for key in [

        "numbers",

        "openCode",

        "code",

        "result"

    ]:


        if key in item:


            numbers=parse_numbers(

                item[key]

            )

            break



    if len(numbers)<7:


        return None



    return {


        "issue":

            parse_issue(
                item
            ),


        "numbers":

            numbers[:6],


        "special":

            numbers[6]

    }



# =====================================================
# 历史解析
# =====================================================


def parse_history(history):


    result=[]



    if not isinstance(
        history,
        list
    ):


        return result



    for row in history:


        data=parse_draw(

            row

        )


        if data:


            result.append(
                data
            )



    return result



# =====================================================
# 导出
# =====================================================


__all__=[

    "parse_numbers",

    "clean_numbers",

    "extract_special",

    "extract_main_numbers",

    "parse_issue",

    "parse_lottery_name",

    "parse_draw",

    "parse_history"

]
