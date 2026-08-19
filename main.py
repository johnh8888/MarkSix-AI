# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
程序入口

V6.0 REAL DATA FINAL
"""

from __future__ import annotations

import sys

from core.engine import run_system


def main():

    try:

        result = run_system()

        if not isinstance(
            result,
            dict,
        ):

            print(
                "❌ 系统返回结果异常"
            )

            sys.exit(1)

        lotteries = result.get(
            "lotteries"
        )

        if not isinstance(
            lotteries,
            dict,
        ):

            print(
                "❌ prediction结果缺少lotteries"
            )

            sys.exit(1)

        required = [
            "新澳门彩",
            "老澳门彩",
            "香港彩",
        ]

        for lottery in required:

            if lottery not in lotteries:

                print(
                    f"❌ 缺少彩种：{lottery}"
                )

                sys.exit(1)

        print("")
        print("=" * 70)
        print("主程序执行成功")
        print("=" * 70)

    except Exception as exc:

        print("")
        print("=" * 70)
        print("系统运行异常")
        print("=" * 70)
        print(str(exc))
        print("=" * 70)

        sys.exit(1)


if __name__ == "__main__":
    main()
