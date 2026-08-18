# -*- coding: utf-8 -*-
"""SQLite 数据库兼容层。统一提供 init_database / connect_db / init_db 等接口。"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .config import DB_FILES


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def connect_db(path: Path | str):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(conn):
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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_draws_date ON draws(draw_date, issue_no)")
    conn.commit()


def init_database():
    for path in DB_FILES.values():
        conn = connect_db(path)
        try:
            init_db(conn)
        finally:
            conn.close()
    return True


def save_draw(conn, issue_no, draw_date, numbers, special, source="unknown"):
    numbers = [int(x) for x in numbers]
    special = int(special)
    all_numbers = numbers + [special]
    if len(all_numbers) != 7 or len(set(all_numbers)) != 7 or not all(1 <= n <= 49 for n in all_numbers):
        return "invalid"
    payload = json.dumps(numbers, ensure_ascii=False)
    existing = conn.execute("SELECT numbers_json, special FROM draws WHERE issue_no=?", (str(issue_no),)).fetchone()
    now = now_iso()
    if existing:
        if existing["numbers_json"] == payload and int(existing["special"]) == special:
            return "unchanged"
        conn.execute("UPDATE draws SET draw_date=?, numbers_json=?, special=?, source=?, updated_at=? WHERE issue_no=?",
                     (draw_date, payload, special, source, now, str(issue_no)))
        conn.commit()
        return "updated"
    conn.execute("INSERT INTO draws(issue_no,draw_date,numbers_json,special,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                 (str(issue_no), draw_date, payload, special, source, now, now))
    conn.commit()
    return "inserted"


def load_rows(conn):
    rows = conn.execute("SELECT issue_no,draw_date,numbers_json,special,source FROM draws ORDER BY draw_date DESC, issue_no DESC").fetchall()
    out = []
    for r in rows:
        try:
            out.append({"issue": str(r["issue_no"]), "issue_no": str(r["issue_no"]),
                        "draw_date": r["draw_date"] or "", "numbers": [int(x) for x in json.loads(r["numbers_json"])],
                        "special": int(r["special"]), "source": r["source"] or ""})
        except Exception:
            continue
    return out


def get_rows(key):
    conn = connect_db(DB_FILES[key])
    try:
        init_db(conn)
        return load_rows(conn)
    finally:
        conn.close()
