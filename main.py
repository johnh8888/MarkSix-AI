# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
V5.0 REAL DATA FINAL

入口：

main.py
    ↓
core.engine
    ↓
API
    ↓
SQLite
    ↓
历史统计
    ↓
预测
    ↓
JSON报告

本文件只负责启动系统。
"""

from __future__ import annotations

import sys


def main() -> int:

    try:

        from core.engine import run_system

        result = run_system()

        if not isinstance(result, dict):
            print("系统返回结果异常")
            return 1

        if result.get("fatal_error"):

            print("")
            print("=" * 70)
            print("系统运行失败")
            print("=" * 70)
            print(result.get("fatal_error"))
            print("=" * 70)

            return 1

        return 0

    except KeyboardInterrupt:

        print("")
        print("用户中断程序")
        return 130

    except Exception as exc:

        print("")
        print("=" * 70)
        print("系统运行异常")
        print("=" * 70)
        print(str(exc))
        print("=" * 70)

        return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )
