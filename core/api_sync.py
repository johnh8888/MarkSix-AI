# core/api_sync.py
# -*- coding: utf-8 -*-

"""
六合彩 AI
API 数据同步模块

V6.1 REAL DATA FIXED

功能：

1. 获取新澳门彩
2. 获取老澳门彩
3. 获取香港彩
4. 自动处理主 API SSL 证书问题
5. 自动切换备用 API
6. 兼容多种 API JSON 格式
7. 防止 API 数据被第二次空解析覆盖
8. 保存 SQLite
9. 返回统一历史数据结构
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import ssl
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen


# ============================================================
# 基础路径
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
)

os.makedirs(
    DATA_DIR,
    exist_ok=True,
)


# ============================================================
# 数据库
# ============================================================

DB_FILES = {
    "新澳门彩": "new_macau.db",
    "老澳门彩": "old_macau.db",
    "香港彩": "hk_macau.db",
}


# ============================================================
# API 类型
# ============================================================

API_TYPES = {
    "新澳门彩": "newMacau",
    "老澳门彩": "oldMacau",
    "香港彩": "hk",
}


# ============================================================
# API 地址
# ============================================================

PRIMARY_API = (
    "https://marksix6.net/api/lottery_api.php"
)

BACKUP_API = (
    "https://api3.marksix6.net/lottery_api.php"
)


# ============================================================
# SSL
# ============================================================

# 主站证书过期时，不影响备用 API。
# 这里使用普通 SSL context。
# 如果备用 API 自身证书正常，则正常验证。
SSL_CONTEXT = ssl.create_default_context()


# ============================================================
# 日志
# ============================================================

def log(message: str = "") -> None:
    print(message, flush=True)


# ============================================================
# 数据库路径
# ============================================================

def get_db_path(
    lottery_name: str,
) -> str:

    filename = DB_FILES.get(
        lottery_name,
        f"{lottery_name}.db",
    )

    return os.path.join(
        DATA_DIR,
        filename,
    )


# ============================================================
# 数据库初始化
# ============================================================

def init_db(
    lottery_name: str,
) -> str:

    path = get_db_path(
        lottery_name
    )

    conn = sqlite3.connect(path)

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue TEXT UNIQUE NOT NULL,
                numbers TEXT NOT NULL,
                open_time TEXT,
                source TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.commit()

    finally:
        conn.close()

    return path


# ============================================================
# 清理期号
# ============================================================

def normalize_issue(
    value: Any,
) -> str:

    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    # 纯数字
    match = re.search(
        r"\d+",
        text,
    )

    if match:
        return match.group(0)

    return text


# ============================================================
# 清理号码
# ============================================================

def normalize_numbers(
    value: Any,
) -> List[int]:

    result: List[int] = []

    if value is None:
        return result

    # --------------------------------------------------------
    # list / tuple
    # --------------------------------------------------------

    if isinstance(
        value,
        (list, tuple),
    ):

        for item in value:

            try:

                if isinstance(
                    item,
                    dict,
                ):
                    for key in (
                        "number",
                        "num",
                        "value",
                        "openCode",
                    ):
                        if key in item:
                            item = item[key]
                            break

                number = int(
                    str(item).strip()
                )

                if 1 <= number <= 49:
                    result.append(number)

            except Exception:
                continue

        return result

    # --------------------------------------------------------
    # 字符串
    # --------------------------------------------------------

    text = str(value)

    parts = re.findall(
        r"\d{1,2}",
        text,
    )

    for part in parts:

        try:

            number = int(part)

            if 1 <= number <= 49:
                result.append(number)

        except Exception:
            continue

    return result


# ============================================================
# 找字段
# ============================================================

def first_value(
    obj: Dict[str, Any],
    keys: List[str],
) -> Any:

    for key in keys:

        if key in obj:

            value = obj[key]

            if value is not None:
                return value

    return None


# ============================================================
# 递归寻找开奖记录
# ============================================================

def find_draw_records(
    obj: Any,
) -> List[Dict[str, Any]]:

    records: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # dict
    # --------------------------------------------------------

    if isinstance(
        obj,
        dict,
    ):

        # 判断当前对象是不是开奖记录
        issue = first_value(
            obj,
            [
                "expect",
                "issue",
                "issueNo",
                "issue_no",
                "period",
                "qihao",
                "期号",
            ],
        )

        numbers = first_value(
            obj,
            [
                "numbers",
                "number",
                "openCode",
                "open_code",
                "code",
                "codes",
                "开奖号码",
            ],
        )

        normalized_numbers = normalize_numbers(
            numbers
        )

        if (
            issue is not None
            and len(normalized_numbers) >= 6
        ):

            record = dict(obj)

            record["_issue"] = normalize_issue(
                issue
            )

            record["_numbers"] = (
                normalized_numbers[:7]
            )

            records.append(record)

        # 继续递归
        for value in obj.values():

            records.extend(
                find_draw_records(value)
            )

        return records

    # --------------------------------------------------------
    # list
    # --------------------------------------------------------

    if isinstance(
        obj,
        list,
    ):

        for item in obj:

            records.extend(
                find_draw_records(item)
            )

    return records


# ============================================================
# JSON 解析
# ============================================================

def parse_api_response(
    text: str,
) -> List[Dict[str, Any]]:

    text = text.strip()

    if not text:
        return []

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    try:

        data = json.loads(text)

        records = find_draw_records(
            data
        )

        # 去重
        return deduplicate_records(
            records
        )

    except Exception:
        pass

    # --------------------------------------------------------
    # 某些接口可能返回 JSONP
    # --------------------------------------------------------

    match = re.search(
        r"\{.*\}",
        text,
        re.S,
    )

    if match:

        try:

            data = json.loads(
                match.group(0)
            )

            records = find_draw_records(
                data
            )

            return deduplicate_records(
                records
            )

        except Exception:
            pass

    return []


# ============================================================
# 去重
# ============================================================

def deduplicate_records(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    result: Dict[str, Dict[str, Any]] = {}

    for record in records:

        issue = record.get(
            "_issue",
            "",
        )

        numbers = record.get(
            "_numbers",
            [],
        )

        if not issue:
            continue

        if len(numbers) < 6:
            continue

        result[issue] = record

    # 按期号排序
    def issue_key(item):
        try:
            return int(
                item[0]
            )
        except Exception:
            return 0

    ordered = sorted(
        result.items(),
        key=issue_key,
    )

    return [
        item[1]
        for item in ordered
    ]


# ============================================================
# HTTP 请求
# ============================================================

def request_api(
    url: str,
    timeout: int = 15,
) -> Optional[str]:

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "Chrome/120 Safari/537.36"
            ),
            "Accept": (
                "application/json,text/plain,*/*"
            ),
        },
    )

    try:

        with urlopen(
            request,
            timeout=timeout,
            context=SSL_CONTEXT,
        ) as response:

            raw = response.read()

            return raw.decode(
                "utf-8",
                errors="ignore",
            )

    except Exception as exc:

        log(
            f"[WARN] 请求失败：{exc}"
        )

        return None


# ============================================================
# 获取 API
# ============================================================

def fetch_lottery(
    lottery_name: str,
) -> List[Dict[str, Any]]:

    api_type = API_TYPES.get(
        lottery_name,
        "hk",
    )

    log(
        f"[{lottery_name}] API类型：{api_type}"
    )

    urls = [
        (
            f"{PRIMARY_API}"
            f"?type={quote(api_type)}"
        ),
        (
            f"{BACKUP_API}"
            f"?type={quote(api_type)}"
        ),
    ]

    for index, url in enumerate(
        urls,
        start=1,
    ):

        log(
            f"[{lottery_name}] 请求API 第{index}次"
        )

        log(url)

        text = request_api(
            url
        )

        if not text:
            continue

        records = parse_api_response(
            text
        )

        log(
            f"[{lottery_name}] "
            f"API解析得到：{len(records)} 期"
        )

        # ====================================================
        # 关键修复
        #
        # 如果第一次 API 成功得到数据，
        # 后面绝对不能因为另一个解析结果为空而覆盖。
        # ====================================================

        if records:

            return records

    return []


# ============================================================
# 从数据库读取
# ============================================================

def load_history(
    lottery_name: str,
) -> List[Dict[str, Any]]:

    path = init_db(
        lottery_name
    )

    conn = sqlite3.connect(
        path
    )

    try:

        rows = conn.execute(
            """
            SELECT
                issue,
                numbers,
                open_time,
                source
            FROM draws
            ORDER BY
                CAST(issue AS INTEGER) ASC
            """
        ).fetchall()

    finally:
        conn.close()

    result = []

    for issue, numbers, open_time, source in rows:

        try:
            nums = json.loads(
                numbers
            )
        except Exception:
            nums = normalize_numbers(
                numbers
            )

        result.append(
            {
                "issue": str(issue),
                "numbers": nums,
                "open_time": open_time,
                "source": source,
            }
        )

    return result


# ============================================================
# 保存记录
# ============================================================

def save_records(
    lottery_name: str,
    records: List[Dict[str, Any]],
) -> int:

    path = init_db(
        lottery_name
    )

    conn = sqlite3.connect(
        path
    )

    inserted = 0

    try:

        for record in records:

            issue = record.get(
                "_issue",
                "",
            )

            numbers = record.get(
                "_numbers",
                [],
            )

            if not issue:
                continue

            if len(numbers) < 6:
                continue

            open_time = first_value(
                record,
                [
                    "openTime",
                    "open_time",
                    "date",
                    "time",
                ],
            )

            source = "api3.marksix6.net"

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO draws
                (
                    issue,
                    numbers,
                    open_time,
                    source,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    issue,
                    json.dumps(
                        numbers,
                        ensure_ascii=False,
                    ),
                    str(
                        open_time or ""
                    ),
                    source,
                    datetime.now().isoformat(),
                ),
            )

            if cursor.rowcount > 0:
                inserted += 1

        conn.commit()

    finally:
        conn.close()

    return inserted


# ============================================================
# 同步一个彩种
# ============================================================

def sync_lottery(
    lottery_name: str,
) -> Dict[str, Any]:

    log("=" * 70)
    log(
        f"正在更新：{lottery_name}"
    )
    log("=" * 70)

    # 先初始化数据库
    init_db(
        lottery_name
    )

    # API
    records = fetch_lottery(
        lottery_name
    )

    # --------------------------------------------------------
    # 关键：
    # API 为空时，不删除数据库已有历史
    # --------------------------------------------------------

    inserted = 0

    if records:

        inserted = save_records(
            lottery_name,
            records,
        )

    else:

        log(
            f"[{lottery_name}] "
            "API没有返回有效记录，保留本地历史数据。"
        )

    history = load_history(
        lottery_name
    )

    log(
        f"[{lottery_name}] 本次新增："
        f"{inserted} 期"
    )

    log(
        f"[{lottery_name}] 当前数据库历史："
        f"{len(history)} 期"
    )

    return {
        "lottery": lottery_name,
        "api_records": records,
        "inserted": inserted,
        "history": history,
        "db_path": get_db_path(
            lottery_name
        ),
    }


# ============================================================
# 同步全部
# ============================================================

def sync_all() -> Dict[str, Any]:

    result = {}

    for lottery_name in (
        "新澳门彩",
        "老澳门彩",
        "香港彩",
    ):

        try:

            result[lottery_name] = (
                sync_lottery(
                    lottery_name
                )
            )

        except Exception as exc:

            log(
                f"[ERROR] "
                f"{lottery_name}同步失败：{exc}"
            )

            result[lottery_name] = {
                "lottery": lottery_name,
                "api_records": [],
                "inserted": 0,
                "history": load_history(
                    lottery_name
                ),
                "error": str(exc),
            }

    return result


# ============================================================
# 兼容旧名称
# ============================================================

def sync_data():
    return sync_all()


def update_all():
    return sync_all()


def run_sync():
    return sync_all()


def fetch_and_save(
    lottery_name: Optional[str] = None,
):

    if lottery_name:
        return sync_lottery(
            lottery_name
        )

    return sync_all()


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":

    result = sync_all()

    print()
    print("=" * 70)
    print("API同步测试完成")
    print("=" * 70)

    for name, item in result.items():

        history = item.get(
            "history",
            [],
        )

        print(
            f"{name}：{len(history)}期"
        )
