# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

wave_model.py

波色智能模型


功能:

1. 波色统计
2. 波色概率
3. 连波检测
4. 反转检测
5. 动态推荐


"""


from collections import Counter


from .features import get_wave





# =====================================================
# 波色列表
# =====================================================


WAVES = [

    "红",

    "蓝",

    "绿"

]





# =====================================================
# 号码解析
# =====================================================


def parse_numbers(rows):


    result=[]


    for row in rows:


        nums=row.get(

            "numbers",

            ""

        )


        if isinstance(nums,str):


            nums=nums.replace(

                ",",

                " "

            ).split()



        for n in nums:


            try:

                result.append(

                    int(n)

                )

            except:

                pass



    return result





# =====================================================
# 波色统计
# =====================================================


def wave_frequency(numbers):


    counter=Counter()



    for n in numbers:


        counter[

            get_wave(n)

        ]+=1



    total=sum(

        counter.values()

    )



    if total==0:

        return {

            x:0

            for x in WAVES

        }



    return {


        x:

        round(

            counter[x]/total,

            4

        )

        for x in WAVES

    }





# =====================================================
# 最近趋势
# =====================================================


def recent_wave(numbers,window=20):


    counter=Counter()



    for n in numbers[:window]:


        counter[

            get_wave(n)

        ]+=1



    return counter.most_common()





# =====================================================
# 连续波检测
# =====================================================


def detect_same_wave(numbers):


    if len(numbers)<3:

        return False



    waves=[

        get_wave(n)

        for n in numbers[:3]

    ]



    return len(set(waves))==1





# =====================================================
# 波色反转
# =====================================================


def detect_wave_reverse(numbers):


    if len(numbers)<6:

        return False



    first=[

        get_wave(n)

        for n in numbers[:3]

    ]



    second=[

        get_wave(n)

        for n in numbers[3:6]

    ]



    return (

        len(set(first))==1

        and

        len(set(second))==1

        and

        first[0]!=second[0]

    )





# =====================================================
# 波色冷热
# =====================================================


def wave_hot_cold(numbers):


    freq=wave_frequency(

        numbers

    )


    hot=max(

        freq,

        key=freq.get

    )


    cold=min(

        freq,

        key=freq.get

    )


    return {


        "hot":

        hot,


        "cold":

        cold,


        "probability":

        freq

    }





# =====================================================
# 动态波色评分
# =====================================================


def wave_score(numbers):


    freq=wave_frequency(

        numbers

    )


    score={}



    for w in WAVES:


        score[w]=freq[w]



    # 连续增强

    if detect_same_wave(numbers):


        last=get_wave(

            numbers[0]

        )


        score[last]+=0.15



    # 反转增强

    if detect_wave_reverse(numbers):


        last=get_wave(

            numbers[0]

        )


        score[last]-=0.05



    total=sum(

        max(v,0)

        for v in score.values()

    )



    if total==0:

        return score



    return {


        k:

        round(

            max(v,0)/total,

            4

        )

        for k,v in score.items()

    }





# =====================================================
# 推荐
# =====================================================


def predict_wave(numbers):


    score=wave_score(

        numbers

    )


    ranking=sorted(

        score.items(),

        key=lambda x:x[1],

        reverse=True

    )


    return {


        "单推":

        ranking[0][0],


        "双推":

        [

            x[0]

            for x in ranking[:2]

        ],


        "概率":

        score,


        "连续":

        detect_same_wave(

            numbers

        ),


        "反转":

        detect_wave_reverse(

            numbers

        )

    }





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    data=[

        {

        "numbers":

        "39 41 08 09 07 14 49"

        }

    ]*20



    nums=parse_numbers(

        data

    )


    print(

        predict_wave(nums)

    )
