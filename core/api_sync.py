# -*- coding:utf-8 -*-

"""
六合彩 AI V3.3 FINAL

API同步模块

支持:

- marksix6.net API
- SSL证书过期兼容
- 历史同步
- 最新同步
- SQLite保存
- 多种JSON结构解析

"""


from __future__ import annotations


import time

import requests

import urllib3



urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)



from config import API_CONFIG


from .database import save_draw





# =====================================================
# API地址
# =====================================================


API_HISTORY = API_CONFIG["history"]

API_HK = API_CONFIG["hk"]

API_NEW_MACAU = API_CONFIG["newMacau"]

API_OLD_MACAU = API_CONFIG["oldMacau"]




TIMEOUT = 20

RETRY = 3





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

                verify=False,

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


    if value is None:

        return []



    if isinstance(value,list):


        result=[]


        for x in value:


            try:

                result.append(
                    int(x)
                )

            except:

                pass


        return result





    if isinstance(value,str):


        for c in [
            ",",
            "-",
            "|",
            " "
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
# 提取一期数据
# =====================================================


def normalize_item(item):


    if isinstance(item,list):

        if item:

            return item[0]

        return {}



    if isinstance(item,dict):


        if "data" in item:

            return normalize_item(
                item["data"]
            )



    return item






# =====================================================
# 保存开奖
# =====================================================


def save_result(
        lottery,
        item
):


    item=normalize_item(
        item
    )


    if not isinstance(item,dict):

        return False




    issue=(

        item.get("expect")

        or

        item.get("issue")

        or

        item.get("period")

    )



    code=(

        item.get("openCode")

        or

        item.get("numbers")

        or

        item.get("openNumber")

    )



    numbers=parse_numbers(
        code
    )



    if not issue:

        return False



    if not numbers:

        return False



    special=numbers[-1]



    result=save_draw(

        lottery,

        str(issue),

        numbers,

        special,

        "api"

    )



    return result.get(
        "status"
    )








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



    result={



    }



    names={


        "hk":
        "香港六合彩",


        "newMacau":
        "新澳门六合彩",


        "oldMacau":
        "老澳门六合彩"

    }




    lottery_data=data.get(

        "lottery_data",

        []

    )



    groups={

        "hk":[],

        "newMacau":[],

        "oldMacau":[]

    }




    # ==================================
    # API返回list
    # ==================================


    if isinstance(
        lottery_data,
        list
    ):


        for block in lottery_data:


            if not isinstance(
                block,
                dict
            ):

                continue



            name=str(

                block.get(
                    "name",
                    ""
                )

            )



            rows=(

                block.get(
                    "history"
                )

                or

                block.get(
                    "data"
                )

                or []

            )



            if "香港" in name:


                groups["hk"]=rows



            elif "新澳门" in name:


                groups["newMacau"]=rows



            elif "老澳门" in name:


                groups["oldMacau"]=rows






    # ==================================
    # API返回dict
    # ==================================


    elif isinstance(
        lottery_data,
        dict
    ):


        groups=lottery_data






    for key,name in names.items():


        count=0



        rows=groups.get(

            key,

            []

        )



        for item in rows:


            if save_result(

                key,

                item

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



            item=normalize_item(
                data
            )



            status=save_result(

                key,

                item

            )



            issue=""



            if isinstance(
                item,
                dict
            ):


                issue=(

                    item.get(
                        "expect",
                        ""
                    )

                    or

                    item.get(
                        "issue",
                        ""
                    )

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
# 总入口
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
