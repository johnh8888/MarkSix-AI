# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

from .config import DB_FILE


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    conn = get_connection()

    cursor = conn.cursor()

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

            UNIQUE(lottery, issue)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_draws_lottery
        ON draws(lottery)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_draws_issue
        ON draws(lottery, issue)
    """)

    conn.commit()
    conn.close()


def insert_draw(draw):

    conn = get_connection()

    cursor = conn.cursor()

    numbers = draw["numbers"]

    if len(numbers) != 7:
        conn.close()
        return False

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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            draw["lottery"],
            draw["issue"],
            draw.get("open_time"),

            numbers[0],
            numbers[1],
            numbers[2],
            numbers[3],
            numbers[4],
            numbers[5],
            numbers[6],

            draw.get("zodiac"),
            draw.get("wave"),

            draw.get("source", ""),
            datetime.utcnow().isoformat(),
        ))

        conn.commit()

        inserted = cursor.rowcount > 0

    except Exception as e:

        print("数据库写入失败:", e)

        inserted = False

    finally:

        conn.close()

    return inserted


def get_draws(lottery, limit=3000):

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


def count_draws(lottery):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM draws
        WHERE lottery = ?
    """, (lottery,))

    result = cursor.fetchone()[0]

    conn.close()

    return result


def get_latest_issue(lottery):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT issue
        FROM draws
        WHERE lottery = ?
        ORDER BY id DESC
        LIMIT 1
    """, (lottery,))

    row = cursor.fetchone()

    conn.close()

    if row:
        return row["issue"]

    return None
