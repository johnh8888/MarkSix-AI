# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
V7.1 数据库模块

功能：

1. SQLite 自动创建
2. 三彩种独立数据库
3. 保存历史开奖记录
4. 防止重复期号
5. 自动更新已有记录
6. 按期号排序读取
7. 兼容旧数据库
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


# ============================================================
# 路径
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 三彩种数据库
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
# 初始化单个数据库
# ============================================================

def get_connection(
    lottery_name: str,
) -> sqlite3.Connection:

    if lottery_name not in DB_FILES:

        raise ValueError(
            f"未知彩种：{lottery_name}"
        )

    db_path = DB_FILES[
        lottery_name
    ]

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


# ============================================================
# 初始化全部数据库
# ============================================================

def init_db() -> None:

    for lottery_name in DB_FILES:

        conn = get_connection(
            lottery_name
        )

        conn.close()


# ============================================================
# 保存开奖记录
# ============================================================

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
                record.get(
                    "issue",
                    "",
                )
            ).strip()

            numbers = record.get(
                "numbers",
                [],
            )

            if not issue:
                continue

            if not isinstance(
                numbers,
                (list, tuple),
            ):
                continue

            try:

                numbers = [
                    int(x)
                    for x in numbers
                ]

            except Exception:

                continue

            if len(numbers) != 7:
                continue

            if len(
                set(numbers)
            ) != 7:
                continue

            if not all(
                1 <= x <= 49
                for x in numbers
            ):
                continue

            numbers_text = ",".join(
                str(x)
                for x in numbers
            )

            # ------------------------------------------------
            # 先检查是否存在
            # ------------------------------------------------

            exists = conn.execute(
                """
                SELECT numbers
                FROM draws
                WHERE issue = ?
                """,
                (issue,),
            ).fetchone()

            # ------------------------------------------------
            # 新记录
            # ------------------------------------------------

            if exists is None:

                conn.execute(
                    """
                    INSERT INTO draws
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

                added += 1

            # ------------------------------------------------
            # 已有记录
            #
            # 如果号码发生变化，则更新
            # ------------------------------------------------

            else:

                old_numbers = str(
                    exists[0]
                )

                if old_numbers != numbers_text:

                    conn.execute(
                        """
                        UPDATE draws
                        SET numbers = ?
                        WHERE issue = ?
                        """,
                        (
                            numbers_text,
                            issue,
                        ),
                    )

        conn.commit()

    finally:

        conn.close()

    return added


# ============================================================
# 读取全部开奖记录
# ============================================================

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
                CAST(issue AS INTEGER) ASC
            """
        ).fetchall()

    finally:

        conn.close()

    result = []

    for issue, numbers in rows:

        try:

            nums = [
                int(x.strip())
                for x in str(
                    numbers
                ).split(",")
            ]

        except Exception:

            continue

        if len(nums) != 7:
            continue

        if len(
            set(nums)
        ) != 7:
            continue

        if not all(
            1 <= x <= 49
            for x in nums
        ):
            continue

        result.append(
            {
                "issue":
                    str(issue),

                "numbers":
                    nums,
            }
        )

    return result


# ============================================================
# 查询历史数量
# ============================================================

def count_records(
    lottery_name: str,
) -> int:

    conn = get_connection(
        lottery_name
    )

    try:

        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM draws
            """
        ).fetchone()

        return int(
            row[0]
        )

    finally:

        conn.close()


# ============================================================
# 查询最新一期
# ============================================================

def get_latest_record(
    lottery_name: str,
) -> dict[str, Any] | None:

    conn = get_connection(
        lottery_name
    )

    try:

        row = conn.execute(
            """
            SELECT
                issue,
                numbers
            FROM draws
            ORDER BY
                CAST(issue AS INTEGER) DESC
            LIMIT 1
            """
        ).fetchone()

    finally:

        conn.close()

    if not row:
        return None

    issue, numbers = row

    try:

        nums = [
            int(x.strip())
            for x in str(
                numbers
            ).split(",")
        ]

    except Exception:

        return None

    if len(nums) != 7:
        return None

    return {
        "issue":
            str(issue),

        "numbers":
            nums,
    }


# ============================================================
# 查询指定期号
# ============================================================

def get_record(
    lottery_name: str,
    issue: str,
) -> dict[str, Any] | None:

    conn = get_connection(
        lottery_name
    )

    try:

        row = conn.execute(
            """
            SELECT
                issue,
                numbers
            FROM draws
            WHERE issue = ?
            """,
            (
                str(issue),
            ),
        ).fetchone()

    finally:

        conn.close()

    if not row:
        return None

    try:

        nums = [
            int(x.strip())
            for x in str(
                row[1]
            ).split(",")
        ]

    except Exception:

        return None

    if len(nums) != 7:
        return None

    return {
        "issue":
            str(row[0]),

        "numbers":
            nums,
    }
