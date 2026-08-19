# ============================================================
# 六合综合预测系统 V8.3.2 FINAL FIX
#
# 数据源:
# https://marksix6.net/index.php?api=1
#
# Python 3.11+
#
# 修复:
# 1. 历史数据同步
# 2. 数据库
# 3. 49码评分
# 4. 10/20/30期回测
# 5. 简洁输出
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





VERSION = "V8.3.2 FINAL FIX"






# ============================================================
# 路径
# ============================================================


BASE_DIR=os.path.dirname(

    os.path.abspath(__file__)

)



DB_DIR=os.path.join(

    BASE_DIR,

    "database"

)


OUTPUT_DIR=os.path.join(

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
# 数据源
# 保持你的原始接口
# ============================================================


API_URL = (

    "https://marksix6.net/index.php?api=1"

)







# ============================================================
# 数据库
# ============================================================


DB_FILES={


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
# 49码波色
# ============================================================



RED={

1,2,7,8,

12,13,18,19,

23,24,29,30,

34,35,40,45,46

}



BLUE={

3,4,9,10,

14,15,20,25,

26,31,36,37,

41,42,47,48

}



GREEN={

5,6,11,16,

17,21,22,27,

28,32,33,38,

39,43,44,49

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



ZODIAC=[

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


    return ZODIAC[

        (int(n)-1)%12

    ]








# ============================================================
# 请求API
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
# 初始化数据库
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
# 数字解析
# ============================================================


def parse_numbers(code):


    if isinstance(code,list):


        nums=[]


        for x in code:


            try:

                nums.append(

                    int(x)

                )

            except:

                pass



        return nums[:7]



    if not code:

        return []



    nums=[]



    for x in str(code).split(","):


        x=x.strip()


        if x.isdigit():

            nums.append(

                int(x)

            )



    return nums[:7]







# ============================================================
# 解析 marksix API
# ============================================================



def parse_marksix_data(data,lottery):


    result=[]



    if not data:


        return result





    code_map={


        "新澳门彩":

        "newMacau",



        "老澳门彩":

        "oldMacau",



        "香港彩":

        "hk"

    }



    target=code_map[lottery]



    lottery_data=data.get(

        "lottery_data",

        []

    )




    for item in lottery_data:



        if item.get(

            "code"

        ) != target:


            continue




        # -------------------------
        # 最新一期
        # -------------------------


        nums=parse_numbers(

            item.get(

                "openCode",

                ""

            )

        )



        if len(nums)==7:


            result.append({

                "issue":

                str(

                    item.get(

                        "expect",

                        ""

                    )

                ),


                "numbers":

                nums,


                "open_time":

                item.get(

                    "openTime",

                    ""

                )

            })





        # -------------------------
        # 历史
        # -------------------------


        for h in item.get(

            "history",

            []

        ):



            if not isinstance(

                h,

                str

            ):

                continue



            try:



                issue,code=h.split(

                    "期：",

                    1

                )



                nums=parse_numbers(

                    code

                )



                if len(nums)!=7:

                    continue



                result.append({

                    "issue":

                    issue.strip(),


                    "numbers":

                    nums,


                    "open_time":

                    ""

                })



            except:


                continue





    return result







# ============================================================
# 保存历史
# ============================================================


def save_history(path,records):


    init_db(path)



    conn=sqlite3.connect(path)



    cur=conn.cursor()



    for r in records:



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

            r["issue"],


            ",".join(

                str(x)

                for x in r["numbers"]

            ),


            r.get(

                "open_time",

                ""

            )

        )

        )



    conn.commit()

    conn.close()







# ============================================================
# 读取数据库
# ============================================================


def load_history(path):


    init_db(path)



    conn=sqlite3.connect(path)



    cur=conn.cursor()



    cur.execute(

    """

    SELECT

    issue,

    numbers,

    open_time

    FROM history

    ORDER BY issue DESC

    """

    )



    rows=cur.fetchall()



    conn.close()



    result=[]



    for issue,numbers,time in rows:



        nums=parse_numbers(

            numbers

        )



        if len(nums)==7:


            result.append({

                "issue":

                issue,


                "numbers":

                nums,


                "open_time":

                time

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



    records=parse_marksix_data(

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
# 49码评分系统
# ============================================================


def score_numbers(history):


    scores={}


    detail={}



    for n in range(1,50):


        scores[n]=0


        detail[n]={

            "frequency":0,

            "missing":0,

            "tail":0,

            "recent":0

        }






    if len(history)<30:


        return scores,detail






    # 最近窗口


    h10=history[:10]

    h20=history[:20]

    h30=history[:30]

    h100=history[:100]





    freq10=Counter()

    freq20=Counter()

    freq30=Counter()

    freq100=Counter()




    for h in h10:


        for n in h["numbers"]:

            freq10[n]+=1



    for h in h20:


        for n in h["numbers"]:

            freq20[n]+=1



    for h in h30:


        for n in h["numbers"]:

            freq30[n]+=1



    for h in h100:


        for n in h["numbers"]:

            freq100[n]+=1






    for n in range(1,50):


        # =========================
        # 频率评分
        # =========================


        frequency=(

            freq10[n]*2.5

            +

            freq20[n]*1.8

            +

            freq30[n]*1.3

            +

            freq100[n]*0.8

        )


        scores[n]+=frequency


        detail[n]["frequency"]=round(

            frequency,

            2

        )





        # =========================
        # 遗漏评分
        # =========================


        miss=0


        for h in history:


            if n in h["numbers"]:

                break


            miss+=1



        missing=min(

            miss,

            40

        )*0.15



        scores[n]+=missing


        detail[n]["missing"]=round(

            missing,

            2

        )






        # =========================
        # 尾数趋势
        # =========================


        tail_score=0



        for h in h30:


            for x in h["numbers"]:


                if get_tail(x)==get_tail(n):


                    tail_score+=0.12



        scores[n]+=tail_score


        detail[n]["tail"]=round(

            tail_score,

            2

        )






        # =========================
        # 最近走势
        # =========================


        recent=0



        for i,h in enumerate(h10):


            if n in h["numbers"]:


                recent+=(10-i)*0.1




        scores[n]+=recent


        detail[n]["recent"]=round(

            recent,

            2

        )





    return scores,detail







# ============================================================
# 排名
# ============================================================


def rank_numbers(scores):


    return sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )





def top_numbers(scores,count):


    return [

        n

        for n,s in rank_numbers(scores)[:count]

    ]






# ============================================================
# 属性模型
# ============================================================


def attribute_predict(history,func):


    counter=Counter()



    for index,h in enumerate(history[:100]):


        weight=1/(1+index*0.02)



        for n in h["numbers"]:


            counter[

                func(n)

            ]+=weight




    return [

        x[0]

        for x in counter.most_common()

    ]






# ============================================================
# 属性独立输出
# ============================================================


def build_attributes(history):


    return {


        "zodiac":{


            "top5":

            attribute_predict(

                history,

                get_zodiac

            )[:5]

        },



        "wave":{


            "rank":

            attribute_predict(

                history,

                get_wave

            )

        },



        "size":{


            "rank":

            attribute_predict(

                history,

                get_size

            )

        },



        "odd_even":{


            "rank":

            attribute_predict(

                history,

                get_odd_even

            )

        }


    }







# ============================================================
# 生成预测
# ============================================================


def predict_lottery(lottery,history):


    if len(history)<30:


        return {

            "success":

            False,


            "error":

            "历史不足30期"

        }






    scores,detail=score_numbers(

        history

    )



    ranking=rank_numbers(

        scores

    )




    return {


        "success":

        True,



        "lottery":

        lottery,



        "latest_issue":

        history[0]["issue"],



        "latest_numbers":

        history[0]["numbers"],



        "history_size":

        len(history),



        "prediction_issue":

        str(

            int(history[0]["issue"])+1

        ),



        "top5":

        top_numbers(

            scores,

            5

        ),



        "top10":

        top_numbers(

            scores,

            10

        ),



        "top12":

        top_numbers(

            scores,

            12

        ),



        "score_rank":[


            {

                "number":n,

                "score":round(s,2),

                "detail":

                detail[n]

            }


            for n,s in ranking

        ],



        "attributes":

        build_attributes(

            history

        )

    }

# ============================================================
# Walk Forward 回测
# ============================================================


def backtest(history):


    result={}



    for window in [10,20,30]:


        hit=0

        total=0



        samples=min(

            100,

            len(history)-window-40

        )



        if samples<=0:


            result[str(window)]={

                "samples":0,

                "hit_rate":0

            }


            continue






        for i in range(samples):


            # 模拟过去时间点

            train_start=i+window


            train=history[

                train_start:

            ]



            if len(train)<50:

                continue





            scores,_=score_numbers(

                train

            )



            predict=set(

                top_numbers(

                    scores,

                    10

                )

            )



            target=history[i]



            real=set(

                target["numbers"]

            )



            hit += len(

                predict & real

            )



            total += 7






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
# 格式化输出
# ============================================================


def print_report(data):


    if not data.get(

        "success"

    ):


        print(

            "预测失败:",

            data.get(

                "error"

            )

        )

        return





    print()

    print("="*60)

    print(

        "【",

        data["lottery"],

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

        " "

        .join(

            f"{x:02d}"

            for x in data["top10"]

        )

    )





    attr=data["attributes"]




    print()

    print(

        "生肖5推:",

        " ".join(

            attr["zodiac"]["top5"]

        )

    )



    print(

        "波色:",

        " "

        .join(

            attr["wave"]["rank"][:3]

        )

    )


    print(

        "大小:",

        " "

        .join(

            attr["size"]["rank"]

        )

    )


    print(

        "单双:",

        " "

        .join(

            attr["odd_even"]["rank"]

        )

    )





    print()

    print(

        "历史回测:"

    )


    bt=data.get(

        "backtest",

        {}

    )



    for x in [10,20,30]:


        print(

            x,

            "期:",

            bt.get(

                str(x),

                {}

            ).get(

                "hit_rate",

                0

            ),

            "%"

        )





# ============================================================
# 保存JSON
# ============================================================


def save_json(result):


    path=os.path.join(

        OUTPUT_DIR,

        "prediction.json"

    )



    output={


        "version":

        VERSION,


        "time":

        datetime.datetime.now()

        .isoformat(),


        "lotteries":

        result

    }



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

    print(

        "输出完成:",

        path

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




    all_result={}





    lotteries=[


        "新澳门彩",

        "老澳门彩",

        "香港彩"


    ]






    for lottery in lotteries:



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



            print_report(

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



        all_result[lottery]=data







    save_json(

        all_result

    )



    print()

    print("="*70)

    print(

        "系统运行完成"

    )

    print("="*70)







# ============================================================
# 启动
# ============================================================


if __name__=="__main__":


    main()
