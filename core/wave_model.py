# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
波色模型

功能：

1. 49码 -> 红/蓝/绿
2. 波色历史统计
3. 12 / 36 / 120窗口
4. 波色转移概率
5. 波色平滑概率
6. 防止出现 0 / 1 的虚假概率
7. 提供 strategies.py 所需要的统一接口

注意：
本模块只做历史统计与概率分析，
不代表开奖结果具有可预测性。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple


# =========================================================
# 波色定义
# =========================================================

WAVES = (
    "红",
    "蓝",
    "绿",
)


# =========================================================
# 香港六合彩常用49码波色
# =========================================================

RED_NUMBERS = {
    1, 2, 7, 8, 12, 13, 18, 19,
    23, 24, 29, 30, 34, 35, 40, 45,
    46,
}


BLUE_NUMBERS = {
    3, 4, 9, 10, 14, 15, 20, 25,
    26, 31, 36, 37, 41, 42, 47, 48,
}


GREEN_NUMBERS = {
    5, 6, 11, 16, 17, 21, 22, 27,
    28, 32, 33, 38, 39, 43, 44, 49,
}


NUMBER_TO_WAVE = {}


for number in RED_NUMBERS:

    NUMBER_TO_WAVE[number] = "红"


for number in BLUE_NUMBERS:

    NUMBER_TO_WAVE[number] = "蓝"


for number in GREEN_NUMBERS:

    NUMBER_TO_WAVE[number] = "绿"


# =========================================================
# 安全概率
# =========================================================

def clamp_probability(
    value: float,
    floor: float = 0.01,
    ceiling: float = 0.99,
) -> float:

    try:

        value = float(value)

    except (
        TypeError,
        ValueError,
    ):

        value = 0.0

    if value < floor:
        value = floor

    if value > ceiling:
        value = ceiling

    return value


# =========================================================
# 号码 -> 波色
# =========================================================

def number_to_wave(
    number: Any,
) -> str:

    try:

        number = int(number)

    except (
        TypeError,
        ValueError,
    ):

        return "未知"

    return NUMBER_TO_WAVE.get(
        number,
        "未知",
    )


# =========================================================
# 多个号码 -> 波色
# =========================================================

def numbers_to_waves(
    numbers: Sequence[Any],
) -> List[str]:

    result = []

    for number in numbers:

        wave = number_to_wave(
            number
        )

        if wave in WAVES:

            result.append(
                wave
            )

    return result


# =========================================================
# 提取特码
# =========================================================

def _extract_special(
    draw: Dict[str, Any],
):

    special = draw.get(
        "special"
    )

    if special is not None:

        try:

            number = int(special)

            if 1 <= number <= 49:

                return number

        except (
            TypeError,
            ValueError,
        ):

            pass

    numbers = draw.get(
        "numbers",
        []
    )

    if isinstance(
        numbers,
        (list, tuple)
    ):

        if len(numbers) >= 7:

            try:

                number = int(
                    numbers[-1]
                )

                if 1 <= number <= 49:

                    return number

            except (
                TypeError,
                ValueError,
            ):

                pass

    return None


# =========================================================
# 提取历史特码波色
# =========================================================

def extract_wave_history(
    draws: Sequence[Dict[str, Any]],
) -> List[str]:

    result = []

    for draw in draws:

        # -------------------------------------------------
        # 优先使用数据库已有wave
        # -------------------------------------------------

        wave = draw.get(
            "wave"
        )

        if isinstance(
            wave,
            str
        ):

            wave = wave.strip()

            if wave in WAVES:

                result.append(
                    wave
                )

                continue

            # 兼容：
            # 红,蓝,绿
            # 红 蓝 绿

            parts = (
                wave
                .replace("，", ",")
                .replace(" ", ",")
                .split(",")
            )

            valid = [
                x.strip()
                for x in parts
                if x.strip() in WAVES
            ]

            if valid:

                # 对于开奖记录，
                # 如果存的是多波色，
                # 取最后一个作为特码波色
                result.append(
                    valid[-1]
                )

                continue

        # -------------------------------------------------
        # 根据特码计算
        # -------------------------------------------------

        special = _extract_special(
            draw
        )

        if special is None:

            continue

        wave = number_to_wave(
            special
        )

        if wave in WAVES:

            result.append(
                wave
            )

    return result


# =========================================================
# 窗口统计
# =========================================================

def wave_frequency(
    draws: Sequence[Dict[str, Any]],
    window: int = 36,
) -> Dict[str, float]:

    history = extract_wave_history(
        draws[:window]
    )

    counter = Counter(
        history
    )

    total = sum(
        counter.get(
            wave,
            0
        )
        for wave in WAVES
    )

    if total <= 0:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    return {

        wave:
            counter.get(
                wave,
                0
            ) / total

        for wave in WAVES
    }


# =========================================================
# 拉普拉斯平滑
# =========================================================

def smoothed_frequency(
    draws: Sequence[Dict[str, Any]],
    window: int = 36,
    alpha: float = 1.0,
) -> Dict[str, float]:

    history = extract_wave_history(
        draws[:window]
    )

    counter = Counter(
        history
    )

    total = (
        sum(
            counter.get(
                wave,
                0
            )
            for wave in WAVES
        )
        + alpha * len(WAVES)
    )

    return {

        wave:
            (
                counter.get(
                    wave,
                    0
                )
                + alpha
            ) / total

        for wave in WAVES
    }


# =========================================================
# 波色转移矩阵
# =========================================================

def transition_matrix(
    draws: Sequence[Dict[str, Any]],
    window: int = 120,
    alpha: float = 1.0,
) -> Dict[str, Dict[str, float]]:

    history = extract_wave_history(
        draws[:window]
    )

    matrix = {

        source: {

            target: alpha

            for target in WAVES

        }

        for source in WAVES
    }


    if len(history) >= 2:

        for index in range(
            len(history) - 1
        ):

            current = history[index]

            previous = history[index + 1]

            if (
                current not in WAVES
                or previous not in WAVES
            ):

                continue

            matrix[
                previous
            ][
                current
            ] += 1


    result = {}

    for source in WAVES:

        total = sum(
            matrix[source].values()
        )

        if total <= 0:

            result[source] = {
                wave: 1.0 / 3.0
                for wave in WAVES
            }

        else:

            result[source] = {

                wave:
                    matrix[source][wave]
                    / total

                for wave in WAVES
            }

    return result


# =========================================================
# 当前状态下的转移概率
# =========================================================

def transition_probabilities(
    draws: Sequence[Dict[str, Any]],
    window: int = 120,
) -> Dict[str, float]:

    history = extract_wave_history(
        draws[:window]
    )

    if not history:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    current = history[0]

    matrix = transition_matrix(
        draws,
        window=window,
    )

    if current not in matrix:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }

    return matrix[
        current
    ]


# =========================================================
# 综合波色概率
# =========================================================

def wave_probabilities(
    draws: Sequence[Dict[str, Any]],
) -> Dict[str, float]:

    """
    V3综合波色概率：

    12期  -> 近期
    36期  -> 中期
    120期 -> 长期
    转移  -> 状态

    最终加权：

        recent    30%
        medium    25%
        long      15%
        transition 30%
    """

    if not draws:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }


    recent = smoothed_frequency(
        draws,
        window=12,
    )


    medium = smoothed_frequency(
        draws,
        window=36,
    )


    long = smoothed_frequency(
        draws,
        window=120,
    )


    transition = (
        transition_probabilities(
            draws,
            window=120,
        )
    )


    raw = {}

    for wave in WAVES:

        raw[wave] = (

            recent[wave] * 0.30

            + medium[wave] * 0.25

            + long[wave] * 0.15

            + transition[wave] * 0.30

        )


    # -----------------------------------------------------
    # 归一化
    # -----------------------------------------------------

    total = sum(
        raw.values()
    )

    if total <= 0:

        return {
            wave: 1.0 / 3.0
            for wave in WAVES
        }


    result = {

        wave:
            clamp_probability(
                raw[wave] / total
            )

        for wave in WAVES
    }


    # 再归一化
    total = sum(
        result.values()
    )

    return {

        wave:
            result[wave] / total

        for wave in WAVES
    }


# =========================================================
# 波色综合评分
# =========================================================

def wave_scores(
    draws: Sequence[Dict[str, Any]],
) -> Dict[str, float]:

    probabilities = wave_probabilities(
        draws
    )

    return dict(
        probabilities
    )


# =========================================================
# 波色排序
# =========================================================

def rank_waves(
    draws: Sequence[Dict[str, Any]],
) -> List[Tuple[str, float]]:

    probabilities = wave_probabilities(
        draws
    )

    return sorted(

        probabilities.items(),

        key=lambda item: item[1],

        reverse=True,
    )


# =========================================================
# 波色单推
# =========================================================

def wave_single_pick(
    draws: Sequence[Dict[str, Any]],
) -> str:

    ranked = rank_waves(
        draws
    )

    if not ranked:

        return "红"

    return ranked[0][0]


# =========================================================
# 波色双推
# =========================================================

def wave_double_pick(
    draws: Sequence[Dict[str, Any]],
) -> List[str]:

    ranked = rank_waves(
        draws
    )

    return [
        wave
        for wave, _ in ranked[:2]
    ]


# =========================================================
# 完整波色分析
# =========================================================

def analyze_wave(
    draws: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:

    probabilities = wave_probabilities(
        draws
    )

    ranked = rank_waves(
        draws
    )

    transition = transition_probabilities(
        draws,
        window=120,
    )

    recent = smoothed_frequency(
        draws,
        window=12,
    )

    medium = smoothed_frequency(
        draws,
        window=36,
    )

    long = smoothed_frequency(
        draws,
        window=120,
    )


    single = (
        ranked[0][0]
        if ranked
        else "红"
    )


    double = [
        wave
        for wave, _ in ranked[:2]
    ]


    return {

        "single":
            single,

        "double":
            double,

        "probability":
            probabilities,

        "rank":
            [
                {
                    "wave":
                        wave,

                    "probability":
                        round(
                            probability,
                            6
                        ),
                }

                for wave, probability
                in ranked
            ],

        "recent":
            recent,

        "medium":
            medium,

        "long":
            long,

        "transition":
            transition,
    }


# =========================================================
# 根据号码返回波色评分
# =========================================================

def number_wave_score(
    number: int,
    probabilities: Dict[str, float],
) -> float:

    wave = number_to_wave(
        number
    )

    if wave not in WAVES:

        return 0.0

    return float(
        probabilities.get(
            wave,
            0.0
        )
    )


# =========================================================
# 49码波色映射
# =========================================================

def get_number_wave_map() -> Dict[int, str]:

    return dict(
        NUMBER_TO_WAVE
    )


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "V3.0 波色模型测试"
    )

    print("=" * 70)


    print()

    print(
        "49码波色数量："
    )

    print(
        "红：",
        len(RED_NUMBERS)
    )

    print(
        "蓝：",
        len(BLUE_NUMBERS)
    )

    print(
        "绿：",
        len(GREEN_NUMBERS)
    )


    print()

    for number in range(
        1,
        50
    ):

        print(
            f"{number:02d}:"
            f"{number_to_wave(number)}",
            end="  "
        )

        if number % 10 == 0:

            print()


    print()

    print()

    test_draws = [

        {
            "numbers":
                [1, 2, 3, 4, 5, 6, 7]
        },

        {
            "numbers":
                [8, 9, 10, 11, 12, 13, 14]
        },

        {
            "numbers":
                [15, 16, 17, 18, 19, 20, 21]
        },

    ]


    result = analyze_wave(
        test_draws
    )


    print(
        "波色概率："
    )

    print(
        result["probability"]
    )


    print()

    print(
        "波色单推：",
        result["single"]
    )


    print(
        "波色双推：",
        result["double"]
    )


    print()

    print("=" * 70)

    print(
        "测试完成"
    )

    print("=" * 70)