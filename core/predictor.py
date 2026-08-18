# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

predictor.py

预测核心


流程:

历史数据

↓

特征工程

↓

模块评分

↓

动态权重

↓

综合预测

"""


from collections import Counter


import math



from .features import (

    number_feature,

    get_wave,

    get_size,

    get_parity

)


from .zodiac_model import (

    analyze_zodiac

)





# =====================================================
# 默认模块权重
# =====================================================


DEFAULT_WEIGHTS = {


    "frequency":0.20,


    "trend":0.15,


    "momentum":0.12,


    "omission":0.10,


    "wave":0.10,


    "size":0.08,


    "parity":0.08,


    "zodiac":0.07,


    "zone":0.05,


    "tail":0.05


}





# =====================================================
# 历史号码解析
# =====================================================


def parse_history(rows):


    result=[]


    for row in rows:


        nums=row.get(

            "numbers",

            ""

        )


        if isinstance(nums,str):


            nums=nums.replace(

                ",",

                " "

            ).split()



        for n in nums:


            try:

                result.append(

                    int(n)

                )

            except:

                pass



    return result





# =====================================================
# 频率模型
# =====================================================


def frequency_score(numbers):


    counter=Counter(numbers)


    result={}



    for n in range(1,50):


        result[n]=counter.get(

            n,

            0

        )



    return normalize(result)





# =====================================================
# 遗漏模型
# =====================================================


def omission_score(numbers):


    last={}



    for index,n in enumerate(

        reversed(numbers)

    ):


        if n not in last:


            last[n]=index



    result={}



    for n in range(1,50):


        result[n]=last.get(

            n,

            len(numbers)

        )



    return normalize(result)





# =====================================================
# 波色评分
# =====================================================


def wave_score(numbers):


    counter=Counter()



    for n in numbers:


        counter[

            get_wave(n)

        ]+=1



    result={}



    for n in range(1,50):


        result[n]=counter[

            get_wave(n)

        ]



    return normalize(result)





# =====================================================
# 大小单双评分
# =====================================================


def attribute_score(numbers,attr):


    counter=Counter()



    for n in numbers:


        if attr=="size":

            key=get_size(n)


        else:

            key=get_parity(n)



        counter[key]+=1



    result={}



    for n in range(1,50):


        if attr=="size":

            key=get_size(n)


        else:

            key=get_parity(n)



        result[n]=counter[key]



    return normalize(result)





# =====================================================
# 趋势模型
# =====================================================


def trend_score(numbers):


    recent=numbers[:50]


    counter=Counter(

        recent

    )


    result={}



    for n in range(1,50):


        result[n]=counter[n]*1.5



    return normalize(result)





# =====================================================
# 归一化
# =====================================================


def normalize(data):


    values=list(

        data.values()

    )


    total=sum(values)



    if total==0:


        return {


            k:0

            for k in data

        }



    return {


        k:

        v/total

        for k,v in data.items()

    }





# =====================================================
# 综合预测
# =====================================================


def predict_numbers(

        history,

        weights=None

):


    if weights is None:

        weights=DEFAULT_WEIGHTS



    scores={

        n:0

        for n in range(1,50)

    }



    numbers=parse_history(

        history

    )



    models={


        "frequency":

        frequency_score(numbers),


        "trend":

        trend_score(numbers),


        "omission":

        omission_score(numbers),


        "wave":

        wave_score(numbers),


        "size":

        attribute_score(

            numbers,

            "size"

        ),


        "parity":

        attribute_score(

            numbers,

            "parity"

        )

    }





    for model,data in models.items():


        w=weights.get(

            model,

            0

        )


        for n,v in data.items():


            scores[n]+=v*w





    ranking=sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )



    return ranking





# =====================================================
# 完整预测输出
# =====================================================


def generate_prediction(

        history

):


    ranking=predict_numbers(

        history

    )


    top10=[

        x[0]

        for x in ranking[:10]

    ]


    top3=[

        x[0]

        for x in ranking[:3]

    ]



    zodiac=analyze_zodiac(

        history

    )



    wave_counter=Counter()



    for n in top10:


        wave_counter[

            get_wave(n)

        ]+=1



    wave_predict=[

        x[0]

        for x in wave_counter.most_common()

    ]



    return {


        "特码10码":

        top10,


        "重点推荐":

        top3,


        "生肖5肖":

        zodiac["top5"],


        "平特2肖":

        zodiac["top2"],


        "波色":

        wave_predict,


        "评分":

        ranking[:10]

    }





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    data=[


        {

        "numbers":

        "39 41 08 09 07 14 49"

        }

    ]



    print(

        generate_prediction(data)

    )
