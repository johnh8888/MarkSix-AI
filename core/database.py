# -*- coding: utf-8 -*-

import sqlite3
import json
from typing import Any, Dict, List, Optional

from core.config import DB_FILE


# =========================================================
# 数据库连接
# =========================================================

def get_connection():

    conn = sqlite3.connect(
        DB_FILE,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# 初始化数据库
# =========================================================

def init_database():

    DB_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = get_connection()

    cursor = conn.cursor()

    # -----------------------------------------------------
    # 开奖数据表
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS draws (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            lottery TEXT NOT NULL,

            name TEXT,

            issue TEXT NOT NULL,

            open_time TEXT,

            numbers TEXT,

            zodiac TEXT,

            wave TEXT,

            source TEXT,

            created_at TEXT,

            UNIQUE(lottery, issue)

        )
        """
    )

    # -----------------------------------------------------
    # 索引
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_draws_lottery_issue
        ON draws(lottery, issue)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_draws_lottery
        ON draws(lottery)
        """
    )

    conn.commit()

    conn.close()


# =========================================================
# numbers 解析
# =========================================================

def parse_numbers(value) -> List[int]:

    """
    将数据库中的 numbers 统一转换为：

        [33, 27, 16, 28, 4, 25, 14]

    支持：

        "33,27,16,28,04,25,14"

        ["33", "27", "16", "28", "04", "25", "14"]

        "[33,27,16,28,4,25,14]"
    """

    if value is None:
        return []

    # -----------------------------------------------------
    # 已经是 list / tuple
    # -----------------------------------------------------

    if isinstance(value, (list, tuple)):

        result = []

        for item in value:

            try:

                number = int(str(item).strip())

                if 1 <= number <= 49:
                    result.append(number)

            except (
                TypeError,
                ValueError
            ):
                continue

        return result

    # -----------------------------------------------------
    # 字符串
    # -----------------------------------------------------

    if isinstance(value, str):

        text = value.strip()

        if not text:
            return []

        # ---------------------------------------------
        # JSON 数组
        # ---------------------------------------------

        if text.startswith("["):

            try:

                data = json.loads(text)

                return parse_numbers(data)

            except Exception:
                pass

        # ---------------------------------------------
        # 逗号 / 空格 / | 分隔
        # ---------------------------------------------

        text = (
            text
            .replace("，", ",")
            .replace("|", ",")
            .replace(" ", ",")
        )

        parts = [
            x.strip()
            for x in text.split(",")
            if x.strip()
        ]

        result = []

        for item in parts:

            try:

                number = int(item)

                if 1 <= number <= 49:
                    result.append(number)

            except (
                TypeError,
                ValueError
            ):
                continue

        return result

    return []


# =========================================================
# 获取特码
# =========================================================

def get_special_from_numbers(
    numbers
) -> Optional[int]:

    parsed = parse_numbers(numbers)

    if len(parsed) >= 7:

        return parsed[-1]

    return None


# =========================================================
# 插入开奖数据
# =========================================================

def insert_draw(
    lottery: str,
    name: str,
    issue: str,
    numbers: str,
    open_time: Optional[str] = None,
    zodiac: Optional[str] = None,
    wave: Optional[str] = None,
    source: Optional[str] = None,
) -> bool:

    if not lottery:
        return False

    if not issue:
        return False

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO draws (

            lottery,
            name,
            issue,
            open_time,
            numbers,
            zodiac,
            wave,
            source,
            created_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))

        """,

        (
            lottery,
            name,
            issue,
            open_time,
            numbers,
            zodiac,
            wave,
            source,
        )
    )

    inserted = (
        cursor.rowcount > 0
    )

    conn.commit()

    conn.close()

    return inserted


# =========================================================
# 更新开奖数据
# =========================================================

def upsert_draw(
    lottery: str,
    name: str,
    issue: str,
    numbers: str,
    open_time: Optional[str] = None,
    zodiac: Optional[str] = None,
    wave: Optional[str] = None,
    source: Optional[str] = None,
) -> bool:

    if not lottery:
        return False

    if not issue:
        return False

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM draws
        WHERE lottery = ?
        AND issue = ?
        LIMIT 1
        """,

        (
            lottery,
            issue,
        )
    )

    existing = cursor.fetchone()

    if existing:

        cursor.execute(
            """
            UPDATE draws

            SET

                name = ?,
                open_time = ?,
                numbers = ?,
                zodiac = ?,
                wave = ?,
                source = ?

            WHERE lottery = ?
            AND issue = ?

            """,

            (
                name,
                open_time,
                numbers,
                zodiac,
                wave,
                source,
                lottery,
                issue,
            )
        )

        changed = True

    else:

        cursor.execute(
            """
            INSERT INTO draws (

                lottery,
                name,
                issue,
                open_time,
                numbers,
                zodiac,
                wave,
                source,
                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))

            """,

            (
                lottery,
                name,
                issue,
                open_time,
                numbers,
                zodiac,
                wave,
                source,
            )
        )

        changed = True

    conn.commit()

    conn.close()

    return changed


# =========================================================
# 标准化数据库记录
# =========================================================

def normalize_draw(
    row: Dict[str, Any]
) -> Dict[str, Any]:

    """
    将 SQLite 原始记录转换成预测器统一格式。

    原始数据库：

        numbers = "33,27,16,28,04,25,14"

    输出：

        numbers = [33,27,16,28,4,25,14]
        special = 14

    同时保留原始字段。
    """

    result = dict(row)

    # -----------------------------------------------------
    # numbers
    # -----------------------------------------------------

    numbers = parse_numbers(
        result.get("numbers")
    )

    result["numbers"] = numbers

    # -----------------------------------------------------
    # special
    # -----------------------------------------------------

    special = get_special_from_numbers(
        numbers
    )

    result["special"] = special

    # -----------------------------------------------------
    # openCode
    # -----------------------------------------------------

    if numbers:

        result["openCode"] = ",".join(
            f"{n:02d}"
            for n in numbers
        )

    else:

        result["openCode"] = ""

    # -----------------------------------------------------
    # 生肖
    # -----------------------------------------------------

    zodiac = result.get("zodiac")

    if isinstance(zodiac, str):

        result["zodiac"] = [
            x.strip()
            for x in zodiac
            .replace("，", ",")
            .split(",")
            if x.strip()
        ]

    elif zodiac is None:

        result["zodiac"] = []

    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    wave = result.get("wave")

    if isinstance(wave, str):

        result["wave"] = [
            x.strip()
            for x in wave
            .replace("，", ",")
            .split(",")
            if x.strip()
        ]

    elif wave is None:

        result["wave"] = []

    return result


# =========================================================
# 获取指定彩种历史
# =========================================================

def get_draws(
    lottery: str,
    limit: int = 3000
) -> List[Dict[str, Any]]:

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            id,
            lottery,
            name,
            issue,
            open_time,
            numbers,
            zodiac,
            wave,
            source,
            created_at

        FROM draws

        WHERE lottery = ?

        ORDER BY

            CAST(issue AS INTEGER) DESC

        LIMIT ?

        """,

        (
            lottery,
            limit,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        normalize_draw(
            dict(row)
        )
        for row in rows
    ]


# =========================================================
# 获取全部数据
# =========================================================

def get_all_draws(
    limit: int = 3000
) -> List[Dict[str, Any]]:

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            id,
            lottery,
            name,
            issue,
            open_time,
            numbers,
            zodiac,
            wave,
            source,
            created_at

        FROM draws

        ORDER BY

            lottery,

            CAST(issue AS INTEGER) DESC

        LIMIT ?

        """,

        (
            limit,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        normalize_draw(
            dict(row)
        )
        for row in rows
    ]


# =========================================================
# 统计指定彩种
# =========================================================

def count_draws(
    lottery: str
) -> int:

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM draws
        WHERE lottery = ?
        """,

        (
            lottery,
        )
    )

    result = cursor.fetchone()[0]

    conn.close()

    return int(result)


# =========================================================
# 统计全部彩种
# =========================================================

def count_all_draws():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            lottery,
            name,
            COUNT(*)

        FROM draws

        GROUP BY

            lottery,
            name

        ORDER BY lottery
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return [

        {
            "lottery":
                row[0],

            "name":
                row[1],

            "count":
                row[2],
        }

        for row in rows
    ]


# =========================================================
# 获取最新一期
# =========================================================

def get_latest_draw(
    lottery: str
) -> Optional[Dict[str, Any]]:

    rows = get_draws(
        lottery,
        limit=1
    )

    if not rows:
        return None

    return rows[0]


# =========================================================
# 删除指定彩种
# =========================================================

def clear_lottery(
    lottery: str
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM draws
        WHERE lottery = ?
        """,

        (
            lottery,
        )
    )

    conn.commit()

    conn.close()


# =========================================================
# 数据库状态
# =========================================================

def database_status():

    return {

        "database":
            str(DB_FILE),

        "lotteries":
            count_all_draws(),
    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    init_database()

    print(
        "=" * 70
    )

    print(
        "SQLite 数据库测试"
    )

    print(
        "=" * 70
    )

    print(
        database_status()
    )

    # -----------------------------------------------------
    # 测试最新三彩种
    # -----------------------------------------------------

    for lottery in (
        "hk",
        "newMacau",
        "oldMacau"
    ):

        try:

            row = get_latest_draw(
                lottery
            )

            if row:

                print()
                print(
                    f"{lottery} 最新记录"
                )

                print(
                    "期号：",
                    row.get("issue")
                )

                print(
                    "号码：",
                    row.get("numbers")
                )

                print(
                    "特码：",
                    row.get("special")
                )

                print(
                    "openCode：",
                    row.get("openCode")
                )

        except Exception as e:

            print(
                f"{lottery} 测试失败：",
                repr(e)
            )
