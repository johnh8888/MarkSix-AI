# -*- coding: utf-8 -*-

import json
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
# 百分比格式
# =========================================================

def pct(value):

    try:
        return f"{float(value):.2%}"
    except Exception:
        return "0.00%"


# =========================================================
# 打印号码
# =========================================================

def print_numbers(items):

    result = []

    for item in items:

        try:
            number = int(item["number"])
            result.append(f"{number:02d}")
        except Exception:
            pass

    return " ".join(result)


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
    print(f"{lottery_name} ({lottery_key})")
    print("=" * 70)

    # -----------------------------------------------------
    # 特码10码
    # -----------------------------------------------------

    top10 = prediction.get(
        "top10_numbers",
        []
    )

    print()
    print("【特码10码】")
    print(print_numbers(top10))

    # -----------------------------------------------------
    # 49码排名
    # -----------------------------------------------------

    ranking = prediction.get(
        "number_ranking",
        []
    )

    print()
    print("【49码综合评分 Top10】")

    for index, item in enumerate(
        ranking[:10],
        1
    ):

        number = int(
            item.get("number", 0)
        )

        score = float(
            item.get("score", 0)
        )

        print(
            f"第{index:02d}名  "
            f"{number:02d}  "
            f"评分：{score:.4f}"
        )

    # -----------------------------------------------------
    # 3码
    # -----------------------------------------------------

    top3 = prediction.get(
        "top3_numbers",
        []
    )

    print()
    print("【下一期3码推荐】")
    print(print_numbers(top3))

    # -----------------------------------------------------
    # 第一推荐
    # -----------------------------------------------------

    first = prediction.get(
        "first_number",
        {}
    )

    print()

    print(
        "【第一推荐】"
        f"{int(first.get('number', 0)):02d}"
        f"  "
        f"模型评分："
        f"{float(first.get('score', 0)):.4f}"
    )

    # -----------------------------------------------------
    # 生肖5肖
    # -----------------------------------------------------

    zodiacs = prediction.get(
        "top5_zodiac",
        []
    )

    print()
    print("【特码生肖5肖】")

    print(
        " ".join(
            str(item.get("zodiac", ""))
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
    print("【平特生肖2肖】")

    print(
        " ".join(
            str(item.get("zodiac", ""))
            for item in pingte
        )
    )

    # -----------------------------------------------------
    # 大小
    # -----------------------------------------------------

    size = prediction.get(
        "size",
        {}
    )

    print()
    print(
        "【大小】"
        f"{size.get('prediction', '-')}"
        f" "
        f"{size.get('probability', {})}"
    )

    # -----------------------------------------------------
    # 单双
    # -----------------------------------------------------

    parity = prediction.get(
        "parity",
        {}
    )

    print(
        "【单双】"
        f"{parity.get('prediction', '-')}"
        f" "
        f"{parity.get('probability', {})}"
    )

    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    wave = prediction.get(
        "wave",
        {}
    )

    print()
    print(
        "【波色概率】",
        wave.get(
            "probability",
            {}
        )
    )

    print(
        "【波色单推】",
        wave.get(
            "single_prediction",
            "-"
        )
    )

    print(
        "【波色双推】",
        " + ".join(
            wave.get(
                "double_prediction",
                []
            )
        )
    )

    # -----------------------------------------------------
    # 波色三组合
    # -----------------------------------------------------

    combinations = wave.get(
        "double_combinations",
        []
    )

    if combinations:

        print()
        print("【波色双推组合评分】")

        for item in combinations:

            pair = item.get(
                "pair",
                []
            )

            pair_text = " + ".join(
                pair
            )

            print(
                f"{pair_text}："
                f"{pct(item.get('score', 0))}"
            )

    # -----------------------------------------------------
    # 随机基准
    # -----------------------------------------------------

    print()
    print(
        "【波色随机基准】"
        "单推 33.33%"
        " / "
        "双推 66.67%"
    )


# =========================================================
# 打印回测
# =========================================================

def print_backtest(
    lottery_name,
    results
):

    print()
    print("=" * 70)
    print(f"{lottery_name} 回测结果")
    print("=" * 70)

    # -----------------------------------------------------
    # 只保留10、20
    # -----------------------------------------------------

    for window in [
        "10",
        "20",
    ]:

        result = results.get(
            window,
            {}
        )

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

        print(
            "测试期数：",
            result.get(
                "tests",
                0
            )
        )

        print(
            "特码10码命中率：",
            pct(
                result.get(
                    "number_top10_hit_rate",
                    0
                )
            )
        )

        print(
            "生肖5肖命中率：",
            pct(
                result.get(
                    "zodiac_top5_hit_rate",
                    0
                )
            )
        )

        print(
            "平特2肖命中率：",
            pct(
                result.get(
                    "pingte_top2_hit_rate",
                    0
                )
            )
        )

        print(
            "大小命中率：",
            pct(
                result.get(
                    "size_hit_rate",
                    0
                )
            )
        )

        print(
            "单双命中率：",
            pct(
                result.get(
                    "parity_hit_rate",
                    0
                )
            )
        )

        print(
            "波色单推命中率：",
            pct(
                result.get(
                    "wave_single_hit_rate",
                    0
                )
            )
        )

        print(
            "波色双推命中率：",
            pct(
                result.get(
                    "wave_double_hit_rate",
                    0
                )
            )
        )

        print(
            "波色单推相对随机：",
            pct(
                result.get(
                    "wave_single_edge",
                    0
                )
            )
        )

        print(
            "波色双推相对随机：",
            pct(
                result.get(
                    "wave_double_edge",
                    0
                )
            )
        )

        # -------------------------------------------------
        # 三种组合
        # -------------------------------------------------

        pairs = result.get(
            "wave_pair_rates",
            {}
        )

        if pairs:

            print()
            print(
                "【波色双推组合命中率】"
            )

            for pair_name, rate in pairs.items():

                print(
                    f"{pair_name}："
                    f"{pct(rate)}"
                )


# =========================================================
# 主程序
# =========================================================

def main():

    print()

    print("=" * 70)
    print("六合彩AI智能预测系统 V1.4")
    print("工作流：数据同步 → 独立模型 → 10码 → 3码 → 生肖 → 属性 → 波色 → 10/20期回测")
    print(datetime.now().isoformat())
    print("=" * 70)

    # =====================================================
    # 1. 初始化
    # =====================================================

    print()
    print("【步骤1】初始化数据库")

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
    # 2. 同步
    # =====================================================

    print()
    print("【步骤2】同步在线数据")

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
            "⚠️ 数据同步出现异常：",
            repr(e)
        )

        print(
            "继续使用数据库历史数据进行预测。"
        )

    # =====================================================
    # 3. 预测
    # =====================================================

    predictions = {}
    backtests = {}

    success_count = 0

    for lottery_key, config in LOTTERIES.items():

        lottery_name = config["name"]

        print()
        print("#" * 70)
        print(
            f"开始分析：{lottery_name}"
        )
        print("#" * 70)

        # -------------------------------------------------
        # 获取数据
        # -------------------------------------------------

        try:

            rows = get_draws(
                lottery_key,
                limit=3000
            )

        except Exception as e:

            print(
                "❌ 获取历史数据失败：",
                repr(e)
            )

            continue

        print(
            f"历史数据：{len(rows)}期"
        )

        if len(rows) < 100:

            print(
                f"⚠️ {lottery_name}"
                " 历史数据不足100期，跳过。"
            )

            continue

        # =================================================
        # 预测
        # =================================================

        print()
        print(
            "【步骤3】生成下一期预测"
        )

        try:

            prediction = generate_prediction(
                rows
            )

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

            print_prediction(
                lottery_key,
                lottery_name,
                prediction
            )

            success_count += 1

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
            "【步骤4】Walk-Forward历史回测"
        )

        try:

            result = multi_window_backtest(
                rows
            )

            backtests[lottery_key] = {

                "name":
                    lottery_name,

                "generated_at":
                    datetime.now().isoformat(),

                "results":
                    result,
            }

            print_backtest(
                lottery_name,
                result
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
    # 5. 保存预测
    # =====================================================

    print()
    print(
        "【步骤5】保存预测结果"
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
            "❌ 保存预测失败：",
            repr(e)
        )

    # =====================================================
    # 6. 保存回测
    # =====================================================

    print()
    print(
        "【步骤6】保存回测结果"
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
            "❌ 保存回测失败：",
            repr(e)
        )

    # =====================================================
    # 完成
    # =====================================================

    print()
    print("=" * 70)
    print("本次运行完成")
    print("=" * 70)

    print(
        f"分析彩种：{success_count}"
    )

    print(
        f"本次新增数据：{inserted}"
    )

    print(
        f"预测文件：{PREDICTION_FILE}"
    )

    print(
        f"回测文件：{BACKTEST_FILE}"
    )

    print("=" * 70)
    print("系统运行结束")
    print("=" * 70)


# =========================================================
# Entry
# =========================================================

if __name__ == "__main__":

    main()
