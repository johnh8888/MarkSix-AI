# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
V4.0 FINAL

程序入口：

main.py
    ↓
core.engine
    ↓
SQLite
    ↓
API同步
    ↓
统计分析
    ↓
预测候选
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
        print(str(exc))
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
