# -*- coding:utf-8 -*-

"""
六合彩 AI V3.5 FINAL

总控制引擎

流程:

main.py

 ↓

engine

 ↓

数据库

 ↓

API同步

 ↓

预测分析

 ↓

生成报告


新增:

🔥 热号
❄ 冷号
📈 趋势
🎯 推荐理由

"""


from datetime import datetime
import json


from config import (
    LOTTERIES,
    OUTPUT_DIR,
    VERSION
)


from .database import (
    init_database,
    load_history
)


from .api_sync import (
    sync_all
)


from .predictor import (
    predict
)


from .quality import (
    analyze_quality
)


from .features import (
    feature_statistics
)



# =====================================================
# 保存JSON
# =====================================================


def save_json(data):

    file = OUTPUT_DIR / "prediction.json"


    file.write_text(

        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"

    )


    print()

    print(
        "JSON输出:",
        file
    )


    return file





# =====================================================
# 生成文字报告
# =====================================================


def make_report(results):


    lines=[]


    lines.append(
        "================================"
    )

    lines.append(
        "六合彩 AI 智能预测报告"
    )

    lines.append(
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    lines.append(
        "================================"
    )



    for key,data in results.items():


        if "error" in data:

            continue



        lines.append("")

        lines.append(
            "🎲 "+data["彩种"]
        )

        lines.append(
            "--------------------------------"
        )



        top=data.get(
            "重点3码",
            []
        )


        ten=data.get(
            "特码10码",
            []
        )



        lines.append(
            f"🎯 推荐3码: {top}"
        )


        lines.append(
            f"⭐ 10码范围: {ten}"
        )



        score=data.get(
            "评分",
            {}
        )



        hot=list(score.keys())[:5]



        lines.append(
            f"🔥 热号: {hot}"
        )



        cold=[]


        for n in range(1,50):

            if str(n) not in score:

                cold.append(n)



        lines.append(
            f"❄ 冷号: {cold[:8]}"
        )



        wave=data.get(
            "波色",
            {}
        )


        lines.append(
            "📈 趋势:"
        )


        if wave:

            lines.append(

                f"波色趋势: "
                f"{wave.get('推荐波色','未知')}"

            )



        reason=[]


        if data.get(
            "历史数量",
            0
        )>=100:

            reason.append(
                "历史数据充足"
            )


        if top:

            reason.append(
                "综合评分最高"
            )


        if wave:

            reason.append(
                "波色模型参与"
            )



        lines.append(
            "🎯 推荐理由:"
        )


        for r in reason:

            lines.append(
                " - "+r
            )


    return "\n".join(lines)




# =====================================================
# 保存报告
# =====================================================


def save_report(text):


    txt=OUTPUT_DIR/"report.txt"


    txt.write_text(
        text,
        encoding="utf-8"
    )


    html=OUTPUT_DIR/"report.html"


    html.write_text(

        f"""
<html>
<head>
<meta charset="utf-8">
<title>六合彩AI预测</title>
</head>

<body>

<pre>

{text}

</pre>

</body>

</html>
""",

        encoding="utf-8"

    )


    print()

    print(
        "文字报告:",
        txt
    )


    print(
        "网页报告:",
        html
    )





# =====================================================
# 单个彩种
# =====================================================


def analyze_lottery(key):


    name=LOTTERIES[key]


    print()

    print(
        "="*60
    )

    print(
        "分析:",
        name
    )

    print(
        "="*60
    )



    history=load_history(
        key
    )



    print(
        "历史数量:",
        len(history)
    )



    quality=analyze_quality(
        history
    )



    if not history:


        return {

            "彩种":name,

            "错误":
            "无数据"

        }



    result=predict(
        history
    )


    result["彩种"]=name


    result["历史数量"]=len(history)


    result["数据质量"]=quality



    result["特征统计"]=feature_statistics(
        history
    )



    return result





# =====================================================
# 主系统
# =====================================================


def run_system():


    print()

    print(
        "="*70
    )


    print(
        "六合彩 AI V3.5 FINAL"
    )


    print(
        datetime.now()
    )


    print(
        "="*70
    )




    # 数据库

    print()

    print(
        "【1】初始化数据库"
    )


    init_database()



    # API

    print()

    print(
        "【2】API同步"
    )


    try:

        sync_result=sync_all()


    except Exception as e:


        sync_result={

            "error":
            str(e)

        }




    # 预测


    print()

    print(
        "【3】智能预测"
    )



    results={}



    for key in LOTTERIES:


        try:

            results[key]=analyze_lottery(
                key
            )


        except Exception as e:


            results[key]={

                "error":
                str(e)

            }




    final={


        "版本":

        VERSION,


        "系统":

        "六合彩 AI V3.5 FINAL",


        "时间":

        datetime.now().isoformat(),


        "同步":

        sync_result,


        "预测":

        results


    }



    save_json(
        final
    )



    report=make_report(
        results
    )



    save_report(
        report
    )



    print()

    print(report)



    print()

    print(
        "="*70
    )


    print(
        "V3.5 FINAL运行完成"
    )


    print(
        "="*70
    )



    return final





__all__=[

    "run_system"

]
