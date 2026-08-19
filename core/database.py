# -*- coding: utf-8 -*-

"""
SQLite 数据库层
V6.0
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
)

os.makedirs(
    DATA_DIR,
    exist_ok=True,
)


DB_FILES = {
    "新澳门彩": "new_macau.db",
    "老澳门彩": "old_macau.db",
    "香港彩": "hk.db",
}


def get_db_path(
    lottery_name: str,
) -> str:

    filename = DB_FILES.get(
        lottery_name,
        "lottery.db",
    )

    return os.path.join(
        DATA_DIR,
        filename,
    )


def connect(
    lottery_name: str,
) -> sqlite3.Connection:

    connection = sqlite3.connect(
        get_db_path(
            lottery_name
        )
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


def init_db(
    lottery_name: str,
) -> None:

    with connect(
        lottery_name
    ) as conn:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue TEXT NOT NULL UNIQUE,
                numbers TEXT NOT NULL,
                open_time TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_draws_issue
            ON draws(issue)
            """
        )

        conn.commit()


def save_records(
    lottery_name: str,
    records: List[Dict[str, Any]],
) -> int:

    init_db(
        lottery_name
    )

    inserted = 0

    with connect(
        lottery_name
    ) as conn:

        for record in records:

            issue = str(
                record.get("issue", "")
            ).strip()

            numbers = record.get(
                "numbers",
                [],
            )

            if not issue:
                continue

            if len(numbers) != 7:
                continue

            try:

                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO draws
                    (
                        issue,
                        numbers,
                        open_time
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        issue,
                        json.dumps(
                            numbers,
                            ensure_ascii=False,
                        ),
                        str(
                            record.get(
                                "open_time",
                                "",
                            )
                        ),
                    ),
                )

                if cursor.rowcount > 0:
                    inserted += 1

            except Exception:
                continue

        conn.commit()

    return inserted


def _sort_rows(
    rows: List[sqlite3.Row],
) -> List[Dict[str, Any]]:

    result = []

    for row in rows:

        try:

            numbers = json.loads(
                row["numbers"]
            )

        except Exception:
            continue

        result.append(
            {
                "issue": row["issue"],
                "numbers": numbers,
                "open_time": row[
                    "open_time"
                ],
            }
        )

    def sort_key(item):

        issue = str(
            item["issue"]
        )

        digits = "".join(
            c for c in issue
            if c.isdigit()
        )

        try:
            return int(digits)
        except Exception:
            return digits

    result.sort(
        key=sort_key
    )

    return result


def get_history(
    lottery_name: str,
    limit: int = 500,
) -> List[Dict[str, Any]]:

    init_db(
        lottery_name
    )

    with connect(
        lottery_name
    ) as conn:

        rows = conn.execute(
            """
            SELECT
                issue,
                numbers,
                open_time
            FROM draws
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                int(limit),
            ),
        ).fetchall()

    return list(
        reversed(
            _sort_rows(rows)
        )
    )


def get_count(
    lottery_name: str,
) -> int:

    init_db(
        lottery_name
    )

    with connect(
        lottery_name
    ) as conn:

        row = conn.execute(
            """
            SELECT COUNT(*)
            AS total
            FROM draws
            """
        ).fetchone()

    return int(
        row["total"]
    )


def clear_database(
    lottery_name: str,
) -> None:

    with connect(
        lottery_name
    ) as conn:

        conn.execute(
            "DROP TABLE IF EXISTS draws"
        )

        conn.commit()

    init_db(
        lottery_name
    )
