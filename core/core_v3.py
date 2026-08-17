# -*- coding: utf-8 -*-
"""
六合彩 AI 智能预测系统 V3.0
============================================================
目标：
1. 三彩种：香港六合彩 / 新澳门六合彩 / 老澳门六合彩
2. SQLite 本地历史数据
3. marksix6.net 历史 + 实时 API
4. 过期 SSL 受控 fallback（仅用于指定数据源）
5. 动态 12 / 36 / 120 期特征
6. 状态识别 + 动态模块权重
7. 特码 Top10 / 重点3码
8. 特码生肖5肖 / 平特生肖2肖
9. 大小 / 单双
10. 波色单推 / 双推
11. Walk-Forward：只输出最近10/20期，不再输出30/60/100
12. 防止“最高分=1.0000”被误解成100%概率
13. prediction.json / backtest.json

说明：
彩票开奖结果具有随机性。本程序用于统计研究和历史回测，
历史命中率不能保证未来结果。
============================================================
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import ssl
import sys
import urllib.request
import urllib.error
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


# ============================================================
# 路径 / API
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_HISTORY = "https://marksix6.net/index.php?api=1"
API_REALTIME = "https://marksix6.net/api/lottery_api.php"

DB_FILES = {
    "hk": BASE_DIR / "hk_macau.db",
    "newMacau": BASE_DIR / "new_macau.db",
    "oldMacau": BASE_DIR / "old_macau.db",
}

LOTTERY_NAMES = {
    "hk": "香港六合彩",
    "newMacau": "新澳门六合彩",
    "oldMacau": "老澳门六合彩",
}

# ============================================================
# 2026 生肖
# ============================================================

ZODIAC_MAP_2026 = {
    "马": [1, 13, 25, 37, 49],
    "蛇": [2, 14, 26, 38],
    "龙": [3, 15, 27, 39],
    "兔": [4, 16, 28, 40],
    "虎": [5, 17, 29, 41],
    "牛": [6, 18, 30, 42],
    "鼠": [7, 19, 31, 43],
    "猪": [8, 20, 32, 44],
    "狗": [9, 21, 33, 45],
    "鸡": [10, 22, 34, 46],
    "猴": [11, 23, 35, 47],
    "羊": [12, 24, 36, 48],
}

NUMBER_TO_ZODIAC = {
    n: z for z, nums in ZODIAC_MAP_2026.items() for n in nums
}

# ============================================================
# 波色
# ============================================================

RED_WAVE = {
    1, 2, 7, 8, 12, 13, 18, 19, 23, 24,
    29, 30, 34, 35, 40, 45, 46
}

BLUE_WAVE = {
    3, 4, 9, 10, 14, 15, 20, 25, 26, 31,
    36, 37, 41, 42, 47, 48
}

GREEN_WAVE = {
    5, 6, 11, 16, 17, 21, 22, 27, 28,
    32, 33, 38, 39, 43, 44, 49
}

NUMBER_TO_WAVE = {}
for n in RED_WAVE:
    NUMBER_TO_WAVE[n] = "红"
for n in BLUE_WAVE:
    NUMBER_TO_WAVE[n] = "蓝"
for n in GREEN_WAVE:
    NUMBER_TO_WAVE[n] = "绿"

ALL_NUMBERS = list(range(1, 50))
ALL_WAVES = ["红", "蓝", "绿"]
ALL_SIZE = ["大", "小"]
ALL_PARITY = ["单", "双"]


# ============================================================
# 基础工具
# ============================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fmt_num(n: int) -> str:
    return f"{int(n):02d}"


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def get_wave(n: int) -> str:
    return NUMBER_TO_WAVE.get(n, "未知")


def get_zodiac(n: int) -> str:
    return NUMBER_TO_ZODIAC.get(n, "未知")


def get_size(n: int) -> str:
    return "大" if n >= 25 else "小"


def get_parity(n: int) -> str:
    return "单" if n % 2 else "双"


def get_tail(n: int) -> int:
    return n % 10


def get_zone(n: int) -> int:
    # 1-10, 11-20, 21-30, 31-40, 41-49
    return min(4, (n - 1) // 10)


def clamp(x: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(x)))


def normalize_map(scores: Dict[Any, float], default: float = 0.5) -> Dict[Any, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if hi <= lo:
        return {k: default for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def softmax(scores: Dict[Any, float], temperature: float = 0.20) -> Dict[Any, float]:
    if not scores:
        return {}
    temperature = max(0.01, temperature)
    m = max(scores.values())
    exps = {}
    total = 0.0
    for k, v in scores.items():
        e = math.exp((v - m) / temperature)
        exps[k] = e
        total += e
    if total <= 0:
        return {k: 1.0 / len(scores) for k in scores}
    return {k: v / total for k, v in exps.items()}


def entropy_from_counts(counts: Dict[Any, int]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log(p, 2)
    return h


# ============================================================
# SSL / HTTP
# ============================================================

def build_ssl_context(verify: bool = True) -> ssl.SSLContext:
    if verify:
        return ssl.create_default_context()
    return ssl._create_unverified_context()


def http_json(url: str, timeout: int = 20, retries: int = 2) -> Any:
    headers = {
        "User-Agent": "Mozilla/5.0 MarkSix-AI-V3.0",
        "Accept": "application/json,text/plain,*/*",
        "Cache-Control": "no-cache",
    }

    last_error = None

    # 第一次：正常 SSL
    for attempt in range(1, retries + 1):
        try:
            print(f"请求API 第{attempt}次")
            print(url)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(
                req,
                timeout=timeout,
                context=build_ssl_context(True),
            ) as resp:
                raw = resp.read()
                return json.loads(raw.decode("utf-8-sig"))
        except Exception as exc:
            last_error = exc
            if "CERTIFICATE_VERIFY_FAILED" in str(exc):
                print("SSL证书错误：", exc)
                break
            if attempt < retries:
                continue

    # 只对 marksix6.net 做受控 fallback
    if "marksix6.net" in url:
        print("⚠️ 正常SSL验证失败")
        print("尝试受控SSL fallback...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(
                req,
                timeout=timeout,
                context=build_ssl_context(False),
            ) as resp:
                raw = resp.read()
                data = json.loads(raw.decode("utf-8-sig"))
                print("✅ SSL fallback成功")
                return data
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"API请求失败：{last_error}")


# ============================================================
# 数据库
# ============================================================

def connect_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_no TEXT NOT NULL UNIQUE,
            draw_date TEXT,
            numbers_json TEXT NOT NULL,
            special INTEGER NOT NULL,
            source TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_draws_date
        ON draws(draw_date, issue_no)
    """)
    conn.commit()


def save_draw(
    conn: sqlite3.Connection,
    issue_no: str,
    draw_date: str,
    numbers: List[int],
    special: int,
    source: str,
) -> str:
    numbers = [int(x) for x in numbers]
    all_numbers = numbers + [special]

    if len(all_numbers) != 7 or len(set(all_numbers)) != 7:
        return "invalid"

    if not all(1 <= n <= 49 for n in all_numbers):
        return "invalid"

    existing = conn.execute(
        "SELECT numbers_json, special FROM draws WHERE issue_no=?",
        (str(issue_no),),
    ).fetchone()

    payload = json.dumps(numbers, ensure_ascii=False)
    now = now_iso()

    if existing:
        if existing["numbers_json"] == payload and int(existing["special"]) == special:
            return "unchanged"

        conn.execute("""
            UPDATE draws
            SET draw_date=?, numbers_json=?, special=?, source=?, updated_at=?
            WHERE issue_no=?
        """, (draw_date, payload, special, source, now, str(issue_no)))
        conn.commit()
        return "updated"

    conn.execute("""
        INSERT INTO draws
        (issue_no, draw_date, numbers_json, special, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(issue_no),
        draw_date,
        payload,
        special,
        source,
        now,
        now,
    ))
    conn.commit()
    return "inserted"


def load_rows(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute("""
        SELECT issue_no, draw_date, numbers_json, special, source
        FROM draws
        ORDER BY draw_date DESC, issue_no DESC
    """).fetchall()

    result = []
    for r in rows:
        try:
            nums = json.loads(r["numbers_json"])
            nums = [int(x) for x in nums]
            special = int(r["special"])
            result.append({
                "issue_no": r["issue_no"],
                "draw_date": r["draw_date"] or "",
                "numbers": nums,
                "special": special,
                "source": r["source"] or "",
            })
        except Exception:
            continue

    return result


# ============================================================
# API 解析
# ============================================================

def identify_lottery(item: Dict[str, Any]) -> Optional[str]:
    raw_name = str(item.get("name", "")).strip().lower()
    raw_type = str(
        item.get("type")
        or item.get("code")
        or item.get("lottery")
        or ""
    ).strip().lower()

    text = raw_name + " " + raw_type

    if "newmacau" in text or "新澳门" in text:
        return "newMacau"

    if "oldmacau" in text or "老澳门" in text:
        return "oldMacau"

    if raw_type == "hk" or "香港" in text:
        return "hk"

    return None


def parse_numbers(value: Any) -> List[int]:
    if isinstance(value, list):
        result = []
        for x in value:
            if isinstance(x, dict):
                x = x.get("number") or x.get("num") or x.get("value")
            n = safe_int(x, -1)
            if 1 <= n <= 49:
                result.append(n)
        return result

    text = str(value or "")
    nums = [safe_int(x, -1) for x in re.findall(r"\d{1,2}", text)]
    return [x for x in nums if 1 <= x <= 49]


def parse_history_string(text: str) -> Optional[Tuple[str, List[int]]]:
    text = str(text).strip()

    # 常见格式：
    # 2026228期：38,26,08,06,29,18,23
    m = re.search(r"([0-9]{3,})\s*期[：:]\s*(.*)", text)
    if not m:
        # 兼容 “2026228: ...”
        m = re.search(r"([0-9]{3,})\s*[：:]\s*(.*)", text)

    if not m:
        return None

    issue = m.group(1)
    nums = parse_numbers(m.group(2))

    if len(nums) < 7:
        return None

    return issue, nums[:7]


def parse_history_api(payload: Dict[str, Any]) -> Dict[str, List[Tuple[str, str, List[int], int]]]:
    result = defaultdict(list)

    lottery_data = payload.get("lottery_data", [])
    if not isinstance(lottery_data, list):
        return result

    for item in lottery_data:
        if not isinstance(item, dict):
            continue

        key = identify_lottery(item)
        if not key:
            continue

        open_time = str(item.get("openTime") or "")
        date = open_time[:10] if open_time else datetime.now().strftime("%Y-%m-%d")

        history = item.get("history", [])
        if not isinstance(history, list):
            continue

        for raw in history:
            parsed = parse_history_string(raw)
            if not parsed:
                continue

            issue, nums = parsed
            result[key].append(
                (issue, date, nums[:6], nums[6])
            )

    return result


def parse_realtime_api(
    payload: Dict[str, Any],
    lottery_key: str,
) -> Optional[Tuple[str, str, List[int], int]]:
    candidates = []

    if isinstance(payload, dict):
        if isinstance(payload.get("lottery_data"), list):
            candidates.extend(payload["lottery_data"])

        for k in ("data", "result"):
            v = payload.get(k)
            if isinstance(v, list):
                candidates.extend(v)
            elif isinstance(v, dict):
                candidates.append(v)

        if not candidates:
            candidates.append(payload)

    elif isinstance(payload, list):
        candidates = payload

    for item in candidates:
        if not isinstance(item, dict):
            continue

        key = identify_lottery(item)
        if key and key != lottery_key:
            continue

        issue = str(
            item.get("expect")
            or item.get("issue")
            or item.get("issueNo")
            or item.get("drawNo")
            or ""
        ).strip()

        open_time = str(
            item.get("openTime")
            or item.get("drawTime")
            or item.get("drawDate")
            or ""
        )

        date = open_time[:10] if open_time else datetime.now().strftime("%Y-%m-%d")

        nums = parse_numbers(
            item.get("openCode")
            or item.get("numbers")
            or item.get("code")
            or ""
        )

        if len(nums) < 7:
            continue

        return issue, date, nums[:6], nums[6]

    return None


# ============================================================
# 数据同步
# ============================================================

def sync_history() -> Dict[str, int]:
    print("=" * 70)
    print("正在获取历史数据")
    print(API_HISTORY)
    print("=" * 70)

    payload = http_json(API_HISTORY)
    parsed = parse_history_api(payload)

    stats = {}

    print(f"历史API彩种数量：{len(payload.get('lottery_data', [])) if isinstance(payload, dict) else 0}")

    for key in DB_FILES:
        conn = connect_db(DB_FILES[key])
        init_db(conn)

        records = parsed.get(key, [])
        inserted = 0
        updated = 0

        print(f"同步历史：{LOTTERY_NAMES[key]}")
        print(f"API返回：{len(records)}期")

        # API通常新→旧；日期只作为排序辅助
        for issue, date, nums, special in records:
            status = save_draw(
                conn,
                issue,
                date,
                nums,
                special,
                "history_api",
            )
            if status == "inserted":
                inserted += 1
            elif status == "updated":
                updated += 1

        count = conn.execute("SELECT COUNT(*) c FROM draws").fetchone()["c"]
        print(f"{LOTTERY_NAMES[key]} 数据库现有：{count}期")
        if inserted or updated:
            print(f"新增：{inserted} 更新：{updated}")

        stats[key] = inserted
        conn.close()

    return stats


def sync_realtime() -> Dict[str, bool]:
    result = {}

    for key in DB_FILES:
        print("=" * 70)
        print(f"正在更新：{LOTTERY_NAMES[key]}")
        print("=" * 70)

        url = f"{API_REALTIME}?type={key}"

        try:
            payload = http_json(url)
            parsed = parse_realtime_api(payload, key)

            if not parsed:
                print("⚠️ 无法解析实时开奖")
                result[key] = False
                continue

            issue, date, nums, special = parsed

            print("解析开奖：1期")
            print("期号：", issue)
            print("开奖号码：", " ".join(fmt_num(n) for n in nums + [special]))
            print("生肖：", ",".join(get_zodiac(n) for n in nums + [special]))
            print("波色：", ",".join(get_wave(n) for n in nums + [special]))

            conn = connect_db(DB_FILES[key])
            init_db(conn)

            status = save_draw(
                conn,
                issue,
                date,
                nums,
                special,
                "realtime_api",
            )

            count = conn.execute("SELECT COUNT(*) c FROM draws").fetchone()["c"]
            print(f"数据库现有：{count}期")
            if status == "inserted":
                print("本次新增：1期")
            else:
                print("本次新增：0期")

            conn.close()
            result[key] = True

        except Exception as exc:
            print("❌ 实时API失败：", exc)
            result[key] = False

    return result


# ============================================================
# 特码历史特征
# ============================================================

def specials(rows: List[Dict[str, Any]]) -> List[int]:
    return [int(r["special"]) for r in rows if 1 <= int(r["special"]) <= 49]


def frequency_feature(sp: List[int], window: int) -> Dict[int, float]:
    data = sp[:window]
    counter = Counter(data)

    # 轻微贝叶斯平滑，避免未出现号码直接成为0
    total = len(data)
    return {
        n: (counter[n] + 0.5) / (total + 24.5)
        for n in ALL_NUMBERS
    }


def omission_feature(sp: List[int], cap: int = 60) -> Dict[int, float]:
    result = {}
    for n in ALL_NUMBERS:
        miss = cap
        for i, x in enumerate(sp):
            if x == n:
                miss = i
                break
        result[n] = min(miss, cap) / cap

    # 过度遗漏不应无限加分
    return result


def momentum_feature(sp: List[int]) -> Dict[int, float]:
    short = frequency_feature(sp, 12)
    medium = frequency_feature(sp, 36)

    return {
        n: clamp(short[n] / max(medium[n], 1e-9) - 0.5)
        for n in ALL_NUMBERS
    }


def trend_feature(sp: List[int]) -> Dict[int, float]:
    f12 = frequency_feature(sp, 12)
    f36 = frequency_feature(sp, 36)
    f120 = frequency_feature(sp, 120)

    result = {}
    for n in ALL_NUMBERS:
        result[n] = (
            0.55 * f12[n]
            + 0.30 * f36[n]
            + 0.15 * f120[n]
        )
    return normalize_map(result)


def adjacency_feature(sp: List[int]) -> Dict[int, float]:
    result = {n: 0.0 for n in ALL_NUMBERS}

    for idx, base in enumerate(sp[:12]):
        weight = 1.0 / (1.0 + idx * 0.35)
        for delta, bonus in ((1, 1.0), (2, 0.65), (3, 0.30)):
            for candidate in (base - delta, base + delta):
                if 1 <= candidate <= 49:
                    result[candidate] += bonus * weight

    return normalize_map(result)


def tail_feature(sp: List[int]) -> Dict[int, float]:
    counts = Counter(n % 10 for n in sp[:36])
    score = {}
    for n in ALL_NUMBERS:
        # 不把冷尾当成必出，只做小权重
        score[n] = 1.0 / (1.0 + counts[n % 10])
    return normalize_map(score)


def zone_feature(sp: List[int]) -> Dict[int, float]:
    counts = Counter(get_zone(n) for n in sp[:36])
    score = {}
    for n in ALL_NUMBERS:
        score[n] = 1.0 / (1.0 + counts[get_zone(n)])
    return normalize_map(score)


def attribute_feature(sp: List[int], attr: str) -> Dict[int, float]:
    counts = Counter()

    for n in sp[:36]:
        if attr == "size":
            counts[get_size(n)] += 1
        elif attr == "parity":
            counts[get_parity(n)] += 1
        elif attr == "wave":
            counts[get_wave(n)] += 1

    total = sum(counts.values())
    if total <= 0:
        return {n: 0.5 for n in ALL_NUMBERS}

    probs = {
        k: (v + 1.0) / (total + len(counts) + 1.0)
        for k, v in counts.items()
    }

    if attr == "size":
        return {
            n: probs.get(get_size(n), 0.5)
            for n in ALL_NUMBERS
        }

    if attr == "parity":
        return {
            n: probs.get(get_parity(n), 0.5)
            for n in ALL_NUMBERS
        }

    return {
        n: probs.get(get_wave(n), 1 / 3)
        for n in ALL_NUMBERS
    }


# ============================================================
# 状态识别
# ============================================================

def market_state(sp: List[int]) -> Dict[str, Any]:
    recent = sp[:12]
    medium = sp[:36]

    wave_counts = Counter(get_wave(n) for n in recent)
    parity_counts = Counter(get_parity(n) for n in recent)
    size_counts = Counter(get_size(n) for n in recent)

    wave_entropy = entropy_from_counts(wave_counts)
    parity_entropy = entropy_from_counts(parity_counts)
    size_entropy = entropy_from_counts(size_counts)

    # 波色理论最大熵约1.585
    wave_balance = wave_entropy / math.log(3, 2) if math.log(3, 2) else 1.0

    # 最近 vs 中期的波色分布偏移
    def distribution(data, func, categories):
        c = Counter(func(x) for x in data)
        total = max(1, len(data))
        return {k: c[k] / total for k in categories}

    r = distribution(recent, get_wave, ALL_WAVES)
    m = distribution(medium, get_wave, ALL_WAVES)

    shift = sum(abs(r[c] - m[c]) for c in ALL_WAVES) / 2.0

    if wave_balance < 0.72 or shift >= 0.20:
        state = "偏态"
    elif wave_balance >= 0.90 and shift < 0.12:
        state = "平衡"
    else:
        state = "过渡"

    return {
        "state": state,
        "wave_entropy": round(wave_entropy, 4),
        "wave_balance": round(wave_balance, 4),
        "wave_shift": round(shift, 4),
        "parity_entropy": round(parity_entropy, 4),
        "size_entropy": round(size_entropy, 4),
    }


# ============================================================
# 动态模块权重
# ============================================================

BASE_MODULE_WEIGHTS = {
    "frequency": 0.20,
    "trend": 0.16,
    "momentum": 0.14,
    "omission": 0.08,
    "adjacency": 0.07,
    "tail": 0.06,
    "zone": 0.05,
    "size": 0.08,
    "parity": 0.07,
    "wave": 0.09,
}


def dynamic_weights(
    state: Dict[str, Any],
    performance: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    weights = BASE_MODULE_WEIGHTS.copy()
    market = state["state"]

    if market == "偏态":
        weights["trend"] += 0.035
        weights["momentum"] += 0.025
        weights["frequency"] += 0.015
        weights["omission"] -= 0.025
        weights["zone"] -= 0.015
        weights["tail"] -= 0.010

    elif market == "平衡":
        weights["frequency"] += 0.025
        weights["omission"] += 0.015
        weights["trend"] -= 0.015
        weights["momentum"] -= 0.015
        weights["adjacency"] -= 0.010

    else:
        weights["frequency"] += 0.015
        weights["trend"] += 0.010
        weights["momentum"] -= 0.010
        weights["omission"] -= 0.010
        weights["adjacency"] -= 0.005

    # 根据最近 Walk-Forward 表现做小幅调整
    # 限制调整幅度，避免过拟合
    if performance:
        for name, score in performance.items():
            if name not in weights:
                continue
            factor = 0.75 + 0.50 * clamp(score)
            weights[name] *= factor

    # 不允许负数
    weights = {k: max(0.001, v) for k, v in weights.items()}

    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


# ============================================================
# 单个模块评分
# ============================================================

def build_modules(sp: List[int]) -> Dict[str, Dict[int, float]]:
    modules = {
        "frequency": normalize_map(frequency_feature(sp, 12)),
        "trend": trend_feature(sp),
        "momentum": momentum_feature(sp),
        "omission": omission_feature(sp),
        "adjacency": adjacency_feature(sp),
        "tail": tail_feature(sp),
        "zone": zone_feature(sp),
        "size": attribute_feature(sp, "size"),
        "parity": attribute_feature(sp, "parity"),
        "wave": attribute_feature(sp, "wave"),
    }

    # 每个模块统一到0~1
    for name, values in modules.items():
        modules[name] = normalize_map(values)

    return modules


def combine_number_scores(
    sp: List[int],
    weights: Dict[str, float],
) -> Dict[int, float]:
    modules = build_modules(sp)

    raw = {n: 0.0 for n in ALL_NUMBERS}

    for module, w in weights.items():
        scores = modules[module]
        for n in ALL_NUMBERS:
            raw[n] += w * scores.get(n, 0.5)

    # 不再直接 minmax 作为“概率”
    # 这里只生成排名分数
    return normalize_map(raw, 0.5)


# ============================================================
# 属性预测
# ============================================================

def probability_by_attr(
    sp: List[int],
    attr: str,
    window: int = 36,
) -> Dict[str, float]:
    data = sp[:window]

    if attr == "size":
        cats = ALL_SIZE
        func = get_size
    elif attr == "parity":
        cats = ALL_PARITY
        func = get_parity
    else:
        cats = ALL_WAVES
        func = get_wave

    c = Counter(func(n) for n in data)
    total = len(data)

    if total <= 0:
        return {x: 1.0 / len(cats) for x in cats}

    # Laplace平滑
    alpha = 1.0
    denom = total + alpha * len(cats)

    return {
        x: (c[x] + alpha) / denom
        for x in cats
    }


# ============================================================
# 波色 V3
# ============================================================

def color_transition_probability(sp: List[int]) -> Dict[str, float]:
    colors = [get_wave(n) for n in sp[:36]]
    if len(colors) < 2:
        return {c: 1 / 3 for c in ALL_WAVES}

    current = colors[0]
    counts = Counter()

    for i in range(1, len(colors)):
        prev = colors[i]
        # rows 是新→旧，因此 prev 后面是更旧；
        # 这里使用所有“当前状态”的历史转移关系。
        if prev == current:
            if i + 1 < len(colors):
                counts[colors[i + 1]] += 1

    total = sum(counts.values())
    if total <= 0:
        return {c: 1 / 3 for c in ALL_WAVES}

    return {
        c: (counts[c] + 1) / (total + 3)
        for c in ALL_WAVES
    }


def color_omission(sp: List[int]) -> Dict[str, float]:
    result = {}
    for c in ALL_WAVES:
        miss = len(sp)
        for i, n in enumerate(sp):
            if get_wave(n) == c:
                miss = i
                break
        result[c] = min(miss, 30) / 30.0
    return result


def predict_wave(sp: List[int]) -> Dict[str, Any]:
    recent = sp[:12]
    medium = sp[:36]

    # 近期衰减
    recent_score = {c: 0.0 for c in ALL_WAVES}
    total_w = 0.0
    for i, n in enumerate(recent):
        w = 1.0 / (1.0 + i * 0.30)
        recent_score[get_wave(n)] += w
        total_w += w

    if total_w:
        recent_score = {c: recent_score[c] / total_w for c in ALL_WAVES}

    medium_p = probability_by_attr(medium, "wave", len(medium))
    omit = color_omission(sp)
    trans = color_transition_probability(sp)

    # 最近占主导，遗漏只作轻微补偿
    score = {}
    for c in ALL_WAVES:
        score[c] = (
            0.45 * recent_score[c]
            + 0.25 * medium_p[c]
            + 0.20 * trans[c]
            + 0.10 * omit[c]
        )

    # 连续同色时，轻微抑制，不强制反转
    if recent:
        last = get_wave(recent[0])
        streak = 0
        for n in recent:
            if get_wave(n) == last:
                streak += 1
            else:
                break

        if streak >= 3:
            score[last] *= 0.80
        elif streak == 2:
            score[last] *= 0.92

    probs = softmax(score, temperature=0.08)
    ranked = sorted(probs.items(), key=lambda x: x[1], reverse=True)

    main = ranked[0][0]
    second = ranked[1][0]

    return {
        "single": main,
        "double": [main, second],
        "exclude": ranked[2][0],
        "probability": {c: round(probs[c], 6) for c in ALL_WAVES},
        "scores": {c: round(score[c], 6) for c in ALL_WAVES},
    }


# ============================================================
# 生肖
# ============================================================

def zodiac_scores(number_scores: Dict[int, float]) -> Dict[str, float]:
    result = {z: 0.0 for z in ZODIAC_MAP_2026}

    for n, score in number_scores.items():
        z = get_zodiac(n)
        if z in result:
            result[z] += score

    return normalize_map(result, 0.5)


def pingte_zodiac_scores(
    sp: List[int],
    number_scores: Dict[int, float],
) -> Dict[str, float]:
    history = Counter(get_zodiac(n) for n in sp[:36])

    raw = {}
    total = max(1, sum(history.values()))

    for z, nums in ZODIAC_MAP_2026.items():
        avg_num = sum(number_scores.get(n, 0.5) for n in nums) / len(nums)
        freq = history[z] / total

        # 平特不完全等同于特码生肖
        raw[z] = 0.72 * avg_num + 0.18 * freq + 0.10 * (1.0 - freq)

    return normalize_map(raw, 0.5)


# ============================================================
# 动态模块表现：轻量 Walk-Forward
# ============================================================

def module_accuracy(
    sp: List[int],
    module_name: str,
    test_size: int = 20,
) -> float:
    if len(sp) < 45:
        return 0.5

    start = min(test_size, len(sp) - 25)
    hits = 0
    total = 0

    # rows 为新→旧。
    # 对每个历史目标 i，训练数据必须只使用更旧的数据。
    for i in range(start):
        train = sp[i + 1:]

        if len(train) < 24:
            continue

        modules = build_modules(train)
        values = modules.get(module_name)
        if not values:
            continue

        pred = max(values.items(), key=lambda x: x[1])[0]

        actual = sp[i]

        if module_name in ("frequency", "trend", "momentum", "omission", "adjacency", "tail", "zone"):
            if pred == actual:
                hits += 1
        elif module_name == "size":
            if get_size(pred) == get_size(actual):
                hits += 1
        elif module_name == "parity":
            if get_parity(pred) == get_parity(actual):
                hits += 1
        elif module_name == "wave":
            if get_wave(pred) == get_wave(actual):
                hits += 1

        total += 1

    return hits / total if total else 0.5


def estimate_module_performance(sp: List[int]) -> Dict[str, float]:
    # 为避免每次运行过慢，只用最近20个目标期
    modules = list(BASE_MODULE_WEIGHTS.keys())
    return {
        m: round(module_accuracy(sp, m, test_size=20), 4)
        for m in modules
    }


# ============================================================
# 预测主引擎
# ============================================================

def generate_prediction(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    sp = specials(rows)

    if len(sp) < 20:
        return {"error": f"历史数据不足：{len(sp)}期，至少需要20期"}

    state = market_state(sp)
    performance = estimate_module_performance(sp)
    weights = dynamic_weights(state, performance)

    scores = combine_number_scores(sp, weights)

    ranking = sorted(
        scores.items(),
        key=lambda x: (-x[1], x[0]),
    )

    top10 = ranking[:10]
    top3 = ranking[:3]

    z_scores = zodiac_scores(scores)
    pz_scores = pingte_zodiac_scores(sp, scores)

    top5_z = sorted(
        z_scores.items(),
        key=lambda x: (-x[1], x[0]),
    )[:5]

    top2_pz = sorted(
        pz_scores.items(),
        key=lambda x: (-x[1], x[0]),
    )[:2]

    size_p = probability_by_attr(sp, "size", 36)
    parity_p = probability_by_attr(sp, "parity", 36)
    wave = predict_wave(sp)

    # 真正的“相对概率”用softmax，仅用于解释，不宣称真实中奖概率
    rank_probability = softmax(
        {n: s for n, s in ranking},
        temperature=0.22,
    )

    return {
        "market_state": state,
        "module_performance": performance,
        "dynamic_weights": {
            k: round(v, 4)
            for k, v in weights.items()
        },

        "top10_numbers": [
            {
                "number": n,
                "score": round(score, 6),
                "relative_probability": round(rank_probability[n], 6),
            }
            for n, score in top10
        ],

        "top3_numbers": [n for n, _ in top3],
        "first_number": top3[0][0],

        "top5_zodiac": [
            {"zodiac": z, "score": round(s, 6)}
            for z, s in top5_z
        ],

        "top2_pingte_zodiac": [
            {"zodiac": z, "score": round(s, 6)}
            for z, s in top2_pz
        ],

        "size": {
            "prediction": max(size_p, key=size_p.get),
            "probability": {
                k: round(v, 6) for k, v in size_p.items()
            },
        },

        "parity": {
            "prediction": max(parity_p, key=parity_p.get),
            "probability": {
                k: round(v, 6) for k, v in parity_p.items()
            },
        },

        "wave": {
            "single": wave["single"],
            "double": wave["double"],
            "exclude": wave["exclude"],
            "probability": wave["probability"],
        },

        "data_count": len(sp),
    }


# ============================================================
# Walk-Forward
# ============================================================

def predict_from_history(train_sp: List[int]) -> Dict[str, Any]:
    if len(train_sp) < 20:
        return {}

    state = market_state(train_sp)
    # 回测时不使用目标期之后的数据
    weights = dynamic_weights(state, None)
    scores = combine_number_scores(train_sp, weights)

    ranking = sorted(
        scores.items(),
        key=lambda x: (-x[1], x[0]),
    )

    top10 = [n for n, _ in ranking[:10]]

    z_scores = zodiac_scores(scores)
    top5_z = [
        z for z, _ in sorted(
            z_scores.items(),
            key=lambda x: (-x[1], x[0]),
        )[:5]
    ]

    pz_scores = pingte_zodiac_scores(train_sp, scores)
    top2_pz = [
        z for z, _ in sorted(
            pz_scores.items(),
            key=lambda x: (-x[1], x[0]),
        )[:2]
    ]

    size_p = probability_by_attr(train_sp, "size", 36)
    parity_p = probability_by_attr(train_sp, "parity", 36)
    wave = predict_wave(train_sp)

    return {
        "top10": top10,
        "zodiac5": top5_z,
        "pingte2": top2_pz,
        "size": max(size_p, key=size_p.get),
        "parity": max(parity_p, key=parity_p.get),
        "wave_single": wave["single"],
        "wave_double": wave["double"],
    }


def empty_metric() -> Dict[str, Any]:
    return {"total": 0, "hit": 0, "rate": 0.0}


def add_hit(metric: Dict[str, Any], ok: bool) -> None:
    metric["total"] += 1
    if ok:
        metric["hit"] += 1
    metric["rate"] = (
        metric["hit"] / metric["total"]
        if metric["total"]
        else 0.0
    )


def walk_forward(rows: List[Dict[str, Any]], test_size: int) -> Dict[str, Any]:
    sp = specials(rows)

    result = {
        "test_size": test_size,
        "valid_tests": 0,
        "number10": empty_metric(),
        "zodiac5": empty_metric(),
        "pingte2": empty_metric(),
        "size": empty_metric(),
        "parity": empty_metric(),
        "wave_single": empty_metric(),
        "wave_double": empty_metric(),
    }

    if len(sp) < 30:
        result["error"] = "历史样本不足"
        return result

    # 只测试最近 test_size 个目标期
    start = min(test_size, len(sp) - 20)

    # sp[0] 是最新。
    # 目标 i 的训练集为 sp[i+1:]，不包含目标本身。
    for i in range(start):
        train = sp[i + 1:]
        actual = sp[i]

        if len(train) < 20:
            continue

        pred = predict_from_history(train)
        if not pred:
            continue

        result["valid_tests"] += 1

        add_hit(
            result["number10"],
            actual in pred["top10"],
        )

        add_hit(
            result["zodiac5"],
            get_zodiac(actual) in pred["zodiac5"],
        )

        add_hit(
            result["pingte2"],
            get_zodiac(actual) in pred["pingte2"],
        )

        add_hit(
            result["size"],
            get_size(actual) == pred["size"],
        )

        add_hit(
            result["parity"],
            get_parity(actual) == pred["parity"],
        )

        actual_wave = get_wave(actual)

        add_hit(
            result["wave_single"],
            actual_wave == pred["wave_single"],
        )

        add_hit(
            result["wave_double"],
            actual_wave in pred["wave_double"],
        )

    if result["valid_tests"] == 0:
        result["error"] = "没有有效测试"

    return result


# ============================================================
# 输出
# ============================================================

def print_prediction(key: str, prediction: Dict[str, Any]) -> None:
    print("=" * 70)
    print(f"{LOTTERY_NAMES[key]} ({key})")
    print("=" * 70)

    top10 = prediction["top10_numbers"]

    print("【特码10码】")
    print(" ".join(fmt_num(x["number"]) for x in top10))

    print("【49码综合评分 Top10】")
    for i, item in enumerate(top10, 1):
        print(
            f"第{i:02d}名 {item['number']:02d} "
            f"评分：{item['score']:.4f} "
            f"相对概率：{item['relative_probability'] * 100:.2f}%"
        )

    print("【下一期重点推荐】")
    print(" ".join(fmt_num(n) for n in prediction["top3_numbers"]))
    print(
        f"第一推荐：{fmt_num(prediction['first_number'])} "
        f"模型评分：{next(x['score'] for x in top10 if x['number'] == prediction['first_number']):.4f}"
    )

    print("【特码生肖5肖】")
    print(" ".join(x["zodiac"] for x in prediction["top5_zodiac"]))

    print("【平特生肖2肖】")
    print(" ".join(x["zodiac"] for x in prediction["top2_pingte_zodiac"]))

    print(
        "【大小】",
        prediction["size"]["prediction"],
        prediction["size"]["probability"],
    )

    print(
        "【单双】",
        prediction["parity"]["prediction"],
        prediction["parity"]["probability"],
    )

    print("【波色单推】", prediction["wave"]["single"])
    print(
        "【波色双推】",
        " + ".join(prediction["wave"]["double"]),
    )
    print(
        "【波色排除】",
        prediction["wave"]["exclude"],
    )
    print(
        "【波色概率】",
        prediction["wave"]["probability"],
    )

    print("【V3.0当前市场状态】", prediction["market_state"]["state"])
    print("【V3.0动态模块权重】")
    for k, v in prediction["dynamic_weights"].items():
        print(f"  {k:<10} {v:.4f}")

    print("【模块最近20期表现】")
    for k, v in prediction["module_performance"].items():
        print(f"  {k:<10} {v * 100:.2f}%")


def print_backtest(key: str, bt: Dict[str, Any]) -> None:
    print("=" * 70)
    print(f"{LOTTERY_NAMES[key]} Walk-Forward回测")
    print("=" * 70)

    if bt.get("error"):
        print("错误：", bt["error"])
        return

    print(f"有效测试期数：{bt['valid_tests']}")

    labels = [
        ("number10", "特码10码命中率"),
        ("zodiac5", "生肖5肖命中率"),
        ("pingte2", "平特2肖命中率"),
        ("size", "大小命中率"),
        ("parity", "单双命中率"),
        ("wave_single", "波色单推命中率"),
        ("wave_double", "波色双推命中率"),
    ]

    for key2, label in labels:
        m = bt[key2]
        print(
            f"{label}：{m['rate'] * 100:.2f}% "
            f"({m['hit']}/{m['total']})"
        )

    single = bt["wave_single"]["rate"]
    double = bt["wave_double"]["rate"]
    print(f"波色双推提升：{(double - single) * 100:+.2f}%")


# ============================================================
# 主程序
# ============================================================

def main() -> None:
    print("=" * 70)
    print("六合彩AI智能预测系统 V3.0")
    print("工作流：同步 → 状态识别 → 动态权重 → 预测 → Walk-Forward")
    print(datetime.now().isoformat())
    print("=" * 70)

    # --------------------------------------------------------
    # 1. 初始化数据库
    # --------------------------------------------------------
    print("【步骤1】初始化数据库")

    for key, path in DB_FILES.items():
        conn = connect_db(path)
        init_db(conn)
        conn.close()

    print("✅ 数据库初始化完成")

    # --------------------------------------------------------
    # 2. 同步历史
    # --------------------------------------------------------
    print("=" * 70)
    print("【步骤2】同步在线数据")
    print("=" * 70)

    history_stats = {}
    try:
        history_stats = sync_history()
    except Exception as exc:
        print("⚠️ 历史API同步失败：", exc)

    realtime = sync_realtime()

    print("=" * 70)
    print("数据同步完成")
    print("=" * 70)

    for key in DB_FILES:
        conn = connect_db(DB_FILES[key])
        count = conn.execute("SELECT COUNT(*) c FROM draws").fetchone()["c"]
        conn.close()
        print(f"{LOTTERY_NAMES[key]}: {count}期")

    print(
        "实时API成功："
        f"{sum(1 for x in realtime.values() if x)}/3"
    )
    print(
        "历史新增：",
        sum(history_stats.values()) if history_stats else 0,
    )

    # --------------------------------------------------------
    # 3. 三彩种预测
    # --------------------------------------------------------
    all_predictions = {}
    all_backtests = {}

    for key, path in DB_FILES.items():
        print("#" * 70)
        print(f"开始分析：{LOTTERY_NAMES[key]}")
        print("#" * 70)

        conn = connect_db(path)
        rows = load_rows(conn)
        conn.close()

        print(f"历史数据：{len(rows)}期")
        print("-" * 70)
        print("【步骤3】生成下一期预测")

        prediction = generate_prediction(rows)

        if prediction.get("error"):
            print("❌", prediction["error"])
            continue

        print_prediction(key, prediction)
        all_predictions[key] = prediction

        # ----------------------------------------------------
        # 4. Walk-Forward
        # 只保留最近10/20，不再输出30/60/100
        # ----------------------------------------------------
        print("-" * 70)
        print("【步骤4】Walk-Forward历史回测")

        bt10 = walk_forward(rows, 10)
        bt20 = walk_forward(rows, 20)

        all_backtests[key] = {
            "recent10": bt10,
            "recent20": bt20,
        }

        print(f"\n【最近10期】")
        print_backtest(key, bt10)

        print(f"\n【最近20期】")
        print_backtest(key, bt20)

    # --------------------------------------------------------
    # 5. 保存预测
    # --------------------------------------------------------
    print("-" * 70)
    print("【步骤5】保存预测结果")

    prediction_path = OUTPUT_DIR / "prediction.json"

    prediction_payload = {
        "version": "V3.0",
        "generated_at": datetime.now().isoformat(),
        "note": (
            "模型评分用于排序；relative_probability为模型内部相对分布，"
            "不代表真实中奖概率。"
        ),
        "lotteries": all_predictions,
    }

    prediction_path.write_text(
        json.dumps(
            prediction_payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("✅ 预测结果已保存")
    print("文件：", prediction_path)

    # --------------------------------------------------------
    # 6. 保存回测
    # --------------------------------------------------------
    print("-" * 70)
    print("【步骤6】保存回测结果")

    backtest_path = OUTPUT_DIR / "backtest.json"

    backtest_payload = {
        "version": "V3.0",
        "generated_at": datetime.now().isoformat(),
        "windows": [10, 20],
        "note": (
            "采用Walk-Forward，每个目标期的预测只使用目标期之前的数据，"
            "避免未来数据泄漏。"
        ),
        "lotteries": all_backtests,
    }

    backtest_path.write_text(
        json.dumps(
            backtest_payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("✅ 回测结果已保存")
    print("文件：", backtest_path)

    print("=" * 70)
    print("本次运行完成")
    print("=" * 70)
    print("分析彩种：", len(all_predictions))
    print("预测文件：", prediction_path)
    print("回测文件：", backtest_path)
    print("=" * 70)
    print("系统运行结束")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(130)
    except Exception as exc:
        print("\n❌ 系统异常：", exc)
        raise
