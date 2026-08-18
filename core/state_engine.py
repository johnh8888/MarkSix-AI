# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

state_engine.py

状态策略引擎

功能:

1. 读取市场状态
2. 自动调整模型权重
3. 输出当前策略模式
4. 给 predictor 调用


"""


from .state import (

    analyze_state,

    dynamic_weight

)





# =====================================================
# 状态等级
# =====================================================


STATE_LEVEL = {


    "数据不足":0,


    "平衡状态":1,


    "趋势变化状态":2,


    "集中趋势状态":3,


    "连续波状态":4,


    "波色反转状态":4,


    "混沌状态":0

}





# =====================================================
# 获取状态等级
# =====================================================


def get_state_level(
        state
):


    return STATE_LEVEL.get(

        state,

        1

    )





# =====================================================
# 策略名称
# =====================================================


def strategy_name(
        state
):


    mapping={


        "平衡状态":

        "均衡策略",


        "趋势变化状态":

        "趋势跟随策略",


        "集中趋势状态":

        "热态追踪策略",


        "连续波状态":

        "惯性延续策略",


        "波色反转状态":

        "反转防守策略",


        "混沌状态":

        "防守降权策略"

    }



    return mapping.get(

        state,

        "普通策略"

    )





# =====================================================
# 状态引擎
# =====================================================


def build_strategy(
        rows
):


    state_info = analyze_state(

        rows

    )


    weights = dynamic_weight(

        state_info

    )


    state = state_info.get(

        "state",

        "平衡状态"

    )


    return {


        "state":

        state,


        "level":

        get_state_level(

            state

        ),


        "strategy":

        strategy_name(

            state

        ),


        "weights":

        weights,


        "details":

        state_info

    }





# =====================================================
# 权重强化
# =====================================================


def apply_state_boost(
        weights,
        engine
):


    result = weights.copy()



    state=engine.get(

        "state"

    )



    if state=="连续波状态":


        result["wave"] = (

            result.get(
                "wave",
                0
            )

            +

            0.05

        )



    elif state=="波色反转状态":


        result["momentum"]=(

            result.get(
                "momentum",
                0
            )

            +

            0.05

        )



    elif state=="混沌状态":


        result["omission"]=(

            result.get(
                "omission",
                0
            )

            +

            0.08

        )



    total=sum(

        result.values()

    )



    return {


        k:

        round(

            v/total,

            4

        )


        for k,v in result.items()

    }





# =====================================================
# 输出报告
# =====================================================


def state_report(rows):


    engine=build_strategy(

        rows

    )


    return {


        "当前状态":

        engine["state"],


        "策略":

        engine["strategy"],


        "等级":

        engine["level"],


        "权重":

        engine["weights"]

    }





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    test=[

        {

        "numbers":

        "39 41 08 09 07 14 49"

        }

    ]*20



    print(

        state_report(test)

    )
