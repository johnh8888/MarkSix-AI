# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
特征计算模块
"""

from collections import Counter
from math import log
from typing import Any, Dict, List


# =========================================================
# 常量
# =========================================================

NUMBERS = range(1, 50)


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


NUMBER_TO_WAVE = {}

for n in RED:
    NUMBER_TO_WAVE[n] = "红"

for n in BLUE:
    NUMBER_TO_WAVE[n] = "蓝"

for n in GREEN:
    NUMBER_TO_WAVE[n] = "绿"


WAVES = (
    "红",
    "蓝",
    "绿"
)


# =========================================================
# 解析号码
# =========================================================

def parse_numbers(row) -> List[int]:

    if row is None:
        return []

    try:
        value = row["numbers"]
    except (
        KeyError,
        TypeError,
        IndexError
    ):
        return []

    if value is None:
        return []

    # -----------------------------------------------------
    # list
    # -----------------------------------------------------

    if isinstance(
        value,
        (list, tuple)
    ):

        result = []

        for item in value:

            try:

                n = int(
                    str(item).strip()
                )

                if 1 <= n <= 49:
                    result.append(n)

            except (
                TypeError,
                ValueError
            ):
                continue

        return result

    # -----------------------------------------------------
    # string
    # -----------------------------------------------------

    text = str(value).strip()

    if not text:
        return []

    text = (
        text
        .replace("，", ",")
        .replace("|", ",")
        .replace("/", ",")
        .replace(" ", ",")
    )

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
# 特码
# =========================================================

def get_special(row) -> int:

    numbers = parse_numbers(row)

    if len(numbers) >= 7:
        return numbers[6]

    try:

        value = row["special"]

        n = int(value)

        if 1 <= n <= 49:
            return n

    except Exception:
        pass

    return 0


# =========================================================
# 全部号码
# =========================================================

def get_all_numbers(row):

    return parse_numbers(row)


# =========================================================
# 大小
# =========================================================

def get_size(number: int) -> str:

    return (
        "大"
        if int(number) >= 25
        else "小"
    )


# =========================================================
# 单双
# =========================================================

def get_odd_even(number: int) -> str:

    return (
        "单"
        if int(number) % 2
        else "双"
    )


# =========================================================
# 波色
# =========================================================

def get_wave(number: int) -> str:

    return NUMBER_TO_WAVE.get(
        int(number),
        "未知"
    )


# =========================================================
# 尾数
# =========================================================

def get_tail(number: int) -> int:

    return int(number) % 10


# =========================================================
# 分区
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
# 特码序列
# =========================================================

def special_sequence(rows):

    result = []

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:
            result.append(n)

    return result


# =========================================================
# 特码频率
# =========================================================

def special_frequency(
    rows,
    limit=None
):

    if limit is not None:
        rows = rows[:limit]

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:
            counter[n] += 1

    return dict(counter)


# =========================================================
# 加权近期频率
# =========================================================

def weighted_special_frequency(
    rows
):

    scores = {
        n: 0.0
        for n in NUMBERS
    }

    if not rows:
        return scores

    total = len(rows)

    for index, row in enumerate(rows):

        n = get_special(row)

        if not 1 <= n <= 49:
            continue

        # 最新权重最高
        weight = (
            (total - index)
            / total
        )

        scores[n] += weight

    return scores


# =========================================================
# 遗漏
# =========================================================

def special_omission(
    rows,
    limit=120
):

    rows = rows[:limit]

    omission = {
        n: len(rows)
        for n in NUMBERS
    }

    for index, row in enumerate(rows):

        n = get_special(row)

        if 1 <= n <= 49:

            # 最新数据 index=0
            # 因此 index 就是当前遗漏
            omission[n] = index

    return omission


# =========================================================
# 最近一次出现
# =========================================================

def last_seen_distance(
    rows
):

    result = {}

    for n in NUMBERS:
        result[n] = len(rows)

    for index, row in enumerate(rows):

        n = get_special(row)

        if n not in result:
            continue

        if result[n] == len(rows):
            result[n] = index

    return result


# =========================================================
# 大小统计
# =========================================================

def special_size_frequency(
    rows
):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:
            counter[
                get_size(n)
            ] += 1

    return dict(counter)


# =========================================================
# 单双统计
# =========================================================

def special_parity_frequency(
    rows
):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:
            counter[
                get_odd_even(n)
            ] += 1

    return dict(counter)


# =========================================================
# 波色统计
# =========================================================

def special_wave_frequency(
    rows
):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            wave = get_wave(n)

            if wave != "未知":
                counter[wave] += 1

    return dict(counter)


# =========================================================
# 尾数
# =========================================================

def special_tail_frequency(
    rows
):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[
                get_tail(n)
            ] += 1

    return dict(counter)


# =========================================================
# 分区
# =========================================================

def special_zone_frequency(
    rows
):

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[
                get_zone(n)
            ] += 1

    return dict(counter)


# =========================================================
# 波色序列
# =========================================================

def wave_sequence(rows):

    result = []

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            wave = get_wave(n)

            if wave in WAVES:
                result.append(wave)

    return result


# =========================================================
# 波色转移矩阵
# =========================================================

def wave_transition_matrix(
    rows
):

    """
    计算：

    红 -> 红 / 蓝 / 绿
    蓝 -> 红 / 蓝 / 绿
    绿 -> 红 / 蓝 / 绿

    rows:
        最新 -> 最旧

    因为方向是：
        当前旧状态 -> 下一期新状态
    """

    sequence = wave_sequence(rows)

    matrix = {

        "红": {
            "红": 0,
            "蓝": 0,
            "绿": 0,
        },

        "蓝": {
            "红": 0,
            "蓝": 0,
            "绿": 0,
        },

        "绿": {
            "红": 0,
            "蓝": 0,
            "绿": 0,
        },
    }

    if len(sequence) < 2:
        return matrix

    # sequence 是 最新 -> 最旧
    # 因此反向遍历才是时间正向

    chronological = list(
        reversed(sequence)
    )

    for i in range(
        len(chronological) - 1
    ):

        current = chronological[i]

        nxt = chronological[i + 1]

        if (
            current in matrix
            and nxt in matrix[current]
        ):

            matrix[current][nxt] += 1

    return matrix


# =========================================================
# 波色转移概率
# =========================================================

def wave_transition_probability(
    rows
):

    matrix = wave_transition_matrix(
        rows
    )

    result = {}

    for current in WAVES:

        total = sum(
            matrix[current].values()
        )

        if total <= 0:

            result[current] = {
                wave: 1 / 3
                for wave in WAVES
            }

        else:

            result[current] = {

                wave:
                    matrix[current][wave]
                    / total

                for wave in WAVES
            }

    return result


# =========================================================
# 当前波色
# =========================================================

def current_wave(rows):

    sequence = wave_sequence(rows)

    if not sequence:
        return None

    return sequence[0]


# =========================================================
# 连续波色长度
# =========================================================

def current_wave_streak(rows):

    sequence = wave_sequence(rows)

    if not sequence:
        return {
            "wave": None,
            "length": 0,
        }

    current = sequence[0]

    length = 0

    for wave in sequence:

        if wave == current:
            length += 1
        else:
            break

    return {
        "wave": current,
        "length": length,
    }


# =========================================================
# 波色反转率
# =========================================================

def wave_reversal_rate(rows):

    sequence = wave_sequence(rows)

    if len(sequence) < 2:
        return 0.5

    changes = 0

    total = 0

    for i in range(
        len(sequence) - 1
    ):

        total += 1

        if sequence[i] != sequence[i + 1]:
            changes += 1

    if total <= 0:
        return 0.5

    return changes / total


# =========================================================
# 波色熵
# =========================================================

def wave_entropy(rows):

    counter = Counter(
        wave_sequence(rows)
    )

    total = sum(
        counter.values()
    )

    if total <= 0:
        return 1.0

    entropy = 0.0

    for wave in WAVES:

        count = counter.get(
            wave,
            0
        )

        if count <= 0:
            continue

        p = count / total

        entropy -= p * log(
            p
        )

    # 最大熵 ln(3)
    max_entropy = log(3)

    if max_entropy <= 0:
        return 0.0

    return entropy / max_entropy


# =========================================================
# 波色近期偏离
# =========================================================

def wave_deviation(rows):

    counter = Counter(
        wave_sequence(rows)
    )

    total = sum(
        counter.values()
    )

    if total <= 0:

        return {
            wave: 0.0
            for wave in WAVES
        }

    return {

        wave:
            (
                counter.get(
                    wave,
                    0
                ) / total
            ) - (1 / 3)

        for wave in WAVES
    }


# =========================================================
# 连续号码特征
# =========================================================

def consecutive_features(rows):

    numbers = special_sequence(rows)

    if len(numbers) < 2:

        return {
            "repeat": 0,
            "up": 0,
            "down": 0,
        }

    repeat = 0
    up = 0
    down = 0

    for i in range(
        len(numbers) - 1
    ):

        current = numbers[i]

        previous = numbers[i + 1]

        if current == previous:
            repeat += 1

        elif current > previous:
            up += 1

        else:
            down += 1

    return {
        "repeat": repeat,
        "up": up,
        "down": down,
    }