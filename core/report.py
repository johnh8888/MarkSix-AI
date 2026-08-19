# -*- coding:utf-8 -*-


"""
六合AI V4.0

用户报告生成
"""


from pathlib import Path


from config import OUTPUT_DIR




def create_report(data):


    lines=[]


    lines.append(
        "="*60
    )

    lines.append(
        "        六合AI V4.0 FINAL"
    )

    lines.append(
        "="*60
    )



    for key,item in data["预测"].items():


        lines.append("")

        lines.append(
            "【"+item["彩种"]+"】"
        )


        lines.append(
            ""
        )


        lines.append(
            "★★★★★ 第一推荐:"
            +
            str(
                item["第一推荐"]
            )
        )


        lines.append(
            "三星推荐:"
            +
            " "
            +
            " ".join(
                map(
                    str,
                    item["重点3码"]
                )
            )
        )


        lines.append(
            "十码精选:"
        )


        lines.append(
            " ".join(
                map(
                    str,
                    item["特码10码"]
                )
            )
        )


        lines.append("")


        wave=item["波色"]

        lines.append(
            "波色:"
            +
            wave["推荐波色"]
        )


        lines.append(
            "概率:"
            +
            str(
                wave["概率"]
            )
        )



        lines.append(
            "大小:"
            +
            item["大小"]["推荐"]
        )


        lines.append(
            "单双:"
            +
            item["单双"]["推荐"]
        )


        lines.append(
            "AI信心:"
            +
            str(
                item["置信度"]
            )
        )


        lines.append(
            "风险:"
            +
            item["风险等级"]
        )


        lines.append(
            "-"*50
        )



    file=OUTPUT_DIR/"report.txt"


    file.write_text(

        "\n".join(lines),

        encoding="utf-8"

    )


    return file
