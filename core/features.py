# -*- coding: utf-8 -*-
"""
六合彩 AI V3.5
core/features.py

统一特征计算模块

功能：
1. 波色
2. 大小
3. 单双
4. 尾数
5. 区域
6. 012路
7. 质合
8. 生肖
9. 单期特征
10. 多期统计
11. extract_draw_feature()
"""

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional


# ============================================================
# 基础常量
# ============================================================

RED = {
    1, 2, 7, 8, 12, 13, 18, 19,
    23, 24, 29, 30, 34, 35, 40, 45, 46
}

BLUE = {
    3, 4, 9, 10, 14, 15, 20,
    25, 26, 31, 36, 37, 41, 42, 47, 48
}

GREEN = {
    5, 6, 11, 16, 17, 21, 22,
    27, 28, 32, 33, 38, 39, 43, 44, 49
}


# ============================================================
# 生肖
# ============================================================

ZODIAC_MAP = {
    1: "马",
    2: "羊",
    3: "猴",
    4: "鸡",
    5: "狗",
    6: "猪",
    7: "鼠",
    8: "猪",
    9: "狗",
    10: "鸡",
    11: "猴",
    12: "羊",
    13: "马",
    14: "蛇",
    15: "龙",
    16: "兔",
    17: "虎",
    18: "牛",
    19: "鼠",
    20: "猪",
    21: "狗",
    22: "鸡",
    23: "猴",
    24: "羊",
    25: "马",
    26: "蛇",
    27: "龙",
    28: "兔",
    29: "虎",
    30: "牛",
    31: "鼠",
    32: "猪",
    33: "狗",
    34: "鸡",
    35: "猴",
    36: "羊",
    37: "马",
    38: "蛇",
    39: "龙",
    40: "兔",
    41: "虎",
    42: "牛",
    43: "鼠",
    44: "猪",
    45: "狗",
    46: "鸡",
    47: "猴",
    48: "羊",
    49: "马",
}


# ============================================================
# 安全转换
# ============================================================

def to_int(value: Any) -> Optional[int]:
    """安全转换整数。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_numbers(numbers: Iterable[Any]) -> List[int]:
    """
    将号码统一转换成 1~49 的整数。
    自动过滤非法值。
    """
    result = []

    if numbers is None:
        return result

    for value in numbers:
        number = to_int(value)

        if number is None:
            continue

        if 1 <= number <= 49:
            result.append(number)

    return result


# ============================================================
# 基础属性
# ============================================================

def get_color(number: Any) -> str:
    """获取波色。"""
    number = to_int(number)

    if number is None:
        return "未知"

    if number in RED:
        return "红"

    if number in BLUE:
        return "蓝"

    if number in GREEN:
        return "绿"

    return "未知"


def get_size(number: Any) -> str:
    """
    大小：
    1~24 = 小
    25~49 = 大
    """
    number = to_int(number)

    if number is None:
        return "未知"

    return "大" if number >= 25 else "小"


def get_odd_even(number: Any) -> str:
    """单双。"""
    number = to_int(number)

    if number is None:
        return "未知"

    return "单" if number % 2 else "双"


def get_tail(number: Any) -> int:
    """尾数。"""
    number = to_int(number)

    if number is None:
        return -1

    return number % 10


def get_mod3(number: Any) -> int:
    """3路。"""
    number = to_int(number)

    if number is None:
        return -1

    return number % 3


def get_mod7(number: Any) -> int:
    """7路。"""
    number = to_int(number)

    if number is None:
        return -1

    return number % 7


def get_012(number: Any) -> int:
    """012路。"""
    number = to_int(number)

    if number is None:
        return -1

    return number % 3


def get_prime(number: Any) -> str:
    """质数 / 合数。"""
    number = to_int(number)

    if number is None:
        return "未知"

    if number < 2:
        return "合"

    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return "合"

    return "质"


def get_zone(number: Any) -> int:
    """
    号码区域：

    1~10   = 1
    11~20  = 2
    21~30  = 3
    31~40  = 4
    41~49  = 5
    """
    number = to_int(number)

    if number is None:
        return -1

    if number <= 10:
        return 1

    if number <= 20:
        return 2

    if number <= 30:
        return 3

    if number <= 40:
        return 4

    return 5


def get_zodiac(number: Any) -> Optional[str]:
    """统一生肖映射。"""
    number = to_int(number)

    if number is None:
        return None

    return ZODIAC_MAP.get(number)


# ============================================================
# 单号码特征
# ============================================================

def extract_number_feature(number: Any) -> Dict[str, Any]:
    """
    提取一个号码的完整特征。
    """
    number = to_int(number)

    if number is None or not 1 <= number <= 49:
        return {}

    return {
        "number": number,
        "color": get_color(number),
        "size": get_size(number),
        "odd_even": get_odd_even(number),
        "tail": get_tail(number),
        "mod3": get_mod3(number),
        "mod7": get_mod7(number),
        "mod012": get_012(number),
        "prime": get_prime(number),
        "zone": get_zone(number),
        "zodiac": get_zodiac(number),
    }


# ============================================================
# 单期开奖特征
# ============================================================

def extract_draw_feature(draw: Any) -> Dict[str, Any]:
    """
    提取单期开奖的特征。

    这是 markov.py 当前需要的核心函数。

    支持：

    [
        39, 41, 8, 9, 7, 14, 49
    ]

    也支持：

    {
        "numbers": [...]
    }

    以及：

    {
        "openCode": "39,41,08,09,07,14,49"
    }

    返回：

    {
        "numbers": [...],
        "colors": [...],
        "sizes": [...],
        "odd_even": [...],
        "tails": [...],
        "zones": [...],
        "zodiacs": [...]
    }
    """

    numbers = []

    # --------------------------------------------------------
    # 直接传入号码列表
    # --------------------------------------------------------

    if isinstance(draw, (list, tuple, set)):
        numbers = normalize_numbers(draw)

    # --------------------------------------------------------
    # 字典
    # --------------------------------------------------------

    elif isinstance(draw, dict):

        raw_numbers = (
            draw.get("numbers")
            or draw.get("openCode")
            or draw.get("opencode")
            or draw.get("code")
            or draw.get("number")
        )

        if isinstance(raw_numbers, str):
            raw_numbers = raw_numbers.replace("，", ",")

            numbers = normalize_numbers(
                raw_numbers.split(",")
            )

        elif isinstance(raw_numbers, (list, tuple)):
            numbers = normalize_numbers(raw_numbers)

        elif raw_numbers is not None:
            number = to_int(raw_numbers)

            if number is not None:
                numbers = [number]

    # --------------------------------------------------------
    # 字符串
    # --------------------------------------------------------

    elif isinstance(draw, str):

        text = draw.strip()

        # 例如：
        # "39,41,08,09,07,14,49"
        # "39 41 08 09 07 14 49"

        text = (
            text.replace("，", ",")
            .replace(" ", ",")
            .replace("、", ",")
        )

        numbers = normalize_numbers(
            text.split(",")
        )

    # --------------------------------------------------------
    # 特征
    # --------------------------------------------------------

    colors = [get_color(n) for n in numbers]

    sizes = [get_size(n) for n in numbers]

    odd_even = [
        get_odd_even(n)
        for n in numbers
    ]

    tails = [
        get_tail(n)
        for n in numbers
    ]

    zones = [
        get_zone(n)
        for n in numbers
    ]

    zodiacs = [
        get_zodiac(n)
        for n in numbers
    ]

    return {
        "numbers": numbers,
        "colors": colors,
        "sizes": sizes,
        "odd_even": odd_even,
        "tails": tails,
        "zones": zones,
        "zodiacs": zodiacs,
    }


# ============================================================
# 多期开奖统计
# ============================================================

def feature_frequency(
    draws: Iterable[Any],
    key: str,
) -> Dict[Any, int]:
    """
    统计某个特征出现次数。
    """

    counter = Counter()

    if draws is None:
        return dict(counter)

    for draw in draws:

        feature = extract_draw_feature(draw)

        values = feature.get(key, [])

        for value in values:
            counter[value] += 1

    return dict(counter)


def number_frequency(
    draws: Iterable[Any],
) -> Dict[int, int]:
    """
    统计号码频率。
    """

    counter = Counter()

    if draws is None:
        return dict(counter)

    for draw in draws:

        feature = extract_draw_feature(draw)

        for number in feature["numbers"]:
            counter[number] += 1

    return dict(counter)


def color_frequency(
    draws: Iterable[Any],
) -> Dict[str, int]:
    return feature_frequency(
        draws,
        "colors",
    )


def size_frequency(
    draws: Iterable[Any],
) -> Dict[str, int]:
    return feature_frequency(
        draws,
        "sizes",
    )


def odd_even_frequency(
    draws: Iterable[Any],
) -> Dict[str, int]:
    return feature_frequency(
        draws,
        "odd_even",
    )


def zodiac_frequency(
    draws: Iterable[Any],
) -> Dict[str, int]:
    return feature_frequency(
        draws,
        "zodiacs",
    )


# ============================================================
# 热号 / 冷号
# ============================================================

def get_hot_numbers(
    draws: Iterable[Any],
    top_n: int = 10,
) -> List[int]:
    """
    获取热号。
    """

    freq = number_frequency(draws)

    ranked = sorted(
        freq.items(),
        key=lambda x: (-x[1], x[0])
    )

    return [
        number
        for number, _ in ranked[:top_n]
    ]


def get_cold_numbers(
    draws: Iterable[Any],
    top_n: int = 10,
) -> List[int]:
    """
    获取冷号。
    """

    freq = number_frequency(draws)

    # 确保1~49全部参与排序
    full = {
        number: freq.get(number, 0)
        for number in range(1, 50)
    }

    ranked = sorted(
        full.items(),
        key=lambda x: (x[1], x[0])
    )

    return [
        number
        for number, _ in ranked[:top_n]
    ]


# ============================================================
# 特别生肖
# ============================================================

def get_zodiac_numbers(
    zodiac: str,
) -> List[int]:
    """
    根据生肖反查号码。
    """

    if not zodiac:
        return []

    return [
        number
        for number in range(1, 50)
        if ZODIAC_MAP.get(number) == zodiac
    ]


def get_special_zodiac(
    draws: Iterable[Any],
    top_n: int = 5,
) -> List[str]:
    """
    根据历史频率选择特别生肖。

    默认5个。
    """

    frequency = zodiac_frequency(draws)

    ranked = sorted(
        frequency.items(),
        key=lambda x: (-x[1], x[0])
    )

    result = [
        zodiac
        for zodiac, _ in ranked[:top_n]
    ]

    # 数据不足时补足
    if len(result) < top_n:

        for zodiac in [
            "鼠",
            "牛",
            "虎",
            "兔",
            "龙",
            "蛇",
            "马",
            "羊",
            "猴",
            "鸡",
            "狗",
            "猪",
        ]:

            if zodiac not in result:
                result.append(zodiac)

            if len(result) >= top_n:
                break

    return result[:top_n]


# ============================================================
# 综合特征
# ============================================================

def extract_features(
    draws: Iterable[Any],
) -> Dict[str, Any]:
    """
    提取整个历史数据集的综合特征。
    """

    draw_list = list(draws or [])

    return {
        "history_count": len(draw_list),

        "number_frequency":
            number_frequency(draw_list),

        "color_frequency":
            color_frequency(draw_list),

        "size_frequency":
            size_frequency(draw_list),

        "odd_even_frequency":
            odd_even_frequency(draw_list),

        "zodiac_frequency":
            zodiac_frequency(draw_list),

        "hot_numbers":
            get_hot_numbers(draw_list, 10),

        "cold_numbers":
            get_cold_numbers(draw_list, 10),

        "special_zodiac":
            get_special_zodiac(draw_list, 5),
    }


# ============================================================
# 兼容旧代码的别名
# ============================================================

extract_features_from_draw = extract_draw_feature
get_number_feature = extract_number_feature


# ============================================================
# 自检
# ============================================================

if __name__ == "__main__":

    test = [
        39,
        41,
        8,
        9,
        7,
        14,
        49,
    ]

    print("=" * 60)
    print("features.py 自检")
    print("=" * 60)

    print("号码:", test)

    print("生肖:")
    print([
        get_zodiac(n)
        for n in test
    ])

    print("波色:")
    print([
        get_color(n)
        for n in test
    ])

    print("大小:")
    print([
        get_size(n)
        for n in test
    ])

    print("单双:")
    print([
        get_odd_even(n)
        for n in test
    ])

    print("完整特征:")
    print(extract_draw_feature(test))

    print("=" * 60)
    print("features.py OK")
    print("=" * 60)
