# -*- coding: utf-8 -*-

"""
六合AI V10.0 FINAL

启动入口
"""

import os
import sys
import json


# UTF-8输出

os.environ["PYTHONIOENCODING"]="utf-8"



from core.engine import run




def show_result():


    path="output/prediction.json"



    if not os.path.exists(path):

        print(
            "没有找到预测文件"
        )

        return



    with open(

        path,

        "r",

        encoding="utf-8"

    ) as f:

        data=json.load(f)



    print()

    print("="*50)

    print(
        "       六合AI最终预测 V10.0 FINAL"
    )

    print("="*50)


    print(
        "时间:",
        data.get("time")
    )



    for key,item in data.get(
        "lotteries",
        {}
    ).items():


        print()

        print(
            "="*50
        )


        print(
            item.get(
                "彩种",
                key
            )
        )


        print(
            "="*50
        )



        if "error" in item:


            print(
                "错误:",
                item["error"]
            )

            continue



        p=item.get(
            "预测",
            {}
        )


        state=p.get(
            "市场状态",
            {}
        )



        print(

            "市场状态:",

            state.get(
                "状态",
                "未知"
            )

        )



        print(

            "特码10码:",

            p.get(
                "特码10码",
                []
            )

        )



        print(

            "重点3码:",

            p.get(
                "重点3码",
                []
            )

        )



        print(

            "第一推荐:",

            p.get(
                "第一推荐"
            )

        )



        print(

            "生肖5肖:",

            p.get(
                "生肖5肖",
                []
            )

        )



        attr=p.get(
            "属性",
            {}
        )


        print(
            "波色:",
            attr.get(
                "波色",
                ""
            )
        )


        print(
            "大小:",
            attr.get(
                "大小",
                ""
            )
        )


        print(
            "单双:",
            attr.get(
                "单双",
                ""
            )
        )



        print(

            "评分:",

            p.get(
                "评分",
                {}
            )

        )




if __name__=="__main__":


    try:


        run()


        show_result()



    except Exception as e:


        print(
            "系统错误:",
            e
        )


        sys.exit(1)
