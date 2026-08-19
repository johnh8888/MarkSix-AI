# -*- coding:utf-8 -*-

"""
六合彩 AI V3.6 FINAL

预测报告模块

输出:

1. TXT文字报告
2. HTML网页报告

显示:

🎯 推荐
🔥 热号
❄ 冷号
📈 趋势
🎯 推荐理由

"""


from datetime import datetime

from config import OUTPUT_DIR





# =====================================================
# 安全读取
# =====================================================


def get(data,key,default=None):


    return data.get(

        key,

        default

    )





# =====================================================
# 单彩种报告
# =====================================================


def lottery_report(

        name,

        data

):


    lines=[]


    lines.append(

        f"🎲 {name}"

    )


    lines.append(

        "-"*40

    )




    # 推荐号码

    lines.append(

        "🎯 推荐3码: "

        +

        str(

            get(

                data,

                "🎯推荐3码",

                []

            )

        )

    )




    lines.append(

        "⭐ 10码范围: "

        +

        str(

            get(

                data,

                "⭐10码范围",

                []

            )

        )

    )




    lines.append("")





    # 热号

    lines.append(

        "🔥 热号: "

        +

        str(

            get(

                data,

                "🔥热号",

                []

            )

        )

    )




    # 冷号

    lines.append(

        "❄ 冷号: "

        +

        str(

            get(

                data,

                "❄冷号",

                []

            )

        )

    )





    lines.append("")




    # 趋势

    lines.append(

        "📈 趋势:"

    )



    trend=get(

        data,

        "📈趋势",

        {}

    )



    if isinstance(

        trend,

        dict

    ):


        for k,v in trend.items():


            lines.append(

                f"  {k}: {v}"

            )


    else:


        lines.append(

            str(trend)

        )





    lines.append("")




    # 理由

    lines.append(

        "🎯 推荐理由:"

    )



    reasons=get(

        data,

        "🎯推荐理由",

        []

    )



    for r in reasons:


        if isinstance(r,dict):


            lines.append(

                f"  {r.get('号码')} : "

                +

                " / ".join(

                    r.get(

                        "理由",

                        []

                    )

                )

            )


        else:


            lines.append(

                str(r)

            )





    lines.append("")



    return "\n".join(lines)








# =====================================================
# 总报告
# =====================================================


def build_report(

        result

):


    lines=[]



    lines.append(

        "="*40

    )


    lines.append(

        "六合彩 AI V3.6 FINAL"

    )


    lines.append(

        str(

            datetime.now()

        )

    )


    lines.append(

        "="*40

    )


    lines.append("")





    predictions=result.get(

        "预测",

        {}

    )



    for key,data in predictions.items():


        if "error" in data:

            continue



        name=data.get(

            "彩种",

            key

        )



        lines.append(

            lottery_report(

                name,

                data

            )

        )



        lines.append(

            "="*40

        )





    return "\n".join(lines)








# =====================================================
# 保存TXT
# =====================================================


def save_txt(

        result

):


    text=build_report(

        result

    )


    file=OUTPUT_DIR / "report.txt"


    file.write_text(

        text,

        encoding="utf-8"

    )


    print(

        "文字报告:",

        file

    )


    return file








# =====================================================
# 保存HTML
# =====================================================


def save_html(

        result

):


    text=build_report(

        result

    )



    html=f"""

<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<title>六合彩AI预测</title>


<style>

body{{

font-family:
Arial,
"Microsoft YaHei";

background:#f5f5f5;

padding:20px;

}}


.box{{

background:white;

padding:20px;

border-radius:10px;

white-space:pre-line;

font-size:18px;

}}

</style>


</head>


<body>


<div class="box">

{text}

</div>


</body>


</html>

"""



    file=OUTPUT_DIR / "report.html"



    file.write_text(

        html,

        encoding="utf-8"

    )



    print(

        "网页报告:",

        file

    )


    return file







# =====================================================
# 一键输出
# =====================================================


def generate_reports(

        result

):


    save_txt(

        result

    )


    save_html(

        result

    )



__all__=[

    "generate_reports",

    "save_txt",

    "save_html"

]
