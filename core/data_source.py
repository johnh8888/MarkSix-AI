# -*- coding: utf-8 -*-
"""
六合彩 AI V3.0 - 数据源同步
支持历史 + 实时 API，带受控 SSL fallback
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.request
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .config import (
    API_HISTORY,
    API_REALTIME,
    DB_FILES,
    LOTTERY_NAMES,
)
from .database import connect_db, init_db, save_draw, get_row_count


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

    for attempt in range(1, retries + 1):
        try:
            print(f"请求API 第{attempt}次 → {url}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(
                req, timeout=timeout, context=build_ssl_context(True)
            ) as resp:
                return json.loads(resp.read().decode("utf-8-sig"))
        except Exception as exc:
            last_error = exc
            if "CERTIFICATE_VERIFY_FAILED" in str(exc):
                print("SSL证书错误：", exc)
                break
            if attempt < retries:
                continue

    # 仅对 marksix6.net 做受控 fallback
    if "marksix6.net" in url:
        print("⚠️ 正常SSL验证失败，尝试受控SSL fallback...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(
                req, timeout=timeout, context=build_ssl_context(False)
            ) as resp:
                data = json.loads(resp.read().decode("utf-8-sig"))
                print("✅ SSL fallback成功")
                return data
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"API请求失败：{last_error}")


def safe_int(value: Any, default: int = -1) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def parse_numbers(value: Any) -> List[int]:
    if isinstance(value, list):
        result = []
        for x in value:
            if isinstance(x, dict):
                x = x.get("number") or x.get("num") or x.get("value")
            n = safe_int(x)
            if 1 <= n <= 49:
                result.append(n)
        return result

    text = str(value or "")
    nums = [safe_int(x) for x in re.findall(r"\d{1,2}", text)]
    return [x for x in nums if 1 <= x <= 49]


def identify_lottery(item: Dict[str, Any]) -> Optional[str]:
    raw_name = str(item.get("name", "")).strip().lower()
    raw_type = str(
        item.get("type") or item.get("code") or item.get("lottery") or ""
    ).strip().lower()
    text = raw_name + " " + raw_type

    if "newmacau" in text or "新澳门" in text:
        return "newMacau"
    if "oldmacau" in text or "老澳门" in text:
        return "oldMacau"
    if raw_type == "hk" or "香港" in text:
        return "hk"
    return None


def parse_history_string(text: str) -> Optional[Tuple[str, List[int]]]:
    text = str(text).strip()
    m = re.search(r"([0-9]{3,})\s*期[：:]\s*(.*)", text)
    if not m:
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
            result[key].append((issue, date, nums[:6], nums[6]))

    return result


def parse_realtime_api(
    payload: Any, lottery_key: str
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
            item.get("openCode") or item.get("numbers") or item.get("code") or ""
        )
        if len(nums) < 7:
            continue
        return issue, date, nums[:6], nums[6]

    return None


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
        inserted = updated = 0

        print(f"同步历史：{LOTTERY_NAMES[key]} → API返回 {len(records)} 期")

        for issue, date, nums, special in records:
            status = save_draw(conn, issue, date, nums, special, "history_api")
            if status == "inserted":
                inserted += 1
            elif status == "updated":
                updated += 1

        count = get_row_count(conn)
        print(f"{LOTTERY_NAMES[key]} 数据库现有：{count} 期")
        if inserted or updated:
            print(f"  新增：{inserted}  更新：{updated}")

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
            print("期号：", issue)
            print("开奖号码：", " ".join(f"{n:02d}" for n in nums + [special]))

            conn = connect_db(DB_FILES[key])
            init_db(conn)
            status = save_draw(conn, issue, date, nums, special, "realtime_api")
            count = get_row_count(conn)
            print(f"数据库现有：{count} 期  本次：{status}")
            conn.close()
            result[key] = True

        except Exception as exc:
            print("❌ 实时API失败：", exc)
            result[key] = False

    return result


def sync_all() -> Dict[str, int]:
    """历史 + 实时一起同步，返回各彩种新增数量"""
    history_stats = {}
    try:
        history_stats = sync_history()
    except Exception as exc:
        print("⚠️ 历史API同步失败：", exc)

    realtime = sync_realtime()
    print("=" * 70)
    print("数据同步完成")
    print(f"实时API成功：{sum(1 for x in realtime.values() if x)}/3")
    print(f"历史新增：{sum(history_stats.values()) if history_stats else 0}")
    return history_stats
