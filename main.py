# -*- coding:utf-8 -*-

"""
六合彩 AI V3.1 FINAL

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

预测

↓

输出JSON

"""


from __future__ import annotations


import sys



from core.engine import run_system





def main():


    try:


        run_system()



    except Exception as e:


        print()

        print(
            "="*70
        )

        print(
            "系统运行异常"
        )

        print(
            e
        )

        print(
            "="*70
        )


        sys.exit(1)





if __name__ == "__main__":


    main()
