# -*- coding: utf-8 -*-
"""
六合彩 AI V3.0 - 数据库层
统一数据格式：
{
    "issue_no": str,
    "draw_date": str,
    "numbers": List[int],   # 前6个正码
    "special": int,
    "source": str
}
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .config import DB_FILES


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_no TEXT NOT NULL UNIQUE,
            draw_date TEXT,
            numbers_json TEXT NOT NULL,
            special INTEGER NOT NULL,
            source TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_draws_date
        ON draws(draw_date, issue_no)
    """)
    conn.commit()


def save_draw(
    conn: sqlite3.Connection,
    issue_no: str,
    draw_date: str,
    numbers: List[int],
    special: int,
    source: str = "api",
) -> str:
    """
    返回: 'inserted' | 'updated' | 'unchanged' | 'invalid'
    """
    try:
        numbers = [int(x) for x in numbers]
        special = int(special)
    except Exception:
        return "invalid"

    all_numbers = numbers + [special]
    if len(all_numbers) != 7 or len(set(all_numbers)) != 7:
        return "invalid"
    if not all(1 <= n <= 49 for n in all_numbers):
        return "invalid"

    payload = json.dumps(numbers, ensure_ascii=False)
    now = now_iso()
    issue_no = str(issue_no).strip()

    existing = conn.execute(
        "SELECT numbers_json, special FROM draws WHERE issue_no=?",
        (issue_no,),
    ).fetchone()

    if existing:
        if existing["numbers_json"] == payload and int(existing["special"]) == special:
            return "unchanged"
        conn.execute(
            """
            UPDATE draws
            SET draw_date=?, numbers_json=?, special=?, source=?, updated_at=?
            WHERE issue_no=?
            """,
            (draw_date, payload, special, source, now, issue_no),
        )
        conn.commit()
        return "updated"

    conn.execute(
        """
        INSERT INTO draws
        (issue_no, draw_date, numbers_json, special, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (issue_no, draw_date, payload, special, source, now, now),
    )
    conn.commit()
    return "inserted"


def load_rows(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """返回：最新 → 最旧"""
    rows = conn.execute(
        """
        SELECT issue_no, draw_date, numbers_json, special, source
        FROM draws
        ORDER BY draw_date DESC, issue_no DESC
        """
    ).fetchall()

    result = []
    for r in rows:
        try:
            nums = [int(x) for x in json.loads(r["numbers_json"])]
            special = int(r["special"])
            if len(nums) != 6 or not (1 <= special <= 49):
                continue
            result.append({
                "issue_no": r["issue_no"],
                "draw_date": r["draw_date"] or "",
                "numbers": nums,
                "special": special,
                "source": r["source"] or "",
            })
        except Exception:
            continue
    return result


def get_row_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) AS c FROM draws").fetchone()["c"]
