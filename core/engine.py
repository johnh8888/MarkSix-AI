# core/engine.py
# -*- coding: utf-8 -*-

"""
============================================================
MarkSix-AI
三彩种智能数据分析核心引擎
============================================================

支持：
    香港彩
    新澳门彩
    老澳门彩

核心功能：
    1. 在线数据同步
    2. SQLite 本地存储
    3. 历史开奖统计
    4. 波色分析
    5. 大小分析
    6. 单双分析
    7. 尾数分析
    8. 分区分析
    9. 热冷分析
    10. 频率分析
    11. 综合评分
    12. 下一期候选号码分析

主入口：
    from core.engine import run_system

    run_system()

Python:
    3.11+
============================================================
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import ssl
import urllib.request
import urllib.parse
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# 基础配置
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# 数据库配置
# ============================================================

DB_FILES = {
    "香港彩": os.path.join(DATA_DIR, "hk_macau.db"),
    "新澳门彩": os.path.join(DATA_DIR, "xin_macau.db"),
    "老澳门彩": os.path.join(DATA_DIR, "old_macau.db"),
}


# ============================================================
# API 配置
# ============================================================

API_URLS = [
    "https://api3.marksix6.net/lottery_api.php?type=hk",
    "https://marksix6.net/index.php?api=1",
    "https://marksix6.net/api/lottery_api.php",
]


# ============================================================
# 香港六合彩波色
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
    return "大" if int(number) >= 25 else "小"


def get_odd_even(number: int) -> str:
    return "单" if int(number) % 2 else "双"


def get_tail(number: int) -> int:
    return int(number) % 10


def get_mod7(number: int) -> int:
    return int(number) % 7


def get_zone(number: int) -> int:
    """
    1-49 分成 5 个区域
    """

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
# 输出
# ============================================================

def log(message: str = "") -> None:
    print(message, flush=True)


def separator(char: str = "=", length: int = 70) -> None:
    log(char * length)


# ============================================================
# SQLite
# ============================================================

def get_db_path(lottery: str) -> str:
    return DB_FILES.get(
        lottery,
        os.path.join(
            DATA_DIR,
            "default.db"
        )
    )


def get_connection(lottery: str) -> sqlite3.Connection:
    path = get_db_path(lottery)

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    conn = sqlite3.connect(path)

    conn.row_factory = sqlite3.Row

    return conn


def init_database(lottery: str) -> None:

    conn = get_connection(lottery)

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue TEXT UNIQUE,
                open_time TEXT,
                numbers TEXT NOT NULL,
                source TEXT,
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
            init_database(lottery)
        except Exception as exc:
            log(
                f"[WARN] 初始化 {lottery} 数据库失败：{exc}"
            )


# ============================================================
# 数字清洗
# ============================================================

def clean_numbers(value: Any) -> List[int]:

    if value is None:
        return []

    result: List[int] = []

    if isinstance(value, (list, tuple)):

        for item in value:

            try:
                n = int(item)

                if 1 <= n <= 49:
                    result.append(n)

            except Exception:
                continue

        return result

    text = str(value)

    parts = re.findall(
        r"\d{1,2}",
        text
    )

    for item in parts:

        try:

            n = int(item)

            if 1 <= n <= 49:
                result.append(n)

        except Exception:
            continue

    return result


# ============================================================
# API 请求
# ============================================================

def http_get_json(
    url: str,
    timeout: int = 15,
) -> Optional[Any]:

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/151.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
    }

    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )

    try:

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
                return json.loads(text)

            except json.JSONDecodeError:

                # 有些接口可能返回 JSONP
                text = re.sub(
                    r"^[^(]*\(",
                    "",
                    text,
                )

                text = re.sub(
                    r"\);?\s*$",
                    "",
                    text,
                )

                try:
                    return json.loads(text)
                except Exception:
                    return text

    except Exception as exc:

        log(
            f"[WARN] API 请求失败：{url}"
        )

        log(
            f"[WARN] {exc}"
        )

        return None


# ============================================================
# 从各种 API 格式提取开奖
# ============================================================

def extract_draws(
    payload: Any,
) -> List[Dict[str, Any]]:

    results: List[Dict[str, Any]] = []

    if payload is None:
        return results

    # --------------------------------------------------------
    # 字符串
    # --------------------------------------------------------

    if isinstance(payload, str):

        # 尝试寻找常见 JSON 结构
        try:
            obj = json.loads(payload)

            if obj != payload:
                return extract_draws(obj)

        except Exception:
            pass

        return results

    # --------------------------------------------------------
    # 列表
    # --------------------------------------------------------

    if isinstance(payload, list):

        for item in payload:

            if isinstance(item, dict):

                draw = parse_draw_dict(item)

                if draw:
                    results.append(draw)

        return results

    # --------------------------------------------------------
    # 字典
    # --------------------------------------------------------

    if isinstance(payload, dict):

        direct = parse_draw_dict(payload)

        if direct:
            results.append(direct)

        # 常见列表字段
        for key in (
            "history",
            "data",
            "list",
            "result",
            "records",
            "lottery_data",
            "lotteryData",
        ):

            value = payload.get(key)

            if isinstance(value, list):

                for item in value:

                    if isinstance(item, dict):

                        draw = parse_draw_dict(item)

                        if draw:
                            results.append(draw)

            elif isinstance(value, dict):

                nested = extract_draws(value)

                results.extend(nested)

        # 防止某些接口 data 嵌套
        for value in payload.values():

            if isinstance(value, dict):

                nested = extract_draws(value)

                results.extend(nested)

    # 去重
    unique: Dict[str, Dict[str, Any]] = {}

    for draw in results:

        issue = str(
            draw.get("issue", "")
        ).strip()

        if issue:
            unique[issue] = draw

    return list(unique.values())


# ============================================================
# 解析单期开奖
# ============================================================

def parse_draw_dict(
    item: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

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

    time_keys = [
        "openTime",
        "open_time",
        "drawTime",
        "date",
        "time",
    ]

    issue = None

    for key in issue_keys:

        if key in item:

            value = item.get(key)

            if value is not None:

                issue = str(value).strip()

                if issue:
                    break

    numbers: List[int] = []

    for key in number_keys:

        if key not in item:
            continue

        value = item.get(key)

        numbers = clean_numbers(value)

        if len(numbers) >= 7:
            break

    # 如果 numbers 是嵌套字典
    if len(numbers) < 7:

        for key, value in item.items():

            if isinstance(value, list):

                candidate = clean_numbers(value)

                if len(candidate) >= 7:
                    numbers = candidate
                    break

    if not issue:
        return None

    if len(numbers) < 7:
        return None

    numbers = numbers[:7]

    open_time = ""

    for key in time_keys:

        if key in item:

            value = item.get(key)

            if value is not None:

                open_time = str(value)

                break

    return {
        "issue": issue,
        "open_time": open_time,
        "numbers": numbers,
        "source": "online",
    }


# ============================================================
# 保存开奖
# ============================================================

def save_draws(
    lottery: str,
    draws: List[Dict[str, Any]],
) -> int:

    if not draws:
        return 0

    init_database(lottery)

    conn = get_connection(lottery)

    inserted = 0

    try:

        for draw in draws:

            issue = str(
                draw.get("issue", "")
            ).strip()

            numbers = clean_numbers(
                draw.get("numbers")
            )

            if not issue:
                continue

            if len(numbers) < 7:
                continue

            try:

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
                        str(draw.get("open_time", "")),
                        json.dumps(
                            numbers,
                            ensure_ascii=False,
                        ),
                        str(
                            draw.get(
                                "source",
                                "online",
                            )
                        ),
                        datetime.now().isoformat(),
                    ),
                )

                if cursor.rowcount:
                    inserted += 1

            except Exception as exc:

                log(
                    f"[WARN] 保存 {lottery} "
                    f"{issue} 失败：{exc}"
                )

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

    init_database(lottery)

    conn = get_connection(lottery)

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
            (int(limit),),
        ).fetchall()

    finally:
        conn.close()

    results: List[Dict[str, Any]] = []

    for row in rows:

        try:

            numbers = json.loads(
                row["numbers"]
            )

        except Exception:

            numbers = clean_numbers(
                row["numbers"]
            )

        results.append(
            {
                "issue": row["issue"],
                "open_time": row["open_time"],
                "numbers": numbers,
                "source": row["source"],
            }
        )

    return results


# ============================================================
# 在线同步
# ============================================================

def sync_lottery(
    lottery: str,
) -> Dict[str, Any]:

    log("")
    separator()
    log(f"正在更新：{lottery}")
    separator()

    # --------------------------------------------------------
    # 初始化
    # --------------------------------------------------------

    init_database(lottery)

    total_inserted = 0
    all_draws: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    for index, url in enumerate(API_URLS, start=1):

        log(
            f"[{lottery}] 请求API 第{index}次"
        )

        log(url)

        payload = http_get_json(url)

        if payload is None:
            continue

        draws = extract_draws(payload)

        if not draws:
            log(
                f"[{lottery}] API 未解析到有效开奖数据"
            )
            continue

        log(
            f"[{lottery}] 解析开奖：{len(draws)} 期"
        )

        all_draws.extend(draws)

        # 有有效数据就可以结束
        if draws:
            break

    # --------------------------------------------------------
    # 保存
    # --------------------------------------------------------

    if all_draws:

        # 去重
        unique: Dict[str, Dict[str, Any]] = {}

        for draw in all_draws:

            issue = str(
                draw.get("issue", "")
            )

            if issue:
                unique[issue] = draw

        all_draws = list(
            unique.values()
        )

        total_inserted = save_draws(
            lottery,
            all_draws,
        )

        log(
            f"本次新增：{total_inserted} 期"
        )

    else:

        log(
            f"[{lottery}] 在线数据暂时不可用"
        )

    # --------------------------------------------------------
    # 当前最新
    # --------------------------------------------------------

    history = load_draws(
        lottery,
        limit=1,
    )

    latest_issue = ""

    if history:

        latest_issue = history[0]["issue"]

    log(
        f"最新期：{latest_issue or '暂无'}"
    )

    return {
        "lottery": lottery,
        "parsed": len(all_draws),
        "inserted": total_inserted,
        "latest_issue": latest_issue,
    }


def sync_all() -> Dict[str, Any]:

    results = {}

    for lottery in DB_FILES:

        try:

            results[lottery] = sync_lottery(
                lottery
            )

        except Exception as exc:

            log(
                f"[ERROR] {lottery} 同步失败：{exc}"
            )

            results[lottery] = {
                "lottery": lottery,
                "error": str(exc),
            }

    return results


# ============================================================
# 统计工具
# ============================================================

def flatten_numbers(
    draws: List[Dict[str, Any]],
) -> List[int]:

    result: List[int] = []

    for draw in draws:

        nums = clean_numbers(
            draw.get("numbers")
        )

        result.extend(nums)

    return result


def count_colors(
    numbers: List[int],
) -> Counter:

    counter = Counter()

    for n in numbers:
        counter[get_color(n)] += 1

    return counter


def count_sizes(
    numbers: List[int],
) -> Counter:

    counter = Counter()

    for n in numbers:
        counter[get_size(n)] += 1

    return counter


def count_odd_even(
    numbers: List[int],
) -> Counter:

    counter = Counter()

    for n in numbers:
        counter[get_odd_even(n)] += 1

    return counter


def count_tails(
    numbers: List[int],
) -> Counter:

    counter = Counter()

    for n in numbers:
        counter[get_tail(n)] += 1

    return counter


def count_zones(
    numbers: List[int],
) -> Counter:

    counter = Counter()

    for n in numbers:
        counter[get_zone(n)] += 1

    return counter


# ============================================================
# 最近开奖属性
# ============================================================

def latest_special(
    draws: List[Dict[str, Any]],
) -> Optional[int]:

    if not draws:
        return None

    nums = clean_numbers(
        draws[0].get("numbers")
    )

    if len(nums) < 7:
        return None

    return nums[-1]


# ============================================================
# 热冷号码
# ============================================================

def number_frequency(
    draws: List[Dict[str, Any]],
) -> Counter:

    counter = Counter()

    for draw in draws:

        nums = clean_numbers(
            draw.get("numbers")
        )

        for n in nums:
            counter[n] += 1

    return counter


def get_hot_numbers(
    draws: List[Dict[str, Any]],
    count: int = 10,
) -> List[int]:

    counter = number_frequency(
        draws
    )

    ranked = sorted(
        range(1, 50),
        key=lambda n: (
            -counter[n],
            n,
        ),
    )

    return ranked[:count]


def get_cold_numbers(
    draws: List[Dict[str, Any]],
    count: int = 10,
) -> List[int]:

    counter = number_frequency(
        draws
    )

    ranked = sorted(
        range(1, 50),
        key=lambda n: (
            counter[n],
            n,
        ),
    )

    return ranked[:count]


# ============================================================
# 遗漏值
# ============================================================

def calculate_missing(
    draws: List[Dict[str, Any]],
) -> Dict[int, int]:

    missing = {
        n: 0
        for n in range(1, 50)
    }

    seen = set()

    for distance, draw in enumerate(draws):

        nums = set(
            clean_numbers(
                draw.get("numbers")
            )
        )

        for n in range(1, 50):

            if n in seen:
                continue

            if n in nums:

                seen.add(n)
                missing[n] = distance

    # 从未出现
    max_distance = len(draws)

    for n in range(1, 50):

        if n not in seen:
            missing[n] = max_distance

    return missing


# ============================================================
# 单期属性
# ============================================================

def analyze_draw(
    draw: Dict[str, Any],
) -> Dict[str, Any]:

    nums = clean_numbers(
        draw.get("numbers")
    )

    if len(nums) < 7:

        return {
            "issue": draw.get("issue"),
            "numbers": nums,
        }

    special = nums[-1]

    return {
        "issue": draw.get("issue"),
        "numbers": nums,
        "special": special,
        "color": get_color(special),
        "size": get_size(special),
        "odd_even": get_odd_even(special),
        "tail": get_tail(special),
        "zone": get_zone(special),
    }


# ============================================================
# 属性趋势
# ============================================================

def analyze_special_attributes(
    draws: List[Dict[str, Any]],
) -> Dict[str, Any]:

    special_numbers: List[int] = []

    for draw in draws:

        nums = clean_numbers(
            draw.get("numbers")
        )

        if len(nums) >= 7:
            special_numbers.append(
                nums[-1]
            )

    if not special_numbers:

        return {
            "count": 0
        }

    colors = Counter(
        get_color(n)
        for n in special_numbers
    )

    sizes = Counter(
        get_size(n)
        for n in special_numbers
    )

    odd_even = Counter(
        get_odd_even(n)
        for n in special_numbers
    )

    tails = Counter(
        get_tail(n)
        for n in special_numbers
    )

    zones = Counter(
        get_zone(n)
        for n in special_numbers
    )

    return {
        "count": len(special_numbers),
        "colors": colors,
        "sizes": sizes,
        "odd_even": odd_even,
        "tails": tails,
        "zones": zones,
        "latest": special_numbers[0],
        "latest_color": get_color(
            special_numbers[0]
        ),
        "latest_size": get_size(
            special_numbers[0]
        ),
        "latest_odd_even": get_odd_even(
            special_numbers[0]
        ),
    }


# ============================================================
# 综合号码评分
# ============================================================

def score_numbers(
    draws: List[Dict[str, Any]],
) -> List[Tuple[int, float]]:

    if not draws:
        return []

    recent = draws[:100]

    frequency = number_frequency(
        recent
    )

    missing = calculate_missing(
        recent
    )

    # 最近一期
    latest_numbers = set()

    if recent:

        latest_numbers = set(
            clean_numbers(
                recent[0].get("numbers")
            )
        )

    scores: Dict[int, float] = {}

    for n in range(1, 50):

        freq = frequency.get(n, 0)

        miss = missing.get(n, 0)

        score = 0.0

        # 历史频率
        score += freq * 1.0

        # 适度考虑遗漏
        score += min(
            miss,
            20,
        ) * 0.15

        # 最近一期出现不直接淘汰
        if n in latest_numbers:
            score -= 0.2

        scores[n] = score

    ranked = sorted(
        scores.items(),
        key=lambda x: (
            -x[1],
            x[0],
        ),
    )

    return ranked


# ============================================================
# 候选号码
# ============================================================

def get_candidate_numbers(
    draws: List[Dict[str, Any]],
    count: int = 10,
) -> List[int]:

    ranked = score_numbers(
        draws
    )

    return [
        number
        for number, _score in ranked[:count]
    ]


# ============================================================
# 综合预测
# ============================================================

def build_prediction(
    draws: List[Dict[str, Any]],
) -> Dict[str, Any]:

    if not draws:

        return {
            "available": False,
            "message": "没有历史开奖数据",
        }

    attributes = analyze_special_attributes(
        draws
    )

    ranked = score_numbers(
        draws
    )

    candidates = [
        n
        for n, _score in ranked[:12]
    ]

    hot = get_hot_numbers(
        draws,
        10,
    )

    cold = get_cold_numbers(
        draws,
        10,
    )

    missing = calculate_missing(
        draws
    )

    longest_missing = sorted(
        missing.items(),
        key=lambda x: (
            -x[1],
            x[0],
        ),
    )[:10]

    return {
        "available": True,
        "sample_size": len(draws),
        "latest_issue": draws[0].get(
            "issue"
        ),
        "latest_numbers": draws[0].get(
            "numbers"
        ),
        "candidates": candidates,
        "hot_numbers": hot,
        "cold_numbers": cold,
        "longest_missing": [
            n for n, _ in longest_missing
        ],
        "attributes": attributes,
    }


# ============================================================
# 格式化 Counter
# ============================================================

def format_counter(
    counter: Counter,
) -> str:

    if not counter:
        return "暂无"

    parts = []

    for key, value in counter.most_common():

        parts.append(
            f"{key}:{value}"
        )

    return " ".join(parts)


# ============================================================
# 打印分析结果
# ============================================================

def print_lottery_result(
    lottery: str,
    draws: List[Dict[str, Any]],
    prediction: Dict[str, Any],
) -> None:

    log("")
    separator()

    log(
        f"【{lottery}】"
    )

    separator()

    if not draws:

        log("历史数据：暂无")
        return

    latest = draws[0]

    log(
        f"历史期数：{len(draws)}"
    )

    log(
        f"最新期号：{latest.get('issue', '-')}"
    )

    log(
        f"最新号码："
        f"{latest.get('numbers', [])}"
    )

    special = latest.get(
        "numbers",
        [],
    )

    if special and len(special) >= 7:

        sp = special[-1]

        log("")
        log(
            f"特码：{sp}"
        )

        log(
            f"波色：{get_color(sp)}"
        )

        log(
            f"大小：{get_size(sp)}"
        )

        log(
            f"单双：{get_odd_even(sp)}"
        )

        log(
            f"尾数：{get_tail(sp)}"
        )

        log(
            f"分区：第{get_zone(sp)}区"
        )

    attrs = prediction.get(
        "attributes",
        {},
    )

    if attrs:

        log("")
        log("近期开奖属性统计：")

        log(
            "波色："
            + format_counter(
                attrs.get(
                    "colors",
                    Counter(),
                )
            )
        )

        log(
            "大小："
            + format_counter(
                attrs.get(
                    "sizes",
                    Counter(),
                )
            )
        )

        log(
            "单双："
            + format_counter(
                attrs.get(
                    "odd_even",
                    Counter(),
                )
            )
        )

        log(
            "尾数："
            + format_counter(
                attrs.get(
                    "tails",
                    Counter(),
                )
            )
        )

        log(
            "分区："
            + format_counter(
                attrs.get(
                    "zones",
                    Counter(),
                )
            )
        )

    log("")
    log(
        "高频号码："
        + " ".join(
            f"{n:02d}"
            for n in prediction.get(
                "hot_numbers",
                [],
            )
        )
    )

    log(
        "低频号码："
        + " ".join(
            f"{n:02d}"
            for n in prediction.get(
                "cold_numbers",
                [],
            )
        )
    )

    log(
        "综合候选："
        + " ".join(
            f"{n:02d}"
            for n in prediction.get(
                "candidates",
                [],
            )
        )
    )

    log("")
    log(
        "说明：以上为基于历史数据的统计分析，"
        "不代表实际开奖结果。"
    )


# ============================================================
# 单彩种运行
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
                f"在线同步异常：{exc}"
            )

    draws = load_draws(
        lottery,
        history_limit,
    )

    prediction = build_prediction(
        draws
    )

    print_lottery_result(
        lottery,
        draws,
        prediction,
    )

    return {
        "lottery": lottery,
        "draws": draws,
        "prediction": prediction,
    }


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
        "真实数据 + SQLite + 统计分析版"
    )

    log(
        f"启动时间：{datetime.now().isoformat()}"
    )

    separator()

    # --------------------------------------------------------
    # 初始化数据库
    # --------------------------------------------------------

    init_all_databases()

    # --------------------------------------------------------
    # 三彩种
    # --------------------------------------------------------

    results: Dict[str, Any] = {}

    lotteries = [
        "新澳门彩",
        "老澳门彩",
        "香港彩",
    ]

    for lottery in lotteries:

        try:

            results[lottery] = run_lottery(
                lottery=lottery,
                sync=sync,
                history_limit=history_limit,
            )

        except Exception as exc:

            log("")
            log(
                f"[ERROR] {lottery} 分析失败：{exc}"
            )

            results[lottery] = {
                "lottery": lottery,
                "error": str(exc),
                "draws": [],
                "prediction": {
                    "available": False,
                    "message": str(exc),
                },
            }

    # --------------------------------------------------------
    # 总结
    # --------------------------------------------------------

    log("")
    separator()

    log(
        "三彩种分析完成"
    )

    separator()

    for lottery in lotteries:

        result = results.get(
            lottery,
            {},
        )

        prediction = result.get(
            "prediction",
            {},
        )

        candidates = prediction.get(
            "candidates",
            [],
        )

        log(
            f"{lottery}："
            + (
                " ".join(
                    f"{n:02d}"
                    for n in candidates
                )
                if candidates
                else "暂无候选数据"
            )
        )

    separator()

    log(
        "系统运行结束"
    )

    separator()

    return results


# ============================================================
# 兼容旧调用
# ============================================================

def run(
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:

    return run_system(
        *args,
        **kwargs,
    )


def start(
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:

    return run_system(
        *args,
        **kwargs,
    )


def main(
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:

    return run_system(
        *args,
        **kwargs,
    )


# ============================================================
# 直接运行
# ============================================================

if __name__ == "__main__":

    run_system()
