# -*- coding: utf-8 -*-

"""
六合彩综合预测系统 V1.2

功能：

1. 在线同步香港六合彩 / 新澳门六合彩 / 老澳门六合彩
2. 49个号码综合评分
3. 特码10码
4. 下一期最推荐号码
5. 特码生肖5肖
6. 平特生肖2肖
7. 大小预测
8. 单双预测
9. 波色预测
10. 10 / 20 / 30 / 60 / 100期回测
11. 波色回测
12. JSON结果保存

说明：

预测号码来自 predictor.py：
    1~49 全部评分
    ↓
    综合排序
    ↓
    Top10

本文件只负责：
    主流程
    输出
    保存
    调度预测和回测
"""


import json

from datetime import datetime


# =========================================================
# 配置
# =========================================================

from core.config import (
    LOTTERIES,
    PREDICTION_FILE,
    BACKTEST_FILE,
)


# =========================================================
# 数据库
# =========================================================

from core.database import (
    init_database,
    get_draws,
)


# =========================================================
# 数据同步
# =========================================================

from core.data_source import (
    update_all,
)


# =========================================================
# 预测模型
# =========================================================

from core.predictor import (
    generate_prediction,
)


# =========================================================
# 回测
# =========================================================

from core.backtest import (
    multi_window_backtest,
)


# =========================================================
# 保存 JSON
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
# 格式化号码
# =========================================================

def format_number(number):

    try:

        return f"{int(number):02d}"

    except Exception:

        return "--"


# =========================================================
# 获取 Top10 号码
# =========================================================

def get_top10_numbers(prediction):

    items = prediction.get(
        "top10_numbers",
        []
    )

    result = []

    for item in items:

        try:

            result.append(
                int(item["number"])
            )

        except Exception:

            continue

    return result


# =========================================================
# 打印 Top10
# =========================================================

def print_top10(prediction):

    numbers = prediction.get(
        "top10_numbers",
        []
    )

    print()
    print("【特码10码】")

    if not numbers:

        print("--")

        return

    result = []

    for index, item in enumerate(
        numbers,
        start=1
    ):

        number = item.get(
            "number"
        )

        score = item.get(
            "score",
            0
        )

        result.append(
            f"{format_number(number)}"
        )

    print(
        " ".join(result)
    )

    # -----------------------------------------------------
    # 显示详细评分
    # -----------------------------------------------------

    print()
    print("【49码综合评分 Top10】")

    for index, item in enumerate(
        numbers,
        start=1
    ):

        number = item.get(
            "number"
        )

        score = item.get(
            "score",
            0
        )

        try:

            score_text = f"{float(score):.4f}"

        except Exception:

            score_text = str(score)

        print(
            f"第{index:02d}名  "
            f"{format_number(number)}  "
            f"评分：{score_text}"
        )


# =========================================================
# 下一期最推荐
# =========================================================

def print_recommended_numbers(
    prediction,
    count=3
):

    numbers = prediction.get(
        "top10_numbers",
        []
    )

    if not numbers:

        print()
        print(
            "【下一期最推荐】--"
        )

        return

    selected = numbers[:count]

    print()
    print(
        "【下一期最推荐】"
    )

    result = []

    for item in selected:

        number = item.get(
            "number"
        )

        result.append(
            format_number(number)
        )

    print(
        " ".join(result)
    )

    # -----------------------------------------------------
    # 显示第一推荐
    # -----------------------------------------------------

    first = selected[0]

    first_number = first.get(
        "number"
    )

    first_score = first.get(
        "score",
        0
    )

    print(
        f"第一推荐："
        f"{format_number(first_number)}"
        f"  "
        f"模型评分：{float(first_score):.4f}"
    )

    # -----------------------------------------------------
    # 注意：
    #
    # 这里的 score 是模型排序分数，
    # 不是经过概率校准后的真实中奖概率。
    #
    # 所以不能直接把 0.50
    # 理解成 50% 中奖概率。
    # -----------------------------------------------------


# =========================================================
# 打印生肖
# =========================================================

def print_zodiacs(prediction):

    # -----------------------------------------------------
    # 特码5肖
    # -----------------------------------------------------

    zodiacs = prediction.get(
        "top5_zodiac",
        []
    )

    print()
    print(
        "【特码生肖5肖】"
    )

    if not zodiacs:

        print("--")

    else:

        print(
            " ".join(
                item.get(
                    "zodiac",
                    "-"
                )

                for item in zodiacs
            )
        )

    # -----------------------------------------------------
    # 平特2肖
    # -----------------------------------------------------

    pingte = prediction.get(
        "top2_pingte_zodiac",
        []
    )

    print()
    print(
        "【平特生肖2肖】"
    )

    if not pingte:

        print("--")

    else:

        print(
            " ".join(
                item.get(
                    "zodiac",
                    "-"
                )

                for item in pingte
            )
        )


# =========================================================
# 打印大小
# =========================================================

def print_size(prediction):

    size = prediction.get(
        "size",
        {}
    )

    predicted = size.get(
        "prediction",
        "-"
    )

    probability = size.get(
        "probability",
        {}
    )

    print()
    print(
        "【大小】"
        f"{predicted}"
        f" "
        f"{probability}"
    )


# =========================================================
# 打印单双
# =========================================================

def print_parity(prediction):

    parity = prediction.get(
        "parity",
        {}
    )

    predicted = parity.get(
        "prediction",
        "-"
    )

    probability = parity.get(
        "probability",
        {}
    )

    print(
        "【单双】"
        f"{predicted}"
        f" "
        f"{probability}"
    )


# =========================================================
# 打印波色
# =========================================================

def print_wave(prediction):

    wave = prediction.get(
        "wave",
        {}
    )

    predicted = wave.get(
        "prediction",
        "-"
    )

    probability = wave.get(
        "probability",
        {}
    )

    print(
        "【波色】"
        f"{predicted}"
        f" "
        f"{probability}"
    )


# =========================================================
# 完整打印预测
# =========================================================

def print_prediction(
    lottery_key,
    lottery_name,
    prediction
):

    print()
    print(
        "=" * 70
    )

    print(
        f"{lottery_name} ({lottery_key})"
    )

    print(
        "=" * 70
    )

    # -----------------------------------------------------
    # Top10
    # -----------------------------------------------------

    print_top10(
        prediction
    )

    # -----------------------------------------------------
    # 下一期推荐
    # -----------------------------------------------------

    print_recommended_numbers(
        prediction,
        count=3
    )

    # -----------------------------------------------------
    # 生肖
    # -----------------------------------------------------

    print_zodiacs(
        prediction
    )

    # -----------------------------------------------------
    # 大小
    # -----------------------------------------------------

    print_size(
        prediction
    )

    # -----------------------------------------------------
    # 单双
    # -----------------------------------------------------

    print_parity(
        prediction
    )

    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    print_wave(
        prediction
    )


# =========================================================
# 打印回测
# =========================================================

def print_backtest(
    lottery_name,
    results
):

    print()
    print(
        "=" * 70
    )

    print(
        f"{lottery_name} 回测结果"
    )

    print(
        "=" * 70
    )

    windows = [
        "10",
        "20",
        "30",
        "60",
        "100",
    ]

    for window in windows:

        result = results.get(
            window,
            {}
        )

        print()

        print(
            f"【最近{window}期】"
        )

        # -------------------------------------------------
        # 错误
        # -------------------------------------------------

        if "error" in result:

            print(
                "错误：",
                result["error"]
            )

            continue

        # -------------------------------------------------
        # 测试数量
        # -------------------------------------------------

        print(
            "测试期数：",
            result.get(
                "tests",
                0
            )
        )

        # -------------------------------------------------
        # 特码10码
        # -------------------------------------------------

        print(
            "特码10码命中率：",
            f"{result.get('number_top10_hit_rate', 0):.2%}"
        )

        # -------------------------------------------------
        # 特码5肖
        # -------------------------------------------------

        print(
            "生肖5肖命中率：",
            f"{result.get('zodiac_top5_hit_rate', 0):.2%}"
        )

        # -------------------------------------------------
        # 平特2肖
        # -------------------------------------------------

        print(
            "平特2肖命中率：",
            f"{result.get('pingte_top2_hit_rate', 0):.2%}"
        )

        # -------------------------------------------------
        # 大小
        # -------------------------------------------------

        print(
            "大小命中率：",
            f"{result.get('size_hit_rate', 0):.2%}"
        )

        # -------------------------------------------------
        # 单双
        # -------------------------------------------------

        print(
            "单双命中率：",
            f"{result.get('parity_hit_rate', 0):.2%}"
        )

        # -------------------------------------------------
        # ⭐ 波色
        # -------------------------------------------------

        print(
            "波色命中率：",
            f"{result.get('wave_hit_rate', 0):.2%}"
        )


# =========================================================
# 打印历史数据状态
# =========================================================

def print_data_status():

    print()
    print(
        "=" * 70
    )

    print(
        "当前数据状态"
    )

    print(
        "=" * 70
    )


# =========================================================
# 主程序
# =========================================================

def main():

    # =====================================================
    # 标题
    # =====================================================

    print()

    print(
        "=" * 70
    )

    print(
        "六合彩AI智能预测系统 V1.2"
    )

    print(
        "工作流：中文综合预测 → 49码评分 → Top10 → 下一期推荐 → 回测"
    )

    print(
        datetime.now().isoformat()
    )

    print(
        "=" * 70
    )

    # =====================================================
    # 1. 初始化数据库
    # =====================================================

    print()

    print(
        "【步骤1】初始化数据库"
    )

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

        return

    # =====================================================
    # 2. 更新在线数据
    # =====================================================

    print()

    print(
        "=" * 70
    )

    print(
        "【步骤2】同步在线数据"
    )

    print(
        "=" * 70
    )

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
            "⚠️ 数据更新出现异常：",
            repr(e)
        )

        print(
            "继续使用数据库已有历史数据..."
        )

    # =====================================================
    # 3. 创建结果容器
    # =====================================================

    predictions = {}

    backtests = {}

    # =====================================================
    # 4. 三彩种统一分析
    # =====================================================

    for lottery_key, config in LOTTERIES.items():

        lottery_name = config["name"]

        print()

        print(
            "#" * 70
        )

        print(
            f"开始分析：{lottery_name}"
        )

        print(
            "#" * 70
        )

        # -------------------------------------------------
        # 获取历史数据
        # -------------------------------------------------

        try:

            rows = get_draws(
                lottery_key,
                limit=3000
            )

        except Exception as e:

            print(
                f"❌ {lottery_name}读取数据库失败：",
                repr(e)
            )

            continue

        print(
            f"历史数据：{len(rows)}期"
        )

        # -------------------------------------------------
        # 数据不足
        # -------------------------------------------------

        if len(rows) < 100:

            print(
                f"⚠️ {lottery_name}"
                " 历史数据不足100期，跳过。"
            )

            continue

        # =================================================
        # 当前预测
        # =================================================

        print()

        print(
            "-" * 70
        )

        print(
            "【步骤3】生成下一期预测"
        )

        print(
            "-" * 70
        )

        try:

            prediction = generate_prediction(
                rows
            )

            # -------------------------------------------------
            # 保存预测
            # -------------------------------------------------

            predictions[lottery_key] = {

                "name":
                    lottery_name,

                "generated_at":
                    datetime.now().isoformat(),

                "history_count":
                    len(rows),

                "prediction":
                    prediction,
            }

            # -------------------------------------------------
            # 打印预测
            # -------------------------------------------------

            print_prediction(
                lottery_key,
                lottery_name,
                prediction
            )

        except Exception as e:

            print()

            print(
                f"❌ {lottery_name}预测失败：",
                repr(e)
            )

            continue

        # =================================================
        # 回测
        # =================================================

        print()

        print(
            "-" * 70
        )

        print(
            "【步骤4】Walk-Forward历史回测"
        )

        print(
            "-" * 70
        )

        try:

            backtest_result = (
                multi_window_backtest(
                    rows
                )
            )

            backtests[lottery_key] = {

                "name":
                    lottery_name,

                "generated_at":
                    datetime.now().isoformat(),

                "results":
                    backtest_result,
            }

            # -------------------------------------------------
            # 打印
            # -------------------------------------------------

            print_backtest(
                lottery_name,
                backtest_result
            )

        except Exception as e:

            print()

            print(
                f"❌ {lottery_name}回测失败：",
                repr(e)
            )

            backtests[lottery_key] = {

                "name":
                    lottery_name,

                "generated_at":
                    datetime.now().isoformat(),

                "error":
                    repr(e),
            }

    # =====================================================
    # 5. 保存预测 JSON
    # =====================================================

    print()

    print(
        "-" * 70
    )

    print(
        "【步骤5】保存预测结果"
    )

    print(
        "-" * 70
    )

    try:

        save_json(
            PREDICTION_FILE,
            predictions
        )

        print(
            "✅ 预测结果已保存"
        )

        print(
            f"文件：{PREDICTION_FILE}"
        )

    except Exception as e:

        print(
            "❌ 保存预测文件失败：",
            repr(e)
        )

    # =====================================================
    # 6. 保存回测 JSON
    # =====================================================

    print()

    print(
        "-" * 70
    )

    print(
        "【步骤6】保存回测结果"
    )

    print(
        "-" * 70
    )

    try:

        save_json(
            BACKTEST_FILE,
            backtests
        )

        print(
            "✅ 回测结果已保存"
        )

        print(
            f"文件：{BACKTEST_FILE}"
        )

    except Exception as e:

        print(
            "❌ 保存回测文件失败：",
            repr(e)
        )

    # =====================================================
    # 7. 最终总结
    # =====================================================

    print()

    print(
        "=" * 70
    )

    print(
        "本次运行完成"
    )

    print(
        "=" * 70
    )

    print(
        f"分析彩种：{len(predictions)}"
    )

    print(
        f"本次新增数据：{inserted}"
    )

    print()

    print(
        "预测文件："
    )

    print(
        PREDICTION_FILE
    )

    print()

    print(
        "回测文件："
    )

    print(
        BACKTEST_FILE
    )

    print()

    print(
        "=" * 70
    )

    print(
        "系统运行结束"
    )

    print(
        "=" * 70
    )


# =========================================================
# Entry
# =========================================================

if __name__ == "__main__":

    main()
