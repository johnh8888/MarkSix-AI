# -*- coding: utf-8 -*-

"""
六合彩 AI 智能预测系统 V2.0

工作流：

1. 初始化数据库
2. 同步在线数据
3. 分析三个彩种
4. 自适应49码评分
5. Top10
6. Top3
7. 生肖5肖
8. 平特2肖
9. 大小
10. 单双
11. 波色单推
12. 波色双推
13. Walk-Forward 10/20期
14. 保存 JSON
"""

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
# JSON
# =========================================================

def save_json(
    path,
    data
):

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
    # Top10
    # =====================================================

    top10 = prediction.get(
        "top10_numbers",
        []
    )


    print()

    print("【特码10码】")

    print(
        " ".join(
            f"{int(item['number']):02d}"
            for item in top10
        )
    )


    print()

    print("【49码综合评分 Top10】")


    for index, item in enumerate(
        top10,
        1
    ):

        print(
            f"第{index:02d}名 "
            f"{int(item['number']):02d} "
            f"评分：{item['score']:.4f}"
        )


    # =====================================================
    # Top3
    # =====================================================

    top3 = prediction.get(
        "top3_numbers",
        []
    )


    print()

    print("【下一期重点推荐】")

    print(
        " ".join(
            f"{int(item['number']):02d}"
            for item in top3
        )
    )


    if top3:

        print(
            f"第一推荐："
            f"{int(top3[0]['number']):02d} "
            f"模型评分："
            f"{top3[0]['score']:.4f}"
        )


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
            item["zodiac"]
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
            item["zodiac"]
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
        ),
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


    print(
        "【单双】",
        parity.get(
            "prediction",
            "-"
        ),
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

    print(
        "【波色单推】",
        wave.get(
            "single",
            "-"
        )
    )


    print(
        "【波色双推】",
        " + ".join(
            wave.get(
                "double",
                []
            )
        )
    )


    print(
        "【波色概率】",
        wave.get(
            "probability",
            {}
        )
    )


    # =====================================================
    # 动态权重
    # =====================================================

    weights = prediction.get(
        "dynamic_weights",
        {}
    )


    print()

    print("【V2.0动态策略权重】")


    for name, weight in weights.items():

        print(
            f"{name:<10}"
            f"{weight:.4f}"
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

    print(
        f"{lottery_name} Walk-Forward回测"
    )

    print("=" * 70)


    # -----------------------------------------------------
    # 只保留10 / 20
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
            f"{result.get('number_top10_hit_rate', 0):.2%}"
        )


        print(
            "生肖5肖命中率：",
            f"{result.get('zodiac_top5_hit_rate', 0):.2%}"
        )


        print(
            "平特2肖命中率：",
            f"{result.get('pingte_top2_hit_rate', 0):.2%}"
        )


        print(
            "大小命中率：",
            f"{result.get('size_hit_rate', 0):.2%}"
        )


        print(
            "单双命中率：",
            f"{result.get('parity_hit_rate', 0):.2%}"
        )


        print(
            "波色单推命中率：",
            f"{result.get('wave_single_hit_rate', 0):.2%}"
        )


        print(
            "波色双推命中率：",
            f"{result.get('wave_double_hit_rate', 0):.2%}"
        )


        print(
            "波色双推提升：",
            f"{result.get('wave_double_improvement', 0):+.2%}"
        )


# =========================================================
# MAIN
# =========================================================

def main():

    print()

    print("=" * 70)

    print(
        "六合彩AI智能预测系统 V2.0"
    )

    print(
        "自适应预测 + 状态识别 + 动态权重"
    )

    print(
        "Walk-Forward：10/20期"
    )

    print(
        datetime.now().isoformat()
    )

    print("=" * 70)


    # =====================================================
    # 1
    # =====================================================

    print()

    print("=" * 70)

    print("【步骤1】初始化数据库")

    print("=" * 70)


    init_database()


    print(
        "✅ 数据库初始化完成"
    )


    # =====================================================
    # 2
    # =====================================================

    print()

    print("=" * 70)

    print("【步骤2】同步在线数据")

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


    # =====================================================
    # 3
    # =====================================================

    predictions = {}

    backtests = {}


    for lottery_key, config in LOTTERIES.items():

        lottery_name = config["name"]


        print()

        print("#" * 70)

        print(
            f"开始分析：{lottery_name}"
        )

        print("#" * 70)


        # -------------------------------------------------
        # 历史
        # -------------------------------------------------

        rows = get_draws(
            lottery_key,
            limit=3000
        )


        print(
            f"历史数据：{len(rows)}期"
        )


        if len(rows) < 100:

            print(
                f"⚠️ {lottery_name}"
                " 历史数据不足100期"
            )

            continue


        # =================================================
        # 预测
        # =================================================

        print()

        print("-" * 70)

        print(
            "【步骤3】生成下一期预测"
        )

        print("-" * 70)


        try:

            prediction = (
                generate_prediction(
                    rows
                )
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


        except Exception as e:

            print()

            print(
                f"❌ {lottery_name}"
                f"预测失败：",
                repr(e)
            )

            continue


        # =================================================
        # 回测
        # =================================================

        print()

        print("-" * 70)

        print(
            "【步骤4】Walk-Forward历史回测"
        )

        print("-" * 70)


        try:

            result = (
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
                    result,
            }


            print_backtest(
                lottery_name,
                result
            )


        except Exception as e:

            print()

            print(
                f"❌ {lottery_name}"
                f"回测失败：",
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
    # 保存
    # =====================================================

    print()

    print("-" * 70)

    print("【步骤5】保存预测结果")

    print("-" * 70)


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


    print()

    print("-" * 70)

    print("【步骤6】保存回测结果")

    print("-" * 70)


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


    # =====================================================
    # 完成
    # =====================================================

    print()

    print("=" * 70)

    print("本次运行完成")

    print("=" * 70)

    print(
        f"分析彩种：{len(predictions)}"
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

    print(
        "系统运行结束"
    )

    print("=" * 70)


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    main()
