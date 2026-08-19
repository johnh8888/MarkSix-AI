# -*- coding:utf-8 -*-

"""
六合彩 AI V3.4 QUANT FINAL

预测报告输出模块

功能:

1. 简化AI输出
2. GitHub Actions显示
3. 人类易读格式
"""


from datetime import datetime



# =====================================================
# 风险判断
# =====================================================


def risk_level(confidence):

    if confidence >= 0.8:

        return "低风险"

    elif confidence >= 0.6:

        return "中风险"

    elif confidence >= 0.4:

        return "较高风险"

    else:

        return "高风险"



# =====================================================
# AI等级
# =====================================================


def ai_level(score):


    if score >= 80:

        return "A级 强趋势"


    elif score >= 60:

        return "B级 可参考"


    elif score >= 40:

        return "C级 观察"


    else:

        return "D级 数据不足"



# =====================================================
# 百分比
# =====================================================


def percent(value):

    try:

        return round(value*100,1)

    except:

        return 0



# =====================================================
# 单个彩种报告
# =====================================================


def print_lottery_report(name,data):


    print()

    print("="*60)

    print("【"+name+"】")

    print("="*60)



    if "error" in data:

        print(
            "错误:",
            data["error"]
        )

        return



    first=data.get(
        "第一推荐",
        "-"
    )


    top3=data.get(
        "重点3码",
        []
    )


    top10=data.get(
        "特码10码",
        []
    )


    wave=data.get(
        "波色",
        {}
    )


    size=data.get(
        "大小",
        {}
    )


    odd=data.get(
        "单双",
        {}
    )


    confidence=data.get(
        "置信度",
        0
    )



    score=int(
        confidence*100
    )



    print()

    print(
        "历史数据:",
        data.get(
            "历史数量",
            0
        ),
        "期"
    )


    print()

    print(
        "🥇 第一推荐:",
        first,
        "号"
    )


    print()

    print(
        "⭐ 重点3码:",
        top3
    )


    print()

    print(
        "🎯 十码精选:"
    )

    print(
        top10
    )


    print()


    if wave:

        print(
            "颜色:",
            wave.get(
                "推荐波色",
                "-"
            ),
            "波"
        )


        print(
            "颜色概率:",
            percent(
                wave.get(
                    "概率",
                    0
                )
            ),
            "%"
        )



    if size:

        print(
            "大小:",
            size.get(
                "推荐",
                "-"
            )
        )



    if odd:

        print(
            "单双:",
            odd.get(
                "推荐",
                "-"
            )
        )


    print()


    print(
        "AI评分:",
        score,
        "分"
    )


    print(
        "等级:",
        ai_level(score)
    )


    print(
        "风险:",
        risk_level(
            confidence
        )
    )



# =====================================================
# 总报告
# =====================================================


def print_final_report(results):


    print()

    print("="*70)

    print(
        "             六合AI V3.4 QUANT FINAL"
    )

    print(
        datetime.now()
    )

    print("="*70)



    for key,data in results.items():


        name=data.get(
            "彩种",
            key
        )


        print_lottery_report(
            name,
            data
        )



    print()

    print("="*70)

    print(
        "最终推荐汇总"
    )

    print("="*70)



    for key,data in results.items():


        print(

            data.get(
                "彩种",
                key
            ),
            ":",

            data.get(
                "第一推荐",
                "-"
            )

        )


    print()

    print("="*70)

    print(
        "报告生成完成"
    )

    print("="*70)



__all__=[

    "print_final_report"

]
