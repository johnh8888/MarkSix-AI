# ============================================================
# 六合彩综合预测系统 V8.3 FINAL
# 数据稳定版
#
# 保留数据源:
# api3.marksix6.net
#
# 功能:
# SQLite
# API同步
# 历史保存
# 49码评分
# 属性预测
# 回测
#
# Python 3.11+
# ============================================================


import os
import json
import sqlite3
import requests
import random
import math
from datetime import datetime
from collections import Counter, defaultdict


VERSION = "V8.3 FINAL"


# ==============================
# 数据库
# ==============================

DB_FILES = {

    "新澳门彩":
        "new_macau.db",

    "老澳门彩":
        "old_macau.db",

    "香港彩":
        "hk.db"

}



# ==============================
# 原数据源 保留
# ==============================

API_URLS = {


"新澳门彩":
"https://api3.marksix6.net/lottery_api.php?type=newMacau",


"老澳门彩":
"https://api3.marksix6.net/lottery_api.php?type=oldMacau",


"香港彩":
"https://api3.marksix6.net/lottery_api.php?type=hk"


}



# ==============================
# 创建数据库
# ==============================

def init_db(db):

    conn = sqlite3.connect(db)

    cur = conn.cursor()


    cur.execute("""

    CREATE TABLE IF NOT EXISTS history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        issue TEXT UNIQUE,

        numbers TEXT,

        open_time TEXT

    )

    """)


    conn.commit()

    conn.close()



# ==============================
# 读取数据库
# ==============================

def load_history(db):

    conn = sqlite3.connect(db)

    cur = conn.cursor()


    cur.execute("""

    SELECT issue,numbers
    FROM history
    ORDER BY id ASC

    """)


    rows = cur.fetchall()


    conn.close()


    result=[]


    for issue,numbers in rows:

        nums=[int(x) for x in numbers.split(",")]

        result.append({

            "issue":issue,

            "numbers":nums

        })


    return result




# ==============================
# 保存数据
# 防覆盖
# ==============================

def save_history(db, rows):


    conn=sqlite3.connect(db)

    cur=conn.cursor()


    add=0


    for item in rows:


        issue=str(item["issue"])


        nums=",".join(

            str(x)

            for x in item["numbers"]

        )


        try:


            cur.execute("""

            INSERT INTO history

            (
            issue,
            numbers,
            open_time
            )

            VALUES
            (?,?,?)

            """,

            (

            issue,

            nums,

            item.get(
                "openTime",
                ""

            )

            ))


            add+=1


        except sqlite3.IntegrityError:


            pass



    conn.commit()

    conn.close()


    return add





# ==============================
# API请求
# ==============================

def request_json(url):


    try:


        r=requests.get(

            url,

            timeout=15,

            headers={

            "User-Agent":
            "Mozilla/5.0"

            }

        )


        r.encoding="utf-8"


        return r.json()



    except Exception as e:


        print(

            "API失败:",

            e

        )


        return None






# ==============================
# 解析开奖数据
# ==============================

def parse_api(data):


    result=[]


    if not data:

        return result



    # 新接口结构

    if isinstance(data,dict):


        if "lottery_data" in data:


            for x in data["lottery_data"]:


                result.extend(

                    parse_one(x)

                )


        else:


            result.extend(

                parse_one(data)

            )



    elif isinstance(data,list):


        for x in data:

            result.extend(

                parse_one(x)

            )



    return result






def parse_one(item):


    result=[]


    if not isinstance(item,dict):

        return result



    if "history" in item:


        for h in item["history"]:


            try:


                issue=h.split("期")[0]


                code=h.split("：")[1]


                nums=[

                    int(x)

                    for x in code.split(",")

                ]


                result.append({

                    "issue":issue,

                    "numbers":nums

                })


            except:

                pass



    if item.get("expect") and item.get("openCode"):


        nums=[

            int(x)

            for x in item["openCode"].split(",")

        ]


        result.append({

            "issue":

            item["expect"],


            "numbers":

            nums,


            "openTime":

            item.get(
                "openTime",
                ""
            )

        })



    return result






# ==============================
# 同步数据
# ==============================

def sync_lottery(name):


    print("="*60)

    print(
        "同步:",
        name
    )

    print("="*60)


    db=DB_FILES[name]


    init_db(db)



    url=API_URLS[name]


    print(url)


    data=request_json(url)


    rows=parse_api(data)



    print(

        "解析:",
        len(rows),
        "期"

    )



    add=save_history(

        db,

        rows

    )



    history=load_history(db)



    print(

        "新增:",
        add

    )


    print(

        "数据库:",
        len(history),
        "期"

    )


    return history
    # ============================================================
# 49码智能评分引擎
# ============================================================


# ==============================
# 基础工具
# ==============================


def clamp(x,a,b):

    return max(a,min(x,b))



def normalize(counter):

    total=sum(counter.values())

    if total==0:

        return {}

    return {

        k:v/total

        for k,v in counter.items()

    }





# ==============================
# 最近开奖号码
# ==============================

def flatten_numbers(history):


    nums=[]


    for h in history:


        nums.extend(

            h["numbers"]

        )


    return nums





# ==============================
# 号码频率
# ==============================

def frequency_score(history):


    nums=flatten_numbers(history)


    counter=Counter(nums)


    result={}


    maxv=max(

        counter.values()

    ) if counter else 1



    for n in range(1,50):


        result[n]=(

            counter.get(n,0)

            /

            maxv

        )


    return result






# ==============================
# 遗漏评分
# ==============================

def missing_score(history):


    last={}


    for index,h in enumerate(history):


        for n in h["numbers"]:


            last[n]=index



    size=len(history)


    result={}



    for n in range(1,50):


        if n not in last:


            miss=size


        else:


            miss=size-last[n]-1



        # 遗漏越久适当增加

        result[n]=clamp(

            miss/30,

            0,

            1

        )



    return result





# ==============================
# 近期热度
# ==============================


def recent_score(history,period=30):


    data=history[-period:]


    counter=Counter()


    for h in data:


        for n in h["numbers"]:


            counter[n]+=1



    result={}


    maxv=max(

        counter.values()

    ) if counter else 1



    for n in range(1,50):


        result[n]=(

            counter.get(n,0)

            /

            maxv

        )


    return result





# ==============================
# 连续趋势
# ==============================

def trend_score(history):


    result={}


    if len(history)<2:

        return {

            n:0.5

            for n in range(1,50)

        }



    last=history[-1]["numbers"]


    before=history[-2]["numbers"]



    for n in range(1,50):


        if n in last:

            if n in before:

                result[n]=1


            else:

                result[n]=0.7


        else:

            result[n]=0.3



    return result






# ==============================
# 综合号码评分
# ==============================

def score_numbers(history):


    freq = {}

    frequency_score(history)



    miss=

    missing_score(history)



    recent10=

    recent_score(history,10)



    recent20=

    recent_score(history,20)



    recent30=

    recent_score(history,30)



    trend=

    trend_score(history)



    scores={}



    for n in range(1,50):


        score=(


            freq[n]*0.25


            +


            miss[n]*0.15


            +


            recent10[n]*0.25


            +


            recent20[n]*0.15


            +


            recent30[n]*0.10


            +


            trend[n]*0.10



        )



        scores[n]=round(

            score*100,

            2

        )



    return scores






# ==============================
# TOP输出
# ==============================

def top_numbers(scores):


    ranking=sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )


    top5=[

        x[0]

        for x in ranking[:5]

    ]


    top10=[

        x[0]

        for x in ranking[:10]

    ]


    top12=[

        x[0]

        for x in ranking[:12]

    ]



    return {


        "ranking":[

            {

            "number":n,

            "score":s

            }

            for n,s in ranking

        ],


        "top5":top5,


        "top10":top10,


        "top12":top12

    }






# ==============================
# 历史命中测试
# ==============================

def hit_rate(history,window,topn):


    if len(history)<=window:

        return 0



    hits=[]



    start=len(history)-window



    for i in range(start,len(history)):



        train=history[:i]



        scores=

        score_numbers(train)



        top=

        [

        x[0]

        for x in sorted(

            scores.items(),

            key=lambda x:x[1],

            reverse=True

        )[:topn]

        ]



        actual=

        set(

            history[i]["numbers"]

        )


        hit=

        len(

            set(top)&actual

        )


        hits.append(hit)



    if not hits:

        return 0



    return round(

        sum(hits)

        /

        len(hits)

        *

        100,

        2

    )
# ============================================================
# 属性独立预测模块
# ============================================================


# ==============================
# 波色
# ==============================


RED = {
    1,2,7,8,12,13,18,19,
    23,24,29,30,34,35,
    40,45,46
}


BLUE = {
    3,4,9,10,14,15,20,25,
    26,31,36,37,41,42,47,48
}


GREEN = {
    5,6,11,16,17,21,22,27,
    28,32,33,38,39,43,44,49
}



def get_wave(n):

    if n in RED:

        return "红"

    if n in BLUE:

        return "蓝"

    return "绿"





# ==============================
# 大小
# ==============================

def get_size(n):

    return "大" if n>=25 else "小"





# ==============================
# 单双
# ==============================

def get_odd_even(n):

    return "单" if n%2 else "双"





# ==============================
# 生肖映射
# ==============================

ZODIAC = [

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



def get_zodiac(n):


    return ZODIAC[(n-1)%12]






# ==============================
# 属性统计
# ==============================

def attribute_counter(history,func):


    c=Counter()


    for h in history:


        for n in h["numbers"]:


            c[func(n)] +=1



    return c





def attribute_probability(history,func):


    c=

    attribute_counter(

        history,

        func

    )


    total=sum(c.values())



    if total==0:

        return {}



    return {


        k:

        round(

            v/total*100,

            2

        )


        for k,v in c.items()

    }







# ==============================
# 属性预测
# ==============================


def predict_attribute(history,func):


    probs=

    attribute_probability(

        history,

        func

    )


    ranking=sorted(

        probs.items(),

        key=lambda x:x[1],

        reverse=True

    )



    return {


        "probability":

            dict(ranking),


        "main":

            ranking[0][0],


        "top5":

            [

                x[0]

                for x in ranking[:5]

            ]

    }







# ==============================
# 属性近期趋势
# ==============================


def attribute_recent(history,func,period):


    data=history[-period:]


    return attribute_probability(

        data,

        func

    )






# ==============================
# 属性回测
# ==============================


def attribute_hit_rate(history,func,window):


    if len(history)<=window:

        return 0



    hit=0


    total=0



    for i in range(

        len(history)-window,

        len(history)

    ):



        train=history[:i]


        pred=

        predict_attribute(

            train,

            func

        )



        real=set(

            func(n)

            for n in history[i]["numbers"]

        )



        if pred["main"] in real:

            hit+=1



        total+=1



    if total==0:

        return 0



    return round(

        hit/total*100,

        2

    )







# ==============================
# 五大属性分析
# ==============================


def analyze_attributes(history):


    result={}



    # 波色

    result["wave"] = predict_attribute(

        history,

        get_wave

    )


    # 大小

    result["size"] = predict_attribute(

        history,

        get_size

    )


    # 单双

    result["odd_even"] = predict_attribute(

        history,

        get_odd_even

    )


    # 生肖

    result["zodiac"] = predict_attribute(

        history,

        get_zodiac

    )



    result["backtest"]={}



    for name,func in [

        ("wave",get_wave),

        ("size",get_size),

        ("odd_even",get_odd_even),

        ("zodiac",get_zodiac)

    ]:


        result["backtest"][name]={


            "10":

            attribute_hit_rate(

                history,

                func,

                10

            ),


            "20":

            attribute_hit_rate(

                history,

                func,

                20

            ),


            "30":

            attribute_hit_rate(

                history,

                func,

                30

            )


        }



    return result
# ============================================================
# 主预测系统
# V8.3 FINAL
# ============================================================


import os
import json
import datetime
import sqlite3



OUTPUT_DIR="output"


os.makedirs(

    OUTPUT_DIR,

    exist_ok=True

)



# ============================================================
# 数据库读取
# ============================================================


DB_MAP={


    "新澳门彩":

        "new_macau.db",


    "老澳门彩":

        "old_macau.db",


    "香港彩":

        "hk.db"

}




def load_history(db):


    conn=sqlite3.connect(db)


    cur=conn.cursor()



    tables=cur.execute(

        """
        SELECT name FROM sqlite_master
        WHERE type='table'
        """

    ).fetchall()



    if not tables:

        conn.close()

        return []



    table=tables[0][0]



    rows=cur.execute(

        f"""

        SELECT *

        FROM {table}

        """

    ).fetchall()



    cols=[

        x[1]

        for x in cur.execute(

        f"PRAGMA table_info({table})"

        ).fetchall()

    ]



    conn.close()



    history=[]



    for r in rows:


        item=dict(

            zip(cols,r)

        )


        nums=[]


        for key in [

            "numbers",

            "openCode",

            "code"

        ]:


            if key in item and item[key]:


                try:

                    nums=[

                        int(x)

                        for x in str(item[key])

                        .replace(

                            "-",

                            ","

                        )

                        .split(",")

                        if x.strip()

                    ]

                    break

                except:

                    pass



        if len(nums)>=7:


            history.append({

                "issue":

                    item.get(

                        "expect",

                        ""

                    ),


                "numbers":

                    nums[:7]

            })


    return history







# ============================================================
# 49码评分模型
# ============================================================


def score_numbers(history):


    freq=Counter()



    recent=history[-30:]



    for h in recent:


        for n in h["numbers"]:


            freq[n]+=1



    scores={}



    for n in range(1,50):


        score=0



        # 高频

        score+=freq[n]*5



        # 长期冷热

        all_count=Counter()



        for h in history:

            for x in h["numbers"]:

                all_count[x]+=1



        score+=all_count[n]*0.5



        # 最近遗漏

        gap=0


        for h in reversed(history):


            if n in h["numbers"]:

                break

            gap+=1



        score+=min(gap,20)*0.8



        scores[n]=round(

            score,

            3

        )



    ranking=sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )


    return ranking







# ============================================================
# 单彩预测
# ============================================================


def predict_lottery(name,db):


    history=load_history(db)



    if len(history)<30:


        return {


            "success":False,

            "lottery":name,

            "history_size":

                len(history)

        }




    ranking=score_numbers(

        history

    )



    top12=[

        x[0]

        for x in ranking[:12]

    ]



    top10=top12[:10]


    top5=top12[:5]



    latest=history[-1]



    latest_issue=str(

        latest["issue"]

    )



    try:

        next_issue=str(

            int(latest_issue)+1

        )

    except:


        next_issue=""




    result={


        "success":True,


        "lottery":name,


        "latest_issue":

            latest_issue,


        "latest_numbers":

            latest["numbers"],


        "prediction_issue":

            next_issue,


        "history_size":

            len(history),



        "top5":

            top5,


        "top10":

            top10,


        "top12":

            top12,


        "candidates":

            top12,


        "attributes":

            analyze_attributes(

                history

            ),


        "backtest":{


            "method":

                "Walk-Forward",


            "samples":

                len(history)-30


        }


    }



    return result








# ============================================================
# 总入口
# ============================================================


def main():


    print("="*70)

    print(

        "六合彩综合预测系统 V8.3 FINAL"

    )

    print("="*70)



    output={


        "version":

            "V8.3 FINAL",


        "time":

            datetime.datetime.now()

            .isoformat(),


        "rule":

            "49码独立评分+属性独立模型",


        "lotteries":{}

    }



    for name,db in DB_MAP.items():


        print(

            "正在分析:",

            name

        )



        output["lotteries"][name]=predict_lottery(

            name,

            db

        )



    path=os.path.join(

        OUTPUT_DIR,

        "prediction.json"

    )



    with open(

        path,

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            output,

            f,

            ensure_ascii=False,

            indent=2

        )



    print("="*70)

    print(

        "预测完成:",

        path

    )

    print("="*70)





if __name__=="__main__":

    main()
