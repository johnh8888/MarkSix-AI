# -*- coding: utf-8 -*-

"""
===========================================================
六合彩 AI 智能预测系统 V3.0
===========================================================

核心架构：

历史开奖
    ↓
数据质量检查
    ↓
短期 / 中期 / 长期状态
    ↓
状态识别
    ↓
动态窗口 12 / 36 / 120
    ↓
动态策略权重
    ↓
49码综合概率模型
    ↓
概率校准
    ↓
特码 Top10
    ↓
重点 Top3
    ↓
生肖5肖
    ↓
平特2肖
    ↓
大小
    ↓
单双
    ↓
波色单推
    ↓
波色双推
    ↓
Walk-Forward
    ↓
模块历史表现
    ↓
动态调整下一轮权重

===========================================================
"""

import json
import traceback
from datetime import datetime

from core.config import (
    LOTTERIES,
    PREDICTION_FILE,
    BACKTEST_FILE,
)

from core.database import (
    init_database,
    get_draws,
)

from core.data_source import (
    update_all,
)

from core.predictor import (
    generate_prediction,
)

from core.backtest import (
    multi_window_backtest,
)


# =========================================================
# 系统版本
# =========================================================

VERSION = "V3.0"

SHORT_WINDOW = 12
MEDIUM_WINDOW = 36
LONG_WINDOW = 120

MIN_HISTORY = 120


# =========================================================
# JSON 保存
# =========================================================

def save_json(path, data):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# 安全格式化概率
# =========================================================

def format_probability(value):

    try:

        value = float(value)

        return f"{value:.3f}"

    except Exception:

        return "-"


# =========================================================
# 打印动态窗口
# =========================================================

def print_windows(prediction):

    windows = prediction.get(
        "windows",
        {}
    )

    if not windows:

        windows = {
            "short": SHORT_WINDOW,
            "medium": MEDIUM_WINDOW,
            "long": LONG_WINDOW,
        }

    print()
    print("【V3.0动态分析窗口】")

    print(
        f"短期：{windows.get('short', SHORT_WINDOW)}期"
    )

    print(
        f"中期：{windows.get('medium', MEDIUM_WINDOW)}期"
    )

    print(
        f"长期：{windows.get('long', LONG_WINDOW)}期"
    )


# =========================================================
# 打印状态
# =========================================================

def print_state(prediction):

    state = prediction.get(
        "state",
        {}
    )

    print()
    print("【当前市场状态】")

    print(
        "状态：",
        state.get(
            "name",
            state.get(
                "state",
                "-"
            )
        )
    )

    print(
        "置信度：",
        format_probability(
            state.get(
                "confidence",
                0
            )
        )
    )


# =========================================================
# 打印动态权重
# =========================================================

def print_weights(prediction):

    weights = prediction.get(
        "dynamic_weights",
        {}
    )

    print()
    print("【V3.0动态策略权重】")

    if not weights:

        print("暂无")

        return

    for name, value in weights.items():

        try:

            print(
                f"{str(name):<15}"
                f"{float(value):.4f}"
            )

        except Exception:

            print(
                f"{str(name):<15}"
                f"{value}"
            )


# =========================================================
# 打印模块表现
# =========================================================

def print_module_performance(prediction):

    performance = prediction.get(
        "module_performance",
        {}
    )

    if not performance:

        return

    print()
    print("【模块历史表现】")

    for name, value in performance.items():

        if isinstance(value, dict):

            hit_rate = value.get(
                "hit_rate",
                value.get(
                    "accuracy",
                    None
                )
            )

            tests = value.get(
                "tests",
                value.get(
                    "count",
                    "-"
                )
            )

            if hit_rate is not None:

                try:

                    print(
                        f"{name:<15}"
                        f"命中率："
                        f"{float(hit_rate):.2%} "
                        f"测试：{tests}"
                    )

                except Exception:

                    print(
                        f"{name:<15}"
                        f"{value}"
                    )

            else:

                print(
                    f"{name:<15}"
                    f"{value}"
                )

        else:

            try:

                print(
                    f"{name:<15}"
                    f"{float(value):.2%}"
                )

            except Exception:

                print(
                    f"{name:<15}"
                    f"{value}"
                )


# =========================================================
# 打印预测
# =========================================================

def print_prediction(
    lottery_key,
    lottery_name,
    prediction
):

    print()
    print("=" * 70)

    print(
        f"{lottery_name} ({lottery_key})"
    )

    print("=" * 70)

    # =====================================================
    # 状态
    # =====================================================

    print_state(prediction)

    print_windows(prediction)

    # =====================================================
    # Top10
    # =====================================================

    top10 = prediction.get(
        "top10_numbers",
        []
    )

    print()
    print("【特码10码】")

    numbers = []

    for item in top10:

        try:

            numbers.append(
                f"{int(item['number']):02d}"
            )

        except Exception:

            pass

    print(
        " ".join(numbers)
    )

    print()

    print("【49码综合评分 Top10】")

    for index, item in enumerate(
        top10,
        1
    ):

        try:

            number = int(
                item["number"]
            )

            score = float(
                item.get(
                    "score",
                    0
                )
            )

            probability = float(
                item.get(
                    "probability",
                    0
                )
            )

            print(
                f"第{index:02d}名 "
                f"{number:02d} "
                f"评分：{score:.4f} "
                f"概率：{probability:.4f}"
            )

        except Exception:

            print(
                f"第{index:02d}名 "
                f"{item}"
            )

    # =====================================================
    # Top3
    # =====================================================

    top3 = prediction.get(
        "top3_numbers",
        []
    )

    print()
    print("【重点推荐 Top3】")

    print(
        " ".join(
            f"{int(item['number']):02d}"
            for item in top3
            if "number" in item
        )
    )

    if top3:

        try:

            first = top3[0]

            print(
                "第一推荐：",
                f"{int(first['number']):02d}",
                "评分：",
                f"{float(first.get('score', 0)):.4f}"
            )

        except Exception:

            pass

    # =====================================================
    # 生肖
    # =====================================================

    zodiacs = prediction.get(
        "top5_zodiac",
        []
    )

    print()
    print("【特码生肖5肖】")

    print(
        " ".join(
            item.get(
                "zodiac",
                "-"
            )
            for item in zodiacs
        )
    )

    # =====================================================
    # 平特
    # =====================================================

    pingte = prediction.get(
        "top2_pingte_zodiac",
        []
    )

    print()
    print("【平特生肖2肖】")

    print(
        " ".join(
            item.get(
                "zodiac",
                "-"
            )
            for item in pingte
        )
    )

    # =====================================================
    # 大小
    # =====================================================

    size = prediction.get(
        "size",
        {}
    )

    print()
    print(
        "【大小】",
        size.get(
            "prediction",
            "-"
        )
    )

    print(
        "概率：",
        size.get(
            "probability",
            {}
        )
    )

    # =====================================================
    # 单双
    # =====================================================

    parity = prediction.get(
        "parity",
        {}
    )

    print()
    print(
        "【单双】",
        parity.get(
            "prediction",
            "-"
        )
    )

    print(
        "概率：",
        parity.get(
            "probability",
            {}
        )
    )

    # =====================================================
    # 波色
    # =====================================================

    wave = prediction.get(
        "wave",
        {}
    )

    print()
    print("【波色单推】")

    print(
        wave.get(
            "single",
            "-"
        )
    )

    print()
    print("【波色双推】")

    double_wave = wave.get(
        "double",
        []
    )

    print(
        " + ".join(
            double_wave
        )
    )

    print()
    print("【波色概率】")

    print(
        wave.get(
            "probability",
            {}
        )
    )

    # =====================================================
    # 波色转移
    # =====================================================

    transition = wave.get(
        "transition",
        {}
    )

    if transition:

        print()
        print("【波色转移模型】")

        for key, value in transition.items():

            print(
                f"{key} → {value}"
            )

    # =====================================================
    # 动态权重
    # =====================================================

    print_weights(
        prediction
    )

    # =====================================================
    # 模块表现
    # =====================================================

    print_module_performance(
        prediction
    )


# =========================================================
# 回测结果安全提取
# =========================================================

def get_result_value(
    result,
    *keys,
    default=0
):

    for key in keys:

        if key in result:

            return result[key]

    return default


# =========================================================
# 打印 V3 回测
# =========================================================

def print_backtest(
    lottery_name,
    results
):

    print()
    print("=" * 70)

    print(
        f"{lottery_name} Walk-Forward V3.0"
    )

    print("=" * 70)

    if not results:

        print(
            "没有回测结果"
        )

        return

    # =====================================================
    # V3 优先读取整体结果
    # =====================================================

    summary = results.get(
        "summary",
        {}
    )

    if summary:

        print()
        print("【V3.0总体表现】")

        for name, value in summary.items():

            if isinstance(value, (int, float)):

                if 0 <= value <= 1:

                    print(
                        f"{name:<25}"
                        f"{value:.2%}"
                    )

                else:

                    print(
                        f"{name:<25}"
                        f"{value}"
                    )

            else:

                print(
                    f"{name:<25}"
                    f"{value}"
                )

    # =====================================================
    # 模块表现
    # =====================================================

    modules = results.get(
        "modules",
        results.get(
            "module_performance",
            {}
        )
    )

    if modules:

        print()
        print("【模块历史命中率】")

        for name, result in modules.items():

            if isinstance(result, dict):

                rate = get_result_value(
                    result,
                    "hit_rate",
                    "accuracy",
                    default=0
                )

                tests = get_result_value(
                    result,
                    "tests",
                    "count",
                    default=0
                )

            else:

                rate = result
                tests = 0

            try:

                print(
                    f"{name:<20}"
                    f"{float(rate):.2%} "
                    f"测试：{tests}"
                )

            except Exception:

                print(
                    f"{name:<20}"
                    f"{result}"
                )

    # =====================================================
    # V2兼容：10/20
    # =====================================================

    for window in [
        "10",
        "20",
    ]:

        result = results.get(
            window
        )

        if not isinstance(
            result,
            dict
        ):

            continue

        print()
        print(
            f"【最近{window}期】"
        )

        if "error" in result:

            print(
                "错误：",
                result["error"]
            )

            continue

        tests = result.get(
            "tests",
            0
        )

        print(
            "测试期数：",
            tests
        )

        fields = [

            (
                "特码10码",
                "number_top10_hit_rate"
            ),

            (
                "生肖5肖",
                "zodiac_top5_hit_rate"
            ),

            (
                "平特2肖",
                "pingte_top2_hit_rate"
            ),

            (
                "大小",
                "size_hit_rate"
            ),

            (
                "单双",
                "parity_hit_rate"
            ),

            (
                "波色单推",
                "wave_single_hit_rate"
            ),

            (
                "波色双推",
                "wave_double_hit_rate"
            ),

        ]

        for label, key in fields:

            value = result.get(
                key,
                0
            )

            try:

                print(
                    f"{label}命中率："
                    f"{float(value):.2%}"
                )

            except Exception:

                print(
                    f"{label}：{value}"
                )

        improvement = result.get(
            "wave_double_improvement",
            0
        )

        try:

            print(
                "波色双推提升：",
                f"{float(improvement):+.2%}"
            )

        except Exception:

            pass


# =========================================================
# 数据质量检查
# =========================================================

def validate_rows(
    lottery_name,
    rows
):

    print()
    print(
        f"【数据质量检查】{lottery_name}"
    )

    if not rows:

        print(
            "❌ 没有历史数据"
        )

        return False

    valid = 0

    for row in rows:

        try:

            numbers = (
                row.get("numbers")
                if isinstance(row, dict)
                else None
            )

            if isinstance(
                numbers,
                str
            ):

                numbers = [
                    int(x)
                    for x in numbers.replace(
                        ",",
                        " "
                    ).split()
                    if x.strip()
                ]

            if numbers:

                if len(numbers) >= 7:

                    valid += 1

        except Exception:

            continue

    print(
        f"总记录：{len(rows)}"
    )

    print(
        f"有效记录：{valid}"
    )

    rate = (
        valid / len(rows)
        if rows
        else 0
    )

    print(
        f"有效率：{rate:.2%}"
    )

    if valid < MIN_HISTORY:

        print(
            f"⚠️ 有效数据不足 "
            f"{MIN_HISTORY}期"
        )

        return False

    print(
        "✅ 数据质量检查通过"
    )

    return True


# =========================================================
# 运行单个彩种
# =========================================================

def process_lottery(
    lottery_key,
    config
):

    lottery_name = config["name"]

    print()
    print("#" * 70)

    print(
        f"开始分析：{lottery_name}"
    )

    print("#" * 70)

    # =====================================================
    # 获取历史
    # =====================================================

    rows = get_draws(
        lottery_key,
        limit=3000
    )

    print(
        f"历史数据：{len(rows)}期"
    )

    # =====================================================
    # 数据质量
    # =====================================================

    if not validate_rows(
        lottery_name,
        rows
    ):

        return None, {
            "name": lottery_name,
            "error": "历史数据不足或数据质量不合格",
        }

    # =====================================================
    # 预测
    # =====================================================

    print()
    print("-" * 70)

    print(
        "【步骤3】生成 V3.0 下一期预测"
    )

    print("-" * 70)

    try:

        prediction = generate_prediction(
            rows
        )

    except TypeError:

        # -------------------------------------------------
        # 如果 V3 predictor 支持 lottery_key
        # -------------------------------------------------

        try:

            prediction = generate_prediction(
                rows,
                lottery_key=lottery_key
            )

        except Exception:

            raise

    # =====================================================
    # 打印
    # =====================================================

    print_prediction(
        lottery_key,
        lottery_name,
        prediction
    )

    prediction_record = {

        "name":
            lottery_name,

        "version":
            VERSION,

        "generated_at":
            datetime.now().isoformat(),

        "history_count":
            len(rows),

        "windows": {

            "short":
                SHORT_WINDOW,

            "medium":
                MEDIUM_WINDOW,

            "long":
                LONG_WINDOW,

        },

        "prediction":
            prediction,

    }

    # =====================================================
    # Walk-Forward
    # =====================================================

    print()
    print("-" * 70)

    print(
        "【步骤4】V3.0 Walk-Forward历史回测"
    )

    print("-" * 70)

    try:

        try:

            result = multi_window_backtest(
                rows
            )

        except TypeError:

            result = multi_window_backtest(
                rows,
                short_window=SHORT_WINDOW,
                medium_window=MEDIUM_WINDOW,
                long_window=LONG_WINDOW,
            )

        print_backtest(
            lottery_name,
            result
        )

        backtest_record = {

            "name":
                lottery_name,

            "version":
                VERSION,

            "generated_at":
                datetime.now().isoformat(),

            "results":
                result,

        }

    except Exception as e:

        print()
        print(
            f"❌ {lottery_name} "
            f"回测失败：{repr(e)}"
        )

        traceback.print_exc()

        backtest_record = {

            "name":
                lottery_name,

            "version":
                VERSION,

            "generated_at":
                datetime.now().isoformat(),

            "error":
                repr(e),

        }

    return (
        prediction_record,
        backtest_record
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print()

    print("=" * 70)

    print(
        "六合彩 AI 智能预测系统 V3.0"
    )

    print(
        "动态状态 + 动态窗口 + 动态策略权重"
    )

    print(
        "号码模型 + 大小 + 单双 + 波色转移"
    )

    print(
        "Walk-Forward + 模块历史表现"
    )

    print(
        datetime.now().isoformat()
    )

    print("=" * 70)

    # =====================================================
    # 1. 初始化数据库
    # =====================================================

    print()
    print("=" * 70)

    print(
        "【步骤1】初始化数据库"
    )

    print("=" * 70)

    try:

        init_database()

        print(
            "✅ 数据库初始化完成"
        )

    except Exception as e:

        print(
            "❌ 数据库初始化失败：",
            repr(e)
        )

        traceback.print_exc()

        raise

    # =====================================================
    # 2. 同步数据
    # =====================================================

    print()
    print("=" * 70)

    print(
        "【步骤2】同步在线数据"
    )

    print("=" * 70)

    inserted = 0

    try:

        inserted = update_all()

        print()
        print(
            f"本次新增数据：{inserted}"
        )

    except Exception as e:

        print()
        print(
            "⚠️ 数据同步异常：",
            repr(e)
        )

        traceback.print_exc()

    # =====================================================
    # 3. 三彩种分析
    # =====================================================

    predictions = {}

    backtests = {}

    errors = {}

    for lottery_key, config in LOTTERIES.items():

        try:

            prediction_record, backtest_record = (
                process_lottery(
                    lottery_key,
                    config
                )
            )

            if prediction_record:

                predictions[
                    lottery_key
                ] = prediction_record

            if backtest_record:

                backtests[
                    lottery_key
                ] = backtest_record

        except Exception as e:

            lottery_name = config["name"]

            print()
            print(
                f"❌ {lottery_name}"
                f"整个分析流程失败："
            )

            print(
                repr(e)
            )

            traceback.print_exc()

            errors[
                lottery_key
            ] = {

                "name":
                    lottery_name,

                "error":
                    repr(e),

            }

    # =====================================================
    # 4. 保存预测
    # =====================================================

    print()
    print("-" * 70)

    print(
        "【步骤5】保存 V3.0预测结果"
    )

    print("-" * 70)

    prediction_output = {

        "version":
            VERSION,

        "generated_at":
            datetime.now().isoformat(),

        "system": {

            "short_window":
                SHORT_WINDOW,

            "medium_window":
                MEDIUM_WINDOW,

            "long_window":
                LONG_WINDOW,

            "dynamic_windows":
                True,

            "dynamic_weights":
                True,

            "state_detection":
                True,

            "wave_transition":
                True,

            "walk_forward":
                True,

        },

        "lotteries":
            predictions,

        "errors":
            errors,

    }

    save_json(
        PREDICTION_FILE,
        prediction_output
    )

    print(
        "✅ 预测结果已保存"
    )

    print(
        f"文件：{PREDICTION_FILE}"
    )

    # =====================================================
    # 5. 保存回测
    # =====================================================

    print()
    print("-" * 70)

    print(
        "【步骤6】保存 V3.0回测结果"
    )

    print("-" * 70)

    backtest_output = {

        "version":
            VERSION,

        "generated_at":
            datetime.now().isoformat(),

        "windows": {

            "short":
                SHORT_WINDOW,

            "medium":
                MEDIUM_WINDOW,

            "long":
                LONG_WINDOW,

        },

        "lotteries":
            backtests,

        "errors":
            errors,

    }

    save_json(
        BACKTEST_FILE,
        backtest_output
    )

    print(
        "✅ 回测结果已保存"
    )

    print(
        f"文件：{BACKTEST_FILE}"
    )

    # =====================================================
    # 完成
    # =====================================================

    print()
    print("=" * 70)

    print(
        "六合彩 AI 智能预测系统 V3.0"
    )

    print(
        "本次运行完成"
    )

    print("=" * 70)

    print(
        f"分析彩种："
        f"{len(predictions)}"
    )

    print(
        f"本次新增数据："
        f"{inserted}"
    )

    print(
        f"失败彩种："
        f"{len(errors)}"
    )

    print(
        f"预测文件："
        f"{PREDICTION_FILE}"
    )

    print(
        f"回测文件："
        f"{BACKTEST_FILE}"
    )

    print("=" * 70)


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    main()