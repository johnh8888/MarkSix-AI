# -*- coding:utf-8 -*-

"""
六合彩 AI V3.4 FINAL

报告输出模块

功能:

1. 简洁文字报告
2. HTML报告
3. 人类可读格式

"""


from datetime import datetime

from config import OUTPUT_DIR



# =====================================================
# 风险显示
# =====================================================


def risk_text(value):

    if value >= 0.7:
        return "低风险"

    elif value >= 0.4:
        return "中风险"

    else:
        return "高风险"





# =====================================================
# 波色格式
# =====================================================


def wave_icon(wave):

    if wave=="红":
        return "🔴 红波"

    if wave=="蓝":
        return "🔵 蓝波"

    if wave=="绿":
        return "🟢 绿波"

    return wave





# =====================================================
# 单个彩种报告
# =====================================================


def lottery_report(name,data):


    lines=[]


    lines.append("")
    lines.append("="*55)

    lines.append(
        f"【{name}】"
    )

    lines.append("="*55)



    if "error" in data:

        lines.append(
            "错误:"
            +
            str(data["error"])
        )

        return lines




    lines.append(
        f"历史数据: {data.get('历史数量',0)}期"
    )


    lines.append("")



    lines.append(
        "🎯 特码推荐"
    )


    lines.append(
        "第一推荐: "
        +
        str(
            data.get(
                "第一推荐",
                "-"
            )
        )
        +
        "号"
    )



    lines.append(
        "精选3码: "
        +
        " ".join(
            map(
                str,
                data.get(
                    "重点3码",
                    []
                )
            )
        )
    )



    lines.append(
        "10码候选: "
        +
        " ".join(
            map(
                str,
                data.get(
                    "特码10码",
                    []
                )
            )
        )
    )




    lines.append("")

    lines.append(
        "🎨 波色预测"
    )


    wave=data.get(
        "波色",
        {}
    )


    lines.append(
        "推荐: "
        +
        wave_icon(
            wave.get(
                "推荐波色",
                ""
            )
        )
    )


    lines.append(
        "概率: "
        +
        str(
            round(
                wave.get(
                    "概率",
                    0
                )*100,
                1
            )
        )
        +
        "%"
    )





    lines.append("")



    size=data.get(
        "大小",
        {}
    )


    lines.append(
        "大小: "
        +
        str(
            size.get(
                "推荐",
                "-"
            )
        )
    )



    lines.append(
        "大小概率: "
        +
        str(
            round(
                size.get(
                    "大概率",
                    0
                )*100
            )
        )
        +
        "% / "
        +
        str(
            round(
                size.get(
                    "小概率",
                    0
                )*100
            )
        )
        +
        "%"
    )




    odd=data.get(
        "单双",
        {}
    )


    lines.append(
        "单双: "
        +
        str(
            odd.get(
                "推荐",
                "-"
            )
        )
    )



    lines.append(
        "单双概率: "
        +
        str(
            round(
                odd.get(
                    "单概率",
                    0
                )*100
            )
        )
        +
        "% / "
        +
        str(
            round(
                odd.get(
                    "双概率",
                    0
                )*100
            )
        )
        +
        "%"
    )





    confidence=data.get(
        "置信度",
        0
    )



    lines.append("")

    lines.append(
        "AI置信度: "
        +
        str(
            round(
                confidence*100,
                1
            )
        )
        +
        "%"
    )


    lines.append(
        "风险:"
        +
        data.get(
            "风险等级",
            risk_text(
                confidence
            )
        )
    )


    return lines







# =====================================================
# TXT报告
# =====================================================


def create_txt_report(result):


    lines=[]


    lines.append(
        "六合彩 AI V3.4 FINAL"
    )


    lines.append(
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )



    for key,data in result.items():

        name=data.get(
            "彩种",
            key
        )

        lines.extend(
            lottery_report(
                name,
                data
            )
        )



    text="\n".join(
        lines
    )



    file=OUTPUT_DIR / "report.txt"


    file.write_text(
        text,
        encoding="utf-8"
    )



    return file







# =====================================================
# HTML报告
# =====================================================


def create_html_report(result):


    txt=[]


    txt.append(
        """
<html>
<head>

<meta charset="utf-8">

<title>六合彩AI预测</title>

<style>

body{

font-family:
Microsoft YaHei;

background:#f5f5f5;

padding:30px;

}


.card{

background:white;

padding:20px;

margin-bottom:20px;

border-radius:10px;

box-shadow:
0 2px 8px #ccc;

}


.title{

font-size:26px;

font-weight:bold;

}


</style>


</head>


<body>

<div class="title">

六合彩 AI V3.4 FINAL

</div>

"""
    )



    for key,data in result.items():


        name=data.get(
            "彩种",
            key
        )


        txt.append(
            "<div class='card'>"
        )


        txt.append(
            "<h2>"
            +
            name
            +
            "</h2>"
        )


        txt.append(
            "<pre>"
        )


        txt.append(
            "\n".join(
                lottery_report(
                    name,
                    data
                )
            )
        )


        txt.append(
            "</pre>"
        )


        txt.append(
            "</div>"
        )



    txt.append(
        "</body></html>"
    )



    file=OUTPUT_DIR / "report.html"



    file.write_text(
        "\n".join(txt),
        encoding="utf-8"
    )


    return file



__all__=[

    "create_txt_report",

    "create_html_report"

]
