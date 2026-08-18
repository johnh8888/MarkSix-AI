# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

data_source.py

数据源模块


功能:

1. API请求
2. SSL fallback
3. 历史同步
4. 实时同步
5. 数据标准化


"""


import json

import ssl

import urllib.request

from datetime import datetime





# =====================================================
# API配置
# =====================================================


BASE_API = (

    "https://marksix6.net"

)


HISTORY_API = (

    BASE_API +

    "/index.php?api=1"

)



LOTTERY_API = (

    BASE_API +

    "/api/lottery_api.php"

)





LOTTERY_MAP={


    "hk":

    "香港六合彩",


    "newMacau":

    "新澳门六合彩",


    "oldMacau":

    "老澳门六合彩"


}






# =====================================================
# SSL请求
# =====================================================


def request_url(url,timeout=15):


    try:


        context=ssl.create_default_context()



        with urllib.request.urlopen(

            url,

            timeout=timeout,

            context=context

        ) as response:


            return response.read().decode(

                "utf-8"

            )



    except Exception as e:


        print(

            "SSL正常验证失败:",

            e

        )



    # fallback


    try:


        print(

            "尝试受控SSL fallback..."

        )


        context=ssl._create_unverified_context()



        with urllib.request.urlopen(

            url,

            timeout=timeout,

            context=context

        ) as response:


            print(

                "SSL fallback成功"

            )


            return response.read().decode(

                "utf-8"

            )


    except Exception as e:


        print(

            "请求失败:",

            e

        )


        return None





# =====================================================
# JSON解析
# =====================================================


def load_json(url):


    text=request_url(

        url

    )



    if not text:


        return None



    try:


        return json.loads(

            text

        )


    except Exception as e:


        print(

            "JSON解析失败",

            e

        )


        return None





# =====================================================
# 数字解析
# =====================================================


def parse_numbers(value):


    if isinstance(value,list):


        return [

            int(x)

            for x in value

        ]



    if isinstance(value,str):


        value=value.replace(

            ",",

            " "

        )


        return [

            int(x)

            for x in value.split()

            if x.isdigit()

        ]



    return []





# =====================================================
# 标准化开奖
# =====================================================


def normalize_draw(item):


    numbers=[]



    if "numbers" in item:


        numbers=parse_numbers(

            item["numbers"]

        )



    elif "openCode" in item:


        numbers=parse_numbers(

            item["openCode"]

        )



    return {


        "issue":

        str(

            item.get(

                "expect",

                item.get(

                    "issue",

                    ""

                )

            )

        ),



        "numbers":

        numbers,



        "open_time":

        item.get(

            "openTime",

            ""

        ),



        "source":

        "marksix6",



        "update_time":

        datetime.now().isoformat()

    }





# =====================================================
# 获取历史数据
# =====================================================


def fetch_history():



    print("="*60)

    print(

        "正在获取历史数据"

    )

    print(

        HISTORY_API

    )

    print("="*60)



    data=load_json(

        HISTORY_API

    )



    if not data:


        return {}



    result={}



    lottery_data=data.get(

        "lottery_data",

        []

    )



    for lottery in lottery_data:



        name=lottery.get(

            "name",

            ""

        )


        code=lottery.get(

            "code",

            ""

        )



        if code not in LOTTERY_MAP:


            continue



        history=lottery.get(

            "history",

            []

        )



        result[code]=[

            normalize_draw(x)

            for x in history

        ]



    return result





# =====================================================
# 获取实时开奖
# =====================================================


def fetch_latest(code):


    url=(

        LOTTERY_API

        +

        "?type="

        +

        code

    )



    print(

        "请求API:",

        url

    )



    data=load_json(

        url

    )



    if not data:


        return None



    lottery=data.get(

        "lottery_data",

        data

    )



    if isinstance(

        lottery,

        list

    ):


        lottery=lottery[0]



    return normalize_draw(

        lottery

    )





# =====================================================
# 同步三个彩种
# =====================================================


def sync_all():


    result={}



    for code in LOTTERY_MAP:


        print(

            "同步:",

            LOTTERY_MAP[code]

        )


        draw=fetch_latest(

            code

        )


        result[code]=draw



    return result





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    data=sync_all()


    print(

        json.dumps(

            data,

            ensure_ascii=False,

            indent=2

        )

    )
