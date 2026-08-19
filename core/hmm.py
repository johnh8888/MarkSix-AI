# -*- coding:utf-8 -*-

"""
简单HMM状态识别

判断:

热
正常
冷
"""



from collections import Counter





class HMMState:



    def __init__(self):

        self.state="正常"





    def fit(self,history):


        nums=[

            x["special"]

            for x in history[-50:]

        ]



        freq=Counter(nums)



        avg=sum(freq.values())/max(

            len(freq),

            1

        )



        hot=max(

            freq.values(),

            default=0

        )



        if hot > avg*2:


            self.state="热"



        elif len(freq)<20:


            self.state="冷"



        else:


            self.state="正常"





    def predict_state(self):


        return self.state





def detect_state(history):


    model=HMMState()


    model.fit(history)


    return model.predict_state()
