# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.1

main.py

系统启动入口

"""


import sys

import traceback

from datetime import datetime



sys.path.append(".")





# =====================================================
# 导入核心引擎
# =====================================================


try:

    from core.engine import run


except Exception as e:


    print()

    print(
        "核心模块加载失败"
    )


    print(e)


    traceback.print_exc()


    sys.exit(1)






# =====================================================
# 欢迎界面
# =====================================================


def 显示标题():


    print()


    print("="*70)


    print(
        "          六合 AI 智能预测系统 V5.1"
    )


    print()


    print(
        "  API真实数据 + SQLite数据库"
    )


    print()


    print(
        "  HMM状态识别 + 马尔可夫链"
    )


    print()


    print(
        "  贝叶斯融合 + 在线学习"
    )


    print()


    print(
        "  防过拟合 Walk-Forward 回测"
    )


    print()


    print(
        datetime.now()
    )


    print("="*70)






# =====================================================
# 主程序
# =====================================================


def main():


    try:


        显示标题()



        print()


        print(
            "启动V5.1智能分析系统..."
        )



        结果=run()



        print()


        print("="*70)


        print(
            "系统运行完成"
        )


        print("="*70)



        return 结果





    except Exception as e:


        print()


        print(
            "系统运行异常"
        )


        print(e)


        traceback.print_exc()


        return None






# =====================================================
# 程序入口
# =====================================================


if __name__=="__main__":


    main()
