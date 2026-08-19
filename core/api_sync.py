# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

API同步模块

支持:

香港六合彩
新澳门六合彩
老澳门六合彩

"""


import json


import requests


import urllib3



from config import (

    API_HISTORY,

    API_REALTIME,

    LOTTERIES

)



from .database import save_draw





urllib3.disable_warnings()





# =====================================================
# 请求
# =====================================================


def request_api(url):


    print(

        "请求:",

        url

    )


    try:


        r=requests.get(

            url,

            timeout=20,

            headers={

                "User-Agent":

                "Mozilla/5.0"

            }

        )


        r.raise_for_status()


        return r.json()



    except Exception as e:


        print(

            "SSL正常请求失败:",

            e

        )



        print(

            "启用SSL备用模式"

        )



        r=requests.get(

            url,

            timeout=20,

            verify=False,

            headers={

                "User-Agent":

                "Mozilla/5.0"

            }

        )


        return r.json()







# =====================================================
# 同步
# =====================================================


def sync_all():


    print("="*60)

    print(

        "开始API同步"

    )

    print("="*60)



    data=request_api(

        API_HISTORY

    )



    count={}



    items=data.get(

        "lottery_data",

        []

    )



    for item in items:



        name=item.get(

            "name",

            ""

        )


        key=None



        for k,v in LOTTERIES.items():


            if v in name:

                key=k



        if not key:

            continue



        history=item.get(

            "history",

            []

        )



        c=0



        for row in history:


            nums=[]


            if isinstance(row,str):


                nums=[

                    int(x)

                    for x in row.replace(

                        ",",

                        " "

                    ).split()

                    if x.isdigit()

                ]



            if len(nums)>=7:


                ok=save_draw(

                    key,

                    str(c),

                    nums[:6],

                    nums[6],

                    "api"

                )


                if ok:

                    c+=1



        count[key]=c



        print(

            key,

            c,

            "期"

        )



    return count
