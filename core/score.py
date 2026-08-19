# -*- coding:utf-8 -*-

"""
六合彩 AI V4.0

综合评分系统
"""


from collections import Counter



def number_score(history):


    scores={}


    freq=Counter(
        x["special"]
        for x in history
    )


    recent30=[
        x["special"]
        for x in history[-30:]
    ]


    recent10=[
        x["special"]
        for x in history[-10:]
    ]



    for n in range(1,50):


        score=0



        # 历史频率 20%

        score += (
            freq[n]
            /
            max(freq.values(),default=1)
            *
            20
        )



        # 遗漏补偿 15%

        if n not in recent30:

            score+=15



        # 最近走势 15%

        if n in recent10:

            score+=15



        # 尾数周期

        tail=n%10


        tail_count=sum(

            1

            for x in history

            if x["special"]%10==tail

        )


        score += (

            tail_count
            /
            max(len(history),1)
            *
            10

        )



        scores[n]=round(
            score,
            2
        )



    return scores
