# -*- coding:utf-8 -*-

"""
六合彩 AI V3.0 FINAL

数据解析工具
"""

from __future__ import annotations

import re


def parse_numbers(value):
    """
    从任意输入中提取 1~49 的号码。
    """

    if value is None:
        return []

    if isinstance(value, list):
        values = value
    else:
        values = [value]

    result = []

    for item in values:

        matches = re.findall(
            r"(?<!\d)(\d{1,2})(?!\d)",
            str(item)
        )

        for x in matches:

            n = int(x)

            if 1 <= n <= 49:
                result.append(n)

    return result


def clean_numbers(numbers):
    """
    清洗号码。
    """

    result = []

    for x in numbers:

        try:
            n = int(x)
        except Exception:
            continue

        if 1 <= n <= 49:
            result.append(n)

    return result


def extract_specials(history):
    """
    从数据库历史记录提取特码。
    """

    result = []

    if not history:
        return result

    for row in history:

        if not isinstance(row, dict):
            continue

        value = row.get("special")

        try:

            n = int(value)

        except Exception:

            continue

        if 1 <= n <= 49:
            result.append(n)

    return result


def extract_numbers(history):
    """
    提取全部正码。
    """

    result = []

    if not history:
        return result

    for row in history:

        if not isinstance(row, dict):
            continue

        numbers = row.get(
            "numbers",
            []
        )

        if isinstance(numbers, list):

            for n in numbers:

                try:
                    n = int(n)
                except Exception:
                    continue

                if 1 <= n <= 49:
                    result.append(n)

    return result


def get_issue(row):
    """
    获取期号。
    """

    if not isinstance(row, dict):
        return None

    value = (
        row.get("issue")
        or row.get("expect")
        or row.get("period")
    )

    if value is None:
        return None

    return str(value)


__all__ = [
    "parse_numbers",
    "clean_numbers",
    "extract_specials",
    "extract_numbers",
    "get_issue"
]
