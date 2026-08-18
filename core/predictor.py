# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.0 FINAL

core/predictor.py

预测核心模块

功能：

1. 特码评分融合
2. Top10号码
3. Top3重点号码
4. 生肖预测
5. 大小单双
6. 波色预测
7. 兼容 predict_next()

"""

from __future__ import annotations


from typing import Dict, List, Any


from collections import Counter



# =====================================================
# 基础导入
# =====================================================


try:

    from .features import build_feature_score


except Exception:

    build_feature_score = None



try:

    from .wave_model import predict_wave


except Exception:

    predict_wave = None



try:

    from .zodiac_model import get_zodiac


except Exception:


    def get_zodiac(n):

        return "未知"





# =====================================================
# 常量
# =====================================================


NUMBERS = list(range(1,50))


RED = {
    1,2,7,8,12,13,18,19,
    23,24,29,30,34,35,
    40,45,46
}


BLUE = {
    3,4,9,10,14,15,
    20,25,26,31,
    36,37,41,42,47,48
}


GREEN = {
    5,6,11,16,17,
    21,22,27,28,
    32,33,38,39,43,44,49
}




# =====================================================
# 基础属性
# =====================================================


def get_wave(num:int):

    if num in RED:

        return "红"


    if num in BLUE:

        return "蓝"


    if num in GREEN:

        return "绿"


    return "未知"




def get_size(num:int):

    return "大" if num>=25 else "小"



def get_parity(num:int):

    return "单" if num%2 else "双"





# =====================================================
# 简单评分融合
# =====================================================


def score_numbers(history:List[int])->Dict[int,float]:

    """
    号码综合评分

    注意：
    这里是排序分
    不是中奖概率

    """


    scores={}


    freq=Counter(history[:120])


    for n in NUMBERS:


        score=0



        # 高频

        score += freq[n]*0.4



        # 遗漏补偿

        if n not in history[:10]:

            score +=0.2



        # 最近出现

        if n in history[:36]:

            score +=0.3



        scores[n]=score



    return scores





# =====================================================
# 生肖评分
# =====================================================


def zodiac_rank(scores):


    result={}


    for num,score in scores.items():

        z=get_zodiac(num)


        result[z]=result.get(z,0)+score



    return sorted(
        result.items(),
        key=lambda x:x[1],
        reverse=True
    )





# =====================================================
# 主预测
# =====================================================


def generate_prediction(
        history:List[int]
)->Dict[str,Any]:


    if not history:


        return {

            "error":"没有历史数据"

        }



    scores=score_numbers(history)



    ranking=sorted(
        scores.items(),
        key=lambda x:x[1],
        reverse=True
    )



    top10=[
        n for n,s in ranking[:10]
    ]



    top3=[
        n for n,s in ranking[:3]
    ]



    size_counter=Counter(
        get_size(x)
        for x in history[:36]
    )


    parity_counter=Counter(
        get_parity(x)
        for x in history[:36]
    )



    wave_result={}


    if predict_wave:


        try:

            wave_result=predict_wave(history)


        except Exception:

            wave_result={}




    return {


        "版本":"V5.0 FINAL",


        "说明":
        "模型评分用于排序，不代表真实中奖概率",



        "特码10码":
        top10,



        "重点3码":
        top3,



        "第一推荐":
        top3[0],



        "生肖5肖":
        [
            z
            for z,s
            in zodiac_rank(scores)[:5]
        ],



        "大小":

        max(
            size_counter,
            key=size_counter.get
        ),



        "单双":

        max(
            parity_counter,
            key=parity_counter.get
        ),



        "波色":

        wave_result,


        "评分":

        {
            n:
            round(s,4)

            for n,s
            in ranking[:10]
        }


    }





# =====================================================
# 兼容旧版本接口
# =====================================================


def predict_next(history):


    """
    V3/V4/V5兼容接口

    旧代码调用：

    predict_next(history)

    不会再报错

    """


    return generate_prediction(history)






# =====================================================
# 多彩种接口
# =====================================================


def predict_lottery(
        lottery_name:str,
        history:List[int]
):


    result=generate_prediction(history)


    result["彩种"]=lottery_name


    return result





__all__=[

    "generate_prediction",

    "predict_next",

    "predict_lottery"

]
