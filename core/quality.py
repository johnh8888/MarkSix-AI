# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

数据质量检测模块

功能:

历史数量检测
重复检测
号码检测
数据评分

"""


from collections import Counter





# =====================================================
# 数字合法性
# =====================================================


def check_numbers(draw):


    numbers=draw.get(

        "numbers",

        []

    )


    special=draw.get(

        "special"

    )



    if len(numbers)!=6:


        return False




    for n in numbers:


        if not 1 <= n <=49:


            return False




    if special is not None:


        if not 1 <= int(special) <=49:


            return False




    return True






# =====================================================
# 重复检测
# =====================================================


def check_duplicate(history):


    issues=[


        x.get("issue")

        for x in history

    ]



    count=Counter(

        issues

    )



    duplicates=[


        k

        for k,v in count.items()

        if v>1

    ]



    return duplicates





# =====================================================
# 完整度评分
# =====================================================


def score_history(history):


    total=len(history)



    if total>=500:


        score=100



    elif total>=300:


        score=90



    elif total>=100:


        score=80



    elif total>=50:


        score=60



    else:


        score=max(

            total,

            10

        )




    return score





# =====================================================
# 数据质量分析
# =====================================================


def analyze_quality(history):


    total=len(history)



    invalid=0



    for row in history:


        if not check_numbers(row):


            invalid+=1




    duplicates=check_duplicate(

        history

    )



    score=score_history(

        history

    )



    if total>=100:


        status="READY"



    elif total>=30:


        status="LIMITED"



    else:


        status="WAIT"





    return {


        "历史数量":

        total,



        "异常数据":

        invalid,



        "重复期":

        len(duplicates),



        "质量评分":

        score,



        "模型状态":

        status

    }






__all__=[

    "analyze_quality",

    "check_numbers",

    "score_history"

]
