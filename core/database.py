# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

from .config import DB_FILE


# =========================================================
# 数据库连接
# =========================================================

def get_connection():

    conn = sqlite3.connect(
        DB_FILE
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# 初始化
# =========================================================

def init_database():

    conn = get_connection()

    cursor = conn.cursor()


    # -----------------------------------------------------
    # 开奖数据
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS draws (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            lottery TEXT NOT NULL,

            issue TEXT NOT NULL,

            open_time TEXT,

            n1 INTEGER,
            n2 INTEGER,
            n3 INTEGER,
            n4 INTEGER,
            n5 INTEGER,
            n6 INTEGER,
            special INTEGER,

            zodiac TEXT,

            wave TEXT,

            source TEXT,

            created_at TEXT NOT NULL,

            UNIQUE (
                lottery,
                issue
            )
        )
    """)


    # -----------------------------------------------------
    # 索引
    # -----------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_draws_lottery

        ON draws (
            lottery
        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_draws_issue

        ON draws (
            lottery,
            issue
        )
    """)


    # -----------------------------------------------------
    # 运行日志
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        fetch_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            lottery TEXT,

            success INTEGER,

            issue TEXT,

            source TEXT,

            error TEXT,

            created_at TEXT NOT NULL
        )
    """)


    conn.commit()

    conn.close()


# =========================================================
# 插入开奖
# =========================================================

def insert_draw(draw):

    numbers = draw.get(
        "numbers",
        []
    )

    if len(numbers) != 7:

        return False


    conn = get_connection()

    cursor = conn.cursor()


    try:

        cursor.execute("""
            INSERT OR IGNORE INTO draws (

                lottery,

                issue,

                open_time,

                n1,
                n2,
                n3,
                n4,
                n5,
                n6,

                special,

                zodiac,

                wave,

                source,

                created_at
            )

            VALUES (
                ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?
            )
        """, (

            draw["lottery"],

            draw["issue"],

            draw.get(
                "open_time"
            ),

            int(numbers[0]),
            int(numbers[1]),
            int(numbers[2]),
            int(numbers[3]),
            int(numbers[4]),
            int(numbers[5]),

            int(numbers[6]),

            draw.get(
                "zodiac"
            ),

            draw.get(
                "wave"
            ),

            draw.get(
                "source"
            ),

            datetime.utcnow()
            .isoformat(),
        ))


        conn.commit()

        return cursor.rowcount > 0


    except Exception as e:

        print(
            "数据库写入失败:",
            e
        )

        return False


    finally:

        conn.close()


# =========================================================
# 获取历史
# =========================================================

def get_draws(
    lottery,
    limit=5000
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *

        FROM draws

        WHERE lottery = ?

        ORDER BY id DESC

        LIMIT ?
    """, (
        lottery,
        limit
    ))


    rows = cursor.fetchall()

    conn.close()


    return list(rows)


# =========================================================
# 获取最新一期
# =========================================================

def get_latest_draw(
    lottery
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *

        FROM draws

        WHERE lottery = ?

        ORDER BY id DESC

        LIMIT 1
    """, (
        lottery,
    ))


    row = cursor.fetchone()

    conn.close()


    return row


# =========================================================
# 最新期号
# =========================================================

def get_latest_issue(
    lottery
):

    row = get_latest_draw(
        lottery
    )

    if row:

        return row["issue"]

    return None


# =========================================================
# 数据数量
# =========================================================

def count_draws(
    lottery
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT COUNT(*)

        FROM draws

        WHERE lottery = ?
    """, (
        lottery,
    ))


    result = cursor.fetchone()[0]

    conn.close()


    return result


# =========================================================
# 抓取日志
# =========================================================

def insert_fetch_log(
    lottery,
    success,
    issue=None,
    source=None,
    error=None
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        INSERT INTO fetch_logs (

            lottery,

            success,

            issue,

            source,

            error,

            created_at
        )

        VALUES (
            ?, ?, ?, ?, ?, ?
        )
    """, (

        lottery,

        1 if success else 0,

        issue,

        source,

        error,

        datetime.utcnow()
        .isoformat(),
    ))


    conn.commit()

    conn.close()
