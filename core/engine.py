# -*- coding: utf-8 -*-

"""
六合彩综合预测系统
核心运行引擎 V6.0

功能：

1. 三彩种统一运行
2. API真实数据同步
3. SQLite历史数据
4. 多期历史统计
5. 高频 / 低频分析
6. Walk-Forward回测
7. 模块表现统计
8. 自动计算最新开奖期数
9. 自动计算下一期预测期数
10. 自动输出JSON
11. 兼容 core/api_sync.py
12. 不依赖 core/api.py

支持：

新澳门彩
老澳门彩
香港彩
"""

from __future__ import annotations

import json
import os
import sqlite3
import traceback
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# 基础配置
# ============================================================

VERSION = "V6.0 REAL DATA FINAL"

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

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 三彩种
# ============================================================

LOTTERIES = [
    "新澳门彩",
    "老澳门彩",
    "香港彩",
]


# ============================================================
# API类型映射
# ============================================================

LOTTERY_API_TYPES = {
    "新澳门彩": "newMacau",
    "老澳门彩": "oldMacau",
    "香港彩": "hk",
}


# ============================================================
# 数据库
# ============================================================

DB_FILES = {
    "新澳门彩": os.path.join(
        DATA_DIR,
        "new_macau.db",
    ),
    "老澳门彩": os.path.join(
        DATA_DIR,
        "old_macau.db",
    ),
    "香港彩": os.path.join(
        DATA_DIR,
        "hk.db",
    ),
}


# ============================================================
# 输出文件
# ============================================================

PREDICTION_FILE = os.path.join(
    OUTPUT_DIR,
    "prediction.json",
)

BACKTEST_FILE = os.path.join(
    OUTPUT_DIR,
    "backtest.json",
)

MODULE_FILE = os.path.join(
    OUTPUT_DIR,
    "module_performance.json",
)


# ============================================================
# 日志
# ============================================================

def log(message: str = "") -> None:
    print(message, flush=True)


def separator() -> None:
    log("=" * 70)


# ============================================================
# 安全整数
# ============================================================

def safe_int(value: Any) -> Optional[int]:

    try:
        return int(value)

    except Exception:
        return None


# ============================================================
# 期号转整数
# ============================================================

def issue_to_int(issue: Any) -> Optional[int]:

    if issue is None:
        return None

    text = str(issue).strip()

    digits = "".join(
        c for c in text
        if c.isdigit()
    )

    if not digits:
        return None

    try:
        return int(digits)

    except Exception:
        return None


# ============================================================
# 计算下一期期号
# ============================================================

def next_issue(issue: Any) -> str:

    number = issue_to_int(issue)

    if number is None:
        return ""

    return str(number + 1)


# ============================================================
# 波色
# ============================================================

RED = {
    1, 2, 7, 8, 12, 13, 18, 19,
    23, 24, 29, 30, 34, 35, 40,
    45, 46
}

BLUE = {
    3, 4, 9, 10, 14, 15, 20,
    25, 26, 31, 36, 37, 41,
    42, 47, 48
}

GREEN = {
    5, 6, 11, 16, 17, 21, 22,
    27, 28, 32, 33, 38, 39,
    43, 44, 49
}


def get_color(number: int) -> str:

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return "未知"


# ============================================================
# 大小
# ============================================================

def get_size(number: int) -> str:

    return "大" if number >= 25 else "小"


# ============================================================
# 单双
# ============================================================

def get_odd_even(number: int) -> str:

    return "单" if number % 2 else "双"


# ============================================================
# 尾数
# ============================================================

def get_tail(number: int) -> str:

    return str(number % 10)


# ============================================================
# 分区
# ============================================================

def get_zone(number: int) -> str:

    if number <= 10:
        return "1"

    if number <= 20:
        return "2"

    if number <= 30:
        return "3"

    if number <= 40:
        return "4"

    return "5"


# ============================================================
# 数据库初始化
# ============================================================

def init_db(db_path: str) -> None:

    os.makedirs(
        os.path.dirname(db_path),
        exist_ok=True,
    )

    conn = sqlite3.connect(
        db_path
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue TEXT UNIQUE,
            numbers TEXT,
            open_time TEXT,
            created_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()


# ============================================================
# 读取数据库
# ============================================================

def load_history(
    lottery: str,
) -> List[Dict[str, Any]]:

    db_path = DB_FILES[lottery]

    init_db(db_path)

    conn = sqlite3.connect(
        db_path
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT issue,
               numbers,
               open_time
        FROM draws
        ORDER BY id ASC
        """
    )

    rows = cursor.fetchall()

    conn.close()

    history = []

    for issue, numbers_text, open_time in rows:

        try:

            numbers = json.loads(
                numbers_text
            )

        except Exception:
            continue

        if not isinstance(
            numbers,
            list,
        ):
            continue

        numbers = [
            int(x)
            for x in numbers
            if safe_int(x) is not None
        ]

        if len(numbers) != 7:
            continue

        history.append(
            {
                "issue": str(issue),
                "numbers": numbers,
                "open_time": open_time,
            }
        )

    return history


# ============================================================
# 保存开奖
# ============================================================

def save_draw(
    lottery: str,
    draw: Dict[str, Any],
) -> bool:

    issue = str(
        draw.get(
            "issue",
            ""
        )
    ).strip()

    numbers = draw.get(
        "numbers",
        []
    )

    if not issue:
        return False

    if not isinstance(
        numbers,
        list,
    ):
        return False

    numbers = [
        int(x)
        for x in numbers
        if safe_int(x) is not None
    ]

    if len(numbers) != 7:
        return False

    db_path = DB_FILES[lottery]

    init_db(db_path)

    conn = sqlite3.connect(
        db_path
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO draws
        (
            issue,
            numbers,
            open_time,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            issue,
            json.dumps(
                numbers,
                ensure_ascii=False,
            ),
            str(
                draw.get(
                    "open_time",
                    ""
                )
            ),
            datetime.now().isoformat(),
        )
    )

    inserted = (
        cursor.rowcount > 0
    )

    conn.commit()
    conn.close()

    return inserted


# ============================================================
# 从 API 模块获取数据
# ============================================================

def fetch_from_api_sync(
    lottery: str,
) -> Any:

    """
    这里非常重要：

    项目使用：

        core/api_sync.py

    而不是：

        core/api.py
    """

    try:

        from . import api_sync

    except Exception as exc:

        log(
            f"[WARN] 无法导入 core.api_sync：{exc}"
        )

        return None

    api_type = LOTTERY_API_TYPES.get(
        lottery,
        "hk",
    )

    # --------------------------------------------------------
    # 尝试不同函数名称
    # --------------------------------------------------------

    functions = [
        "fetch_lottery",
        "fetch_lottery_data",
        "fetch_data",
        "get_lottery_data",
        "sync_lottery",
        "update_lottery",
        "fetch_online",
        "request_api",
    ]

    for name in functions:

        func = getattr(
            api_sync,
            name,
            None,
        )

        if not callable(func):
            continue

        attempts = [
            (lottery,),
            (api_type,),
            (lottery, api_type),
            (),
        ]

        for args in attempts:

            try:

                result = func(
                    *args
                )

                if result is not None:

                    return result

            except TypeError:

                continue

            except Exception as exc:

                log(
                    f"[WARN] "
                    f"api_sync.{name} "
                    f"执行失败：{exc}"
                )

                break

    log(
        f"[WARN] core.api_sync 中没有找到可用的数据函数：{lottery}"
    )

    return None


# ============================================================
# API 数据标准化
# ============================================================

def normalize_draw(
    item: Any,
) -> Optional[Dict[str, Any]]:

    if not isinstance(
        item,
        dict,
    ):
        return None

    issue = (
        item.get("issue")
        or item.get("expect")
        or item.get("period")
        or item.get("qihao")
        or item.get("drawNumber")
    )

    numbers = (
        item.get("numbers")
        or item.get("openCode")
        or item.get("open_code")
        or item.get("codes")
    )

    if isinstance(
        numbers,
        str,
    ):

        parts = (
            numbers
            .replace(",", " ")
            .replace("|", " ")
            .replace("-", " ")
            .split()
        )

        parsed = []

        for x in parts:

            value = safe_int(x)

            if value is not None:
                parsed.append(value)

        numbers = parsed

    if not isinstance(
        numbers,
        list,
    ):
        return None

    parsed_numbers = []

    for number in numbers:

        value = safe_int(number)

        if value is not None:
            parsed_numbers.append(
                value
            )

    if len(parsed_numbers) < 7:
        return None

    parsed_numbers = parsed_numbers[:7]

    if issue is None:
        return None

    return {
        "issue": str(issue),
        "numbers": parsed_numbers,
        "open_time": (
            item.get("openTime")
            or item.get("open_time")
            or item.get("openDate")
            or ""
        ),
    }


# ============================================================
# 解析 API 返回
# ============================================================

def parse_api_result(
    result: Any,
) -> List[Dict[str, Any]]:

    if result is None:
        return []

    # --------------------------------------------------------
    # 直接是列表
    # --------------------------------------------------------

    if isinstance(
        result,
        list,
    ):

        output = []

        for item in result:

            draw = normalize_draw(
                item
            )

            if draw:
                output.append(draw)

        return output

    # --------------------------------------------------------
    # 字典
    # --------------------------------------------------------

    if isinstance(
        result,
        dict,
    ):

        # lottery_data
        lottery_data = result.get(
            "lottery_data"
        )

        if isinstance(
            lottery_data,
            list,
        ):

            return parse_api_result(
                lottery_data
            )

        # history
        history = result.get(
            "history"
        )

        if isinstance(
            history,
            list,
        ):

            return parse_api_result(
                history
            )

        # data
        data = result.get(
            "data"
        )

        if isinstance(
            data,
            list,
        ):

            return parse_api_result(
                data
            )

        if isinstance(
            data,
            dict,
        ):

            return parse_api_result(
                data
            )

        # 单期数据
        draw = normalize_draw(
            result
        )

        if draw:
            return [draw]

    return []


# ============================================================
# 同步一个彩种
# ============================================================

def sync_lottery(
    lottery: str,
) -> List[Dict[str, Any]]:

    separator()

    log(
        f"正在更新：{lottery}"
    )

    api_type = LOTTERY_API_TYPES[
        lottery
    ]

    log(
        f"[{lottery}] API类型：{api_type}"
    )

    result = fetch_from_api_sync(
        lottery
    )

    draws = parse_api_result(
        result
    )

    log(
        f"[{lottery}] API解析得到：{len(draws)} 期"
    )

    added = 0

    for draw in draws:

        if save_draw(
            lottery,
            draw,
        ):

            added += 1

    log(
        f"[{lottery}] 本次新增：{added} 期"
    )

    history = load_history(
        lottery
    )

    return history


# ============================================================
# 历史号码统计
# ============================================================

def count_numbers(
    history: List[Dict[str, Any]],
) -> Counter:

    counter = Counter()

    for draw in history:

        numbers = draw.get(
            "numbers",
            []
        )

        for number in numbers:

            if 1 <= number <= 49:

                counter[number] += 1

    return counter


# ============================================================
# 高频号码
# ============================================================

def get_hot_numbers(
    history: List[Dict[str, Any]],
    limit: int = 10,
) -> List[int]:

    counter = count_numbers(
        history
    )

    if not counter:
        return []

    result = sorted(
        range(1, 50),
        key=lambda n: (
            -counter[n],
            n,
        ),
    )

    return result[:limit]


# ============================================================
# 低频 / 遗漏号码
# ============================================================

def get_cold_numbers(
    history: List[Dict[str, Any]],
    limit: int = 10,
) -> List[int]:

    counter = count_numbers(
        history
    )

    result = sorted(
        range(1, 50),
        key=lambda n: (
            counter[n],
            n,
        ),
    )

    return result[:limit]


# ============================================================
# 属性统计
# ============================================================

def attribute_statistics(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    colors = Counter()
    sizes = Counter()
    odd_even = Counter()
    tails = Counter()
    zones = Counter()

    for draw in history:

        numbers = draw.get(
            "numbers",
            []
        )

        if not numbers:
            continue

        # 这里统计特码
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
            get_tail(special)
        ] += 1

        zones[
            get_zone(special)
        ] += 1

    return {
        "sample_size": len(history),
        "colors": dict(colors),
        "sizes": dict(sizes),
        "odd_even": dict(odd_even),
        "tails": dict(tails),
        "zones": dict(zones),
    }


# ============================================================
# 号码评分
# ============================================================

def score_numbers(
    history: List[Dict[str, Any]],
) -> Dict[int, float]:

    scores = {
        n: 0.0
        for n in range(1, 50)
    }

    if not history:
        return scores

    counter = count_numbers(
        history
    )

    # --------------------------------------------------------
    # 全历史频率
    # --------------------------------------------------------

    for number in range(1, 50):

        scores[number] += (
            counter[number] * 1.0
        )

    # --------------------------------------------------------
    # 最近10期
    # --------------------------------------------------------

    recent = history[-10:]

    recent_counter = count_numbers(
        recent
    )

    for number in range(1, 50):

        scores[number] += (
            recent_counter[number] * 1.5
        )

    # --------------------------------------------------------
    # 最近5期
    # --------------------------------------------------------

    recent5 = history[-5:]

    recent5_counter = count_numbers(
        recent5
    )

    for number in range(1, 50):

        scores[number] += (
            recent5_counter[number] * 2.0
        )

    # --------------------------------------------------------
    # 轻微遗漏因素
    # --------------------------------------------------------

    last_seen = {
        n: None
        for n in range(1, 50)
    }

    for index, draw in enumerate(history):

        for number in draw.get(
            "numbers",
            []
        ):

            if 1 <= number <= 49:

                last_seen[number] = index

    current_index = len(history)

    for number in range(1, 50):

        if last_seen[number] is None:

            scores[number] += 0.5

        else:

            overdue = (
                current_index
                - last_seen[number]
            )

            scores[number] += min(
                overdue * 0.05,
                1.5,
            )

    return scores


# ============================================================
# 综合候选
# ============================================================

def build_candidates(
    history: List[Dict[str, Any]],
    limit: int = 12,
) -> List[int]:

    scores = score_numbers(
        history
    )

    ranking = sorted(
        range(1, 50),
        key=lambda n: (
            -scores[n],
            n,
        ),
    )

    return ranking[:limit]


# ============================================================
# Walk-Forward 回测
# ============================================================

def walk_forward_backtest(
    history: List[Dict[str, Any]],
    candidate_count: int = 12,
) -> Dict[str, Any]:

    total = len(history)

    # 至少需要多期历史
    if total < 10:

        return {
            "method": "Walk-Forward",
            "history_size": total,
            "samples": 0,
            "hits": 0,
            "hit_rate": 0.0,
            "status": "历史数据不足",
        }

    samples = 0
    hits = 0

    # --------------------------------------------------------
    # 使用前面的数据预测下一期
    # --------------------------------------------------------

    start = 10

    for index in range(
        start,
        total,
    ):

        train = history[:index]

        actual = set(
            history[index].get(
                "numbers",
                []
            )
        )

        candidates = set(
            build_candidates(
                train,
                candidate_count,
            )
        )

        if not actual:
            continue

        samples += 1

        if candidates & actual:
            hits += 1

    rate = (
        hits / samples
        if samples
        else 0.0
    )

    return {
        "method": "Walk-Forward",
        "history_size": total,
        "samples": samples,
        "hits": hits,
        "hit_rate": round(
            rate,
            4,
        ),
        "status": "完成",
    }


# ============================================================
# 模块表现
# ============================================================

def module_performance(
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    total = len(history)

    if total < 10:

        return {
            "history_size": total,
            "modules": {
                "frequency": {
                    "score": 0.0,
                    "status": "数据不足",
                },
                "recent_frequency": {
                    "score": 0.0,
                    "status": "数据不足",
                },
                "overdue": {
                    "score": 0.0,
                    "status": "数据不足",
                },
            },
        }

    counter = count_numbers(
        history
    )

    recent = count_numbers(
        history[-10:]
    )

    # 归一化
    max_frequency = max(
        counter.values()
    ) if counter else 1

    max_recent = max(
        recent.values()
    ) if recent else 1

    frequency_score = (
        sum(counter.values())
        /
        max(
            total * 7,
            1,
        )
    )

    recent_score = (
        sum(recent.values())
        /
        max(
            min(total, 10) * 7,
            1,
        )
    )

    overdue_numbers = 0

    last_draw = (
        history[-1].get(
            "numbers",
            []
        )
        if history
        else []
    )

    for number in range(1, 50):

        if number not in last_draw:
            overdue_numbers += 1

    overdue_score = (
        overdue_numbers / 49
    )

    return {
        "history_size": total,
        "modules": {
            "frequency": {
                "score": round(
                    frequency_score,
                    4,
                ),
                "status": "正常",
            },
            "recent_frequency": {
                "score": round(
                    recent_score,
                    4,
                ),
                "status": "正常",
            },
            "overdue": {
                "score": round(
                    overdue_score,
                    4,
                ),
                "status": "正常",
            },
        },
    }


# ============================================================
# 单彩种分析
# ============================================================

def analyze_lottery(
    lottery: str,
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:

    result = {
        "lottery": lottery,
        "latest_issue": "",
        "next_issue": "",
        "latest_numbers": [],
        "history_size": len(history),
        "candidates": [],
        "hot_numbers": [],
        "cold_numbers": [],
        "attributes": {},
        "backtest": {},
        "module_performance": {},
        "success": False,
    }

    if not history:

        result["next_issue"] = ""

        return result

    latest = history[-1]

    latest_issue = str(
        latest.get(
            "issue",
            ""
        )
    )

    latest_numbers = [
        int(x)
        for x in latest.get(
            "numbers",
            []
        )
    ]

    result["latest_issue"] = (
        latest_issue
    )

    result["next_issue"] = (
        next_issue(
            latest_issue
        )
    )

    result["latest_numbers"] = (
        latest_numbers
    )

    candidates = build_candidates(
        history,
        12,
    )

    hot = get_hot_numbers(
        history,
        10,
    )

    cold = get_cold_numbers(
        history,
        10,
    )

    result["candidates"] = candidates
    result["hot_numbers"] = hot
    result["cold_numbers"] = cold

    result["attributes"] = (
        attribute_statistics(
            history
        )
    )

    result["backtest"] = (
        walk_forward_backtest(
            history
        )
    )

    result["module_performance"] = (
        module_performance(
            history
        )
    )

    result["success"] = True

    return result


# ============================================================
# 控制台输出
# ============================================================

def print_lottery_result(
    lottery: str,
    result: Dict[str, Any],
) -> None:

    separator()

    log(
        f"【{lottery}】"
    )

    separator()

    history_size = result.get(
        "history_size",
        0,
    )

    latest_issue = result.get(
        "latest_issue",
        "",
    )

    next_issue_value = result.get(
        "next_issue",
        "",
    )

    numbers = result.get(
        "latest_numbers",
        [],
    )

    log(
        f"历史期数：{history_size}"
    )

    log(
        f"最新开奖期数：{latest_issue}"
    )

    log(
        f"下一期预测期数：{next_issue_value}"
    )

    log(
        f"最新号码：{numbers}"
    )

    if numbers:

        special = numbers[-1]

        log(
            f"特码：{special}"
        )

        log(
            f"波色：{get_color(special)}"
        )

        log(
            f"大小：{get_size(special)}"
        )

        log(
            f"单双：{get_odd_even(special)}"
        )

        log(
            f"尾数：{get_tail(special)}"
        )

        log(
            f"分区：第{get_zone(special)}区"
        )

    attributes = result.get(
        "attributes",
        {},
    )

    log(
        "近期开奖属性统计："
    )

    log(
        f"波色：{attributes.get('colors', {})}"
    )

    log(
        f"大小：{attributes.get('sizes', {})}"
    )

    log(
        f"单双：{attributes.get('odd_even', {})}"
    )

    log(
        f"尾数：{attributes.get('tails', {})}"
    )

    log(
        f"分区：{attributes.get('zones', {})}"
    )

    hot = result.get(
        "hot_numbers",
        [],
    )

    cold = result.get(
        "cold_numbers",
        [],
    )

    candidates = result.get(
        "candidates",
        [],
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

    if history_size < 10:

        log(
            "⚠ 当前历史数据少于10期，"
            "统计结果仅用于程序测试，"
            "不适合进行稳定性判断。"
        )

    log(
        "说明：以上为基于历史数据的统计分析，"
        "不代表实际开奖结果。"
    )


# ============================================================
# JSON保存
# ============================================================

def save_json(
    path: str,
    data: Dict[str, Any],
) -> None:

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# 生成总回测
# ============================================================

def build_backtest_output(
    results: Dict[str, Any],
) -> Dict[str, Any]:

    return {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(),
        "method": "Walk-Forward",
        "lotteries": {
            lottery: result.get(
                "backtest",
                {},
            )
            for lottery, result
            in results.items()
        },
    }


# ============================================================
# 生成模块表现
# ============================================================

def build_module_output(
    results: Dict[str, Any],
) -> Dict[str, Any]:

    return {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(),
        "lotteries": {
            lottery: result.get(
                "module_performance",
                {},
            )
            for lottery, result
            in results.items()
        },
    }


# ============================================================
# 运行系统
# ============================================================

def run_system(
    sync: bool = True,
    auto_sync: Optional[bool] = None,
    data: Any = None,
    **kwargs,
) -> Dict[str, Any]:

    if auto_sync is not None:
        sync = auto_sync

    separator()

    log(
        "六合彩综合预测系统"
    )

    log(
        "真实数据 + SQLite + 多期历史统计 + "
        "Walk-Forward + 输出文件版"
    )

    log(
        f"版本：{VERSION}"
    )

    log(
        f"启动时间：{datetime.now().isoformat()}"
    )

    separator()

    results: Dict[
        str,
        Dict[str, Any]
    ] = {}

    # --------------------------------------------------------
    # 三彩种
    # --------------------------------------------------------

    for lottery in LOTTERIES:

        try:

            if sync:

                history = sync_lottery(
                    lottery
                )

            else:

                history = load_history(
                    lottery
                )

            result = analyze_lottery(
                lottery,
                history,
            )

            results[lottery] = result

            print_lottery_result(
                lottery,
                result,
            )

        except Exception as exc:

            log("")
            log(
                f"[ERROR] {lottery}运行失败：{exc}"
            )

            traceback.print_exc()

            results[lottery] = {
                "lottery": lottery,
                "latest_issue": "",
                "next_issue": "",
                "latest_numbers": [],
                "history_size": 0,
                "candidates": [],
                "hot_numbers": [],
                "cold_numbers": [],
                "attributes": {},
                "backtest": {
                    "method": "Walk-Forward",
                    "history_size": 0,
                    "samples": 0,
                    "hits": 0,
                    "hit_rate": 0.0,
                    "status": "运行失败",
                },
                "module_performance": {},
                "success": False,
                "error": str(exc),
            }

    # ========================================================
    # prediction.json
    # ========================================================

    separator()

    log(
        "保存预测结果"
    )

    prediction = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(),
        "note": (
            "历史统计分析结果，"
            "不代表真实中奖概率。"
        ),
        "lotteries": results,
    }

    save_json(
        PREDICTION_FILE,
        prediction,
    )

    log(
        f"✅ 预测结果已保存：{PREDICTION_FILE}"
    )

    # ========================================================
    # backtest.json
    # ========================================================

    separator()

    log(
        "保存 Walk-Forward 回测"
    )

    backtest = build_backtest_output(
        results
    )

    save_json(
        BACKTEST_FILE,
        backtest,
    )

    log(
        f"✅ 回测结果已保存：{BACKTEST_FILE}"
    )

    # ========================================================
    # module_performance.json
    # ========================================================

    separator()

    log(
        "保存模块表现"
    )

    module_data = build_module_output(
        results
    )

    save_json(
        MODULE_FILE,
        module_data,
    )

    log(
        f"✅ 模块表现已保存：{MODULE_FILE}"
    )

    # ========================================================
    # 输出文件检查
    # ========================================================

    separator()

    log(
        "输出文件检查"
    )

    output_files = [
        PREDICTION_FILE,
        BACKTEST_FILE,
        MODULE_FILE,
    ]

    for path in output_files:

        if os.path.isfile(path):

            size = os.path.getsize(
                path
            )

            log(
                f"✅ {path} ({size} bytes)"
            )

        else:

            log(
                f"❌ 文件不存在：{path}"
            )

    # ========================================================
    # 三彩种汇总
    # ========================================================

    separator()

    log(
        "三彩种分析完成"
    )

    for lottery in LOTTERIES:

        result = results.get(
            lottery,
            {},
        )

        candidates = result.get(
            "candidates",
            [],
        )

        latest_issue = result.get(
            "latest_issue",
            "",
        )

        next_issue_value = result.get(
            "next_issue",
            "",
        )

        candidate_text = " ".join(
            f"{n:02d}"
            for n in candidates
        )

        log(
            f"{lottery}："
            f"最新第 {latest_issue} 期"
        )

        log(
            f"{lottery}："
            f"预测下一期第 {next_issue_value} 期"
        )

        log(
            f"{lottery}候选："
            f"{candidate_text}"
        )

    log(
        "说明：候选号码来自历史统计评分，"
        "不代表真实中奖概率。"
    )

    separator()

    log(
        "系统运行结束"
    )

    separator()

    return prediction


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
