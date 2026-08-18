# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.0

data_source.py

数据源管理模块


功能：

1. API请求
2. SSL异常处理
3. 历史开奖同步
4. 最新开奖同步
5. 数据格式统一


"""


import json

import ssl

import urllib.request

from datetime import datetime





from .config import (

    历史数据接口,

    实时数据接口,

    彩种列表

)





# =====================================================
# SSL请求
# =====================================================


def 请求数据(url):


    try:


        print(

            "正在请求数据:",

            url

        )


        ssl_context = ssl.create_default_context()



        request = urllib.request.Request(

            url,

            headers={

                "User-Agent":

                "Mozilla/5.0"

            }

        )



        with urllib.request.urlopen(

            request,

            timeout=15,

            context=ssl_context

        ) as response:


            return response.read().decode(

                "utf-8"

            )



    except Exception as e:


        print(

            "⚠️ SSL正常验证失败:",

            e

        )





    # =================================================
    # SSL备用模式
    # =================================================


    try:


        print(

            "正在尝试备用SSL模式..."

        )



        ssl_context = ssl._create_unverified_context()



        request = urllib.request.Request(

            url,

            headers={

                "User-Agent":

                "Mozilla/5.0"

            }

        )



        with urllib.request.urlopen(

            request,

            timeout=15,

            context=ssl_context

        ) as response:


            print(

                "✅ SSL备用模式成功"

            )



            return response.read().decode(

                "utf-8"

            )



    except Exception as e:


        print(

            "❌ 数据请求失败:",

            e

        )


        return None





# =====================================================
# JSON解析
# =====================================================


def 解析JSON(text):


    if not text:


        return None



    try:


        return json.loads(

            text

        )


    except Exception as e:


        print(

            "JSON解析失败:",

            e

        )


        return None





# =====================================================
# 号码标准化
# =====================================================


def 标准化号码(numbers):


    if isinstance(

        numbers,

        list

    ):


        return [

            int(x)

            for x in numbers

        ]



    if isinstance(

        numbers,

        str

    ):


        numbers=numbers.replace(

            ",",

            " "

        )



        return [

            int(x)

            for x in numbers.split()

            if x.isdigit()

        ]



    return []





# =====================================================
# 单期开奖转换
# =====================================================


def 标准化开奖(data):


    if not data:


        return None



    号码=[]



    if "numbers" in data:


        号码=标准化号码(

            data["numbers"]

        )


    elif "openCode" in data:


        号码=标准化号码(

            data["openCode"]

        )





    return {


        "期号":

        str(

            data.get(

                "expect",

                data.get(

                    "issue",

                    ""

                )

            )

        ),



        "号码":

        号码,



        "生肖":

        data.get(

            "zodiac",

            []

        ),



        "波色":

        data.get(

            "wave",

            []

        ),



        "开奖时间":

        data.get(

            "openTime",

            ""

        ),



        "来源":

        "marksix6"



    }





# =====================================================
# 获取历史开奖
# =====================================================


def 获取历史数据():


    print("="*60)

    print(

        "正在获取历史开奖数据"

    )

    print(

        历史数据接口

    )

    print("="*60)



    text = 请求数据(

        历史数据接口

    )



    data = 解析JSON(

        text

    )



    if not data:


        return {}





    result={}





    彩种数据=data.get(

        "lottery_data",

        []

    )



    for item in 彩种数据:


        code=item.get(

            "code",

            ""

        )



        if code not in 彩种列表:


            continue



        history=item.get(

            "history",

            []

        )



        result[code]=[

            标准化开奖(x)

            for x in history

        ]



        print(

            彩种列表[code],

            "历史数据:",

            len(result[code]),

            "期"

        )



    return result





# =====================================================
# 获取最新开奖
# =====================================================


def 获取最新开奖(code):


    url=(

        实时数据接口

        +

        "?type="

        +

        code

    )



    print(

        "正在更新:",

        彩种列表.get(

            code,

            code

        )

    )



    text=请求数据(

        url

    )



    data=解析JSON(

        text

    )



    if not data:


        return None





    if isinstance(

        data.get(

            "lottery_data"

        ),

        list

    ):


        data=data["lottery_data"][0]



    return 标准化开奖(

        data

    )





# =====================================================
# 同步全部彩种
# =====================================================


def 同步全部彩种():



    result={}



    for code in 彩种列表:


        result[code]=获取最新开奖(

            code

        )



    return result





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    历史=获取历史数据()



    print(

        "同步完成"

    )



    最新=同步全部彩种()



    print(

        最新

    )
