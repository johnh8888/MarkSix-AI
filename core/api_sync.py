# -*- coding:utf-8 -*-

"""
六合彩 AI V3.3 FINAL

API同步模块

功能:

1. 同步历史
2. 同步最新
3. 写入SQLite
4. 防重复

"""


from __future__ import annotations


import time

import requests



from config import API_CONFIG


from .database import save_draw





TIMEOUT = 15

RETRY = 3




API_HISTORY = API_CONFIG["history"]

API_HK = API_CONFIG["hk"]

API_NEW_MACAU = API_CONFIG["newMacau"]

API_OLD_MACAU = API_CONFIG["oldMacau"]





# =====================================================
# 请求
# =====================================================


def request_api(url):


    for i in range(RETRY):


        try:


            print()

            print(
                "正在请求API:"
            )

            print(url)



            r=requests.get(

                url,

                timeout=TIMEOUT,

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



        except Exception as e:


            print(

                "请求失败",

                i+1,

                e

            )


            time.sleep(2)



    raise Exception(

        "API请求失败"

    )






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


        for c in [

            ",",

            "-",

            "|"

        ]:

            value=value.replace(

                c,

                " "

            )


        return [

            int(x)

            for x in value.split()

            if x.isdigit()

        ]



    return []






# =====================================================
# 保存开奖
# =====================================================


def save_result(
        lottery,
        item
):


    if not isinstance(item,dict):

        return False



    issue=(

        item.get("expect")

        or

        item.get("issue")

    )



    code=(

        item.get("openCode")

        or

        item.get("numbers")

    )



    numbers=parse_numbers(code)



    if not issue or len(numbers)==0:

        return False




    special=numbers[-1]



    result=save_draw(

        lottery,

        issue,

        numbers,

        special,

        "api"

    )



    return result.get("status")






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



    # 兼容API结构


    lottery_data=data.get(

        "lottery_data",

        {}

    )



    mapping={


        "hk":

            "香港六合彩",


        "newMacau":

            "新澳门六合彩",


        "oldMacau":

            "老澳门六合彩"

    }



    for key,name in mapping.items():


        count=0



        rows=lottery_data.get(

            key,

            []

        )



        for row in rows:


            if save_result(

                key,

                row

            ):

                count+=1




        result[key]=count



        print(

            name,

            "新增:",

            count,

            "期"

        )



    return result







# =====================================================
# 最新同步
# =====================================================


def sync_latest():


    print()

    print("="*70)

    print(

        "正在同步最新开奖"

    )

    print("="*70)



    urls={


        "hk":

        API_HK,


        "newMacau":

        API_NEW_MACAU,


        "oldMacau":

        API_OLD_MACAU

    }




    result={}



    for key,url in urls.items():


        try:


            data=request_api(

                url

            )



            item=data



            if isinstance(data,dict):


                if "data" in data:

                    item=data["data"]



                if isinstance(item,list):

                    item=item[0]




            status=save_result(

                key,

                item

            )



            issue=""



            if isinstance(item,dict):

                issue=(

                    item.get("expect")

                    or

                    item.get("issue")

                    or ""

                )




            print(

                key,

                "最新期:",

                issue,

                "状态:",

                status

            )



            result[key]={


                "status":

                status,


                "issue":

                issue

            }




        except Exception as e:


            result[key]={

                "error":

                str(e)

            }



    return result






# =====================================================
# 总同步入口
# =====================================================


def sync_all():


    print()

    print("="*70)

    print(

        "开始API同步"

    )

    print("="*70)



    history=sync_history()



    realtime=sync_latest()




    return {


        "history":

        history,


        "realtime":

        realtime,


        "status":

        "completed"

    }





__all__=[


    "sync_all",

    "sync_history",

    "sync_latest"

]
