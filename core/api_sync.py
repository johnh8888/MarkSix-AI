# -*- coding:utf-8 -*-

"""
六合彩 AI V3.3 FINAL

API同步模块


功能:

1. 请求历史数据
2. 请求最新开奖
3. 解析开奖
4. 写入SQLite
5. 防重复
6. 自动重试

"""


from __future__ import annotations


import time

import requests



from config import (
    API_CONFIG,
    API_HISTORY,
    API_HK,
    API_NEW_MACAU,
    API_OLD_MACAU
)



from .database import (
    save_draw
)





# =====================================================
# 请求配置
# =====================================================


TIMEOUT = 15


RETRY = 3






# =====================================================
# HTTP请求
# =====================================================


def request_json(url):


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



            data=r.json()



            print(
                "API请求成功"
            )


            return data




        except Exception as e:


            print(

                "API失败",

                i+1,

                "/",

                RETRY,

                e

            )


            time.sleep(2)





    raise Exception(

        "API请求失败:"+url

    )








# =====================================================
# 数字解析
# =====================================================


def parse_numbers(value):


    if value is None:

        return []



    if isinstance(value,list):


        return [

            int(x)

            for x in value

            if str(x).isdigit()

        ]





    if isinstance(value,str):


        value=value.replace(

            ",",

            " "

        )


        value=value.replace(

            "-",

            " "

        )


        return [

            int(x)

            for x in value.split()

            if x.isdigit()

        ]



    return []








# =====================================================
# 提取特码
# =====================================================


def parse_special(item):


    # openCode

    if "openCode" in item:


        nums=parse_numbers(

            item["openCode"]

        )


        if nums:

            return nums[-1]





    # numbers

    if "numbers" in item:


        nums=parse_numbers(

            item["numbers"]

        )


        if nums:

            return nums[-1]






    # openNumber


    if "openNumber" in item:


        nums=parse_numbers(

            item["openNumber"]

        )


        if nums:

            return nums[-1]




    return None








# =====================================================
# 保存一期开奖结果
# =====================================================


def save_item(
        lottery,
        item
):


    issue=(

        item.get("issue")

        or

        item.get("expect")

        or

        item.get("period")

        or

        item.get("draw")

    )



    if issue is None:


        return False




    nums=parse_numbers(

        item.get(

            "numbers"

        )

    )



    if not nums:


        nums=parse_numbers(

            item.get(

                "openCode"

            )

        )



    special=parse_special(

        item

    )



    if special is None:


        return False





    result=save_draw(


        lottery,


        str(issue),


        nums,


        special,


        "api"


    )




    return result.get(

        "status"

    )









# =====================================================
# 同步历史
# =====================================================


def sync_history():


    print()

    print("="*70)

    print(

        "正在同步历史开奖"

    )

    print("="*70)



    data=request_json(

        API_HISTORY

    )



    result={}



    lottery_map={


        "hk":

            "香港六合彩",



        "newMacau":

            "新澳门六合彩",



        "oldMacau":

            "老澳门六合彩"

    }



    # API可能返回 lottery_data


    history=data.get(

        "lottery_data",

        data

    )





    for key,name in lottery_map.items():


        count=0



        rows=[]



        if isinstance(history,dict):


            rows=history.get(

                key,

                []

            )



        elif isinstance(history,list):


            rows=history




        for item in rows:


            if save_item(

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
# 同步最新
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


            data=request_json(

                url

            )




            item=data





            if isinstance(data,dict):


                if "data" in data:

                    item=data["data"]



                elif "lottery_data" in data:

                    item=data["lottery_data"]





                if isinstance(item,list):

                    item=item[0]





            status=save_item(

                lottery,

                item

            )



            issue=(

                item.get("issue")

                or

                item.get("expect")

                if isinstance(item,dict)

                else ""

            )





            result[lottery]={


                "status":

                    status,


                "issue":

                    str(issue)

            }




            print(

                lottery,

                "最新期:",

                issue,

                "状态:",

                status

            )





        except Exception as e:


            result[lottery]={


                "error":

                    str(e)

            }





    return result







# =====================================================
# 总同步
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
