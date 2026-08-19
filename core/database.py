# -*- coding: utf-8 -*-

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


DB_FILES = {
    "新澳门彩": DATA_DIR / "new_macau.db",
    "老澳门彩": DATA_DIR / "old_macau.db",
    "香港彩": DATA_DIR / "hk.db",
}


def get_connection(lottery_name: str):

    db_path = DB_FILES[lottery_name]

    conn = sqlite3.connect(
        str(db_path)
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS draws (
            issue TEXT PRIMARY KEY,
            numbers TEXT NOT NULL
        )
        """
    )

    conn.commit()

    return conn


def save_records(
    lottery_name: str,
    records: list[dict[str, Any]],
) -> int:

    if not records:
        return 0

    conn = get_connection(
        lottery_name
    )

    added = 0

    try:

        for record in records:

            issue = str(
                record["issue"]
            )

            numbers = record[
                "numbers"
            ]

            numbers_text = ",".join(
                str(x)
                for x in numbers
            )

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO draws
                (
                    issue,
                    numbers
                )
                VALUES (?, ?)
                """,
                (
                    issue,
                    numbers_text,
                ),
            )

            if cursor.rowcount > 0:
                added += 1

        conn.commit()

    finally:

        conn.close()

    return added


def load_records(
    lottery_name: str,
) -> list[dict[str, Any]]:

    conn = get_connection(
        lottery_name
    )

    try:

        rows = conn.execute(
            """
            SELECT
                issue,
                numbers
            FROM draws
            ORDER BY
                CAST(issue AS INTEGER)
            """
        ).fetchall()

    finally:

        conn.close()

    result = []

    for issue, numbers in rows:

        try:

            nums = [
                int(x)
                for x in numbers.split(",")
            ]

        except Exception:

            continue

        if len(nums) != 7:
            continue

        result.append(
            {
                "issue": str(issue),
                "numbers": nums,
            }
        )

    return result


def count_records(
    lottery_name: str,
) -> int:

    conn = get_connection(
        lottery_name
    )

    try:

        row = conn.execute(
            "SELECT COUNT(*) FROM draws"
        ).fetchone()

        return int(row[0])

    finally:

        conn.close()
