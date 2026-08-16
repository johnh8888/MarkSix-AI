# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
SQLite 数据库模块

功能：

1. 初始化 SQLite
2. 插入开奖
3. 更新开奖
4. 查询历史
5. 标准化开奖数据
6. 获取特码
7. 获取最新一期
8. 三彩种独立数据
9. 兼容旧数据库
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import Any, Dict, List, Optional

from core.config import DB_FILE


# =========================================================
# 数据库连接
# =========================================================

def get_connection() -> sqlite3.Connection:
    """
    创建 SQLite 连接。
    """

    DB_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(
        str(DB_FILE),
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    # 提高并发稳定性
    try:
        conn.execute(
            "PRAGMA journal_mode=WAL"
        )

        conn.execute(
            "PRAGMA busy_timeout=30000"
        )

    except Exception:
        pass

    return conn


# =========================================================
# 初始化数据库
# =========================================================

def init_database() -> None:

    DB_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        # -------------------------------------------------
        # 开奖数据
        # -------------------------------------------------

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

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(lottery, issue)

            )
            """
        )

        # -------------------------------------------------
        # 索引
        # -------------------------------------------------

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


# =========================================================
# 安全转整数
# =========================================================

def safe_int(value: Any) -> Optional[int]:

    try:

        return int(
            str(value).strip()
        )

    except (
        TypeError,
        ValueError
    ):

        return None


# =========================================================
# numbers 解析
# =========================================================

def parse_numbers(
    value: Any
) -> List[int]:

    """
    统一解析开奖号码。

    支持：

    "33,27,16,28,04,25,14"

    ["33","27","16","28","04","25","14"]

    [33,27,16,28,4,25,14]

    "[33,27,16,28,4,25,14]"

    "33 27 16 28 04 25 14"

    "33|27|16|28|04|25|14"
    """

    if value is None:
        return []

    # -----------------------------------------------------
    # list / tuple
    # -----------------------------------------------------

    if isinstance(
        value,
        (list, tuple)
    ):

        result = []

        for item in value:

            number = safe_int(item)

            if number is not None:

                if 1 <= number <= 49:

                    result.append(number)

        return result

    # -----------------------------------------------------
    # JSON
    # -----------------------------------------------------

    if isinstance(
        value,
        str
    ):

        text = value.strip()

        if not text:
            return []

        if text.startswith("["):

            try:

                parsed = json.loads(text)

                return parse_numbers(
                    parsed
                )

            except Exception:
                pass

        # -------------------------------------------------
        # 统一分隔符
        # -------------------------------------------------

        replacements = {

            "，": ",",
            "|": ",",
            "、": ",",
            ";": ",",
            "；": ",",
            "\t": ",",
            "\n": ",",
            "\r": ",",
        }

        for old, new in replacements.items():

            text = text.replace(
                old,
                new
            )

        # 空格也作为分隔
        text = text.replace(
            " ",
            ","
        )

        parts = [
            item.strip()
            for item in text.split(",")
            if item.strip()
        ]

        result = []

        for item in parts:

            number = safe_int(item)

            if number is not None:

                if 1 <= number <= 49:

                    result.append(number)

        return result

    return []


# =========================================================
# 获取特码
# =========================================================

def get_special_from_numbers(
    numbers: Any
) -> Optional[int]:

    parsed = parse_numbers(
        numbers
    )

    if len(parsed) >= 7:

        return parsed[-1]

    return None


# =========================================================
# 标准化字符串列表
# =========================================================

def parse_string_list(
    value: Any
) -> List[str]:

    if value is None:
        return []

    # -----------------------------------------------------
    # list / tuple
    # -----------------------------------------------------

    if isinstance(
        value,
        (list, tuple)
    ):

        result = []

        for item in value:

            text = str(
                item
            ).strip()

            if text:

                result.append(
                    text
                )

        return result

    # -----------------------------------------------------
    # JSON 数组
    # -----------------------------------------------------

    if isinstance(
        value,
        str
    ):

        text = value.strip()

        if not text:
            return []

        if text.startswith("["):

            try:

                parsed = json.loads(
                    text
                )

                return parse_string_list(
                    parsed
                )

            except Exception:
                pass

        for symbol in (
            "，",
            "|",
            "、",
            ";",
            "；"
        ):

            text = text.replace(
                symbol,
                ","
            )

        parts = [
            item.strip()
            for item in text.split(",")
            if item.strip()
        ]

        # -------------------------------------------------
        # 如果没有逗号，尝试空格
        # -------------------------------------------------

        if len(parts) == 1:

            parts = [
                item.strip()
                for item in text.split()
                if item.strip()
            ]

        return parts

    return []


# =========================================================
# 标准化 issue
# =========================================================

def normalize_issue(
    value: Any
) -> str:

    if value is None:
        return ""

    return str(
        value
    ).strip()


# =========================================================
# 期号排序辅助
# =========================================================

def issue_sort_key(
    issue: Any
) -> tuple:

    """
    尽量兼容：

    123
    "123"
    "2026123"
    "2026-123"
    """

    text = normalize_issue(
        issue
    )

    digits = "".join(
        ch
        for ch in text
        if ch.isdigit()
    )

    if digits:

        try:

            return (
                1,
                int(digits),
                text
            )

        except Exception:
            pass

    return (
        0,
        0,
        text
    )


# =========================================================
# 标准化数据库记录
# =========================================================

def normalize_draw(
    row: Dict[str, Any]
) -> Dict[str, Any]:

    result = dict(row)

    # -----------------------------------------------------
    # issue
    # -----------------------------------------------------

    result["issue"] = normalize_issue(
        result.get("issue")
    )

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

    result["openCode"] = ",".join(
        f"{number:02d}"
        for number in numbers
    )

    # -----------------------------------------------------
    # 生肖
    # -----------------------------------------------------

    zodiacs = parse_string_list(
        result.get("zodiac")
    )

    result["zodiac"] = zodiacs

    # -----------------------------------------------------
    # 特码生肖
    # -----------------------------------------------------

    if zodiacs:

        result["special_zodiac"] = (
            zodiacs[-1]
        )

    else:

        result["special_zodiac"] = None

    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    waves = parse_string_list(
        result.get("wave")
    )

    result["wave"] = waves

    # -----------------------------------------------------
    # 特码波色
    # -----------------------------------------------------

    if waves:

        result["special_wave"] = (
            waves[-1]
        )

    else:

        result["special_wave"] = None

    return result


# =========================================================
# 插入开奖
# =========================================================

def insert_draw(
    lottery: str,
    name: str,
    issue: str,
    numbers: Any,
    open_time: Optional[str] = None,
    zodiac: Optional[Any] = None,
    wave: Optional[Any] = None,
    source: Optional[str] = None,
) -> bool:

    lottery = str(
        lottery or ""
    ).strip()

    issue = normalize_issue(
        issue
    )

    if not lottery or not issue:

        return False

    numbers_text = (
        json.dumps(
            parse_numbers(numbers),
            ensure_ascii=False
        )
    )

    zodiac_text = (
        json.dumps(
            parse_string_list(zodiac),
            ensure_ascii=False
        )
        if zodiac is not None
        else None
    )

    wave_text = (
        json.dumps(
            parse_string_list(wave),
            ensure_ascii=False
        )
        if wave is not None
        else None
    )

    with closing(get_connection()) as conn:

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
                numbers_text,
                zodiac_text,
                wave_text,
                source,
            )
        )

        inserted = (
            cursor.rowcount > 0
        )

        conn.commit()

    return inserted


# =========================================================
# 更新 / 插入
# =========================================================

def upsert_draw(
    lottery: str,
    name: str,
    issue: str,
    numbers: Any,
    open_time: Optional[str] = None,
    zodiac: Optional[Any] = None,
    wave: Optional[Any] = None,
    source: Optional[str] = None,
) -> bool:

    lottery = str(
        lottery or ""
    ).strip()

    issue = normalize_issue(
        issue
    )

    if not lottery or not issue:

        return False

    numbers_text = json.dumps(
        parse_numbers(numbers),
        ensure_ascii=False
    )

    zodiac_text = (
        json.dumps(
            parse_string_list(zodiac),
            ensure_ascii=False
        )
        if zodiac is not None
        else None
    )

    wave_text = (
        json.dumps(
            parse_string_list(wave),
            ensure_ascii=False
        )
        if wave is not None
        else None
    )

    with closing(get_connection()) as conn:

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
                issue
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
                    numbers_text,
                    zodiac_text,
                    wave_text,
                    source,
                    lottery,
                    issue,
                )
            )

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
                    numbers_text,
                    zodiac_text,
                    wave_text,
                    source,
                )
            )

        conn.commit()

    return True


# =========================================================
# 获取指定彩种历史
# =========================================================

def get_draws(
    lottery: str,
    limit: int = 3000
) -> List[Dict[str, Any]]:

    limit = max(
        1,
        int(limit)
    )

    with closing(get_connection()) as conn:

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
                id DESC

            LIMIT ?

            """,

            (
                lottery,
                limit
            )
        )

        rows = cursor.fetchall()

    result = [
        normalize_draw(
            dict(row)
        )
        for row in rows
    ]

    # -----------------------------------------------------
    # 数据库返回顺序：
    #
    # 最新 → 最旧
    #
    # 预测器使用这个顺序。
    # -----------------------------------------------------

    return result


# =========================================================
# 获取全部数据
# =========================================================

def get_all_draws(
    limit: int = 3000
) -> List[Dict[str, Any]]:

    limit = max(
        1,
        int(limit)
    )

    with closing(get_connection()) as conn:

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
                id DESC

            LIMIT ?

            """,

            (
                limit,
            )
        )

        rows = cursor.fetchall()

    return [
        normalize_draw(
            dict(row)
        )
        for row in rows
    ]


# =========================================================
# 获取全部历史并按彩种分组
# =========================================================

def get_draws_grouped(
    limit: int = 3000
) -> Dict[str, List[Dict[str, Any]]]:

    rows = get_all_draws(
        limit
    )

    grouped = {}

    for row in rows:

        lottery = row.get(
            "lottery"
        )

        if lottery not in grouped:

            grouped[lottery] = []

        grouped[lottery].append(
            row
        )

    return grouped


# =========================================================
# 统计指定彩种
# =========================================================

def count_draws(
    lottery: str
) -> int:

    with closing(get_connection()) as conn:

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

        result = cursor.fetchone()

    if not result:

        return 0

    return int(
        result[0]
    )


# =========================================================
# 统计全部彩种
# =========================================================

def count_all_draws() -> List[Dict[str, Any]]:

    with closing(get_connection()) as conn:

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

    return [

        {
            "lottery":
                row[0],

            "name":
                row[1],

            "count":
                int(row[2]),
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
# 获取最近 N 期
# =========================================================

def get_recent_draws(
    lottery: str,
    limit: int
) -> List[Dict[str, Any]]:

    return get_draws(
        lottery,
        limit
    )


# =========================================================
# 删除指定彩种
# =========================================================

def clear_lottery(
    lottery: str
) -> None:

    with closing(get_connection()) as conn:

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


# =========================================================
# 删除全部数据
# =========================================================

def clear_database() -> None:

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM draws
            """
        )

        conn.commit()


# =========================================================
# 数据库状态
# =========================================================

def database_status() -> Dict[str, Any]:

    return {

        "database":
            str(DB_FILE),

        "exists":
            DB_FILE.exists(),

        "lotteries":
            count_all_draws(),

    }


# =========================================================
# 数据质量检查
# =========================================================

def validate_draw(
    draw: Dict[str, Any]
) -> Dict[str, Any]:

    numbers = parse_numbers(
        draw.get("numbers")
    )

    errors = []

    warnings = []

    # -----------------------------------------------------
    # 号码数量
    # -----------------------------------------------------

    if len(numbers) != 7:

        errors.append(
            f"号码数量异常：{len(numbers)}"
        )

    # -----------------------------------------------------
    # 范围
    # -----------------------------------------------------

    invalid_numbers = [
        number
        for number in numbers
        if not 1 <= number <= 49
    ]

    if invalid_numbers:

        errors.append(
            f"号码超出范围：{invalid_numbers}"
        )

    # -----------------------------------------------------
    # 重复
    # -----------------------------------------------------

    if len(numbers) != len(set(numbers)):

        errors.append(
            "开奖号码存在重复"
        )

    # -----------------------------------------------------
    # 特码
    # -----------------------------------------------------

    special = (
        numbers[-1]
        if numbers
        else None
    )

    if special is None:

        warnings.append(
            "无法识别特码"
        )

    return {

        "valid":
            len(errors) == 0,

        "errors":
            errors,

        "warnings":
            warnings,

        "numbers":
            numbers,

        "special":
            special,

    }


# =========================================================
# 数据库测试
# =========================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "六合彩 AI V3.0 SQLite 数据库测试"
    )

    print("=" * 70)

    init_database()

    print()

    print(
        "数据库：",
        DB_FILE
    )

    print()

    print(
        "数据库状态："
    )

    print(
        json.dumps(
            database_status(),
            ensure_ascii=False,
            indent=2
        )
    )

    # -----------------------------------------------------
    # 三彩种
    # -----------------------------------------------------

    for lottery in (
        "hk",
        "newMacau",
        "oldMacau"
    ):

        print()

        print(
            "-" * 70
        )

        print(
            lottery,
            "最新开奖"
        )

        print(
            "-" * 70
        )

        try:

            row = get_latest_draw(
                lottery
            )

            if not row:

                print(
                    "暂无数据"
                )

                continue

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

            print(
                "生肖：",
                row.get("zodiac")
            )

            print(
                "波色：",
                row.get("wave")
            )

            print(
                "数据源：",
                row.get("source")
            )

            validation = validate_draw(
                row
            )

            print(
                "数据有效：",
                validation["valid"]
            )

            if validation["errors"]:

                print(
                    "错误：",
                    validation["errors"]
                )

            if validation["warnings"]:

                print(
                    "警告：",
                    validation["warnings"]
                )

        except Exception as e:

            print(
                f"{lottery} 测试失败：",
                repr(e)
            )

    print()

    print("=" * 70)

    print(
        "数据库测试完成"
    )

    print("=" * 70)