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
# 打印预测
# =========================================================

def print_prediction(
    lottery_key,
    lottery_name,
    prediction
):

    print()
    print(
        "=" * 60
    )

    print(
        f"{lottery_name} ({lottery_key})"
    )

    print(
        "=" * 60
    )

    # -----------------------------------------------------
    # 特码10码
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 特码生肖5肖
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 平特生肖2肖
    # -----------------------------------------------------

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
        f"{size.get('probability', '-')}"
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
        f"{parity.get('probability', '-')}"
    )

    # -----------------------------------------------------
    # 波色
    # -----------------------------------------------------

    wave = prediction.get(
        "wave",
        {}
    )

    print(
        "【波色】"
        f"{wave.get('prediction', '-')}"
        f" "
        f"{wave.get('probability', '-')}"
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


# =========================================================
# 主程序
# =========================================================

def main():

    print()

    print(
        "=" * 60
    )

    print(
        "六合彩综合预测系统 V1.1"
    )

    print(
        datetime.now().isoformat()
    )

    print(
        "=" * 60
    )

    # =====================================================
    # 1. 初始化数据库
    # =====================================================

    init_database()

    # =====================================================
    # 2. 更新数据
    # =====================================================

    print()

    print(
        "正在更新在线数据..."
    )

    try:

        inserted = update_all()

        print()

        print(
            f"本次新增数据：{inserted}"
        )

    except Exception as e:

        print()

        print(
            "❌ 数据更新出现异常：",
            repr(e)
        )

    # =====================================================
    # 3. 预测
    # =====================================================

    predictions = {}

    backtests = {}

    for lottery_key, config in LOTTERIES.items():

        lottery_name = config["name"]

        print()

        print(
            "=" * 60
        )

        print(
            f"正在分析：{lottery_name}"
        )

        print(
            "=" * 60
        )

        # -------------------------------------------------
        # 获取历史
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
                f"{lottery_name}"
                " 历史数据不足100期，跳过。"
            )

            continue

        # =================================================
        # 当前预测
        # =================================================

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
            f"正在回测：{lottery_name}"
        )

        try:

            backtest_result = (
                multi_window_backtest(rows)
            )

            backtests[lottery_key] = {

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
    # 4. 保存预测
    # =====================================================

    save_json(
        PREDICTION_FILE,
        predictions
    )

    # =====================================================
    # 5. 保存回测
    # =====================================================

    save_json(
        BACKTEST_FILE,
        backtests
    )

    # =====================================================
    # 6. 完成
    # =====================================================

    print()

    print(
        "=" * 60
    )

    print(
        "运行完成"
    )

    print(
        f"预测文件：{PREDICTION_FILE}"
    )

    print(
        f"回测文件：{BACKTEST_FILE}"
    )

    print(
        "=" * 60
    )


# =========================================================
# Entry
# =========================================================

if __name__ == "__main__":

    main()
