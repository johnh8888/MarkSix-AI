# -*- coding:utf-8 -*-

"""
六合彩 AI V3.2 FINAL

API同步模块

功能:

1. 历史开奖同步
2. 最新开奖同步
3. 多格式解析
4. SQLite保存

支持:

香港六合彩
新澳门六合彩
老澳门六合彩

"""


from __future__ import annotations


import requests
import urllib3
import re
import json


from datetime import datetime


from config import (
    API_HISTORY,
    API_REALTIME,
    LOTTERIES
)


from .database import save_draw



urllib3.disable_warnings()



# =====================================================
# HTTP请求
# =====================================================


def request_api(url):


    print()

    print(
        "正在请求API:"
    )

    print(url)



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

            headers=headers,

            verify=False

        )


        r.raise_for_status()


        print(
            "API请求成功"
        )


        return r.json()



    except Exception as e:


        print(
            "API失败:",
            e
        )


        return {}





# =====================================================
# 彩种识别
# =====================================================


def identify(name):


    text=str(name)



    if "香港" in text:

        return "hk"



    if "新澳门" in text:

        return "newMacau"



    if "老澳门" in text:

        return "oldMacau"



    return None





# =====================================================
# 数字解析
# =====================================================


def parse_numbers(value):


    if value is None:

        return []



    nums=re.findall(

        r"\d+",

        str(value)

    )



    result=[]



    for x in nums:


        n=int(x)


        if 1<=n<=49:

            result.append(n)



    return result





# =====================================================
# 单条开奖解析
# =====================================================


def parse_draw(row):


    issue=None

    numbers=[]



    if isinstance(row,dict):


        issue=(

            row.get("expect")

            or

            row.get("issue")

            or

            row.get("period")

        )



        code=(

            row.get("openCode")

            or

            row.get("code")

            or

            row.get("numbers")

        )


        numbers=parse_numbers(code)



    else:


        text=str(row)


        m=re.search(

            r"(\d{3,})",

            text

        )


        if m:

            issue=m.group(1)



        numbers=parse_numbers(text)




    if len(numbers)>=7:


        return {


            "issue":str(issue),


            "numbers":numbers[:6],


            "special":numbers[6]

        }



    return None





# =====================================================
# 历史同步
# =====================================================


def sync_history():


    print()

    print("="*70)

    print(
        "正在同步历史开奖"
    )

    print("="*70)



    data=request_api(

        API_HISTORY

    )



    result={}



    items=data.get(

        "lottery_data",

        []

    )



    for item in items:


        key=identify(

            item.get(

                "name",

                ""

            )

        )



        if not key:

            continue



        count=0



        history=(

            item.get(

                "history",

                []

            )

        )



        for row in history:


            draw=parse_draw(row)



            if not draw:

                continue



            ok=save_draw(

                key,

                draw["issue"],

                draw["numbers"],

                draw["special"],

                "history_api"

            )



            if ok:

                count+=1



        result[key]=count



        print(

            LOTTERIES[key],

            "新增:",

            count,

            "期"

        )



    return result






# =====================================================
# 最新同步
# =====================================================


def sync_realtime():


    result={}



    print()

    print("="*70)

    print(

        "正在同步最新开奖"

    )

    print("="*70)




    for key in LOTTERIES:


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



        draw=parse_draw(

            data

        )



        if not draw:


            result[key]={

                "status":

                "empty"

            }


            continue





        ok=save_draw(

            key,

            draw["issue"],

            draw["numbers"],

            draw["special"],

            "realtime_api"

        )



        result[key]={


            "status":

            "new"

            if ok

            else

            "exists",



            "issue":

            draw["issue"]

        }




        print(

            LOTTERIES[key],

            "最新期:",

            draw["issue"],

            "状态:",

            result[key]["status"]

        )



    return result






# =====================================================
# 总入口
# =====================================================


def sync_all():


    print("="*70)

    print(
        "开始API同步"
    )

    print("="*70)



    history={}


    realtime={}



    try:


        history=sync_history()



    except Exception as e:


        print(

            "历史同步错误:",

            e

        )



    try:


        realtime=sync_realtime()



    except Exception as e:


        print(

            "实时同步错误:",

            e

        )




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
