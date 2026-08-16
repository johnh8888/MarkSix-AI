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
    count_draws,
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
# 保存 JSON
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

    print(
        "=" * 70
    )

    print(
        f"{lottery_name} ({lottery_key})"
    )

    print(
        "=" * 70
    )

    # =====================================================
    # 特码10码
    # =====================================================

    numbers = prediction.get(
        "top10_numbers",
        []
    )

    print()

    print(
        "【特码10码】"
    )

    print(
        " ".join(

            f"{int(item['number']):02d}"

            for item in numbers
        )
    )

    # =====================================================
    # 49码综合评分 Top10
    # =====================================================

    print()

    print(
        "【49码综合评分 Top10】"
    )

    for index, item in enumerate(
        numbers,
        1
    ):

        print(

            f"第{index:02d}名  "
            f"{int(item['number']):02d}  "
            f"评分："
            f"{float(item['score']):.4f}"
        )

    # =====================================================
    # 下一期推荐
    # =====================================================

    if numbers:

        top3 = numbers[:3]

        print()

        print(
            "【下一期最推荐】"
        )

        print(
            " ".join(

                f"{int(item['number']):02d}"

                for item in top3
            )
        )

        first = top3[0]

        print(

            f"第一推荐："
            f"{int(first['number']):02d}  "
            f"模型评分："
            f"{float(first['score']):.4f}"
        )

    # =====================================================
    # 生肖5肖
    # =====================================================

    zodiacs = prediction.get(
        "top5_zodiac",
        []
    )

    print()

    print(
        "【特码生肖5肖】"
    )

    print(

        " ".join(

            item["zodiac"]

            for item in zodiacs
        )
    )

    # =====================================================
    # 平特2肖
    # =====================================================

    pingte = prediction.get(
        "top2_pingte_zodiac",
        []
    )

    print()

    print(
        "【平特生肖2肖】"
    )

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
        "【大小】"
        f"{size.get('prediction', '-')}"
        f" "
        f"{size.get('probability', {})}"
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
        "【单双】"
        f"{parity.get('prediction', '-')}"
        f" "
        f"{parity.get('probability', {})}"
    )

    # =====================================================
    # ⭐ 波色
    # =====================================================

    wave = prediction.get(
        "wave",
        {}
    )

    # -----------------------------------------------------
    # 单推
    # -----------------------------------------------------

    wave_single = wave.get(
        "prediction",
        "-"
    )

    # -----------------------------------------------------
    # 双推
    # -----------------------------------------------------

    wave_top2 = wave.get(
        "top2",
        []
    )

    wave_top2_names = [

        item.get(
            "wave",
            "-"
        )

        for item in wave_top2
    ]

    # -----------------------------------------------------
    # 概率
    # -----------------------------------------------------

    wave_probability = wave.get(
        "probability",
        {}
    )

    print()

    print(
        "【波色单推】",
        wave_single
    )

    print(
        "【波色双推】",
        " + ".join(
            wave_top2_names
        )
    )

    print(
        "【波色概率】",
        wave_probability
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

    for window in [

        "10",

        "20",

        "30",

        "60",

        "100",

    ]:

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
        # 测试期数
        # -------------------------------------------------

        print(
            "测试期数：",
            result.get(
                "tests",
                0
            )
        )

        # -------------------------------------------------
        # 特码
        # -------------------------------------------------

        print(
            "特码10码命中率：",
            f"{result.get('number_top10_hit_rate', 0):.2%}"
        )

        # -------------------------------------------------
        # 生肖
        # -------------------------------------------------

        print(
            "生肖5肖命中率：",
            f"{result.get('zodiac_top5_hit_rate', 0):.2%}"
        )

        # -------------------------------------------------
        # 平特
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
        # 波色单推
        # -------------------------------------------------

        print(
            "波色单推命中率：",
            f"{result.get('wave_hit_rate', 0):.2%}"
        )

        # -------------------------------------------------
        # ⭐ 波色双推
        # -------------------------------------------------

        print(
            "波色双推命中率：",
            f"{result.get('wave_top2_hit_rate', 0):.2%}"
        )

        # -------------------------------------------------
        # ⭐ 双推提升
        # -------------------------------------------------

        gain = result.get(
            "wave_top2_gain",
            0
        )

        print(
            "波色双推提升：",
            f"{gain:+.2%}"
        )


# =========================================================
# 主程序
# =========================================================

def main():

    print()

    print(
        "=" * 70
    )

    print(
        "六合彩AI智能预测系统 V1.3"
    )

    print(
        "工作流："
        "中文综合预测 → "
        "49码评分 → "
        "Top10 → "
        "下一期推荐 → "
        "波色双推 → "
        "Walk-Forward回测"
    )

    print(
        datetime.now().isoformat()
    )

    print(
        "=" * 70
    )

    # =====================================================
    # 步骤1：初始化数据库
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
    # 步骤2：同步在线数据
    # =====================================================

    print()

    print(
        "【步骤2】同步在线数据"
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
    # 预测
    # =====================================================

    predictions = {}

    backtests = {}

    analyzed_count = 0

    # =====================================================
    # 遍历彩种
    # =====================================================

    for lottery_key, config in LOTTERIES.items():

        lottery_name = config[
            "name"
        ]

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
        # 获取历史
        # -------------------------------------------------

        try:

            rows = get_draws(

                lottery_key,

                limit=3000
            )

        except Exception as e:

            print(
                f"❌ {lottery_name}"
                f"读取数据库失败：",
                repr(e)
            )

            continue

        print(
            f"历史数据：{len(rows)}期"
        )

        # -------------------------------------------------
        # 最少100期
        # -------------------------------------------------

        if len(rows) < 100:

            print(

                f"⚠️ {lottery_name}"
                f"历史数据不足100期，跳过。"
            )

            continue

        analyzed_count += 1

        # =================================================
        # 步骤3：生成下一期预测
        # =================================================

        print()

        print(
            "----------------------------------------------------------------------"
        )

        print(
            "【步骤3】生成下一期预测"
        )

        print(
            "----------------------------------------------------------------------"
        )

        try:

            prediction = generate_prediction(
                rows
            )

            predictions[
                lottery_key
            ] = {

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
        # 步骤4：Walk-Forward历史回测
        # =================================================

        print()

        print(
            "----------------------------------------------------------------------"
        )

        print(
            "【步骤4】Walk-Forward历史回测"
        )

        print(
            "----------------------------------------------------------------------"
        )

        try:

            backtest_result = (
                multi_window_backtest(
                    rows
                )
            )

            backtests[
                lottery_key
            ] = {

                "name":
                    lottery_name,

                "generated_at":
                    datetime.now().isoformat(),

                "results":
                    backtest_result,
            }

            print_backtest(

                lottery_name,

                backtest_result
            )

        except Exception as e:

            print()

            print(

                f"❌ {lottery_name}"
                f"回测失败：",

                repr(e)
            )

            backtests[
                lottery_key
            ] = {

                "name":
                    lottery_name,

                "generated_at":
                    datetime.now().isoformat(),

                "error":
                    repr(e),
            }

    # =====================================================
    # 步骤5：保存预测
    # =====================================================

    print()

    print(
        "----------------------------------------------------------------------"
    )

    print(
        "【步骤5】保存预测结果"
    )

    print(
        "----------------------------------------------------------------------"
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
            "❌ 预测结果保存失败：",
            repr(e)
        )

    # =====================================================
    # 步骤6：保存回测
    # =====================================================

    print()

    print(
        "----------------------------------------------------------------------"
    )

    print(
        "【步骤6】保存回测结果"
    )

    print(
        "----------------------------------------------------------------------"
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
            "❌ 回测结果保存失败：",
            repr(e)
        )

    # =====================================================
    # 完成
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
        f"分析彩种：{analyzed_count}"
    )

    print(
        f"本次新增数据：{inserted}"
    )

    print(
        "预测文件："
    )

    print(
        PREDICTION_FILE
    )

    print(
        "回测文件："
    )

    print(
        BACKTEST_FILE
    )

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
