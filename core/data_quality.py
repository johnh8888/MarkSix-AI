# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

data_quality.py

数据质量检测模块


功能:

1. 数据合法性检测
2. 数据去重
3. 异常数据过滤
4. 数据质量评分

"""


from collections import Counter





# =====================================================
# 基础配置
# =====================================================


MIN_NUMBER = 1

MAX_NUMBER = 49

REQUIRED_COUNT = 7





# =====================================================
# 获取号码
# =====================================================


def extract_numbers(row):


    if not row:

        return []



    value = (
        row.get("numbers")
        or
        row.get("openCode")
        or
        ""
    )



    if isinstance(
        value,
        list
    ):

        nums=value


    else:

        nums=[]


        for x in str(value).replace(
            "|",
            ","
        ).split(","):


            x=x.strip()


            if x.isdigit():

                nums.append(
                    int(x)
                )



    return nums





# =====================================================
# 检查号码
# =====================================================


def check_numbers(row):


    nums=extract_numbers(
        row
    )


    # 数量

    if len(nums)<REQUIRED_COUNT:

        return False



    # 范围

    for n in nums:


        if n<MIN_NUMBER or n>MAX_NUMBER:

            return False



    return True





# =====================================================
# 期号获取
# =====================================================


def get_issue(row):


    if not row:

        return None



    return (

        row.get("issue")

        or

        row.get("expect")

        or

        row.get("period")

    )





# =====================================================
# 单条质量检测
# =====================================================


def validate_row(row):


    result={

        "valid":

        True,


        "reason":

        []

    }



    if not check_numbers(row):


        result["valid"]=False


        result["reason"].append(
            "号码异常"
        )



    if not get_issue(row):


        result["valid"]=False


        result["reason"].append(
            "缺少期号"
        )



    return result





# =====================================================
# 去重
# =====================================================


def remove_duplicate(rows):


    seen=set()


    clean=[]



    for row in rows:


        issue=get_issue(
            row
        )


        if issue in seen:

            continue



        if not validate_row(row)["valid"]:

            continue



        seen.add(issue)


        clean.append(
            row
        )



    return clean





# =====================================================
# 号码重复检测
# =====================================================


def remove_same_numbers(rows):


    seen=set()


    result=[]



    for row in rows:


        nums=extract_numbers(
            row
        )


        key=tuple(
            sorted(nums)
        )



        if key in seen:

            continue



        seen.add(
            key
        )


        result.append(
            row
        )



    return result





# =====================================================
# 综合清洗
# =====================================================


def clean_history(rows):


    if not rows:

        return []



    rows=remove_duplicate(
        rows
    )


    rows=remove_same_numbers(
        rows
    )


    return rows





# =====================================================
# 数据质量评分
# =====================================================


def quality_score(rows):


    if not rows:

        return 0



    valid=0



    for row in rows:


        if validate_row(row)["valid"]:

            valid+=1



    score=(

        valid /

        len(rows)

    )



    return round(
        score,
        4
    )





# =====================================================
# 数据报告
# =====================================================


def quality_report(rows):


    clean=clean_history(
        rows
    )


    return {


        "original":

        len(rows),



        "clean":

        len(clean),



        "removed":

        len(rows)-len(clean),



        "quality":

        quality_score(
            clean
        )

    }





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    data=[


        {

        "issue":"001",

        "numbers":
        "01,02,03,04,05,06,07"

        },


        {

        "issue":"001",

        "numbers":
        "01,02,03,04,05,06,07"

        },


        {

        "issue":"002",

        "numbers":
        "60,02,03"

        }


    ]



    print(
        quality_report(
            data
        )
    )
