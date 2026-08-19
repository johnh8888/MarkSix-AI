# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

SQLite数据库模块

唯一数据库接口
"""


import sqlite3


from datetime import datetime


from pathlib import Path


import sys



# =====================================================
# 修复 GitHub Actions 导入路径
# =====================================================


BASE_DIR = Path(__file__).resolve().parent.parent


if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR)
    )



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


    conn=get_connection()

    cur=conn.cursor()



    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS draws
        (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            lottery TEXT,

            issue TEXT,

            numbers TEXT,

            special INTEGER,

            source TEXT,

            create_time TEXT,


            UNIQUE(lottery,issue)

        )
        """
    )


    conn.commit()

    conn.close()







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


    conn=get_connection()

    cur=conn.cursor()



    try:


        cur.execute(

            """
            INSERT OR IGNORE INTO draws
            (

            lottery,

            issue,

            numbers,

            special,

            source,

            create_time

            )

            VALUES (?,?,?,?,?,?)

            """,

            (

                lottery,

                str(issue),

                ",".join(

                    map(str,numbers)

                ),

                int(special),

                source,

                datetime.now().isoformat()

            )

        )


        conn.commit()



        return cur.rowcount > 0



    except Exception as e:


        print(
            "保存失败:",
            e
        )


        return False



    finally:


        conn.close()








# =====================================================
# 获取历史
# =====================================================


def load_history(

        lottery,

        limit=500

):


    conn=get_connection()

    cur=conn.cursor()



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



    rows=cur.fetchall()



    conn.close()



    result=[]



    for issue,numbers,special in rows:


        result.append(

            {

                "issue":issue,


                "numbers":[

                    int(x)

                    for x in numbers.split(",")

                    if x

                ],


                "special":special

            }

        )



    return result[::-1]







# =====================================================
# 最新一期
# =====================================================


def latest_draw(lottery):


    data=load_history(

        lottery,

        1

    )


    if data:


        return data[0]


    return None





__all__=[

    "init_database",

    "save_draw",

    "load_history",

    "latest_draw"

]
