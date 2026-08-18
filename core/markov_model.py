# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/markov_model.py


马尔可夫预测模型


功能：

1. 一阶马尔可夫
2. 二阶马尔可夫
3. 状态转移统计
4. 输出号码评分


说明：

彩票不存在确定规律，
该模块只用于历史统计研究。

"""


from __future__ import annotations


from collections import defaultdict, Counter


from typing import Dict, List





NUMBERS=list(range(1,50))





# =====================================================
# 一阶马尔可夫
# =====================================================


class MarkovModel:



    def __init__(

            self,

            order:int=1

    ):


        self.order=order


        self.transition=defaultdict(
            Counter
        )





    # ---------------------------------
    # 训练
    # ---------------------------------


    def fit(

            self,

            history:List[int]

    ):


        if len(history)<=self.order:

            return



        data=list(
            reversed(history)
        )


        for i in range(

            len(data)-self.order

        ):


            state=tuple(

                data[i:i+self.order]

            )


            next_value=data[

                i+self.order

            ]



            self.transition[state][

                next_value

            ]+=1







    # ---------------------------------
    # 转移概率
    # ---------------------------------


    def predict_proba(

            self,

            history:List[int]

    )->Dict[int,float]:


        result={

            n:0

            for n in NUMBERS

        }




        if len(history)<self.order:

            return {

                n:

                1/49

                for n in NUMBERS

            }





        state=tuple(

            reversed(

                history[:self.order]

            )

        )




        counter=self.transition.get(

            state,

            {}

        )



        total=sum(
            counter.values()
        )



        if total==0:


            return {

                n:

                1/49

                for n in NUMBERS

            }




        for n,c in counter.items():


            result[n]=(

                c+1

            )/(

                total+49

            )



        return result






# =====================================================
# 二阶马尔可夫
# =====================================================


class MarkovN(MarkovModel):


    def __init__(self):


        super().__init__(
            order=2
        )






# =====================================================
# 简易评分接口
# =====================================================


def markov_score(

        history:List[int]

)->Dict[int,float]:


    """
    外部调用接口


    返回：

    {
       号码:评分
    }

    """


    if not history:


        return {}





    model1=MarkovModel(
        order=1
    )


    model2=MarkovModel(
        order=2
    )



    model1.fit(
        history
    )


    model2.fit(
        history
    )



    p1=model1.predict_proba(
        history
    )


    p2=model2.predict_proba(
        history
    )




    result={}



    for n in NUMBERS:


        result[n]=(


            p1.get(
                n,
                0
            )
            *

            0.6


            +

            p2.get(
                n,
                0
            )
            *

            0.4


        )



    return result






# =====================================================
# 属性马尔可夫
# =====================================================


def attribute_markov(

        values:List[str]

):


    transition=defaultdict(
        Counter
    )



    for i in range(

        len(values)-1

    ):


        transition[

            values[i]

        ][

            values[i+1]

        ]+=1




    if not values:

        return {}



    current=values[0]



    counter=transition.get(

        current,

        {}

    )



    total=sum(

        counter.values()

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

        in counter.items()

    }






__all__=[

"MarkovModel",

"MarkovN",

"markov_score",

"attribute_markov"

]
