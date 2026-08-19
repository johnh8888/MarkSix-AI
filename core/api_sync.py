# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

API同步模块

功能:

1. 请求 marksix6 API
2. 自动处理SSL证书过期
3. 解析历史开奖
4. 保存SQLite

支持:

香港六合彩
新澳门六合彩
老澳门六合彩

"""


from __future__ import annotations


import json
import re
import urllib3
import requests



from config import (

    API_HISTORY,

    LOTTERIES

)



from .database import save_draw





urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)





# =====================================================
# API请求
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

        "Mozilla/5.0"


    }



    # -------------------------
    # 第一次正常SSL
    # -------------------------


    try:


        r=requests.get(

            url,

            headers=headers,

            timeout=20

        )


        r.raise_for_status()


        print(
            "SSL正常"
        )


        return r.json()



    except Exception as e:


        print(

            "正常SSL失败:",

            e

        )





    # -------------------------
    # 第二次关闭SSL验证
    # -------------------------


    try:


        print(

            "启用SSL兼容模式"

        )


        r=requests.get(

            url,

            headers=headers,

            timeout=20,

            verify=False

        )


        r.raise_for_status()



        return r.json()



    except Exception as e:


        print(

            "API请求失败:",

            e

        )


        return {}







# =====================================================
# 数字解析
# =====================================================


def parse_numbers(text):


    nums=re.findall(

        r"\d+",

        str(text)

    )


    result=[]



    for x in nums:


        n=int(x)


        if 1<=n<=49:

            result.append(n)



    return result







# =====================================================
# 彩种识别
# =====================================================


def detect_lottery(name):


    name=str(name)



    for key,title in LOTTERIES.items():


        if title in name:


            return key



    return None







# =====================================================
# 历史同步
# =====================================================


def sync_history():


    data=request_api(

        API_HISTORY

    )



    if not data:


        return {}



    result={}



    items=data.get(

        "lottery_data",

        []

    )



    print()

    print(

        "发现彩种:",

        len(items)

    )




    for item in items:



        if not isinstance(

            item,

            dict

        ):

            continue




        key=detect_lottery(

            item.get(

                "name",

                ""

            )

        )



        if not key:

            continue





        history=item.get(

            "history",

            []

        )



        count=0



        for index,row in enumerate(history):



            nums=parse_numbers(

                row

            )



            if len(nums)<7:

                continue





            issue=str(

                index

            )



            ok=save_draw(

                key,

                issue,

                nums[:6],

                nums[6],

                "marksix6"

            )



            if ok:

                count+=1





        result[key]=count



        print(

            LOTTERIES[key],

            "新增",

            count,

            "期"

        )



    return result







# =====================================================
# 总同步入口
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

            "历史同步错误:",

            e

        )


        history={}





    return {


        "history":

        history,


        "status":

        "完成"


    }





__all__=[

    "sync_all"

]
