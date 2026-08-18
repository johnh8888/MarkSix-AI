# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.1

api_sync.py

真实开奖数据同步模块


功能:

1. 请求开奖API
2. 解析开奖数据
3. 标准化格式
4. 提供给SQLite


"""


import requests

from datetime import datetime





# =====================================================
# API地址
# =====================================================


API_LIST={


    "香港六合彩":

    "https://marksix6.net/api/lottery_api.php",



    "新澳门彩":

    "https://marksix6.net/api/lottery_api.php",



    "老澳门彩":

    "https://marksix6.net/api/lottery_api.php"


}






# =====================================================
# 请求API
# =====================================================


def 请求数据(

        url,

        timeout=10

):


    try:


        response=requests.get(

            url,

            timeout=timeout,

            headers={

                "User-Agent":

                "Mozilla/5.0"

            }

        )


        response.encoding="utf-8"


        return response.json()



    except Exception as e:


        print(

            "API请求失败:",

            e

        )


        return {}





# =====================================================
# 号码解析
# =====================================================


def 解析号码(

        code

):


    if not code:


        return []



    if isinstance(

        code,

        list

    ):


        return [

            int(x)

            for x in code

        ]



    return [

        int(x)

        for x in str(code)

        .replace(

            " ",

            ""

        )

        .split(",")

        if x

    ]





# =====================================================
# 单期开奖标准化
# =====================================================


def 标准化开奖(

        item

):


    return {


        "期号":

        item.get(

            "expect",

            ""

        ),



        "号码":

        解析号码(

            item.get(

                "openCode",

                ""

            )

        ),



        "开奖时间":

        item.get(

            "openTime",

            ""

        ),



        "更新时间":

        str(

            datetime.now()

        )

    }





# =====================================================
# 解析历史
# =====================================================


def 解析历史(

        data

):


    result=[]



    if not data:


        return result





    # 不同API兼容


    history=data.get(

        "history",

        []

    )



    if isinstance(

        history,

        list

    ):


        for item in history:


            result.append(

                标准化开奖(

                    item

                )

            )





    return result





# =====================================================
# 获取彩种数据
# =====================================================


def 获取彩种(

        彩种

):


    url=API_LIST.get(

        彩种

    )



    if not url:


        return []



    print(

        "正在同步:",

        彩种

    )



    data=请求数据(

        url

    )



    历史=解析历史(

        data

    )



    print(

        彩种,

        "获取",

        len(历史),

        "期"

    )



    return 历史





# =====================================================
# 三彩种同步
# =====================================================


def 同步全部():



    数据={}



    for name in API_LIST:


        数据[name]=获取彩种(

            name

        )



    return 数据





if __name__=="__main__":


    result=同步全部()



    print(

        result.keys()

    )
