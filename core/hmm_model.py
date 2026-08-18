# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/hmm_model.py


隐藏状态模型


功能：

1. 热态识别
2. 冷态识别
3. 平衡状态
4. 混沌检测
5. 输出状态概率


无第三方依赖

"""


from __future__ import annotations


from collections import Counter

import math


from typing import Dict, List





STATES = [

    "hot",

    "cold",

    "balance",

    "chaos"

]







# =====================================================
# 熵
# =====================================================


def entropy(values):


    if not values:

        return 0



    counter=Counter(values)


    total=len(values)


    result=0.0



    for c in counter.values():


        p=c/total


        result-=p*math.log(

            p,

            2

        )



    return result







# =====================================================
# 状态模型
# =====================================================


class StableHMM:



    def __init__(self):


        self.states=STATES



        self.state_probability={

            s:

            0.25

            for s in STATES

        }








    # ------------------------------------
    # 状态判断
    # ------------------------------------


    def analyze(

            self,

            history:List[int]

    ):



        if len(history)<10:


            return {


                "state":

                "balance",


                "probability":

                self.state_probability

            }






        recent=history[:12]


        medium=history[:36]





        recent_count=Counter(
            recent
        )


        medium_count=Counter(
            medium
        )





        recent_max=max(

            recent_count.values()

        )



        concentration=(

            recent_max

            /

            len(recent)

        )







        h_recent=entropy(
            recent
        )


        h_medium=entropy(
            medium
        )



        gap=h_medium-h_recent







        # 热态

        if concentration>=0.25:



            state="hot"



        # 冷态

        elif gap>0.6:



            state="cold"




        # 混沌

        elif h_recent>3.3:



            state="chaos"



        else:


            state="balance"







        probability={

            s:0.05

            for s in STATES

        }



        probability[state]=0.85



        remain=(

            1 -

            probability[state]

        )/3



        for s in STATES:


            if s!=state:


                probability[s]=round(

                    remain,

                    4

                )





        return {


            "state":

            state,


            "probability":

            probability,


            "entropy_recent":

            round(

                h_recent,

                4

            ),


            "entropy_medium":

            round(

                h_medium,

                4

            )


        }







    # ------------------------------------
    # 训练接口
    # ------------------------------------


    def fit(

            self,

            history

    ):


        result=self.analyze(

            history

        )


        self.state_probability=result[

            "probability"

        ]


        return result





    # ------------------------------------
    # 预测状态
    # ------------------------------------


    def predict_next_state(

            self,

            history

    ):


        result=self.analyze(

            history

        )


        return max(

            result["probability"].items(),

            key=lambda x:x[1]

        )[0]








# =====================================================
# 外部接口
# =====================================================


def hmm_state(

        history

):


    model=StableHMM()


    return model.analyze(

        history

    )







def hmm_score(

        history

)->Dict[int,float]:


    """
    HMM输出号码状态评分

    热态:
    最近出现号码增加权重

    冷态:
    增加遗漏号码

    混沌:
    降低影响


    """



    scores={

        n:0.5

        for n in range(1,50)

    }




    if not history:


        return scores





    result=hmm_state(

        history

    )


    state=result["state"]






    recent=history[:12]





    if state=="hot":


        for n in recent:


            scores[n]+=0.3





    elif state=="cold":



        for n in scores:


            if n not in recent:


                scores[n]+=0.15






    elif state=="chaos":



        for n in scores:


            scores[n]=0.5






    else:



        for n in recent:


            scores[n]+=0.1





    return scores







__all__=[

"StableHMM",

"hmm_state",

"hmm_score"

]
