# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
特征计算模块

数据库：

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

特码：
    numbers 第 7 个号码
"""


from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional
import math


# =========================================================
# 常量
# =========================================================

NUMBERS = list(range(1, 50))

WAVES = [
    "红",
    "蓝",
    "绿",
]


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


# =========================================================
# 基础解析
# =========================================================

def parse_numbers(row) -> List[int]:

    if row is None:
        return []

    # -----------------------------------------------------
    # row 可能已经是 list
    # -----------------------------------------------------

    if isinstance(row, (list, tuple)):

        result = []

        for item in row:

            try:

                n = int(
                    str(item).strip()
                )

                if 1 <= n <= 49:
                    result.append(n)

            except Exception:
                continue

        return result

    # -----------------------------------------------------
    # row 字典
    # -----------------------------------------------------

    try:
        value = row["numbers"]
    except Exception:
        return []

    if value is None:
        return []

    # -----------------------------------------------------
    # list
    # -----------------------------------------------------

    if isinstance(value, (list, tuple)):

        result = []

        for item in value:

            try:

                n = int(
                    str(item).strip()
                )

                if 1 <= n <= 49:
                    result.append(n)

            except Exception:
                continue

        return result

    # -----------------------------------------------------
    # 字符串
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

    result = []

    for item in text.split(","):

        item = item.strip()

        if not item:
            continue

        try:

            n = int(item)

            if 1 <= n <= 49:
                result.append(n)

        except Exception:
            continue

    return result


# =========================================================
# 特码
# =========================================================

def get_special(row) -> int:

    numbers = parse_numbers(row)

    if len(numbers) >= 7:
        return numbers[6]

    return 0


# =========================================================
# 所有号码
# =========================================================

def get_all_numbers(row) -> List[int]:

    return parse_numbers(row)


# =========================================================
# 大小
# =========================================================

def get_size(number: int) -> str:

    try:
        number = int(number)
    except Exception:
        return "未知"

    return "大" if number >= 25 else "小"


# =========================================================
# 单双
# =========================================================

def get_odd_even(number: int) -> str:

    try:
        number = int(number)
    except Exception:
        return "未知"

    return "单" if number % 2 else "双"


# =========================================================
# 波色
# =========================================================

def get_wave(number: int) -> str:

    try:
        number = int(number)
    except Exception:
        return "未知"

    return NUMBER_TO_WAVE.get(
        number,
        "未知"
    )


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
# 特码频率
# =========================================================

def special_frequency(
    rows,
    limit: Optional[int] = None
) -> Dict[int, int]:

    if limit is not None:
        rows = rows[:limit]

    counter = Counter()

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
    limit: int = 120
) -> Dict[int, int]:

    rows = rows[:limit]

    omission = {
        n: len(rows)
        for n in NUMBERS
    }

    for index, row in enumerate(rows):

        n = get_special(row)

        if 1 <= n <= 49:

            # 最新出现的距离
            omission[n] = index

    return omission


# =========================================================
# 特码大小统计
# =========================================================

def special_size_frequency(
    rows
) -> Dict[str, int]:

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[
                get_size(n)
            ] += 1

    return dict(counter)


# =========================================================
# 特码单双统计
# =========================================================

def special_parity_frequency(
    rows
) -> Dict[str, int]:

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[
                get_odd_even(n)
            ] += 1

    return dict(counter)


# =========================================================
# 特码波色统计
# =========================================================

def special_wave_frequency(
    rows
) -> Dict[str, int]:

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            wave = get_wave(n)

            if wave in WAVES:
                counter[wave] += 1

    return dict(counter)


# =========================================================
# 尾数统计
# =========================================================

def special_tail_frequency(
    rows
) -> Dict[int, int]:

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[
                get_tail(n)
            ] += 1

    return dict(counter)


# =========================================================
# MOD7
# =========================================================

def special_mod7_frequency(
    rows
) -> Dict[int, int]:

    counter = Counter()

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            counter[
                get_mod7(n)
            ] += 1

    return dict(counter)


# =========================================================
# 分区
# =========================================================

def special_zone_frequency(
    rows
) -> Dict[int, int]:

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

def get_wave_sequence(
    rows
) -> List[str]:

    result = []

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            wave = get_wave(n)

            if wave in WAVES:
                result.append(wave)

    return result


# =========================================================
# 最新波色
# =========================================================

def latest_wave(
    rows
) -> Optional[str]:

    sequence = get_wave_sequence(rows)

    if not sequence:
        return None

    return sequence[0]


# =========================================================
# 波色连续长度
# =========================================================

def wave_streak(
    rows
) -> Dict[str, int]:

    sequence = get_wave_sequence(rows)

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
# 波色转移矩阵
# =========================================================

def wave_transition_matrix(
    rows
) -> Dict[str, Dict[str, float]]:

    sequence = get_wave_sequence(rows)

    counts = {

        wave: {
            target: 1.0
            for target in WAVES
        }

        for wave in WAVES
    }

    # Laplace smoothing
    for i in range(
        len(sequence) - 1
    ):

        current = sequence[i]

        next_wave = sequence[i + 1]

        if (
            current in WAVES
            and next_wave in WAVES
        ):

            counts[
                current
            ][
                next_wave
            ] += 1.0

    matrix = {}

    for wave in WAVES:

        total = sum(
            counts[wave].values()
        )

        matrix[wave] = {

            target:
                counts[wave][target] / total

            for target in WAVES
        }

    return matrix


# =========================================================
# 波色转移概率
# =========================================================

def wave_transition_probability(
    rows
) -> Dict[str, float]:

    matrix = wave_transition_matrix(
        rows
    )

    current = latest_wave(rows)

    if current not in WAVES:

        return {
            wave: 1 / 3
            for wave in WAVES
        }

    return matrix[current]


# =========================================================
# 波色熵
# =========================================================

def wave_entropy(
    rows,
    limit: int = 36
) -> float:

    sequence = get_wave_sequence(
        rows[:limit]
    )

    if not sequence:
        return 1.0

    counter = Counter(sequence)

    total = len(sequence)

    entropy = 0.0

    for wave in WAVES:

        count = counter.get(
            wave,
            0
        )

        if count <= 0:
            continue

        p = count / total

        entropy -= p * math.log(
            p
        )

    max_entropy = math.log(3)

    if max_entropy <= 0:
        return 1.0

    return entropy / max_entropy


# =========================================================
# 波色偏离程度
# =========================================================

def wave_deviation(
    rows,
    limit: int = 36
) -> Dict[str, float]:

    sequence = get_wave_sequence(
        rows[:limit]
    )

    if not sequence:

        return {
            wave: 0.0
            for wave in WAVES
        }

    counter = Counter(sequence)

    total = len(sequence)

    result = {}

    expected = 1 / 3

    for wave in WAVES:

        actual = (
            counter.get(
                wave,
                0
            ) / total
        )

        result[wave] = (
            actual - expected
        )

    return result


# =========================================================
# 波色综合特征
# =========================================================

def wave_features(
    rows
) -> Dict[str, Any]:

    sequence = get_wave_sequence(rows)

    latest = (
        sequence[0]
        if sequence
        else None
    )

    streak = wave_streak(rows)

    transition = wave_transition_probability(
        rows
    )

    entropy = wave_entropy(
        rows,
        limit=36
    )

    deviation = wave_deviation(
        rows,
        limit=36
    )

    return {

        "latest":
            latest,

        "streak_wave":
            streak["wave"],

        "streak_length":
            streak["length"],

        "transition":
            transition,

        "entropy":
            entropy,

        "deviation":
            deviation,
    }


# =========================================================
# 动态窗口
# =========================================================

def dynamic_windows(
    rows
) -> Dict[str, List]:

    return {

        "short":
            rows[:12],

        "medium":
            rows[:36],

        "long":
            rows[:120],
    }


# =========================================================
# 数据质量
# =========================================================

def data_quality(
    rows
) -> Dict[str, Any]:

    total = len(rows)

    valid = 0

    invalid = 0

    duplicate_special = 0

    previous_issue = None

    issue_order_errors = 0

    for row in rows:

        numbers = get_all_numbers(row)

        if len(numbers) >= 7:

            valid += 1

            special = numbers[6]

            if not (
                1 <= special <= 49
            ):

                invalid += 1

            if (
                len(set(numbers[:6]))
                != len(numbers[:6])
            ):

                duplicate_special += 1

        else:

            invalid += 1

        issue = row.get(
            "issue"
        ) if isinstance(
            row,
            dict
        ) else None

        if issue is not None:

            try:

                current_issue = int(
                    str(issue)
                    .replace(
                        "-",
                        ""
                    )
                )

                if (
                    previous_issue is not None
                    and current_issue
                    > previous_issue
                ):

                    issue_order_errors += 1

                previous_issue = current_issue

            except Exception:
                pass

    valid_ratio = (
        valid / total
        if total > 0
        else 0.0
    )

    return {

        "total":
            total,

        "valid":
            valid,

        "invalid":
            invalid,

        "valid_ratio":
            valid_ratio,

        "duplicate_main_numbers":
            duplicate_special,

        "issue_order_errors":
            issue_order_errors,

        "quality_score":
            valid_ratio,
    }