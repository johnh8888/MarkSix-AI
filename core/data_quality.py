# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

data_quality.py

数据质量检测模块


功能:

1. 开奖数据验证
2. 异常过滤
3. 完整性评分
4. 数据清洗


"""


from datetime import datetime





# =====================================================
# 基础配置
# =====================================================


MIN_NUMBER = 1

MAX_NUMBER = 49

VALID_COUNT = 7





# =====================================================
# 检查号码
# =====================================================


def check_numbers(numbers):


    result = {


        "valid":True,


        "errors":[]


    }



    if not isinstance(numbers,list):


        result["valid"]=False


        result["errors"].append(

            "号码格式错误"

        )


        return result





    if len(numbers)!=VALID_COUNT:


        result["valid"]=False


        result["errors"].append(

            f"号码数量错误:{len(numbers)}"

        )





    for n in numbers:


        try:


            n=int(n)


        except:


            result["valid"]=False


            result["errors"].append(

                "存在非数字号码"

            )

            continue





        if n<MIN_NUMBER or n>MAX_NUMBER:


            result["valid"]=False


            result["errors"].append(

                f"号码越界:{n}"

            )



    return result





# =====================================================
# 重复号码检查
# =====================================================


def check_duplicate(numbers):


    return len(numbers)==len(set(numbers))





# =====================================================
# 期号检查
# =====================================================


def check_issue(issue):


    if issue is None:


        return False



    try:


        int(issue)


        return True


    except:


        return False





# =====================================================
# 时间检查
# =====================================================


def check_time(open_time):


    if not open_time:


        return False



    try:


        datetime.fromisoformat(

            str(open_time)

            .replace(

                "Z",

                ""

            )

        )


        return True


    except:


        return False





# =====================================================
# 单条数据检测
# =====================================================


def validate_draw(draw):


    errors=[]



    numbers=draw.get(

        "numbers",

        []

    )



    # 号码

    check=check_numbers(

        numbers

    )



    if not check["valid"]:


        errors.extend(

            check["errors"]

        )





    # 重复


    if not check_duplicate(numbers):


        errors.append(

            "号码重复"

        )





    # 期号


    if not check_issue(

        draw.get(

            "issue"

        )

    ):


        errors.append(

            "期号错误"

        )





    return {


        "valid":

        len(errors)==0,


        "errors":

        errors

    }





# =====================================================
# 批量检测
# =====================================================


def validate_history(rows):


    clean=[]

    bad=[]



    for row in rows:


        result=validate_draw(

            row

        )


        if result["valid"]:


            clean.append(row)


        else:


            bad.append(

                {

                    "data":row,

                    "errors":

                    result["errors"]

                }

            )



    return {


        "total":

        len(rows),


        "valid":

        len(clean),


        "invalid":

        len(bad),


        "clean_data":

        clean,


        "bad_data":

        bad

    }





# =====================================================
# 数据评分
# =====================================================


def quality_score(rows):


    if not rows:


        return 0



    result=validate_history(

        rows

    )



    score=(

        result["valid"]

        /

        result["total"]

    )



    return round(

        score*100,

        2

    )





# =====================================================
# 数据报告
# =====================================================


def quality_report(rows):


    result=validate_history(

        rows

    )



    return {


        "数据总量":

        result["total"],


        "有效":

        result["valid"],


        "异常":

        result["invalid"],


        "质量评分":

        quality_score(

            rows

        )

    }





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    data=[


        {

        "issue":

        "2026090",


        "numbers":

        [

            39,

            41,

            8,

            9,

            7,

            14,

            49

        ]

        }

    ]



    print(

        quality_report(

            data

        )

    )
