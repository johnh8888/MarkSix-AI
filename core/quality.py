# -*- coding:utf-8 -*-

"""
数据质量检测
"""




def check_quality(history):


    if not history:


        return 0



    score=0



    if len(history)>=50:

        score+=0.5


    if len(history)>=200:

        score+=0.5



    return round(

        score,

        2

    )
