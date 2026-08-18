# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.0

predictor.py

核心预测模块


功能:

1. 49号码评分
2. 特码预测
3. 生肖预测
4. 波色预测
5. 大小单双预测

"""


from collections import Counter


from .features import (

    获取波色,

    获取大小,

    获取单双

)


from .zodiac_model import (

    get_zodiac

)


from .wave_model import (

    推荐波色,

    波色概率

)


from .state_engine import (

    状态引擎

)


from .strategies import (

    生成策略

)





# =====================================================
# 基础号码频率
# =====================================================


def 号码频率(

        历史数据

):


    counter=Counter()



    for item in 历史数据:


        for num in item.get(

            "号码",

            []

        ):


            counter[int(num)] +=1



    return counter





# =====================================================
# 号码评分
# =====================================================


def 号码评分(

        历史数据

):


    freq=号码频率(

        历史数据

    )



    scores={}



    for num in range(1,50):


        score=freq.get(

            num,

            0

        )



        scores[num]=score





    最大=max(

        scores.values()

    ) if scores else 1



    for num in scores:


        scores[num]=round(

            scores[num]/最大,

            4

        )



    return dict(

        sorted(

            scores.items(),

            key=lambda x:x[1],

            reverse=True

        )

    )





# =====================================================
# 特码10码
# =====================================================


def predict_numbers(

        历史数据,

        数量=10

):


    scores=号码评分(

        历史数据

    )


    return [

        num

        for num,_ in list(

            scores.items()

        )[:数量]

    ]





# =====================================================
# 第一推荐
# =====================================================


def predict_next(

        历史数据

):


    numbers=predict_numbers(

        历史数据,

        10

    )


    return {


        "特码10码":

        numbers,


        "重点推荐":

        numbers[:3],


        "第一推荐":

        numbers[0]

        if numbers

        else None

    }





# =====================================================
# 生肖预测
# =====================================================


def predict_zodiac(

        历史数据,

        数量=5

):


    numbers=predict_numbers(

        历史数据,

        15

    )



    counter=Counter()



    for num in numbers:


        counter[

            get_zodiac(num)

        ]+=1





    return [

        x[0]

        for x in counter.most_common(

            数量

        )

    ]





# =====================================================
# 波色预测
# =====================================================


def predict_wave(

        历史数据

):


    return 推荐波色(

        历史数据

    )





# =====================================================
# 大小预测
# =====================================================


def predict_size(

        历史数据

):


    numbers=predict_numbers(

        历史数据,

        20

    )



    counter=Counter()



    for num in numbers:


        counter[

            获取大小(num)

        ]+=1





    if counter["大"]>=counter["小"]:


        return {


            "推荐":

            "大",


            "概率":

            round(

                counter["大"]

                /

                len(numbers),

                4

            )

        }



    return {


        "推荐":

        "小",


        "概率":

        round(

            counter["小"]

            /

            len(numbers),

            4

        )

    }





# =====================================================
# 单双预测
# =====================================================


def predict_parity(

        历史数据

):


    numbers=predict_numbers(

        历史数据,

        20

    )



    counter=Counter()



    for num in numbers:


        counter[

            获取单双(num)

        ]+=1





    推荐=max(

        counter,

        key=counter.get

    )



    return {


        "推荐":

        推荐,


        "统计":

        dict(counter)

    }





# =====================================================
# 完整预测入口
# =====================================================


def full_predict(

        历史数据

):


    状态=状态引擎(

        历史数据

    )



    策略=生成策略(

        状态["市场状态"]

    )



    return {


        "市场状态":

        状态,


        "策略":

        策略,


        "预测号码":

        predict_next(

            历史数据

        ),



        "生肖":

        predict_zodiac(

            历史数据

        ),



        "波色":

        predict_wave(

            历史数据

        ),



        "大小":

        predict_size(

            历史数据

        ),



        "单双":

        predict_parity(

            历史数据

        )

    }





if __name__=="__main__":


    print(

        "V5 predictor启动"

    )
