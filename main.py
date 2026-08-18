# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

main.py

系统入口


运行:

python main.py


流程:

初始化
 ↓
数据同步
 ↓
状态分析
 ↓
动态策略
 ↓
预测
 ↓
Walk Forward
 ↓
保存结果


"""


import sys

import traceback


from core.main_engine import run





def banner():


    print("="*70)

    print(

        """

        ███╗   ███╗ █████╗ ██████╗ 
        ████╗ ████║██╔══██╗██╔══██╗
        ██╔████╔██║███████║██████╔╝
        ██║╚██╔╝██║██╔══██║██╔══██╗
        ██║ ╚═╝ ██║██║  ██║██║  ██║
        ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝


        MarkSix AI V4.0

        """

    )


    print("="*70)





def main():


    banner()



    try:


        result=run()



        print()


        print("="*70)

        print(

            "系统执行成功"

        )

        print(

            "生成彩种:",

            len(result)

        )

        print("="*70)



    except Exception:


        print()


        print("="*70)

        print(

            "系统运行异常"

        )

        print("="*70)



        traceback.print_exc()



        sys.exit(1)





if __name__=="__main__":


    main()
