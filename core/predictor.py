# -*- coding:utf-8 -*-

"""
V9.0 FINAL预测器

状态机
+
热度
+
Markov
+
贝叶斯
"""


from collections import Counter
import random
from datetime import datetime


from .state_engine import analyze_state



def predict_next(history):


    if len(history)<30:

        return {

            "error":

            "数据不足"

        }



    state=analyze_state(history)



    counter=Counter(history)



    scores={}



    # 热度

    for n in range(1,50):


        hot=counter[n]/len(history)



        scores[n]=hot*10




    # 状态调整


    if state["state"]=="HOT":


        for n in scores:

            scores[n]*=1.2



    elif state["state"]=="COLD":


        for n in scores:

            scores[n]*=0.8



    elif state["state"]=="CHAOS":


        for n in scores:

            scores[n]*=0.9

            scores[n]+=random.random()*0.5



    elif state["state"]=="REVERSAL":


        for n in scores:

            scores[n]+=random.random()*1.2




    result=sorted(

        scores,

        key=scores.get,

        reverse=True

    )



    top10=result[:10]



    top3=top10[:3]



    first=top3[0]



    return {


        "版本":

        "V9.0 STATE FUSION",


        "市场状态":

        state,


        "特码10码":

        top10,


        "重点3码":

        top3,


        "第一推荐":

        first,


        "评分":

        {

            str(k):

            round(scores[k],3)

            for k in top10

        },


        "时间":

        datetime.now().isoformat()


    }
