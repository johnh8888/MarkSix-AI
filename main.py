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


def save_json(path, data):

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


def print_prediction(
    lottery_key,
    lottery_name,
    prediction
):

    print()
    print("=" * 60)

    print(
        f"{lottery_name} "
        f"({lottery_key})"
    )

    print("=" * 60)

    # -----------------------------------------
    # 特码10码
    # -----------------------------------------

    numbers = prediction.get(
        "top10_numbers",
        []
    )

    print()

    print("【特码10码】")

    print(
        " ".join(
            f"{item['number']:02d}"
            for item in numbers
        )
    )

    # -----------------------------------------
    # 特码生肖5肖
    # -----------------------------------------

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

    # -----------------------------------------
    # 平特生肖2肖
    # -----------------------------------------

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

    # -----------------------------------------
    # 大小
    # -----------------------------------------

    size = prediction["size"]

    print()

    print(
        f"【大小】"
        f"{size['prediction']} "
        f"{size['probability']}"
    )

    # -----------------------------------------
    # 单双
    # -----------------------------------------

    parity = prediction["parity"]

    print(
        f"【单双】"
        f"{parity['prediction']} "
        f"{parity['probability']}"
    )

    # -----------------------------------------
    # 波色
    # -----------------------------------------

    wave = prediction["wave"]

    print(
        f"【波色】"
        f"{wave['prediction']} "
        f"{wave['probability']}"
    )


def main():

    print()
    print("=" * 60)

    print(
        "六合彩综合预测系统 V1.0"
    )

    print(
        datetime.now().isoformat()
    )

    print("=" * 60)

    # -----------------------------------------
    # 1. 初始化数据库
    # -----------------------------------------

    init_database()

    # -----------------------------------------
    # 2. 自动更新三个彩种
    # -----------------------------------------

    print()
    print("正在更新在线数据...")

    try:

        inserted = update_all()

        print(
            f"本次新增数据：{inserted}"
        )

    except Exception as e:

        print(
            "数据更新出现异常：",
            e
        )

    # -----------------------------------------
    # 3. 分别预测
    # -----------------------------------------

    predictions = {}

    backtests = {}

    for lottery_key, config in LOTTERIES.items():

        lottery_name = config["name"]

        print()
        print(
            f"正在分析：{lottery_name}"
        )

        rows = get_draws(
            lottery_key,
            limit=3000
        )

        print(
            f"历史数据：{len(rows)}期"
        )

        if len(rows) < 100:

            print(
                f"{lottery_name} "
                f"历史数据不足100期，跳过。"
            )

            continue

        # -------------------------------------
        # 当前预测
        # -------------------------------------

        prediction = generate_prediction(
            rows
        )

        predictions[lottery_key] = {
            "name": lottery_name,
            "generated_at":
                datetime.now().isoformat(),
            "history_count":
                len(rows),
            "prediction":
                prediction
        }

        print_prediction(
            lottery_key,
            lottery_name,
            prediction
        )

        # -------------------------------------
        # 回测
        # -------------------------------------

        print()
        print(
            f"正在回测：{lottery_name}"
        )

        backtest_result = (
            multi_window_backtest(rows)
        )

        backtests[lottery_key] = {
            "name": lottery_name,
            "generated_at":
                datetime.now().isoformat(),
            "results":
                backtest_result
        }

    # -----------------------------------------
    # 4. 保存预测
    # -----------------------------------------

    save_json(
        PREDICTION_FILE,
        predictions
    )

    # -----------------------------------------
    # 5. 保存回测
    # -----------------------------------------

    save_json(
        BACKTEST_FILE,
        backtests
    )

    print()
    print("=" * 60)

    print(
        "运行完成"
    )

    print(
        f"预测文件："
        f"{PREDICTION_FILE}"
    )

    print(
        f"回测文件："
        f"{BACKTEST_FILE}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
