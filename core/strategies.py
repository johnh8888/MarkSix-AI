# -*- coding: utf-8 -*-

"""
六合彩 V3.0 策略层

统一向 predictor.py 提供：

- 号码频率
- 遗漏
- 趋势
- 大小
- 单双
- 波色
- 尾数
- 分区
- 号码评分

所有模型均基于：
最新 → 最旧
"""

from collections import Counter
from typing import Any, Dict, List

from .wave_model import (
    RED,
    BLUE,
    GREEN,
    WAVES,
    NUMBER_TO_WAVE,
    get_wave,
    wave_probabilities,
    wave_single_pick,
    wave_double_pick,
    analyze_wave,
)


# =========================================================
# 基础号码
# =========================================================

NUMBERS = list(range(1, 50))


# =========================================================
# 解析 numbers
# =========================================================

def parse_numbers(value) -> List[int]:

    if value is None:
        return []

    if isinstance(
        value,
        (list, tuple)
    ):

        result = []

        for x in value:

            try:

                n = int(x)

                if 1 <= n <= 49:
                    result.append(n)

            except Exception:
                continue

        return result

    text = str(value).strip()

    if not text:
        return []

    text = (
        text
        .replace("，", ",")
        .replace("|", ",")
        .replace(" ", ",")
    )

    result = []

    for x in text.split(","):

        try:

            n = int(
                x.strip()
            )

            if 1 <= n <= 49:
                result.append(n)

        except Exception:
            continue

    return result


# =========================================================
# 获取特码
# =========================================================

def get_special(row) -> int:

    try:

        special = row.get(
            "special"
        )

        if special is not None:

            n = int(special)

            if 1 <= n <= 49:
                return n

    except Exception:
        pass

    try:

        numbers = row.get(
            "numbers"
        )

    except Exception:

        return 0

    numbers = parse_numbers(
        numbers
    )

    if len(numbers) >= 7:
        return numbers[6]

    return 0


# =========================================================
# 提取特码
# =========================================================

def special_history(
    rows,
    limit=None
) -> List[int]:

    if limit is not None:
        rows = rows[:limit]

    result = []

    for row in rows:

        n = get_special(row)

        if 1 <= n <= 49:

            result.append(n)

    return result


# =========================================================
# 频率模型
# =========================================================

def frequency_score(
    rows,
    window=120
) -> Dict[int, float]:

    history = special_history(
        rows,
        window
    )

    counter = Counter(
        history
    )

    total = len(history)

    if total <= 0:

        return {
            n: 1.0 / 49.0
            for n in NUMBERS
        }

    # 拉普拉斯平滑
    denominator = (
        total + 49
    )

    return {

        n:
        (
            counter.get(n, 0) + 1
        ) / denominator

        for n in NUMBERS
    }


# =========================================================
# 遗漏模型
# =========================================================

def omission_score(
    rows,
    window=120
) -> Dict[int, float]:

    history = special_history(
        rows,
        window
    )

    result = {}

    for n in NUMBERS:

        try:

            index = history.index(n)

            omission = index

        except ValueError:

            omission = len(history)

        result[n] = omission

    # -----------------------------------------------------
    # 防止遗漏无限放大
    # -----------------------------------------------------

    max_omission = max(
        result.values()
    ) if result else 1

    if max_omission <= 0:
        max_omission = 1

    normalized = {}

    for n in NUMBERS:

        # 适度衰减
        value = (
            result[n] /
            max_omission
        )

        normalized[n] = value

    return normalized


# =========================================================
# 趋势模型
# =========================================================

def trend_score(
    rows
) -> Dict[int, float]:

    short = frequency_score(
        rows,
        12
    )

    medium = frequency_score(
        rows,
        36
    )

    long = frequency_score(
        rows,
        120
    )

    result = {}

    for n in NUMBERS:

        result[n] = (

            short[n] * 0.50

            +

            medium[n] * 0.30

            +

            long[n] * 0.20

        )

    return result


# =========================================================
# 尾数
# =========================================================

def tail_score(
    rows
) -> Dict[int, float]:

    history = special_history(
        rows,
        120
    )

    counter = Counter(
        n % 10
        for n in history
    )

    total = len(history)

    result = {}

    for n in NUMBERS:

        tail = n % 10

        result[n] = (
            (
                counter.get(
                    tail,
                    0
                ) + 1
            )
            /
            (
                total + 10
            )
        )

    return result


# =========================================================
# 分区
# =========================================================

def get_zone(
    number: int
) -> int:

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


def zone_score(
    rows
) -> Dict[int, float]:

    history = special_history(
        rows,
        120
    )

    counter = Counter(
        get_zone(n)
        for n in history
    )

    total = len(history)

    result = {}

    for n in NUMBERS:

        zone = get_zone(n)

        result[n] = (
            counter.get(
                zone,
                0
            ) + 1
        ) / (
            total + 5
        )

    return result


# =========================================================
# 大小
# =========================================================

def size_score(
    rows
) -> Dict[str, float]:

    history = special_history(
        rows,
        36
    )

    counter = Counter(
        "大" if n >= 25 else "小"
        for n in history
    )

    total = len(history)

    return {

        "大":
        (
            counter.get("大", 0) + 1
        ) / (total + 2),

        "小":
        (
            counter.get("小", 0) + 1
        ) / (total + 2),
    }


# =========================================================
# 单双
# =========================================================

def parity_score(
    rows
) -> Dict[str, float]:

    history = special_history(
        rows,
        36
    )

    counter = Counter(
        "单" if n % 2 else "双"
        for n in history
    )

    total = len(history)

    return {

        "单":
        (
            counter.get("单", 0) + 1
        ) / (total + 2),

        "双":
        (
            counter.get("双", 0) + 1
        ) / (total + 2),
    }


# =========================================================
# 波色
# =========================================================

def wave_score(
    rows
) -> Dict[str, float]:

    return wave_probabilities(
        rows
    )


# =========================================================
# 号码波色
# =========================================================

def number_wave_score(
    number: int,
    wave_prob: Dict[str, float]
) -> float:

    wave = NUMBER_TO_WAVE.get(
        number
    )

    if wave is None:
        return 0.0

    return wave_prob.get(
        wave,
        0.0
    )


# =========================================================
# 综合号码评分
# =========================================================

def combined_number_score(
    rows
) -> Dict[int, float]:

    frequency = frequency_score(
        rows,
        120
    )

    trend = trend_score(
        rows
    )

    omission = omission_score(
        rows,
        120
    )

    tail = tail_score(
        rows
    )

    zone = zone_score(
        rows
    )

    wave = wave_score(
        rows
    )

    result = {}

    for n in NUMBERS:

        # -------------------------------------------------
        # 遗漏采用适度权重
        #
        # 注意：
        # 遗漏不是“越久没出越一定出”
        # -------------------------------------------------

        omission_component = (
            1.0 -
            omission[n] * 0.30
        )

        if omission_component < 0:
            omission_component = 0.0

        score = (

            frequency[n] * 0.25

            +

            trend[n] * 0.30

            +

            omission_component * 0.10

            +

            tail[n] * 0.10

            +

            zone[n] * 0.10

            +

            number_wave_score(
                n,
                wave
            ) * 0.15

        )

        result[n] = score

    return result


# =========================================================
# Top10
# =========================================================

def top_numbers(
    rows,
    count=10
) -> List[int]:

    scores = combined_number_score(
        rows
    )

    ordered = sorted(

        NUMBERS,

        key=lambda n:
        scores[n],

        reverse=True
    )

    return ordered[:count]


# =========================================================
# Top3
# =========================================================

def top_numbers_3(
    rows
) -> List[int]:

    return top_numbers(
        rows,
        3
    )


# =========================================================
# 完整策略分析
# =========================================================

def analyze_strategies(
    rows
) -> Dict[str, Any]:

    numbers = combined_number_score(
        rows
    )

    ordered = sorted(
        NUMBERS,
        key=lambda n:
        numbers[n],
        reverse=True
    )

    wave = analyze_wave(
        rows
    )

    return {

        "number_scores":
            numbers,

        "top10":
            ordered[:10],

        "top3":
            ordered[:3],

        "wave":
            wave,

        "wave_single":
            wave_single_pick(rows),

        "wave_double":
            wave_double_pick(rows),

        "size":
            size_score(rows),

        "parity":
            parity_score(rows),

    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    rows = [

        {
            "numbers":
                "38,26,08,06,29,18,23"
        },

        {
            "numbers":
                "33,27,16,28,04,25,14"
        },

        {
            "numbers":
                "01,12,19,24,30,35,46"
        },

        {
            "numbers":
                "05,11,17,22,38,43,49"
        },

    ]

    print(
        "=" * 70
    )

    print(
        "V3.0 Strategies 测试"
    )

    print(
        "=" * 70
    )

    print(
        "Top10：",
        top_numbers(rows)
    )

    print(
        "Top3：",
        top_numbers_3(rows)
    )

    print(
        "波色概率：",
        wave_score(rows)
    )

    print(
        "波色单推：",
        wave_single_pick(rows)
    )

    print(
        "波色双推：",
        wave_double_pick(rows)
    )

    print(
        "大小：",
        size_score(rows)
    )

    print(
        "单双：",
        parity_score(rows)
    )