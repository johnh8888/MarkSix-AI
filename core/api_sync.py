# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.3

core/api_sync.py

API同步模块

功能:

1. api3.marksix6.net实时接口
2. SQLite保存
3. JSON本地缓存
4. 自动去重
5. 支持多彩种

"""


from __future__ import annotations


import json
import ssl
import urllib.request


from pathlib import Path
from datetime import datetime


from .sqlite_manager import save_draw





# =====================================================
# 路径
# =====================================================


BASE_DIR = Path(__file__).resolve().parent.parent


CACHE_DIR = BASE_DIR / "cache"


CACHE_DIR.mkdir(
    exist_ok=True
)





# =====================================================
# API
# =====================================================


API_URL = (
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


def ssl_context():

    return ssl.create_default_context()






# =====================================================
# 请求JSON
# =====================================================


def request_json(url):


    req = urllib.request.Request(

        url,

        headers={

            "User-Agent":
            "Mozilla/5.0",

            "Accept":
            "application/json"

        }

    )


    try:


        with urllib.request.urlopen(

            req,

            timeout=20,

            context=ssl_context()

        ) as r:


            text = r.read().decode(

                "utf-8-sig"

            )


            return json.loads(text)



    except Exception as e:


        print(
            "API请求失败:",
            e
        )


        raise






# =====================================================
# 保存缓存
# =====================================================


def save_cache(
        key,
        data
):


    path = CACHE_DIR / (
        key + ".json"
    )


    path.write_text(

        json.dumps(

            data,

            ensure_ascii=False,

            indent=2

        ),

        encoding="utf-8"

    )







# =====================================================
# 号码处理
# =====================================================


def parse_numbers(data):


    nums=[]


    values=data.get(

        "numbers",

        []

    )



    for n in values:


        try:


            n=int(n)


            if 1 <= n <=49:

                nums.append(n)



        except:


            pass



    return nums







# =====================================================
# 单彩种同步
# =====================================================


def sync_one(key):


    url = (

        API_URL

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



    data=request_json(
        url
    )



    save_cache(
        key,
        data
    )



    nums=parse_numbers(
        data
    )



    if len(nums)!=7:


        print(
            "号码异常:",
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



    # 前六正码

    normal=nums[:6]


    # 最后特码

    special=nums[6]



    result=save_draw(

        key,

        issue,

        normal,

        special,

        "api3"

    )



    if result:


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



    return result







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


            result[key]=sync_one(
                key
            )



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
