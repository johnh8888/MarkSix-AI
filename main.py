# ============================================================
# 六合彩综合预测系统 V8.3 FINAL
# QUANT MULTI ENGINE VERSION
#
# 模块:
# 1. 49码独立评分
# 2. 波色独立预测
# 3. 生肖独立预测
# 4. 大小独立预测
# 5. 单双独立预测
# 6. 10/20/30期回测
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
from collections import Counter


VERSION = "V8.3 FINAL"


# ============================================================
# 配置
# ============================================================


LOTTERIES = {

    "新澳门彩": {
        "code": "newMacau",
        "db": "new_macau.db"
    },

    "老澳门彩": {
        "code": "oldMacau",
        "db": "old_macau.db"
    },

    "香港彩": {
        "code": "hk",
        "db": "hk.db"
    }

}


API_LIST = [

    "https://api3.marksix6.net/lottery_api.php?type={}",

    "https://api.macaumarksix.com/api/macaujc2.com"

]


OUTPUT_DIR = "output"


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)



# ============================================================
# 49码属性
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
    5,6,11,16,17,21,
    22,27,28,32,33,
    38,39,43,44,49
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
# 基础函数
# ============================================================


def get_color(num):

    num = int(num)

    if num in RED:
        return "红"

    if num in BLUE:
        return "蓝"

    return "绿"



def get_size(num):

    num = int(num)

    return "大" if num >= 25 else "小"



def get_odd_even(num):

    num = int(num)

    return "单" if num % 2 else "双"



def get_tail(num):

    return int(num) % 10



def get_zodiac(num):

    """
    49码生肖映射
    """

    num = int(num)

    index = (num + 5) % 12

    return ZODIAC[index]



# ============================================================
# 网络请求
# ============================================================


def request_json(url, timeout=15):

    headers = {

        "User-Agent":
        "Mozilla/5.0"

    }


    try:

        r = requests.get(

            url,
            headers=headers,
            timeout=timeout,
            verify=False

        )

        r.encoding = "utf-8"

        return r.json()


    except Exception as e:

        print(
            "请求失败:",
            url,
            e
        )

        return None




# ============================================================
# 数据解析
# ============================================================


def parse_numbers(code):

    if not code:

        return []


    result = []

    for x in str(code).split(","):

        try:

            result.append(
                int(x)
            )

        except:

            pass


    return result




def parse_history(api_data):

    """

    统一历史格式

    返回:

    [
      {
       issue:"",
       numbers:[]
      }
    ]

    """


    history = []


    if not api_data:

        return history



    # marksix6结构

    if isinstance(api_data,dict):

        data = api_data.get(
            "lottery_data",
            []
        )


        if data:

            item=data[0]

            for h in item.get(
                "history",
                []
            ):

                try:

                    issue = h.split("期")[0]

                    nums = h.split("：")[1]

                    history.append({

                        "issue":issue,

                        "numbers":
                        parse_numbers(nums)

                    })


                except:

                    continue



    # macaumarksix结构

    if isinstance(api_data,list):

        for item in api_data:

            history.append({

                "issue":
                item.get(
                    "expect",
                    ""
                ),

                "numbers":
                parse_numbers(
                    item.get(
                        "openCode",
                        ""
                    )
                )

            })



    return history




# ============================================================
# SQLite
# ============================================================


def init_db(path):

    conn = sqlite3.connect(path)

    c = conn.cursor()


    c.execute(
        """
        CREATE TABLE IF NOT EXISTS history
        (
        issue TEXT PRIMARY KEY,
        numbers TEXT,
        create_time TEXT
        )
        """
    )


    conn.commit()

    conn.close()




def save_history(path,history):

    init_db(path)


    conn = sqlite3.connect(path)

    c = conn.cursor()


    for item in history:


        nums = ",".join(

            str(x)
            for x in item["numbers"]

        )


        c.execute(

            """
            INSERT OR IGNORE INTO history
            VALUES(?,?,?)
            """,

            (

                item["issue"],

                nums,

                datetime.now().isoformat()

            )

        )



    conn.commit()

    conn.close()




def load_history(path):

    init_db(path)


    conn = sqlite3.connect(path)

    c = conn.cursor()


    rows = c.execute(

        """
        SELECT issue,numbers
        FROM history
        ORDER BY issue
        """

    ).fetchall()



    conn.close()


    result=[]


    for issue,nums in rows:


        result.append({

            "issue":

            issue,


            "numbers":

            [
                int(x)
                for x in nums.split(",")
            ]

        })


    return result



# ============================================================
# API同步
# ============================================================


def update_lottery(name):


    cfg = LOTTERIES[name]


    print(
        "="*60
    )

    print(
        "更新:",
        name
    )


    url = API_LIST[0].format(

        cfg["code"]

    )


    print(
        url
    )


    data=request_json(url)


    history=parse_history(data)


    if len(history)<30:


        #备用接口

        data=request_json(

            API_LIST[1]

        )


        history=parse_history(data)



    print(

        "解析:",
        len(history),

        "期"

    )


    save_history(

        cfg["db"],

        history

    )


    local=load_history(

        cfg["db"]

    )


    print(

        "数据库:",
        len(local)

    )


    return local
# ============================================================
# V8.3 FINAL
# 独立预测引擎
# ============================================================



# ============================================================
# 通用统计
# ============================================================


def flatten_history(history):

    nums=[]

    for h in history:

        nums.extend(
            h["numbers"]
        )

    return nums




def recent_history(history,n):

    return history[-n:]




def frequency_score(history):

    """

    49码出现频率

    """

    nums=flatten_history(history)

    counter=Counter(nums)


    result={}


    for i in range(1,50):

        result[i]=counter.get(
            i,
            0
        )


    return result




def omission_score(history):

    """

    遗漏期数

    """

    result={}


    last={}


    for idx,h in enumerate(history):

        for n in h["numbers"]:

            last[n]=idx



    length=len(history)


    for i in range(1,50):

        if i in last:

            result[i]=length-last[i]-1

        else:

            result[i]=length



    return result




# ============================================================
# 1. 49码预测 Engine
# ============================================================


class NumberEngine:


    def __init__(self,history):

        self.history=history



    def score(self):


        freq30=frequency_score(

            recent_history(
                self.history,
                30
            )

        )


        freq100=frequency_score(

            recent_history(
                self.history,
                100
            )

        )


        freq_all=frequency_score(

            self.history

        )


        omission=omission_score(

            self.history

        )



        result={}



        for n in range(1,50):


            score=0


            # 最近趋势

            score += (

                freq30[n]
                /
                max(freq30.values())
                *
                35

            )



            # 中期

            score += (

                freq100[n]
                /
                max(freq100.values())
                *
                25

            )



            # 全历史

            score += (

                freq_all[n]
                /
                max(freq_all.values())
                *
                20

            )



            # 遗漏修正

            if omission[n] >= 8:

                score += 5



            # 小随机保护

            score += random.uniform(
                0,
                5
            )


            result[n]=round(

                score,

                2

            )



        return result




    def predict(self):


        scores=self.score()



        ranking=sorted(

            scores.items(),

            key=lambda x:x[1],

            reverse=True

        )


        top12=[

            x[0]

            for x in ranking[:12]

        ]


        return {


            "scores":

            dict(ranking),


            "top5":

            top12[:5],


            "top10":

            top12[:10],


            "top12":

            top12

        }





# ============================================================
# 2. 波色预测 Engine
# ============================================================


class WaveEngine:


    def __init__(self,history):

        self.history=history



    def predict(self):


        recent=recent_history(

            self.history,

            30

        )


        counter=Counter()



        for h in recent:


            for n in h["numbers"]:


                counter[
                    get_color(n)
                ] += 1



        total=sum(
            counter.values()
        )


        probability={}


        for c in [
            "红",
            "蓝",
            "绿"
        ]:


            probability[c]=round(

                counter[c]
                /
                total
                *
                100,

                2

            )



        rank=sorted(

            probability.items(),

            key=lambda x:x[1],

            reverse=True

        )



        return {


            "probability":

            probability,


            "main":

            rank[0][0],


            "double":

            [
                rank[0][0],
                rank[1][0]
            ]

        }




# ============================================================
# 3. 生肖预测 Engine
# ============================================================


class ZodiacEngine:


    def __init__(self,history):

        self.history=history



    def predict(self):


        recent=recent_history(

            self.history,

            50

        )


        counter=Counter()



        for h in recent:


            for n in h["numbers"]:


                counter[
                    get_zodiac(n)
                ]+=1



        result=[]



        for z in ZODIAC:


            result.append(

                (
                    z,

                    counter[z]

                )

            )



        result.sort(

            key=lambda x:x[1],

            reverse=True

        )



        return {


            "top5":

            [
                x[0]
                for x in result[:5]
            ],


            "ranking":

            result

        }




# ============================================================
# 4. 大小预测 Engine
# ============================================================


class SizeEngine:


    def __init__(self,history):

        self.history=history



    def predict(self):


        counter=Counter()


        recent=recent_history(

            self.history,

            50

        )


        for h in recent:

            for n in h["numbers"]:

                counter[
                    get_size(n)
                ]+=1



        total=sum(
            counter.values()
        )


        big=round(

            counter["大"]
            /
            total
            *
            100,

            2

        )


        small=round(

            counter["小"]
            /
            total
            *
            100,

            2

        )


        return {


            "probability":

            {

                "大":

                big,


                "小":

                small

            },


            "main":

            "大"

            if big>=small

            else

            "小"

        }





# ============================================================
# 5. 单双预测 Engine
# ============================================================


class OddEvenEngine:


    def __init__(self,history):

        self.history=history



    def predict(self):


        counter=Counter()


        recent=recent_history(

            self.history,

            50

        )


        for h in recent:


            for n in h["numbers"]:


                counter[
                    get_odd_even(n)
                ]+=1




        total=sum(
            counter.values()
        )


        odd=round(

            counter["单"]
            /
            total
            *
            100,

            2

        )


        even=round(

            counter["双"]
            /
            total
            *
            100,

            2

        )


        return {


            "probability":

            {

                "单":

                odd,


                "双":

                even

            },


            "main":

            "单"

            if odd>=even

            else

            "双"

        }
# ============================================================
# V8.3 FINAL
# Backtest Engine
#
# 独立模块回测
# ============================================================



class BacktestEngine:


    def __init__(self, history):

        self.history = history



    # --------------------------------------------------------
    # 通用窗口回测
    # --------------------------------------------------------

    def evaluate_windows(
        self,
        predictor,
        windows=(10,20,30)
    ):


        result = {}



        for window in windows:


            result[str(window)] = (
                self.evaluate_last(
                    predictor,
                    window
                )
            )



        return result




    # --------------------------------------------------------
    # 号码Top命中
    # --------------------------------------------------------

    def evaluate_number(
        self,
        top_size=10,
        test_count=30
    ):


        history=self.history



        if len(history)<=test_count:

            return 0



        hit=0

        total=0



        start=len(history)-test_count



        for i in range(
            start,
            len(history)
        ):



            train=history[:i]

            real=history[i]["numbers"]



            pred=NumberEngine(
                train
            ).predict()



            top=pred[

                "top"+str(top_size)

            ]



            special=real[-1]



            if special in top:

                hit+=1



            total+=1



        return round(

            hit /
            total *
            100,

            2

        )





    # --------------------------------------------------------
    # 波色回测
    # --------------------------------------------------------

    def evaluate_wave(
        self,
        test_count=30
    ):


        hit=0

        total=0



        start=len(
            self.history
        )-test_count



        for i in range(
            start,
            len(self.history)
        ):



            train=self.history[:i]

            real=self.history[i]["numbers"][-1]



            pred=WaveEngine(
                train
            ).predict()



            if get_color(real) in pred["double"]:

                hit+=1



            total+=1



        return round(

            hit/
            total*
            100,

            2

        )





    # --------------------------------------------------------
    # 生肖回测
    # --------------------------------------------------------

    def evaluate_zodiac(
        self,
        test_count=30
    ):


        hit=0

        total=0



        start=len(
            self.history
        )-test_count



        for i in range(
            start,
            len(self.history)
        ):


            train=self.history[:i]


            real=self.history[i]["numbers"][-1]


            pred=ZodiacEngine(
                train
            ).predict()



            if get_zodiac(real) in pred["top5"]:

                hit+=1



            total+=1



        return round(

            hit/
            total*
            100,

            2

        )





    # --------------------------------------------------------
    # 大小回测
    # --------------------------------------------------------

    def evaluate_size(
        self,
        test_count=30
    ):


        hit=0

        total=0



        start=len(
            self.history
        )-test_count



        for i in range(
            start,
            len(self.history)
        ):


            train=self.history[:i]


            real=self.history[i]["numbers"][-1]



            pred=SizeEngine(
                train
            ).predict()



            if get_size(real)==pred["main"]:

                hit+=1



            total+=1



        return round(

            hit/
            total*
            100,

            2

        )





    # --------------------------------------------------------
    # 单双回测
    # --------------------------------------------------------

    def evaluate_oddeven(
        self,
        test_count=30
    ):


        hit=0

        total=0



        start=len(
            self.history
        )-test_count



        for i in range(
            start,
            len(self.history)
        ):


            train=self.history[:i]


            real=self.history[i]["numbers"][-1]



            pred=OddEvenEngine(
                train
            ).predict()



            if get_odd_even(real)==pred["main"]:

                hit+=1



            total+=1



        return round(

            hit/
            total*
            100,

            2

        )




    # --------------------------------------------------------
    # 综合回测输出
    # --------------------------------------------------------

    def run(self):


        return {


            "number_top5":

            {

                "10期":

                self.evaluate_number(
                    5,
                    10
                ),


                "20期":

                self.evaluate_number(
                    5,
                    20
                ),


                "30期":

                self.evaluate_number(
                    5,
                    30
                )

            },



            "number_top10":

            {

                "10期":

                self.evaluate_number(
                    10,
                    10
                ),


                "20期":

                self.evaluate_number(
                    10,
                    20
                ),


                "30期":

                self.evaluate_number(
                    10,
                    30
                )

            },



            "wave_double":

            {

                "10期":
                self.evaluate_wave(10),

                "20期":
                self.evaluate_wave(20),

                "30期":
                self.evaluate_wave(30)

            },



            "zodiac_top5":

            {

                "10期":
                self.evaluate_zodiac(10),

                "20期":
                self.evaluate_zodiac(20),

                "30期":
                self.evaluate_zodiac(30)

            },



            "size":

            {

                "10期":
                self.evaluate_size(10),

                "20期":
                self.evaluate_size(20),

                "30期":
                self.evaluate_size(30)

            },



            "odd_even":

            {

                "10期":
                self.evaluate_oddeven(10),

                "20期":
                self.evaluate_oddeven(20),

                "30期":
                self.evaluate_oddeven(30)

            }

        }
        # ============================================================
# V8.3 FINAL
# 主程序
# ============================================================



def save_json(path,data):

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
# 单彩种分析
# ============================================================


def analyze_lottery(
    name,
    history
):


    print()

    print("="*70)

    print(
        name,
        "分析"
    )

    print("="*70)



    if len(history)<30:


        return {


            "success":False,

            "reason":
            "历史不足30期"


        }




    latest = history[-1]



    # ------------------------
    # 号码
    # ------------------------

    number_result = NumberEngine(
        history
    ).predict()



    # ------------------------
    # 波色
    # ------------------------

    wave_result = WaveEngine(
        history
    ).predict()



    # ------------------------
    # 生肖
    # ------------------------

    zodiac_result = ZodiacEngine(
        history
    ).predict()



    # ------------------------
    # 大小
    # ------------------------

    size_result = SizeEngine(
        history
    ).predict()



    # ------------------------
    # 单双
    # ------------------------

    odd_result = OddEvenEngine(
        history
    ).predict()



    # ------------------------
    # 回测
    # ------------------------

    backtest = BacktestEngine(
        history
    ).run()




    prediction_issue = str(

        int(
            latest["issue"]
        )
        +1

    )




    result={



        "success":

        True,



        "lottery":

        name,



        "latest_issue":

        latest["issue"],



        "latest_numbers":

        latest["numbers"],



        "prediction_issue":

        prediction_issue,



        "history_size":

        len(history),




        "number":

        {

            "top5":

            number_result["top5"],


            "top10":

            number_result["top10"],


            "top12":

            number_result["top12"],


            "score":

            number_result["scores"]

        },




        "wave":

        wave_result,



        "zodiac":

        zodiac_result,



        "size":

        size_result,



        "odd_even":

        odd_result,



        "backtest":

        backtest


    }



    return result





# ============================================================
# 中文报告
# ============================================================


def create_report(data):


    lines=[]



    lines.append(

        "六合彩综合预测系统 V8.3 FINAL"

    )


    lines.append(

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    )


    lines.append("")



    for name,item in data["lotteries"].items():


        if not item["success"]:

            continue



        lines.append(

            "="*50

        )


        lines.append(

            name

        )


        lines.append(

            "最新期:"
            +
            item["latest_issue"]

        )


        lines.append(

            "预测期:"
            +
            item["prediction_issue"]

        )



        lines.append("")



        lines.append(

            "【49码推荐Top10】"

        )



        lines.append(

            " ".join(

                f"{x:02d}"

                for x in
                item["number"]["top10"]

            )

        )



        lines.append("")



        lines.append(

            "【波色】"

        )


        lines.append(

            str(
                item["wave"]
            )

        )


        lines.append("")



        lines.append(

            "【生肖Top5】"

        )


        lines.append(

            " ".join(

                item["zodiac"]["top5"]

            )

        )


        lines.append("")



        lines.append(

            "【大小】"

        )


        lines.append(

            str(
                item["size"]
            )

        )


        lines.append("")



        lines.append(

            "【单双】"

        )


        lines.append(

            str(
                item["odd_even"]
            )

        )



        lines.append("")



        lines.append(

            "【回测】"

        )


        lines.append(

            json.dumps(

                item["backtest"],

                ensure_ascii=False

            )

        )



    with open(

        OUTPUT_DIR+"/report.txt",

        "w",

        encoding="utf-8"

    ) as f:


        f.write(

            "\n".join(lines)

        )





# ============================================================
# MAIN
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

        datetime.now().isoformat(),


        "lotteries":{}

    }




    for name in LOTTERIES:


        history=update_lottery(

            name

        )



        result=analyze_lottery(

            name,

            history

        )



        output["lotteries"][name]=result




    save_json(

        OUTPUT_DIR+
        "/prediction.json",

        output

    )



    create_report(

        output

    )



    print()

    print("="*70)

    print(

        "运行完成"

    )

    print("="*70)





if __name__=="__main__":


    main()
