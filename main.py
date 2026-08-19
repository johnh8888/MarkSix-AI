# ============================================================
# 六合综合预测系统 V8.3.1 FINAL FIX
# 数据源修复版
#
# 数据源:
# https://marksix6.net/index.php?api=1
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



VERSION = "V8.3.1 FINAL FIX"



# ============================================================
# 路径
# ============================================================


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)



DB_DIR = os.path.join(
    BASE_DIR,
    "database"
)


OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)



os.makedirs(
    DB_DIR,
    exist_ok=True
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)





# ============================================================
# 你的数据源（保持不变）
# ============================================================


API_URL = (

    "https://marksix6.net/index.php?api=1"

)






# ============================================================
# 数据库
# ============================================================


DB_FILES = {


    "新澳门彩":

    os.path.join(
        DB_DIR,
        "new_macau.db"
    ),



    "老澳门彩":

    os.path.join(
        DB_DIR,
        "old_macau.db"
    ),



    "香港彩":

    os.path.join(
        DB_DIR,
        "hk.db"
    )

}







# ============================================================
# 49码属性
# ============================================================



RED = {

1,2,7,8,12,13,
18,19,23,24,
29,30,34,35,
40,45,46

}



BLUE = {

3,4,9,10,14,
15,20,25,26,
31,36,37,41,
42,47,48

}



GREEN = {

5,6,11,16,17,
21,22,27,28,
32,33,38,39,
43,44,49

}






def get_wave(n):


    n=int(n)


    if n in RED:

        return "红"


    if n in BLUE:

        return "蓝"


    return "绿"





def get_size(n):


    return (

        "大"

        if int(n)>=25

        else

        "小"

    )





def get_odd_even(n):


    return (

        "单"

        if int(n)%2

        else

        "双"

    )





def get_tail(n):


    return int(n)%10





# ============================================================
# 生肖
# ============================================================



ZODIAC = [

"鼠","牛","虎","兔",

"龙","蛇","马","羊",

"猴","鸡","狗","猪"

]



def get_zodiac(n):


    return ZODIAC[

        (int(n)-1)%12

    ]







# ============================================================
# 请求函数
# ============================================================



def request_json(url):


    try:


        print(

            "请求:",

            url

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



        r.raise_for_status()



        return r.json()



    except Exception as e:


        print(

            "请求失败:",

            e

        )


        return None





# ============================================================
# 数据库初始化
# ============================================================



def init_db(path):


    conn=sqlite3.connect(path)



    cur=conn.cursor()



    cur.execute(

    """

    CREATE TABLE IF NOT EXISTS history(

        issue TEXT PRIMARY KEY,

        numbers TEXT,

        open_time TEXT

    )

    """

    )



    conn.commit()

    conn.close()





# ============================================================
# 保存数据
# ============================================================



def save_history(path,records):


    init_db(path)



    conn=sqlite3.connect(path)



    cur=conn.cursor()



    for item in records:



        cur.execute(

        """

        INSERT OR IGNORE INTO history

        (

        issue,

        numbers,

        open_time

        )

        VALUES(?,?,?)

        """,

        (

        item["issue"],

        ",".join(

            map(

                str,

                item["numbers"]

            )

        ),

        item.get(

            "open_time",

            ""

        )

        )

        )




    conn.commit()

    conn.close()


# ============================================================
# 数据标准化
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
# 解析 marksix6 API
#
# lottery_data:
#
# 新澳门彩
# 老澳门彩
# 香港彩
#
# ============================================================



def parse_marksix_api(data,lottery):


    result=[]



    if not data:

        return result





    mapping={


        "香港彩":

        "hk",



        "新澳门彩":

        "newMacau",



        "老澳门彩":

        "oldMacau"


    }



    target=mapping[lottery]




    lottery_data=data.get(

        "lottery_data",

        []

    )




    for item in lottery_data:



        if item.get(

            "code"

        ) != target:



            continue





        # =========================
        # 当前一期
        # =========================


        issue=item.get(

            "expect",

            ""

        )



        code=item.get(

            "openCode",

            ""

        )



        nums=parse_numbers(code)



        if len(nums)==7:


            result.append({


                "issue":

                str(issue),



                "numbers":

                nums,



                "open_time":

                item.get(

                    "openTime",

                    ""

                )


            })






        # =========================
        # 历史
        # =========================



        history=item.get(

            "history",

            []

        )



        for h in history:



            if not isinstance(

                h,

                str

            ):

                continue




            try:


                left,right=h.split(

                    "期：",

                    1

                )



                nums=parse_numbers(

                    right

                )



                if len(nums)!=7:

                    continue



                result.append({


                    "issue":

                    left.strip(),



                    "numbers":

                    nums,



                    "open_time":

                    ""



                })



            except:


                continue




    return result






# ============================================================
# 读取数据库
# ============================================================



def load_history(path):


    init_db(path)



    conn=sqlite3.connect(path)



    cur=conn.cursor()



    cur.execute(

        """

        SELECT issue,numbers,open_time

        FROM history

        ORDER BY issue DESC

        """

    )



    rows=cur.fetchall()



    conn.close()



    result=[]



    for issue,numbers,open_time in rows:



        nums=parse_numbers(numbers)



        if len(nums)==7:


            result.append({


                "issue":

                issue,



                "numbers":

                nums,



                "open_time":

                open_time


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





    data=request_json(

        API_URL

    )



    records=parse_marksix_api(

        data,

        lottery

    )




    print(

        "解析",

        len(records),

        "期"

    )




    if records:


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
# 49号码评分模型
# ============================================================


def score_numbers(history):


    scores={

        n:0

        for n in range(1,50)

    }



    if len(history)<30:

        return scores




    last10=history[:10]

    last20=history[:20]

    last30=history[:30]

    last100=history[:100]



    freq10=Counter()

    freq20=Counter()

    freq30=Counter()

    freq100=Counter()



    for h in last10:


        for n in h["numbers"]:

            freq10[n]+=1



    for h in last20:


        for n in h["numbers"]:

            freq20[n]+=1



    for h in last30:


        for n in h["numbers"]:

            freq30[n]+=1



    for h in last100:


        for n in h["numbers"]:

            freq100[n]+=1





    for n in range(1,50):


        # 长期基础

        scores[n]+=freq100[n]*1.0



        # 中期趋势

        scores[n]+=freq30[n]*1.5



        # 短期趋势

        scores[n]+=freq10[n]*2.0



        # 20期趋势

        scores[n]+=freq20[n]*1.3




        # 遗漏

        miss=0


        for h in history:


            if n in h["numbers"]:

                break


            miss+=1



        scores[n]+=min(

            miss,

            30

        )*0.15





        # 尾数趋势

        tail_hit=0



        for h in last30:


            for x in h["numbers"]:


                if get_tail(x)==get_tail(n):

                    tail_hit+=1




        scores[n]+=tail_hit*0.1




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





def get_top(scores,count):


    return [

        n

        for n,s in rank_numbers(scores)[:count]

    ]








# ============================================================
# 属性独立模型
# ============================================================



def attribute_model(history,func):


    score=Counter()



    for index,h in enumerate(history[:100]):


        weight=1/(1+index*0.03)



        for n in h["numbers"]:


            score[

                func(n)

            ] += weight




    return [

        x[0]

        for x in score.most_common()

    ]








# ============================================================
# 生肖
# ============================================================


def zodiac_predict(history):


    return attribute_model(

        history,

        get_zodiac

    )[:5]





# ============================================================
# 波色
# ============================================================


def wave_predict(history):


    return attribute_model(

        history,

        get_wave

    )





# ============================================================
# 大小
# ============================================================


def size_predict(history):


    return attribute_model(

        history,

        get_size

    )





# ============================================================
# 单双
# ============================================================


def odd_even_predict(history):


    return attribute_model(

        history,

        get_odd_even

    )








# ============================================================
# 单彩预测
# ============================================================


def predict_lottery(lottery,history):


    if len(history)<30:


        return {


            "success":

            False,


            "error":

            "历史不足30期"


        }





    scores=score_numbers(

        history

    )



    ranking=rank_numbers(

        scores

    )




    result={


        "success":

        True,



        "lottery":

        lottery,



        "history_size":

        len(history),



        "latest_issue":

        history[0]["issue"],



        "latest_numbers":

        history[0]["numbers"],



        "top5":

        get_top(

            scores,

            5

        ),



        "top10":

        get_top(

            scores,

            10

        ),



        "top12":

        get_top(

            scores,

            12

        ),



        "score_rank":

        [

            {

                "number":n,

                "score":

                round(

                    s,

                    3

                )

            }

            for n,s in ranking

        ],



        "attributes":{


            "zodiac":

            zodiac_predict(

                history

            ),



            "wave":

            wave_predict(

                history

            ),



            "size":

            size_predict(

                history

            ),



            "odd_even":

            odd_even_predict(

                history

            )

        }



    }





    try:


        result["prediction_issue"]=str(

            int(

                history[0]["issue"]

            )+1

        )



    except:


        result["prediction_issue"]=""



    return result

# ============================================================
# 回测模块
# ============================================================


def backtest(history):


    result={}



    for days in [10,20,30]:


        if len(history)<60:


            result[str(days)]={

                "samples":0,

                "hit_rate":0

            }


            continue





        hit=0

        total=0



        samples=min(

            200,

            len(history)-30

        )




        for i in range(samples):


            train=history[i+30:]


            target=history[i]



            if len(train)<30:

                continue




            scores=score_numbers(

                train

            )



            pred=set(

                get_top(

                    scores,

                    10

                )

            )



            real=set(

                target["numbers"]

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



        result[str(days)]={


            "samples":

            samples,


            "hit_rate":

            rate


        }



    return result








# ============================================================
# 控制台显示
# ============================================================


def show_result(name,data):


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

        data["history_size"],

        "期"

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

        " ".join(

            data["attributes"]

            ["zodiac"]

        )

    )



    print(

        "波色:",

        " ".join(

            data["attributes"]

            ["wave"]

        )

    )


    print(

        "大小:",

        " ".join(

            data["attributes"]

            ["size"]

        )

    )



    print(

        "单双:",

        " ".join(

            data["attributes"]

            ["odd_even"]

        )

    )



    print()



    print(

        "历史回测:"

    )


    for k,v in data["backtest"].items():


        print(

            k,

            "期:",

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



        data=predict_lottery(

            lottery,

            history

        )



        if data.get(

            "success"

        ):


            data["backtest"]=backtest(

                history

            )



            show_result(

                lottery,

                data

            )


        else:


            print(

                lottery,

                "失败:",

                data["error"]

            )




        output["lotteries"][lottery]=data





    output_file=os.path.join(

        OUTPUT_DIR,

        "prediction.json"

    )





    with open(

        output_file,

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

        output_file

    )

    print("="*70)








if __name__=="__main__":


    main()

