# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/bayesian_engine.py


贝叶斯模型融合


功能：

1. 多模型权重管理
2. 在线更新模型可信度
3. 防止单模型过拟合
4. 输出融合权重


"""


from __future__ import annotations


from typing import Dict





# =====================================================
# 默认先验
# =====================================================


DEFAULT_MODELS = {


    "frequency":

    1.0,


    "trend":

    1.0,


    "markov":

    1.0,


    "hmm":

    1.0,


    "wave":

    1.0,


    "zodiac":

    1.0

}







# =====================================================
# 贝叶斯权重模型
# =====================================================


class BayesianEngine:



    def __init__(

            self,

            models=None

    ):


        if models is None:

            models=DEFAULT_MODELS



        self.alpha={

            k:2.0

            for k in models

        }



        self.beta={

            k:2.0

            for k in models

        }






    # --------------------------------
    # 更新模型表现
    # --------------------------------


    def update(

            self,

            model_name:str,

            hit:bool

    ):



        if model_name not in self.alpha:


            self.alpha[model_name]=2.0

            self.beta[model_name]=2.0




        if hit:


            self.alpha[model_name]+=1


        else:


            self.beta[model_name]+=1






    # --------------------------------
    # 获取模型概率
    # --------------------------------


    def get_probability(

            self,

            model_name:str

    ):


        a=self.alpha.get(

            model_name,

            2.0

        )


        b=self.beta.get(

            model_name,

            2.0

        )


        return a/(a+b)






    # --------------------------------
    # 所有权重
    # --------------------------------


    def weights(self):


        result={}



        for name in self.alpha:


            result[name]=self.get_probability(
                name
            )



        total=sum(
            result.values()
        )


        if total<=0:


            return {

                k:

                1/len(result)

                for k in result

            }



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
# 融合评分
# =====================================================


def bayesian_fusion(

        predictions:Dict[str,Dict[int,float]]

):


    """
    输入：

    {
      "frequency":{
          1:0.5
      },

      "trend":{
          1:0.8
      }
    }


    输出:

    {
       1:综合评分
    }

    """



    if not predictions:


        return {}





    engine=BayesianEngine(

        predictions.keys()

    )



    weights=engine.weights()



    result={}



    for model,scores in predictions.items():


        w=weights.get(

            model,

            0

        )


        for num,value in scores.items():


            result[num]=(

                result.get(
                    num,
                    0
                )

                +

                value*w

            )



    return result






__all__=[

"BayesianEngine",

"bayesian_fusion"

]
