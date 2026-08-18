# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.3 HISTORICAL FINAL

core/api_sync.py

功能:

1. 历史数据同步
2. 实时开奖同步
3. SSL证书异常处理
4. SQLite保存
5. JSON缓存
6. 三彩种支持

"""


from __future__ import annotations


import json
import ssl
import urllib.request
import urllib.error
import re


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
# SSL
# =====================================================


def create_ssl(
        verify=True
):


    if verify:

        return ssl.create_default_context()


    return ssl._create_unverified_context()







# =====================================================
# HTTP请求
# =====================================================


def request_json(

        url,

        verify=True

):


    req = urllib.request.Request(

        url,

        headers={

            "User-Agent":
            "Mozilla/5.0",

            "Accept":
            "application/json"

        }

    )



    with urllib.request.urlopen(

        req,

        timeout=20,

        context=create_ssl(verify)

    ) as r:


        text=r.read().decode(

            "utf-8-sig"

        )


        return json.loads(text)








def safe_request(url):


    try:


        return request_json(

            url,

            True

        )


    except ssl.SSLError as e:


        print(
            "SSL错误:",
            e
        )


        print(
            "启用SSL备用模式"
        )


        return request_json(

            url,

            False

        )



    except urllib.error.URLError as e:


        print(
            "网络错误:",
            e
        )


        print(
            "尝试备用SSL"
        )


        return request_json(

            url,

            False

        )








# =====================================================
# 缓存
# =====================================================


def save_cache(

        name,

        data

):


    path = CACHE_DIR / (

        name + ".json"

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
# 数字解析
# =====================================================


def parse_numbers(value):


    result=[]


    if isinstance(value,list):


        for x in value:


            m=re.findall(

                r"\d+",

                str(x)

            )


            if m:


                n=int(m[0])


                if 1 <= n <=49:

                    result.append(n)



    else:


        m=re.findall(

            r"\d+",

            str(value)

        )


        for x in m:


            n=int(x)


            if 1<=n<=49:

                result.append(n)



    return result







# =====================================================
# 保存开奖
# =====================================================


def save_result(

        key,

        issue,

        nums,

        source

):


    if len(nums)<7:

        return False



    return save_draw(

        key,

        str(issue),

        nums[:6],

        nums[6],

        source

    )








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



            print()

            print(
                "实时:",
                url
            )



            data=safe_request(

                url

            )



            save_cache(

                key+"_realtime",

                data

            )



            nums=parse_numbers(

                data.get(

                    "numbers",

                    []

                )

            )


            issue=data.get(

                "expect",

                datetime.now().strftime("%Y%m%d")

            )



            ok=save_result(

                key,

                issue,

                nums,

                "realtime"

            )



            print(

                LOTTERIES[key],

                "实时保存",

                ok

            )


            result[key]=ok



        except Exception as e:


            print(

                key,

                "实时失败:",

                e

            )


            result[key]=False



    return result







# =====================================================
# 历史同步
# =====================================================


def sync_history():


    print()

    print(
        "开始历史同步"
    )



    result={}



    try:


        data=safe_request(

            API_HISTORY

        )


        save_cache(

            "history",

            data

        )



    except Exception as e:


        print(

            "历史接口失败:",

            e

        )


        return result






    items=data.get(

        "lottery_data",

        []

    )



    for item in items:


        if not isinstance(item,dict):

            continue



        name=str(

            item.get(

                "name",

                ""

            )

        )



        key=None



        if "香港" in name:

            key="hk"


        elif "新澳门" in name:

            key="newMacau"


        elif "老澳门" in name:

            key="oldMacau"



        if not key:

            continue



        history=item.get(

            "history",

            []

        )



        count=0



        for row in history:


            nums=parse_numbers(

                row

            )



            if len(nums)<7:

                continue



            issue=re.findall(

                r"\d+",

                str(row)

            )



            if not issue:

                continue



            ok=save_result(

                key,

                issue[0],

                nums,

                "history"

            )



            if ok:

                count+=1



        result[key]=count



        print(

            LOTTERIES[key],

            "历史新增",

            count

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

            "历史异常:",

            e

        )



    try:

        realtime=sync_realtime()


    except Exception as e:


        print(

            "实时异常:",

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
