# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.1

markov_model.py

马尔可夫链预测模块


功能:

1. 状态转移统计
2. 一阶马尔可夫
3. 二阶马尔可夫
4. 概率预测


"""


from collections import defaultdict

from collections import Counter





# =====================================================
# 状态转移矩阵
# =====================================================


class MarkovModel:


    def __init__(self):


        self.transitions=defaultdict(

            Counter

        )



    # -------------------------------------------------

    # 训练

    # -------------------------------------------------


    def train(

            self,

            sequence

    ):


        if len(sequence)<2:


            return



        for i in range(

            len(sequence)-1

        ):


            current=sequence[i]


            next_state=sequence[i+1]



            self.transitions[current][next_state]+=1






    # -------------------------------------------------

    # 转移概率

    # -------------------------------------------------


    def probability(

            self,

            state

    ):


        result={}



        data=self.transitions.get(

            state,

            {}

        )


        total=sum(

            data.values()

        )



        if total==0:


            return {}





        for k,v in data.items():


            result[k]=round(

                v/total,

                4

            )



        return dict(

            sorted(

                result.items(),

                key=lambda x:x[1],

                reverse=True

            )

        )





    # -------------------------------------------------

    # 下一状态预测

    # -------------------------------------------------


    def predict(

            self,

            current

    ):


        prob=self.probability(

            current

        )



        if not prob:


            return None



        return max(

            prob,

            key=prob.get

        )





# =====================================================
# 二阶马尔可夫
# =====================================================


class MarkovOrder2:



    def __init__(self):


        self.transitions=defaultdict(

            Counter

        )




    def train(

            self,

            sequence

    ):


        if len(sequence)<3:


            return



        for i in range(

            len(sequence)-2

        ):


            state=(

                sequence[i],

                sequence[i+1]

            )



            nxt=sequence[i+2]



            self.transitions[state][nxt]+=1






    def predict(

            self,

            last_two

    ):


        data=self.transitions.get(

            tuple(last_two),

            {}

        )



        if not data:


            return None



        return max(

            data,

            key=data.get

        )





# =====================================================
# 波色马尔可夫
# =====================================================


def 波色序列(

        历史数据

):


    seq=[]


    for item in 历史数据:


        if "波色" in item:


            seq.append(

                item["波色"]

            )



    return seq





def 训练波色模型(

        历史数据

):


    seq=波色序列(

        历史数据

    )



    model=MarkovModel()



    model.train(

        seq

    )


    return model





# =====================================================
# 大小序列
# =====================================================


def 大小序列(

        历史数据

):


    result=[]



    for item in 历史数据:


        if "大小" in item:


            result.append(

                item["大小"]

            )



    return result





def 训练大小模型(

        历史数据

):


    model=MarkovModel()



    model.train(

        大小序列(

            历史数据

        )

    )


    return model





# =====================================================
# 单双序列
# =====================================================


def 单双序列(

        历史数据

):


    result=[]



    for item in 历史数据:


        if "单双" in item:


            result.append(

                item["单双"]

            )



    return result





def 训练单双模型(

        历史数据

):


    model=MarkovModel()



    model.train(

        单双序列(

            历史数据

        )

    )


    return model





# =====================================================
# 号码转移
# =====================================================


def 号码转移模型(

        历史数据

):


    model=MarkovModel()



    seq=[]



    for item in 历史数据:


        nums=item.get(

            "号码",

            []

        )


        if nums:


            seq.append(

                nums[0]

            )



    model.train(

        seq

    )


    return model





# =====================================================
# 综合接口
# =====================================================


def 创建马尔可夫模型(

        历史数据

):


    return {


        "波色":

        训练波色模型(

            历史数据

        ),



        "大小":

        训练大小模型(

            历史数据

        ),



        "单双":

        训练单双模型(

            历史数据

        ),



        "号码":

        号码转移模型(

            历史数据

        )

    }





if __name__=="__main__":


    print(

        "V5.1 马尔可夫模型启动"

    )
