# ============================================================
# 六合智能预测系统
# V8.3 FINAL FIX
#
# 修复:
# 1. history丢失
# 2. 数据库被覆盖
# 3. API格式兼容
#
# Python 3.11+
# ============================================================


import os
import json
import sqlite3
import requests
import datetime
import urllib3

from collections import Counter


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)



VERSION = "V8.3 FINAL FIX"



# ============================================================
# 目录
# ============================================================


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
# 不修改你的源
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
# 只备用，不主动覆盖


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
# 六合属性
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





# ============================================================
# 属性函数
# ============================================================


def get_wave(n):


    if n in RED:

        return "红"


    if n in BLUE:

        return "蓝"


    return "绿"





def get_size(n):


    return (

        "大"

        if n>=25

        else "小"

    )





def get_odd_even(n):


    return (

        "单"

        if n%2

        else "双"

    )





def get_tail(n):


    return n % 10





def get_zodiac(n):


    return ZODIAC[(n-1)%12]





# ============================================================
# 请求
# ============================================================


def request_json(url):


    try:


        r=requests.get(

            url,

            timeout=15,

            verify=False,

            headers={

            "User-Agent":

            "Mozilla/5.0"

            }

        )


        return r.json()



    except Exception as e:


        print(

            "API失败:",

            e

        )


        return None





# ============================================================
# 数字解析
# ============================================================


def parse_numbers(code):


    if isinstance(code,list):

        return [

            int(x)

            for x in code

        ][:7]



    if not code:

        return []



    result=[]



    for x in str(code).split(","):


        x=x.strip()


        if x.isdigit():


            result.append(

                int(x)

            )



    return result[:7]





# ============================================================
# 标准化数据
# ============================================================


def normalize_record(data):


    if not data:

        return None



    issue=str(

        data.get(

            "expect",

            ""

        )

    )



    nums=parse_numbers(

        data.get(

            "openCode",

            ""

        )

    )



    if len(nums)!=7:


        nums=parse_numbers(

            data.get(

                "numbers",

                []

            )

        )



    if len(nums)!=7:

        return None



    return {


        "issue":issue,


        "numbers":nums,


        "openTime":

        data.get(

            "openTime",

            ""

        )

    }

# ============================================================
# API数据解析（核心修复）
# ============================================================


def parse_api_data(lottery, data):


    records=[]



    if not data:

        return records




    # --------------------------------------------------------
    # 情况1:
    # api3.marksix6.net
    #
    # {
    # expect:
    # openCode:
    # history:[]
    # }
    # --------------------------------------------------------


    if isinstance(data,dict):


        # 当前一期


        if "expect" in data:


            records.append(data)




        history=data.get(

            "history",

            []

        )



        for item in history:


            # history字符串

            if isinstance(item,str):


                try:


                    issue=item.split(

                        "期"

                    )[0].strip()



                    code=item.split(

                        "："

                    )[1].strip()



                    records.append({

                        "expect":issue,

                        "openCode":code

                    })


                except:


                    continue



            # history对象

            elif isinstance(item,dict):


                records.append(item)






    # --------------------------------------------------------
    # 情况2:
    # marksix6综合接口
    #
    # lottery_data:[]
    # --------------------------------------------------------


    if isinstance(data,dict):


        lottery_data=data.get(

            "lottery_data",

            []

        )



        for item in lottery_data:


            code=item.get(

                "code",

                ""

            )


            name=item.get(

                "name",

                ""

            )



            if (

                code=={

                "香港彩":"hk",

                "新澳门彩":"newMacau",

                "老澳门彩":"oldMacau"

                }.get(lottery)

                or

                name==lottery

            ):



                records.append(item)



                for h in item.get(

                    "history",

                    []

                ):



                    if isinstance(h,str):


                        try:


                            issue=h.split(

                                "期"

                            )[0]


                            opencode=h.split(

                                "："

                            )[1]



                            records.append({

                                "expect":issue,

                                "openCode":opencode

                            })



                        except:


                            pass






    # --------------------------------------------------------
    # list格式
    # --------------------------------------------------------


    if isinstance(data,list):


        records.extend(data)





    # --------------------------------------------------------
    # 标准化
    # --------------------------------------------------------


    result=[]

    seen=set()



    for r in records:


        n=normalize_record(r)



        if not n:

            continue




        if n["issue"] in seen:

            continue



        seen.add(

            n["issue"]

        )


        result.append(n)




    return result







# ============================================================
# SQLite初始化
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





# ============================================================
# 保存历史
#
# 注意:
# INSERT OR IGNORE
#
# 防止API异常清空数据库
# ============================================================


def save_history(db,records):


    init_db(db)



    conn=sqlite3.connect(db)


    cur=conn.cursor()



    for r in records:


        nums=r["numbers"]



        if len(nums)!=7:

            continue




        cur.execute(

        """

        INSERT OR IGNORE INTO history

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

        r.get(

            "openTime",

            ""

        )

        )

        )



    conn.commit()


    conn.close()







# ============================================================
# 读取数据库
# ============================================================


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

            [

            r[1],

            r[2],

            r[3],

            r[4],

            r[5],

            r[6],

            r[7]

            ],


            "openTime":r[8]

        })



    return result





# ============================================================
# 更新数据库
# ============================================================


def update_database(lottery):


    print()

    print("="*60)

    print(

        "更新",

        lottery

    )

    print("="*60)



    urls=API_LIST[lottery]



    all_records=[]



    for url in urls:


        print(

            "请求:",

            url

        )



        data=request_json(url)



        records=parse_api_data(

            lottery,

            data

        )



        all_records.extend(records)





    print(

        "解析",

        len(all_records),

        "期"

    )




    save_history(

        DB_FILES[lottery],

        all_records

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
# 49码综合评分
# ============================================================


def score_numbers(history):


    scores={

        n:0

        for n in range(1,50)

    }



    if not history:

        return scores





    # --------------------------------------------------------
    # 不同时间窗口
    # --------------------------------------------------------


    last10=history[:10]

    last30=history[:30]

    last100=history[:100]





    freq10=Counter()

    freq30=Counter()

    freq100=Counter()




    for h in last10:


        for n in h["numbers"]:

            freq10[n]+=1



    for h in last30:


        for n in h["numbers"]:

            freq30[n]+=1



    for h in last100:


        for n in h["numbers"]:

            freq100[n]+=1





    for n in range(1,50):



        # ------------------------------------------------
        # 长期稳定
        # ------------------------------------------------

        scores[n]+=freq100[n]*1.0



        # ------------------------------------------------
        # 中期趋势
        # ------------------------------------------------

        scores[n]+=freq30[n]*1.8



        # ------------------------------------------------
        # 短期趋势
        # ------------------------------------------------

        scores[n]+=freq10[n]*2.5





        # ------------------------------------------------
        # 遗漏修正
        # ------------------------------------------------


        miss=0



        for h in history:


            if n in h["numbers"]:

                break


            miss+=1




        # 避免无限补冷

        if miss>0:


            scores[n]+=min(

                miss,

                25

            )*0.12







        # ------------------------------------------------
        # 尾数趋势
        # ------------------------------------------------


        tail_count=0



        for h in last30:


            for x in h["numbers"]:


                if get_tail(x)==get_tail(n):

                    tail_count+=1




        scores[n]+=tail_count*0.15




    return scores





# ============================================================
# 排名
# ============================================================



def rank_numbers(scores):


    return sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )





def top_numbers(scores,n=10):


    return [

        x[0]

        for x in rank_numbers(scores)[:n]

    ]







# ============================================================
# 独立属性模型
# ============================================================



def attribute_score(history,func):


    score=Counter()



    for index,h in enumerate(history[:100]):


        weight=1/(1+index*0.02)



        for n in h["numbers"]:


            score[

                func(n)

            ]+=weight





    return [

        x[0]

        for x in score.most_common()

    ]








# ============================================================
# 生肖预测
# ============================================================


def predict_zodiac(history):


    return attribute_score(

        history,

        get_zodiac

    )[:5]





# ============================================================
# 波色预测
# ============================================================


def predict_wave(history):


    return attribute_score(

        history,

        get_wave

    )





# ============================================================
# 大小预测
# ============================================================


def predict_size(history):


    return attribute_score(

        history,

        get_size

    )





# ============================================================
# 单双预测
# ============================================================


def predict_odd_even(history):


    return attribute_score(

        history,

        get_odd_even

    )






# ============================================================
# 单期预测
# ============================================================


def predict_one(lottery,history):


    if len(history)<30:


        return {


        "success":False,


        "error":

        "历史不足30期"

        }




    scores=score_numbers(

        history

    )



    ranking=rank_numbers(

        scores

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




    latest=history[0]



    try:


        next_issue=str(

            int(

            latest["issue"]

            )+1

        )



    except:


        next_issue=""





    return {


        "success":True,


        "lottery":lottery,


        "latest_issue":

            latest["issue"],



        "prediction_issue":

            next_issue,



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



        "scores":{

            str(k):

            round(v,3)

            for k,v in ranking[:49]

        },



        "attributes":{


            "zodiac":

                predict_zodiac(history),



            "wave":

                predict_wave(history),



            "size":

                predict_size(history),



            "odd_even":

                predict_odd_even(history)

        }


    }


# ============================================================
# 回测模块
# ============================================================


def backtest(history):


    result={}



    for window in [10,20,30]:


        if len(history)<=window+30:


            result[str(window)] = {


                "samples":0,


                "hit_rate":0


            }


            continue





        hit=0

        total=0



        samples=min(

            200,

            len(history)-window

        )




        for i in range(samples):


            train=history[i+window:]


            test=history[i]



            if len(train)<30:

                continue




            scores=score_numbers(

                train

            )



            pred=set(

                top_numbers(

                    scores,

                    10

                )

            )



            real=set(

                test["numbers"]

            )



            hit+=len(

                pred & real

            )



            total+=7





        rate=0



        if total:


            rate=round(

                hit/total*100,

                2

            )



        result[str(window)]={


            "samples":

                samples,


            "hit_rate":

                rate


        }



    return result







# ============================================================
# 输出格式
# ============================================================


def print_result(name,data):


    print()

    print("="*60)

    print(

        "【",

        name,

        "】"

    )

    print("="*60)



    print(

        "历史:",

        data["history_size"]

    )


    print(

        "最新期:",

        data["latest_issue"]

    )



    print(

        "预测期:",

        data["prediction_issue"]

    )



    print()


    print(

        "推荐10码:"

    )



    print(

        " ".join(

            f"{x:02d}"

            for x in data["top10"]

        )

    )



    print()



    print(

        "生肖5推:",

        " "

        .join(

            data["attributes"]

            ["zodiac"]

        )

    )



    print(

        "波色:",

        " "

        .join(

            data["attributes"]

            ["wave"][:3]

        )

    )



    print(

        "大小:",

        " "

        .join(

            data["attributes"]

            ["size"]

        )

    )



    print(

        "单双:",

        " "

        .join(

            data["attributes"]

            ["odd_even"]

        )

    )



    print()


    print(

        "10/20/30期命中率:"

    )


    for k,v in data["backtest"].items():


        print(

            f"{k}期:",

            v["hit_rate"],

            "%"

        )








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

            datetime.datetime.now()

            .isoformat(),


        "lotteries":{}

    }





    for lottery in [

        "新澳门彩",

        "老澳门彩",

        "香港彩"

    ]:



        history=update_database(

            lottery

        )



        data=predict_one(

            lottery,

            history

        )



        if data.get(

            "success"

        ):


            data["backtest"]=backtest(

                history

            )


            print_result(

                lottery,

                data

            )



        else:


            print(

                lottery,

                "失败:",

                data.get(

                    "error"

                )

            )



        output["lotteries"][lottery]=data





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





    print()

    print("="*70)

    print(

        "生成完成:",

        path

    )

    print("="*70)







if __name__=="__main__":


    main()
