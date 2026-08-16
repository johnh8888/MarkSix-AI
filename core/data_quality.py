# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
数据质量检查
"""

from typing import Any, Dict, List

from core.features import (
    get_special,
    parse_numbers,
)


# =========================================================
# 单条数据检查
# =========================================================

def validate_row(
    row: Dict[str, Any]
) -> Dict[str, Any]:

    errors = []

    warnings = []

    # -----------------------------------------------------
    # 期号
    # -----------------------------------------------------

    issue = row.get(
        "issue"
    )

    if issue is None:
        errors.append(
            "缺少期号"
        )

    # -----------------------------------------------------
    # 号码
    # -----------------------------------------------------

    numbers = parse_numbers(
        row
    )

    if len(numbers) != 7:

        errors.append(
            f"号码数量异常：{len(numbers)}"
        )

    # -----------------------------------------------------
    # 范围
    # -----------------------------------------------------

    for n in numbers:

        if not 1 <= n <= 49:

            errors.append(
                f"号码超出范围：{n}"
            )

    # -----------------------------------------------------
    # 重复号码
    # -----------------------------------------------------

    if len(numbers) != len(
        set(numbers)
    ):

        errors.append(
            "开奖号码存在重复"
        )

    # -----------------------------------------------------
    # 特码
    # -----------------------------------------------------

    special = get_special(
        row
    )

    if not 1 <= special <= 49:

        errors.append(
            "特码无效"
        )

    # -----------------------------------------------------
    # 号码不足
    # -----------------------------------------------------

    if len(numbers) < 7:

        warnings.append(
            "开奖号码不足7个"
        )

    return {

        "valid":
            len(errors) == 0,

        "errors":
            errors,

        "warnings":
            warnings,

        "issue":
            issue,

        "special":
            special,
    }


# =========================================================
# 批量检查
# =========================================================

def validate_rows(
    rows: List[Dict[str, Any]]
):

    valid_rows = []

    invalid_rows = []

    warning_count = 0

    for row in rows:

        result = validate_row(
            row
        )

        if result["valid"]:

            valid_rows.append(
                row
            )

        else:

            invalid_rows.append({

                "row":
                    row,

                "errors":
                    result["errors"],

                "warnings":
                    result["warnings"],
            })

        warning_count += len(
            result["warnings"]
        )

    return {

        "total":
            len(rows),

        "valid":
            len(valid_rows),

        "invalid":
            len(invalid_rows),

        "warnings":
            warning_count,

        "valid_rows":
            valid_rows,

        "invalid_rows":
            invalid_rows,
    }


# =========================================================
# 去重
# =========================================================

def remove_duplicate_issues(
    rows
):

    seen = set()

    result = []

    for row in rows:

        issue = str(
            row.get(
                "issue",
                ""
            )
        )

        if not issue:
            continue

        if issue in seen:
            continue

        seen.add(issue)

        result.append(
            row
        )

    return result


# =========================================================
# 最终清洗
# =========================================================

def clean_history(
    rows
):

    rows = remove_duplicate_issues(
        rows
    )

    result = validate_rows(
        rows
    )

    return result[
        "valid_rows"
    ]