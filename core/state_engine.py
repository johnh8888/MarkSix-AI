# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

state_engine.py

动态策略引擎


功能:

1. 读取市场状态
2. 动态调整模型权重
3. 状态切换
4. 权重归一化


"""


from .state import (

    analyze_state,

    STATE_HOT,

    STATE_COLD,

    STATE_BALANCE,

    STATE_CHAOS,

    STATE_REVERSE,

)





# =====================================================
# 默认模型
# =====================================================


DEFAULT_WEIGHTS = {


    "frequency":

        0.20,


    "trend":

        0.15,


    "momentum":

        0.10,


    "omission":

        0.10,


    "adjacency":

        0.08,


    "tail":

        0.07,


    "zone":

        0.05,


    "size":

        0.10,


    "parity":

        0.05,


    "wave":

        0.10,


}





# =====================================================
# 权重归一化
# =====================================================


def normalize_weights(weights):


    total=sum(
        weights.values()
    )


    if total==0:


        return DEFAULT_WEIGHTS.copy()



    return {


        k:

        round(
            v/total,
            4
        )


        for k,v in weights.items()

    }





# =====================================================
# 状态调整规则
# =====================================================


def adjust_by_state(weights,state):


    result=weights.copy()



    # =========================
    # 热态
    # =========================

    if state==STATE_HOT:


        result["trend"]*=1.5

        result["momentum"]*=1.4

        result["frequency"]*=1.2


        result["omission"]*=0.7





    # =========================
    # 冷态
    # =========================

    elif state==STATE_COLD:


        result["omission"]*=1.8

        result["frequency"]*=0.8

        result["trend"]*=0.8





    # =========================
    # 混沌
    # =========================

    elif state==STATE_CHAOS:


        result["frequency"]*=1.2

        result["size"]*=1.3

        result["parity"]*=1.3


        result["momentum"]*=0.6

        result["trend"]*=0.6





    # =========================
    # 反转
    # =========================

    elif state==STATE_REVERSE:


        result["wave"]*=1.8

        result["trend"]*=1.3


        result["frequency"]*=0.8





    # =========================
    # 平衡
    # =========================

    else:


        result["frequency"]*=1.1

        result["trend"]*=1.1





    return normalize_weights(
        result
    )





# =====================================================
# 主入口
# =====================================================


def generate_dynamic_weights(rows):


    state_info=analyze_state(
        rows
    )


    state=state_info.get(
        "state",
        STATE_BALANCE
    )


    weights=adjust_by_state(

        DEFAULT_WEIGHTS,

        state

    )


    return {


        "state":state,


        "state_info":

            state_info,


        "weights":

            weights


    }





# =====================================================
# 获取单独权重
# =====================================================


def get_weights(rows):


    result=generate_dynamic_weights(
        rows
    )


    return result["weights"]





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

        },

    ]



    result=generate_dynamic_weights(
        rows
    )


    print("="*60)

    print(
        "状态:",
        result["state"]
    )


    print(
        "权重:"
    )


    for k,v in result["weights"].items():

        print(
            k,
            v
        )
