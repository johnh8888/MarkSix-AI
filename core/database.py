# -*- coding: utf-8 -*-

"""
六合AI V10.0 FINAL

SQLite数据库模块

功能:
历史保存
实时保存
预测读取
"""

import sqlite3
import os
from datetime import datetime



DB_FILE="marksix.db"



# ==========================
# 初始化
# ==========================

def init_db():

    conn=sqlite3.connect(
        DB_FILE
    )

    c=conn.cursor()


    c.execute(
    """
    CREATE TABLE IF NOT EXISTS history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        lottery TEXT,

        issue TEXT,

        n1 INTEGER,
        n2 INTEGER,
        n3 INTEGER,
        n4 INTEGER,
        n5 INTEGER,
        n6 INTEGER,
        special INTEGER,

        create_time TEXT

    )
    """
    )


    conn.commit()

    conn.close()





# ==========================
# 保存开奖
# ==========================

def save_draw(
    lottery,
    issue,
    numbers
):


    if not numbers:

        return False



    nums=list(numbers)



    while len(nums)<7:

        nums.append(0)



    conn=sqlite3.connect(
        DB_FILE
    )


    c=conn.cursor()



    # 防止重复

    c.execute(
    """
    SELECT id FROM history
    WHERE lottery=? AND issue=?
    """,
    (
        lottery,
        issue
    )
    )



    exists=c.fetchone()



    if exists:

        conn.close()

        return False




    c.execute(
    """
    INSERT INTO history
    (
    lottery,
    issue,
    n1,n2,n3,n4,n5,n6,
    special,
    create_time
    )
    VALUES
    (?,?,?,?,?,?,?,?,?,?)
    """,
    (

        lottery,

        issue,

        nums[0],
        nums[1],
        nums[2],
        nums[3],
        nums[4],
        nums[5],

        nums[-1],

        datetime.now().isoformat()

    )

    )



    conn.commit()

    conn.close()


    return True





# ==========================
# 读取历史
# ==========================

def get_history(
    lottery,
    limit=500
):


    conn=sqlite3.connect(
        DB_FILE
    )


    c=conn.cursor()



    c.execute(
    """
    SELECT

    n1,n2,n3,n4,n5,n6,special

    FROM history

    WHERE lottery=?

    ORDER BY id DESC

    LIMIT ?

    """,
    (
        lottery,
        limit
    )
    )



    rows=c.fetchall()


    conn.close()



    result=[]


    for r in rows:


        nums=[

            x for x in r

            if x

        ]


        result.append(
            nums
        )



    return result





# ==========================
# 获取数量
# ==========================

def count_history(
    lottery
):


    conn=sqlite3.connect(
        DB_FILE
    )


    c=conn.cursor()



    c.execute(
    """
    SELECT COUNT(*)

    FROM history

    WHERE lottery=?

    """,
    (
        lottery,
    )
    )



    n=c.fetchone()[0]


    conn.close()


    return n





# ==========================
# 清空
# ==========================

def clear_db():

    if os.path.exists(
        DB_FILE
    ):

        os.remove(
            DB_FILE
        )
