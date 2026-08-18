# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.2 FINAL

core/api_sync.py

API数据同步模块

修复:
1. 使用 api3.marksix6.net 新接口
2. 正确解析 numbers
3. 正确读取 expect期号
4. 修复号码污染问题
5. 保留 sync_all 接口
"""


from __future__ import annotations


import json
import ssl
import urllib.request

from datetime import datetime


from .sqlite_manager import save_draw





# =====================================================
# API
# =====================================================


API_REALTIME = (
    "https://api3.marksix6.net/lottery_api.php"
)



LOTTERIES = {

    "hk":
    "香港六合彩",


    "newMacau":
    "新澳门六合彩",


    "oldMacau":
    "老澳门六合彩"

}





# =====================================================
# SSL
# =====================================================


def ssl_context(verify=True):

    if verify:

        return ssl.create_default_context()

    return ssl._create_unverified_context()






# =====================================================
# 请求JSON
# =====================================================


def request_json(url):


    headers = {

        "User-Agent":
        "Mozilla/5.0",

        "Accept":
        "application/json"

    }



    req = urllib.request.Request(

        url,

        headers=headers

    )



    try:


        with urllib.request.urlopen(

            req,

            timeout=20,

            context=ssl_context(True)

        ) as r:


            text = r.read().decode(

                "utf-8-sig"

            )


            return json.loads(text)



    except Exception as e:


        print(

            "SSL正常请求失败:",

            e

        )



        print(

            "启用备用SSL模式"

        )



        with urllib.request.urlopen(

            req,

            timeout=20,

            context=ssl_context(False)

        ) as r:


            text = r.read().decode(

                "utf-8-sig"

            )


            return json.loads(text)







# =====================================================
# 号码解析
# =====================================================


def parse_numbers(numbers):


    result=[]


    for n in numbers:


        try:


            value=int(n)


            if 1 <= value <= 49:

                result.append(value)



        except:


            continue



    return result







# =====================================================
# 单彩种同步
# =====================================================


def sync_one(key):


    url = (

        API_REALTIME

        +

        "?type="

        +

        key

    )



    print()

    print(

        "请求:",

        url

    )



    data=request_json(url)



    nums=parse_numbers(

        data.get(

            "numbers",

            []

        )

    )



    if len(nums)!=7:


        print(

            "号码数量异常:",

            nums

        )


        return False



    issue=str(

        data.get(

            "expect",

            ""

        )

    )



    if not issue:


        issue=datetime.now().strftime(

            "%Y%m%d"

        )



    # 前6个正码

    main_numbers=nums[:6]


    # 第7个特码

    special=nums[6]



    ok=save_draw(

        key,

        issue,

        main_numbers,

        special,

        "api3"

    )



    if ok:


        print(

            LOTTERIES[key],

            "保存成功",

            "期号:",

            issue,

            "特码:",

            special

        )


    else:


        print(

            LOTTERIES[key],

            "保存失败"

        )



    return ok







# =====================================================
# 总同步
# =====================================================


def sync_all():


    print("="*70)

    print(

        "开始API同步"

    )

    print("="*70)



    result={}



    for key in LOTTERIES:


        try:


            result[key]=sync_one(key)



        except Exception as e:


            print(

                key,

                "异常:",

                e

            )


            result[key]=False





    return {


        "realtime":

        result,


        "time":

        datetime.now().isoformat()

    }






__all__=[

    "sync_all"

]
