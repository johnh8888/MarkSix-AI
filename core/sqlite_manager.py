# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.1

sqlite_manager.py

SQLite数据库管理模块


功能:

1. 创建数据库
2. 保存开奖
3. 查询历史
4. 自动去重


"""


import sqlite3

import os

import json

from datetime import datetime





# =====================================================
# 数据目录
# =====================================================


DATA_DIR="data"


os.makedirs(

    DATA_DIR,

    exist_ok=True

)





# =====================================================
# 数据库映射
# =====================================================


DB_FILES={


    "香港六合彩":

    "hk_macau.db",



    "老澳门彩":

    "old_macau.db",



    "新澳门彩":

    "xin_macau.db"

}





# =====================================================
# 获取数据库
# =====================================================


def 获取数据库(

        彩种

):


    filename=DB_FILES.get(

        彩种

    )



    if not filename:


        raise Exception(

            "未知彩种:"+彩种

        )



    return os.path.join(

        DATA_DIR,

        filename

    )





# =====================================================
# 初始化数据库
# =====================================================


def 初始化数据库(

        彩种

):


    db=获取数据库(

        彩种

    )



    conn=sqlite3.connect(

        db

    )


    cur=conn.cursor()



    cur.execute(

        """

        CREATE TABLE IF NOT EXISTS history(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            issue TEXT UNIQUE,

            numbers TEXT,

            open_time TEXT,

            update_time TEXT

        )

        """

    )


    conn.commit()


    conn.close()



    return db





# =====================================================
# 保存开奖
# =====================================================


def 保存开奖(

        彩种,

        数据

):


    db=初始化数据库(

        彩种

    )



    conn=sqlite3.connect(

        db

    )


    cur=conn.cursor()



    新增=0



    for item in 数据:


        issue=str(

            item.get(

                "期号",

                ""

            )

        )



        numbers=item.get(

            "号码",

            []

        )



        if not issue:


            continue





        try:


            cur.execute(

                """

                INSERT INTO history

                (

                issue,

                numbers,

                open_time,

                update_time

                )

                VALUES(?,?,?,?)

                """,

                (

                    issue,

                    json.dumps(

                        numbers,

                        ensure_ascii=False

                    ),

                    item.get(

                        "开奖时间",

                        ""

                    ),

                    str(

                        datetime.now()

                    )

                )

            )


            新增+=1



        except sqlite3.IntegrityError:


            # 已存在

            pass





    conn.commit()


    conn.close()



    return 新增





# =====================================================
# 读取历史
# =====================================================


def 读取历史(

        彩种,

        数量=None

):


    db=初始化数据库(

        彩种

    )


    conn=sqlite3.connect(

        db

    )


    cur=conn.cursor()



    sql="""

    SELECT

    issue,

    numbers,

    open_time

    FROM history

    ORDER BY id ASC

    """



    if 数量:


        sql += f"""

        LIMIT {数量}

        """





    rows=cur.execute(

        sql

    ).fetchall()



    conn.close()



    result=[]



    for row in rows:


        result.append(

            {


                "期号":

                row[0],



                "号码":

                json.loads(

                    row[1]

                ),



                "开奖时间":

                row[2]

            }

        )



    return result





# =====================================================
# 获取最新一期
# =====================================================


def 最新一期(

        彩种

):


    data=读取历史(

        彩种,

        1

    )


    if data:


        return data[-1]



    return None





# =====================================================
# 数据统计
# =====================================================


def 数据统计(

        彩种

):


    db=初始化数据库(

        彩种

    )


    conn=sqlite3.connect(

        db

    )


    cur=conn.cursor()



    count=cur.execute(

        """

        SELECT COUNT(*)

        FROM history

        """

    ).fetchone()[0]



    conn.close()



    return {


        "彩种":

        彩种,


        "总期数":

        count,


        "数据库":

        db

    }





if __name__=="__main__":


    for name in DB_FILES:


        print(

            数据统计(

                name

            )

        )
