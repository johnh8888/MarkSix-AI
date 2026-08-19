# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

SQLite 数据库模块

职责：
1. 初始化数据库
2. 保存开奖数据
3. 读取历史数据
4. 获取最新一期

整个 V3.0 只允许通过本文件操作 SQLite。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


# =====================================================
# 配置导入
# =====================================================

try:
    from config import DATABASE_FILE, HISTORY_LIMIT
except ImportError:
    from ..config import DATABASE_FILE, HISTORY_LIMIT


# =====================================================
# 数据库路径
# =====================================================

DATABASE_PATH = Path(DATABASE_FILE)

DATABASE_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)


# =====================================================
# 数据库连接
# =====================================================

def get_connection():
    """
    创建 SQLite 连接。
    """

    conn = sqlite3.connect(
        str(DATABASE_PATH),
        timeout=30
    )

    conn.execute(
        "PRAGMA journal_mode=WAL"
    )

    conn.execute(
        "PRAGMA foreign_keys=ON"
    )

    return conn


# =====================================================
# 初始化数据库
# =====================================================

def init_database():
    """
    初始化 draws 表。
    """

    conn = get_connection()

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS draws
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                lottery TEXT NOT NULL,

                issue TEXT NOT NULL,

                numbers TEXT NOT NULL,

                special INTEGER NOT NULL,

                source TEXT DEFAULT 'api',

                create_time TEXT NOT NULL,

                UNIQUE(lottery, issue)
            )
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_draws_lottery
            ON draws(lottery)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_draws_issue
            ON draws(lottery, issue)
            """
        )

        conn.commit()

    finally:

        conn.close()

    print(
        f"数据库初始化完成: {DATABASE_PATH}"
    )


# =====================================================
# 数据验证
# =====================================================

def validate_draw(numbers, special):
    """
    验证开奖数据。

    正常六合彩：
    6个正码 + 1个特码
    """

    try:

        nums = [
            int(x)
            for x in numbers
        ]

        sp = int(special)

    except Exception:

        return False

    if len(nums) != 6:
        return False

    if len(set(nums)) != 6:
        return False

    if any(
        x < 1 or x > 49
        for x in nums
    ):
        return False

    if sp < 1 or sp > 49:
        return False

    if sp in nums:
        return False

    return True


# =====================================================
# 保存开奖
# =====================================================

def save_draw(
    lottery,
    issue,
    numbers,
    special,
    source="api"
):
    """
    保存一期开奖。

    返回：
    True  = 新增
    False = 已存在或数据无效
    """

    if not validate_draw(
        numbers,
        special
    ):
        print(
            "跳过无效开奖:",
            lottery,
            issue,
            numbers,
            special
        )

        return False

    conn = get_connection()

    try:

        cur = conn.execute(
            """
            INSERT OR IGNORE INTO draws
            (
                lottery,
                issue,
                numbers,
                special,
                source,
                create_time
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(lottery),

                str(issue),

                ",".join(
                    str(x)
                    for x in numbers
                ),

                int(special),

                str(source),

                datetime.now().isoformat()
            )
        )

        conn.commit()

        return cur.rowcount > 0

    except Exception as e:

        print(
            "保存开奖失败:",
            e
        )

        return False

    finally:

        conn.close()


# =====================================================
# 获取历史数据
# =====================================================

def load_history(
    lottery,
    limit=None
):
    """
    获取指定彩种历史开奖。

    返回：

    [
        {
            "issue": "...",
            "numbers": [1,2,3,4,5,6],
            "special": 7
        }
    ]
    """

    if limit is None:

        limit = HISTORY_LIMIT

    try:

        limit = int(limit)

    except Exception:

        limit = HISTORY_LIMIT

    limit = max(
        1,
        min(limit, 5000)
    )

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT
                issue,
                numbers,
                special
            FROM draws
            WHERE lottery = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                str(lottery),
                limit
            )
        ).fetchall()

    finally:

        conn.close()

    result = []

    for issue, numbers, special in rows:

        try:

            nums = [
                int(x)
                for x in str(numbers).split(",")
                if str(x).strip()
            ]

            result.append(
                {
                    "issue": str(issue),

                    "numbers": nums,

                    "special": int(special)
                }
            )

        except Exception:

            continue

    # 数据按照旧 → 新排列
    result.reverse()

    return result


# =====================================================
# 获取特码历史
# =====================================================

def load_specials(
    lottery,
    limit=None
):
    """
    直接获取特码序列。
    """

    history = load_history(
        lottery,
        limit
    )

    return [
        int(row["special"])
        for row in history
        if row.get("special") is not None
    ]


# =====================================================
# 最新一期
# =====================================================

def latest_draw(lottery):
    """
    获取最新一期。
    """

    data = load_history(
        lottery,
        1
    )

    if data:

        return data[-1]

    return None


# =====================================================
# 数据统计
# =====================================================

def count_draws(lottery=None):
    """
    获取数据库开奖数量。
    """

    conn = get_connection()

    try:

        if lottery is None:

            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM draws
                """
            ).fetchone()

        else:

            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM draws
                WHERE lottery=?
                """,
                (str(lottery),)
            ).fetchone()

        return int(
            row[0]
        )

    finally:

        conn.close()


# =====================================================
# 导出接口
# =====================================================

__all__ = [
    "get_connection",
    "init_database",
    "validate_draw",
    "save_draw",
    "load_history",
    "load_specials",
    "latest_draw",
    "count_draws"
]
