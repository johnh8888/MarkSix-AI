# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V4.0

database.py

SQLite数据库模块


功能:

1. 初始化数据库
2. 创建表
3. 保存开奖
4. 查询历史
5. 查询最新数据


"""


import sqlite3

import os

from datetime import datetime





# =====================================================
# 数据目录
# =====================================================


DATA_DIR = "data"


os.makedirs(

    DATA_DIR,

    exist_ok=True

)





# =====================================================
# 彩种数据库
# =====================================================


DB_FILES = {


    "hk":

    os.path.join(

        DATA_DIR,

        "hk.db"

    ),



    "newMacau":

    os.path.join(

        DATA_DIR,

        "newMacau.db"

    ),



    "oldMacau":

    os.path.join(

        DATA_DIR,

        "oldMacau.db"

    )

}






# =====================================================
# 获取连接
# =====================================================


def get_connection(code):


    if code not in DB_FILES:


        raise ValueError(

            f"未知彩种:{code}"

        )



    conn=sqlite3.connect(

        DB_FILES[code]

    )


    conn.row_factory=sqlite3.Row



    return conn





# =====================================================
# 初始化单数据库
# =====================================================


def init_single_database(code):


    conn=get_connection(

        code

    )


    cur=conn.cursor()



    cur.execute(

        """

        CREATE TABLE IF NOT EXISTS draws

        (

            id INTEGER PRIMARY KEY AUTOINCREMENT,


            issue TEXT UNIQUE,


            numbers TEXT,


            open_time TEXT,


            source TEXT,


            create_time TEXT

        )

        """

    )



    conn.commit()


    conn.close()





# =====================================================
# 初始化全部数据库
# =====================================================


def init_database():


    for code in DB_FILES:


        init_single_database(

            code

        )


    print(

        "数据库初始化完成"

    )





# =====================================================
# 保存开奖
# =====================================================


def save_draw(

        code,

        draw

):


    conn=get_connection(

        code

    )


    cur=conn.cursor()



    numbers=" ".join(

        str(x)

        for x in draw.get(

            "numbers",

            []

        )

    )



    try:


        cur.execute(

            """

            INSERT INTO draws

            (

            issue,

            numbers,

            open_time,

            source,

            create_time

            )

            VALUES

            (?,?,?,?,?)

            """,

            (

            draw.get(

                "issue"

            ),


            numbers,


            draw.get(

                "open_time",

                ""

            ),


            draw.get(

                "source",

                ""

            ),


            datetime.now().isoformat()

            )

        )


        conn.commit()


        result=True



    except sqlite3.IntegrityError:


        result=False



    finally:


        conn.close()



    return result





# =====================================================
# 批量保存
# =====================================================


def save_history(

        code,

        rows

):


    count=0



    for row in rows:


        if save_draw(

            code,

            row

        ):


            count+=1



    return count





# =====================================================
# 加载历史
# =====================================================


def load_history(

        code,

        limit=None

):


    conn=get_connection(

        code

    )


    cur=conn.cursor()



    sql="""

    SELECT *

    FROM draws

    ORDER BY id DESC

    """



    if limit:


        sql += f"""

        LIMIT {int(limit)}

        """



    rows=cur.execute(

        sql

    ).fetchall()



    conn.close()



    result=[]



    for row in rows:


        result.append(

            {

            "issue":

            row["issue"],


            "numbers":

            [

            int(x)

            for x in row["numbers"].split()

            ],


            "open_time":

            row["open_time"]

            }

        )



    return result





# =====================================================
# 获取最新一期
# =====================================================


def get_latest(code):


    data=load_history(

        code,

        1

    )


    if data:


        return data[0]


    return None





# =====================================================
# 数据数量
# =====================================================


def count_draws(code):


    conn=get_connection(

        code

    )


    cur=conn.cursor()



    row=cur.execute(

        """

        SELECT COUNT(*)

        FROM draws

        """

    ).fetchone()



    conn.close()



    return row[0]





# =====================================================
# 删除数据库
# =====================================================


def clear_database(code):


    conn=get_connection(

        code

    )


    cur=conn.cursor()



    cur.execute(

        "DELETE FROM draws"

    )



    conn.commit()

    conn.close()





# =====================================================
# 测试
# =====================================================


if __name__=="__main__":


    init_database()



    test={


        "issue":

        "2026090",


        "numbers":

        [

        39,

        41,

        8,

        9,

        7,

        14,

        49

        ],


        "source":

        "test"


    }



    print(

        save_draw(

            "hk",

            test

        )

    )



    print(

        load_history(

            "hk",

            5

        )

    )
