# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V5.1 FINAL

core/sqlite_manager.py

SQLite数据库管理

功能：

1. 初始化数据库
2. 保存开奖数据
3. 读取历史数据
4. 支持三彩种

"""


from __future__ import annotations


import sqlite3
import json

from pathlib import Path
from datetime import datetime





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
# 连接数据库
# =====================================================


def connect_db(path):


    conn = sqlite3.connect(
        str(path)
    )


    conn.row_factory = sqlite3.Row


    return conn





# =====================================================
# 初始化
# =====================================================


def init_database():


    for key,path in DB_FILES.items():


        conn=connect_db(path)


        conn.execute(
            """

            CREATE TABLE IF NOT EXISTS draws(

                id INTEGER PRIMARY KEY AUTOINCREMENT,


                issue TEXT UNIQUE,


                numbers TEXT,


                special INTEGER,


                source TEXT,


                created_at TEXT


            )

            """
        )


        conn.commit()


        conn.close()



    return True





# =====================================================
# 保存开奖
# =====================================================


def save_draw(

        lottery,

        issue,

        numbers,

        special,

        source="api"

):


    if lottery not in DB_FILES:


        print(
            "未知彩种:",
            lottery
        )

        return False




    path=DB_FILES[lottery]


    conn=connect_db(path)



    try:


        conn.execute(

            """

            INSERT OR REPLACE INTO draws

            (

            issue,

            numbers,

            special,

            source,

            created_at

            )

            VALUES(?,?,?,?,?)

            """,

            (

                str(issue),


                json.dumps(

                    numbers,

                    ensure_ascii=False

                ),


                int(special),


                source,


                datetime.now().isoformat()

            )

        )


        conn.commit()



        return True



    except Exception as e:


        print(
            "保存失败:",
            e
        )


        return False



    finally:


        conn.close()








# =====================================================
# 读取历史
# =====================================================


def load_history(lottery):


    if lottery not in DB_FILES:


        return []



    conn=connect_db(
        DB_FILES[lottery]
    )


    rows=conn.execute(

        """

        SELECT *

        FROM draws

        ORDER BY id DESC


        """

    ).fetchall()



    result=[]



    for r in rows:


        try:


            numbers=json.loads(
                r["numbers"]
            )


            result.append(

                {


                "issue":

                r["issue"],



                "numbers":

                numbers,



                "special":

                int(
                    r["special"]
                ),



                "source":

                r["source"]


                }

            )


        except:


            continue



    conn.close()



    return result





# =====================================================
# 获取特码历史
# =====================================================


def load_specials(lottery):


    rows=load_history(
        lottery
    )


    return [

        x["special"]

        for x in rows

        if "special" in x

    ]





# =====================================================
# 数据统计
# =====================================================


def database_info():


    result={}



    for key,path in DB_FILES.items():


        conn=connect_db(path)


        count=conn.execute(

            "SELECT COUNT(*) FROM draws"

        ).fetchone()[0]


        conn.close()



        result[key]=count



    return result





__all__=[

    "init_database",

    "save_draw",

    "load_history",

    "load_specials",

    "database_info"

]
