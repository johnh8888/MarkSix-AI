# -*- coding:utf-8 -*-

"""
六合彩 AI V4.1 QUANT FINAL

Walk Forward 回测模块


规则:

使用历史数据预测下一期

禁止偷看未来数据


输出:

预测次数
命中次数
命中率
模型评分


"""


from .quant import bayesian_fusion





# =====================================================
# 单次预测
# =====================================================


def predict_once(history):


    scores=bayesian_fusion(

        history

    )


    ranking=sorted(

        scores.items(),

        key=lambda x:x[1],

        reverse=True

    )



    return [


        x[0]

        for x in ranking[:10]

    ]







# =====================================================
# Walk Forward
# =====================================================


def walk_forward(history):


    total=len(history)



    if total<50:


        return {


            "状态":

            "数据不足",


            "历史数量":

            total


        }





    test_count=0


    hit_count=0



    records=[]





    # 保留最后100期测试

    start=max(

        50,

        total-100

    )




    for i in range(

        start,

        total

    ):


        train=history[:i]


        real=history[i]["special"]



        prediction=predict_once(

            train

        )



        hit=real in prediction



        test_count+=1



        if hit:

            hit_count+=1





        records.append(


            {


                "期":

                history[i]["issue"],


                "实际":

                real,


                "预测":

                prediction,


                "命中":

                hit


            }


        )







    rate=round(

        hit_count/

        max(test_count,1),

        3

    )





    return {



        "状态":

        "完成",



        "测试期数":

        test_count,



        "命中次数":

        hit_count,



        "命中率":

        rate,



        "模型评级":

        model_level(

            rate

        ),



        "记录":

        records[-20:]

    }








# =====================================================
# 模型评级
# =====================================================


def model_level(rate):


    if rate>=0.5:


        return "优秀"



    elif rate>=0.35:


        return "良好"



    elif rate>=0.2:


        return "一般"



    else:


        return "需要优化"






__all__=[

    "walk_forward"

]
