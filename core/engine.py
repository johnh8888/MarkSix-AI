# core/engine.py
# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
V4.0 FINAL

功能：

1. 三彩种独立 API
2. SQLite 数据库存储
3. 历史开奖读取
4. 统计分析
5. 高频号码
6. 低频号码
7. 遗漏统计
8. 综合候选
9. Walk-Forward 基础回测
10. prediction.json
11. backtest.json
12. module_performance.json

注意：
本程序仅进行历史数据统计与模型实验，
不代表真实中奖概率。
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import ssl
import urllib.request

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# 路径
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

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output",
)

os.makedirs(
    DATA_DIR,
    exist_ok=True,
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True,
)


# ============================================================
# 数据库
# ============================================================

DB_FILES = {

    "新澳门彩":
        os.path.join(
            DATA_DIR,
            "xin_macau.db",
        ),

    "老澳门彩":
        os.path.join(
            DATA_DIR,
            "old_macau.db",
        ),

    "香港彩":
        os.path.join(
            DATA_DIR,
            "hk_macau.db",
        ),
}


# ============================================================
# API
#
# 这里故意只使用 api3。
#
# marksix6.net 主站当前存在过期 SSL 证书，
# 不再作为第一请求地址。
# ============================================================

API_URLS = {

    "新澳门彩": [
        "https://api3.marksix6.net/lottery_api.php?type=newMacau",
    ],

    "老澳门彩": [
        "https://api3.marksix6.net/lottery_api.php?type=oldMacau",
    ],

    "香港彩": [
        "https://api3.marksix6.net/lottery_api.php?type=hk",
    ],
}


# ============================================================
# 波色
# ============================================================

RED_NUMBERS = {
    1, 2, 7, 8, 12, 13, 18, 19,
    23, 24, 29, 30, 34, 35, 40,
    45, 46,
}

BLUE_NUMBERS = {
    3, 4, 9, 10, 14, 15, 20,
    25, 26, 31, 36, 37, 41, 42,
    47, 48,
}

GREEN_NUMBERS = {
    5, 6, 11, 16, 17, 21, 22,
    27, 28, 32, 33, 38, 39, 43,
    44, 49,
}


# ============================================================
# 日志
# ============================================================

def log(message: str = "") -> None:
    print(
        message,
        flush=True,
    )


def separator() -> None:
    log("=" * 70)


# ============================================================
# 基础属性
# ============================================================

def get_color(number: int) -> str:

    number = int(number)

    if number in RED_NUMBERS:
        return "红"

    if number in BLUE_NUMBERS:
        return "蓝"

    if number in GREEN_NUMBERS:
        return "绿"

    return "未知"


def get_size(number: int) -> str:

    return (
        "大"
        if int(number) >= 25
        else "小"
    )


def get_odd_even(number: int) -> str:

    return (
        "单"
        if int(number) % 2
        else "双"
    )


def get_tail(number: int) -> int:

    return int(number) % 10


def get_zone(number: int) -> int:

    number = int(number)

    if 1 <= number <= 10:
        return 1

    if 11 <= number <= 20:
        return 2

    if 21 <= number <= 30:
        return 3

    if 31 <= number <= 40:
        return 4

    if 41 <= number <= 49:
        return 5

    return 0


# ============================================================
# 数据库
# ============================================================

def get_connection(
    lottery: str,
) -> sqlite3.Connection:

    path = DB_FILES[lottery]

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True,
    )

    conn = sqlite3.connect(
        path
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_database(
    lottery: str,
) -> None:

    conn = get_connection(
        lottery
    )

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue TEXT UNIQUE NOT NULL,
                open_time TEXT DEFAULT '',
                numbers TEXT NOT NULL,
                source TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )

        conn.commit()

    finally:

        conn.close()


def init_all_databases() -> None:

    for lottery in DB_FILES:

        try:

            init_database(
                lottery
            )

        except Exception as exc:

            log(
                f"[WARN] 数据库初始化失败："
                f"{lottery} -> {exc}"
            )


# ============================================================
# 数字解析
# ============================================================

def clean_numbers(
    value: Any,
) -> List[int]:

    if value is None:
        return []

    if isinstance(
        value,
        (list, tuple),
    ):

        result = []

        for item in value:

            try:

                number = int(item)

                if 1 <= number <= 49:
                    result.append(
                        number
                    )

            except Exception:
                continue

        return result

    text = str(value)

    result = []

    for item in re.findall(
        r"\d{1,2}",
        text,
    ):

        try:

            number = int(item)

            if 1 <= number <= 49:
                result.append(
                    number
                )

        except Exception:
            continue

    return result


# ============================================================
# HTTP
# ============================================================

def http_get(
    url: str,
    timeout: int = 20,
) -> Optional[Any]:

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "Mozilla/5.0 "
                "MarkSix-AI/4.0",

            "Accept":
                "application/json,"
                "text/plain,"
                "*/*",
        },
        method="GET",
    )

    try:

        # 正常 SSL 验证
        context = ssl.create_default_context()

        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=context,
        ) as response:

            raw = response.read()

            text = raw.decode(
                "utf-8",
                errors="ignore",
            ).strip()

            if not text:
                return None

            try:

                return json.loads(
                    text
                )

            except Exception:

                return text

    except Exception as exc:

        log(
            f"[WARN] 请求失败：{exc}"
        )

        return None


# ============================================================
# API 数据解析
# ============================================================

def parse_draw(
    item: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    issue = ""

    issue_keys = [
        "expect",
        "issue",
        "period",
        "periods",
        "draw",
        "drawNo",
        "draw_number",
        "qihao",
        "qishu",
    ]

    for key in issue_keys:

        if key not in item:
            continue

        value = item.get(key)

        if value is None:
            continue

        value = str(value).strip()

        if value:

            issue = value
            break

    numbers = []

    number_keys = [
        "numbers",
        "number",
        "openCode",
        "open_code",
        "openCodeList",
        "code",
        "result",
        "open_number",
    ]

    for key in number_keys:

        if key not in item:
            continue

        candidate = clean_numbers(
            item.get(key)
        )

        if len(candidate) >= 7:

            numbers = candidate
            break

    if len(numbers) < 7:

        for value in item.values():

            if not isinstance(
                value,
                list,
            ):
                continue

            candidate = clean_numbers(
                value
            )

            if len(candidate) >= 7:

                numbers = candidate
                break

    if not issue:
        return None

    if len(numbers) < 7:
        return None

    open_time = ""

    for key in [
        "openTime",
        "open_time",
        "drawTime",
        "date",
        "time",
    ]:

        if key not in item:
            continue

        value = item.get(key)

        if value is not None:

            open_time = str(
                value
            )

            break

    return {
        "issue": issue,
        "open_time": open_time,
        "numbers": numbers[:7],
    }


def extract_draws(
    payload: Any,
) -> List[Dict[str, Any]]:

    if payload is None:
        return []

    if isinstance(
        payload,
        str,
    ):

        try:

            return extract_draws(
                json.loads(payload)
            )

        except Exception:

            return []

    result = []

    if isinstance(
        payload,
        list,
    ):

        for item in payload:

            if not isinstance(
                item,
                dict,
            ):
                continue

            draw = parse_draw(
                item
            )

            if draw:
                result.append(
                    draw
                )

    elif isinstance(
        payload,
        dict,
    ):

        direct = parse_draw(
            payload
        )

        if direct:
            result.append(
                direct
            )

        keys = [
            "history",
            "data",
            "list",
            "result",
            "records",
            "lottery_data",
            "lotteryData",
        ]

        for key in keys:

            value = payload.get(
                key
            )

            if isinstance(
                value,
                list,
            ):

                for item in value:

                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    draw = parse_draw(
                        item
                    )

                    if draw:
                        result.append(
                            draw
                        )

            elif isinstance(
                value,
                dict,
            ):

                result.extend(
                    extract_draws(
                        value
                    )
                )

    unique = {}

    for draw in result:

        issue = str(
            draw["issue"]
        )

        unique[issue] = draw

    return list(
        unique.values()
    )


# ============================================================
# 保存开奖
# ============================================================

def save_draws(
    lottery: str,
    draws: List[Dict[str, Any]],
    source: str,
) -> int:

    if not draws:
        return 0

    init_database(
        lottery
    )

    conn = get_connection(
        lottery
    )

    inserted = 0

    try:

        for draw in draws:

            issue = str(
                draw.get(
                    "issue",
                    "",
                )
            ).strip()

            numbers = clean_numbers(
                draw.get(
                    "numbers"
                )
            )

            if not issue:
                continue

            if len(numbers) < 7:
                continue

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO draws
                (
                    issue,
                    open_time,
                    numbers,
                    source,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    issue,
                    str(
                        draw.get(
                            "open_time",
                            "",
                        )
                    ),
                    json.dumps(
                        numbers,
                        ensure_ascii=False,
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
# 读取历史
# ============================================================

def load_draws(
    lottery: str,
    limit: int = 500,
) -> List[Dict[str, Any]]:

    init_database(
        lottery
    )

    conn = get_connection(
        lottery
    )

    try:

        rows = conn.execute(
            """
            SELECT
                issue,
                open_time,
                numbers,
                source
            FROM draws
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    finally:

        conn.close()

    result = []

    for row in rows:

        try:

            numbers = json.loads(
                row["numbers"]
            )

        except Exception:

            numbers = clean_numbers(
                row["numbers"]
            )

        result.append(
            {
                "issue":
                    row["issue"],

                "open_time":
                    row["open_time"],

                "numbers":
                    numbers,

                "source":
                    row["source"],
            }
        )

    return result


# ============================================================
# 同步单彩种
# ============================================================

def sync_lottery(
    lottery: str,
) -> Dict[str, Any]:

    log("")
    separator()

    log(
        f"正在更新：{lottery}"
    )

    separator()

    urls = API_URLS.get(
        lottery,
        [],
    )

    all_draws = []
    used_url = ""

    for index, url in enumerate(
        urls,
        start=1,
    ):

        log(
            f"[{lottery}] 请求API "
            f"第{index}次"
        )

        log(url)

        payload = http_get(
            url
        )

        if payload is None:
            continue

        draws = extract_draws(
            payload
        )

        if not draws:

            log(
                f"[{lottery}] "
                f"API没有解析到开奖"
            )

            continue

        log(
            f"[{lottery}] "
            f"解析开奖："
            f"{len(draws)} 期"
        )

        all_draws = draws
        used_url = url

        break

    inserted = 0

    if all_draws:

        inserted = save_draws(
            lottery,
            all_draws,
            used_url,
        )

    history = load_draws(
        lottery,
        1,
    )

    latest_issue = ""

    if history:

        latest_issue = history[0].get(
            "issue",
            "",
        )

    log(
        f"本次新增："
        f"{inserted} 期"
    )

    log(
        f"最新期："
        f"{latest_issue or '暂无'}"
    )

    return {
        "lottery":
            lottery,

        "parsed":
            len(all_draws),

        "inserted":
            inserted,

        "latest_issue":
            latest_issue,

        "source":
            used_url,
    }


# ============================================================
# 统计
# ============================================================

def number_frequency(
    draws: List[Dict[str, Any]],
) -> Counter:

    counter = Counter()

    for draw in draws:

        for number in clean_numbers(
            draw.get("numbers")
        ):

            counter[number] += 1

    return counter


def hot_numbers(
    draws: List[Dict[str, Any]],
    count: int = 10,
) -> List[int]:

    counter = number_frequency(
        draws
    )

    return sorted(
        range(1, 50),
        key=lambda n: (
            -counter[n],
            n,
        ),
    )[:count]


def cold_numbers(
    draws: List[Dict[str, Any]],
    count: int = 10,
) -> List[int]:

    counter = number_frequency(
        draws
    )

    return sorted(
        range(1, 50),
        key=lambda n: (
            counter[n],
            n,
        ),
    )[:count]


def calculate_missing(
    draws: List[Dict[str, Any]],
) -> Dict[int, int]:

    result = {}

    seen = set()

    for distance, draw in enumerate(
        draws
    ):

        numbers = set(
            clean_numbers(
                draw.get("numbers")
            )
        )

        for number in numbers:

            if number not in seen:

                seen.add(
                    number
                )

                result[number] = (
                    distance
                )

    for number in range(
        1,
        50,
    ):

        if number not in seen:

            result[number] = len(
                draws
            )

    return result


# ============================================================
# 综合评分
# ============================================================

def rank_numbers(
    draws: List[Dict[str, Any]],
) -> List[Tuple[int, float]]:

    if not draws:

        return [
            (
                number,
                0.0,
            )
            for number in range(
                1,
                50,
            )
        ]

    recent = draws[:100]

    frequency = number_frequency(
        recent
    )

    missing = calculate_missing(
        recent
    )

    latest = set()

    if recent:

        latest = set(
            clean_numbers(
                recent[0].get(
                    "numbers"
                )
            )
        )

    scores = {}

    for number in range(
        1,
        50,
    ):

        score = 0.0

        # 历史频率
        score += (
            frequency.get(
                number,
                0,
            )
            * 1.0
        )

        # 遗漏
        score += (
            min(
                missing.get(
                    number,
                    0,
                ),
                20,
            )
            * 0.15
        )

        # 最近一期轻微降权
        if number in latest:

            score -= 0.2

        scores[number] = score

    return sorted(
        scores.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )


# ============================================================
# 属性统计
# ============================================================

def analyze_attributes(
    draws: List[Dict[str, Any]],
) -> Dict[str, Any]:

    special_numbers = []

    for draw in draws:

        numbers = clean_numbers(
            draw.get("numbers")
        )

        if len(numbers) >= 7:

            special_numbers.append(
                numbers[-1]
            )

    return {

        "sample_size":
            len(special_numbers),

        "colors":
            dict(
                Counter(
                    get_color(n)
                    for n in special_numbers
                )
            ),

        "sizes":
            dict(
                Counter(
                    get_size(n)
                    for n in special_numbers
                )
            ),

        "odd_even":
            dict(
                Counter(
                    get_odd_even(n)
                    for n in special_numbers
                )
            ),

        "tails":
            dict(
                Counter(
                    get_tail(n)
                    for n in special_numbers
                )
            ),

        "zones":
            dict(
                Counter(
                    get_zone(n)
                    for n in special_numbers
                )
            ),
    }


# ============================================================
# 预测
# ============================================================

def predict(
    draws: List[Dict[str, Any]],
) -> Dict[str, Any]:

    ranked = rank_numbers(
        draws
    )

    candidates = [
        number
        for number, score in ranked[:12]
    ]

    return {

        "candidates":
            candidates,

        "hot_numbers":
            hot_numbers(
                draws,
                10,
            ),

        "cold_numbers":
            cold_numbers(
                draws,
                10,
            ),

        "attributes":
            analyze_attributes(
                draws
            ),
    }


# ============================================================
# Walk Forward
# ============================================================

def walk_forward(
    draws: List[Dict[str, Any]],
    test_size: int = 20,
) -> Dict[str, Any]:

    if len(draws) < 3:

        return {

            "available":
                False,

            "sample_size":
                len(draws),

            "hits":
                0,

            "hit_rate":
                0.0,

            "message":
                "历史数据不足",
        }

    chronological = list(
        reversed(draws)
    )

    start = max(
        1,
        len(chronological)
        - test_size,
    )

    total = 0
    hits = 0

    records = []

    for index in range(
        start,
        len(chronological),
    ):

        train = chronological[
            :index
        ]

        target = chronological[
            index
        ]

        prediction = predict(
            list(
                reversed(train)
            )
        )

        candidates = prediction[
            "candidates"
        ]

        actual = clean_numbers(
            target.get("numbers")
        )

        if len(actual) < 7:
            continue

        special = actual[-1]

        hit = special in candidates

        total += 1

        if hit:
            hits += 1

        records.append(
            {
                "issue":
                    target.get(
                        "issue",
                        "",
                    ),

                "special":
                    special,

                "hit":
                    hit,
            }
        )

    return {

        "available":
            total > 0,

        "sample_size":
            total,

        "hits":
            hits,

        "hit_rate":
            round(
                hits / total,
                4,
            )
            if total
            else 0.0,

        "records":
            records,
    }


# ============================================================
# 格式化
# ============================================================

def format_counter(
    value: Dict[str, Any],
) -> str:

    if not value:
        return "暂无"

    return " ".join(
        f"{key}:{val}"
        for key, val in value.items()
    )


# ============================================================
# 输出单彩种
# ============================================================

def print_lottery(
    lottery: str,
    result: Dict[str, Any],
) -> None:

    log("")
    separator()

    log(
        f"【{lottery}】"
    )

    separator()

    draws = result.get(
        "draws",
        [],
    )

    log(
        f"历史期数："
        f"{len(draws)}"
    )

    if not draws:

        log(
            "暂无历史数据"
        )

        return

    latest = draws[0]

    numbers = clean_numbers(
        latest.get(
            "numbers"
        )
    )

    log(
        f"最新期号："
        f"{latest.get('issue', '')}"
    )

    log(
        f"最新号码："
        f"{numbers}"
    )

    if len(numbers) >= 7:

        special = numbers[-1]

        log(
            f"特码：{special}"
        )

        log(
            f"波色："
            f"{get_color(special)}"
        )

        log(
            f"大小："
            f"{get_size(special)}"
        )

        log(
            f"单双："
            f"{get_odd_even(special)}"
        )

        log(
            f"尾数："
            f"{get_tail(special)}"
        )

        log(
            f"分区："
            f"第{get_zone(special)}区"
        )

    attributes = result.get(
        "attributes",
        {},
    )

    log(
        "近期开奖属性统计："
    )

    log(
        "波色："
        + format_counter(
            attributes.get(
                "colors",
                {},
            )
        )
    )

    log(
        "大小："
        + format_counter(
            attributes.get(
                "sizes",
                {},
            )
        )
    )

    log(
        "单双："
        + format_counter(
            attributes.get(
                "odd_even",
                {},
            )
        )
    )

    log(
        "尾数："
        + format_counter(
            attributes.get(
                "tails",
                {},
            )
        )
    )

    log(
        "分区："
        + format_counter(
            attributes.get(
                "zones",
                {},
            )
        )
    )

    log("")

    log(
        "高频号码："
        + " ".join(
            f"{n:02d}"
            for n in result.get(
                "hot_numbers",
                [],
            )
        )
    )

    log(
        "低频号码："
        + " ".join(
            f"{n:02d}"
            for n in result.get(
                "cold_numbers",
                [],
            )
        )
    )

    log(
        "综合候选："
        + " ".join(
            f"{n:02d}"
            for n in result.get(
                "candidates",
                [],
            )
        )
    )

    log(
        "说明：以上为基于历史数据的统计分析，"
        "不代表实际开奖结果。"
    )


# ============================================================
# 单彩种
# ============================================================

def run_lottery(
    lottery: str,
    sync: bool = True,
    history_limit: int = 500,
) -> Dict[str, Any]:

    if sync:

        try:

            sync_lottery(
                lottery
            )

        except Exception as exc:

            log(
                f"[WARN] {lottery} "
                f"同步失败：{exc}"
            )

    draws = load_draws(
        lottery,
        history_limit,
    )

    prediction = predict(
        draws
    )

    latest_issue = ""

    latest_numbers = []

    if draws:

        latest_issue = str(
            draws[0].get(
                "issue",
                "",
            )
        )

        latest_numbers = clean_numbers(
            draws[0].get(
                "numbers"
            )
        )

    result = {

        "lottery":
            lottery,

        "draws":
            draws,

        "history_size":
            len(draws),

        "latest_issue":
            latest_issue,

        "latest_numbers":
            latest_numbers,

        "candidates":
            prediction[
                "candidates"
            ],

        "hot_numbers":
            prediction[
                "hot_numbers"
            ],

        "cold_numbers":
            prediction[
                "cold_numbers"
            ],

        "attributes":
            prediction[
                "attributes"
            ],
    }

    print_lottery(
        lottery,
        result,
    )

    return result


# ============================================================
# prediction.json
# ============================================================

def write_prediction(
    results: Dict[str, Any],
) -> str:

    payload = {

        "version":
            "V4.0 FINAL",

        "generated_at":
            datetime.now().isoformat(),

        "note":
            "历史统计分析结果，"
            "不代表真实中奖概率。",

        "lotteries":
            {},
    }

    for lottery, result in results.items():

        payload[
            "lotteries"
        ][lottery] = {

            "latest_issue":
                result.get(
                    "latest_issue",
                    "",
                ),

            "latest_numbers":
                result.get(
                    "latest_numbers",
                    [],
                ),

            "history_size":
                result.get(
                    "history_size",
                    0,
                ),

            "candidates":
                result.get(
                    "candidates",
                    [],
                ),

            "hot_numbers":
                result.get(
                    "hot_numbers",
                    [],
                ),

            "cold_numbers":
                result.get(
                    "cold_numbers",
                    [],
                ),

            "attributes":
                result.get(
                    "attributes",
                    {},
                ),
        }

    path = os.path.join(
        OUTPUT_DIR,
        "prediction.json",
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return path


# ============================================================
# backtest.json
# ============================================================

def write_backtest(
    results: Dict[str, Any],
) -> str:

    payload = {

        "version":
            "V4.0 FINAL",

        "generated_at":
            datetime.now().isoformat(),

        "method":
            "Walk-Forward",

        "lotteries":
            {},
    }

    for lottery, result in results.items():

        draws = result.get(
            "draws",
            [],
        )

        payload[
            "lotteries"
        ][lottery] = {

            "test10":
                walk_forward(
                    draws,
                    10,
                ),

            "test20":
                walk_forward(
                    draws,
                    20,
                ),
        }

    path = os.path.join(
        OUTPUT_DIR,
        "backtest.json",
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return path


# ============================================================
# module_performance.json
# ============================================================

def write_module_performance(
    results: Dict[str, Any],
) -> str:

    payload = {

        "version":
            "V4.0 FINAL",

        "generated_at":
            datetime.now().isoformat(),

        "modules": {

            "frequency":
                {
                    "enabled":
                        True,
                    "weight":
                        1.0,
                },

            "missing":
                {
                    "enabled":
                        True,
                    "weight":
                        0.15,
                },

            "recent_penalty":
                {
                    "enabled":
                        True,
                    "weight":
                        -0.2,
                },

            "color":
                {
                    "enabled":
                        True,
                },

            "size":
                {
                    "enabled":
                        True,
                },

            "odd_even":
                {
                    "enabled":
                        True,
                },

            "tail":
                {
                    "enabled":
                        True,
                },

            "zone":
                {
                    "enabled":
                        True,
                },
        },

        "lotteries":
            {},
    }

    for lottery, result in results.items():

        payload[
            "lotteries"
        ][lottery] = {

            "history_size":
                result.get(
                    "history_size",
                    0,
                ),

            "status":
                (
                    "ok"
                    if result.get(
                        "history_size",
                        0,
                    ) > 0
                    else "no_data"
                ),
        }

    path = os.path.join(
        OUTPUT_DIR,
        "module_performance.json",
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return path


# ============================================================
# 最终输出检查
# ============================================================

def verify_output_files() -> bool:

    required = [

        os.path.join(
            OUTPUT_DIR,
            "prediction.json",
        ),

        os.path.join(
            OUTPUT_DIR,
            "backtest.json",
        ),

        os.path.join(
            OUTPUT_DIR,
            "module_performance.json",
        ),
    ]

    success = True

    for path in required:

        if not os.path.isfile(path):

            log(
                f"❌ 文件不存在："
                f"{path}"
            )

            success = False

            continue

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(
                    file
                )

            if not isinstance(
                data,
                dict,
            ):

                log(
                    f"❌ JSON结构错误："
                    f"{path}"
                )

                success = False

                continue

            size = os.path.getsize(
                path
            )

            log(
                f"✅ {path} "
                f"({size} bytes)"
            )

        except Exception as exc:

            log(
                f"❌ JSON读取失败："
                f"{path} -> {exc}"
            )

            success = False

    return success


# ============================================================
# 主系统
# ============================================================

def run_system(
    sync: bool = True,
    data: Any = None,
    auto_sync: Optional[bool] = None,
    history_limit: int = 500,
    **kwargs: Any,
) -> Dict[str, Any]:

    if auto_sync is not None:

        sync = auto_sync

    log("")
    separator()

    log(
        "六合彩综合预测系统"
    )

    log(
        "真实数据 + SQLite + "
        "统计分析 + 输出文件版"
    )

    log(
        f"启动时间："
        f"{datetime.now().isoformat()}"
    )

    separator()

    init_all_databases()

    lotteries = [

        "新澳门彩",

        "老澳门彩",

        "香港彩",
    ]

    results = {}

    for lottery in lotteries:

        try:

            results[
                lottery
            ] = run_lottery(

                lottery,

                sync=sync,

                history_limit=
                    history_limit,
            )

        except Exception as exc:

            log("")
            log(
                f"[ERROR] "
                f"{lottery}分析失败："
                f"{exc}"
            )

            results[
                lottery
            ] = {

                "lottery":
                    lottery,

                "draws":
                    [],

                "history_size":
                    0,

                "latest_issue":
                    "",

                "latest_numbers":
                    [],

                "candidates":
                    [],

                "hot_numbers":
                    [],

                "cold_numbers":
                    [],

                "attributes":
                    {},

                "error":
                    str(exc),
            }

    # ========================================================
    # 输出
    # ========================================================

    log("")
    separator()

    log(
        "保存预测结果"
    )

    separator()

    prediction_path = (
        write_prediction(
            results
        )
    )

    log(
        f"✅ 预测结果已保存："
        f"{prediction_path}"
    )

    log("")
    separator()

    log(
        "保存 Walk-Forward 回测"
    )

    separator()

    backtest_path = (
        write_backtest(
            results
        )
    )

    log(
        f"✅ 回测结果已保存："
        f"{backtest_path}"
    )

    log("")
    separator()

    log(
        "保存模块表现"
    )

    separator()

    performance_path = (
        write_module_performance(
            results
        )
    )

    log(
        f"✅ 模块表现已保存："
        f"{performance_path}"
    )

    # ========================================================
    # 检查
    # ========================================================

    log("")
    separator()

    log(
        "输出文件检查"
    )

    separator()

    output_ok = verify_output_files()

    if not output_ok:

        raise RuntimeError(
            "输出文件检查失败"
        )

    # ========================================================
    # 汇总
    # ========================================================

    log("")
    separator()

    log(
        "三彩种分析完成"
    )

    separator()

    for lottery in lotteries:

        candidates = results[
            lottery
        ].get(
            "candidates",
            [],
        )

        formatted = " ".join(
            f"{n:02d}"
            for n in candidates
        )

        log(
            f"{lottery}："
            f"{formatted}"
        )

    log("")
    log(
        "说明：候选号码来自历史统计评分，"
        "不代表真实中奖概率。"
    )

    separator()

    log(
        "系统运行结束"
    )

    separator()

    return results


# ============================================================
# 兼容旧版本
# ============================================================

def run(
    *args,
    **kwargs,
):

    return run_system(
        *args,
        **kwargs,
    )


def start(
    *args,
    **kwargs,
):

    return run_system(
        *args,
        **kwargs,
    )


def main(
    *args,
    **kwargs,
):

    return run_system(
        *args,
        **kwargs,
    )


# ============================================================
# 直接运行
# ============================================================

if __name__ == "__main__":

    run_system()
