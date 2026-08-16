# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
========================================================

自适应预测策略引擎

V3.0 核心：

1. 动态 12 / 36 / 120 窗口
2. 状态识别
3. 近期频率
4. 中期频率
5. 长期频率
6. 遗漏模型
7. 趋势模型
8. 尾数模型
9. 分区模型
10. 大小模型
11. 单双模型
12. 波色模型
13. 波色转移矩阵
14. 波色连续 / 反转
15. 波色熵
16. 动态模块评分
17. 概率校准
18. 防止虚假 1.0000
19. 为 Walk-Forward 提供统一接口

注意：

本系统属于历史统计与回测模型。

开奖结果具有随机性。

任何历史统计结果都不能保证下一期开奖。
"""


from collections import Counter
from typing import Dict, List, Any, Tuple
import math

from .features import (
    get_special,
    get_wave,
    get_size,
    get_odd_even,
    get_tail,
    get_zone,
)


# =========================================================
# 常量
# =========================================================

NUMBERS = list(range(1, 50))

WAVES = [
    "红",
    "蓝",
    "绿",
]

SIZES = [
    "大",
    "小",
]

PARITIES = [
    "单",
    "双",
]

ZONES = [
    1,
    2,
    3,
    4,
    5,
]


# =========================================================
# V3 动态窗口
# =========================================================

SHORT_WINDOW = 12

MEDIUM_WINDOW = 36

LONG_WINDOW = 120


# =========================================================
# 安全数学函数
# =========================================================

def clamp(
    value: float,
    low: float = 0.0,
    high: float = 1.0,
) -> float:

    try:

        value = float(value)

    except Exception:

        return low

    if math.isnan(value):
        return low

    if math.isinf(value):

        return high if value > 0 else low

    return max(
        low,
        min(high, value)
    )


def safe_div(
    a: float,
    b: float,
    default: float = 0.0,
) -> float:

    try:

        if b == 0:
            return default

        return a / b

    except Exception:

        return default


# =========================================================
# 平滑概率
# =========================================================

def smoothed_probability(
    count: int,
    total: int,
    categories: int = 2,
) -> float:

    """
    Laplace 平滑。

    防止：

        0%
        100%

    直接作为模型概率。

    例如：

        count = 12
        total = 12

    不返回：

        1.0000

    而是返回经过平滑后的概率。
    """

    if total < 0:
        total = 0

    try:

        return (
            count + 1
        ) / (
            total + categories
        )

    except Exception:

        return 1.0 / max(
            categories,
            1
        )


# =========================================================
# 评分归一化
# =========================================================

def normalize_scores(
    scores: Dict[int, float],
    floor: float = 0.02,
) -> Dict[int, float]:

    """
    将任意评分转换到 0~1。

    V3 不再简单：

        min -> 0
        max -> 1

    因为这种方式很容易制造：

        1.0000

    这里采用：

        sigmoid + 平滑

    保留相对排名。
    """

    if not scores:

        return {
            n: 0.5
            for n in NUMBERS
        }

    values = []

    for n in NUMBERS:

        value = scores.get(
            n,
            0.0
        )

        try:
            value = float(value)

        except Exception:
            value = 0.0

        values.append(value)

    mean = (
        sum(values)
        / max(len(values), 1)
    )

    variance = (
        sum(
            (x - mean) ** 2
            for x in values
        )
        / max(len(values), 1)
    )

    std = math.sqrt(
        variance
    )

    if std < 1e-9:

        return {
            n: 0.5
            for n in NUMBERS
        }

    result = {}

    for n in NUMBERS:

        value = scores.get(
            n,
            mean
        )

        z = (
            value - mean
        ) / std

        # 限制 sigmoid 输入
        z = max(
            -8.0,
            min(8.0, z)
        )

        probability = (
            1.0
            /
            (
                1.0
                + math.exp(-z)
            )
        )

        # 概率收缩
        probability = (
            floor
            +
            (
                1.0
                - 2 * floor
            )
            * probability
        )

        result[n] = clamp(
            probability,
            floor,
            1.0 - floor
        )

    return result


# =========================================================
# 获取特码
# =========================================================

def safe_special(
    row: Dict[str, Any]
):

    try:

        n = get_special(row)

        n = int(n)

        if 1 <= n <= 49:
            return n

    except Exception:

        pass

    return None


# =========================================================
# 获取有效特码
# =========================================================

def get_special_numbers(
    rows: List[Dict[str, Any]]
) -> List[int]:

    result = []

    for row in rows:

        n = safe_special(row)

        if n is not None:

            result.append(n)

    return result


# =========================================================
# 数据质量检查
# =========================================================

def data_quality(
    rows: List[Dict[str, Any]]
) -> Dict[str, Any]:

    total = len(rows)

    valid = 0

    invalid = 0

    numbers = []

    issues = []

    for row in rows:

        n = safe_special(row)

        if n is None:

            invalid += 1

            continue

        valid += 1

        numbers.append(n)

        issue = row.get(
            "issue"
        )

        if issue is not None:

            issues.append(
                str(issue)
            )

    unique_issues = len(
        set(issues)
    )

    duplicate_issues = (
        max(
            0,
            len(issues)
            - unique_issues
        )
    )

    return {

        "total":
            total,

        "valid":
            valid,

        "invalid":
            invalid,

        "valid_rate":
            safe_div(
                valid,
                total,
                0.0
            ),

        "unique_issues":
            unique_issues,

        "duplicate_issues":
            duplicate_issues,

        "enough_data":
            valid >= 20,
    }


# =========================================================
# 取窗口
# =========================================================

def get_window(
    rows: List[Dict[str, Any]],
    size: int,
) -> List[Dict[str, Any]]:

    return rows[:size]


# =========================================================
# 频率统计
# =========================================================

def frequency_counts(
    rows: List[Dict[str, Any]]
) -> Counter:

    counter = Counter()

    for row in rows:

        n = safe_special(row)

        if n is not None:

            counter[n] += 1

    return counter


# =========================================================
# 频率策略
# =========================================================

def strategy_frequency(
    rows: List[Dict[str, Any]],
    window: int,
) -> Dict[int, float]:

    data = get_window(
        rows,
        window
    )

    counter = frequency_counts(
        data
    )

    total = sum(
        counter.values()
    )

    scores = {}

    for n in NUMBERS:

        count = counter.get(
            n,
            0
        )

        scores[n] = smoothed_probability(
            count,
            total,
            49
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 近期频率
# =========================================================

def strategy_recent(
    rows
) -> Dict[int, float]:

    return strategy_frequency(
        rows,
        SHORT_WINDOW
    )


# =========================================================
# 中期频率
# =========================================================

def strategy_medium(
    rows
) -> Dict[int, float]:

    return strategy_frequency(
        rows,
        MEDIUM_WINDOW
    )


# =========================================================
# 长期频率
# =========================================================

def strategy_long(
    rows
) -> Dict[int, float]:

    return strategy_frequency(
        rows,
        LONG_WINDOW
    )


# =========================================================
# 遗漏
# =========================================================

def omission_counts(
    rows: List[Dict[str, Any]]
) -> Dict[int, int]:

    data = rows[:LONG_WINDOW]

    omission = {
        n: len(data)
        for n in NUMBERS
    }

    for index, row in enumerate(data):

        n = safe_special(row)

        if n is None:
            continue

        if omission[n] == len(data):

            omission[n] = index

    return omission


# =========================================================
# 遗漏策略
# =========================================================

def strategy_omission(
    rows
) -> Dict[int, float]:

    omission = omission_counts(
        rows
    )

    scores = {}

    for n in NUMBERS:

        miss = omission.get(
            n,
            LONG_WINDOW
        )

        # -------------------------------------------------
        # 遗漏不是越大越好
        #
        # 使用软饱和函数
        # -------------------------------------------------

        score = (
            1.0
            -
            math.exp(
                -miss / 35.0
            )
        )

        scores[n] = score

    return normalize_scores(
        scores
    )


# =========================================================
# 趋势策略
# =========================================================

def strategy_trend(
    rows
) -> Dict[int, float]:

    short = get_window(
        rows,
        SHORT_WINDOW
    )

    medium = get_window(
        rows,
        MEDIUM_WINDOW
    )

    short_counter = frequency_counts(
        short
    )

    medium_counter = frequency_counts(
        medium
    )

    short_total = len(
        get_special_numbers(
            short
        )
    )

    medium_total = len(
        get_special_numbers(
            medium
        )
    )

    scores = {}

    for n in NUMBERS:

        short_rate = safe_div(
            short_counter.get(n, 0),
            short_total,
            0.0
        )

        medium_rate = safe_div(
            medium_counter.get(n, 0),
            medium_total,
            0.0
        )

        trend = (
            short_rate
            -
            medium_rate
        )

        scores[n] = trend

    return normalize_scores(
        scores
    )


# =========================================================
# 大小模型
# =========================================================

def category_probability(
    rows: List[Dict[str, Any]],
    category_func,
    categories: List[Any],
) -> Dict[Any, float]:

    counter = Counter()

    total = 0

    for row in rows:

        n = safe_special(row)

        if n is None:
            continue

        category = category_func(n)

        counter[
            category
        ] += 1

        total += 1

    return {

        category:
            smoothed_probability(
                counter.get(
                    category,
                    0
                ),
                total,
                len(categories)
            )

        for category in categories
    }


# =========================================================
# 大小策略
# =========================================================

def strategy_size(
    rows
) -> Dict[int, float]:

    data = get_window(
        rows,
        MEDIUM_WINDOW
    )

    probabilities = category_probability(
        data,
        get_size,
        SIZES
    )

    scores = {}

    for n in NUMBERS:

        category = get_size(n)

        scores[n] = probabilities.get(
            category,
            0.5
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 单双策略
# =========================================================

def strategy_parity(
    rows
) -> Dict[int, float]:

    data = get_window(
        rows,
        MEDIUM_WINDOW
    )

    probabilities = category_probability(
        data,
        get_odd_even,
        PARITIES
    )

    scores = {}

    for n in NUMBERS:

        category = get_odd_even(n)

        scores[n] = probabilities.get(
            category,
            0.5
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 尾数模型
# =========================================================

def strategy_tail(
    rows
) -> Dict[int, float]:

    data = get_window(
        rows,
        MEDIUM_WINDOW
    )

    counter = Counter()

    total = 0

    for row in data:

        n = safe_special(row)

        if n is None:
            continue

        counter[
            get_tail(n)
        ] += 1

        total += 1

    tail_probability = {

        tail:
            smoothed_probability(
                counter.get(
                    tail,
                    0
                ),
                total,
                10
            )

        for tail in range(10)
    }

    scores = {}

    for n in NUMBERS:

        scores[n] = tail_probability.get(
            get_tail(n),
            0.1
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 分区模型
# =========================================================

def strategy_zone(
    rows
) -> Dict[int, float]:

    data = get_window(
        rows,
        MEDIUM_WINDOW
    )

    counter = Counter()

    total = 0

    for row in data:

        n = safe_special(row)

        if n is None:
            continue

        zone = get_zone(n)

        counter[
            zone
        ] += 1

        total += 1

    probabilities = {

        zone:
            smoothed_probability(
                counter.get(
                    zone,
                    0
                ),
                total,
                5
            )

        for zone in ZONES
    }

    scores = {}

    for n in NUMBERS:

        scores[n] = probabilities.get(
            get_zone(n),
            0.2
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 连续数字 / 反转
# =========================================================

def strategy_reversal(
    rows
) -> Dict[int, float]:

    numbers = get_special_numbers(
        rows
    )

    if len(numbers) < 3:

        return {
            n: 0.5
            for n in NUMBERS
        }

    transition = Counter()

    previous = Counter()

    for i in range(
        len(numbers) - 1
    ):

        current = numbers[i]

        next_number = numbers[i + 1]

        previous[
            current
        ] += 1

        transition[
            (
                current,
                next_number
            )
        ] += 1

    latest = numbers[0]

    scores = {}

    for n in NUMBERS:

        count = transition.get(
            (
                latest,
                n
            ),
            0
        )

        total = previous.get(
            latest,
            0
        )

        scores[n] = smoothed_probability(
            count,
            total,
            49
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 波色序列
# =========================================================

def get_wave_sequence(
    rows: List[Dict[str, Any]]
) -> List[str]:

    result = []

    for row in rows:

        n = safe_special(row)

        if n is None:
            continue

        wave = get_wave(n)

        if wave in WAVES:

            result.append(
                wave
            )

    return result


# =========================================================
# 波色频率
# =========================================================

def wave_frequency(
    rows
) -> Dict[str, float]:

    sequence = get_wave_sequence(
        rows
    )

    counter = Counter(
        sequence
    )

    total = len(
        sequence
    )

    return {

        wave:
            smoothed_probability(
                counter.get(
                    wave,
                    0
                ),
                total,
                3
            )

        for wave in WAVES
    }


# =========================================================
# 波色转移矩阵
# =========================================================

def wave_transition_matrix(
    rows
) -> Dict[str, Dict[str, float]]:

    sequence = get_wave_sequence(
        rows
    )

    matrix = {}

    for source in WAVES:

        counter = Counter()

        total = 0

        for i in range(
            len(sequence) - 1
        ):

            current = sequence[i]

            next_wave = sequence[
                i + 1
            ]

            if current != source:
                continue

            counter[
                next_wave
            ] += 1

            total += 1

        matrix[source] = {

            target:
                smoothed_probability(
                    counter.get(
                        target,
                        0
                    ),
                    total,
                    3
                )

            for target in WAVES
        }

    return matrix


# =========================================================
# 波色连续长度
# =========================================================

def wave_streak(
    sequence: List[str]
) -> Tuple[str, int]:

    if not sequence:

        return (
            "未知",
            0
        )

    current = sequence[0]

    streak = 1

    for wave in sequence[1:]:

        if wave == current:

            streak += 1

        else:

            break

    return (
        current,
        streak
    )


# =========================================================
# 波色熵
# =========================================================

def wave_entropy(
    rows
) -> float:

    sequence = get_wave_sequence(
        rows
    )

    if not sequence:

        return 1.0

    counter = Counter(
        sequence
    )

    total = len(
        sequence
    )

    entropy = 0.0

    for wave in WAVES:

        p = safe_div(
            counter.get(
                wave,
                0
            ),
            total,
            0.0
        )

        if p > 0:

            entropy -= (
                p
                * math.log(
                    p
                )
            )

    max_entropy = math.log(
        len(WAVES)
    )

    if max_entropy <= 0:

        return 1.0

    return clamp(
        entropy
        /
        max_entropy
    )


# =========================================================
# 波色模型
# =========================================================

def wave_model(
    rows
) -> Dict[str, Any]:

    short = get_window(
        rows,
        SHORT_WINDOW
    )

    medium = get_window(
        rows,
        MEDIUM_WINDOW
    )

    short_prob = wave_frequency(
        short
    )

    medium_prob = wave_frequency(
        medium
    )

    matrix = wave_transition_matrix(
        rows
    )

    sequence = get_wave_sequence(
        rows
    )

    latest_wave = (
        sequence[0]
        if sequence
        else None
    )

    transition_prob = {

        wave:
            (
                matrix
                .get(
                    latest_wave,
                    {}
                )
                .get(
                    wave,
                    1 / 3
                )
            )

        for wave in WAVES
    }

    # -----------------------------------------------------
    # 近期 + 中期 + 转移
    # -----------------------------------------------------

    combined = {}

    for wave in WAVES:

        combined[wave] = (

            short_prob.get(
                wave,
                1 / 3
            )
            * 0.40

            +

            medium_prob.get(
                wave,
                1 / 3
            )
            * 0.25

            +

            transition_prob.get(
                wave,
                1 / 3
            )
            * 0.35
        )

    # -----------------------------------------------------
    # 连续波色惩罚
    # -----------------------------------------------------

    current_wave, streak = wave_streak(
        sequence
    )

    if (
        current_wave in WAVES
        and streak >= 3
    ):

        combined[current_wave] *= 0.88

    elif (
        current_wave in WAVES
        and streak == 2
    ):

        combined[current_wave] *= 0.95

    # -----------------------------------------------------
    # 归一化
    # -----------------------------------------------------

    total = sum(
        combined.values()
    )

    if total <= 0:

        probabilities = {
            wave: 1 / 3
            for wave in WAVES
        }

    else:

        probabilities = {

            wave:
                combined[wave]
                /
                total

            for wave in WAVES
        }

    ranked = sorted(
        probabilities.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return {

        "probabilities":
            probabilities,

        "ranking":
            ranked,

        "single":
            ranked[0][0],

        "double":
            [
                ranked[0][0],
                ranked[1][0],
            ],

        "latest":
            latest_wave,

        "streak_wave":
            current_wave,

        "streak":
            streak,

        "entropy":
            wave_entropy(rows),

        "transition":
            matrix,
    }


# =========================================================
# 波色号码评分
# =========================================================

def strategy_wave(
    rows
) -> Dict[int, float]:

    model = wave_model(
        rows
    )

    probabilities = model[
        "probabilities"
    ]

    scores = {}

    for n in NUMBERS:

        wave = get_wave(n)

        scores[n] = probabilities.get(
            wave,
            1 / 3
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 状态识别
# =========================================================

def detect_state(
    rows
) -> Dict[str, Any]:

    short_numbers = get_special_numbers(
        rows[:SHORT_WINDOW]
    )

    medium_numbers = get_special_numbers(
        rows[:MEDIUM_WINDOW]
    )

    long_numbers = get_special_numbers(
        rows[:LONG_WINDOW]
    )

    if len(short_numbers) < 5:

        return {

            "state":
                "unknown",

            "confidence":
                0.0,

            "size":
                "unknown",

            "parity":
                "unknown",

            "wave":
                "unknown",

            "trend":
                "neutral",

            "entropy":
                1.0,
        }

    # -----------------------------------------------------
    # 大小偏离
    # -----------------------------------------------------

    def size_rate(numbers):

        if not numbers:
            return 0.5

        return sum(
            n >= 25
            for n in numbers
        ) / len(numbers)

    short_size = size_rate(
        short_numbers
    )

    medium_size = size_rate(
        medium_numbers
    )

    size_deviation = abs(
        short_size
        -
        0.5
    )

    # -----------------------------------------------------
    # 单双偏离
    # -----------------------------------------------------

    def odd_rate(numbers):

        if not numbers:
            return 0.5

        return sum(
            n % 2 == 1
            for n in numbers
        ) / len(numbers)

    short_odd = odd_rate(
        short_numbers
    )

    parity_deviation = abs(
        short_odd
        -
        0.5
    )

    # -----------------------------------------------------
    # 趋势
    # -----------------------------------------------------

    if len(short_numbers) >= 6:

        half = len(
            short_numbers
        ) // 2

        latest = short_numbers[
            :half
        ]

        older = short_numbers[
            half:
        ]

        latest_avg = (
            sum(latest)
            /
            len(latest)
        )

        older_avg = (
            sum(older)
            /
            len(older)
        )

        diff = (
            latest_avg
            -
            older_avg
        )

    else:

        diff = 0.0

    if diff >= 3:

        trend = "up"

    elif diff <= -3:

        trend = "down"

    else:

        trend = "neutral"

    # -----------------------------------------------------
    # 波色熵
    # -----------------------------------------------------

    entropy = wave_entropy(
        rows[:SHORT_WINDOW]
    )

    # -----------------------------------------------------
    # 波色偏离
    # -----------------------------------------------------

    wave_probs = wave_frequency(
        rows[:SHORT_WINDOW]
    )

    wave_deviation = max(
        abs(
            wave_probs.get(
                wave,
                1 / 3
            )
            -
            1 / 3
        )
        for wave in WAVES
    )

    # -----------------------------------------------------
    # 综合状态分数
    # -----------------------------------------------------

    trend_strength = min(
        1.0,
        abs(diff) / 8.0
    )

    deviation_strength = min(
        1.0,
        (
            size_deviation
            +
            parity_deviation
            +
            wave_deviation
        )
        / 0.7
    )

    # -----------------------------------------------------
    # 状态判断
    # -----------------------------------------------------

    if (
        trend_strength >= 0.60
        or deviation_strength >= 0.65
    ):

        state = "trend"

        confidence = (
            0.55
            +
            0.35
            *
            max(
                trend_strength,
                deviation_strength
            )
        )

    elif entropy <= 0.78:

        state = "structured"

        confidence = (
            0.55
            +
            0.30
            *
            (
                1.0
                -
                entropy
            )
        )

    else:

        state = "chaos"

        confidence = (
            0.50
            +
            0.25
            *
            entropy
        )

    # -----------------------------------------------------
    # 大小状态
    # -----------------------------------------------------

    if short_size >= 0.65:

        size_state = "big_hot"

    elif short_size <= 0.35:

        size_state = "small_hot"

    else:

        size_state = "balanced"

    # -----------------------------------------------------
    # 单双状态
    # -----------------------------------------------------

    if short_odd >= 0.65:

        parity_state = "odd_hot"

    elif short_odd <= 0.35:

        parity_state = "even_hot"

    else:

        parity_state = "balanced"

    # -----------------------------------------------------
    # 波色状态
    # -----------------------------------------------------

    highest_wave = max(
        wave_probs,
        key=wave_probs.get
    )

    if wave_probs[
        highest_wave
    ] >= 0.50:

        wave_state = (
            highest_wave
            +
            "_hot"
        )

    else:

        wave_state = "balanced"

    return {

        "state":
            state,

        "confidence":
            clamp(
                confidence
            ),

        "size":
            size_state,

        "parity":
            parity_state,

        "wave":
            wave_state,

        "trend":
            trend,

        "entropy":
            entropy,

        "size_rate":
            short_size,

        "odd_rate":
            short_odd,

        "trend_strength":
            trend_strength,

        "wave_deviation":
            wave_deviation,
    }


# =========================================================
# 动态窗口权重
# =========================================================

def calculate_window_weights(
    rows
) -> Dict[str, float]:

    state = detect_state(
        rows
    )

    mode = state.get(
        "state"
    )

    if mode == "trend":

        weights = {

            "short":
                0.50,

            "medium":
                0.30,

            "long":
                0.20,
        }

    elif mode == "chaos":

        weights = {

            "short":
                0.20,

            "medium":
                0.35,

            "long":
                0.45,
        }

    else:

        weights = {

            "short":
                0.35,

            "medium":
                0.35,

            "long":
                0.30,
        }

    return weights


# =========================================================
# 动态窗口综合号码模型
# =========================================================

def dynamic_frequency_model(
    rows
) -> Dict[int, float]:

    weights = calculate_window_weights(
        rows
    )

    short_scores = strategy_recent(
        rows
    )

    medium_scores = strategy_medium(
        rows
    )

    long_scores = strategy_long(
        rows
    )

    scores = {}

    for n in NUMBERS:

        scores[n] = (

            short_scores[n]
            * weights["short"]

            +

            medium_scores[n]
            * weights["medium"]

            +

            long_scores[n]
            * weights["long"]
        )

    return normalize_scores(
        scores
    )


# =========================================================
# 综合策略
# =========================================================

def generate_strategy_scores(
    rows
) -> Dict[str, Dict[int, float]]:

    """
    返回所有独立模块。

    prediction.py / backtest.py
    可以直接调用。
    """

    return {

        "frequency":
            dynamic_frequency_model(
                rows
            ),

        "recent":
            strategy_recent(
                rows
            ),

        "medium":
            strategy_medium(
                rows
            ),

        "long":
            strategy_long(
                rows
            ),

        "omission":
            strategy_omission(
                rows
            ),

        "trend":
            strategy_trend(
                rows
            ),

        "reversal":
            strategy_reversal(
                rows
            ),

        "size":
            strategy_size(
                rows
            ),

        "parity":
            strategy_parity(
                rows
            ),

        "tail":
            strategy_tail(
                rows
            ),

        "zone":
            strategy_zone(
                rows
            ),

        "wave":
            strategy_wave(
                rows
            ),
    }


# =========================================================
# 默认模块权重
# =========================================================

DEFAULT_MODULE_WEIGHTS = {

    "frequency":
        0.16,

    "recent":
        0.10,

    "medium":
        0.08,

    "long":
        0.06,

    "omission":
        0.06,

    "trend":
        0.14,

    "reversal":
        0.10,

    "size":
        0.08,

    "parity":
        0.08,

    "tail":
        0.05,

    "zone":
        0.04,

    "wave":
        0.05,
}


# =========================================================
# 权重归一化
# =========================================================

def normalize_weights(
    weights: Dict[str, float]
) -> Dict[str, float]:

    clean = {}

    for name, value in weights.items():

        try:

            value = float(value)

        except Exception:

            value = 0.0

        clean[name] = max(
            0.001,
            value
        )

    total = sum(
        clean.values()
    )

    if total <= 0:

        return dict(
            DEFAULT_MODULE_WEIGHTS
        )

    return {

        name:
            value / total

        for name, value
        in clean.items()
    }


# =========================================================
# 状态动态调整模块权重
# =========================================================

def state_adjust_weights(
    rows,
    weights=None,
) -> Dict[str, float]:

    if weights is None:

        weights = dict(
            DEFAULT_MODULE_WEIGHTS
        )

    else:

        weights = dict(
            weights
        )

    state = detect_state(
        rows
    )

    mode = state.get(
        "state"
    )

    # -----------------------------------------------------
    # 趋势
    # -----------------------------------------------------

    if mode == "trend":

        weights[
            "trend"
        ] *= 1.30

        weights[
            "recent"
        ] *= 1.20

        weights[
            "reversal"
        ] *= 1.15

        weights[
            "long"
        ] *= 0.80

    # -----------------------------------------------------
    # 混沌
    # -----------------------------------------------------

    elif mode == "chaos":

        weights[
            "long"
        ] *= 1.30

        weights[
            "medium"
        ] *= 1.20

        weights[
            "trend"
        ] *= 0.75

        weights[
            "recent"
        ] *= 0.75

        weights[
            "reversal"
        ] *= 0.80

    # -----------------------------------------------------
    # 结构状态
    # -----------------------------------------------------

    elif mode == "structured":

        weights[
            "wave"
        ] *= 1.20

        weights[
            "size"
        ] *= 1.15

        weights[
            "parity"
        ] *= 1.10

    return normalize_weights(
        weights
    )


# =========================================================
# 模块表现 -> 权重
# =========================================================

def performance_to_weights(
    module_performance: Dict[str, float]
) -> Dict[str, float]:

    """
    将 Walk-Forward 模块表现转换成权重。

    performance：

        0.50 = 随机附近
        0.60 = 较好
        0.70 = 很好

    使用平滑映射，避免某个模块
    因为少量样本直接获得极端权重。
    """

    if not module_performance:

        return dict(
            DEFAULT_MODULE_WEIGHTS
        )

    weights = {}

    for module in DEFAULT_MODULE_WEIGHTS:

        performance = module_performance.get(
            module,
            0.50
        )

        try:

            performance = float(
                performance
            )

        except Exception:

            performance = 0.50

        # -------------------------------------------------
        # 以 0.50 为基准
        # -------------------------------------------------

        edge = (
            performance
            -
            0.50
        )

        # -------------------------------------------------
        # 平滑
        # -------------------------------------------------

        factor = (
            1.0
            +
            2.5
            * edge
        )

        factor = max(
            0.45,
            min(
                1.80,
                factor
            )
        )

        weights[module] = (
            DEFAULT_MODULE_WEIGHTS[
                module
            ]
            *
            factor
        )

    return normalize_weights(
        weights
    )


# =========================================================
# 最终综合评分
# =========================================================

def combine_strategies(
    rows,
    module_performance=None,
) -> Tuple[
    Dict[int, float],
    Dict[str, Dict[int, float]],
    Dict[str, float],
]:

    if not rows:

        empty = {
            n: 0.5
            for n in NUMBERS
        }

        return (
            empty,
            {},
            {},
        )

    strategies = generate_strategy_scores(
        rows
    )

    # -----------------------------------------------------
    # Walk-Forward表现 -> 基础权重
    # -----------------------------------------------------

    weights = performance_to_weights(
        module_performance
        or {}
    )

    # -----------------------------------------------------
    # 当前状态 -> 动态调整
    # -----------------------------------------------------

    weights = state_adjust_weights(
        rows,
        weights
    )

    # -----------------------------------------------------
    # 综合
    # -----------------------------------------------------

    final_scores = {

        n: 0.0

        for n in NUMBERS
    }

    total_weight = sum(
        weights.values()
    )

    if total_weight <= 0:

        total_weight = 1.0

    for module, scores in strategies.items():

        weight = weights.get(
            module,
            0.0
        )

        for n in NUMBERS:

            final_scores[n] += (

                scores.get(
                    n,
                    0.5
                )

                *

                weight
            )

    # -----------------------------------------------------
    # 归一化
    # -----------------------------------------------------

    final_scores = normalize_scores(
        final_scores
    )

    # -----------------------------------------------------
    # 概率校准
    # -----------------------------------------------------

    final_scores = calibrate_number_scores(
        final_scores
    )

    return (
        final_scores,
        strategies,
        weights,
    )


# =========================================================
# 号码概率校准
# =========================================================

def calibrate_number_scores(
    scores: Dict[int, float]
) -> Dict[int, float]:

    """
    号码排名分数 -> 校准分数。

    注意：

    这里不是声称这是严格统计意义上的
    贝叶斯真实概率。

    它是模型内部置信度。

    防止最高号码永远变成 1.0000。
    """

    if not scores:

        return {
            n: 0.5
            for n in NUMBERS
        }

    values = list(
        scores.values()
    )

    mean = sum(
        values
    ) / len(values)

    calibrated = {}

    for n in NUMBERS:

        value = scores.get(
            n,
            mean
        )

        # -------------------------------------------------
        # 向中心收缩
        # -------------------------------------------------

        value = (
            0.50
            +
            (
                value
                -
                0.50
            )
            * 0.72
        )

        calibrated[n] = clamp(
            value,
            0.08,
            0.92
        )

    return calibrated


# =========================================================
# Top N
# =========================================================

def rank_numbers(
    scores: Dict[int, float],
    top_n: int = 10,
) -> List[Tuple[int, float]]:

    return sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]


# =========================================================
# 模型摘要
# =========================================================

def model_summary(
    rows,
    module_performance=None,
) -> Dict[str, Any]:

    scores, strategies, weights = (
        combine_strategies(
            rows,
            module_performance
        )
    )

    state = detect_state(
        rows
    )

    window_weights = (
        calculate_window_weights(
            rows
        )
    )

    wave = wave_model(
        rows
    )

    return {

        "state":
            state,

        "window_weights":
            window_weights,

        "module_weights":
            weights,

        "wave":
            wave,

        "top10":
            rank_numbers(
                scores,
                10
            ),

        "top3":
            rank_numbers(
                scores,
                3
            ),

        "scores":
            scores,

        "quality":
            data_quality(
                rows
            ),
    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    test_rows = [

        {
            "issue":
                str(1000 - i),

            "numbers":
                "38,26,08,06,29,18,23"
                if i % 7 == 0

                else

                "33,27,16,28,04,25,14"

                if i % 5 == 0

                else

                "47,14,44,32,07,37,11"

        }

        for i in range(150)
    ]

    print("=" * 70)

    print(
        "六合彩 AI V3.0 strategies.py"
    )

    print("=" * 70)

    print()

    quality = data_quality(
        test_rows
    )

    print(
        "数据质量：",
        quality
    )

    print()

    state = detect_state(
        test_rows
    )

    print(
        "状态：",
        state
    )

    print()

    window_weights = (
        calculate_window_weights(
            test_rows
        )
    )

    print(
        "动态窗口：",
        window_weights
    )

    print()

    wave = wave_model(
        test_rows
    )

    print(
        "波色单推：",
        wave["single"]
    )

    print(
        "波色双推：",
        wave["double"]
    )

    print(
        "波色概率："
    )

    for name, probability in sorted(
        wave["probabilities"].items(),
        key=lambda x: x[1],
        reverse=True
    ):

        print(
            f"  {name}："
            f"{probability:.4f}"
        )

    print()

    scores, strategies, weights = (
        combine_strategies(
            test_rows
        )
    )

    print(
        "动态模块权重："
    )

    for name, weight in weights.items():

        print(
            f"  {name:<12}"
            f"{weight:.4f}"
        )

    print()

    print(
        "Top10："
    )

    for index, (
        number,
        score
    ) in enumerate(
        rank_numbers(
            scores,
            10
        ),
        1
    ):

        print(
            f"{index:02d}. "
            f"{number:02d} "
            f"{score:.4f}"
        )

    print()

    print(
        "Top3："
    )

    for number, score in rank_numbers(
        scores,
        3
    ):

        print(
            f"{number:02d} "
            f"{score:.4f}"
        )

    print()

    print("=" * 70)
    print("V3.0 strategies.py 测试结束")
    print("=" * 70)