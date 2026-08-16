# -*- coding: utf-8 -*-

"""
六合彩特征计算模块

重要说明：

数据库当前结构没有 special 字段：

draws:
    lottery
    name
    issue
    open_time
    numbers
    zodiac
    wave
    source
    created_at

因此特码统一从 numbers 的第 7 个号码读取。

例如：

numbers = "38,26,08,06,29,18,23"

special = 23
"""

from collections import Counter
from typing import Any, Dict, List


# =========================================================
# 基础解析
# =========================================================

def parse_numbers(row) -> List[int]:
    """
    从数据库 row 中读取 7 个开奖号码。

    支持：

    numbers = "38,26,08,06,29,18,23"

    或：

    numbers = ["38", "26", ...]
    """

    if row is None:
        return []

    # -----------------------------------------------------
    # numbers
    # -----------------------------------------------------

    try:
        value = row["numbers"]
    except (KeyError, TypeError, IndexError):
        return []

    if value is None:
        return []

    # -----------------------------------------------------
    # list / tuple
    # -----------------------------------------------------

    if isinstance(value, (list, tuple)):

        result = []

        for item in value:

            try:

                n = int(str(item).strip())

                if 1 <= n <= 49:
                    result.append(n)

            except (TypeError, ValueError):
                continue

        return result

    # -----------------------------------------------------
    # string
    # -----------------------------------------------------

    text = str(value).strip()

    if not text:
        return []

    # 支持：
    #
    # 38,26,08,06,29,18,23
    #
    # 以及：
    #
    # 38，26，08，06，29，18，23

    text = text.replace("，", ",")

    parts = text.split(",")

    result = []

    for item in parts:

        item = item.strip()

        if not item:
            continue

        try:

            n = int(item)

            if 1 <= n <= 49:
                result.append(n)

        except ValueError:
            continue

    return result


# =========================================================
# 取得特码
# =========================================================

def get_special(row) -> int:
    """
    获取特码。

    Mark Six 数据中：

    第 7 个号码 = 特码

    例如：

    33,27,16,28,04,25,14
                       ↑
                      特码

    返回：
        14
    """

    numbers = parse_numbers(row)

    if len(numbers) >= 7:

        return numbers[6]

    # -----------------------------------------------------
    # 兼容未来数据库可能增加 special 字段
    # -----------------------------------------------------

    try:

        value = row["special"]

        if value is not None:

            n = int(value)

            if 1 <= n <= 49:
                return n

    except (KeyError, TypeError, ValueError, IndexError):
        pass

    return 0


# =========================================================
# 所有号码
# =========================================================

def get_all_numbers(row) -> List[int]:

    return parse_numbers(row)


# =========================================================
# 特码频率
# =========================================================

def special_frequency(
    rows,
    limit: int = None
) -> Dict[int, int]:

    counter = Counter()

    if limit is not None:
        rows = rows[:limit]

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[n] += 1

    return dict(counter)


# =========================================================
# 特码遗漏
# =========================================================

def special_omission(
    rows,
    limit: int = 300
) -> Dict[int, int]:
    """
    计算 1~49 特码当前遗漏期数。

    rows 必须是：
        最新 -> 最旧

    例如：

    最新一期特码 = 23

    那么：

    23 -> 0
    其他号码 -> 根据距离最近出现的期数计算
    """

    rows = rows[:limit]

    omission = {
        n: len(rows)
        for n in range(1, 50)
    }

    for index, row in enumerate(rows):

        special = get_special(row)

        if 1 <= special <= 49:

            omission[special] = index

    return omission


# =========================================================
# 大小
# =========================================================

def get_size(number: int) -> str:

    number = int(number)

    return "大" if number >= 25 else "小"


# =========================================================
# 单双
# =========================================================

def get_odd_even(number: int) -> str:

    number = int(number)

    return "单" if number % 2 else "双"


# =========================================================
# 波色
# =========================================================

RED = {
    1, 2, 7, 8, 12, 13,
    18, 19, 23, 24, 29,
    30, 34, 35, 40, 45,
    46
}

BLUE = {
    3, 4, 9, 10, 14, 15,
    20, 25, 26, 31, 36,
    37, 41, 42, 47, 48
}

GREEN = {
    5, 6, 11, 16, 17,
    21, 22, 27, 28, 32,
    33, 38, 39, 43, 44,
    49
}


def get_wave(number: int) -> str:

    number = int(number)

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return "未知"


# =========================================================
# 尾数
# =========================================================

def get_tail(number: int) -> int:

    return int(number) % 10


# =========================================================
# MOD7
# =========================================================

def get_mod7(number: int) -> int:

    return int(number) % 7


# =========================================================
# 号码分区
# =========================================================

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


# =========================================================
# 特码大小历史统计
# =========================================================

def special_size_frequency(rows):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if n <= 0:
            continue

        counter[
            get_size(n)
        ] += 1

    return dict(counter)


# =========================================================
# 特码单双历史统计
# =========================================================

def special_parity_frequency(rows):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if n <= 0:
            continue

        counter[
            get_odd_even(n)
        ] += 1

    return dict(counter)


# =========================================================
# 特码波色历史统计
# =========================================================

def special_wave_frequency(rows):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if n <= 0:
            continue

        counter[
            get_wave(n)
        ] += 1

    return dict(counter)


# =========================================================
# 特码尾数统计
# =========================================================

def special_tail_frequency(rows):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if n <= 0:
            continue

        counter[
            get_tail(n)
        ] += 1

    return dict(counter)


# =========================================================
# 特码 MOD7 统计
# =========================================================

def special_mod7_frequency(rows):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if n <= 0:
            continue

        counter[
            get_mod7(n)
        ] += 1

    return dict(counter)


# =========================================================
# 特码分区统计
# =========================================================

def special_zone_frequency(rows):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if n <= 0:
            continue

        counter[
            get_zone(n)
        ] += 1

    return dict(counter)


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    test_row = {

        "numbers":
            "38,26,08,06,29,18,23"

    }

    print("=" * 70)
    print("features.py 测试")
    print("=" * 70)

    print(
        "开奖号码：",
        get_all_numbers(test_row)
    )

    print(
        "特码：",
        get_special(test_row)
    )

    print(
        "大小：",
        get_size(get_special(test_row))
    )

    print(
        "单双：",
        get_odd_even(get_special(test_row))
    )

    print(
        "波色：",
        get_wave(get_special(test_row))
    )

    print(
        "尾数：",
        get_tail(get_special(test_row))
    )

    print(
        "MOD7：",
        get_mod7(get_special(test_row))
    )

    print(
        "分区：",
        get_zone(get_special(test_row))
    )
