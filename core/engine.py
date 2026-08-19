# -*- coding: utf-8 -*-

"""
六合彩 AI V3.6 FINAL
core/engine.py

功能：

1. API同步
2. 三彩种统一分析
3. 特码3码
4. 特码10码
5. 🔥 热号
6. ❄ 冷号
7. 📈 趋势
8. 🐉 特别生肖5个
9. 🌊 波色
10. 📊 大小
11. ⚖️ 单双
12. 🎯 推荐理由
13. JSON
14. TXT
15. HTML
"""

import json
import os
from datetime import datetime


# ============================================================
# 路径
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

JSON_FILE = os.path.join(
    OUTPUT_DIR,
    "prediction.json"
)

TXT_FILE = os.path.join(
    OUTPUT_DIR,
    "report.txt"
)

HTML_FILE = os.path.join(
    OUTPUT_DIR,
    "report.html"
)


# ============================================================
# 彩种
# ============================================================

LOTTERY_NAMES = {

    "hk":
        "香港六合彩",

    "newMacau":
        "新澳门六合彩",

    "oldMacau":
        "老澳门六合彩",

}


# ============================================================
# 安全转换
# ============================================================

def safe_int(value):

    try:
        return int(value)

    except (
        TypeError,
        ValueError,
    ):
        return None


# ============================================================
# 获取历史
# ============================================================

def get_history(
    database,
    lottery_code
):

    """
    兼容不同 database 实现。

    优先尝试：

    get_history(code)

    get_lottery_history(code)

    query_history(code)
    """

    methods = [

        "get_history",

        "get_lottery_history",

        "query_history",

    ]

    for method_name in methods:

        method = getattr(
            database,
            method_name,
            None
        )

        if not callable(method):

            continue

        try:

            result = method(
                lottery_code
            )

            if result is not None:

                return list(
                    result
                )

        except TypeError:

            try:

                result = method()

                if result is not None:

                    return list(
                        result
                    )

            except Exception:

                pass

        except Exception:

            pass

    return []


# ============================================================
# 兼容历史字段
# ============================================================

def normalize_history(
    history
):

    result = []

    for row in history:

        # ----------------------------------------------------
        # 已经是 dict
        # ----------------------------------------------------

        if isinstance(
            row,
            dict
        ):

            item = dict(
                row
            )

            # special
            if item.get(
                "special"
            ) is None:

                for key in (
                    "special_number",
                    "specialNumber",
                    "specialNum",
                    "special_num",
                ):

                    if item.get(key) is not None:

                        item["special"] = (
                            item[key]
                        )

                        break

            # issue
            if item.get(
                "issue"
            ) is None:

                for key in (
                    "expect",
                    "period",
                    "qihao",
                ):

                    if item.get(key) is not None:

                        item["issue"] = (
                            item[key]
                        )

                        break

            special = safe_int(
                item.get(
                    "special"
                )
            )

            if special is None:

                # 尝试从 numbers 提取
                numbers = item.get(
                    "numbers"
                )

                if isinstance(
                    numbers,
                    list
                ) and numbers:

                    try:

                        special = int(
                            numbers[-1]
                        )

                    except Exception:

                        special = None

            if special is None:

                continue

            item["special"] = (
                special
            )

            result.append(
                item
            )

            continue

        # ----------------------------------------------------
        # tuple / list
        # ----------------------------------------------------

        if isinstance(
            row,
            (list, tuple)
        ):

            if not row:

                continue

            item = {}

            # 常见：

            # issue
            # numbers
            # special

            if len(row) >= 1:

                item["issue"] = (
                    row[0]
                )

            if len(row) >= 2:

                value = row[1]

                if isinstance(
                    value,
                    (list, tuple)
                ):

                    numbers = [
                        safe_int(x)
                        for x in value
                    ]

                    numbers = [
                        x
                        for x in numbers
                        if x is not None
                    ]

                    if numbers:

                        item["numbers"] = (
                            numbers
                        )

                        item["special"] = (
                            numbers[-1]
                        )

                else:

                    value = safe_int(
                        value
                    )

                    if value is not None:

                        item["special"] = (
                            value
                        )

            if len(row) >= 3:

                value = safe_int(
                    row[-1]
                )

                if value is not None:

                    item["special"] = (
                        value
                    )

            if item.get(
                "special"
            ) is not None:

                result.append(
                    item
                )

    return result


# ============================================================
# 热号
# ============================================================

def calculate_hot_numbers(
    history
):

    numbers = []

    for row in history:

        try:

            value = int(
                row.get(
                    "special"
                )
            )

            if 1 <= value <= 49:

                numbers.append(
                    value
                )

        except Exception:

            continue

    if not numbers:

        return []

    # 最近50期
    recent = numbers[-50:]

    from collections import Counter

    counter = Counter(
        recent
    )

    return [
        number
        for number, count
        in counter.most_common(8)
    ]


# ============================================================
# 冷号
# ============================================================

def calculate_cold_numbers(
    history
):

    numbers = []

    for row in history:

        try:

            value = int(
                row.get(
                    "special"
                )
            )

            if 1 <= value <= 49:

                numbers.append(
                    value
                )

        except Exception:

            continue

    if not numbers:

        return []

    missing = {}

    for number in range(
        1,
        50
    ):

        count = 0

        for value in reversed(
            numbers
        ):

            if value == number:

                break

            count += 1

        missing[number] = count

    return [
        number
        for number, _ in sorted(
            missing.items(),
            key=lambda x: x[1],
            reverse=True
        )[:8]
    ]


# ============================================================
# 趋势
# ============================================================

def calculate_trend(
    history,
    prediction
):

    result = {}

    wave = prediction.get(
        "波色"
    )

    if isinstance(
        wave,
        dict
    ):

        result[
            "波色趋势"
        ] = wave.get(
            "推荐波色",
            "未知"
        )

    size = prediction.get(
        "大小"
    )

    if isinstance(
        size,
        dict
    ):

        result[
            "大小趋势"
        ] = size.get(
            "推荐",
            "未知"
        )

    odd_even = prediction.get(
        "单双"
    )

    if isinstance(
        odd_even,
        dict
    ):

        result[
            "单双趋势"
        ] = odd_even.get(
            "推荐",
            "未知"
        )

    return result


# ============================================================
# 推荐理由
# ============================================================

def build_reasons(
    history,
    prediction
):

    reasons = []

    count = len(
        history
    )

    if count >= 500:

        reasons.append(
            "历史数据充足"
        )

    elif count >= 100:

        reasons.append(
            "历史数据较充足"
        )

    else:

        reasons.append(
            "历史数据有限"
        )

    if prediction.get(
        "🔥热号"
    ):

        reasons.append(
            "近期热号参与评分"
        )

    if prediction.get(
        "❄冷号"
    ):

        reasons.append(
            "遗漏走势参与评分"
        )

    if prediction.get(
        "波色"
    ):

        reasons.append(
            "波色模型参与"
        )

    models = prediction.get(
        "模型状态",
        {}
    )

    if models.get(
        "Markov"
    ) == "启用":

        reasons.append(
            "Markov趋势参与"
        )

    if models.get(
        "HMM"
    ) == "启用":

        reasons.append(
            "HMM状态参与"
        )

    reasons.append(
        "综合评分排序"
    )

    return reasons


# ============================================================
# 整理特别生肖
# ============================================================

def normalize_zodiac(
    zodiac
):

    if not isinstance(
        zodiac,
        dict
    ):

        return {
            "特别生肖": [],
            "特别生肖Top5": [],
            "对应号码": {},
        }

    top5 = zodiac.get(
        "特别生肖Top5",
        []
    )

    simple = zodiac.get(
        "特别生肖",
        []
    )

    number_map = {}

    for item in top5:

        if not isinstance(
            item,
            dict
        ):

            continue

        name = item.get(
            "生肖"
        )

        numbers = item.get(
            "对应号码",
            []
        )

        if name:

            number_map[name] = (
                numbers
            )

    return {

        "特别生肖":
            simple[:5],

        "特别生肖Top5":
            top5[:5],

        "对应号码":
            number_map,

    }


# ============================================================
# 单个彩种分析
# ============================================================

def analyze_lottery(
    code,
    history,
    predictor
):

    name = LOTTERY_NAMES.get(
        code,
        code
    )

    print()
    print("=" * 60)
    print(
        f"分析: {name}"
    )
    print("=" * 60)

    history = normalize_history(
        history
    )

    print(
        f"历史数量: {len(history)}"
    )

    # --------------------------------------------------------
    # predictor
    # --------------------------------------------------------

    prediction = predictor(
        history
    )

    if not isinstance(
        prediction,
        dict
    ):

        prediction = {}

    # --------------------------------------------------------
    # 兼容旧字段
    # --------------------------------------------------------

    top3 = prediction.get(
        "🎯推荐3码"
    )

    if not top3:

        top3 = prediction.get(
            "重点3码",
            []
        )

    top10 = prediction.get(
        "⭐10码范围"
    )

    if not top10:

        top10 = prediction.get(
            "特码10码",
            []
        )

    hot = prediction.get(
        "🔥热号"
    )

    if hot is None:

        hot = calculate_hot_numbers(
            history
        )

    cold = prediction.get(
        "❄冷号"
    )

    if cold is None:

        cold = calculate_cold_numbers(
            history
        )

    # --------------------------------------------------------
    # 生肖
    # --------------------------------------------------------

    zodiac = normalize_zodiac(
        prediction.get(
            "🐉特别生肖",
            prediction.get(
                "特别生肖",
                {}
            )
        )
    )

    # --------------------------------------------------------
    # 趋势
    # --------------------------------------------------------

    trend = prediction.get(
        "📈趋势"
    )

    if not isinstance(
        trend,
        dict
    ):

        trend = calculate_trend(
            history,
            prediction
        )

    # --------------------------------------------------------
    # 推荐理由
    # --------------------------------------------------------

    reasons = prediction.get(
        "🎯推荐理由"
    )

    if not reasons:

        reasons = build_reasons(
            history,
            prediction
        )

    # --------------------------------------------------------
    # 最终结构
    # --------------------------------------------------------

    result = {

        "模型版本":
            "V3.6 FINAL",

        "彩种":
            name,

        "代码":
            code,

        "历史数量":
            len(history),

        "🎯推荐3码":
            top3,

        "⭐10码范围":
            top10,

        "🔥热号":
            hot,

        "❄冷号":
            cold,

        "📈趋势":
            trend,

        "🐉特别生肖":
            zodiac,

        "波色":
            prediction.get(
                "波色",
                {}
            ),

        "大小":
            prediction.get(
                "大小",
                {}
            ),

        "单双":
            prediction.get(
                "单双",
                {}
            ),

        "第一推荐":
            prediction.get(
                "第一推荐",
                top3[0]
                if top3
                else None
            ),

        "置信度":
            prediction.get(
                "置信度",
                0
            ),

        "风险等级":
            prediction.get(
                "风险等级",
                "高风险"
            ),

        "🎯推荐理由":
            reasons,

        "模型状态":
            prediction.get(
                "模型状态",
                {}
            ),

        "当前状态":
            prediction.get(
                "当前状态",
                {}
            ),

        "评分":
            prediction.get(
                "评分",
                {}
            ),

    }

    return result


# ============================================================
# 控制台显示
# ============================================================

def print_prediction(
    result
):

    print()
    print(
        "🎲 " +
        result.get(
            "彩种",
            "未知"
        )
    )

    print("-" * 60)

    # --------------------------------------------------------
    # 推荐
    # --------------------------------------------------------

    print(
        "🎯 推荐3码:",
        result.get(
            "🎯推荐3码",
            []
        )
    )

    print(
        "⭐ 10码:",
        result.get(
            "⭐10码范围",
            []
        )
    )

    print()

    # --------------------------------------------------------
    # 热冷
    # --------------------------------------------------------

    print(
        "🔥 热号:",
        result.get(
            "🔥热号",
            []
        )
    )

    print(
        "❄ 冷号:",
        result.get(
            "❄冷号",
            []
        )
    )

    print()

    # --------------------------------------------------------
    # 趋势
    # --------------------------------------------------------

    print(
        "📈 趋势:"
    )

    trend = result.get(
        "📈趋势",
        {}
    )

    if isinstance(
        trend,
        dict
    ):

        for key, value in trend.items():

            print(
                f"   {key}: {value}"
            )

    # --------------------------------------------------------
    # 特别生肖
    # --------------------------------------------------------

    print()
    print(
        "🐉 特别生肖:"
    )

    zodiac = result.get(
        "🐉特别生肖",
        {}
    )

    top5 = zodiac.get(
        "特别生肖Top5",
        []
    )

    if top5:

        for item in top5:

            if not isinstance(
                item,
                dict
            ):

                continue

            rank = item.get(
                "排名",
                ""
            )

            name = item.get(
                "生肖",
                "未知"
            )

            numbers = item.get(
                "对应号码",
                []
            )

            score = item.get(
                "评分",
                0
            )

            print(
                f"   {rank}. {name}"
                f" 号码:{numbers}"
                f" 评分:{score}"
            )

    else:

        print(
            "   暂无"
        )

    # --------------------------------------------------------
    # 波色
    # --------------------------------------------------------

    wave = result.get(
        "波色",
        {}
    )

    if isinstance(
        wave,
        dict
    ):

        print()
        print(
            "🌊 波色:",
            wave.get(
                "推荐波色",
                "未知"
            ),
            "(",
            wave.get(
                "概率",
                0
            ),
            ")"
        )

    # --------------------------------------------------------
    # 大小
    # --------------------------------------------------------

    size = result.get(
        "大小",
        {}
    )

    if isinstance(
        size,
        dict
    ):

        print(
            "📊 大小:",
            size.get(
                "推荐",
                "未知"
            )
        )

    # --------------------------------------------------------
    # 单双
    # --------------------------------------------------------

    odd_even = result.get(
        "单双",
        {}
    )

    if isinstance(
        odd_even,
        dict
    ):

        print(
            "⚖️ 单双:",
            odd_even.get(
                "推荐",
                "未知"
            )
        )

    # --------------------------------------------------------
    # 置信度
    # --------------------------------------------------------

    print(
        "📊 置信度:",
        result.get(
            "置信度",
            0
        )
    )

    print(
        "⚠️ 风险:",
        result.get(
            "风险等级",
            "高风险"
        )
    )

    # --------------------------------------------------------
    # 推荐理由
    # --------------------------------------------------------

    print()
    print(
        "🎯 推荐理由:"
    )

    for reason in result.get(
        "🎯推荐理由",
        []
    ):

        print(
            f"   - {reason}"
        )


# ============================================================
# TXT报告
# ============================================================

def build_txt(
    results
):

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    lines = []

    lines.append(
        "=============================================="
    )

    lines.append(
        "🔥 六合AI智能预测报告"
    )

    lines.append(
        f"时间: {now}"
    )

    lines.append(
        "=============================================="
    )

    for result in results.values():

        lines.append("")

        lines.append(
            f"🎲 {result['彩种']}"
        )

        lines.append(
            "----------------------------------------------"
        )

        lines.append(
            "🎯 推荐3码: "
            + str(
                result["🎯推荐3码"]
            )
        )

        lines.append(
            "⭐ 10码: "
            + str(
                result["⭐10码范围"]
            )
        )

        lines.append(
            "🔥 热号: "
            + str(
                result["🔥热号"]
            )
        )

        lines.append(
            "❄ 冷号: "
            + str(
                result["❄冷号"]
            )
        )

        lines.append(
            "📈 趋势:"
        )

        for key, value in result[
            "📈趋势"
        ].items():

            lines.append(
                f"   {key}: {value}"
            )

        lines.append(
            "🐉 特别生肖:"
        )

        zodiac = result[
            "🐉特别生肖"
        ]

        for item in zodiac.get(
            "特别生肖Top5",
            []
        ):

            lines.append(
                f"   {item.get('排名')}. "
                f"{item.get('生肖')} "
                f"号码:{item.get('对应号码')}"
            )

        lines.append(
            "🌊 波色: "
            + str(
                result[
                    "波色"
                ].get(
                    "推荐波色",
                    "未知"
                )
            )
        )

        lines.append(
            "📊 大小: "
            + str(
                result[
                    "大小"
                ].get(
                    "推荐",
                    "未知"
                )
            )
        )

        lines.append(
            "⚖️ 单双: "
            + str(
                result[
                    "单双"
                ].get(
                    "推荐",
                    "未知"
                )
            )
        )

        lines.append(
            "📊 置信度: "
            + str(
                result[
                    "置信度"
                ]
            )
        )

        lines.append(
            "⚠️ 风险: "
            + str(
                result[
                    "风险等级"
                ]
            )
        )

        lines.append(
            "🎯 推荐理由:"
        )

        for reason in result[
            "🎯推荐理由"
        ]:

            lines.append(
                f"   - {reason}"
            )

    lines.append("")

    lines.append(
        "=============================================="
    )

    return "\n".join(
        lines
    )


# ============================================================
# HTML报告
# ============================================================

def build_html(
    results
):

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    html = []

    html.append(
        "<!DOCTYPE html>"
    )

    html.append(
        "<html lang='zh-CN'>"
    )

    html.append(
        "<head>"
    )

    html.append(
        "<meta charset='UTF-8'>"
    )

    html.append(
        "<meta name='viewport' "
        "content='width=device-width,initial-scale=1'>"
    )

    html.append(
        "<title>六合彩 AI 智能预测</title>"
    )

    html.append(
        "<style>"
    )

    html.append(
        """
        body{
            font-family:Arial,
            "Microsoft YaHei",
            sans-serif;
            margin:0;
            padding:20px;
            background:#f5f5f5;
        }

        .container{
            max-width:1000px;
            margin:auto;
        }

        .title{
            font-size:28px;
            font-weight:bold;
            margin-bottom:8px;
        }

        .time{
            color:#666;
            margin-bottom:20px;
        }

        .card{
            background:white;
            border-radius:12px;
            padding:20px;
            margin-bottom:20px;
            box-shadow:
                0 2px 8px
                rgba(0,0,0,.08);
        }

        .number{
            display:inline-block;
            padding:8px 12px;
            margin:4px;
            border-radius:8px;
            background:#eee;
            font-weight:bold;
        }

        .recommend{
            font-size:24px;
            font-weight:bold;
        }

        .section{
            margin-top:15px;
            font-weight:bold;
        }

        ul{
            line-height:1.8;
        }
        """
    )

    html.append(
        "</style>"
    )

    html.append(
        "</head>"
    )

    html.append(
        "<body>"
    )

    html.append(
        "<div class='container'>"
    )

    html.append(
        "<div class='title'>🔥 "
        "六合彩 AI 智能预测</div>"
    )

    html.append(
        f"<div class='time'>{now}</div>"
    )

    for result in results.values():

        html.append(
            "<div class='card'>"
        )

        html.append(
            f"<h2>🎲 "
            f"{result['彩种']}</h2>"
        )

        html.append(
            "<div class='recommend'>"
            "🎯 推荐3码: "
        )

        for number in result[
            "🎯推荐3码"
        ]:

            html.append(
                f"<span class='number'>"
                f"{number:02d}</span>"
            )

        html.append(
            "</div>"
        )

        html.append(
            "<div class='section'>⭐ 10码</div>"
        )

        html.append(
            str(
                result[
                    "⭐10码范围"
                ]
            )
        )

        html.append(
            "<div class='section'>🔥 热号</div>"
        )

        html.append(
            str(
                result[
                    "🔥热号"
                ]
            )
        )

        html.append(
            "<div class='section'>❄ 冷号</div>"
        )

        html.append(
            str(
                result[
                    "❄冷号"
                ]
            )
        )

        html.append(
            "<div class='section'>📈 趋势</div>"
        )

        for key, value in result[
            "📈趋势"
        ].items():

            html.append(
                f"<div>{key}: "
                f"{value}</div>"
            )

        html.append(
            "<div class='section'>"
            "🐉 特别生肖"
            "</div>"
        )

        for item in result[
            "🐉特别生肖"
        ].get(
            "特别生肖Top5",
            []
        ):

            html.append(
                f"<div>"
                f"{item.get('排名')}. "
                f"{item.get('生肖')} "
                f"— "
                f"{item.get('对应号码')}"
                f"</div>"
            )

        html.append(
            "<div class='section'>🎯 推荐理由</div>"
        )

        html.append(
            "<ul>"
        )

        for reason in result[
            "🎯推荐理由"
        ]:

            html.append(
                f"<li>{reason}</li>"
            )

        html.append(
            "</ul>"
        )

        html.append(
            f"<div>🌊 波色: "
            f"{result['波色'].get('推荐波色','未知')}"
            f"</div>"
        )

        html.append(
            f"<div>📊 大小: "
            f"{result['大小'].get('推荐','未知')}"
            f"</div>"
        )

        html.append(
            f"<div>⚖️ 单双: "
            f"{result['单双'].get('推荐','未知')}"
            f"</div>"
        )

        html.append(
            f"<div>📊 置信度: "
            f"{result['置信度']}"
            f"</div>"
        )

        html.append(
            f"<div>⚠️ 风险: "
            f"{result['风险等级']}"
            f"</div>"
        )

        html.append(
            "</div>"
        )

    html.append(
        "</div>"
    )

    html.append(
        "</body>"
    )

    html.append(
        "</html>"
    )

    return "\n".join(
        html
    )


# ============================================================
# Engine主入口
# ============================================================

def run_engine(
    database,
    predictor,
    sync_result=None
):

    print()
    print("=" * 60)
    print(
        "🔥 六合AI V3.6 FINAL"
    )
    print(
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    print("=" * 60)

    results = {}

    # ========================================================
    # 三彩种
    # ========================================================

    for code in (
        "hk",
        "newMacau",
        "oldMacau",
    ):

        history = get_history(
            database,
            code
        )

        result = analyze_lottery(
            code,
            history,
            predictor
        )

        results[code] = result

        # ====================================================
        # 直接显示预测
        # ====================================================

        print_prediction(
            result
        )

    # ========================================================
    # JSON
    # ========================================================

    output = {

        "版本":
            "V3.6 FINAL",

        "系统":
            "六合彩 AI V3.6 FINAL",

        "时间":
            datetime.now().isoformat(),

        "同步":
            sync_result,

        "预测":
            results,

    }

    with open(
        JSON_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ========================================================
    # TXT
    # ========================================================

    txt = build_txt(
        results
    )

    with open(
        TXT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            txt
        )

    # ========================================================
    # HTML
    # ========================================================

    html = build_html(
        results
    )

    with open(
        HTML_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            html
        )

    # ========================================================
    # 文件
    # ========================================================

    print()
    print("=" * 60)

    print(
        f"JSON输出: {JSON_FILE}"
    )

    print(
        f"文字报告: {TXT_FILE}"
    )

    print(
        f"网页报告: {HTML_FILE}"
    )

    print("=" * 60)

    return output


# ============================================================
# 兼容旧调用
# ============================================================

def generate_report(
    results
):

    txt = build_txt(
        results
    )

    with open(
        TXT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            txt
        )

    html = build_html(
        results
    )

    with open(
        HTML_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            html
        )

    return {
        "json": JSON_FILE,
        "txt": TXT_FILE,
        "html": HTML_FILE,
    }


__all__ = [
    "run_engine",
    "analyze_lottery",
    "print_prediction",
    "generate_report",
]
