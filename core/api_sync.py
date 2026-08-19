# -*- coding:utf-8 -*-

"""
六合彩 AI V3.3 FINAL

API同步模块

功能:

1. 历史开奖同步
2. 最新开奖同步
3. SSL证书异常兼容
4. 自动重试
5. SQLite保存
6. 防重复写入

"""


from __future__ import annotations


import time

import requests

import urllib3



# =====================================================
# SSL兼容
# =====================================================


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
# 请求API
# =====================================================


def request_api(url):


    for i in range(RETRY):


        try:


            print()

            print(
                "正在请求API:"
            )

            print(url)



            response = requests.get(

                url,

                timeout=TIMEOUT,

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



        except Exception as e:


            print(

                "请求失败",

                i + 1,

                e

            )


            time.sleep(2)





    raise Exception(

        "API请求失败:"+url

    )







# =====================================================
# 数字解析
# =====================================================


def parse_numbers(data):


    if data is None:

        return []



    if isinstance(data,list):


        result=[]


        for x in data:


            try:

                result.append(
                    int(x)
                )

            except:

                pass


        return result





    if isinstance(data,str):


        for c in [

            ",",

            "-",

            "|",

            " "

        ]:


            data=data.replace(

                c,

                " "

            )



        return [

            int(x)

            for x in data.split()

            if x.isdigit()

        ]



    return []








# =====================================================
# 获取开奖结果字段
# =====================================================


def extract_item(data):


    if isinstance(data,list):


        if data:

            return data[0]


        return {}




    if isinstance(data,dict):


        if "data" in data:


            return extract_item(

                data["data"]

            )



        if "lottery_data" in data:


            return extract_item(

                data["lottery_data"]

            )



    return data






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



    if len(numbers)==0:

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




    result={}



    mapping={


        "hk":

        "香港六合彩",



        "newMacau":

        "新澳门六合彩",



        "oldMacau":

        "老澳门六合彩"

    }





    lottery_data=data.get(

        "lottery_data",

        {}

    )





    for key,name in mapping.items():


        count=0



        rows=lottery_data.get(

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




    for lottery,url in urls.items():


        try:


            data=request_api(

                url

            )



            item=extract_item(

                data

            )



            status=save_result(

                lottery,

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

                lottery,

                "最新期:",

                issue,

                "状态:",

                status

            )





            result[lottery]={


                "status":

                status,


                "issue":

                issue

            }






        except Exception as e:



            result[lottery]={


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
