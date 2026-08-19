# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V8.2 FINAL

修复：
1. marksix6 index.php?api=1 历史解析
2. lottery_data.history 解析
3. api3.marksix6.net兼容
4. SSL证书异常兼容
5. SQLite历史累计
6. 特别号码第7位预测
7. Walk Forward回测

Python 3.11+
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


INDEX_API = (

    "https://marksix6.net/index.php?api=1"

)


API3 = (

    "https://api3.marksix6.net/lottery_api.php"

)


MACAU_HISTORY = (

    "https://api.macaumarksix.com/history/macaujc2/y/{}"

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
        "Mozilla/5.0",

    "Accept":
        "application/json",

    "Connection":
        "close",

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

3,4,9,10,14,15,
20,25,26,31,36,37,
41,42,47,48

}


GREEN = {

5,6,11,16,17,
21,22,27,28,32,
33,38,39,43,44,49

}


WAVES = [

"红",
"蓝",
"绿"

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
"猪"

]



# ============================================================
# HTTP JSON
# ============================================================


def request_json(
    url:str,
    timeout:int=20
)->Any:


    req = urllib.request.Request(

        url,

        headers=HEADERS

    )


    try:


        with urllib.request.urlopen(

            req,

            timeout=timeout

        ) as r:


            text = r.read().decode(

                "utf-8",

                errors="ignore"

            )


    except ssl.SSLError:


        with urllib.request.urlopen(

            req,

            timeout=timeout,

            context=SSL_CONTEXT

        ) as r:


            text = r.read().decode(

                "utf-8",

                errors="ignore"

            )


    except urllib.error.URLError as e:


        if "CERTIFICATE" in str(e).upper():


            with urllib.request.urlopen(

                req,

                timeout=timeout,

                context=SSL_CONTEXT

            ) as r:


                text = r.read().decode(

                    "utf-8",

                    errors="ignore"

                )

        else:

            raise



    text = text.strip()


    if text.startswith("\ufeff"):

        text=text[1:]


    return json.loads(text)





# ============================================================
# 基础解析
# ============================================================


def clean_issue(x):


    if x is None:

        return None


    x=str(x).strip()


    if not x:

        return None


    if x.endswith(".0"):

        x=x[:-2]


    return x





def parse_numbers(value):


    if isinstance(value,list):


        nums=[]


        for i in value:

            try:

                nums.append(
                    int(i)
                )

            except:

                return None


        if len(nums)==7:

            return nums



    if isinstance(value,str):


        text=value.replace(
            " ",
            ""
        )


        for sep in [

            ",",
            "-",
            "|"

        ]:


            if sep in text:


                arr=text.split(sep)


                if len(arr)==7:


                    try:

                        nums=[
                            int(x)
                            for x in arr
                        ]

                        return nums


                    except:

                        pass


    return None

# ============================================================
# 特殊历史字符串解析
# 例如：
#
# "2026090 期：39,41,08,09,07,14,49"
#
# ============================================================


def parse_history_string(
    text:str
):

    if not isinstance(
        text,
        str
    ):
        return None


    if "期：" not in text:
        return None


    try:

        issue, codes = text.split(
            "期：",
            1
        )


        issue = (
            issue
            .replace(
                "期",
                ""
            )
            .strip()
        )


        nums = parse_numbers(
            codes
        )


        if not nums:
            return None


        if len(nums)!=7:
            return None


        return {

            "issue":
                issue,

            "numbers":
                nums,

            "source":
                "history"

        }


    except Exception:


        return None





# ============================================================
# 单条记录解析
# ============================================================


def parse_record(
    item:dict
):


    if not isinstance(
        item,
        dict
    ):

        return None



    issue = None


    for key in [

        "expect",
        "issue",
        "period",
        "qihao"

    ]:


        if key in item:


            issue = clean_issue(
                item[key]
            )


            if issue:

                break



    nums=None


    for key in [

        "numbers",
        "openCode",
        "open_code",
        "code"

    ]:


        if key in item:


            nums=parse_numbers(
                item[key]
            )


            if nums:

                break



    if issue and nums:


        return {

            "issue":
                issue,

            "numbers":
                nums,

            "source":
                "api"

        }


    return None





# ============================================================
# 递归解析JSON
# ============================================================


def extract_json_records(
    node,
    result:list
):


    if isinstance(
        node,
        dict
    ):


        # 普通接口格式

        record=parse_record(
            node
        )


        if record:

            result.append(
                record
            )



        for k,v in node.items():


            extract_json_records(
                v,
                result
            )



    elif isinstance(
        node,
        list
    ):


        for item in node:

            extract_json_records(
                item,
                result
            )






# ============================================================
# index.php?api=1 专用解析
# ============================================================


def parse_index_history(
    payload,
    lottery_name
):


    result=[]


    if not isinstance(
        payload,
        dict
    ):

        return result



    data=payload.get(
        "lottery_data",
        []
    )


    for lottery in data:


        if not isinstance(
            lottery,
            dict
        ):

            continue



        name=lottery.get(
            "name",
            ""
        )


        code=lottery.get(
            "code",
            ""
        )



        match=False



        if lottery_name=="香港彩":


            match = (
                code=="hk"
                or
                "香港" in name
            )



        elif lottery_name=="新澳门彩":


            match = (
                "新澳门" in name
                or
                "澳门" in name
                or
                code in [
                    "macau",
                    "newMacau"
                ]
            )



        elif lottery_name=="老澳门彩":


            match = (
                "老澳门" in name
                or
                code=="oldMacau"
            )



        if not match:

            continue




        # 当前一期

        current=parse_record(
            lottery
        )


        if current:

            result.append(
                current
            )



        # 历史数组

        history=lottery.get(
            "history",
            []
        )


        if isinstance(
            history,
            list
        ):


            for line in history:


                item=parse_history_string(
                    line
                )


                if item:

                    result.append(
                        item
                    )



    return result





# ============================================================
# 新澳门历史补充
# ============================================================


def fetch_macau_year_history(
    year=2026
):


    url=MACAU_HISTORY.format(
        year
    )


    try:


        payload=request_json(
            url
        )


    except Exception:


        return []



    result=[]



    if isinstance(
        payload,
        dict
    ):


        data=payload.get(
            "data",
            []
        )


    elif isinstance(
        payload,
        list
    ):

        data=payload


    else:

        data=[]



    for row in data:


        item=parse_record(
            row
        )


        if item:

            result.append(
                item
            )



    return result





# ============================================================
# API总获取
# ============================================================


def fetch_lottery(
    lottery_name
):


    print("="*70)

    print(
        "正在同步",
        lottery_name
    )

    print("="*70)



    records=[]



    # --------------------------------------------------------
    # 第一来源
    # --------------------------------------------------------


    try:


        print(
            "请求历史接口:",
            INDEX_API
        )


        payload=request_json(
            INDEX_API
        )


        records.extend(

            parse_index_history(

                payload,

                lottery_name

            )

        )


    except Exception as e:


        print(
            "历史接口失败:",
            e
        )



    # --------------------------------------------------------
    # api3备用
    # --------------------------------------------------------


    try:


        url=(
            API3
            +
            "?type="
            +
            API_TYPES[lottery_name]
        )


        print(
            "备用接口:",
            url
        )


        payload=request_json(
            url
        )


        temp=[]


        extract_json_records(

            payload,

            temp

        )


        records.extend(
            temp
        )


    except Exception as e:


        print(
            "备用接口失败:",
            e
        )



    # --------------------------------------------------------
    # 新澳门补历史
    # --------------------------------------------------------


    if lottery_name=="新澳门彩":


        records.extend(

            fetch_macau_year_history()

        )



    # 去重

    unique={}



    for r in records:


        issue=r.get(
            "issue"
        )


        nums=r.get(
            "numbers"
        )


        if (

            issue
            and
            nums
            and
            len(nums)==7

        ):

            unique[issue]={

                "issue":
                    issue,

                "numbers":
                    nums,

                "source":
                    r.get(
                        "source",
                        ""
                    )

            }



    final=list(
        unique.values()
    )


    final.sort(
        key=lambda x:int(
            x["issue"]
        )
    )



    print(
        lottery_name,
        "解析历史:",
        len(final),
        "期"
    )


    return final

# ============================================================
# SQLite
# ============================================================


def get_conn(
    lottery_name
):


    path=DB_FILES[
        lottery_name
    ]


    conn=sqlite3.connect(
        str(path)
    )


    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS draws
        (
            issue TEXT PRIMARY KEY,
            numbers TEXT NOT NULL,
            source TEXT
        )
        """
    )


    conn.commit()


    return conn





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


    try:


        for row in records:


            issue=str(
                row["issue"]
            )


            nums=row["numbers"]


            if len(nums)!=7:

                continue



            text=",".join(

                str(x)

                for x in nums

            )



            cur=conn.execute(

                """
                INSERT OR IGNORE INTO draws
                (
                    issue,
                    numbers,
                    source
                )
                VALUES(?,?,?)
                """,

                (
                    issue,
                    text,
                    row.get(
                        "source",
                        ""
                    )
                )

            )


            if cur.rowcount:

                count+=1



        conn.commit()



    finally:

        conn.close()



    return count






def load_records(
    lottery_name
):


    conn=get_conn(
        lottery_name
    )


    rows=conn.execute(

        """
        SELECT
            issue,
            numbers
        FROM draws
        ORDER BY
            CAST(issue AS INTEGER)
        """

    ).fetchall()



    conn.close()



    result=[]


    for issue,text in rows:


        try:


            nums=[

                int(x)

                for x in text.split(",")

            ]


        except:


            continue



        if len(nums)!=7:

            continue



        result.append(

            {
                "issue":
                    str(issue),

                "numbers":
                    nums

            }

        )



    return result






# ============================================================
# 号码属性
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
    n,
    issue
):


    try:

        year=int(
            str(issue)[:4]
        )

    except:

        year=2026



    # 2024 龙
    base=4


    year_index=(

        base
        +
        year
        -
        2024

    )%12



    index=(

        year_index
        -
        (n-1)

    )%12



    return ANIMALS[index]






# ============================================================
# 特别号码统计
# 第7个号码
# ============================================================


def special_counter(
    history,
    window=100
):


    counter=Counter()



    for row in history[-window:]:


        nums=row["numbers"]


        if len(nums)==7:


            counter[
                nums[6]
            ]+=1



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


    score={}



    for n in range(1,50):


        score[n]=(

            c100[n]*1

            +

            c50[n]*1.5

            +

            c20[n]*2

        )



    ranking=sorted(

        range(1,50),

        key=lambda x:(

            -score[x],

            -c20[x],

            -c50[x]

        )

    )



    return {


        "top5":
            ranking[:5],


        "top10":
            ranking[:10],


        "top12":
            ranking[:12],


        "score":
            score

    }






# ============================================================
# 属性统计
# ============================================================


def attribute_counter(
    history,
    field,
    window=100
):


    c=Counter()



    for row in history[-window:]:


        nums=row["numbers"]


        if len(nums)!=7:

            continue



        n=nums[6]



        if field=="wave":

            value=get_wave(n)



        elif field=="size":

            value=get_size(n)



        elif field=="odd":

            value=get_odd_even(n)



        elif field=="zodiac":

            value=get_zodiac(

                n,

                row["issue"]

            )



        else:

            value=""



        if value:

            c[value]+=1



    return c






# ============================================================
# 属性预测
# ============================================================


def predict_attributes(
    history
):


    zodiac=[

        x[0]

        for x in

        attribute_counter(

            history,

            "zodiac"

        ).most_common()

    ]



    for a in ANIMALS:

        if a not in zodiac:

            zodiac.append(a)



    wave=[

        x[0]

        for x in

        attribute_counter(

            history,

            "wave"

        ).most_common()

    ]



    for a in WAVES:

        if a not in wave:

            wave.append(a)



    odd=[

        x[0]

        for x in

        attribute_counter(

            history,

            "odd"

        ).most_common()

    ]



    size=[

        x[0]

        for x in

        attribute_counter(

            history,

            "size"

        ).most_common()

    ]



    return {


        "zodiac":{

            "top5":
                zodiac[:5],

            "main":
                zodiac[0]

        },


        "wave":{

            "main":
                wave[0],

            "secondary":
                wave[1],

            "double":
                wave[:2]

        },


        "odd_even":{

            "main":
                odd[0]

        },


        "size":{

            "main":
                size[0]

        }


    }
  # ============================================================
# 命中率
# ============================================================


def hit_rate(
    hit,
    total
):

    if total==0:

        return 0


    return round(
        hit/total*100,
        2
    )





# ============================================================
# 单次预测评价
# ============================================================


def evaluate(
    prediction,
    actual
):


    nums=actual["numbers"]


    if len(nums)!=7:

        return {}



    special=nums[6]



    attrs=prediction["attributes"]



    result={}



    # 特别号码

    result["top5"]=int(

        special

        in

        prediction["top5"]

    )


    result["top10"]=int(

        special

        in

        prediction["top10"]

    )


    result["top12"]=int(

        special

        in

        prediction["top12"]

    )



    # 属性


    zodiac=get_zodiac(

        special,

        actual["issue"]

    )


    result["zodiac5"]=int(

        zodiac

        in

        attrs["zodiac"]["top5"]

    )



    result["odd"]=int(

        get_odd_even(special)

        ==

        attrs["odd_even"]["main"]

    )



    result["size"]=int(

        get_size(special)

        ==

        attrs["size"]["main"]

    )



    wave=get_wave(
        special
    )


    result["wave_main"]=int(

        wave

        ==

        attrs["wave"]["main"]

    )


    result["wave_double"]=int(

        wave

        in

        attrs["wave"]["double"]

    )



    return result






# ============================================================
# Walk Forward
# ============================================================


def walk_forward(
    history,
    minimum=30
):


    evaluations=[]



    if len(history)<=minimum:


        return {

            "samples":0,

            "status":
                "数据不足"

        }



    for i in range(

        minimum,

        len(history)

    ):


        train=history[:i]


        actual=history[i]



        sp=predict_special(
            train
        )


        attrs=predict_attributes(
            train
        )


        pred={


            "top5":
                sp["top5"],


            "top10":
                sp["top10"],


            "top12":
                sp["top12"],


            "attributes":
                attrs

        }



        ev=evaluate(

            pred,

            actual

        )


        evaluations.append(
            ev
        )



    total=len(
        evaluations
    )


    def count(k):

        return sum(

            x.get(k,0)

            for x in evaluations

        )



    return {


        "method":

            "Walk-Forward",


        "samples":

            total,


        "performance":{


            "special":{


                "top5":

                    hit_rate(

                        count("top5"),

                        total

                    ),


                "top10":

                    hit_rate(

                        count("top10"),

                        total

                    ),


                "top12":

                    hit_rate(

                        count("top12"),

                        total

                    )


            },


            "zodiac5":

                hit_rate(

                    count("zodiac5"),

                    total

                ),



            "odd":

                hit_rate(

                    count("odd"),

                    total

                ),



            "size":

                hit_rate(

                    count("size"),

                    total

                ),



            "wave_main":

                hit_rate(

                    count("wave_main"),

                    total

                ),



            "wave_double":

                hit_rate(

                    count("wave_double"),

                    total

                )

        }

    }






# ============================================================
# 分析单个彩种
# ============================================================


def analyze(
    lottery,
    history
):


    if not history:


        return {


            "success":
                False,


            "lottery":
                lottery

        }



    latest=history[-1]


    sp=predict_special(
        history
    )


    attrs=predict_attributes(
        history
    )


    backtest=walk_forward(
        history
    )



    return {


        "success":

            True,


        "lottery":

            lottery,


        "latest_issue":

            latest["issue"],


        "latest_numbers":

            latest["numbers"],



        "prediction_issue":

            str(

                int(
                    latest["issue"]
                )+1

            ),



        "history_size":

            len(history),



        "top5":

            sp["top5"],



        "top10":

            sp["top10"],



        "top12":

            sp["top12"],



        "candidates":

            sp["top12"],



        "attributes":

            attrs,



        "backtest":

            backtest



    }






# ============================================================
# 保存JSON
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



    print(

        "保存:",

        path

    )  
# ============================================================
# 打印结果
# ============================================================


def print_result(
    result
):

    if not result.get(
        "success",
        False
    ):

        print(
            "分析失败"
        )

        return



    print("="*70)

    print(
        "【",
        result["lottery"],
        "】"
    )

    print("="*70)


    print(
        "历史期数:",
        result["history_size"]
    )


    print(
        "最新期:",
        result["latest_issue"]
    )


    print(
        "预测期:",
        result["prediction_issue"]
    )


    print(
        "最新号码:",
        " ".join(

            f"{x:02d}"

            for x in result["latest_numbers"]

        )
    )



    print()

    print(
        "特别号码预测"
    )


    print(

        "Top5:",

        " ".join(

            f"{x:02d}"

            for x in result["top5"]

        )

    )


    print(

        "Top10:",

        " ".join(

            f"{x:02d}"

            for x in result["top10"]

        )

    )


    print(

        "Top12:",

        " ".join(

            f"{x:02d}"

            for x in result["top12"]

        )

    )



    attrs=result["attributes"]


    print()


    print(
        "生肖5推:",
        " ".join(

            attrs["zodiac"]["top5"]

        )

    )


    print(
        "单双:",
        attrs["odd_even"]["main"]
    )


    print(
        "大小:",
        attrs["size"]["main"]
    )


    print(

        "波色:",

        attrs["wave"]["main"],

        "+",

        attrs["wave"]["secondary"]

    )



    bt=result["backtest"]


    if bt.get(
        "performance"
    ):


        print()

        print(
            "Walk Forward"
        )


        p=bt["performance"]


        print(

            "特别Top5:",

            p["special"]["top5"],

            "%"

        )


        print(

            "特别Top10:",

            p["special"]["top10"],

            "%"

        )


        print(

            "特别Top12:",

            p["special"]["top12"],

            "%"

        )



    print()






# ============================================================
# 主程序
# ============================================================


def run_system():



    print("="*70)

    print(
        "六合彩综合预测系统 V8.2 FINAL"
    )

    print(
        "真实API + 历史同步 + SQLite + 特别号码预测"
    )


    print(
        datetime.now()
    )


    print("="*70)



    all_results={}



    for lottery in LOTTERIES:


        try:


            records=fetch_lottery(
                lottery
            )


            added=save_records(

                lottery,

                records

            )


            print(

                lottery,

                "新增:",

                added

            )



            history=load_records(

                lottery

            )


            print(

                lottery,

                "数据库:",

                len(history),

                "期"

            )



            result=analyze(

                lottery,

                history

            )



            all_results[lottery]=result



            print_result(
                result
            )



        except Exception as e:


            print(

                lottery,

                "错误:",

                e

            )


            all_results[lottery]={

                "success":
                    False,

                "error":
                    str(e)

            }




    # ========================================================
    # 输出文件
    # ========================================================


    prediction={


        "version":

            "V8.2 FINAL",


        "time":

            datetime.now().isoformat(),


        "rule":

            "特别号码=第7个号码",


        "lotteries":

            all_results


    }



    save_json(

        "prediction.json",

        prediction

    )




    backtest={}


    for k,v in all_results.items():


        backtest[k]=v.get(

            "backtest",

            {}

        )



    save_json(

        "backtest.json",

        backtest

    )




    module={}


    for k,v in all_results.items():


        module[k]={

            "history":

                v.get(
                    "history_size",
                    0
                )

        }



    save_json(

        "module_performance.json",

        module

    )



    print("="*70)

    print(
        "系统运行完成"
    )

    print("="*70)





# ============================================================
# 入口
# ============================================================


if __name__=="__main__":


    try:


        run_system()


    except KeyboardInterrupt:


        print(
            "用户停止"
        )


    except Exception as e:


        print(
            "[FATAL]",
            e
        )

        raise
        
