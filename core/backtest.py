# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

backtest.py

Walk Forward历史回测

"""


from .predictor import generate_prediction


from .features import (

    get_wave,

    get_size,

    get_parity

)


from .zodiac_model import (

    get_zodiac

)





# =====================================================
# 解析号码
# =====================================================


def parse_numbers(text):


    if isinstance(text,list):

        return [

            int(x)

            for x in text

        ]



    return [

        int(x)

        for x in str(text)

        .replace(","," ")

        .split()

    ]





# =====================================================
# 获取特码
# =====================================================


def get_special(row):


    nums=parse_numbers(

        row.get(

            "numbers",

            ""

        )

    )


    if len(nums)==0:

        return None


    return nums[-1]





# =====================================================
# 波色判断
# =====================================================


def check_wave(

        prediction,

        actual

):


    waves=prediction.get(

        "波色",

        []

    )


    real=get_wave(

        actual

    )


    return real in waves





# =====================================================
# 大小判断
# =====================================================


def check_size(

        prediction,

        actual

):


    size=get_size(

        actual

    )


    return (

        size==prediction.get(

            "大小"

        )

    )





# =====================================================
# 单双判断
# =====================================================


def check_parity(

        prediction,

        actual

):


    parity=get_parity(

        actual

    )


    return (

        parity==prediction.get(

            "单双"

        )

    )





# =====================================================
# 生肖判断
# =====================================================


def check_zodiac(

        prediction,

        actual,

        year=2026

):


    z=get_zodiac(

        actual,

        year

    )


    return {


        "5肖":

        z in prediction.get(

            "生肖5肖",

            []

        ),



        "2肖":

        z in prediction.get(

            "平特2肖",

            []

        )

    }





# =====================================================
# 单期测试
# =====================================================


def test_one(

        history,

        target

):


    prediction=generate_prediction(

        history

    )


    actual=get_special(

        target

    )



    if actual is None:

        return None





    zodiac=check_zodiac(

        prediction,

        actual

    )



    return {


        "特码":

        actual in prediction.get(

            "特码10码",

            []

        ),



        "生肖5肖":

        zodiac["5肖"],



        "平特2肖":

        zodiac["2肖"],



        "波色":

        check_wave(

            prediction,

            actual

        ),



        "大小":

        check_size(

            prediction,

            actual

        ),



        "单双":

        check_parity(

            prediction,

            actual

        )

    }





# =====================================================
# Walk Forward
# =====================================================


def walk_forward(

        rows,

        window=20

):


    result=[]



    total=len(rows)



    if total<=window:

        return result



    for i in range(

        window,

        total

    ):


        history=rows[i:]



        target=rows[i-1]



        r=test_one(

            history,

            target

        )



        if r:

            result.append(r)



    return result





# =====================================================
# 统计
# =====================================================


def calculate_result(

        records

):


    total=len(records)



    if total==0:

        return {}



    keys=[

        "特码",

        "生肖5肖",

        "平特2肖",

        "波色",

        "大小",

        "单双"

    ]



    result={}



    for k in keys:


        hit=sum(

            1

            for x in records

            if x[k]

        )


        result[k]={


            "命中":

            hit,


            "总数":

            total,


            "命中率":

            round(

                hit/total*100,

                2

            )

        }



    return result





# =====================================================
# 完整回测
# =====================================================


def run_backtest(

        rows

):


    outputs={}



    for window in [10,20]:


        records=walk_forward(

            rows,

            window

        )


        outputs[

            f"最近{window}期"

        ]=calculate_result(

            records

        )



    return outputs





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    test=[

        {

        "numbers":

        "39 41 08 09 07 14 49"

        }

    ]*50



    print(

        run_backtest(test)

    )
