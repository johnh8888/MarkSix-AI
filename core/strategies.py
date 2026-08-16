# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
策略引擎

功能：

1. 12期近期统计
2. 36期中期统计
3. 120期长期统计
4. 遗漏策略
5. 趋势策略
6. 转移策略
7. 大小策略
8. 单双策略
9. 波色策略
10. 尾数策略
11. 分区策略
12. 动态模块权重
13. 49码综合评分
14. Top10 / Top3
15. 生肖统计
16. 平特生肖
17. 大小概率
18. 单双概率
19. 波色单推 / 双推

注意：
本模块属于历史数据统计模型，不代表可以确定预测随机开奖结果。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple
import math


# =========================================================
# 导入配置
# =========================================================

from core.config import (
    SHORT_WINDOW,
    MEDIUM_WINDOW,
    LONG_WINDOW,
    MIN_MODULE_WEIGHT,
    MAX_MODULE_WEIGHT,
    DEFAULT_MODULE_WEIGHTS,
    WAVES,
    TOP10_NUMBERS,
    TOP3_NUMBERS,
    TOP5_ZODIACS,
    TOP2_PINGTE_ZODIACS,
    PROBABILITY_FLOOR,
    PROBABILITY_CEILING,
    PROBABILITY_TEMPERATURE,
)


# =========================================================
# 波色模型
# =========================================================

from core.wave_model import (
    NUMBER_TO_WAVE,
    number_to_wave,
    wave_probabilities,
    transition_probabilities,
    analyze_wave,
)


# =========================================================
# 基础常量
# =========================================================

NUMBERS = tuple(
    range(1, 50)
)


# =========================================================
# 安全浮点
# =========================================================

def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:

        value = float(value)

        if not math.isfinite(value):

            return default

        return value

    except (
        TypeError,
        ValueError,
    ):

        return default


# =========================================================
# 限制概率
# =========================================================

def clamp_probability(
    value: float,
) -> float:

    value = safe_float(
        value
    )

    return max(
        PROBABILITY_FLOOR,
        min(
            PROBABILITY_CEILING,
            value,
        ),
    )


# =========================================================
# 号码解析
# =========================================================

def extract_numbers(
    draw: Dict[str, Any],
) -> List[int]:

    numbers = draw.get(
        "numbers",
        []
    )

    result = []

    if isinstance(
        numbers,
        (list, tuple)
    ):

        for value in numbers:

            try:

                number = int(value)

            except (
                TypeError,
                ValueError,
            ):

                continue

            if 1 <= number <= 49:

                result.append(
                    number
                )

    return result


# =========================================================
# 获取特码
# =========================================================

def get_special(
    draw: Dict[str, Any],
) -> int | None:

    special = draw.get(
        "special"
    )

    if special is not None:

        try:

            number = int(
                special
            )

            if 1 <= number <= 49:

                return number

        except (
            TypeError,
            ValueError,
        ):

            pass


    numbers = extract_numbers(
        draw
    )


    if len(numbers) >= 7:

        return numbers[-1]


    return None


# =========================================================
# 提取历史特码
# =========================================================

def special_history(
    draws: Sequence[Dict[str, Any]],
    window: int | None = None,
) -> List[int]:

    source = draws

    if window is not None:

        source = draws[
            :window
        ]


    result = []

    for draw in source:

        number = get_special(
            draw
        )

        if number is not None:

            result.append(
                number
            )

    return result


# =========================================================
# 归一化分数
# =========================================================

def normalize_scores(
    scores: Dict[int, float],
) -> Dict[int, float]:

    if not scores:

        return {
            number: 0.0
            for number in NUMBERS
        }


    values = [
        safe_float(
            scores.get(
                number,
                0.0
            )
        )
        for number in NUMBERS
    ]


    minimum = min(
        values
    )

    maximum = max(
        values
    )


    if abs(
        maximum - minimum
    ) < 1e-12:

        return {
            number: 0.5
            for number in NUMBERS
        }


    result = {}


    for number in NUMBERS:

        value = safe_float(
            scores.get(
                number,
                0.0
            )
        )


        result[number] = (
            value - minimum
        ) / (
            maximum - minimum
        )


    return result


# =========================================================
# 近期策略
# =========================================================

def recent_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    history = special_history(
        draws,
        SHORT_WINDOW
    )


    counter = Counter(
        history
    )


    total = max(
        len(history),
        1
    )


    scores = {}


    for number in NUMBERS:

        frequency = (
            counter.get(
                number,
                0
            ) / total
        )


        scores[number] = frequency


    return normalize_scores(
        scores
    )


# =========================================================
# 中期策略
# =========================================================

def medium_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    history = special_history(
        draws,
        MEDIUM_WINDOW
    )


    counter = Counter(
        history
    )


    total = max(
        len(history),
        1
    )


    scores = {}


    for number in NUMBERS:

        scores[number] = (
            counter.get(
                number,
                0
            ) / total
        )


    return normalize_scores(
        scores
    )


# =========================================================
# 长期策略
# =========================================================

def long_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    history = special_history(
        draws,
        LONG_WINDOW
    )


    counter = Counter(
        history
    )


    total = max(
        len(history),
        1
    )


    scores = {}


    for number in NUMBERS:

        scores[number] = (
            counter.get(
                number,
                0
            ) / total
        )


    return normalize_scores(
        scores
    )


# =========================================================
# 遗漏策略
# =========================================================

def omission_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    history = special_history(
        draws,
        LONG_WINDOW
    )


    position = {
        number: None
        for number in NUMBERS
    }


    for index, number in enumerate(
        history
    ):

        if position[number] is None:

            position[number] = index


    scores = {}


    max_omission = max(
        [
            value
            for value in position.values()
            if value is not None
        ]
        or [1]
    )


    for number in NUMBERS:

        value = position[number]


        if value is None:

            omission = (
                max_omission + 1
            )

        else:

            omission = value


        # 平滑遗漏，避免极端值
        scores[number] = math.log1p(
            omission
        )


    return normalize_scores(
        scores
    )


# =========================================================
# 趋势策略
# =========================================================

def trend_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    short = Counter(
        special_history(
            draws,
            SHORT_WINDOW
        )
    )


    medium = Counter(
        special_history(
            draws,
            MEDIUM_WINDOW
        )
    )


    long = Counter(
        special_history(
            draws,
            LONG_WINDOW
        )
    )


    scores = {}


    for number in NUMBERS:

        scores[number] = (

            short.get(
                number,
                0
            ) * 0.50

            + medium.get(
                number,
                0
            ) * 0.30

            + long.get(
                number,
                0
            ) * 0.20

        )


    return normalize_scores(
        scores
    )


# =========================================================
# 转移策略
# =========================================================

def transition_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    history = special_history(
        draws,
        LONG_WINDOW
    )


    scores = {
        number: 0.0
        for number in NUMBERS
    }


    if len(history) < 2:

        return {
            number: 0.5
            for number in NUMBERS
        }


    previous = history[0]


    # -----------------------------------------------------
    # 根据上一期号码的属性建立条件偏好
    # -----------------------------------------------------

    previous_wave = number_to_wave(
        previous
    )


    previous_size = (
        "大"
        if previous >= 25
        else "小"
    )


    previous_parity = (
        "单"
        if previous % 2
        else "双"
    )


    for number in NUMBERS:

        score = 0.0


        # 波色转移
        current_wave = number_to_wave(
            number
        )


        wave_prob = wave_probabilities(
            draws
        )


        score += (
            wave_prob.get(
                current_wave,
                1 / 3
            ) * 0.45
        )


        # 大小切换
        current_size = (
            "大"
            if number >= 25
            else "小"
        )


        if current_size != previous_size:

            score += 0.15


        # 单双切换
        current_parity = (
            "单"
            if number % 2
            else "双"
        )


        if current_parity != previous_parity:

            score += 0.15


        # 避免简单复制上一特码
        if number != previous:

            score += 0.10


        # 尾数变化
        if number % 10 != previous % 10:

            score += 0.15


        scores[number] = score


    return normalize_scores(
        scores
    )


# =========================================================
# 大小策略
# =========================================================

def size_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    history = special_history(
        draws,
        MEDIUM_WINDOW
    )


    big = sum(
        1
        for number in history
        if number >= 25
    )


    small = sum(
        1
        for number in history
        if number < 25
    )


    total = max(
        big + small,
        1
    )


    big_rate = big / total

    small_rate = small / total


    scores = {}


    for number in NUMBERS:

        if number >= 25:

            scores[number] = (
                big_rate
            )

        else:

            scores[number] = (
                small_rate
            )


    return normalize_scores(
        scores
    )


# =========================================================
# 单双策略
# =========================================================

def parity_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    history = special_history(
        draws,
        MEDIUM_WINDOW
    )


    odd = sum(
        1
        for number in history
        if number % 2 == 1
    )


    even = sum(
        1
        for number in history
        if number % 2 == 0
    )


    total = max(
        odd + even,
        1
    )


    odd_rate = odd / total

    even_rate = even / total


    scores = {}


    for number in NUMBERS:

        if number % 2:

            scores[number] = odd_rate

        else:

            scores[number] = even_rate


    return normalize_scores(
        scores
    )


# =========================================================
# 波色策略
# =========================================================

def wave_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    probabilities = wave_probabilities(
        draws
    )


    scores = {}


    for number in NUMBERS:

        wave = number_to_wave(
            number
        )


        scores[number] = probabilities.get(
            wave,
            1 / 3
        )


    return normalize_scores(
        scores
    )


# =========================================================
# 尾数策略
# =========================================================

def tail_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    history = special_history(
        draws,
        MEDIUM_WINDOW
    )


    counter = Counter(
        number % 10
        for number in history
    )


    total = max(
        len(history),
        1
    )


    scores = {}


    for number in NUMBERS:

        tail = number % 10

        scores[number] = (
            counter.get(
                tail,
                0
            ) / total
        )


    return normalize_scores(
        scores
    )


# =========================================================
# 分区策略
# =========================================================

def zone_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    history = special_history(
        draws,
        MEDIUM_WINDOW
    )


    def zone(
        number: int
    ) -> int:

        if number <= 16:

            return 1

        if number <= 32:

            return 2

        return 3


    counter = Counter(
        zone(number)
        for number in history
    )


    total = max(
        len(history),
        1
    )


    scores = {}


    for number in NUMBERS:

        scores[number] = (
            counter.get(
                zone(number),
                0
            ) / total
        )


    return normalize_scores(
        scores
    )


# =========================================================
# 获取所有策略
# =========================================================

def calculate_all_strategies(
    draws: Sequence[Dict[str, Any]],
) -> Dict[str, Dict[int, float]]:

    return {

        "recent":
            recent_strategy(draws),

        "medium":
            medium_strategy(draws),

        "long":
            long_strategy(draws),

        "omission":
            omission_strategy(draws),

        "trend":
            trend_strategy(draws),

        "transition":
            transition_strategy(draws),

        "size":
            size_strategy(draws),

        "parity":
            parity_strategy(draws),

        "wave":
            wave_strategy(draws),

        "tail":
            tail_strategy(draws),

        "zone":
            zone_strategy(draws),

    }


# =========================================================
# 权重归一化
# =========================================================

def normalize_weights(
    weights: Dict[str, float],
) -> Dict[str, float]:

    result = {}


    for name in DEFAULT_MODULE_WEIGHTS:

        value = safe_float(
            weights.get(
                name,
                DEFAULT_MODULE_WEIGHTS[name]
            )
        )


        value = max(
            MIN_MODULE_WEIGHT,
            min(
                MAX_MODULE_WEIGHT,
                value,
            ),
        )


        result[name] = value


    total = sum(
        result.values()
    )


    if total <= 0:

        return dict(
            DEFAULT_MODULE_WEIGHTS
        )


    return {

        name:
            value / total

        for name, value
        in result.items()

    }


# =========================================================
# 动态模块权重
# =========================================================

def calculate_dynamic_weights(
    draws: Sequence[Dict[str, Any]],
) -> Dict[str, float]:

    """
    V3冷启动权重。

    当历史不足以进行稳定Walk-Forward学习时，
    使用配置文件默认权重。

    后续backtest可以把历史表现反馈给这里。
    """

    weights = dict(
        DEFAULT_MODULE_WEIGHTS
    )


    history_count = len(
        draws
    )


    # -----------------------------------------------------
    # 数据越多，近期模块略微提高
    # -----------------------------------------------------

    if history_count >= 300:

        weights["recent"] += 0.02

        weights["medium"] += 0.01

        weights["long"] -= 0.01

        weights["trend"] += 0.01

        weights["omission"] -= 0.01


    elif history_count >= 200:

        weights["recent"] += 0.01

        weights["trend"] += 0.01


    # -----------------------------------------------------
    # 波色模块
    # -----------------------------------------------------

    if history_count >= 120:

        weights["wave"] += 0.01

        weights["transition"] += 0.01


    return normalize_weights(
        weights
    )


# =========================================================
# 综合策略
# =========================================================

def combine_strategies(
    strategies: Dict[str, Dict[int, float]],
    weights: Dict[str, float] | None = None,
) -> Dict[int, float]:

    if weights is None:

        weights = dict(
            DEFAULT_MODULE_WEIGHTS
        )


    weights = normalize_weights(
        weights
    )


    scores = {
        number: 0.0
        for number in NUMBERS
    }


    for module_name, module_scores in strategies.items():

        weight = weights.get(
            module_name,
            0.0
        )


        if weight <= 0:

            continue


        for number in NUMBERS:

            scores[number] += (

                safe_float(
                    module_scores.get(
                        number,
                        0.0
                    )
                )
                * weight

            )


    return normalize_scores(
        scores
    )


# =========================================================
# 综合策略 V2兼容接口
# =========================================================

def combined_strategy(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    strategies = calculate_all_strategies(
        draws
    )


    weights = calculate_dynamic_weights(
        draws
    )


    return combine_strategies(
        strategies,
        weights,
    )


# =========================================================
# 49码排名
# =========================================================

def rank_numbers(
    scores: Dict[int, float],
) -> List[Dict[str, Any]]:

    ranked = sorted(

        NUMBERS,

        key=lambda number: (
            safe_float(
                scores.get(
                    number,
                    0.0
                )
            ),
            -number,
        ),

        reverse=True,
    )


    result = []


    for index, number in enumerate(
        ranked,
        1
    ):

        result.append({

            "rank":
                index,

            "number":
                number,

            "score":
                round(
                    safe_float(
                        scores[number]
                    ),
                    6
                ),

            "wave":
                number_to_wave(
                    number
                ),

        })


    return result


# =========================================================
# Top10
# =========================================================

def get_top10(
    scores: Dict[int, float],
) -> List[Dict[str, Any]]:

    return rank_numbers(
        scores
    )[
        :TOP10_NUMBERS
    ]


# =========================================================
# Top3
# =========================================================

def get_top3(
    scores: Dict[int, float],
) -> List[Dict[str, Any]]:

    return rank_numbers(
        scores
    )[
        :TOP3_NUMBERS
    ]


# =========================================================
# 大小概率
# =========================================================

def calculate_size_probability(
    draws: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:

    history = special_history(
        draws,
        MEDIUM_WINDOW
    )


    big = sum(
        1
        for number in history
        if number >= 25
    )


    small = sum(
        1
        for number in history
        if number < 25
    )


    total = max(
        big + small,
        1
    )


    big_probability = (
        big / total
    )


    small_probability = (
        small / total
    )


    prediction = (
        "大"
        if big_probability >= small_probability
        else "小"
    )


    return {

        "prediction":
            prediction,

        "probability": {

            "大":
                round(
                    big_probability,
                    6
                ),

            "小":
                round(
                    small_probability,
                    6
                ),

        },

        "sample_size":
            len(history),

    }


# =========================================================
# 单双概率
# =========================================================

def calculate_parity_probability(
    draws: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:

    history = special_history(
        draws,
        MEDIUM_WINDOW
    )


    odd = sum(
        1
        for number in history
        if number % 2
    )


    even = sum(
        1
        for number in history
        if number % 2 == 0
    )


    total = max(
        odd + even,
        1
    )


    odd_probability = (
        odd / total
    )


    even_probability = (
        even / total
    )


    prediction = (
        "单"
        if odd_probability >= even_probability
        else "双"
    )


    return {

        "prediction":
            prediction,

        "probability": {

            "单":
                round(
                    odd_probability,
                    6
                ),

            "双":
                round(
                    even_probability,
                    6
                ),

        },

        "sample_size":
            len(history),

    }


# =========================================================
# 生肖名称提取
# =========================================================

def extract_zodiac(
    draw: Dict[str, Any],
) -> str | None:

    zodiac = draw.get(
        "zodiac"
    )


    if isinstance(
        zodiac,
        list
    ):

        if zodiac:

            return str(
                zodiac[-1]
            ).strip()


    if isinstance(
        zodiac,
        str
    ):

        text = zodiac.strip()

        if not text:

            return None


        parts = (
            text
            .replace("，", ",")
            .replace(" ", ",")
            .split(",")
        )


        valid = [
            x.strip()
            for x in parts
            if x.strip()
        ]


        if valid:

            return valid[-1]


    return None


# =========================================================
# 生肖历史统计
# =========================================================

def zodiac_frequency(
    draws: Sequence[Dict[str, Any]],
    window: int = 120,
) -> Dict[str, float]:

    counter = Counter()


    for draw in draws[
        :window
    ]:

        zodiac = extract_zodiac(
            draw
        )


        if zodiac:

            counter[zodiac] += 1


    total = sum(
        counter.values()
    )


    if total <= 0:

        return {}


    return {

        zodiac:
            count / total

        for zodiac, count
        in counter.items()

    }


# =========================================================
# 生肖Top5
# =========================================================

def get_top5_zodiac(
    draws: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    frequency = zodiac_frequency(
        draws,
        LONG_WINDOW
    )


    ranked = sorted(

        frequency.items(),

        key=lambda item: item[1],

        reverse=True,
    )


    return [

        {
            "zodiac":
                zodiac,

            "score":
                round(
                    probability,
                    6
                ),

            "probability":
                round(
                    probability,
                    6
                ),

        }

        for zodiac, probability
        in ranked[
            :TOP5_ZODIACS
        ]

    ]


# =========================================================
# 平特Top2
# =========================================================

def get_pingte_zodiac(
    draws: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    frequency = zodiac_frequency(
        draws,
        MEDIUM_WINDOW
    )


    ranked = sorted(

        frequency.items(),

        key=lambda item: item[1],

        reverse=True,
    )


    return [

        {
            "zodiac":
                zodiac,

            "score":
                round(
                    probability,
                    6
                ),

            "probability":
                round(
                    probability,
                    6
                ),

        }

        for zodiac, probability
        in ranked[
            :TOP2_PINGTE_ZODIACS
        ]

    ]


# =========================================================
# 完整策略分析
# =========================================================

def analyze_strategies(
    draws: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:

    strategies = calculate_all_strategies(
        draws
    )


    weights = calculate_dynamic_weights(
        draws
    )


    combined = combine_strategies(
        strategies,
        weights
    )


    return {

        "strategies":
            strategies,

        "dynamic_weights":
            weights,

        "combined_scores":
            combined,

        "ranked":
            rank_numbers(
                combined
            ),

        "top10":
            get_top10(
                combined
            ),

        "top3":
            get_top3(
                combined
            ),

        "size":
            calculate_size_probability(
                draws
            ),

        "parity":
            calculate_parity_probability(
                draws
            ),

        "wave":
            analyze_wave(
                draws
            ),

        "top5_zodiac":
            get_top5_zodiac(
                draws
            ),

        "top2_pingte_zodiac":
            get_pingte_zodiac(
                draws
            ),

    }


# =========================================================
# 兼容旧代码
# =========================================================

def get_strategy_scores(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    return combined_strategy(
        draws
    )


# =========================================================
# 兼容旧代码
# =========================================================

def calculate_scores(
    draws: Sequence[Dict[str, Any]],
) -> Dict[int, float]:

    return combined_strategy(
        draws
    )


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "六合彩 AI V3.0 strategies.py 测试"
    )

    print("=" * 70)


    test_draws = []


    # -----------------------------------------------------
    # 创建模拟数据
    # -----------------------------------------------------

    for issue in range(
        300,
        0,
        -1
    ):

        numbers = [

            (issue * 3) % 49 + 1,

            (issue * 5) % 49 + 1,

            (issue * 7) % 49 + 1,

            (issue * 11) % 49 + 1,

            (issue * 13) % 49 + 1,

            (issue * 17) % 49 + 1,

            (issue * 19) % 49 + 1,

        ]


        # 去重
        unique = []


        for number in numbers:

            if number not in unique:

                unique.append(
                    number
                )


        while len(unique) < 7:

            for number in NUMBERS:

                if number not in unique:

                    unique.append(
                        number
                    )

                if len(unique) >= 7:

                    break


        test_draws.append({

            "issue":
                str(issue),

            "numbers":
                unique[:7],

            "special":
                unique[6],

        })


    # -----------------------------------------------------
    # 测试
    # -----------------------------------------------------

    result = analyze_strategies(
        test_draws
    )


    print()

    print(
        "历史数据：",
        len(test_draws)
    )


    print()

    print(
        "动态权重："
    )


    for name, weight in result[
        "dynamic_weights"
    ].items():

        print(
            f"{name:<12}"
            f"{weight:.6f}"
        )


    print()

    print(
        "Top10："
    )


    for item in result[
        "top10"
    ]:

        print(
            f"{item['rank']:02d} "
            f"{item['number']:02d} "
            f"{item['wave']} "
            f"{item['score']:.6f}"
        )


    print()

    print(
        "Top3：",
        [
            item["number"]
            for item in result[
                "top3"
            ]
        ]
    )


    print()

    print(
        "大小：",
        result["size"]
    )


    print()

    print(
        "单双：",
        result["parity"]
    )


    print()

    print(
        "波色：",
        result["wave"]
    )


    print()

    print(
        "生肖5肖：",
        result["top5_zodiac"]
    )


    print()

    print(
        "平特2肖：",
        result["top2_pingte_zodiac"]
    )


    print()

    print("=" * 70)

    print(
        "strategies.py 测试完成"
    )

    print("=" * 70)