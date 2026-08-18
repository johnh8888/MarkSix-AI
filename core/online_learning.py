# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/online_learning.py


在线学习模块


功能：

1. 记录模型表现
2. 更新模型可信度
3. 输出动态权重
4. 支持 Bayesian Engine


"""


from __future__ import annotations


from typing import Dict, Any





# =====================================================
# 在线学习器
# =====================================================


class OnlineLearner:


    def __init__(self):


        self.models = {}




    # ---------------------------------
    # 注册模型
    # ---------------------------------


    def register(

            self,

            name:str

    ):


        if name not in self.models:


            self.models[name]={


                "hit":0,


                "miss":0,


                "total":0


            }







    # ---------------------------------
    # 更新结果
    # ---------------------------------


    def update(

            self,

            model:str,

            success:bool

    ):


        self.register(model)


        item=self.models[model]


        item["total"]+=1



        if success:


            item["hit"]+=1


        else:


            item["miss"]+=1






    # ---------------------------------
    # 模型准确率
    # ---------------------------------


    def accuracy(

            self,

            model:str

    ):


        if model not in self.models:


            return 0.5



        item=self.models[model]


        if item["total"]==0:


            return 0.5



        return round(

            item["hit"]

            /

            item["total"],

            4

        )






    # ---------------------------------
    # 动态权重
    # ---------------------------------


    def weights(self):


        result={}



        for name in self.models:


            acc=self.accuracy(

                name

            )


            # 平滑

            result[name]=(

                0.5

                +

                acc

            )





        total=sum(

            result.values()

        )



        if total==0:


            return {}




        return {


            k:

            round(

                v/total,

                4

            )


            for k,v

            in result.items()

        }









# =====================================================
# 全局学习器
# =====================================================


ONLINE_ENGINE=OnlineLearner()






# =====================================================
# 快捷接口
# =====================================================


def update_model(

        model_name:str,

        hit:bool

):


    ONLINE_ENGINE.update(

        model_name,

        hit

    )






def get_online_weights()->Dict[str,float]:


    return ONLINE_ENGINE.weights()






def get_learning_state()->Dict[str,Any]:


    return {


        "models":

        ONLINE_ENGINE.models,


        "weights":

        ONLINE_ENGINE.weights()


    }







__all__=[

"OnlineLearner",

"update_model",

"get_online_weights",

"get_learning_state"

]
