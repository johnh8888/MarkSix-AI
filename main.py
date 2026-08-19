# ============================================================
# 六合智能预测系统 V1.0 STABLE
# ============================================================
# 稳定版
# 数据源:
# https://marksix6.net/index.php?api=1
#
# 功能:
# SQLite历史保存
# 三彩种独立
# 49码评分
# 生肖/波色/大小/单双
# 简单输出
# ============================================================


import os
import json
import sqlite3
import datetime
import requests

from collections import Counter



VERSION = "V1.0 STABLE"



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
# 数据源
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

    return (
        "大"
        if num >=25
        else
        "小"
    )




# ============================================================
# 单双
# ============================================================


def get_odd_even(num):

    return (
        "单"
        if num % 2
        else
        "双"
    )





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


    conn = sqlite3.connect(
        path
    )


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

            timeout=30,

            verify=False

        )


        r.encoding="utf-8"


        data = r.json()


        return data



    except Exception as e:


        print(
            "API请求失败:",
            e
        )


        return None





# ============================================================
# 号码解析
# ============================================================


def parse_numbers(code):


    if isinstance(code,list):

        try:

            return [

                int(x)

                for x in code

            ]

        except:

            return []




    if isinstance(code,str):


        code = code.replace(

            ",",

            " "

        )


        code = code.replace(

            "|",

            " "

        )


        parts = code.split()



        try:

            return [

                int(x)

                for x in parts

            ]

        except:

            return []



    return []





# ============================================================
# API历史解析
#
# 真实结构:
#
# lottery_data
#       |
#       name
#       |
#       history
#       |
#       openCode
#
# ============================================================


def extract_history(data, lottery):


    result=[]



    if not isinstance(data,dict):

        return result




    lottery_data=data.get(

        "lottery_data",

        []

    )




    for block in lottery_data:



        name=str(

            block.get(

                "name",

                ""

            )

        )



        if lottery not in name:

            continue




        history=block.get(

            "history",

            []

        )




        for item in history:



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

                    ""

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
# 保存历史
# ============================================================


def save_history(lottery,records):


    path=DB_FILES[lottery]


    conn=sqlite3.connect(

        path

    )


    add=0



    for row in records:



        cur=conn.execute(

            """

            INSERT OR IGNORE INTO history

            VALUES(?,?,?)

            """,

            (

            row["issue"],

            json.dumps(

                row["numbers"]

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
# 读取历史
# ============================================================


def load_history(lottery):


    path=DB_FILES[lottery]


    conn=sqlite3.connect(

        path

    )



    rows=conn.execute(

        """

        SELECT

        issue,

        numbers,

        open_time

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

            json.loads(

                r[1]

            ),

            "open_time":r[2]

            }

        )



    return result





# ============================================================
# 同步数据库
# ============================================================


def update_database(lottery):


    print()

    print("="*60)

    print(
        "更新:",
        lottery
    )

    print("="*60)



    api_data=fetch_api()



    records=extract_history(

        api_data,

        lottery

    )



    print(

        "API解析:",

        len(records),

        "期"

    )



    # 数据保护

    if len(records)<30:


        print(

            "⚠️ API数据异常"

        )


        history=load_history(

            lottery

        )


        print(

            "使用本地历史:",

            len(history),

            "期"

        )


        return history




    save_history(

        lottery,

        records

    )



    history=load_history(

        lottery

    )



    print(

        "数据库历史:",

        len(history),

        "期"

    )



    return history
    # ============================================================
# 49码评分模型
# ============================================================


def score_numbers(history):


    scores={}



    recent=[]


    for row in history[:50]:

        recent.extend(
            row["numbers"]
        )



    freq=Counter(
        recent
    )



    # 最近出现位置

    last_seen={}



    for index,row in enumerate(history):


        for n in row["numbers"]:


            if n not in last_seen:

                last_seen[n]=index





    for num in range(1,50):


        score=0



        # 高频奖励

        score += freq.get(
            num,
            0
        ) * 2




        # 遗漏奖励

        miss=last_seen.get(

            num,

            30

        )


        score += min(
            miss,
            20
        )




        # 最近一期关联

        if history and num in history[0]["numbers"]:

            score += 3




        # 尾数趋势

        tail=get_tail(num)



        tail_count=0


        for x in recent:


            if get_tail(x)==tail:

                tail_count+=1



        score += tail_count*0.3




        scores[num]=round(
            score,
            2
        )




    return scores





# ============================================================
# 获取Top号码
# ============================================================


def get_top(scores,count):


    return [

        x[0]

        for x in sorted(

            scores.items(),

            key=lambda x:x[1],

            reverse=True

        )[:count]

    ]





# ============================================================
# 属性统计
# ============================================================


def attribute_predict(numbers):


    wave=[]

    size=[]

    odd=[]

    zodiac=[]



    for n in numbers:


        wave.append(
            get_wave(n)
        )


        size.append(
            get_size(n)
        )


        odd.append(
            get_odd_even(n)
        )


        zodiac.append(
            get_zodiac(n)
        )





    def unique(arr):

        return list(
            dict.fromkeys(arr)
        )




    return {


        "生肖":unique(
            zodiac
        )[:5],


        "波色":unique(
            wave
        ),


        "大小":unique(
            size
        ),


        "单双":unique(
            odd
        )

    }





# ============================================================
# 简单回测
# ============================================================


def backtest(history,top10):


    if len(history)<40:

        return 0



    hit=0

    total=0



    for i in range(
        10,
        min(
            len(history),
            60
        )
    ):



        real=set(
            history[i]["numbers"]
        )


        pred=set(
            top10
        )



        if real & pred:

            hit+=1



        total+=1




    if total==0:

        return 0



    return round(

        hit/total*100,

        2

    )





# ============================================================
# 生成预测
# ============================================================


def build_prediction(lottery,history):


    if len(history)<30:


        return {


            "success":False,


            "error":

            "历史不足30期"

        }





    scores=score_numbers(

        history

    )



    top5=get_top(

        scores,

        5

    )


    top10=get_top(

        scores,

        10

    )


    top12=get_top(

        scores,

        12

    )



    attrs=attribute_predict(

        top10

    )



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


        "历史期数":

        len(history),



        "最新期":

        latest["issue"],



        "预测期":

        next_issue,



        "开奖号码":

        latest["numbers"],



        "Top5":

        top5,



        "Top10":

        top10,



        "Top12":

        top12,



        "属性":

        attrs,



        "回测":

        backtest(

            history,

            top10

        )

    }
   # ============================================================
# 保存JSON
# ============================================================


def save_json(data,filename):


    path=os.path.join(

        OUTPUT_DIR,

        filename

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
# 简单中文输出
# ============================================================


def print_result(name,result):


    if not result.get(
        "success"
    ):


        print()

        print(
            name,
            "预测失败:",
            result.get(
                "error"
            )
        )

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

        result["历史期数"],

        "期"

    )



    print(

        "最新期:",

        result["最新期"]

    )



    print(

        "开奖号码:",

        " ".join(

            f"{x:02d}"

            for x in result["开奖号码"]

        )

    )



    print()

    print(

        "预测期:",

        result["预测期"]

    )



    print()

    print(

        "推荐10码:",

        " ".join(

            f"{x:02d}"

            for x in result["Top10"]

        )

    )



    print()


    print(

        "生肖:",

        " ".join(

            result["属性"]["生肖"]

        )

    )



    print(

        "波色:",

        " ".join(

            result["属性"]["波色"]

        )

    )



    print(

        "大小:",

        " ".join(

            result["属性"]["大小"]

        )

    )



    print(

        "单双:",

        " ".join(

            result["属性"]["单双"]

        )

    )



    print()


    print(

        "回测命中:",

        result["回测"],

        "%"

    )





# ============================================================
# 输出完整结果
# ============================================================


def build_output(results):


    return {


        "系统":

        VERSION,


        "时间":

        datetime.datetime.now().isoformat(),



        "数据源":

        API_URL,



        "彩种":results

    }
# ============================================================
# 主程序
# ============================================================


def main():


    print()

    print("="*70)

    print(

        "六合智能预测系统",

        VERSION

    )

    print("="*70)



    print(

        "数据源:",

        API_URL

    )



    print()



    # 初始化数据库

    init_all_db()



    results={}




    # 三个彩种

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





    output=build_output(

        results

    )



    save_json(

        output,

        "prediction.json"

    )



    print()

    print("="*70)

    print(

        "输出完成"

    )

    print(

        "文件:",

        "output/prediction.json"

    )

    print("="*70)






if __name__=="__main__":


    main()
