# ============================================================
# 六合彩智能预测系统
# V8.3 FINAL
#
# 特点:
# 1. 不改变数据源
# 2. SQLite历史数据
# 3. 49码独立评分
# 4. 生肖/波色/大小/单双独立模型
# 5. 10/20/30期回测
# 6. 简洁输出
#
# Python >=3.11
# ============================================================


import os
import json
import sqlite3
import requests
import datetime
import math
from collections import Counter, defaultdict



# ============================================================
# 基础配置
# ============================================================


VERSION = "V8.3 FINAL"



OUTPUT_DIR = "output"

DATABASE_DIR = "database"



os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)



os.makedirs(
    DATABASE_DIR,
    exist_ok=True
)



# ============================================================
# 数据源
#
# 保留你的接口
# ============================================================


API_LIST = {


    "新澳门彩":
        [
            "https://api3.marksix6.net/lottery_api.php?type=newMacau"
        ],


    "老澳门彩":
        [
            "https://api3.marksix6.net/lottery_api.php?type=oldMacau"
        ],


    "香港彩":
        [
            "https://api3.marksix6.net/lottery_api.php?type=hk"
        ]

}




# 备用综合接口

THIRD_PARTY_URLS_DEFAULT = [

    "https://marksix6.net/index.php?api=1",

    "https://marksix6.net/api/lottery_api.php"

]





# ============================================================
# 数据库
# ============================================================


DB_FILES = {


    "新澳门彩":
        os.path.join(
            DATABASE_DIR,
            "new_macau.db"
        ),


    "老澳门彩":
        os.path.join(
            DATABASE_DIR,
            "old_macau.db"
        ),


    "香港彩":
        os.path.join(
            DATABASE_DIR,
            "hk.db"
        )

}




# ============================================================
# 六合49码属性
# ============================================================



RED = {

1,2,7,8,12,13,18,19,23,24,
29,30,34,35,40,45,46

}



BLUE = {

3,4,9,10,14,15,20,25,
26,31,36,37,41,42,47,48

}



GREEN = {

5,6,11,16,17,21,22,27,
28,32,33,38,39,43,44,49

}




ZODIAC = {

1:"鼠",2:"牛",3:"虎",4:"兔",
5:"龙",6:"蛇",7:"马",8:"羊",
9:"猴",10:"鸡",11:"狗",12:"猪"

}




# ============================================================
# 属性函数
# ============================================================



def get_wave(num):


    if num in RED:

        return "红"


    if num in BLUE:

        return "蓝"


    return "绿"





def get_size(num):


    return (

        "大"

        if num >=25

        else "小"

    )





def get_odd_even(num):


    return (

        "单"

        if num % 2

        else "双"

    )





def get_tail(num):


    return num % 10





def get_zodiac(num):


    return ZODIAC.get(

        ((num-1)%12)+1,

        ""

    )





# ============================================================
# 网络请求
# ============================================================



def request_json(url, timeout=10):


    try:


        r = requests.get(

            url,

            timeout=timeout,

            verify=False,

            headers={

                "User-Agent":

                "Mozilla/5.0"

            }

        )


        r.encoding="utf-8"


        return r.json()



    except Exception as e:


        print(

            "请求失败:",

            url,

            e

        )


        return None





# ============================================================
# 数字解析
# ============================================================



def parse_numbers(code):


    if not code:

        return []



    if isinstance(code,list):


        return [

            int(x)

            for x in code

            if str(x).isdigit()

        ]



    result=[]


    for x in str(code).replace(

        " ",

        ""

    ).split(","):


        if x.isdigit():

            result.append(

                int(x)

            )



    return result[:7]





# ============================================================
# 读取API数据
# ============================================================



def fetch_api(lottery):


    urls = API_LIST.get(

        lottery,

        []

    )


    for url in urls:


        data=request_json(url)



        if data:


            return data



    return None
    # ============================================================
# 数据标准化
# ============================================================


def normalize_record(item):


    """
    统一不同API格式
    """


    if not item:

        return None



    issue = str(

        item.get(

            "expect",

            ""

        )

    )



    code = item.get(

        "openCode",

        ""

    )


    nums = parse_numbers(code)



    if len(nums) < 7:

        nums = [

            int(x)

            for x in item.get(

                "numbers",

                []

            )

        ]



    if len(nums) != 7:

        return None



    return {


        "issue":issue,


        "numbers":nums,


        "openTime":

            item.get(

                "openTime",

                ""

            ),


        "wave":

            item.get(

                "wave",

                ""


            ),


        "zodiac":

            item.get(

                "zodiac",

                ""

            )


    }





# ============================================================
# API解析
# ============================================================



def parse_api_data(lottery,data):


    records=[]



    if not data:

        return []




    # api3格式

    if isinstance(data,dict):


        if "history" in data:


            history=data.get(

                "history",

                []

            )


            for h in history:


                if isinstance(h,str):


                    try:


                        issue=h.split("期")[0]


                        code=h.split("：")[1]


                        records.append({

                            "expect":issue,

                            "openCode":code

                        })


                    except:


                        pass



        else:


            records.append(data)





        # 综合接口

        if "lottery_data" in data:


            for x in data["lottery_data"]:


                if x.get("name")==lottery:


                    records.append(x)



                    for h in x.get(

                        "history",

                        []

                    ):


                        try:


                            issue=h.split(

                                "期"

                            )[0]


                            code=h.split(

                                "："

                            )[1]


                            records.append({

                                "expect":issue,

                                "openCode":code

                            })


                        except:


                            pass





    # list格式

    elif isinstance(data,list):


        records.extend(data)




    result=[]


    seen=set()



    for r in records:


        n=normalize_record(r)



        if n:


            if n["issue"] not in seen:


                seen.add(

                    n["issue"]

                )

                result.append(n)



    return result





# ============================================================
# SQLite
# ============================================================



def init_db(db):


    conn=sqlite3.connect(db)


    cur=conn.cursor()


    cur.execute("""


    CREATE TABLE IF NOT EXISTS history

    (

        issue TEXT PRIMARY KEY,

        n1 INTEGER,

        n2 INTEGER,

        n3 INTEGER,

        n4 INTEGER,

        n5 INTEGER,

        n6 INTEGER,

        n7 INTEGER,

        openTime TEXT

    )


    """)



    conn.commit()


    conn.close()





def save_history(db,records):


    init_db(db)


    conn=sqlite3.connect(db)


    cur=conn.cursor()



    for r in records:


        nums=r["numbers"]


        cur.execute(

        """

        INSERT OR REPLACE INTO history

        VALUES(?,?,?,?,?,?,?,?,?)

        """,

        (

            r["issue"],

            nums[0],

            nums[1],

            nums[2],

            nums[3],

            nums[4],

            nums[5],

            nums[6],

            r["openTime"]

        )

        )



    conn.commit()


    conn.close()





def load_history(db):


    init_db(db)


    conn=sqlite3.connect(db)


    cur=conn.cursor()



    cur.execute(

        """

        SELECT *

        FROM history

        ORDER BY issue DESC

        """

    )


    rows=cur.fetchall()


    conn.close()



    result=[]


    for r in rows:


        result.append({

            "issue":r[0],

            "numbers":

            list(r[1:8]),

            "openTime":r[8]

        })



    return result





# ============================================================
# 更新数据
# ============================================================



def update_database(lottery):


    print("="*60)

    print(

        "更新",

        lottery

    )

    print("="*60)



    data=fetch_api(lottery)



    records=parse_api_data(

        lottery,

        data

    )



    print(

        "解析",

        len(records),

        "期"

    )



    save_history(

        DB_FILES[lottery],

        records

    )



    history=load_history(

        DB_FILES[lottery]

    )


    print(

        "数据库历史:",

        len(history)

    )



    return history





# ============================================================
# 49码评分模型
# ============================================================



def score_numbers(history):


    scores={

        i:0

        for i in range(1,50)

    }



    # 最近多少期权重

    recent=history[:100]



    freq=Counter()



    for h in recent:


        for n in h["numbers"]:


            freq[n]+=1





    for n in range(1,50):


        # 出现频率

        scores[n]+=freq[n]*2





        # 遗漏修正

        miss=0


        for h in history:


            if n in h["numbers"]:

                break


            miss+=1



        scores[n]+=min(

            miss,

            30

        )*0.15





        # 尾数

        tail_count=Counter()


        for h in recent:


            for x in h["numbers"]:


                tail_count[get_tail(x)] +=1



        scores[n]+=tail_count[get_tail(n)]*0.3





    return scores





def top_numbers(scores):


    return [

        x[0]

        for x in sorted(

            scores.items(),

            key=lambda x:x[1],

            reverse=True

        )

    ]
# ============================================================
# 属性独立模型
# ============================================================



def attribute_rank(history,func):


    counter=Counter()



    for h in history:


        for n in h["numbers"]:


            counter[

                func(n)

            ]+=1




    return [

        x[0]

        for x in counter.most_common()

    ]





# ============================================================
# 回测
# ============================================================



def backtest(history):


    result={}



    for days in [10,20,30]:


        if len(history)<=days:

            result[str(days)] = 0

            continue



        hit=0

        total=0



        data=history[days:]



        for i in range(

            min(

                len(data),

                100

            )

        ):


            train=data[i+days:]

            target=data[i]



            if not train:

                continue



            scores=score_numbers(

                train

            )


            top10=top_numbers(

                scores

            )[:10]



            real=set(

                target["numbers"]

            )



            hit+=len(

                real.intersection(

                    top10

                )

            )



            total+=1



        if total:


            result[str(days)] = round(

                hit/(total*7)*100,

                2

            )



        else:


            result[str(days)] = 0



    return result





# ============================================================
# 单个彩种预测
# ============================================================



def predict_lottery(name,history):


    if len(history)<30:


        return {

            "success":False,

            "error":

            "历史不足30期"

        }




    scores=score_numbers(

        history

    )



    ranking=top_numbers(

        scores

    )



    top5=ranking[:5]

    top10=ranking[:10]

    top12=ranking[:12]




    latest=history[0]



    issue=str(

        int(

            latest["issue"]

        )+1

    )





    result={


        "success":True,


        "lottery":name,


        "latest_issue":

            latest["issue"],


        "prediction_issue":

            issue,


        "latest_numbers":

            latest["numbers"],



        "history_size":

            len(history),



        "top5":

            top5,


        "top10":

            top10,


        "top12":

            top12,




        "attributes":{


            "zodiac":{

                "top5":

                attribute_rank(

                    history,

                    get_zodiac

                )[:5]

            },


            "wave":{

                "top":

                attribute_rank(

                    history,

                    get_wave

                )[:3]

            },


            "size":{

                "top":

                attribute_rank(

                    history,

                    get_size

                )[:2]

            },


            "odd_even":{

                "top":

                attribute_rank(

                    history,

                    get_odd_even

                )[:2]

            }


        },



        "backtest":

            backtest(history)

    }



    return result





# ============================================================
# 主程序
# ============================================================



def main():


    print()

    print("="*70)

    print(

        "六合彩综合预测系统",

        VERSION

    )

    print("="*70)



    output={


        "version":

            VERSION,


        "time":

            datetime.datetime.now().isoformat(),


        "lotteries":{}

    }





    for name in [

        "新澳门彩",

        "老澳门彩",

        "香港彩"

    ]:


        history=update_database(

            name

        )



        result=predict_lottery(

            name,

            history

        )



        output["lotteries"][name]=result





        if result["success"]:


            print()

            print(

                "【",

                name,

                "】"

            )


            print(

                "历史:",

                result["history_size"]

            )


            print(

                "最新:",

                result["latest_issue"]

            )


            print(

                "预测:",

                result["prediction_issue"]

            )



            print(

                "推荐10码:",

                " ".join(

                    f"{x:02d}"

                    for x in result["top10"]

                )

            )



            print(

                "生肖:",

                " ".join(

                    result["attributes"]

                    ["zodiac"]

                    ["top5"]

                )

            )


            print(

                "波色:",

                result["attributes"]

                ["wave"]

                ["top"]

            )



            print(

                "大小:",

                result["attributes"]

                ["size"]

                ["top"]

            )



            print(

                "单双:",

                result["attributes"]

                ["odd_even"]

                ["top"]

            )



            print(

                "10/20/30期命中:",

                result["backtest"]

            )





    with open(

        os.path.join(

            OUTPUT_DIR,

            "prediction.json"

        ),

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            output,

            f,

            ensure_ascii=False,

            indent=2

        )



    print()

    print("="*70)

    print(

        "输出完成:",

        "output/prediction.json"

    )

    print("="*70)





if __name__=="__main__":


    main()


