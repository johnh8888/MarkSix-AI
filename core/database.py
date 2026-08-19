# -*- coding:utf-8 -*-

"""
六合彩 AI V3.1 FINAL

SQLite数据库模块

功能：

1. 初始化数据库
2. 保存开奖
3. 查询历史
4. 查询最新一期
5. 防重复写入

"""

from __future__ import annotations


import sqlite3

from datetime import datetime

from pathlib import Path


from config import DATABASE_FILE



# =====================================================
# 数据库连接
# =====================================================


def get_connection():

    return sqlite3.connect(
        DATABASE_FILE
    )



# =====================================================
# 初始化数据库
# =====================================================


def init_database():

    conn = get_connection()

    cur = conn.cursor()


    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS draws
        (

            id INTEGER PRIMARY KEY AUTOINCREMENT,


            lottery TEXT NOT NULL,


            issue TEXT NOT NULL,


            numbers TEXT NOT NULL,


            special INTEGER NOT NULL,


            source TEXT,


            create_time TEXT,


            UNIQUE(lottery, issue)

        )
        """
    )


    conn.commit()

    conn.close()


    print(
        "数据库初始化完成:",
        DATABASE_FILE
    )



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


    conn = get_connection()

    cur = conn.cursor()


    try:


        # 查询是否存在

        cur.execute(
            """
            SELECT id
            FROM draws
            WHERE lottery=?
            AND issue=?
            """,

            (
                lottery,
                str(issue)
            )
        )


        exists = cur.fetchone()



        if exists:


            return {

                "status":
                    "exists",

                "lottery":
                    lottery,

                "issue":
                    str(issue)

            }




        cur.execute(

            """
            INSERT INTO draws
            (

            lottery,

            issue,

            numbers,

            special,

            source,

            create_time

            )

            VALUES(?,?,?,?,?,?)

            """,

            (

                lottery,

                str(issue),

                ",".join(
                    map(
                        str,
                        numbers
                    )
                ),

                int(special),

                source,

                datetime.now().isoformat()

            )

        )


        conn.commit()



        return {

            "status":
                "new",

            "lottery":
                lottery,

            "issue":
                str(issue)

        }



    except Exception as e:


        print(
            "数据库保存错误:",
            e
        )


        return {

            "status":
                "error",

            "error":
                str(e)

        }



    finally:


        conn.close()



# =====================================================
# 兼容旧版本
# =====================================================


def save_draw_bool(
        lottery,
        issue,
        numbers,
        special,
        source="api"
):


    result = save_draw(
        lottery,
        issue,
        numbers,
        special,
        source
    )


    return (
        result.get("status")
        ==
        "new"
    )



# =====================================================
# 获取历史
# =====================================================


def load_history(
        lottery,
        limit=500
):


    conn = get_connection()

    cur = conn.cursor()



    cur.execute(

        """

        SELECT

        issue,

        numbers,

        special


        FROM draws


        WHERE lottery=?


        ORDER BY id DESC


        LIMIT ?

        """,

        (

            lottery,

            limit

        )

    )


    rows = cur.fetchall()


    conn.close()



    result=[]


    for issue,numbers,special in rows:


        result.append(

            {

                "issue":

                    issue,


                "numbers":

                    [

                        int(x)

                        for x in numbers.split(",")

                        if x

                    ],


                "special":

                    int(special)

            }

        )



    return result[::-1]



# =====================================================
# 最新一期
# =====================================================


def latest_draw(
        lottery
):


    data = load_history(
        lottery,
        1
    )


    if data:

        return data[0]


    return None



# =====================================================
# 数据统计
# =====================================================


def count_draws(
        lottery=None
):


    conn=get_connection()

    cur=conn.cursor()


    if lottery:


        cur.execute(
            """
            SELECT COUNT(*)
            FROM draws
            WHERE lottery=?
            """,
            (
                lottery,
            )
        )

    else:


        cur.execute(
            """
            SELECT COUNT(*)
            FROM draws
            """
        )


    count = cur.fetchone()[0]


    conn.close()


    return count



__all__=[

    "init_database",

    "save_draw",

    "save_draw_bool",

    "load_history",

    "latest_draw",

    "count_draws"

]
