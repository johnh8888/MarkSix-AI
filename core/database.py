# -*- coding:utf-8 -*-

"""
六合彩AI智能预测系统 V5.0

database.py

数据库管理模块


功能：

1. SQLite初始化
2. 保存开奖数据
3. 查询历史数据
4. 保存模型权重
5. 保存预测记录


"""


import sqlite3

import json

import os

from datetime import datetime


from .config import (
    数据目录,
    模型文件
)





# =====================================================
# 数据库路径
# =====================================================


数据库文件 = os.path.join(

    数据目录,

    "marksix_v5.db"

)





# =====================================================
# 获取连接
# =====================================================


def 获取连接():

    return sqlite3.connect(

        数据库文件

    )





# =====================================================
# 初始化数据库
# =====================================================


def init_database():


    conn = 获取连接()

    cursor = conn.cursor()



    # 开奖历史表


    cursor.execute(

        """

        CREATE TABLE IF NOT EXISTS 开奖历史 (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            彩种 TEXT,

            期号 TEXT,

            开奖号码 TEXT,

            生肖 TEXT,

            波色 TEXT,

            开奖时间 TEXT,

            创建时间 TEXT

        )

        """

    )





    # 模型权重表


    cursor.execute(

        """

        CREATE TABLE IF NOT EXISTS 模型权重 (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            模型 TEXT UNIQUE,

            权重 REAL,

            命中率 REAL,

            更新时间 TEXT

        )

        """

    )





    # 预测记录表


    cursor.execute(

        """

        CREATE TABLE IF NOT EXISTS 预测记录 (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            彩种 TEXT,

            推荐号码 TEXT,

            推荐生肖 TEXT,

            推荐波色 TEXT,

            预测时间 TEXT

        )

        """

    )





    conn.commit()

    conn.close()



    print(

        "✅ 数据库初始化完成"

    )





# =====================================================
# 保存历史开奖
# =====================================================


def save_history(

        彩种,

        数据列表

):


    conn = 获取连接()

    cursor = conn.cursor()



    新增 = 0



    for 数据 in 数据列表:


        期号 = str(

            数据.get(

                "期号",

                数据.get(

                    "expect",

                    ""

                )

            )

        )



        cursor.execute(

            """

            SELECT id

            FROM 开奖历史

            WHERE 彩种=? AND 期号=?

            """,

            (

                彩种,

                期号

            )

        )


        已存在 = cursor.fetchone()



        if 已存在:


            continue





        号码 = 数据.get(

            "号码",

            数据.get(

                "numbers",

                []

            )

        )



        生肖 = 数据.get(

            "生肖",

            []

        )



        波色 = 数据.get(

            "波色",

            []

        )



        时间 = 数据.get(

            "开奖时间",

            ""

        )



        cursor.execute(

            """

            INSERT INTO 开奖历史

            (

            彩种,

            期号,

            开奖号码,

            生肖,

            波色,

            开奖时间,

            创建时间

            )

            VALUES (?,?,?,?,?,?,?)

            """,

            (

                彩种,

                期号,

                json.dumps(

                    号码,

                    ensure_ascii=False

                ),

                json.dumps(

                    生肖,

                    ensure_ascii=False

                ),

                json.dumps(

                    波色,

                    ensure_ascii=False

                ),

                时间,

                datetime.now().isoformat()

            )

        )



        新增 += 1





    conn.commit()

    conn.close()



    return 新增





# =====================================================
# 读取历史数据
# =====================================================


def load_history(

        彩种

):


    conn = 获取连接()

    cursor = conn.cursor()



    cursor.execute(

        """

        SELECT

        期号,

        开奖号码,

        生肖,

        波色,

        开奖时间

        FROM 开奖历史

        WHERE 彩种=?

        ORDER BY id ASC

        """,

        (

            彩种,

        )

    )



    rows = cursor.fetchall()



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


                "生肖":

                json.loads(

                    row[2]

                ),


                "波色":

                json.loads(

                    row[3]

                ),


                "开奖时间":

                row[4]

            }

        )



    return result





# =====================================================
# 保存模型权重
# =====================================================


def save_model_weight(

        模型,

        权重,

        命中率

):


    conn = 获取连接()

    cursor = conn.cursor()



    cursor.execute(

        """

        INSERT INTO 模型权重

        (

        模型,

        权重,

        命中率,

        更新时间

        )

        VALUES (?,?,?,?)

        ON CONFLICT(模型)

        DO UPDATE SET

        权重=excluded.权重,

        命中率=excluded.命中率,

        更新时间=excluded.更新时间

        """,

        (

            模型,

            权重,

            命中率,

            datetime.now().isoformat()

        )

    )



    conn.commit()

    conn.close()





# =====================================================
# 获取模型权重
# =====================================================


def get_model_weights():


    conn = 获取连接()

    cursor = conn.cursor()



    cursor.execute(

        """

        SELECT

        模型,

        权重

        FROM 模型权重

        """

    )


    rows = cursor.fetchall()


    conn.close()



    return {


        r[0]:

        r[1]

        for r in rows

    }





# =====================================================
# 保存预测
# =====================================================


def save_prediction(

        数据

):


    conn = 获取连接()

    cursor = conn.cursor()



    cursor.execute(

        """

        INSERT INTO 预测记录

        (

        彩种,

        推荐号码,

        推荐生肖,

        推荐波色,

        预测时间

        )

        VALUES (?,?,?,?,?)

        """,

        (

            数据.get(

                "彩种",

                ""

            ),


            json.dumps(

                数据.get(

                    "号码",

                    []

                ),

                ensure_ascii=False

            ),


            json.dumps(

                数据.get(

                    "生肖",

                    []

                ),

                ensure_ascii=False

            ),


            json.dumps(

                数据.get(

                    "波色",

                    []

                ),

                ensure_ascii=False

            ),


            datetime.now().isoformat()

        )

    )



    conn.commit()

    conn.close()





# =====================================================
# 测试
# =====================================================


if __name__ == "__main__":


    init_database()

    print(

        "数据库位置:",

        数据库文件

    )
