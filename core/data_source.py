# -*- coding: utf-8 -*-

import requests
import time

from .config import API_URLS, LOTTERIES
from .database import insert_draw


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/130 Safari/537.36"
    )
}


def normalize_number(value):

    try:

        if isinstance(value, int):
            return value

        value = str(value).strip()

        value = value.replace("号", "")
        value = value.replace(",", "")
        value = value.replace(" ", "")

        return int(value)

    except Exception:

        return None


def extract_numbers(item):

    # 优先 numbers
    numbers = item.get("numbers")

    if isinstance(numbers, list):

        result = []

        for n in numbers:

            n = normalize_number(n)

            if n is not None:
                result.append(n)

        if len(result) >= 7:
            return result[:7]

    # 尝试 openCode
    open_code = item.get("openCode")

    if open_code:

        if isinstance(open_code, str):

            parts = (
                open_code
                .replace("|", ",")
                .replace("/", ",")
                .replace(" ", ",")
                .split(",")
            )

            result = []

            for p in parts:

                n = normalize_number(p)

                if n is not None:
                    result.append(n)

            if len(result) >= 7:
                return result[:7]

    return []


def parse_record(item, lottery_key, source):

    if not isinstance(item, dict):
        return None

    issue = (
        item.get("expect")
        or item.get("issue")
        or item.get("period")
    )

    if issue is None:
        return None

    issue = str(issue).strip()

    numbers = extract_numbers(item)

    if len(numbers) != 7:
        return None

    # 检查号码范围
    if any(n < 1 or n > 49 for n in numbers):
        return None

    return {
        "lottery": lottery_key,
        "issue": issue,

        "open_time": (
            item.get("openTime")
            or item.get("open_time")
            or item.get("date")
        ),

        "numbers": numbers,

        "zodiac": item.get("zodiac"),
        "wave": item.get("wave"),

        "source": source,
    }


def request_api(url, api_type):

    try:

        response = requests.get(
            url,
            params={"type": api_type},
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        print(
            f"API失败: {url} "
            f"type={api_type} "
            f"error={e}"
        )

        return None


def find_lottery_data(payload, api_type):

    if not isinstance(payload, dict):
        return []

    # 常见结构
    lottery_data = payload.get("lottery_data")

    if isinstance(lottery_data, dict):

        if api_type in lottery_data:

            return lottery_data[api_type]

    if isinstance(lottery_data, list):

        return lottery_data

    # 其他可能结构
    for key in [
        "data",
        "result",
        "history"
    ]:

        value = payload.get(key)

        if isinstance(value, list):
            return value

    return []


def get_history_for_lottery(lottery_key):

    config = LOTTERIES[lottery_key]

    api_type = config["api_type"]

    for base_url in API_URLS:

        print(
            f"尝试数据源: "
            f"{base_url} "
            f"type={api_type}"
        )

        payload = request_api(
            base_url,
            api_type
        )

        if payload is None:
            continue

        data = find_lottery_data(
            payload,
            api_type
        )

        if not data:
            continue

        records = []

        # 当前数据
        if isinstance(data, dict):

            current = parse_record(
                data,
                lottery_key,
                base_url
            )

            if current:
                records.append(current)

            history = data.get("history", [])

            if isinstance(history, list):

                for item in history:

                    record = parse_record(
                        item,
                        lottery_key,
                        base_url
                    )

                    if record:
                        records.append(record)

        # history 本身就是 list
        elif isinstance(data, list):

            for item in data:

                record = parse_record(
                    item,
                    lottery_key,
                    base_url
                )

                if record:
                    records.append(record)

                if isinstance(item, dict):

                    history = item.get("history", [])

                    if isinstance(history, list):

                        for h in history:

                            record = parse_record(
                                h,
                                lottery_key,
                                base_url
                            )

                            if record:
                                records.append(record)

        # 去重
        unique = {}

        for record in records:

            key = record["issue"]

            unique[key] = record

        records = list(unique.values())

        if records:

            print(
                f"{config['name']} "
                f"获取 {len(records)} 期"
            )

            return records

    print(
        f"{config['name']} "
        f"所有数据源均失败"
    )

    return []


def update_lottery(lottery_key):

    records = get_history_for_lottery(
        lottery_key
    )

    inserted = 0

    for record in records:

        if insert_draw(record):

            inserted += 1

    print(
        f"{LOTTERIES[lottery_key]['name']} "
        f"新增 {inserted} 期"
    )

    return inserted


def update_all():

    total = 0

    for lottery_key in LOTTERIES:

        try:

            total += update_lottery(
                lottery_key
            )

        except Exception as e:

            print(
                f"{lottery_key} 更新失败:",
                e
            )

        time.sleep(1)

    return total
