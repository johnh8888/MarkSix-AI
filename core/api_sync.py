# -*- coding:utf-8 -*-

"""
六合彩 AI V3.4 FINAL

API同步模块

支持:
marksix6.net

功能:
1. 历史开奖同步
2. 最新开奖同步
3. SSL异常兼容
4. SQLite保存
5. 三彩种统一处理

"""


from __future__ import annotations


import re

import requests

import urllib3


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)



from config import API_CONFIG


from .database import save_draw





# =====================================================
# API
# =====================================================


API_HISTORY = API_CONFIG["history"]


API_URLS = {


    "hk":

    API_CONFIG["hk"],


    "newMacau":

    API_CONFIG["newMacau"],


    "oldMacau":

    API_CONFIG["oldMacau"]

}





# =====================================================
# 请求
# =====================================================


def request_api(url):


    print()

    print(
        "正在请求API:"
    )

    print(url)



    response=requests.get(

        url,

        timeout=20,

        verify=False,

        headers={

            "User-Agent":

            "Mozilla/5.0"

        }

    )



    response.raise_for_status()



    print(

        "API请求成功"

    )



    return response.json()








# =====================================================
# 历史字符串解析
# =====================================================


def parse_history(text):


    """
    例如:

    2026090 期：39,41,08,09,07,14,49

    """


    if not isinstance(
        text,
        str
    ):

        return None



    match=re.search(

        r"(\d+).*?([\d,]+)",

        text

    )



    if not match:

        return None




    issue=match.group(1)



    nums=[


        int(x)


        for x in match.group(2).split(",")

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







# =====================================================
# 历史同步
# =====================================================


def sync_history():


    print("="*70)

    print(
        "正在同步历史开奖"
    )

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



        if code not in API_URLS:


            continue



        history=item.get(

            "history",

            []

        )



        count=0



        for row in history:


            info=parse_history(
                row
            )



            if not info:

                continue



            saved=save_draw(

                code,

                info["issue"],

                info["numbers"],

                info["special"],

                "api"

            )



            if saved.get(

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







# =====================================================
# 最新同步
# =====================================================


def sync_latest():


    print("="*70)

    print(
        "正在同步最新开奖"
    )

    print("="*70)



    result={}



    for code,url in API_URLS.items():


        try:


            data=request_api(

                url

            )



            item=None




            # ----------------------
            # 兼容结构
            # ----------------------


            if isinstance(
                data,
                dict
            ):



                if (

                    "expect" in data

                    or

                    "issue" in data

                ):


                    item=data



                elif "lottery_data" in data:


                    item=data["lottery_data"]


                    if isinstance(
                        item,
                        list
                    ):

                        item=item[0]



                elif "data" in data:


                    item=data["data"]


                    if isinstance(
                        item,
                        list
                    ):

                        item=item[0]




            if not isinstance(
                item,
                dict
            ):


                raise Exception(
                    "API格式错误"
                )






            issue=(

                item.get(
                    "expect"
                )

                or

                item.get(
                    "issue"
                )

            )



            numbers=(

                item.get(
                    "numbers"
                )

                or

                item.get(
                    "openCode"
                )

            )



            if isinstance(
                numbers,
                str
            ):


                numbers=[


                    int(x)


                    for x in numbers.replace(

                        "-",

                        ","

                    ).split(",")


                    if x.strip()

                ]



            else:


                numbers=[

                    int(x)

                    for x in numbers

                ]






            saved=save_draw(

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

                saved.get(
                    "status"
                )

            )



            result[code]={


                "status":

                saved.get(
                    "status"
                ),


                "issue":

                issue

            }




        except Exception as e:



            print(

                code,

                "失败:",

                e

            )



            result[code]={


                "status":

                "error",


                "error":

                str(e)

            }





    return result







# =====================================================
# 总同步入口
# =====================================================


def sync_all():


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
