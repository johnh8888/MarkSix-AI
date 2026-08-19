# -*- coding:utf-8 -*-

"""
六合彩 AI V3.4 FINAL

API同步模块

支持:
marksix6.net
历史数据同步
最新数据同步
SQLite保存

"""


from __future__ import annotations


import re
import requests
import urllib3


urllib3.disable_warnings()



from config import API_CONFIG


from .database import save_draw




API_HISTORY = API_CONFIG["history"]

API_URLS = {


    "hk":

    API_CONFIG["hk"],


    "newMacau":

    API_CONFIG["newMacau"],


    "oldMacau":

    API_CONFIG["oldMacau"]

}






# ==================================================
# 请求
# ==================================================


def request_api(url):


    print()

    print("正在请求API:")

    print(url)



    r=requests.get(

        url,

        verify=False,

        timeout=20,

        headers={

            "User-Agent":

            "Mozilla/5.0"

        }

    )


    r.raise_for_status()



    print(

        "API请求成功"

    )


    return r.json()






# ==================================================
# 解析历史字符串
# ==================================================


def parse_history_line(text):


    """
    例如:

    2026090 期：39,41,08,09,07,14,49

    """


    if not isinstance(
        text,
        str
    ):

        return None



    m=re.search(

        r"(\d+).*?([\d,]+)",

        text

    )


    if not m:

        return None



    issue=m.group(1)


    nums=[


        int(x)


        for x in m.group(2).split(",")


    ]



    if len(nums)!=7:

        return None



    return {


        "issue":

        issue,


        "numbers":

        nums,


        "special":

        nums[-1]

    }







# ==================================================
# 历史同步
# ==================================================


def sync_history():


    print("="*70)

    print("正在同步历史开奖")

    print("="*70)



    data=request_api(

        API_HISTORY

    )



    result={}



    lottery_data=data.get(

        "lottery_data",

        []

    )




    for item in lottery_data:


        code=item.get(

            "code"

        )


        if code not in [

            "hk",

            "newMacau",

            "oldMacau"

        ]:

            continue




        history=item.get(

            "history",

            []

        )



        count=0



        for row in history:


            info=parse_history_line(

                row

            )


            if not info:

                continue



            save=save_draw(

                code,

                info["issue"],

                info["numbers"],

                info["special"],

                "api"

            )



            if save.get(

                "status"

            )=="new":

                count+=1




        result[code]=count



        print(

            item.get("name"),

            "新增:",

            count,

            "期"

        )



    return result






# ==================================================
# 最新同步
# ==================================================


def sync_latest():


    print("="*70)

    print("正在同步最新开奖")

    print("="*70)



    result={}



    for code,url in API_URLS.items():


        data=request_api(

            url

        )



        item=data.get(

            "lottery_data"

        )



        if isinstance(

            item,

            list

        ):

            item=item[0]



        issue=item.get(

            "expect"

        )



        numbers=item.get(

            "numbers"

        )



        numbers=[

            int(x)

            for x in numbers

        ]



        save=save_draw(

            code,

            issue,

            numbers,

            numbers[-1],

            "api"

        )



        print(

            code,

            "最新期:",

            issue,

            "状态:",

            save.get("status")

        )



        result[code]={

            "issue":

            issue,


            "status":

            save.get("status")

        }



    return result







# ==================================================
# 总同步
# ==================================================


def sync_all():


    print("="*70)

    print("开始API同步")

    print("="*70)



    history=sync_history()



    realtime=sync_latest()



    result={


        "history":

        history,


        "realtime":

        realtime,


        "status":

        "completed"

    }



    print()

    print(

        "API同步结果:"

    )

    print(result)



    return result





__all__=[

    "sync_all",

    "sync_history",

    "sync_latest"

]
