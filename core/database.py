# -*- coding: utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

database.py

数据库管理模块


功能:

1. 初始化数据库
2. 创建开奖表
3. 插入数据
4. 自动去重
5. 查询历史
6. 获取最新开奖


"""


import sqlite3

import os





# =====================================================
# 数据库配置
# =====================================================


DB_DIR="data"



DB_FILES={


    "hk":

    "hk.db",



    "newMacau":

    "new_macau.db",



    "oldMacau":

    "old_macau.db"

}





# =====================================================
# 数据库路径
# =====================================================


def get_db_path(code):


    os.makedirs(
        DB_DIR,
        exist_ok=True
    )


    filename=DB_FILES.get(

        code,

        f"{code}.db"

    )


    return os.path.join(

        DB_DIR,

        filename

    )





# =====================================================
# 连接数据库
# =====================================================


def connect_db(code):


    path=get_db_path(
        code
    )


    conn=sqlite3.connect(
        path
    )


    conn.row_factory=sqlite3.Row


    return conn





# =====================================================
# 初始化单个数据库
# =====================================================


def init_database(code):


    conn=connect_db(
        code
    )


    cursor=conn.cursor()



    cursor.execute(

        """

        CREATE TABLE IF NOT EXISTS history
        (

            id INTEGER PRIMARY KEY AUTOINCREMENT,


            issue TEXT UNIQUE,


            numbers TEXT,


            special INTEGER,


            zodiac TEXT,


            wave TEXT,


            open_time TEXT,


            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """

    )



    conn.commit()

    conn.close()



    return True





# =====================================================
# 初始化全部数据库
# =====================================================


def init_all_database():


    for code in DB_FILES:


        init_database(
            code
        )


    return True





# =====================================================
# 插入开奖
# =====================================================


def insert_draw(
        code,
        data
):


    init_database(
        code
    )


    conn=connect_db(
        code
    )


    cursor=conn.cursor()



    try:


        cursor.execute(

        """

        INSERT OR IGNORE INTO history

        (

        issue,

        numbers,

        special,

        zodiac,

        wave,

        open_time

        )


        VALUES

        (?,?,?,?,?,?)

        """,

        (

        data.get("issue"),

        data.get("numbers"),

        data.get("special"),

        data.get("zodiac"),

        data.get("wave"),

        data.get("open_time")

        )


        )



        conn.commit()



        result=cursor.rowcount



    finally:


        conn.close()



    return result





# =====================================================
# 批量插入
# =====================================================


def insert_many(
        code,
        rows
):


    count=0



    for row in rows:


        count += insert_draw(

            code,

            row

        )



    return count





# =====================================================
# 查询历史
# =====================================================


def get_history(
        code,

        limit=None

):


    conn=connect_db(
        code
    )


    cursor=conn.cursor()



    sql="""

    SELECT *

    FROM history

    ORDER BY id DESC

    """



    if limit:


        sql += f" LIMIT {int(limit)}"



    cursor.execute(
        sql
    )



    rows=[

        dict(x)

        for x in cursor.fetchall()

    ]



    conn.close()



    return rows





# =====================================================
# 最新一期
# =====================================================


def get_latest(code):


    rows=get_history(
        code,

        1

    )


    if rows:


        return rows[0]


    return None





# =====================================================
# 数据数量
# =====================================================


def count_history(code):


    conn=connect_db(
        code
    )


    cursor=conn.cursor()



    cursor.execute(

        "SELECT COUNT(*) FROM history"

    )



    result=cursor.fetchone()[0]


    conn.close()



    return result





# =====================================================
# 清空数据库
# =====================================================


def clear_database(code):


    conn=connect_db(
        code
    )


    cursor=conn.cursor()



    cursor.execute(

        "DELETE FROM history"

    )


    conn.commit()

    conn.close()





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    print(

        "初始化数据库"

    )


    init_all_database()



    print(

        "香港记录:",

        count_history(
            "hk"
        )

    )
