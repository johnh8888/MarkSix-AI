# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/sqlite_manager.py

SQLite统一管理

接口:

init_database()
load_history()
get_connection()

"""

from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any


# =====================================================
# 路径
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent


DB_FILES = {

    "hk":
    BASE_DIR / "hk_macau.db",


    "newMacau":
    BASE_DIR / "new_macau.db",


    "oldMacau":
    BASE_DIR / "old_macau.db"

}



# =====================================================
# 连接
# =====================================================


def get_connection(key:str):

    if key not in DB_FILES:

        raise ValueError(
            f"未知彩种:{key}"
        )


    conn=sqlite3.connect(
        str(DB_FILES[key])
    )

    conn.row_factory=sqlite3.Row

    return conn





# =====================================================
# 初始化
# =====================================================


def init_database():

    for key in DB_FILES:


        conn=get_connection(key)


        conn.execute("""

        CREATE TABLE IF NOT EXISTS draws(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            issue_no TEXT UNIQUE,

            draw_date TEXT,

            numbers_json TEXT,

            special INTEGER,

            source TEXT,

            created_at TEXT

        )

        """)


        conn.commit()

        conn.close()


    return True





# =====================================================
# 保存开奖
# =====================================================


def save_draw(
    key:str,
    issue_no:str,
    date:str,
    numbers:list,
    special:int,
    source="api"
):


    conn=get_connection(key)


    conn.execute(
    """

    INSERT OR REPLACE INTO draws

    (
    issue_no,
    draw_date,
    numbers_json,
    special,
    source,
    created_at
    )

    VALUES(?,?,?,?,?,datetime('now'))

    """,

    (

    str(issue_no),

    date,

    json.dumps(numbers),

    int(special),

    source

    )


    )


    conn.commit()

    conn.close()






# =====================================================
# 读取历史
# =====================================================


def load_history(
        key:str
)->List[Dict[str,Any]]:


    conn=get_connection(key)


    rows=conn.execute(
    """

    SELECT *

    FROM draws

    ORDER BY id DESC

    """
    ).fetchall()


    conn.close()



    result=[]


    for r in rows:


        try:


            numbers=json.loads(
                r["numbers_json"]
            )


            result.append(

            {

            "issue":
            r["issue_no"],


            "date":
            r["draw_date"],


            "numbers":
            numbers,


            "special":
            int(r["special"])


            }

            )


        except Exception:


            continue



    return result





# =====================================================
# 兼容旧名称
# =====================================================


load_data=load_history



__all__=[

"init_database",

"load_history",

"save_draw",

"get_connection"

]
