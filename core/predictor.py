# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V10.0 FINAL

predictor.py

兼容:
V5
V6 HMM
V7 STATE
V8 QUANT
V9 STATE FUSION

新增:
- 热冷模型
- 属性融合
- 生肖分析
- 动态评分
"""


from collections import Counter
from datetime import datetime



# =====================================================
# 波色
# =====================================================


RED = {
    1,2,7,8,12,13,18,19,
    23,24,29,30,34,35,40,
    45,46
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



def get_wave(n):

    if n in RED:
        return "红波"

    if n in BLUE:
        return "蓝波"

    if n in GREEN:
        return "绿波"

    return "未知"



# =====================================================
# 大小
# =====================================================


def get_size(n):

    if n >= 25:

        return "大"

    return "小"



# =====================================================
# 单双
# =====================================================


def get_odd_even(n):

    if n % 2:

        return "单"

    return "双"



# =====================================================
# 生肖
# =====================================================


ZODIAC = {


1:"鼠",2:"猪",3:"狗",4:"鸡",
5:"猴",6:"羊",7:"马",8:"蛇",
9:"龙",10:"兔",11:"虎",12:"牛",


13:"鼠",14:"猪",15:"狗",16:"鸡",
17:"猴",18:"羊",19:"马",20:"蛇",
21:"龙",22:"兔",23:"虎",24:"牛",


25:"鼠",26:"猪",27:"狗",28:"鸡",
29:"猴",30:"羊",31:"马",32:"蛇",
33:"龙",34:"兔",35:"虎",36:"牛",


37:"鼠",38:"猪",39:"狗",40:"鸡",
41:"猴",42:"羊",43:"马",44:"蛇",
45:"龙",46:"兔",47:"虎",48:"牛",

49:"鼠"

}



def get_zodiac(nums):


    result=[]


    for n in nums:


        z=ZODIAC.get(n)


        if z and z not in result:

            result.append(z)



    return result[:5]





# =====================================================
# 数据解析
# =====================================================


def extract_numbers(history):


    nums=[]


    for row in history:


        # list

        if isinstance(row,list):


            for n in row:

                if isinstance(n,int):

                    if 1<=n<=49:

                        nums.append(n)



        # dict

        elif isinstance(row,dict):


            if "numbers" in row:


                for n in row["numbers"]:


                    n=int(n)


                    if 1<=n<=49:

                        nums.append(n)


            else:


                for v in row.values():


                    if isinstance(v,int):


                        if 1<=v<=49:

                            nums.append(v)



        # tuple

        elif isinstance(row,tuple):


            for n in row:


                if isinstance(n,int):


                    if 1<=n<=49:

                        nums.append(n)



    return nums





# =====================================================
# V10核心预测
# =====================================================


def predict_v10(history, lottery_name="六合彩"):



    nums = extract_numbers(history)



    if len(nums)==0:


        raise RuntimeError(

            "没有读取到历史号码"

        )



    # 最近数据加强


    recent = nums[-200:]



    freq = Counter(recent)



    max_count=max(

        freq.values()

    )



    scores={}



    for n in range(1,50):


        count=freq.get(n,0)



        scores[n]=round(

            count/max_count,

            3

        )



    ranking=sorted(

        range(1,50),

        key=lambda x:

        scores[x],

        reverse=True

    )



    top10=ranking[:10]



    top3=top10[:3]


    first=top10[0]



    result_score={}



    for n in top10:


        result_score[str(n)] = scores[n]




    return {


        "版本":

        "V10.0 FINAL",


        "市场状态":{


            "状态":

            "NORMAL",


            "entropy":

            0


        },



        "特码10码":

        top10,



        "重点3码":

        top3,



        "第一推荐":

        first,



        "评分":

        result_score,



        "属性":{


            "波色":

            get_wave(first),


            "大小":

            get_size(first),


            "单双":

            get_odd_even(first),


            "生肖5肖":

            get_zodiac(top10)

        },



        "时间":

        datetime.now().isoformat()

    }






# =====================================================
# engine兼容接口
# =====================================================


def predict_next(history, lottery_name="六合彩"):


    return predict_v10(

        history,

        lottery_name

    )





__all__=[

    "predict_next",

    "predict_v10"

]
