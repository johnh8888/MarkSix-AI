# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V6.0

程序入口
"""

from __future__ import annotations

import sys

from core.engine import run_system


def main() -> None:
    try:
        result = run_system()

        if not isinstance(result, dict):
            print("系统返回结果异常")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n用户中断程序")
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
