# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
特征计算模块

数据库结构：

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
    numbers 第7个号码
"""


from collections import Counter
from typing import Dict, List, Any
import math


# =========================================================
# 常量
# =========================================================

NUMBERS = range(1, 50)

WAVES = (
    "红",
    "蓝",
    "绿",
)


# =========================================================
# 波色
# =========================================================

RED = {
    1, 2, 7, 8,
    12, 13,
    18, 19,
    23, 24,
    29, 30,
    34, 35,
    40,
    45, 46,
}


BLUE = {
    3, 4,
    9, 10,
    14, 15,
    20,
    25, 26,
    31,
    36, 37,
    41, 42,
    47, 48,
}


GREEN = {
    5, 6,
    11,
    16, 17,
    21, 22,
    27, 28,
    32, 33,
    38, 39,
    43, 44,
    49,
}


NUMBER_TO_WAVE = {}

for number in RED:
    NUMBER_TO_WAVE[number] = "红"

for number in BLUE:
    NUMBER_TO_WAVE[number] = "蓝"

for number in GREEN:
    NUMBER_TO_WAVE[number] = "绿"


# =========================================================
# 解析号码
# =========================================================

def parse_numbers(row) -> List[int]:

    if row is None:
        return []

    # -----------------------------------------------------
    # row 可能已经是 numbers list
    # -----------------------------------------------------

    if isinstance(row, (list, tuple)):

        result = []

        for item in row:

            try:

                number = int(
                    str(item).strip()
                )

                if 1 <= number <= 49:
                    result.append(number)

            except Exception:
                continue

        return result


    # -----------------------------------------------------
    # row 字典
    # -----------------------------------------------------

    if isinstance(row, dict):

        value = row.get(
            "numbers"
        )

    else:

        try:
            value = row["numbers"]

        except Exception:
            return []


    if value is None:
        return []


    # -----------------------------------------------------
    # numbers 本身是 list
    # -----------------------------------------------------

    if isinstance(value, (list, tuple)):

        return parse_numbers(
            value
        )


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


    parts = text.split(",")

    result = []

    for item in parts:

        item = item.strip()

        if not item:
            continue

        try:

            number = int(item)

            if 1 <= number <= 49:
                result.append(number)

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


    # 兼容 future special 字段

    try:

        value = row.get(
            "special"
        )

        if value is not None:

            number = int(value)

            if 1 <= number <= 49:
                return number

    except Exception:
        pass


    return 0


# =========================================================
# 全部号码
# =========================================================

def get_all_numbers(row):

    return parse_numbers(row)


# =========================================================
# 安全获取特码
# =========================================================

def safe_special(row):

    number = get_special(row)

    if 1 <= number <= 49:
        return number

    return None


# =========================================================
# 频率
# =========================================================

def special_frequency(
    rows,
    limit=None
) -> Dict[int, int]:

    if limit is not None:

        rows = rows[:limit]


    counter = Counter()

    for row in rows:

        number = safe_special(row)

        if number is not None:

            counter[number] += 1


    return dict(counter)


# =========================================================
# 频率概率
# =========================================================

def special_frequency_probability(
    rows,
    limit=None
):

    frequency = special_frequency(
        rows,
        limit
    )


    total = sum(
        frequency.values()
    )


    if total <= 0:

        return {
            n: 1 / 49
            for n in NUMBERS
        }


    return {

        n:
            frequency.get(n, 0)
            / total

        for n in NUMBERS

    }


# =========================================================
# 遗漏
# =========================================================

def special_omission(
    rows,
    limit=120
):

    rows = rows[:limit]


    result = {

        n: len(rows)

        for n in NUMBERS

    }


    for index, row in enumerate(rows):

        number = safe_special(row)

        if number is not None:

            # 最新数据 index = 0
            if result[number] == len(rows):

                result[number] = index


    return result


# =========================================================
# 遗漏概率
# =========================================================

def omission_score(
    rows,
    limit=120
):

    omission = special_omission(
        rows,
        limit
    )


    values = list(
        omission.values()
    )


    if not values:

        return {
            n: 0.5
            for n in NUMBERS
        }


    low = min(values)

    high = max(values)


    if high == low:

        return {
            n: 0.5
            for n in NUMBERS
        }


    # 遗漏不能无限线性增加权重
    #
    # 使用 sqrt 压缩极端遗漏

    result = {}

    for number in NUMBERS:

        value = omission[number]

        normalized = (
            value - low
        ) / (
            high - low
        )


        result[number] = math.sqrt(
            max(normalized, 0)
        )


    return result


# =========================================================
# 大小
# =========================================================

def get_size(number):

    return (
        "大"
        if int(number) >= 25
        else "小"
    )


# =========================================================
# 单双
# =========================================================

def get_odd_even(number):

    return (
        "单"
        if int(number) % 2
        else "双"
    )


# =========================================================
# 波色
# =========================================================

def get_wave(number):

    number = int(number)

    return NUMBER_TO_WAVE.get(
        number,
        "未知"
    )


# =========================================================
# 尾数
# =========================================================

def get_tail(number):

    return int(number) % 10


# =========================================================
# 分区
# =========================================================

def get_zone(number):

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
# 分类统计
# =========================================================

def special_size_frequency(rows):

    counter = Counter()

    for row in rows:

        number = safe_special(row)

        if number is not None:

            counter[
                get_size(number)
            ] += 1

    return dict(counter)


def special_parity_frequency(rows):

    counter = Counter()

    for row in rows:

        number = safe_special(row)

        if number is not None:

            counter[
                get_odd_even(number)
            ] += 1

    return dict(counter)


def special_wave_frequency(rows):

    counter = Counter()

    for row in rows:

        number = safe_special(row)

        if number is not None:

            wave = get_wave(number)

            if wave in WAVES:

                counter[wave] += 1

    return dict(counter)


def special_tail_frequency(rows):

    counter = Counter()

    for row in rows:

        number = safe_special(row)

        if number is not None:

            counter[
                get_tail(number)
            ] += 1

    return dict(counter)


def special_zone_frequency(rows):

    counter = Counter()

    for row in rows:

        number = safe_special(row)

        if number is not None:

            counter[
                get_zone(number)
            ] += 1

    return dict(counter)


# =========================================================
# 波色序列
# =========================================================

def wave_sequence(rows):

    sequence = []

    for row in rows:

        number = safe_special(row)

        if number is None:
            continue

        wave = get_wave(number)

        if wave in WAVES:

            sequence.append(wave)

    return sequence


# =========================================================
# 当前连续波色
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
# 波色转移矩阵
# =========================================================

def wave_transition_matrix(
    rows
):

    sequence = wave_sequence(
        rows
    )


    matrix = {

        source: {

            target: 0

            for target in WAVES

        }

        for source in WAVES

    }


    if len(sequence) < 2:

        return matrix


    for i in range(
        len(sequence) - 1
    ):

        current = sequence[i]

        previous = sequence[i + 1]


        if (
            previous in WAVES
            and current in WAVES
        ):

            matrix[
                previous
            ][
                current
            ] += 1


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


    for source in WAVES:

        total = sum(
            matrix[source].values()
        )


        if total <= 0:

            result[source] = {

                wave:
                    1 / 3

                for wave in WAVES

            }

        else:

            # Laplace smoothing
            denominator = (
                total + 3
            )

            result[source] = {

                wave:
                    (
                        matrix[source][wave]
                        + 1
                    )
                    / denominator

                for wave in WAVES

            }


    return result


# =========================================================
# 熵
# =========================================================

def entropy(
    probabilities
):

    values = [
        p
        for p in probabilities
        if p > 0
    ]


    if not values:
        return 0.0


    result = 0.0

    for p in values:

        result -= (
            p * math.log(
                p,
                2
            )
        )


    return result


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


    probabilities = [

        counter.get(
            wave,
            0
        ) / total

        for wave in WAVES

    ]


    # 归一化到 0~1
    value = entropy(
        probabilities
    )


    return value / math.log(
        3,
        2
    )


# =========================================================
# 波色近期偏离程度
# =========================================================

def wave_deviation(
    rows,
    window=12
):

    data = rows[:window]

    counter = Counter(
        wave_sequence(data)
    )


    total = sum(
        counter.values()
    )


    if total <= 0:

        return {
            wave: 0.0
            for wave in WAVES
        }


    expected = 1 / 3


    return {

        wave:
            (
                counter.get(
                    wave,
                    0
                ) / total
            ) - expected

        for wave in WAVES

    }


# =========================================================
# 数字热度
# =========================================================

def number_hot_score(
    rows,
    window
):

    data = rows[:window]

    frequency = special_frequency(
        data
    )


    total = sum(
        frequency.values()
    )


    if total <= 0:

        return {
            n: 0.0
            for n in NUMBERS
        }


    return {

        n:
            frequency.get(n, 0)
            / total

        for n in NUMBERS

    }


# =========================================================
# 趋势
# =========================================================

def number_trend_score(
    rows,
    short_window=12,
    medium_window=36
):

    short = number_hot_score(
        rows,
        short_window
    )


    medium = number_hot_score(
        rows,
        medium_window
    )


    result = {}


    for number in NUMBERS:

        result[number] = (
            short[number]
            - medium[number]
        )


    return result


# =========================================================
# 数字尾数概率
# =========================================================

def tail_probability(
    rows,
    window=36
):

    data = rows[:window]

    counter = Counter()


    for row in data:

        number = safe_special(row)

        if number is not None:

            counter[
                get_tail(number)
            ] += 1


    total = sum(
        counter.values()
    )


    if total <= 0:

        return {
            tail: 0.1
            for tail in range(10)
        }


    return {

        tail:
            (
                counter.get(
                    tail,
                    0
                ) + 1
            )
            / (
                total + 10
            )

        for tail in range(10)

    }


# =========================================================
# 分区概率
# =========================================================

def zone_probability(
    rows,
    window=36
):

    data = rows[:window]

    counter = Counter()


    for row in data:

        number = safe_special(row)

        if number is not None:

            counter[
                get_zone(number)
            ] += 1


    total = sum(
        counter.values()
    )


    if total <= 0:

        return {
            zone:
                0.2
            for zone in range(1, 6)
        }


    return {

        zone:
            (
                counter.get(
                    zone,
                    0
                ) + 1
            )
            / (
                total + 5
            )

        for zone in range(1, 6)

    }


# =========================================================
# 大小概率
# =========================================================

def size_probability(
    rows,
    window=36
):

    data = rows[:window]

    counter = Counter()


    for row in data:

        number = safe_special(row)

        if number is not None:

            counter[
                get_size(number)
            ] += 1


    total = sum(
        counter.values()
    )


    if total <= 0:

        return {
            "大": 0.5,
            "小": 0.5,
        }


    return {

        "大":
            (
                counter["大"] + 1
            )
            / (
                total + 2
            ),

        "小":
            (
                counter["小"] + 1
            )
            / (
                total + 2
            ),

    }


# =========================================================
# 单双概率
# =========================================================

def parity_probability(
    rows,
    window=36
):

    data = rows[:window]

    counter = Counter()


    for row in data:

        number = safe_special(row)

        if number is not None:

            counter[
                get_odd_even(number)
            ] += 1


    total = sum(
        counter.values()
    )


    if total <= 0:

        return {
            "单": 0.5,
            "双": 0.5,
        }


    return {

        "单":
            (
                counter["单"] + 1
            )
            / (
                total + 2
            ),

        "双":
            (
                counter["双"] + 1
            )
            / (
                total + 2
            ),

    }


# =========================================================
# 特征摘要
# =========================================================

def build_feature_summary(
    rows
):

    return {

        "short_window":
            12,

        "medium_window":
            36,

        "long_window":
            120,

        "size":
            size_probability(
                rows,
                36
            ),

        "parity":
            parity_probability(
                rows,
                36
            ),

        "wave":
            special_wave_frequency(
                rows[:36]
            ),

        "wave_entropy":
            wave_entropy(
                rows[:36]
            ),

        "wave_streak":
            current_wave_streak(
                rows
            ),

        "wave_transition":
            wave_transition_probability(
                rows[:120]
            ),

        "wave_deviation":
            wave_deviation(
                rows,
                12
            ),

        "tail":
            tail_probability(
                rows,
                36
            ),

        "zone":
            zone_probability(
                rows,
                36
            ),

    }