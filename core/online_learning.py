# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.1

online_learning.py

在线学习模块


功能:

1. 预测反馈
2. 模型奖励
3. 模型惩罚
4. 动态权重
5. 时间衰减


"""


import math

from datetime import datetime





# =====================================================
# 初始化在线学习
# =====================================================


def 初始化学习器():

    return {


        "models":{},


        "history":[]


    }





# =====================================================
# 注册模型
# =====================================================


def 注册模型(

        learner,

        模型

):


    if 模型 not in learner["models"]:


        learner["models"][模型]={


            "success":0,


            "fail":0,


            "total":0,


            "weight":1.0,


            "last_update":

            str(datetime.now())

        }


    return learner





# =====================================================
# 记录结果
# =====================================================


def 更新模型(

        learner,

        模型,

        命中

):


    注册模型(

        learner,

        模型

    )



    data=learner["models"][模型]



    data["total"]+=1



    if 命中:


        data["success"]+=1



    else:


        data["fail"]+=1





    # 基础成功率


    rate=(

        data["success"]

        /

        data["total"]

    )





    # 动态权重


    data["weight"]=round(

        0.5

        +

        rate,

        4

    )



    data["last_update"]=str(

        datetime.now()

    )



    return learner





# =====================================================
# 批量更新
# =====================================================


def 批量反馈(

        learner,

        结果

):


    """


    结果格式:

    {

      "frequency":True,

      "trend":False

    }


    """



    for 模型,命中 in 结果.items():


        更新模型(

            learner,

            模型,

            命中

        )



    return learner





# =====================================================
# 时间衰减
# =====================================================


def 时间衰减权重(

        原权重,

        天数

):


    decay=math.exp(

        -0.03*天数

    )


    return round(

        原权重*decay,

        4

    )





# =====================================================
# 获取模型权重
# =====================================================


def 获取权重(

        learner

):


    result={}



    for 模型,data in learner["models"].items():


        result[模型]=data.get(

            "weight",

            1

        )



    total=sum(

        result.values()

    )



    if total==0:


        return result





    return {


        k:

        round(

            v/total,

            4

        )


        for k,v in result.items()

    }





# =====================================================
# 自动淘汰低效模型
# =====================================================


def 模型筛选(

        learner,

        最低次数=30,

        最低成功率=0.25

):


    保留=[]



    for 模型,data in learner["models"].items():


        if data["total"]<最低次数:


            保留.append(

                模型

            )


            continue





        rate=(

            data["success"]

            /

            data["total"]

        )



        if rate>=最低成功率:


            保留.append(

                模型

            )



    return 保留





# =====================================================
# 学习报告
# =====================================================


def 学习报告(

        learner

):


    report={}



    for 模型,data in learner["models"].items():


        total=data["total"]



        rate=0



        if total:


            rate=round(

                data["success"]

                /

                total,

                4

            )



        report[模型]={


            "次数":

            total,


            "成功率":

            rate,


            "权重":

            data["weight"]

        }



    return report





# =====================================================
# V5在线更新入口
# =====================================================


def 在线学习更新(

        learner,

        模型结果

):


    learner=批量反馈(

        learner,

        模型结果

    )


    return {


        "学习器":

        learner,


        "权重":

        获取权重(

            learner

        ),


        "报告":

        学习报告(

            learner

        )

    }





if __name__=="__main__":


    print(

        "V5.1 在线学习模块启动"

    )
