# -*- coding: utf-8 -*-

"""
六合彩 AI V3.0
数据质量检查
"""

from typing import Dict, List


VALID_NUMBERS = set(
    range(1, 50)
)


# =========================================================
# 单行检查
# =========================================================

def validate_row(row) -> Dict:

    errors = []

    warnings = []


    if not isinstance(
        row,
        dict
    ):

        return {

            "valid": False,

            "errors":
                ["row不是dict"],

            "warnings":
                [],

        }


    issue = row.get(
        "issue"
    )


    if issue is None:

        errors.append(
            "缺少issue"
        )


    numbers = row.get(
        "numbers"
    )


    # -----------------------------------------------------
    # numbers
    # -----------------------------------------------------

    if isinstance(
        numbers,
        str
    ):

        text = (
            numbers
            .replace(
                "，",
                ","
            )
            .strip()
        )

        parts = [
            x.strip()
            for x in text.split(",")
            if x.strip()
        ]


        parsed = []

        for item in parts:

            try:

                parsed.append(
                    int(item)
                )

            except Exception:

                errors.append(
                    f"号码无法解析:{item}"
                )


    elif isinstance(
        numbers,
        (list, tuple)
    ):

        parsed = []

        for item in numbers:

            try:

                parsed.append(
                    int(item)
                )

            except Exception:

                errors.append(
                    f"号码无法解析:{item}"
                )

    else:

        parsed = []


        if numbers is not None:

            errors.append(
                "numbers类型错误"
            )


    # -----------------------------------------------------
    # 数量
    # -----------------------------------------------------

    if len(parsed) != 7:

        errors.append(
            f"号码数量异常:{len(parsed)}"
        )


    # -----------------------------------------------------
    # 范围
    # -----------------------------------------------------

    invalid = [

        n

        for n in parsed

        if n not in VALID_NUMBERS

    ]


    if invalid:

        errors.append(
            f"号码超范围:{invalid}"
        )


    # -----------------------------------------------------
    # 重复
    # -----------------------------------------------------

    if len(parsed) == 7:

        if len(set(parsed)) != 7:

            errors.append(
                "开奖号码存在重复"
            )


    # -----------------------------------------------------
    # 特码
    # -----------------------------------------------------

    if len(parsed) >= 7:

        special = parsed[6]

        if special not in VALID_NUMBERS:

            errors.append(
                "特码非法"
            )


    # -----------------------------------------------------
    # issue
    # -----------------------------------------------------

    if issue is not None:

        issue_text = str(
            issue
        ).strip()


        if not issue_text:

            errors.append(
                "issue为空"
            )


    # -----------------------------------------------------
    # warning
    # -----------------------------------------------------

    if (
        len(parsed) == 7
        and parsed == sorted(parsed)
    ):

        warnings.append(
            "开奖号码已经排序，"
            "请确认数据源是否改变了原始顺序"
        )


    return {

        "valid":
            len(errors) == 0,

        "errors":
            errors,

        "warnings":
            warnings,

    }


# =========================================================
# 全部检查
# =========================================================

def validate_history(
    rows
):

    valid_rows = []

    invalid_rows = []

    all_warnings = []


    for index, row in enumerate(
        rows
    ):

        result = validate_row(
            row
        )


        if result["valid"]:

            valid_rows.append(
                row
            )

        else:

            invalid_rows.append({

                "index":
                    index,

                "issue":
                    row.get(
                        "issue"
                    )
                    if isinstance(
                        row,
                        dict
                    )
                    else None,

                "errors":
                    result["errors"],

            })


        if result["warnings"]:

            all_warnings.extend(
                result["warnings"]
            )


    return {

        "valid":
            len(valid_rows),

        "invalid":
            len(invalid_rows),

        "warnings":
            len(all_warnings),

        "valid_rows":
            valid_rows,

        "invalid_rows":
            invalid_rows,

    }


# =========================================================
# 去重
# =========================================================

def deduplicate_history(
    rows
):

    seen = set()

    result = []


    for row in rows:

        if not isinstance(
            row,
            dict
        ):
            continue


        issue = str(
            row.get(
                "issue",
                ""
            )
        ).strip()


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
# 数据清洗
# =========================================================

def clean_history(
    rows
):

    rows = deduplicate_history(
        rows
    )


    quality = validate_history(
        rows
    )


    valid_rows = quality[
        "valid_rows"
    ]


    # 保持最新 -> 最旧
    #
    # 如果 issue 是纯数字，
    # 按期号倒序。

    try:

        valid_rows.sort(

            key=lambda row:
                int(
                    str(
                        row.get(
                            "issue"
                        )
                    )
                ),

            reverse=True

        )

    except Exception:

        pass


    return valid_rows, quality