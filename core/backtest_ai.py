# -*- coding:utf-8 -*-

"""
六合彩 AI V3.9 FINAL

智能回测系统


功能:

1. Walk Forward
2. 历史模拟预测
3. 命中统计
4. 模型评分
5. 权重反馈


"""


from collections import defaultdict



# =====================================================
# 单次命中
# =====================================================


def check_hit(
        predict_numbers,
        real_number
):


    if real_number in predict_numbers:

        return 1


    return 0





# =====================================================
# 滚动回测
# =====================================================


def walk_forward(
        history,
        predictor,
        window=100
):


    total=0


    hit3=0


    hit10=0



    records=[]



    size=len(history)



    if size<window+10:


        return {


            "状态":
            "数据不足",


            "数量":
            size

        }




    for i in range(
        window,
        size
    ):



        train=history[:i]


        test=history[i]



        try:


            result=predictor(
                train
            )



            top3=result.get(
                "重点3码",
                []
            )



            top10=result.get(
                "特码10码",
                []
            )



            real=test["special"]



            h3=check_hit(

                top3,

                real

            )



            h10=check_hit(

                top10,

                real

            )



            total+=1


            hit3+=h3


            hit10+=h10



            records.append({

                "期":

                test["issue"],


                "真实":

                real,


                "3码命中":

                h3,


                "10码命中":

                h10

            })



        except Exception:


            continue





    return {


        "回测次数":

        total,


        "3码命中":

        hit3,


        "10码命中":

        hit10,



        "3码命中率":

        round(

            hit3/total,

            3

        )
        if total else 0,



        "10码命中率":

        round(

            hit10/total,

            3

        )
        if total else 0,


        "记录":

        records[-20:]

    }





# =====================================================
# 模型评分
# =====================================================


def model_score(backtest):


    rate=backtest.get(

        "10码命中率",

        0

    )



    if rate>=0.8:

        level="优秀"


    elif rate>=0.6:

        level="良好"


    elif rate>=0.4:

        level="一般"


    else:

        level="需要优化"



    return {


        "等级":

        level,


        "评分":

        round(

            rate*100,

            2

        )

    }





__all__=[

"walk_forward",

"model_score"

]
