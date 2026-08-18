# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.2 FINAL

core/strategies.py


动态策略引擎


功能：

1. 根据市场状态切换策略
2. 调整模型权重
3. 热态追踪
4. 冷态补偿
5. 混沌降权


"""


from __future__ import annotations


from typing import Dict, Any





# =====================================================
# 基础策略权重
# =====================================================


BASE_WEIGHTS = {


    "frequency":

    0.20,


    "trend":

    0.18,


    "markov":

    0.15,


    "hmm":

    0.15,


    "wave":

    0.12,


    "zodiac":

    0.10,


    "omission":

    0.10


}







# =====================================================
# 权重归一化
# =====================================================


def normalize(

        weights:Dict[str,float]

):


    total=sum(

        weights.values()

    )


    if total<=0:


        return weights



    return {


        k:

        round(

            v/total,

            4

        )

        for k,v

        in weights.items()

    }







# =====================================================
# 动态策略
# =====================================================


class StrategyEngine:



    def __init__(self):


        self.current="balance"






    # ---------------------------------
    # 根据状态选择策略
    # ---------------------------------


    def choose(

            self,

            state:Dict[str,Any]

    ):


        market=state.get(

            "state",

            "balance"

        )


        self.current=market



        weights=BASE_WEIGHTS.copy()






        # =============================
        # 热态
        # =============================


        if market=="hot":


            weights["trend"]+=0.10


            weights["frequency"]+=0.08


            weights["omission"]-=0.05


            weights["zodiac"]+=0.02






        # =============================
        # 冷态
        # =============================


        elif market=="cold":


            weights["omission"]+=0.12


            weights["frequency"]-=0.05


            weights["markov"]+=0.05


            weights["trend"]-=0.03






        # =============================
        # 混沌
        # =============================


        elif market=="chaos":


            # 降低所有趋势模型


            weights["trend"]-=0.05


            weights["markov"]-=0.05


            weights["hmm"]+=0.10


            weights["frequency"]+=0.05


            weights["wave"]+=0.03






        # =============================
        # 平衡
        # =============================


        else:


            weights["frequency"]+=0.05


            weights["markov"]+=0.03






        # 防止负数


        for k in weights:


            if weights[k]<0:


                weights[k]=0.01




        return normalize(weights)







    # ---------------------------------
    # 获取当前策略
    # ---------------------------------


    def name(self):


        return self.current







# =====================================================
# 快捷接口
# =====================================================


def dynamic_strategy(

        state

):


    engine=StrategyEngine()


    return engine.choose(

        state

    )








__all__=[

"StrategyEngine",

"dynamic_strategy"

]
