# -*- coding: utf-8 -*-

"""
六合彩综合预测系统

程序入口

流程：

main.py
    ↓
core.engine
    ↓
core.api_sync
    ↓
SQLite
    ↓
统计分析
    ↓
Walk-Forward
    ↓
JSON输出
"""

from __future__ import annotations

import sys

from core.engine import run_system


def main() -> None:

    try:

        run_system()

    except KeyboardInterrupt:

        print()
        print("=" * 70)
        print("用户中断程序")
        print("=" * 70)

        sys.exit(130)

    except Exception as exc:

        print()
        print("=" * 70)
        print("系统运行异常")
        print("=" * 70)

        print(
            f"{type(exc).__name__}: {exc}"
        )

        print("=" * 70)

        sys.exit(1)


if __name__ == "__main__":
    main()
