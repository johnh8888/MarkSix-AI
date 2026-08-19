# -*- coding: utf-8 -*-

"""
六合彩数据库模块

统一使用单一 SQLite 数据库（config.DATABASE_FILE），
三个彩种共用一张表，用 lottery 字段区分。

对外接口（与 core/engine.py 的调用方式保持一致）：

    init_db()
    save_records(lottery_name, records) -> int   新增条数
    load_records(lottery_name) -> list[dict]
    count_records(lottery_name) -> int
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

import config


def _connect() -> sqlite3.Connection:

    config.DATA_DIR.mkdir(
        exist_ok=True,
    )

    conn = sqlite3.connect(
        str(config.DATABASE_FILE)
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS draws (
            issue TEXT NOT NULL,
            lottery TEXT NOT NULL,
            numbers TEXT NOT NULL,
            special_number INTEGER,
            open_time TEXT,
            source TEXT,
            PRIMARY KEY (issue, lottery)
        )
        """
    )

    return conn


def init_db() -> None:

    conn = _connect()

    conn.commit()

    conn.close()


def save_records(
    lottery_name: str,
    records: list[dict[str, Any]],
) -> int:

    if not records:
        return 0

    conn = _connect()

    try:

        cursor = conn.cursor()

        inserted = 0

        for row in records:

            issue = str(
                row.get("issue", "")
            )

            numbers = row.get(
                "numbers", []
            )

            if not issue:
                continue

            if len(numbers) != 7:
                continue

            cursor.execute(
                """
                INSERT OR REPLACE INTO draws
                (issue, lottery, numbers, special_number, open_time, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    issue,
                    lottery_name,
                    json.dumps(
                        numbers,
                        ensure_ascii=False,
                    ),
                    int(numbers[6]),
                    row.get("open_time", ""),
                    row.get("source", ""),
                ),
            )

            inserted += 1

        conn.commit()

        return inserted

    finally:

        conn.close()


def load_records(
    lottery_name: str,
) -> list[dict[str, Any]]:

    conn = _connect()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT issue, numbers, special_number, open_time, source
            FROM draws
            WHERE lottery = ?
            """,
            (lottery_name,),
        )

        rows = cursor.fetchall()

    finally:

        conn.close()

    result = []

    for issue, numbers, special, open_time, source in rows:

        try:
            parsed = json.loads(numbers)
        except Exception:
            continue

        if not isinstance(parsed, list):
            continue

        if len(parsed) != 7:
            continue

        result.append(
            {
                "issue": issue,
                "lottery": lottery_name,
                "numbers": [int(x) for x in parsed],
                "special_number": int(
                    special or parsed[6]
                ),
                "open_time": open_time or "",
                "source": source or "",
            }
        )

    result.sort(
        key=lambda x: int(x["issue"])
    )

    return result


def count_records(
    lottery_name: str,
) -> int:

    conn = _connect()

    try:

        count = conn.execute(
            "SELECT COUNT(*) FROM draws WHERE lottery = ?",
            (lottery_name,),
        ).fetchone()[0]

    finally:

        conn.close()

    return count
