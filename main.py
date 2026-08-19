# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V3.0 FINAL

唯一入口

流程：

初始化
 ↓
同步数据
 ↓
预测
 ↓
回测
 ↓
输出JSON

"""


from datetime import datetime


from core.engine import run_system





def banner():


    print("=" * 70)


    print(

        "        六合 AI 智能预测系统 V3.0 FINAL"

    )


    print()


    print(

        " API真实数据 + SQLite数据库"

    )


    print(

        " 特征工程 + 马尔可夫 + 贝叶斯融合"

    )


    print(

        " Walk Forward 防过拟合回测"

    )


    print()


    print(datetime.now())


    print("=" * 70)






def main():


    banner()


    result = run_system()



    print()


    print("=" * 70)


    print(

        "系统运行完成"

    )


    print("=" * 70)


    return result






if __name__ == "__main__":


    main()
