# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

state_engine.py

动态状态权重引擎


输入:
历史开奖


输出:

市场状态

+
模型动态权重


"""


from collections import Counter


from .features import (

    get_special,

    get_wave,

)





# =====================================================
# 状态定义
# =====================================================


STATE_HOT = "热态"

STATE_COLD = "冷态"

STATE_BALANCE = "平衡"

STATE_REVERSE = "反转"

STATE_CHAOS = "混沌"





# =====================================================
# 默认权重
# =====================================================


BASE_WEIGHTS = {


    "frequency":
        0.20,


    "trend":
        0.15,


    "momentum":
        0.10,


    "omission":
        0.10,


    "adjacency":
        0.08,


    "tail":
        0.07,


    "zone":
        0.05,


    "size":
        0.10,


    "parity":
        0.05,


    "wave":
        0.10,


}





# =====================================================
# 归一化
# =====================================================


def normalize(weights):


    total=sum(
        weights.values()
    )


    if total<=0:

        return BASE_WEIGHTS.copy()



    return {


        k:

        round(
            v/total,
            4
        )


        for k,v in weights.items()

    }





# =====================================================
# 热冷检测
# =====================================================


def detect_hot_cold(rows):


    recent=[]


    for row in rows[:20]:


        n=get_special(row)


        if n:

            recent.append(n)



    if not recent:

        return STATE_BALANCE



    counter=Counter(
        recent
    )



    max_count=max(
        counter.values()
    )



    # 高频集中

    if max_count>=4:

        return STATE_HOT



    # 最近号码重复少

    if len(set(recent))>=18:

        return STATE_COLD



    return STATE_BALANCE





# =====================================================
# 波色状态
# =====================================================


def detect_wave_state(rows):


    waves=[]


    for row in rows[:20]:


        n=get_special(row)


        if n:

            waves.append(
                get_wave(n)
            )



    if len(waves)<5:

        return STATE_BALANCE



    count=Counter(
        waves
    )


    value=max(
        count.values()
    )



    if value>=12:

        return STATE_HOT



    if value<=5:

        return STATE_COLD



    return STATE_BALANCE





# =====================================================
# 连续反转检测
# =====================================================


def detect_reverse(rows):


    nums=[]


    for row in rows[:10]:


        n=get_special(row)


        if n:

            nums.append(n)



    if len(nums)<5:

        return False



    big_small=[]


    for n in nums:


        if n>=25:

            big_small.append(1)

        else:

            big_small.append(0)



    # 大小连续切换

    changes=0


    for i in range(
        len(big_small)-1
    ):


        if big_small[i]!=big_small[i+1]:

            changes+=1



    return changes>=7





# =====================================================
# 市场状态分析
# =====================================================


def analyze_state(rows):


    hot=detect_hot_cold(rows)


    wave=detect_wave_state(rows)


    reverse=detect_reverse(rows)



    if reverse:


        state=STATE_REVERSE



    elif hot==STATE_HOT:


        state=STATE_HOT



    elif hot==STATE_COLD:


        state=STATE_COLD



    else:


        state=STATE_BALANCE




    return {


        "state":

        state,


        "hot_state":

        hot,


        "wave_state":

        wave,


        "reverse":

        reverse,


    }





# =====================================================
# 状态调整权重
# =====================================================


def adjust_weights(rows):


    info=analyze_state(
        rows
    )


    state=info["state"]



    weights=BASE_WEIGHTS.copy()



    # ====================
    # 热态
    # ====================

    if state==STATE_HOT:


        weights["trend"]*=1.5

        weights["momentum"]*=1.5

        weights["frequency"]*=1.2


        weights["omission"]*=0.7




    # ====================
    # 冷态
    # ====================

    elif state==STATE_COLD:


        weights["omission"]*=1.8

        weights["frequency"]*=0.8


        weights["trend"]*=0.8





    # ====================
    # 反转
    # ====================

    elif state==STATE_REVERSE:


        weights["wave"]*=1.8

        weights["parity"]*=1.4

        weights["size"]*=1.3


        weights["momentum"]*=0.6





    # ====================
    # 平衡
    # ====================

    else:


        weights["frequency"]*=1.1

        weights["trend"]*=1.1





    return {


        "state":

        info,


        "weights":

        normalize(weights)

    }





# =====================================================
# 外部调用
# =====================================================


def get_weights(rows):


    return adjust_weights(
        rows
    )["weights"]





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    test=[


        {
        "numbers":
        "38,26,08,06,29,18,23"
        },


        {
        "numbers":
        "33,27,16,28,04,25,14"
        }

    ]



    result=adjust_weights(
        test
    )


    print(result)
