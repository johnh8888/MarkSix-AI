# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
V5.0 REAL DATA FINAL

核心功能：

1. 三彩种统一运行
2. 新澳门彩
3. 老澳门彩
4. 香港彩
5. API真实数据
6. SSL异常自动备用API
7. API历史数据深度解析
8. SQLite历史数据
9. 自动去重
10. 历史数据累计
11. 号码频率统计
12. 热号
13. 冷号
14. 遗漏
15. 波色
16. 大小
17. 单双
18. 尾数
19. 分区
20. 号码综合评分
21. Walk-Forward基础回测
22. 模块表现
23. prediction.json
24. backtest.json
25. module_performance.json

设计原则：

- 不依赖 requests
- 不依赖 pandas
- 不依赖 numpy
- Python 3.11+ 可以直接运行
- API失败不直接导致程序退出
- 主API SSL异常自动切备用API
- API只有最新一期时保留SQLite旧历史
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import ssl
import statistics
import time
import traceback
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# ============================================================
# 基础路径
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CORE_DIR = os.path.join(
    BASE_DIR,
    "core",
)

DB_DIR = os.path.join(
    BASE_DIR,
    "data",
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output",
)

os.makedirs(
    DB_DIR,
    exist_ok=True,
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True,
)


# ============================================================
# 配置
# ============================================================

VERSION = "V5.0 REAL DATA FINAL"

MAX_HISTORY = 1000

REQUEST_TIMEOUT = 15

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; MarkSix-AI/5.0; Python)"
)


LOTTERIES = {

    "新澳门彩": {

        "type": "newMacau",

        "db": "new_macau.db",

    },

    "老澳门彩": {

        "type": "oldMacau",

        "db": "old_macau.db",

    },

    "香港彩": {

        "type": "hk",

        "db": "hk.db",

    },
}


# ============================================================
# API地址
# ============================================================

API_URLS = [

    "https://marksix6.net/api/lottery_api.php",

    "https://api3.marksix6.net/lottery_api.php",

    "http://marksix6.net/api/lottery_api.php",

    "http://api3.marksix6.net/lottery_api.php",

]


# ============================================================
# 波色
# ============================================================

RED = {

    1, 2, 7, 8, 12, 13,
    18, 19, 23, 24,
    29, 30, 34, 35,
    40, 45, 46,
}

BLUE = {

    3, 4, 9, 10, 14,
    15, 20, 25, 26,
    31, 36, 37, 41,
    42, 47, 48,
}

GREEN = {

    5, 6, 11, 16, 17,
    21, 22, 27, 28,
    32, 33, 38, 39,
    43, 44, 49,
}


# ============================================================
# 日志
# ============================================================

def log(
    message: str = "",
) -> None:

    print(
        message,
        flush=True,
    )


# ============================================================
# 数字处理
# ============================================================

def clean_numbers(
    value: Any,
) -> List[int]:

    result: List[int] = []

    if value is None:
        return result

    if isinstance(
        value,
        str,
    ):

        text = value

        found = re.findall(
            r"\d{1,2}",
            text,
        )

        for item in found:

            try:

                n = int(item)

                if 1 <= n <= 49:
                    result.append(n)

            except Exception:
                pass

        return result

    if isinstance(
        value,
        (list, tuple),
    ):

        for item in value:

            if isinstance(
                item,
                dict,
            ):

                for key in (
                    "number",
                    "num",
                    "value",
                    "openCode",
                    "code",
                ):

                    if key in item:

                        result.extend(
                            clean_numbers(
                                item[key]
                            )
                        )

                        break

            elif isinstance(
                item,
                (int, float),
            ):

                n = int(item)

                if 1 <= n <= 49:
                    result.append(n)

            elif isinstance(
                item,
                str,
            ):

                result.extend(
                    clean_numbers(
                        item
                    )
                )

        return result

    if isinstance(
        value,
        dict,
    ):

        for key in (
            "numbers",
            "number",
            "openCode",
            "opencode",
            "open_code",
            "code",
            "balls",
            "result",
        ):

            if key in value:

                result.extend(
                    clean_numbers(
                        value[key]
                    )
                )

                if len(result) >= 7:
                    break

        return result

    if isinstance(
        value,
        (int, float),
    ):

        n = int(value)

        if 1 <= n <= 49:
            return [n]

    return result


def normalize_numbers(
    numbers: List[int],
) -> List[int]:

    result = []

    for n in numbers:

        try:

            n = int(n)

        except Exception:
            continue

        if 1 <= n <= 49:

            result.append(n)

    # 保留开奖顺序，但去掉重复
    unique = []

    seen = set()

    for n in result:

        if n not in seen:

            seen.add(n)
            unique.append(n)

    return unique[:7]


# ============================================================
# 属性
# ============================================================

def get_color(
    number: int,
) -> str:

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return "未知"


def get_size(
    number: int,
) -> str:

    return (
        "大"
        if number >= 25
        else "小"
    )


def get_odd_even(
    number: int,
) -> str:

    return (
        "单"
        if number % 2
        else "双"
    )


def get_tail(
    number: int,
) -> int:

    return number % 10


def get_zone(
    number: int,
) -> int:

    if number <= 10:
        return 1

    if number <= 20:
        return 2

    if number <= 30:
        return 3

    if number <= 40:
        return 4

    return 5


# ============================================================
# SQLite
# ============================================================

def get_db_path(
    lottery: str,
) -> str:

    config = LOTTERIES[
        lottery
    ]

    return os.path.join(
        DB_DIR,
        config["db"],
    )


def get_connection(
    lottery: str,
) -> sqlite3.Connection:

    path = get_db_path(
        lottery
    )

    conn = sqlite3.connect(
        path
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue TEXT UNIQUE NOT NULL,
            open_time TEXT,
            numbers TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()

    return conn


# ============================================================
# API开奖结构解析
# ============================================================

def parse_draw(
    obj: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    if not isinstance(
        obj,
        dict,
    ):
        return None

    issue = None

    issue_keys = [

        "expect",

        "issue",

        "period",

        "periods",

        "draw",

        "drawNo",

        "drawNumber",

        "issueNo",

        "lotteryNo",

        "qihao",

        "qishu",
    ]

    for key in issue_keys:

        if key in obj:

            value = obj.get(
                key
            )

            if value is not None:

                text = str(
                    value
                ).strip()

                if text:

                    issue = text

                    break

    if not issue:
        return None

    numbers = []

    number_keys = [

        "numbers",

        "number",

        "openCode",

        "opencode",

        "open_code",

        "openNumbers",

        "open_numbers",

        "code",

        "codes",

        "balls",

        "result",
    ]

    for key in number_keys:

        if key not in obj:
            continue

        value = obj.get(
            key
        )

        candidate = clean_numbers(
            value
        )

        if len(candidate) >= 7:

            numbers = normalize_numbers(
                candidate
            )

            if len(numbers) >= 7:
                break

    if len(numbers) < 7:

        # 尝试扫描所有字段
        for value in obj.values():

            candidate = clean_numbers(
                value
            )

            if len(candidate) >= 7:

                numbers = normalize_numbers(
                    candidate
                )

                if len(numbers) >= 7:
                    break

    if len(numbers) < 7:
        return None

    open_time = ""

    for key in (
        "openTime",
        "open_time",
        "openDate",
        "date",
        "time",
        "drawTime",
    ):

        if key in obj:

            value = obj.get(
                key
            )

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


# ============================================================
# API深度解析
# ============================================================

def extract_draws(
    payload: Any,
) -> List[Dict[str, Any]]:

    result: List[
        Dict[str, Any]
    ] = []

    visited = set()

    def walk(
        obj: Any,
        depth: int = 0,
    ) -> None:

        if depth > 25:
            return

        if obj is None:
            return

        try:

            marker = id(obj)

            if marker in visited:
                return

            visited.add(marker)

        except Exception:
            pass

        # ----------------------------------------------------
        # 字符串
        # ----------------------------------------------------

        if isinstance(
            obj,
            str,
        ):

            text = obj.strip()

            if not text:
                return

            try:

                parsed = json.loads(
                    text
                )

                if parsed is not obj:

                    walk(
                        parsed,
                        depth + 1,
                    )

                    return

            except Exception:
                pass

            return

        # ----------------------------------------------------
        # list
        # ----------------------------------------------------

        if isinstance(
            obj,
            (list, tuple),
        ):

            for item in obj:

                if isinstance(
                    item,
                    dict,
                ):

                    draw = parse_draw(
                        item
                    )

                    if draw:

                        result.append(
                            draw
                        )

                walk(
                    item,
                    depth + 1,
                )

            return

        # ----------------------------------------------------
        # dict
        # ----------------------------------------------------

        if isinstance(
            obj,
            dict,
        ):

            draw = parse_draw(
                obj
            )

            if draw:

                result.append(
                    draw
                )

            priority = [

                "history",

                "lottery_data",

                "lotteryData",

                "records",

                "data",

                "list",

                "items",

                "result",

                "rows",

                "draws",

                "results",

            ]

            handled = set()

            for key in priority:

                if key not in obj:
                    continue

                handled.add(key)

                walk(
                    obj[key],
                    depth + 1,
                )

            for key, value in obj.items():

                if key in handled:
                    continue

                if isinstance(
                    value,
                    (
                        dict,
                        list,
                        tuple,
                    ),
                ):

                    walk(
                        value,
                        depth + 1,
                    )

    walk(
        payload
    )

    # --------------------------------------------------------
    # 去重
    # --------------------------------------------------------

    unique = {}

    for draw in result:

        issue = str(
            draw.get(
                "issue",
                "",
            )
        ).strip()

        numbers = normalize_numbers(
            draw.get(
                "numbers",
                [],
            )
        )

        if not issue:
            continue

        if len(numbers) < 7:
            continue

        unique[
            issue
        ] = {

            "issue": issue,

            "open_time":
                draw.get(
                    "open_time",
                    "",
                ),

            "numbers":
                numbers[:7],

        }

    def sort_key(
        item: Dict[str, Any],
    ):

        issue = str(
            item.get(
                "issue",
                "",
            )
        )

        digits = re.sub(
            r"\D",
            "",
            issue,
        )

        if digits:

            try:

                return (
                    1,
                    int(digits),
                )

            except Exception:
                pass

        return (
            0,
            issue,
        )

    draws = sorted(
        unique.values(),
        key=sort_key,
        reverse=True,
    )

    return draws[:MAX_HISTORY]


# ============================================================
# HTTP请求
# ============================================================

def request_json(
    url: str,
    params: Dict[str, Any],
    verify_ssl: bool = True,
) -> Any:

    query = urlencode(
        params
    )

    final_url = (
        url
        + (
            "&"
            if "?" in url
            else "?"
        )
        + query
    )

    request = Request(
        final_url,
        headers={
            "User-Agent":
                USER_AGENT,
            "Accept":
                "application/json,text/plain,*/*",
        },
    )

    context = None

    if not verify_ssl:

        context = ssl._create_unverified_context()

    with urlopen(
        request,
        timeout=REQUEST_TIMEOUT,
        context=context,
    ) as response:

        raw = response.read()

    text = raw.decode(
        "utf-8",
        errors="replace",
    )

    return json.loads(
        text
    )


# ============================================================
# API同步
# ============================================================

def fetch_online(
    lottery: str,
) -> List[Dict[str, Any]]:

    config = LOTTERIES[
        lottery
    ]

    lottery_type = config[
        "type"
    ]

    log("")
    log("=" * 70)
    log(
        f"正在更新：{lottery}"
    )
    log("=" * 70)

    all_draws = []

    # --------------------------------------------------------
    # 先尝试正常HTTPS
    # --------------------------------------------------------

    for index, base_url in enumerate(
        API_URLS,
        start=1,
    ):

        url = base_url

        log(
            f"[{lottery}] "
            f"请求API 第{index}次"
        )

        log(
            f"{url}?type={lottery_type}"
        )

        try:

            payload = request_json(
                url,
                {
                    "type":
                        lottery_type
                },
                verify_ssl=(
                    not url.startswith(
                        "http://"
                    )
                ),
            )

            draws = extract_draws(
                payload
            )

            if draws:

                log(
                    f"[{lottery}] "
                    f"API解析得到："
                    f"{len(draws)} 期"
                )

                return draws

            log(
                f"[{lottery}] "
                "API返回成功，但没有找到有效开奖数据"
            )

        except HTTPError as exc:

            log(
                f"[WARN] HTTP错误："
                f"{exc.code}"
            )

        except URLError as exc:

            log(
                f"[WARN] 请求失败："
                f"{exc}"
            )

        except ssl.SSLError as exc:

            log(
                f"[WARN] SSL错误："
                f"{exc}"
            )

        except Exception as exc:

            log(
                f"[WARN] 请求失败："
                f"{exc}"
            )

        time.sleep(
            0.5
        )

    # --------------------------------------------------------
    # 最后尝试SSL忽略模式
    # --------------------------------------------------------

    for base_url in API_URLS:

        if not base_url.startswith(
            "https://"
        ):
            continue

        log(
            f"[{lottery}] "
            "尝试备用SSL模式"
        )

        try:

            payload = request_json(
                base_url,
                {
                    "type":
                        lottery_type
                },
                verify_ssl=False,
            )

            draws = extract_draws(
                payload
            )

            if draws:

                log(
                    f"[{lottery}] "
                    f"备用模式解析："
                    f"{len(draws)} 期"
                )

                return draws

        except Exception as exc:

            log(
                f"[WARN] 备用SSL模式失败："
                f"{exc}"
            )

    return []


# ============================================================
# SQLite保存
# ============================================================

def save_draws(
    lottery: str,
    draws: List[
        Dict[str, Any]
    ],
) -> int:

    if not draws:
        return 0

    conn = get_connection(
        lottery
    )

    inserted = 0

    try:

        for draw in draws:

            issue = str(
                draw[
                    "issue"
                ]
            )

            numbers = normalize_numbers(
                draw[
                    "numbers"
                ]
            )

            if len(numbers) < 7:
                continue

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO draws
                (
                    issue,
                    open_time,
                    numbers,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    issue,
                    draw.get(
                        "open_time",
                        "",
                    ),
                    json.dumps(
                        numbers,
                        ensure_ascii=False,
                    ),
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
# SQLite读取
# ============================================================

def load_history(
    lottery: str,
) -> List[
    Dict[str, Any]
]:

    conn = get_connection(
        lottery
    )

    try:

        rows = conn.execute(
            """
            SELECT
                issue,
                open_time,
                numbers
            FROM draws
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                MAX_HISTORY,
            ),
        ).fetchall()

    finally:

        conn.close()

    result = []

    for row in rows:

        try:

            numbers = json.loads(
                row[
                    "numbers"
                ]
            )

        except Exception:

            numbers = clean_numbers(
                row[
                    "numbers"
                ]
            )

        numbers = normalize_numbers(
            numbers
        )

        if len(numbers) >= 7:

            result.append(
                {
                    "issue":
                        row[
                            "issue"
                        ],

                    "open_time":
                        row[
                            "open_time"
                        ],

                    "numbers":
                        numbers[:7],
                }
            )

    return result


# ============================================================
# 号码统计
# ============================================================

def number_frequency(
    history: List[
        Dict[str, Any]
    ],
) -> Counter:

    counter = Counter()

    for draw in history:

        for n in draw[
            "numbers"
        ]:

            counter[n] += 1

    return counter


def calculate_overdue(
    history: List[
        Dict[str, Any]
    ],
) -> Dict[int, int]:

    overdue = {}

    for number in range(
        1,
        50,
    ):

        gap = len(
            history
        )

        for index, draw in enumerate(
            history
        ):

            if number in draw[
                "numbers"
            ]:

                gap = index

                break

        overdue[
            number
        ] = gap

    return overdue


# ============================================================
# 综合评分
# ============================================================

def calculate_scores(
    history: List[
        Dict[str, Any]
    ],
) -> Dict[int, float]:

    if not history:

        return {
            n: 0.0
            for n in range(
                1,
                50,
            )
        }

    frequency = number_frequency(
        history
    )

    overdue = calculate_overdue(
        history
    )

    recent = history[
        :min(
            20,
            len(history),
        )
    ]

    recent_frequency = number_frequency(
        recent
    )

    scores = {}

    max_frequency = max(
        frequency.values(),
        default=1,
    )

    max_recent = max(
        recent_frequency.values(),
        default=1,
    )

    max_overdue = max(
        overdue.values(),
        default=1,
    )

    for number in range(
        1,
        50,
    ):

        freq_score = (
            frequency[number]
            / max_frequency
        )

        recent_score = (
            recent_frequency[number]
            / max_recent
        )

        overdue_score = (
            overdue[number]
            / max_overdue
            if max_overdue
            else 0
        )

        # 频率 45%
        # 近期 35%
        # 遗漏 20%
        score = (

            freq_score * 0.45

            +

            recent_score * 0.35

            +

            overdue_score * 0.20

        )

        scores[
            number
        ] = round(
            score,
            6,
        )

    return scores


# ============================================================
# 属性统计
# ============================================================

def attribute_statistics(
    history: List[
        Dict[str, Any]
    ],
) -> Dict[str, Any]:

    colors = Counter()

    sizes = Counter()

    odd_even = Counter()

    tails = Counter()

    zones = Counter()

    for draw in history:

        numbers = draw[
            "numbers"
        ]

        if not numbers:
            continue

        # 这里使用特码，即第7个号码
        special = numbers[-1]

        colors[
            get_color(special)
        ] += 1

        sizes[
            get_size(special)
        ] += 1

        odd_even[
            get_odd_even(special)
        ] += 1

        tails[
            str(
                get_tail(
                    special
                )
            )
        ] += 1

        zones[
            str(
                get_zone(
                    special
                )
            )
        ] += 1

    return {

        "sample_size":
            len(history),

        "colors":
            dict(colors),

        "sizes":
            dict(sizes),

        "odd_even":
            dict(odd_even),

        "tails":
            dict(tails),

        "zones":
            dict(zones),

    }


# ============================================================
# 热号 / 冷号
# ============================================================

def hot_cold(
    history: List[
        Dict[str, Any]
    ],
) -> Tuple[
    List[int],
    List[int],
]:

    frequency = number_frequency(
        history
    )

    hot = sorted(
        range(
            1,
            50,
        ),
        key=lambda n: (
            frequency[n],
            n,
        ),
        reverse=True,
    )

    cold = sorted(
        range(
            1,
            50,
        ),
        key=lambda n: (
            frequency[n],
            -n,
        ),
    )

    return (
        hot[:10],
        cold[:10],
    )


# ============================================================
# 综合候选
# ============================================================

def generate_candidates(
    history: List[
        Dict[str, Any]
    ],
) -> Dict[str, Any]:

    scores = calculate_scores(
        history
    )

    ranking = sorted(
        scores.keys(),
        key=lambda n: (
            scores[n],
            n,
        ),
        reverse=True,
    )

    # 历史不足时，仍然保证输出12个
    candidates = ranking[
        :12
    ]

    hot, cold = hot_cold(
        history
    )

    return {

        "candidates":
            candidates,

        "hot_numbers":
            hot,

        "cold_numbers":
            cold,

        "scores":
            {
                str(n):
                    scores[n]
                for n in ranking[:20]
            },

    }


# ============================================================
# Walk Forward
# ============================================================

def walk_forward_backtest(
    history: List[
        Dict[str, Any]
    ],
) -> Dict[str, Any]:

    total = len(
        history
    )

    if total < 2:

        return {

            "method":
                "Walk-Forward",

            "history_size":
                total,

            "samples":
                0,

            "hits":
                0,

            "hit_rate":
                0.0,

            "status":
                "历史数据不足",

        }

    samples = 0

    hits = 0

    # 从较早历史开始
    # 每次用之前的数据预测下一期
    minimum_train = min(
        30,
        max(
            1,
            total - 1,
        ),
    )

    for i in range(
        minimum_train,
        total,
    ):

        train = history[
            i:
        ]

        target = history[
            i - 1
        ]

        if not train:
            continue

        scores = calculate_scores(
            train
        )

        candidates = set(
            sorted(
                scores,
                key=scores.get,
                reverse=True,
            )[:12]
        )

        actual = set(
            target[
                "numbers"
            ]
        )

        samples += 1

        if candidates & actual:

            hits += 1

    rate = (
        hits / samples
        if samples
        else 0.0
    )

    return {

        "method":
            "Walk-Forward",

        "history_size":
            total,

        "samples":
            samples,

        "hits":
            hits,

        "hit_rate":
            round(
                rate,
                6,
            ),

        "status":
            (
                "正常"
                if samples
                else "历史数据不足"
            ),

    }


# ============================================================
# 模块表现
# ============================================================

def module_performance(
    history: List[
        Dict[str, Any]
    ],
) -> Dict[str, Any]:

    total = len(
        history
    )

    if total < 2:

        return {

            "history_size":
                total,

            "modules": {

                "frequency":
                    {
                        "score":
                            0.0,
                        "status":
                            "数据不足",
                    },

                "recent_frequency":
                    {
                        "score":
                            0.0,
                        "status":
                            "数据不足",
                    },

                "overdue":
                    {
                        "score":
                            0.0,
                        "status":
                            "数据不足",
                    },

            },

        }

    frequency = number_frequency(
        history
    )

    recent = number_frequency(
        history[:20]
    )

    overdue = calculate_overdue(
        history
    )

    avg_frequency = statistics.mean(
        frequency.values()
    ) if frequency else 0

    avg_recent = statistics.mean(
        recent.values()
    ) if recent else 0

    avg_overdue = statistics.mean(
        overdue.values()
    ) if overdue else 0

    return {

        "history_size":
            total,

        "modules": {

            "frequency":
                {
                    "score":
                        round(
                            avg_frequency,
                            6,
                        ),
                    "status":
                        "正常",
                },

            "recent_frequency":
                {
                    "score":
                        round(
                            avg_recent,
                            6,
                        ),
                    "status":
                        "正常",
                },

            "overdue":
                {
                    "score":
                        round(
                            avg_overdue,
                            6,
                        ),
                    "status":
                        "正常",
                },

        },

    }


# ============================================================
# 保存JSON
# ============================================================

def save_json(
    filename: str,
    data: Dict[str, Any],
) -> str:

    path = os.path.join(
        OUTPUT_DIR,
        filename,
    )

    temp = (
        path
        + ".tmp"
    )

    with open(
        temp,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(
        temp,
        path,
    )

    return path


# ============================================================
# 文件检查
# ============================================================

def verify_output(
    path: str,
) -> bool:

    try:

        if not os.path.isfile(
            path
        ):
            return False

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(
                f
            )

        return isinstance(
            data,
            dict,
        )

    except Exception:

        return False


# ============================================================
# 单彩种分析
# ============================================================

def analyze_lottery(
    lottery: str,
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    online_draws = fetch_online(
        lottery
    )

    # --------------------------------------------------------
    # 保存
    # --------------------------------------------------------

    inserted = save_draws(
        lottery,
        online_draws,
    )

    log(
        f"[{lottery}] "
        f"本次新增：{inserted} 期"
    )

    # --------------------------------------------------------
    # 从SQLite读取完整历史
    # --------------------------------------------------------

    history = load_history(
        lottery
    )

    if not history:

        return {

            "lottery":
                lottery,

            "success":
                False,

            "error":
                "没有可用历史数据",

            "history_size":
                0,

            "candidates":
                [],

        }

    latest = history[
        0
    ]

    numbers = latest[
        "numbers"
    ]

    special = numbers[
        -1
    ]

    attributes = attribute_statistics(
        history
    )

    prediction = generate_candidates(
        history
    )

    backtest = walk_forward_backtest(
        history
    )

    performance = module_performance(
        history
    )

    hot = prediction[
        "hot_numbers"
    ]

    cold = prediction[
        "cold_numbers"
    ]

    candidates = prediction[
        "candidates"
    ]

    # --------------------------------------------------------
    # 控制台输出
    # --------------------------------------------------------

    log("")
    log("=" * 70)
    log(
        f"【{lottery}】"
    )
    log("=" * 70)

    log(
        f"历史期数："
        f"{len(history)}"
    )

    log(
        f"最新期号："
        f"{latest['issue']}"
    )

    log(
        f"最新号码："
        f"{numbers}"
    )

    log(
        f"特码："
        f"{special}"
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

    log(
        "近期开奖属性统计："
    )

    log(
        "波色："
        + str(
            attributes[
                "colors"
            ]
        )
    )

    log(
        "大小："
        + str(
            attributes[
                "sizes"
            ]
        )
    )

    log(
        "单双："
        + str(
            attributes[
                "odd_even"
            ]
        )
    )

    log(
        "尾数："
        + str(
            attributes[
                "tails"
            ]
        )
    )

    log(
        "分区："
        + str(
            attributes[
                "zones"
            ]
        )
    )

    log(
        "高频号码："
        + " ".join(
            f"{n:02d}"
            for n in hot
        )
    )

    log(
        "低频号码："
        + " ".join(
            f"{n:02d}"
            for n in cold
        )
    )

    log(
        "综合候选："
        + " ".join(
            f"{n:02d}"
            for n in candidates
        )
    )

    if len(history) < 10:

        log(
            "⚠ 当前历史数据少于10期，"
            "统计结果仅用于程序测试，"
            "不适合进行稳定性判断。"
        )

    log(
        "说明："
        "以上为基于历史数据的统计分析，"
        "不代表实际开奖结果。"
    )

    return {

        "lottery":
            lottery,

        "latest_issue":
            latest[
                "issue"
            ],

        "latest_numbers":
            numbers,

        "history_size":
            len(history),

        "candidates":
            candidates,

        "hot_numbers":
            hot,

        "cold_numbers":
            cold,

        "attributes":
            attributes,

        "backtest":
            backtest,

        "module_performance":
            performance,

        "success":
            True,

    }


# ============================================================
# 三彩种统一运行
# ============================================================

def run_all_lotteries() -> Dict[
    str,
    Dict[str, Any],
]:

    results = {}

    for lottery in LOTTERIES:

        try:

            results[
                lottery
            ] = analyze_lottery(
                lottery
            )

        except Exception as exc:

            log("")
            log(
                f"[ERROR] "
                f"{lottery}分析失败："
                f"{exc}"
            )

            traceback.print_exc()

            results[
                lottery
            ] = {

                "lottery":
                    lottery,

                "success":
                    False,

                "error":
                    str(exc),

                "candidates":
                    [],

            }

    return results


# ============================================================
# 主系统
# ============================================================

def run_system(
    sync: bool = True,
    **kwargs,
) -> Dict[str, Any]:

    start_time = datetime.now()

    log("=" * 70)

    log(
        "六合彩综合预测系统"
    )

    log(
        "真实数据 + SQLite + "
        "多期历史统计 + "
        "Walk-Forward + 输出文件版"
    )

    log(
        f"版本：{VERSION}"
    )

    log(
        f"启动时间："
        f"{start_time.isoformat()}"
    )

    log("=" * 70)

    try:

        results = run_all_lotteries()

    except Exception as exc:

        log("")
        log(
            "系统核心异常："
            f"{exc}"
        )

        traceback.print_exc()

        return {

            "fatal_error":
                str(exc)

        }

    # ========================================================
    # prediction.json
    # ========================================================

    prediction_data = {

        "version":
            VERSION,

        "generated_at":
            datetime.now().isoformat(),

        "note":
            "历史统计分析结果，不代表真实中奖概率。",

        "lotteries":
            results,

    }

    log("")
    log("=" * 70)
    log(
        "保存预测结果"
    )
    log("=" * 70)

    prediction_path = save_json(
        "prediction.json",
        prediction_data,
    )

    if verify_output(
        prediction_path
    ):

        log(
            "✅ 预测结果已保存："
            + prediction_path
        )

    else:

        log(
            "❌ prediction.json保存失败"
        )

    # ========================================================
    # 汇总回测
    # ========================================================

    backtest_data = {

        "version":
            VERSION,

        "generated_at":
            datetime.now().isoformat(),

        "method":
            "Walk-Forward",

        "lotteries":
            {
                lottery:
                    result.get(
                        "backtest",
                        {},
                    )
                    for lottery, result
                    in results.items()
            },

    }

    log("")
    log("=" * 70)
    log(
        "保存 Walk-Forward 回测"
    )
    log("=" * 70)

    backtest_path = save_json(
        "backtest.json",
        backtest_data,
    )

    if verify_output(
        backtest_path
    ):

        log(
            "✅ 回测结果已保存："
            + backtest_path
        )

    else:

        log(
            "❌ backtest.json保存失败"
        )

    # ========================================================
    # 模块表现
    # ========================================================

    module_data = {

        "version":
            VERSION,

        "generated_at":
            datetime.now().isoformat(),

        "lotteries":
            {
                lottery:
                    result.get(
                        "module_performance",
                        {},
                    )
                    for lottery, result
                    in results.items()
            },

    }

    log("")
    log("=" * 70)
    log(
        "保存模块表现"
    )
    log("=" * 70)

    module_path = save_json(
        "module_performance.json",
        module_data,
    )

    if verify_output(
        module_path
    ):

        log(
            "✅ 模块表现已保存："
            + module_path
        )

    else:

        log(
            "❌ module_performance.json保存失败"
        )

    # ========================================================
    # 文件检查
    # ========================================================

    log("")
    log("=" * 70)
    log(
        "输出文件检查"
    )
    log("=" * 70)

    output_files = [

        prediction_path,

        backtest_path,

        module_path,

    ]

    for path in output_files:

        if os.path.isfile(
            path
        ):

            size = os.path.getsize(
                path
            )

            log(
                f"✅ {path} "
                f"({size} bytes)"
            )

        else:

            log(
                f"❌ {path}"
            )

    # ========================================================
    # 最终汇总
    # ========================================================

    log("")
    log("=" * 70)
    log(
        "三彩种分析完成"
    )
    log("=" * 70)

    for lottery, result in results.items():

        candidates = result.get(
            "candidates",
            [],
        )

        text = " ".join(
            f"{n:02d}"
            for n in candidates
        )

        log(
            f"{lottery}："
            f"{text}"
        )

    log(
        "说明：候选号码来自历史统计评分，"
        "不代表真实中奖概率。"
    )

    log("=" * 70)
    log(
        "系统运行结束"
    )
    log("=" * 70)

    return {

        "success":
            True,

        "prediction":
            prediction_data,

        "backtest":
            backtest_data,

        "module_performance":
            module_data,

    }


# ============================================================
# 兼容旧代码
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
