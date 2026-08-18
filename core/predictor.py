# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V10.0 QUANT FINAL

预测输出统一模块

功能:

1. 特码评分
2. 状态融合
3. 属性分析
4. 中文输出
5. 标准JSON结构
"""


from datetime import datetime
import random



# ===============================
# 属性
# ===============================


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



def get_color(num):

    if num in RED:
        return "红"

    if num in BLUE:
        return "蓝"

    return "绿"



def get_size(num):

    return "大" if num >=25 else "小"



def get_odd_even(num):

    return "单" if num % 2 else "双"




# ===============================
# 状态中文
# ===============================


STATE_MAP={


    "NORMAL":
    "正常状态",


    "HOT":
    "热区状态",


    "COLD":
    "冷区状态",


    "REVERSAL":
    "反转状态",


    "CHAOS":
    "混沌状态"

}




# ===============================
# 生成预测
# ===============================


def build_prediction_output(


        lottery,


        numbers,


        state=None,


        scores=None,


        backtest=None



):


    if state is None:

        state={}


    if scores is None:

        scores={}



    state_code = state.get(

        "state",

        "NORMAL"

    )


    state_name = STATE_MAP.get(

        state_code,

        "正常状态"

    )



    first = numbers[0]



    result={



        "版本":

        "V10.0 QUANT FINAL",



        "彩种":

        lottery,



        "时间":

        datetime.now().isoformat(),




        "状态":

        {


            "名称":

            state_name,


            "状态代码":

            state_code,


            "熵值":

            round(

                state.get(
                    "entropy",
                    0
                ),

                4

            ),


            "重复率":

            round(

                state.get(
                    "repeat_rate",
                    0
                ),

                4

            )


        },




        "预测":

        {


            "特码10码":

            numbers[:10],



            "重点3码":

            numbers[:3],



            "第一推荐":

            first


        },





        "属性":

        {


            "波色":

            get_color(first),



            "大小":

            get_size(first),



            "单双":

            get_odd_even(first)


        },




        "评分":

        scores,




        "模型":

        {


            "状态引擎":

            True,


            "Markov":

            True,


            "贝叶斯":

            True


        },




        "回测":

        backtest or {}



    }


    return result





__all__=[

    "build_prediction_output",

    "get_color",

    "get_size",

    "get_odd_even"

]
# =====================================================
# V10 FINAL 兼容旧接口
# =====================================================


def predict_next(
    history,
    lottery_name="六合彩"
):

    """
    兼容 V5-V9 engine调用

    返回格式保持旧版
    """

    try:

        # 调用V10核心预测

        result = predict_v10(
            history,
            lottery_name
        )


        return {

            "版本":
            "V10.0 FINAL",


            "特码10码":
            result.get(
                "numbers",
                []
            ),


            "重点3码":
            result.get(
                "top3",
                []
            ),


            "第一推荐":
            result.get(
                "first",
                None
            ),


            "评分":
            result.get(
                "scores",
                {}
            ),


            "属性":
            result.get(
                "attributes",
                {})


        }


    except Exception as e:


        # 防止workflow中断

        return {

            "版本":
            "V10.0 FINAL ERROR",

            "错误":
            str(e),

            "特码10码":
            [],

            "重点3码":
            [],

            "第一推荐":
            None

        }



__all__=[

    "predict_next"

]
