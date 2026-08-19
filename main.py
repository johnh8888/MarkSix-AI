# -*- coding:utf-8 -*-

"""
六合AI V4.0 FINAL

程序入口


流程:

main.py

↓

core.engine

↓

数据库

↓

API同步

↓

AI预测

↓

报告输出


"""


from __future__ import annotations


import sys



from core.engine import run_system





def main():


    try:


        run_system()



    except Exception as e:


        print()

        print("="*70)

        print(

            "系统运行异常"

        )

        print(

            e

        )

        print("="*70)


        sys.exit(1)






if __name__=="__main__":


    main()
