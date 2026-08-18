# -*- coding: utf-8 -*-

"""
六合AI V10.0 FINAL
API同步模块

支持:
香港六合彩
新澳门六合彩
老澳门六合彩

自动处理:
SSL证书过期
"""

import json
import ssl
import urllib.request
from datetime import datetime



# ==========================
# API地址
# ==========================

API_HOST = "https://marksix6.net"


REALTIME_API = {

    "hk":
    API_HOST + "/api/lottery_api.php?type=hk",

    "newMacau":
    API_HOST + "/api/lottery_api.php?type=newMacau",

    "oldMacau":
    API_HOST + "/api/lottery_api.php?type=oldMacau"

}



HISTORY_API = (
    API_HOST +
    "/index.php?api=1"
)



# ==========================
# SSL备用
# ==========================

def ssl_context():

    return ssl._create_unverified_context()



# ==========================
# 请求
# ==========================

def request_json(url):

    try:

        req = urllib.request.Request(

            url,

            headers={
                "User-Agent":
                "Mozilla/5.0"
            }

        )


        ctx = ssl_context()


        with urllib.request.urlopen(

            req,

            timeout=15,

            context=ctx

        ) as r:


            data = r.read()



        text=data.decode(
            "utf-8",
            errors="ignore"
        )


        return json.loads(text)



    except Exception as e:

        print(
            "API错误:",
            e
        )

        return None




# ==========================
# 实时数据
# ==========================

def get_realtime(name):


    url=REALTIME_API.get(name)


    if not url:

        return None



    print(
        "请求:",
        url
    )


    data=request_json(url)



    if not data:

        return None



    return parse_realtime(
        data,
        name
    )




# ==========================
# 历史数据
# ==========================

def get_history():


    print(
        "请求历史接口"
    )


    data=request_json(
        HISTORY_API
    )


    if not data:

        return {}



    return parse_history(
        data
    )




# ==========================
# 实时解析
# ==========================

def parse_realtime(data,name):


    result={}


    try:


        # 兼容字段

        if "lottery_data" in data:

            item=data["lottery_data"]


            if isinstance(
                item,
                list
            ):

                item=item[0]



        else:

            item=data



        expect=(

            item.get(
                "expect"
            )

            or

            item.get(
                "issue"
            )

            or ""

        )



        code=(

            item.get(
                "openCode"
            )

            or

            item.get(
                "code"
            )

            or ""

        )


        numbers=[]


        if isinstance(code,str):

            for x in code.split(","):

                if x.isdigit():

                    numbers.append(
                        int(x)
                    )



        result={

            "name":name,

            "issue":expect,

            "numbers":numbers,

            "time":
            datetime.now().isoformat()

        }



    except Exception as e:


        print(
            "解析失败:",
            e
        )



    return result




# ==========================
# 历史解析
# ==========================

def parse_history(data):


    result={}


    try:


        history=data.get(
            "history",
            []
        )


        if not isinstance(
            history,
            list
        ):

            return result



        for item in history:


            name=item.get(
                "type",
                "hk"
            )


            nums=[]


            code=item.get(
                "openCode",
                ""
            )


            for x in str(code).split(","):


                if x.isdigit():

                    nums.append(
                        int(x)
                    )



            result.setdefault(
                name,
                []
            ).append(

                {
                    "issue":
                    item.get(
                        "expect",
                        ""
                    ),

                    "numbers":
                    nums
                }

            )


    except Exception as e:

        print(
            "历史解析失败:",
            e
        )


    return result
