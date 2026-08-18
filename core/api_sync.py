# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/api_sync.py

在线数据同步模块

流程：

marksix6 API
        |
        ↓
数据解析
        |
        ↓
SQLite保存


支持：

香港六合彩
新澳门六合彩
老澳门六合彩

"""


from __future__ import annotations


import json
import ssl
import urllib.request
import re

from datetime import datetime


from .sqlite_manager import (
    save_draw
)



# =====================================================
# API
# =====================================================


API_HISTORY = (
    "https://marksix6.net/index.php?api=1"
)


API_REALTIME = (
    "https://marksix6.net/api/lottery_api.php"
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
# HTTP
# =====================================================


def ssl_context(verify=True):

    if verify:

        return ssl.create_default_context()

    return ssl._create_unverified_context()



def request_json(url):


    headers={

        "User-Agent":
        "Mozilla/5.0",

        "Accept":
        "application/json"

    }


    req=urllib.request.Request(
        url,
        headers=headers
    )


    try:


        with urllib.request.urlopen(
            req,
            timeout=20,
            context=ssl_context(True)
        ) as r:


            text=r.read().decode(
                "utf-8-sig"
            )


            return json.loads(text)



    except Exception as e:


        print(
            "SSL正常失败:",
            e
        )


        # 仅指定网站关闭验证

        with urllib.request.urlopen(
            req,
            timeout=20,
            context=ssl_context(False)
        ) as r:


            text=r.read().decode(
                "utf-8-sig"
            )


            return json.loads(text)





# =====================================================
# 数字解析
# =====================================================


def parse_numbers(value):


    if isinstance(value,list):

        result=[]

        for x in value:

            n=int(
                re.findall(
                    r"\d+",
                    str(x)
                )[0]
            )

            result.append(n)


        return result



    nums=re.findall(
        r"\d+",
        str(value)
    )


    return [
        int(x)
        for x in nums
        if 1<=int(x)<=49
    ]





# =====================================================
# 彩种识别
# =====================================================


def identify(item):


    text=(

        str(
            item.get("name","")
        )

        +

        str(
            item.get("type","")
        )

    )


    if "香港" in text:

        return "hk"


    if "新澳门" in text:

        return "newMacau"


    if "老澳门" in text:

        return "oldMacau"



    return None





# =====================================================
# 历史同步
# =====================================================


def sync_history():


    print(
        "正在获取历史数据"
    )


    data=request_json(
        API_HISTORY
    )


    result={}


    items=data.get(
        "lottery_data",
        []
    )


    for item in items:


        if not isinstance(
            item,
            dict
        ):

            continue



        key=identify(item)


        if not key:

            continue



        history=item.get(
            "history",
            []
        )


        count=0


        for row in history:


            m=re.search(
                r"(\d+)期.*?([\d, ]+)",
                str(row)
            )


            if not m:

                continue



            issue=m.group(1)


            nums=parse_numbers(
                m.group(2)
            )


            if len(nums)<7:

                continue



            status=save_draw(

                key,

                issue,

                nums[:6],

                nums[6],

                "history_api"

            )


            if status:

                count+=1



        result[key]=count



        print(
            LOTTERIES[key],
            "同步",
            count,
            "期"
        )


    return result





# =====================================================
# 实时同步
# =====================================================


def sync_realtime():


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


            data=request_json(
                url
            )


            nums=parse_numbers(
                json.dumps(data,ensure_ascii=False)
            )


            if len(nums)<7:

                result[key]=False

                continue



            issue=str(
                datetime.now()
                .strftime("%Y%m%d")
            )


            ok=save_draw(

                key,

                issue,

                nums[:6],

                nums[6],

                "realtime_api"

            )


            result[key]=ok



        except Exception as e:


            print(
                key,
                e
            )

            result[key]=False



    return result





# =====================================================
# 总同步入口
# =====================================================


def sync_all():


    print(
        "="*70
    )

    print(
        "开始API同步"
    )

    print(
        "="*70
    )



    history={}


    try:

        history=sync_history()


    except Exception as e:


        print(
            "历史同步失败:",
            e
        )



    realtime={}


    try:

        realtime=sync_realtime()


    except Exception as e:


        print(
            "实时同步失败:",
            e
        )



    return {


        "history":

        history,


        "realtime":

        realtime,


        "time":

        datetime.now().isoformat()

    }





__all__=[

    "sync_all"

]
