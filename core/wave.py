# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

波色模型
"""


from collections import Counter



RED = {
    1,2,7,8,12,13,18,19,
    23,24,29,30,34,35,
    40,45,46
}


BLUE = {
    3,4,9,10,14,15,
    20,25,26,31,
    36,37,41,42,47,48
}


GREEN = {
    5,6,11,16,17,
    21,22,27,28,
    32,33,38,39,
    43,44,49
}





def get_wave(num):


    if num in RED:

        return "红波"


    if num in BLUE:

        return "蓝波"


    if num in GREEN:

        return "绿波"



    return "未知"





def predict_wave(history):


    waves=[]


    for row in history[-50:]:


        n=row["special"]


        waves.append(

            get_wave(n)

        )



    counter=Counter(waves)



    return {


        "推荐":

        counter.most_common(1)[0][0],


        "统计":

        dict(counter)

    }
