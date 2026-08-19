# -*- coding:utf-8 -*-

"""
马尔可夫预测模型
"""


from collections import defaultdict



class MarkovModel:



    def __init__(self):


        self.transition=defaultdict(
            dict
        )





    def train(self,history):


        nums=[

            x["special"]

            for x in history

        ]



        for a,b in zip(

            nums[:-1],

            nums[1:]

        ):


            if b not in self.transition[a]:

                self.transition[a][b]=0


            self.transition[a][b]+=1





    def predict(self,last):


        data=self.transition.get(

            last,

            {}

        )



        if not data:

            return []



        return sorted(

            data.items(),

            key=lambda x:x[1],

            reverse=True

        )





def markov_predict(history):


    model=MarkovModel()


    model.train(history)



    last=history[-1]["special"]



    return model.predict(last)
