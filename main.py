# ============================================================
# 六合智能预测系统 V8.4 FINAL
# ============================================================
# 功能:
# API真实数据同步
# SQLite长期历史
# 49码评分
# 生肖/波色/大小/单双独立预测
# 数据健康检查
# Walk Forward回测
# ============================================================


import os
import json
import sqlite3
import datetime
import requests

from collections import Counter



VERSION = "V8.4 FINAL"



# ============================================================
# 路径
# ============================================================


DATA_DIR = "data"

OUTPUT_DIR = "output"



os.makedirs(
    DATA_DIR,
    exist_ok=True
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)




# ============================================================
# API
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
        DATA_DIR,
        "new_macau.db"
    ),



    "老澳门彩":

    os.path.join(
        DATA_DIR,
        "old_macau.db"
    ),



    "香港彩":

    os.path.join(
        DATA_DIR,
        "hk.db"
    )


}




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

25,26,31,36,37,41,

42,47,48

}



GREEN = {

5,6,11,16,17,21,22,

27,28,32,33,38,39,

43,44,49

}




def get_wave(num):


    if num in RED:

        return "红"


    if num in BLUE:

        return "蓝"


    return "绿"






# ============================================================
# 大小
# ============================================================


def get_size(num):


    if num >= 25:

        return "大"


    return "小"






# ============================================================
# 单双
# ============================================================


def get_odd_even(num):


    if num % 2:

        return "单"


    return "双"







# ============================================================
# 尾数
# ============================================================


def get_tail(num):


    return num % 10






# ============================================================
# 生肖
# ============================================================


ZODIAC = {


    1:"鼠",
    2:"牛",
    3:"虎",
    4:"兔",
    5:"龙",
    6:"蛇",
    7:"马",
    8:"羊",
    9:"猴",
    10:"鸡",
    11:"狗",
    12:"猪"

}





def get_zodiac(num):


    return ZODIAC[

        ((num-1)%12)+1

    ]







# ============================================================
# 初始化数据库
# ============================================================


def init_db(path):


    conn = sqlite3.connect(path)



    conn.execute(

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
# 初始化全部数据库
# ============================================================


def init_all_db():


    for path in DB_FILES.values():

        init_db(path)
# ============================================================
# API请求
# ============================================================


def fetch_api():


    try:


        r = requests.get(

            API_URL,

            timeout=20,

            verify=False

        )


        r.encoding="utf-8"



        data=r.json()



        return data



    except Exception as e:



        print(

            "API请求失败:",

            e

        )



        return None







# ============================================================
# 解析开奖号码
# ============================================================


def parse_numbers(code):


    if isinstance(code,list):

        nums=[

            int(x)

            for x in code

        ]


        return nums




    if isinstance(code,str):


        parts=code.replace(

            ",",

            " "

        ).split()



        return [

            int(x)

            for x in parts

        ]



    return []








# ============================================================
# 提取彩种历史
# ============================================================


def extract_history(data, lottery):


    result=[]



    if not data:


        return result




    items=[]



    if isinstance(data,dict):


        items=data.get(

            "history",

            []

        )



        if not items:


            items=data.get(

                "data",

                []

            )



        if not items:


            items=data.get(

                "lottery_data",

                []

            )





    for item in items:



        if not isinstance(item,dict):

            continue





        name=str(

            item.get(

                "name",

                ""

            )

        )



        # 彩种过滤

        if lottery not in name and name:


            continue





        issue=str(

            item.get(

                "expect",

                item.get(

                    "issue",

                    ""

                )

            )

        )




        code=item.get(

            "openCode",

            item.get(

                "numbers",

                []

            )

        )



        nums=parse_numbers(

            code

        )





        if len(nums)!=7:


            continue





        result.append(

            {

            "issue":issue,

            "numbers":nums,

            "open_time":

            item.get(

                "openTime",

                ""

            )

            }

        )





    return result







# ============================================================
# 保存数据库
# ============================================================


def save_history(

        lottery,

        records

):


    path=DB_FILES[lottery]



    conn=sqlite3.connect(

        path

    )



    cur=conn.cursor()



    add=0



    for row in records:



        cur.execute(

        """

        INSERT OR IGNORE INTO history

        VALUES(?,?,?)

        """,

        (

        row["issue"],

        json.dumps(

            row["numbers"],

            ensure_ascii=False

        ),

        row["open_time"]

        )

        )



        if cur.rowcount:

            add+=1




    conn.commit()

    conn.close()



    return add







# ============================================================
# 读取数据库
# ============================================================


def load_history(lottery):


    path=DB_FILES[lottery]


    conn=sqlite3.connect(

        path

    )



    rows=conn.execute(

    """

    SELECT issue,numbers,open_time

    FROM history

    ORDER BY issue DESC

    """

    ).fetchall()



    conn.close()




    result=[]



    for r in rows:



        result.append(

            {

            "issue":r[0],

            "numbers":

            json.loads(r[1]),

            "open_time":r[2]

            }

        )



    return result







# ============================================================
# 同步数据
# ============================================================


def update_database(lottery):



    print()

    print("="*60)

    print(

        "更新",

        lottery

    )

    print("="*60)




    api_data=fetch_api()



    records=extract_history(

        api_data,

        lottery

    )



    print(

        "解析:",

        len(records),

        "期"

    )



    if len(records)<10:


        print(

            "API返回数据异常，停止写入"

        )


        return load_history(

            lottery

        )





    save_history(

        lottery,

        records

    )



    history=load_history(

        lottery

    )



    print(

        "数据库历史:",

        len(history)

    )



    return history

# ============================================================
# 数据健康检查
# ============================================================


def data_health_check(lottery, history):


    result = {

        "ok": True,

        "errors": [],

        "warnings": []

    }



    if len(history) < 30:


        result["ok"] = False

        result["errors"].append(

            "历史不足30期"

        )



    if not history:


        result["ok"] = False

        result["errors"].append(

            "数据库为空"

        )

        return result





    latest = history[0]



    nums = latest.get(

        "numbers",

        []

    )




    if len(nums) != 7:


        result["ok"] = False

        result["errors"].append(

            "开奖号码不是7个"

        )




    if len(set(nums)) != 7:


        result["ok"] = False

        result["errors"].append(

            "开奖号码重复"

        )





    for n in nums:


        if n < 1 or n > 49:


            result["ok"] = False

            result["errors"].append(

                f"号码异常:{n}"

            )



    return result







# ============================================================
# 49码评分
# ============================================================


def score_numbers(history):


    scores={}



    recent=[]


    for row in history[:30]:


        recent.extend(

            row["numbers"]

        )



    freq=Counter(

        recent

    )



    # 最近遗漏

    last_seen={}



    for i,row in enumerate(history):


        for n in row["numbers"]:


            if n not in last_seen:

                last_seen[n]=i





    for n in range(1,50):


        score=0



        # 频率

        score += freq.get(

            n,

            0

        ) * 2




        # 遗漏

        miss=last_seen.get(

            n,

            30

        )


        score += min(

            miss,

            15

        )




        # 近期出现奖励

        if n in history[0]["numbers"]:


            score += 3




        # 尾数趋势

        tail_count=sum(

            1

            for x in recent

            if get_tail(x)==get_tail(n)

        )


        score += tail_count*0.2





        scores[n]=round(

            score,

            2

        )



    return scores







# ============================================================
# Top号码
# ============================================================


def get_top_numbers(scores, count=10):


    return [

        x[0]

        for x in sorted(

            scores.items(),

            key=lambda x:x[1],

            reverse=True

        )[:count]

    ]







# ============================================================
# 属性预测
# ============================================================


def attribute_predict(numbers):


    waves=[]

    sizes=[]

    odds=[]

    zodiacs=[]




    for n in numbers:


        waves.append(

            get_wave(n)

        )


        sizes.append(

            get_size(n)

        )


        odds.append(

            get_odd_even(n)

        )


        zodiacs.append(

            get_zodiac(n)

        )





    return {


        "zodiac":{

            "top5":

            list(dict.fromkeys(

                zodiacs

            ))[:5],

            "main":

            zodiacs[0]

            if zodiacs else ""

        },


        "wave":{

            "rank":

            list(dict.fromkeys(

                waves

            ))

        },


        "size":{

            "rank":

            list(dict.fromkeys(

                sizes

            ))

        },


        "odd_even":{

            "rank":

            list(dict.fromkeys(

                odds

            ))

        }


    }







# ============================================================
# 模块命中率计算
# ============================================================


def calc_hit_rate(history, top):


    if len(history)<40:

        return 0




    hit=[]



    for i in range(

        10,

        min(

            len(history)-1,

            40

        )

    ):


        actual=set(

            history[i]["numbers"]

        )



        predict=set(top)



        if actual.intersection(

            predict

        ):

            hit.append(1)

        else:

            hit.append(0)



    if not hit:

        return 0



    return round(

        sum(hit)/len(hit)*100,

        2

    )
   # ============================================================
# V8.4 预测生成
# ============================================================


def build_prediction(lottery, history):


    health=data_health_check(

        lottery,

        history

    )



    if not health["ok"]:


        print(

            lottery,

            "数据异常"

        )


        for e in health["errors"]:

            print(

                "❌",

                e

            )



        return {


            "success":False,

            "lottery":lottery,

            "error":

            health["errors"]

        }






    scores=score_numbers(

        history

    )



    top5=get_top_numbers(

        scores,

        5

    )


    top10=get_top_numbers(

        scores,

        10

    )


    top12=get_top_numbers(

        scores,

        12

    )





    attrs=attribute_predict(

        top10

    )






    backtest={



        "10":{

            "hit_rate":

            calc_hit_rate(

                history[10:],

                top10

            )

        },


        "20":{

            "hit_rate":

            calc_hit_rate(

                history[20:],

                top10

            )

        },


        "30":{

            "hit_rate":

            calc_hit_rate(

                history[30:],

                top10

            )

        }


    }






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



        "history_size":

        len(history),



        "latest_numbers":

        latest["numbers"],



        "top5":

        top5,



        "top10":

        top10,



        "top12":

        top12,



        "candidates":

        top12,



        "attributes":

        attrs,



        "scores":

        {

            str(k):

            v

            for k,v in sorted(

                scores.items(),

                key=lambda x:x[1],

                reverse=True

            )[:20]

        },



        "backtest":

        backtest

    }









# ============================================================
# 保存预测结果
# ============================================================


def save_json(data,name):


    path=os.path.join(

        OUTPUT_DIR,

        name

    )



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



    return path







# ============================================================
# 中文终端输出
# ============================================================


def print_result(name,item):


    if not item.get(

        "success"

    ):


        return



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

        item["history_size"],

        "期"

    )


    print(

        "最新开奖:",

        " ".join(

            f"{x:02d}"

            for x in item["latest_numbers"]

        )

    )



    print(

        "预测期:",

        item["prediction_issue"]

    )



    print()

    print(

        "推荐10码:",

        " ".join(

            f"{x:02d}"

            for x in item["top10"]

        )

    )



    attr=item["attributes"]



    print(

        "生肖5推:",

        " ".join(

            attr["zodiac"]["top5"]

        )

    )



    print(

        "波色:",

        " ".join(

            attr["wave"]["rank"]

        )

    )



    print(

        "大小:",

        " ".join(

            attr["size"]["rank"]

        )

    )



    print(

        "单双:",

        " ".join(

            attr["odd_even"]["rank"]

        )

    )



    print()

    print("回测:")



    for k,v in item["backtest"].items():


        print(

            k+"期:",

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



    # 初始化数据库

    init_all_db()



    results={}



    module_performance={}



    backtest_all={}






    for lottery in DB_FILES:



        history=update_database(

            lottery

        )



        result=build_prediction(

            lottery,

            history

        )



        results[lottery]=result



        print_result(

            lottery,

            result

        )



        if result.get(

            "success"

        ):


            backtest_all[lottery]=result.get(

                "backtest",

                {}

            )



            module_performance[lottery]={


                "history":

                result["history_size"],


                "top10":

                result["top10"]

            }





    output={


        "version":

        VERSION,


        "time":

        datetime.datetime.now().isoformat(),



        "rule":

        "49码独立评分模型",



        "lotteries":

        results


    }





    save_json(

        output,

        "prediction.json"

    )



    save_json(

        backtest_all,

        "backtest.json"

    )



    save_json(

        module_performance,

        "module_performance.json"

    )





    print()

    print("="*70)

    print(

        "输出完成"

    )

    print("="*70)







if __name__=="__main__":


    main()
