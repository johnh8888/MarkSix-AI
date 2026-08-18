# -*- coding:utf-8 -*-

"""
六合彩 AI 智能预测系统 V10.1

在线学习模块

功能:

1. 保存预测记录
2. 开奖后评估
3. 更新模型权重
"""


from datetime import datetime

import sqlite3

from pathlib import Path



BASE_DIR = Path(__file__).resolve().parent.parent


LEARN_DB = BASE_DIR / "learning.db"




# =========================
# 初始化
# =========================


def init_learning():

    conn=sqlite3.connect(
        LEARN_DB
    )


    conn.execute(

    """

    CREATE TABLE IF NOT EXISTS prediction_history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        lottery TEXT,

        issue TEXT,

        predict TEXT,

        result INTEGER,

        hit INTEGER,

        model TEXT,

        created TEXT

    )

    """

    )


    conn.execute(

    """

    CREATE TABLE IF NOT EXISTS model_weight(

        model TEXT PRIMARY KEY,

        weight REAL

    )

    """

    )


    # 默认权重


    models={

        "hot":0.4,

        "markov":0.35,

        "bayes":0.25

    }


    for k,v in models.items():


        conn.execute(

        """

        INSERT OR IGNORE INTO model_weight

        VALUES(?,?)

        """,

        (
            k,
            v
        )

        )



    conn.commit()

    conn.close()




# =========================
# 保存预测
# =========================


def save_prediction(

        lottery,

        issue,

        numbers,

        model="V10"


):


    conn=sqlite3.connect(
        LEARN_DB
    )


    conn.execute(

    """

    INSERT INTO prediction_history

    (

    lottery,

    issue,

    predict,

    model,

    created

    )

    VALUES(?,?,?,?,?)

    """,

    (

        lottery,

        issue,

        ",".join(

            map(
                str,
                numbers
            )

        ),

        model,

        datetime.now().isoformat()

    )

    )


    conn.commit()

    conn.close()




# =========================
# 开奖评估
# =========================


def check_result(

        lottery,

        issue,

        special

):


    conn=sqlite3.connect(

        LEARN_DB

    )


    row=conn.execute(

    """

    SELECT id,predict,model

    FROM prediction_history

    WHERE lottery=?

    AND issue=?

    """,

    (

        lottery,

        issue

    )

    ).fetchone()



    if not row:

        conn.close()

        return False




    nums=[

        int(x)

        for x in row[1].split(",")

    ]



    hit = 1 if special in nums else 0




    conn.execute(

    """

    UPDATE prediction_history

    SET result=?,

    hit=?

    WHERE id=?

    """,

    (

        special,

        hit,

        row[0]

    )

    )



    # 自动调整模型


    adjust_weight(

        row[2],

        hit

    )



    conn.commit()

    conn.close()


    return hit





# =========================
# 权重学习
# =========================


def adjust_weight(

        model,

        hit

):


    conn=sqlite3.connect(

        LEARN_DB

    )


    row=conn.execute(

    """

    SELECT weight

    FROM model_weight

    WHERE model=?

    """,

    (

        model,

    )

    ).fetchone()



    if row:


        w=row[0]


        if hit:


            w +=0.02


        else:


            w -=0.01



        # 限制范围


        w=max(

            0.05,

            min(

                w,

                0.8

            )

        )



        conn.execute(

        """

        UPDATE model_weight

        SET weight=?

        WHERE model=?

        """,

        (

            w,

            model

        )

        )



    conn.commit()

    conn.close()




# =========================
# 获取权重
# =========================


def get_weights():


    conn=sqlite3.connect(

        LEARN_DB

    )


    rows=conn.execute(

    """

    SELECT model,weight

    FROM model_weight

    """

    ).fetchall()


    conn.close()



    return {

        x[0]:

        round(

            x[1],

            3

        )

        for x in rows

    }





__all__=[

    "init_learning",

    "save_prediction",

    "check_result",

    "get_weights"

]
