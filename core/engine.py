# core/engine.py
# -*- coding: utf-8 -*-

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
# 基础路径
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 三彩种数据库
# ============================================================

DB_FILES = {
    "香港彩": os.path.join(DATA_DIR, "hk_macau.db"),
    "新澳门彩": os.path.join(DATA_DIR, "xin_macau.db"),
    "老澳门彩": os.path.join(DATA_DIR, "old_macau.db"),
}


# ============================================================
# 三彩种 API
# ============================================================

API_URLS = {
    "香港彩": [
        "https://marksix6.net/api/lottery_api.php?type=hk",
        "https://api3.marksix6.net/lottery_api.php?type=hk",
    ],

    "新澳门彩": [
        "https://marksix6.net/api/lottery_api.php?type=newMacau",
        "https://api3.marksix6.net/lottery_api.php?type=newMacau",
    ],

    "老澳门彩": [
        "https://marksix6.net/api/lottery_api.php?type=oldMacau",
        "https://api3.marksix6.net/lottery_api.php?type=oldMacau",
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
# 日志
# ============================================================

def log(message: str = "") -> None:
    print(message, flush=True)


def separator(char: str = "=", length: int = 70) -> None:
    log(char * length)


# ============================================================
# 数据库
# ============================================================

def get_db_path(lottery: str) -> str:
    return DB_FILES[lottery]


def get_connection(lottery: str):

    path = get_db_path(lottery)

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True,
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
                f"[WARN] 初始化数据库失败："
                f"{lottery}: {exc}"
            )


# ============================================================
# 数字清洗
# ============================================================

def clean_numbers(value: Any) -> List[int]:

    if value is None:
        return []

    if isinstance(value, (list, tuple)):

        result = []

        for x in value:

            try:

                n = int(x)

                if 1 <= n <= 49:
                    result.append(n)

            except Exception:
                pass

        return result

    text = str(value)

    result = []

    for x in re.findall(
        r"\d{1,2}",
        text,
    ):

        try:

            n = int(x)

            if 1 <= n <= 49:
                result.append(n)

        except Exception:
            pass

    return result


# ============================================================
# HTTP
# ============================================================

def http_get(
    url: str,
    timeout: int = 20,
) -> Optional[Any]:

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "MarkSix-AI/4.0"
        ),
        "Accept": (
            "application/json,"
            "text/plain,"
            "*/*"
        ),
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
            except Exception:
                return text

    except Exception as exc:

        log(
            f"[WARN] 请求失败：{exc}"
        )

        return None


# ============================================================
# 解析开奖记录
# ============================================================

def parse_draw_dict(
    item: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    issue = None

    for key in (
        "expect",
        "issue",
        "period",
        "periods",
        "draw",
        "drawNo",
        "draw_number",
        "qihao",
        "qishu",
    ):

        if key in item:

            value = item.get(key)

            if value is not None:

                value = str(value).strip()

                if value:
                    issue = value
                    break

    numbers = []

    for key in (
        "numbers",
        "number",
        "openCode",
        "open_code",
        "openCodeList",
        "code",
        "result",
        "open_number",
    ):

        if key in item:

            numbers = clean_numbers(
                item.get(key)
            )

            if len(numbers) >= 7:
                break

    if len(numbers) < 7:

        for value in item.values():

            if isinstance(value, list):

                candidate = clean_numbers(
                    value
                )

                if len(candidate) >= 7:

                    numbers = candidate
                    break

    if not issue or len(numbers) < 7:
        return None

    open_time = ""

    for key in (
        "openTime",
        "open_time",
        "drawTime",
        "date",
        "time",
    ):

        if key in item:

            value = item.get(key)

            if value is not None:

                open_time = str(value)
                break

    return {
        "issue": issue,
        "open_time": open_time,
        "numbers": numbers[:7],
    }


def extract_draws(
    payload: Any,
) -> List[Dict[str, Any]]:

    results = []

    if payload is None:
        return results

    if isinstance(payload, str):

        try:
            obj = json.loads(payload)
            return extract_draws(obj)
        except Exception:
            return results

    if isinstance(payload, list):

        for item in payload:

            if isinstance(item, dict):

                draw = parse_draw_dict(item)

                if draw:
                    results.append(draw)

        return deduplicate_draws(results)

    if isinstance(payload, dict):

        direct = parse_draw_dict(payload)

        if direct:
            results.append(direct)

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

                results.extend(
                    extract_draws(value)
                )

    return deduplicate_draws(results)


def deduplicate_draws(
    draws: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    unique = {}

    for draw in draws:

        issue = str(
            draw.get("issue", "")
        ).strip()

        if issue:
            unique[issue] = draw

    return list(unique.values())


# ============================================================
# 保存数据
# ============================================================

def save_draws(
    lottery: str,
    draws: List[Dict[str, Any]],
    source: str,
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

            if not issue or len(numbers) < 7:
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

            if cursor.rowcount:
                inserted += 1

        conn.commit()

    finally:
        conn.close()

    return inserted


# ============================================================
# 读取数据
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
                "issue": row["issue"],
                "open_time": row["open_time"],
                "numbers": numbers,
                "source": row["source"],
            }
        )

    return result


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

        payload = http_get(url)

        if payload is None:
            continue

        draws = extract_draws(
            payload
        )

        if not draws:

            log(
                f"[{lottery}] "
                f"没有解析到有效开奖"
            )

            continue

        log(
            f"[{lottery}] "
            f"解析开奖：{len(draws)} 期"
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

    else:

        log(
            f"[{lottery}] "
            f"在线数据暂不可用，"
            f"继续使用本地数据库"
        )

    history = load_draws(
        lottery,
        1,
    )

    latest_issue = ""

    if history:
        latest_issue = history[0]["issue"]

    log(
        f"本次新增：{inserted} 期"
    )

    log(
        f"最新期："
        f"{latest_issue or '暂无'}"
    )

    return {
        "lottery": lottery,
        "parsed": len(all_draws),
        "inserted": inserted,
        "latest_issue": latest_issue,
        "source": used_url,
    }


# ============================================================
# 频率
# ============================================================

def number_frequency(
    draws: List[Dict[str, Any]],
) -> Counter:

    counter = Counter()

    for draw in draws:

        numbers = clean_numbers(
            draw.get("numbers")
        )

        for n in numbers:
            counter[n] += 1

    return counter


def get_hot_numbers(
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


def get_cold_numbers(
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


# ============================================================
# 遗漏
# ============================================================

def calculate_missing(
    draws: List[Dict[str, Any]],
) -> Dict[int, int]:

    missing = {}

    seen = set()

    for distance, draw in enumerate(draws):

        numbers = set(
            clean_numbers(
                draw.get("numbers")
            )
        )

        for n in numbers:

            if n not in seen:

                seen.add(n)
                missing[n] = distance

    for n in range(1, 50):

        if n not in seen:

            missing[n] = len(draws)

    return missing


# ============================================================
# 评分
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

    for n in range(1, 50):

        score = 0.0

        # 历史频率
        score += frequency.get(
            n,
            0,
        ) * 1.0

        # 遗漏
        score += min(
            missing.get(n, 0),
            20,
        ) * 0.15

        # 最近一期适度降权
        if n in latest:
            score -= 0.2

        scores[n] = score

    return sorted(
        scores.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )


# ============================================================
# 属性分析
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
        "sample_size": len(
            special_numbers
        ),
        "colors": dict(colors),
        "sizes": dict(sizes),
        "odd_even": dict(odd_even),
        "tails": dict(tails),
        "zones": dict(zones),
    }


# ============================================================
# 单期预测评分
# ============================================================

def predict_from_history(
    draws: List[Dict[str, Any]],
) -> Dict[str, Any]:

    ranked = score_numbers(
        draws
    )

    candidates = [
        n
        for n, _score in ranked[:12]
    ]

    return {
        "candidates": candidates,
        "hot_numbers": get_hot_numbers(
            draws,
            10,
        ),
        "cold_numbers": get_cold_numbers(
            draws,
            10,
        ),
        "attributes": analyze_attributes(
            draws
        ),
    }


# ============================================================
# Walk-Forward
# ============================================================

def walk_forward(
    draws: List[Dict[str, Any]],
    window: int = 10,
) -> Dict[str, Any]:

    if len(draws) < window + 1:

        return {
            "window": window,
            "available": False,
            "sample_size": len(draws),
            "message": (
                "历史数据不足，"
                "无法进行Walk-Forward"
            ),
        }

    # 数据按最新在前
    chronological = list(
        reversed(draws)
    )

    total = 0
    hits = 0

    records = []

    start = max(
        1,
        len(chronological) - window,
    )

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

        prediction = predict_from_history(
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

        if not actual:
            continue

        special = actual[-1]

        hit = special in candidates

        total += 1

        if hit:
            hits += 1

        records.append(
            {
                "issue": target.get(
                    "issue"
                ),
                "special": special,
                "hit": hit,
            }
        )

    rate = (
        hits / total
        if total
        else 0.0
    )

    return {
        "window": window,
        "available": total > 0,
        "sample_size": total,
        "hits": hits,
        "hit_rate": round(
            rate,
            4,
        ),
        "records": records,
    }


# ============================================================
# 生成 prediction.json
# ============================================================

def build_prediction_payload(
    all_results: Dict[str, Any],
) -> Dict[str, Any]:

    lotteries = {}

    for lottery, result in all_results.items():

        lotteries[lottery] = {
            "latest_issue": result.get(
                "latest_issue"
            ),
            "latest_numbers": result.get(
                "latest_numbers",
                [],
            ),
            "history_size": result.get(
                "history_size",
                0,
            ),
            "candidates": result.get(
                "candidates",
                [],
            ),
            "hot_numbers": result.get(
                "hot_numbers",
                [],
            ),
            "cold_numbers": result.get(
                "cold_numbers",
                [],
            ),
            "attributes": result.get(
                "attributes",
                {},
            ),
        }

    return {
        "version": "V4.0",
        "generated_at": datetime.now().isoformat(),
        "note": (
            "模型评分仅用于历史数据排序和分析，"
            "不代表真实中奖概率。"
        ),
        "lotteries": lotteries,
    }


def save_prediction(
    payload: Dict[str, Any],
) -> str:

    path = os.path.join(
        OUTPUT_DIR,
        "prediction.json",
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            payload,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return path


# ============================================================
# 生成 backtest.json
# ============================================================

def save_backtest(
    all_results: Dict[str, Any],
) -> str:

    payload = {
        "version": "V4.0",
        "generated_at": datetime.now().isoformat(),
        "windows": [10, 20],
        "note": (
            "Walk-Forward只使用目标期之前的数据。"
        ),
        "lotteries": {},
    }

    for lottery, result in all_results.items():

        draws = result.get(
            "draws",
            [],
        )

        payload["lotteries"][lottery] = {
            "recent10": walk_forward(
                draws,
                10,
            ),
            "recent20": walk_forward(
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
    ) as f:

        json.dump(
            payload,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return path


# ============================================================
# module_performance.json
# ============================================================

def save_module_performance(
    all_results: Dict[str, Any],
) -> str:

    payload = {
        "version": "V4.0",
        "generated_at": datetime.now().isoformat(),
        "modules": {
            "frequency": {
                "enabled": True,
                "weight": 1.0,
            },
            "missing": {
                "enabled": True,
                "weight": 0.15,
            },
            "recent_penalty": {
                "enabled": True,
                "weight": -0.2,
            },
            "color": {
                "enabled": True,
            },
            "size": {
                "enabled": True,
            },
            "odd_even": {
                "enabled": True,
            },
            "tail": {
                "enabled": True,
            },
            "zone": {
                "enabled": True,
            },
        },
        "lotteries": {},
    }

    for lottery, result in all_results.items():

        payload["lotteries"][lottery] = {
            "history_size": result.get(
                "history_size",
                0,
            ),
            "status": (
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
    ) as f:

        json.dump(
            payload,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return path


# ============================================================
# 打印结果
# ============================================================

def print_result(
    lottery: str,
    result: Dict[str, Any],
) -> None:

    separator()

    log(
        f"【{lottery}】"
    )

    separator()

    draws = result.get(
        "draws",
        [],
    )

    if not draws:

        log("历史数据：暂无")
        return

    latest = draws[0]

    log(
        f"历史期数：{len(draws)}"
    )

    log(
        f"最新期号："
        f"{latest.get('issue', '-')}"
    )

    log(
        f"最新号码："
        f"{latest.get('numbers', [])}"
    )

    numbers = clean_numbers(
        latest.get("numbers")
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

    log("")

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


def format_counter(
    value: Any,
) -> str:

    if not value:
        return "暂无"

    if isinstance(
        value,
        Counter,
    ):
        value = dict(value)

    if isinstance(
        value,
        dict,
    ):

        return " ".join(
            f"{k}:{v}"
            for k, v in sorted(
                value.items(),
                key=lambda x: (
                    -x[1]
                    if isinstance(
                        x[1],
                        (int, float),
                    )
                    else 0
                ),
            )
        )

    return str(value)


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
                f"[WARN] 同步异常："
                f"{lottery}: {exc}"
            )

    draws = load_draws(
        lottery,
        history_limit,
    )

    prediction = predict_from_history(
        draws
    )

    latest_issue = ""
    latest_numbers = []

    if draws:

        latest_issue = draws[0].get(
            "issue",
            "",
        )

        latest_numbers = clean_numbers(
            draws[0].get(
                "numbers"
            )
        )

    result = {
        "lottery": lottery,
        "draws": draws,
        "history_size": len(draws),
        "latest_issue": latest_issue,
        "latest_numbers": latest_numbers,
        "candidates": prediction.get(
            "candidates",
            [],
        ),
        "hot_numbers": prediction.get(
            "hot_numbers",
            [],
        ),
        "cold_numbers": prediction.get(
            "cold_numbers",
            [],
        ),
        "attributes": prediction.get(
            "attributes",
            {},
        ),
    }

    print_result(
        lottery,
        result,
    )

    return result


# ============================================================
# 主入口
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

            results[lottery] = run_lottery(
                lottery,
                sync=sync,
                history_limit=history_limit,
            )

        except Exception as exc:

            log("")
            log(
                f"[ERROR] {lottery}："
                f"{exc}"
            )

            results[lottery] = {
                "lottery": lottery,
                "draws": [],
                "history_size": 0,
                "latest_issue": "",
                "latest_numbers": [],
                "candidates": [],
                "hot_numbers": [],
                "cold_numbers": [],
                "attributes": {},
                "error": str(exc),
            }

    # ========================================================
    # 保存三个核心输出
    # ========================================================

    log("")
    separator()
    log("保存预测结果")
    separator()

    prediction_payload = (
        build_prediction_payload(
            results
        )
    )

    prediction_path = save_prediction(
        prediction_payload
    )

    log(
        f"✅ 预测结果已保存："
        f"{prediction_path}"
    )

    log("")
    separator()
    log("保存 Walk-Forward 回测")
    separator()

    backtest_path = save_backtest(
        results
    )

    log(
        f"✅ 回测结果已保存："
        f"{backtest_path}"
    )

    log("")
    separator()
    log("保存模块表现")
    separator()

    performance_path = (
        save_module_performance(
            results
        )
    )

    log(
        f"✅ 模块表现已保存："
        f"{performance_path}"
    )

    # ========================================================
    # 最终检查
    # ========================================================

    required_files = [
        prediction_path,
        backtest_path,
        performance_path,
    ]

    log("")
    separator()
    log("输出文件检查")
    separator()

    for path in required_files:

        if os.path.isfile(path):

            size = os.path.getsize(path)

            log(
                f"✅ {path} "
                f"({size} bytes)"
            )

        else:

            log(
                f"❌ 缺少：{path}"
            )

    # ========================================================
    # 汇总
    # ========================================================

    log("")
    separator()
    log("三彩种分析完成")
    separator()

    for lottery in lotteries:

        candidates = results[
            lottery
        ].get(
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

    log("系统运行结束")

    separator()

    return results


# ============================================================
# 兼容旧入口
# ============================================================

def run(*args, **kwargs):
    return run_system(
        *args,
        **kwargs,
    )


def start(*args, **kwargs):
    return run_system(
        *args,
        **kwargs,
    )


def main(*args, **kwargs):
    return run_system(
        *args,
        **kwargs,
    )


# ============================================================
# 直接运行
# ============================================================

if __name__ == "__main__":
    run_system()
