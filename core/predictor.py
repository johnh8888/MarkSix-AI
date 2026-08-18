# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

predictor.py

预测输出模块

"""


from collections import Counter


from .strategies import combine_models


from .features import (

    get_special,

    get_wave,

    get_zodiac,

)





# =====================================================
# 排序Top
# =====================================================


def get_top_numbers(scores,limit=10):


    return sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )[:limit]





# =====================================================
# 特码10码
# =====================================================


def predict_special10(rows):


    scores,models,weights = combine_models(rows)


    top10=get_top_numbers(
        scores,
        10
    )


    return {


        "numbers":

        [
            n
            for n,s in top10
        ],


        "scores":

        {

            str(n):

            round(s,4)

            for n,s in top10

        },


        "all_scores":

        scores,


        "models":

        models,


        "weights":

        weights,

    }





# =====================================================
# 重点推荐
# =====================================================


def predict_focus(rows):


    result=predict_special10(rows)


    nums=result["numbers"]



    return nums[:3]





# =====================================================
# 生肖5肖
# =====================================================


def predict_zodiac(rows):


    result=predict_special10(rows)


    counter=Counter()



    for n in result["numbers"]:


        counter[
            get_zodiac(n)
        ]+=1



    return [

        x[0]

        for x in counter.most_common(5)

    ]





# =====================================================
# 平特2肖
# =====================================================


def predict_flat_zodiac(rows):


    result=predict_special10(rows)


    counter=Counter()



    for n in result["numbers"]:


        counter[
            get_zodiac(n)
        ]+=1



    return [

        x[0]

        for x in counter.most_common(2)

    ]





# =====================================================
# 大小
# =====================================================


def predict_size(rows):


    big=0

    small=0



    result=predict_special10(rows)


    for n in result["numbers"]:


        if n>=25:

            big+=1

        else:

            small+=1



    if big>=small:

        return {


            "recommend":

            "大",


            "prob":

            {

                "大":

                round(big/10,3),


                "小":

                round(small/10,3)

            }

        }


    else:

        return {


            "recommend":

            "小",


            "prob":

            {

                "大":

                round(big/10,3),


                "小":

                round(small/10,3)

            }

        }





# =====================================================
# 单双
# =====================================================


def predict_parity(rows):


    odd=0

    even=0



    result=predict_special10(rows)



    for n in result["numbers"]:


        if n%2:

            odd+=1

        else:

            even+=1



    if odd>=even:

        r="单"

    else:

        r="双"



    return {


        "recommend":r,


        "prob":

        {

        "单":

        round(odd/10,3),


        "双":

        round(even/10,3)

        }

    }





# =====================================================
# 波色预测
# =====================================================


def predict_wave(rows):


    result=predict_special10(rows)



    counter=Counter()



    for n in result["numbers"]:


        counter[
            get_wave(n)
        ]+=1



    total=sum(
        counter.values()
    )



    probs={}


    for k,v in counter.items():

        probs[k]=round(
            v/total,
           3
        )



    order=sorted(

        probs.items(),

        key=lambda x:x[1],

        reverse=True

    )



    return {


        "single":

        order[0][0],



        "double":

        [

            order[0][0],

            order[1][0]

        ],



        "exclude":

        order[-1][0],



        "prob":

        probs

    }





# =====================================================
# 完整预测
# =====================================================


def predict_all(rows,name="unknown"):


    special=predict_special10(rows)



    result={


        "name":

        name,


        "special10":

        special["numbers"],


        "top10_score":

        special["scores"],


        "focus":

        predict_focus(rows),



        "zodiac5":

        predict_zodiac(rows),



        "flat_zodiac2":

        predict_flat_zodiac(rows),



        "size":

        predict_size(rows),



        "parity":

        predict_parity(rows),



        "wave":

        predict_wave(rows),



        "weights":

        special["weights"],

    }



    return result





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    rows=[

        {
        "numbers":
        "38,26,08,06,29,18,23"
        },

        {
        "numbers":
        "33,27,16,28,04,25,14"
        }

    ]


    data=predict_all(
        rows,
        "test"
    )


    print(data)
