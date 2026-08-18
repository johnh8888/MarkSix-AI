# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

strategies.py

预测策略融合引擎


"""



import math


from core.config import (

    NUMBER_MIN,

    NUMBER_MAX,

    MODEL_WEIGHTS,

    SOFTMAX_TEMPERATURE,

)


from core.features import (

    build_features,

)


from core.state_engine import (

    detect_market_state,

    dynamic_weights,

)





from core.wave_model import (

    wave_score,

)





# =========================================================
# Min-Max
# =========================================================


def normalize(values):


    if not values:

        return {}



    low=min(
        values.values()
    )


    high=max(
        values.values()
    )



    if high==low:

        return {

            k:0.5

            for k in values

        }



    return {


        k:

        (

            v-low

        )

        /

        (

            high-low

        )



        for k,v in values.items()

    }





# =========================================================
# Softmax
# =========================================================


def softmax(scores):


    if not scores:

        return {}



    temp=SOFTMAX_TEMPERATURE



    exp={}



    max_value=max(
        scores.values()
    )



    total=0



    for k,v in scores.items():


        e=math.exp(

            (

                v-max_value

            )

            /

            temp

        )


        exp[k]=e


        total+=e



    return {


        k:

        round(

            v/total,

            6

        )


        for k,v in exp.items()

    }





# =========================================================
# 单模型评分
# =========================================================


def model_scores(rows):


    features=build_features(
        rows
    )



    result={}



    for model,data in features.items():


        if isinstance(data,dict):


            # 数字模型

            if all(

                isinstance(k,int)

                for k in data.keys()

            ):


                result[model]=normalize(

                    data

                )



    return result





# =========================================================
# 波色影响
# =========================================================


def apply_wave_bonus(
        scores,
        rows
):


    waves=wave_score(
        rows
    )


    for n in scores:


        w=__import__(

            "core.features",

            fromlist=[

                "get_wave"

            ]

        ).get_wave(n)



        if w:


            scores[n]+=(

                waves.get(
                    w,
                    0
                )

                *

                0.08

            )



    return scores





# =========================================================
# 主融合
# =========================================================


def combine_prediction(rows):


    """

    返回:

    最终49码评分


    """



    models=model_scores(
        rows
    )



    state=detect_market_state(
        rows
    )



    weights=dynamic_weights(

        MODEL_WEIGHTS,

        state

    )



    final={


        n:0

        for n in range(

            NUMBER_MIN,

            NUMBER_MAX+1

        )

    }




    contribution={}




    for model,scores in models.items():


        weight=weights.get(

            model,

            0

        )


        contribution[model]=weight



        for n,v in scores.items():


            final[n]+=(

                v

                *

                weight

            )



    # 波色增强


    final=apply_wave_bonus(

        final,

        rows

    )



    # softmax概率


    probability=softmax(

        final

    )



    ranking=sorted(

        probability.items(),

        key=lambda x:x[1],

        reverse=True

    )



    return {


        "ranking":

        ranking,


        "probability":

        probability,


        "state":

        state,


        "weights":

        contribution


    }





# =========================================================
# 输出Top10
# =========================================================


def top_numbers(
        rows,
        count=10
):


    result=combine_prediction(
        rows
    )



    return result["ranking"][:count]





# =========================================================
# 测试
# =========================================================


if __name__=="__main__":


    rows=[

        {

        "numbers":

        "38,26,08,06,29,18,23"

        }

    ]



    result=combine_prediction(
        rows
    )


    print(
        "状态:",
        result["state"]
    )



    print(
        "Top10:"
    )



    for n,p in result["ranking"][:10]:


        print(

            n,

            p

        )
