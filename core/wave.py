# -*- coding:utf-8 -*-

"""
六合彩 AI V3.3 FINAL

波色智能分析模块


功能:

1. 红蓝绿判断
2. 历史波色统计
3. 最近趋势
4. 连续波检测
5. 波色转移
6. 反转分析
7. 综合波色预测

"""


from collections import Counter, defaultdict





# =====================================================
# 波色表
# =====================================================


RED = {

    1,2,7,8,
    12,13,18,19,
    23,24,29,30,
    34,35,40,45,46

}



BLUE = {

    3,4,9,10,
    14,15,20,25,
    26,31,36,37,
    41,42,47,48

}



GREEN = {

    5,6,11,16,
    17,21,22,27,
    28,32,33,38,
    39,43,44,49

}







# =====================================================
# 单号码波色
# =====================================================


def get_wave(number):


    if number in RED:

        return "红"


    if number in BLUE:

        return "蓝"


    if number in GREEN:

        return "绿"


    return "未知"







# =====================================================
# 历史波色
# =====================================================


def history_wave(history):


    result=[]



    for row in history:


        number=row.get(

            "special"

        )


        if number:


            result.append(

                get_wave(number)

            )



    return result







# =====================================================
# 波色统计
# =====================================================


def wave_statistics(history):


    waves=history_wave(history)



    if not waves:

        return {}



    counter=Counter(waves)



    total=len(waves)



    return {


        "红":{

            "数量":

                counter["红"],


            "比例":

                round(

                    counter["红"]/total,

                    3

                )

        },



        "蓝":{

            "数量":

                counter["蓝"],


            "比例":

                round(

                    counter["蓝"]/total,

                    3

                )

        },



        "绿":{

            "数量":

                counter["绿"],


            "比例":

                round(

                    counter["绿"]/total,

                    3

                )

        }

    }







# =====================================================
# 连续波检测
# =====================================================


def detect_streak(history):


    waves=history_wave(history)



    if not waves:


        return {

            "连续次数":0

        }



    last=waves[-1]



    count=1



    for x in reversed(waves[:-1]):


        if x==last:

            count+=1

        else:

            break




    return {


        "当前波":

            last,


        "连续次数":

            count

    }







# =====================================================
# 最近趋势
# =====================================================


def recent_trend(history):


    waves=history_wave(history)



    if not waves:


        return {}




    result={}



    for name,size in [

        ("最近10期",10),

        ("最近50期",50)

    ]:


        data=waves[-size:]



        counter=Counter(data)



        total=len(data)



        result[name]={



            "红":

            round(

                counter["红"]/total,

                3

            ),



            "蓝":

            round(

                counter["蓝"]/total,

                3

            ),



            "绿":

            round(

                counter["绿"]/total,

                3

            )

        }



    return result







# =====================================================
# 波色转移
# =====================================================


def wave_transition(history):


    waves=history_wave(history)



    if len(waves)<2:


        return {}




    matrix=defaultdict(
        Counter
    )



    for a,b in zip(

        waves[:-1],

        waves[1:]

    ):


        matrix[a][b]+=1




    result={}



    for k,v in matrix.items():


        total=sum(v.values())


        result[k]={



            x:

            round(

                y/total,

                3

            )

            for x,y in v.items()

        }



    return result







# =====================================================
# 反转检测
# =====================================================


def detect_reverse(history):


    streak=detect_streak(history)



    if streak.get(

        "连续次数",

        0

    )>=3:


        return {


            "状态":

                "可能反转",


            "当前":

                streak.get(

                    "当前波"

                )

        }




    return {


        "状态":

            "正常"

    }








# =====================================================
# 综合预测
# =====================================================


def predict_wave(history):


    stats=wave_statistics(history)



    if not stats:


        return {


            "状态":

                "数据不足"

        }






    recent=recent_trend(history)



    transition=wave_transition(history)



    streak=detect_streak(history)



    reverse=detect_reverse(history)





    score={

        "红":0,

        "蓝":0,

        "绿":0

    }




    # 历史权重 30%

    for k,v in stats.items():

        score[k]+=v["比例"]*30






    # 最近50权重 40%

    if "最近50期" in recent:


        for k,v in recent["最近50期"].items():

            score[k]+=v*40






    # 最近10权重 30%

    if "最近10期" in recent:


        for k,v in recent["最近10期"].items():

            score[k]+=v*30







    ranking=sorted(

        score.items(),

        key=lambda x:x[1],

        reverse=True

    )





    probability={}


    total=sum(score.values())



    for k,v in score.items():


        probability[k]=round(

            v/total,

            3

        )





    return {


        "推荐波色":

            ranking[0][0],



        "概率":

            probability[

                ranking[0][0]

            ],



        "综合概率":

            probability,



        "历史统计":

            stats,



        "近期趋势":

            recent,



        "连续状态":

            streak,



        "转移":

            transition,



        "反转检测":

            reverse

    }







__all__=[

    "get_wave",

    "predict_wave",

    "wave_statistics",

    "history_wave"

]
