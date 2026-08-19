# -*- coding: utf-8 -*-

"""
SQLite 数据库模块
"""

from __future__ import annotations

import sqlite3

from pathlib import Path

from typing import Iterable


# ============================================================
# 路径
# ============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATA_DIR = (
    ROOT / "data"
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 数据库
# ============================================================

DB_FILES = {

    "新澳门彩":
        DATA_DIR / "new_macau.db",

    "老澳门彩":
        DATA_DIR / "old_macau.db",

    "香港彩":
        DATA_DIR / "hk.db",

}


# ============================================================
# 连接数据库
# ============================================================

def connect(
    lottery_name: str,
) -> sqlite3.Connection:

    database = DB_FILES[
        lottery_name
    ]

    connection = sqlite3.connect(
        database
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS draws (

            issue TEXT PRIMARY KEY,

            n1 INTEGER NOT NULL,

            n2 INTEGER NOT NULL,

            n3 INTEGER NOT NULL,

            n4 INTEGER NOT NULL,

            n5 INTEGER NOT NULL,

            n6 INTEGER NOT NULL,

            n7 INTEGER NOT NULL,

            created_at
                TEXT
                DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    connection.commit()

    return connection


# ============================================================
# 保存开奖记录
# ============================================================

def save_records(
    lottery_name: str,
    records: Iterable[dict],
) -> int:

    records = list(records)

    if not records:

        return 0

    connection = connect(
        lottery_name
    )

    inserted = 0

    try:

        for record in records:

            issue = str(
                record["issue"]
            )

            numbers = [
                int(x)
                for x in record[
                    "numbers"
                ]
            ]

            if len(numbers) != 7:

                continue

            if len(set(numbers)) != 7:

                continue

            if not all(
                1 <= x <= 49
                for x in numbers
            ):

                continue

            cursor = connection.execute(

                """
                INSERT OR IGNORE INTO draws
                (
                    issue,
                    n1,
                    n2,
                    n3,
                    n4,
                    n5,
                    n6,
                    n7
                )
                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
                """,

                (
                    issue,
                    *numbers,
                ),

            )

            inserted += (
                cursor.rowcount
            )

        connection.commit()

    finally:

        connection.close()

    return inserted


# ============================================================
# 获取全部历史
# ============================================================

def get_history(
    lottery_name: str,
) -> list[dict]:

    connection = connect(
        lottery_name
    )

    try:

        rows = connection.execute(

            """
            SELECT
                issue,
                n1,
                n2,
                n3,
                n4,
                n5,
                n6,
                n7
            FROM draws
            ORDER BY
                CAST(issue AS INTEGER) ASC
            """

        ).fetchall()

        result = []

        for row in rows:

            result.append({

                "issue":
                    str(row["issue"]),

                "numbers": [

                    int(row["n1"]),

                    int(row["n2"]),

                    int(row["n3"]),

                    int(row["n4"]),

                    int(row["n5"]),

                    int(row["n6"]),

                    int(row["n7"]),

                ],

            })

        return result

    finally:

        connection.close()
