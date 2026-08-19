# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sqlite3
import json
from typing import Any


def init_db() -> None:

    os.makedirs(
        "data",
        exist_ok=True,
    )


def save_records(
    db_path: str,
    records: list[dict[str, Any]],
) -> int:

    if not records:
        return 0

    os.makedirs(
        os.path.dirname(db_path),
        exist_ok=True,
    )

    connection = sqlite3.connect(
        db_path
    )

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS draws (
                issue TEXT PRIMARY KEY,
                numbers TEXT NOT NULL,
                special_number INTEGER,
                open_time TEXT,
                lottery TEXT,
                source TEXT
            )
            """
        )

        inserted = 0

        for row in records:

            issue = str(
                row.get(
                    "issue",
                    "",
                )
            )

            numbers = row.get(
                "numbers",
                [],
            )

            if not issue:
                continue

            if len(numbers) != 7:
                continue

            cursor.execute(
                """
                INSERT OR REPLACE INTO draws
                (
                    issue,
                    numbers,
                    special_number,
                    open_time,
                    lottery,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    issue,
                    json.dumps(
                        numbers,
                        ensure_ascii=False,
                    ),
                    int(
                        numbers[6]
                    ),
                    row.get(
                        "open_time",
                        "",
                    ),
                    row.get(
                        "lottery",
                        "",
                    ),
                    row.get(
                        "source",
                        "",
                    ),
                ),
            )

            inserted += 1

        connection.commit()

        return inserted

    finally:

        connection.close()


def load_records(
    db_path: str,
) -> list[dict[str, Any]]:

    if not os.path.isfile(
        db_path
    ):
        return []

    connection = sqlite3.connect(
        db_path
    )

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS draws (
                issue TEXT PRIMARY KEY,
                numbers TEXT NOT NULL,
                special_number INTEGER,
                open_time TEXT,
                lottery TEXT,
                source TEXT
            )
            """
        )

        cursor.execute(
            """
            SELECT
                issue,
                numbers,
                special_number,
                open_time,
                lottery,
                source
            FROM draws
            """
        )

        rows = cursor.fetchall()

        result = []

        for row in rows:

            try:

                numbers = json.loads(
                    row[1]
                )

            except Exception:

                continue

            if not isinstance(
                numbers,
                list,
            ):
                continue

            if len(numbers) != 7:
                continue

            result.append(
                {
                    "issue": row[0],
                    "numbers": [
                        int(x)
                        for x in numbers
                    ],
                    "special_number":
                        int(
                            row[2]
                            or numbers[6]
                        ),
                    "open_time":
                        row[3] or "",
                    "lottery":
                        row[4] or "",
                    "source":
                        row[5] or "",
                }
            )

        result.sort(
            key=lambda x: int(
                x["issue"]
            )
        )

        return result

    finally:

        connection.close()
