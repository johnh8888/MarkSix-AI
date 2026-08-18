# -*- coding:utf-8 -*-

"""
在线贝叶斯权重
"""


class BayesianWeight:


    def __init__(self):

        self.models={

            "hot":{
                "hit":1,
                "total":1
            },

            "markov":{
                "hit":1,
                "total":1
            },

            "random":{
                "hit":1,
                "total":1
            }

        }



    def update(self,name,success):


        if name not in self.models:

            return


        self.models[name]["total"]+=1


        if success:

            self.models[name]["hit"]+=1




    def weights(self):


        result={}


        total=0


        for k,v in self.models.items():

            score=(

                v["hit"]

                /

                v["total"]

            )


            result[k]=score

            total+=score




        for k in result:

            result[k]=round(

                result[k]/total,

                3

            )



        return result
