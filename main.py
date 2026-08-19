# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V8.1 FINAL

============================================================
升级内容
============================================================

1. api3.marksix6.net真实接口
2. 三彩种独立同步
3. SQLite历史缓存
4. 自动兼容SSL异常
5. 特别号码预测
6. 生肖/单双/大小/波色预测
7. Walk Forward回测
8. JSON输出

============================================================
"""

from __future__ import annotations


import json
import ssl
import sqlite3
import urllib.request
import urllib.error

from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Any



# ============================================================
# 目录
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


DATA_DIR = BASE_DIR / "data"

OUTPUT_DIR = BASE_DIR / "output"


DATA_DIR.mkdir(
    exist_ok=True
)


OUTPUT_DIR.mkdir(
    exist_ok=True
)



# ============================================================
# 彩种
# ============================================================

LOTTERIES = [

    "新澳门彩",

    "老澳门彩",

    "香港彩",

]



DB_FILES = {


    "新澳门彩":
        DATA_DIR / "new_macau.db",


    "老澳门彩":
        DATA_DIR / "old_macau.db",


    "香港彩":
        DATA_DIR / "hk.db",

}



# ============================================================
# API
# ============================================================


API_URL = (

    "https://api3.marksix6.net/"
    "lottery_api.php"

)



API_TYPES = {


    "香港彩":
        "hk",


    "新澳门彩":
        "newMacau",


    "老澳门彩":
        "oldMacau",

}



HEADERS = {


    "User-Agent":

        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)",


    "Accept":

        "application/json,*/*",

}



SSL_CONTEXT = ssl._create_unverified_context()



# ============================================================
# 波色
# ============================================================


RED = {

1,2,7,8,12,13,18,19,
23,24,29,30,34,35,
40,45,46

}



BLUE = {

3,4,9,10,14,15,20,
25,26,31,36,37,
41,42,47,48

}



GREEN = {

5,6,11,16,17,21,22,
27,28,32,33,38,39,
43,44,49

}



WAVES = [

    "红",

    "蓝",

    "绿",

]




# ============================================================
# 生肖
# ============================================================


ANIMALS = [

"鼠",
"牛",
"虎",
"兔",
"龙",
"蛇",
"马",
"羊",
"猴",
"鸡",
"狗",
"猪",

]



# ============================================================
# HTTP请求
# ============================================================


def request_json(
    url:str,
    timeout:int=30
):


    req = urllib.request.Request(

        url,

        headers=HEADERS

    )


    try:


        with urllib.request.urlopen(

            req,

            timeout=timeout

        ) as response:


            text = response.read()



    except ssl.SSLError:


        print(

            "[WARN] SSL异常，启用兼容模式"

        )


        with urllib.request.urlopen(

            req,

            timeout=timeout,

            context=SSL_CONTEXT

        ) as response:


            text=response.read()



    except urllib.error.URLError as e:


        if "CERTIFICATE_VERIFY_FAILED" in str(e):


            print(

                "[WARN] SSL证书错误，跳过验证"

            )


            with urllib.request.urlopen(

                req,

                timeout=timeout,

                context=SSL_CONTEXT

            ) as response:


                text=response.read()

        else:

            raise



    result=json.loads(

        text.decode(

            "utf-8",

            errors="ignore"

        )

    )


    return result





# ============================================================
# 数据标准化
# ============================================================


def normalize_issue(
    value
):


    if value is None:

        return None


    value=str(value).strip()


    if not value.isdigit():

        return None


    return value




def normalize_numbers(
    value
):


    if isinstance(value,list):


        try:

            nums=[

                int(x)

                for x in value

            ]

        except:

            return None



    elif isinstance(value,str):


        for sep in [

            ",",

            " ",

            "|",

        ]:


            if sep in value:


                try:


                    nums=[

                        int(x)

                        for x in value.split(sep)

                        if x

                    ]

                    break


                except:

                    continue


        else:

            return None


    else:

        return None



    if len(nums)!=7:

        return None



    if len(set(nums))!=7:

        return None



    if not all(

        1<=x<=49

        for x in nums

    ):

        return None



    return nums




# ============================================================
# 解析单条记录
# ============================================================


def parse_record(
    item:dict
):


    issue=None


    for key in [

        "expect",

        "issue",

        "period",

        "qihao",

        "drawNo",

    ]:


        if key in item:


            issue=normalize_issue(

                item[key]

            )


            if issue:

                break



    numbers=None


    for key in [

        "numbers",

        "openCode",

        "open_code",

        "code",

        "result",

    ]:


        if key in item:


            numbers=normalize_numbers(

                item[key]

            )


            if numbers:

                break



    if issue and numbers:


        return {


            "issue":issue,


            "numbers":numbers,

        }


    return None
    # ============================================================
# 递归提取开奖记录
# ============================================================


def extract_records(
    node,
    output:list
):


    if isinstance(node,dict):


        record=parse_record(node)


        if record:

            output.append(record)



        for value in node.values():

            extract_records(
                value,
                output
            )



    elif isinstance(node,list):


        for item in node:

            extract_records(
                item,
                output
            )





def normalize_records(
    payload
):


    result=[]


    extract_records(
        payload,
        result
    )


    unique={}



    for item in result:


        issue=item["issue"]


        if issue not in unique:


            unique[issue]=item



    data=list(
        unique.values()
    )


    data.sort(
        key=lambda x:int(x["issue"])
    )


    return data





# ============================================================
# API同步
# ============================================================


def fetch_lottery(
    lottery_name:str
):


    api_type=API_TYPES[lottery_name]


    url=(

        API_URL

        +

        "?type="

        +

        api_type

    )


    print("="*70)

    print(
        f"[{lottery_name}] 请求API"
    )

    print(url)



    payload=request_json(url)



    records=normalize_records(
        payload
    )



    print(

        f"[{lottery_name}] "
        f"解析开奖：{len(records)}期"

    )


    return records





# ============================================================
# SQLite
# ============================================================


def get_conn(
    lottery_name:str
):


    path=DB_FILES[lottery_name]


    conn=sqlite3.connect(
        str(path)
    )


    conn.execute(

        """
        CREATE TABLE IF NOT EXISTS draws
        (
            issue TEXT PRIMARY KEY,
            numbers TEXT NOT NULL
        )
        """

    )


    conn.commit()


    return conn





def init_db():

    for lottery in LOTTERIES:

        conn=get_conn(
            lottery
        )

        conn.close()





def save_records(
    lottery_name,
    records
):


    if not records:

        return 0



    conn=get_conn(
        lottery_name
    )


    count=0



    for item in records:


        numbers=",".join(

            str(x)

            for x in item["numbers"]

        )



        cur=conn.execute(

            """
            INSERT OR IGNORE INTO draws
            (
                issue,
                numbers
            )
            VALUES
            (?,?)
            """,

            (

                item["issue"],

                numbers,

            )

        )



        if cur.rowcount:

            count+=1



    conn.commit()

    conn.close()



    return count






def load_history(
    lottery_name
):


    conn=get_conn(
        lottery_name
    )


    rows=conn.execute(

        """
        SELECT issue,numbers
        FROM draws
        ORDER BY CAST(issue AS INTEGER)
        """

    ).fetchall()



    conn.close()



    result=[]



    for issue,numbers in rows:


        nums=[

            int(x)

            for x in numbers.split(",")

        ]



        if len(nums)==7:


            result.append(

                {

                    "issue":issue,

                    "numbers":nums

                }

            )


    return result






# ============================================================
# 属性函数
# ============================================================


def get_wave(
    n
):

    if n in RED:

        return "红"


    if n in BLUE:

        return "蓝"


    if n in GREEN:

        return "绿"


    return ""





def get_size(
    n
):

    return "大" if n>=25 else "小"





def get_odd_even(
    n
):

    return "单" if n%2 else "双"





def get_zodiac(
    number,
    issue
):


    animals=ANIMALS


    try:

        year=int(issue[:4])

    except:

        year=2026



    base=(year-2024+4)%12


    index=(base-(number-1))%12


    return animals[index]






# ============================================================
# 特别号码统计
# ============================================================


def special_counter(
    history,
    window=100
):


    counter=Counter()


    for row in history[-window:]:


        nums=row["numbers"]


        special=nums[6]


        counter[special]+=1



    return counter





# ============================================================
# 特别号码预测
# ============================================================


def predict_special(
    history
):


    c100=special_counter(
        history,
        100
    )


    c50=special_counter(
        history,
        50
    )


    c20=special_counter(
        history,
        20
    )



    scores={}



    for n in range(1,50):


        scores[n]=(

            c100[n]

            +

            c50[n]*1.5

            +

            c20[n]*2

        )



    ranking=sorted(

        range(1,50),

        key=lambda x:(

            -scores[x],

            x

        )

    )



    return {


        "top5":

            ranking[:5],


        "top10":

            ranking[:10],


        "top12":

            ranking[:12],

    }
    # ============================================================
# 属性预测
# ============================================================


def attribute_history(
    history,
    field
):

    counter=Counter()


    for row in history[-100:]:

        number=row["numbers"][6]

        issue=row["issue"]


        if field=="wave":

            value=get_wave(number)


        elif field=="size":

            value=get_size(number)


        elif field=="odd_even":

            value=get_odd_even(number)


        elif field=="zodiac":

            value=get_zodiac(
                number,
                issue
            )

        else:

            value=""


        if value:

            counter[value]+=1


    return counter





def predict_zodiac(
    history
):


    counter=attribute_history(
        history,
        "zodiac"
    )


    ranking=[

        x[0]

        for x in counter.most_common()

    ]



    for x in ANIMALS:

        if x not in ranking:

            ranking.append(x)



    return {


        "main":ranking[0],


        "secondary":ranking[1],


        "top5":ranking[:5],


        "double":ranking[:5]

    }







def predict_single(
    history,
    field
):


    counter=attribute_history(
        history,
        field
    )


    ranking=[

        x[0]

        for x in counter.most_common()

    ]


    if not ranking:


        return {


            "main":"",

            "secondary":"",

            "double":[]

        }



    return {


        "main":ranking[0],


        "secondary":
            ranking[1]
            if len(ranking)>1
            else "",


        "double":[ranking[0]]

    }






def predict_wave(
    history
):


    counter=attribute_history(
        history,
        "wave"
    )


    ranking=[

        x[0]

        for x in counter.most_common()

    ]



    for x in WAVES:

        if x not in ranking:

            ranking.append(x)



    return {


        "main":ranking[0],


        "secondary":ranking[1],


        "double":
            [
                ranking[0],
                ranking[1]
            ]

    }






def predict_attributes(
    history
):


    return {


        "zodiac":

            predict_zodiac(history),


        "odd_even":

            predict_single(
                history,
                "odd_even"
            ),


        "size":

            predict_single(
                history,
                "size"
            ),


        "wave":

            predict_wave(history)

    }






# ============================================================
# Walk Forward
# ============================================================


def evaluate(
    prediction,
    actual
):


    number=actual["numbers"][6]


    result={}


    result["top5"]=int(

        number in prediction["top5"]

    )


    result["top10"]=int(

        number in prediction["top10"]

    )


    result["top12"]=int(

        number in prediction["top12"]

    )


    attrs=prediction["attributes"]



    result["wave"]=int(

        get_wave(number)

        in

        attrs["wave"]["double"]

    )


    result["size"]=int(

        get_size(number)

        ==

        attrs["size"]["main"]

    )


    result["odd_even"]=int(

        get_odd_even(number)

        ==

        attrs["odd_even"]["main"]

    )


    result["zodiac"]=int(

        get_zodiac(
            number,
            actual["issue"]
        )

        in

        attrs["zodiac"]["top5"]

    )


    return result






def walk_forward(
    history
):


    if len(history)<50:


        return {


            "samples":0,


            "status":
                "历史不足"

        }



    results=[]



    for i in range(
        30,
        len(history)
    ):


        train=history[:i]


        pred_number=predict_special(
            train
        )


        pred={


            **pred_number,


            "attributes":

                predict_attributes(
                    train
                )

        }



        results.append(

            evaluate(
                pred,
                history[i]
            )

        )



    total=len(results)



    return {


        "samples":total,


        "top5":

            round(
                sum(x["top5"] for x in results)
                /
                total
                *
                100,
                2
            ),


        "top10":

            round(
                sum(x["top10"] for x in results)
                /
                total
                *
                100,
                2
            ),


        "top12":

            round(
                sum(x["top12"] for x in results)
                /
                total
                *
                100,
                2
            )

    }






# ============================================================
# 单彩种分析
# ============================================================


def analyze(
    lottery,
    history
):


    latest=history[-1]


    special=predict_special(
        history
    )


    attrs=predict_attributes(
        history
    )


    return {


        "lottery":
            lottery,


        "success":
            True,


        "history_size":
            len(history),


        "latest_issue":
            latest["issue"],


        "latest_numbers":
            latest["numbers"],


        "special_number":
            latest["numbers"][6],


        "prediction_issue":
            str(
                int(latest["issue"])+1
            ),


        "top5":
            special["top5"],


        "top10":
            special["top10"],


        "top12":
            special["top12"],


        "attributes":
            attrs,


        "backtest":
            walk_forward(history)

    }






# ============================================================
# 保存
# ============================================================


def save_json(
    name,
    data
):


    path=OUTPUT_DIR/name


    with open(

        path,

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            data,

            f,

            ensure_ascii=False,

            indent=2

        )






# ============================================================
# 主程序
# ============================================================


def main():

    print("="*70)

    print(
        "六合彩综合预测系统 V8.1 FINAL"
    )

    print("="*70)



    init_db()


    results={}



    for lottery in LOTTERIES:


        print(
            f"正在更新 {lottery}"
        )


        records=fetch_lottery(
            lottery
        )


        added=save_records(
            lottery,
            records
        )


        print(
            "新增:",
            added
        )



        history=load_history(
            lottery
        )


        print(
            "历史:",
            len(history)
        )



        if history:

            results[lottery]=analyze(
                lottery,
                history
            )



    output={


        "version":
            "V8.1 FINAL",


        "generated_at":
            datetime.now().isoformat(),


        "lotteries":
            results

    }



    save_json(
        "prediction.json",
        output
    )


    save_json(
        "backtest.json",
        {
            "lotteries":
                {
                    k:v["backtest"]

                    for k,v in results.items()

                }
        }
    )


    print("="*70)

    print(
        "运行完成"
    )

    print("="*70)






if __name__=="__main__":

    main()
