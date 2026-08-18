# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.2 FINAL

core/data_quality.py


数据质量检测模块


功能：

1. 历史数据检查
2. 开奖号码合法性检查
3. 重复数据检查
4. 数据完整度评分
5. 给预测系统提供安全判断


"""


from __future__ import annotations


from typing import List, Dict, Any





# =====================================================
# 常量
# =====================================================


MIN_HISTORY = 20


MAX_NUMBER = 49


MIN_NUMBER = 1







# =====================================================
# 单期检查
# =====================================================


def validate_draw(

        numbers:List[int],

        special:int

)->Dict[str,Any]:

    """
    检查一期开奖数据

    """



    errors=[]




    if not isinstance(numbers,list):

        errors.append(
            "号码不是列表"
        )

        numbers=[]




    all_numbers=list(numbers)+[special]



    if len(all_numbers)!=7:

        errors.append(
            "开奖号码数量不是7个"
        )



    if len(set(all_numbers))!=7:

        errors.append(
            "号码重复"
        )



    for n in all_numbers:


        if not isinstance(n,int):

            errors.append(
                "存在非整数号码"
            )

            continue



        if n<MIN_NUMBER or n>MAX_NUMBER:

            errors.append(
                f"号码越界:{n}"
            )



    return {


        "valid":

        len(errors)==0,


        "errors":

        errors

    }







# =====================================================
# 历史检查
# =====================================================


def validate_history(

        history:List[Dict[str,Any]]

)->Dict[str,Any]:


    result={


        "total":

        len(history),


        "valid":

        0,


        "invalid":

        0,


        "errors":[]

    }





    if not history:


        result["errors"].append(

            "没有历史数据"

        )

        return result







    issues=set()





    for row in history:



        try:


            issue=str(

                row.get(

                    "issue_no",

                    row.get(

                        "issue",

                        ""

                    )

                )

            )



            if issue in issues:


                result["errors"].append(

                    f"重复期号:{issue}"

                )

            else:

                issues.add(issue)





            nums=row.get(

                "numbers",

                []

            )



            special=int(

                row.get(

                    "special",

                    0

                )

            )



            check=validate_draw(

                nums,

                special

            )



            if check["valid"]:


                result["valid"]+=1


            else:


                result["invalid"]+=1


                result["errors"].extend(

                    check["errors"]

                )




        except Exception as e:


            result["invalid"]+=1


            result["errors"].append(

                str(e)

            )





    return result








# =====================================================
# 数据评分
# =====================================================


def quality_score(

        history:List[Dict[str,Any]]

)->float:


    """

    返回0-1数据可信度

    """



    if not history:


        return 0.0




    result=validate_history(

        history

    )



    total=result["total"]


    if total==0:


        return 0.0




    score=(

        result["valid"]

        /

        total

    )



    # 数据量奖励

    if total>=120:


        score+=0.05


    elif total<MIN_HISTORY:


        score-=0.15




    return max(

        0,

        min(

            1,

            score

        )

    )







# =====================================================
# 预测前安全检查
# =====================================================


def data_ready(

        history:List[Dict[str,Any]]

)->bool:


    if len(history)<MIN_HISTORY:


        return False



    return quality_score(

        history

    )>=0.8







# =====================================================
# 报告
# =====================================================


def quality_report(

        history

):


    return {


        "数据数量":

        len(history),



        "质量评分":

        round(

            quality_score(history),

            4

        ),



        "可以预测":

        data_ready(history),



        "检查":

        validate_history(history)

    }





__all__=[

"validate_draw",

"validate_history",

"quality_score",

"data_ready",

"quality_report"

]
