# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/backtest.py

Walk Forward 回测模块


原则：

预测第N期

只能使用：

第N期之前的数据


禁止未来数据泄漏


"""


from __future__ import annotations


from typing import List, Dict, Any




# =====================================================
# 基础指标
# =====================================================


def empty_metric():

    return {

        "total":0,

        "hit":0,

        "rate":0

    }





def add_result(
        metric,
        hit
):


    metric["total"]+=1


    if hit:

        metric["hit"]+=1



    metric["rate"]=round(

        metric["hit"]

        /

        metric["total"],

        4

    )







# =====================================================
# 回测预测接口
# =====================================================


def simple_predict(history):


    """
    调用预测模块

    防止循环导入

    """


    try:


        from .predictor import predict_next


        result=predict_next(
            history
        )


        return result



    except Exception:


        return {}








# =====================================================
# 提取号码
# =====================================================


def get_top10(pred):


    try:

        return pred.get(
            "特码10码",
            []
        )


    except:

        return []








# =====================================================
# Walk Forward
# =====================================================


def walk_forward(

        history:List[int],

        test_size:int=20

)->Dict[str,Any]:


    result={


        "测试期数":

        test_size,


        "有效测试":

        0,


        "特码10码":

        empty_metric(),



        "大小":

        empty_metric(),



        "单双":

        empty_metric(),



        "波色":

        empty_metric()

    }





    if len(history)<30:


        result["错误"]=(
            "历史数据不足"
        )


        return result





    # history:

    # 新 -> 旧


    max_test=min(

        test_size,

        len(history)-20

    )






    for i in range(max_test):



        # 当前目标期

        actual=history[i]



        # 只使用更旧数据

        train=history[i+1:]



        if len(train)<20:

            continue




        prediction=simple_predict(
            train
        )



        if not prediction:

            continue



        result["有效测试"]+=1




        # -----------------------
        # 特码10码
        # -----------------------


        top10=get_top10(
            prediction
        )


        add_result(

            result["特码10码"],

            actual in top10

        )





        # -----------------------
        # 大小
        # -----------------------


        size=prediction.get(
            "大小"
        )


        if size:


            hit=(

                size

                ==

                ("大" if actual>=25 else "小")

            )


            add_result(

                result["大小"],

                hit

            )





        # -----------------------
        # 单双
        # -----------------------


        parity=prediction.get(
            "单双"
        )


        if parity:


            hit=(

                parity

                ==

                ("单" if actual%2 else "双")

            )


            add_result(

                result["单双"],

                hit

            )






        # -----------------------
        # 波色
        # -----------------------


        wave=prediction.get(
            "波色",
            {}
        )


        if isinstance(wave,dict):


            single=wave.get(
                "single"
            )


            try:


                from .wave_model import get_wave


                hit=(

                    get_wave(actual)

                    ==

                    single

                )


                add_result(

                    result["波色"],

                    hit

                )


            except:

                pass







    return result







__all__=[

    "walk_forward"

]
