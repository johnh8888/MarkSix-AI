def get_special(row):
    """
    获取特码。

    兼容以下数据结构：

    1. row["special"]
    2. row["special_number"]
    3. row["numbers"] 为列表
    4. row["numbers"] 为逗号分隔字符串
    5. row["openCode"] 为逗号分隔字符串

    香港六合彩 / 澳门六合彩：
    最后一个号码作为特码。
    """

    # -----------------------------------------
    # 1. 直接存在 special
    # -----------------------------------------

    value = row.get("special")

    if value not in (None, ""):

        try:
            return int(value)
        except (TypeError, ValueError):
            pass

    # -----------------------------------------
    # 2. special_number
    # -----------------------------------------

    value = row.get("special_number")

    if value not in (None, ""):

        try:
            return int(value)
        except (TypeError, ValueError):
            pass

    # -----------------------------------------
    # 3. numbers
    # -----------------------------------------

    numbers = row.get("numbers")

    if numbers:

        if isinstance(numbers, str):

            parts = [
                x.strip()
                for x in numbers.split(",")
                if x.strip()
            ]

        elif isinstance(numbers, (list, tuple)):

            parts = list(numbers)

        else:

            parts = []

        if parts:

            try:
                return int(parts[-1])
            except (TypeError, ValueError):
                pass

    # -----------------------------------------
    # 4. openCode
    # -----------------------------------------

    open_code = row.get("openCode")

    if open_code:

        if isinstance(open_code, str):

            parts = [
                x.strip()
                for x in open_code.split(",")
                if x.strip()
            ]

        elif isinstance(open_code, (list, tuple)):

            parts = list(open_code)

        else:

            parts = []

        if parts:

            try:
                return int(parts[-1])
            except (TypeError, ValueError):
                pass

    # -----------------------------------------
    # 5. 无法解析
    # -----------------------------------------

    raise ValueError(
        f"无法获取特码，数据库记录字段："
        f"{list(row.keys())}"
    )
