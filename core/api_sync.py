# -*- coding:utf-8 -*-

"""
六合彩 AI V3.1 FINAL

API同步模块

功能:

1. 历史开奖同步
2. 最新开奖同步
3. 自动解析
4. SQLite保存
5. 重复检测

"""

from __future__ import annotations


import requests

import urllib3


from datetime import datetime


from config import (
    API_HISTORY,
    API_REALTIME,
    LOTTERIES
)


from .database import save_draw



urllib3.disable_warnings()



# =====================================================
# 请求
# =====================================================


def request_api(url):


    print()

    print(
        "正在请求API:"
    )

    print(
        url
    )


    headers={

        "User-Agent":

        "Mozilla/5.0",

        "Accept":

        "application/json"

    }



    try:


        r=requests.get(

            url,

            timeout=20,

            headers=headers

        )


        r.raise_for_status()


        print(
            "API请求成功"
        )


        return r.json()



    except Exception as e:


        print(
            "正常SSL请求失败:",
            e
        )


        print(
            "启用SSL备用模式"
        )


        r=requests.get(

            url,

            timeout=20,

            verify=False,

            headers=headers

        )


        r.raise_for_status()


        print(
            "备用SSL请求成功"
        )


        return r.json()



# =====================================================
# 数字解析
# =====================================================


def parse_numbers(value):


    import re


    nums=re.findall(

        r"\d+",

        str(value)

    )


    return [

        int(x)

        for x in nums

        if 1 <= int(x) <=49

    ]



# =====================================================
# 彩种识别
# =====================================================


def identify(name):


    for key,title in LOTTERIES.items():


        if title in name:


            return key


    return None



# =====================================================
# 历史同步
# =====================================================


def sync_history():


    print()

    print(
        "="*70
    )

    print(
        "正在同步历史开奖"
    )

    print(
        "="*70
    )



    data=request_api(

        API_HISTORY

    )



    result={}



    items=data.get(

        "lottery_data",

        []

    )



    for item in items:


        name=item.get(

            "name",

            ""

        )


        key=identify(

            name

        )


        if not key:

            continue



        history=item.get(

            "history",

            []

        )


        new_count=0

        exist_count=0

        error_count=0



        for index,row in enumerate(history):


            nums=parse_numbers(row)



            if len(nums)<7:

                error_count +=1

                continue



            issue=str(

                index

            )



            save_result=save_draw(

                key,

                issue,

                nums[:6],

                nums[6],

                "history_api"

            )



            status=save_result.get(

                "status"

            )



            if status=="new":


                new_count +=1



            elif status=="exists":


                exist_count +=1



            else:


                error_count +=1




        result[key]={


            "新增":

            new_count,


            "已存在":

            exist_count,


            "错误":

            error_count


        }



        print()

        print(

            LOTTERIES[key]

        )

        print(

            "新增:",

            new_count,

            "期"

        )

        print(

            "已存在:",

            exist_count,

            "期"

        )



    return result



# =====================================================
# 实时同步
# =====================================================


def sync_realtime():


    print()

    print(
        "="*70
    )

    print(
        "正在同步最新开奖"
    )

    print(
        "="*70
    )



    result={}



    for key in LOTTERIES:


        try:


            url=(

                API_REALTIME

                +

                "?type="

                +

                key

            )



            data=request_api(

                url

            )



            nums=parse_numbers(

                data

            )



            if len(nums)<7:


                result[key]={

                    "status":

                    "error",

                    "message":

                    "号码不足"

                }


                continue




            issue=data.get(

                "expect",

                datetime.now().strftime(
                    "%Y%m%d"
                )

            )



            save_result=save_draw(

                key,

                issue,

                nums[:6],

                nums[6],

                "realtime_api"

            )



            result[key]=save_result



            print()

            print(

                LOTTERIES[key],

                "最新期:",

                issue

            )

            print(

                "状态:",

                save_result.get(

                    "status"

                )

            )



        except Exception as e:


            result[key]={

                "status":

                "error",

                "message":

                str(e)

            }


            print(

                key,

                e

            )



    return result



# =====================================================
# 总入口
# =====================================================


def sync_all():


    print()

    print(
        "="*70
    )

    print(
        "开始API同步"
    )

    print(
        "="*70
    )



    try:


        history=sync_history()



    except Exception as e:


        print(

            "历史同步失败:",

            e

        )


        history={

            "error":

            str(e)

        }



    try:


        realtime=sync_realtime()



    except Exception as e:


        print(

            "实时同步失败:",

            e

        )


        realtime={

            "error":

            str(e)

        }



    return {


        "history":

        history,


        "realtime":

        realtime,


        "status":

        "completed",


        "time":

        datetime.now().isoformat()

    }



__all__=[

    "sync_all"

]
