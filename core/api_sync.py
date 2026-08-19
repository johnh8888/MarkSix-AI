# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import ssl
import urllib.request


URL = "https://marksix6.net/index.php?api=1"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}


CTX = ssl._create_unverified_context()


def get_raw():

    request = urllib.request.Request(
        URL,
        headers=HEADERS,
        method="GET",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:

            raw = response.read()

    except Exception as exc:

        print("第一次请求失败：", repr(exc))
        print("尝试SSL兼容模式...")

        with urllib.request.urlopen(
            request,
            timeout=30,
            context=CTX,
        ) as response:

            raw = response.read()

    return raw


def print_structure(
    obj,
    path="ROOT",
    depth=0,
    max_depth=8,
):

    indent = "  " * depth

    if depth > max_depth:
        print(
            indent +
            f"{path}: <超过最大深度>"
        )
        return

    if isinstance(obj, dict):

        print(
            indent +
            f"{path}: DICT "
            f"({len(obj)} keys)"
        )

        for key, value in obj.items():

            key_path = (
                f"{path}.{key}"
            )

            if isinstance(
                value,
                (dict, list),
            ):

                print_structure(
                    value,
                    key_path,
                    depth + 1,
                    max_depth,
                )

            else:

                text = repr(value)

                if len(text) > 300:
                    text = (
                        text[:300]
                        + "..."
                    )

                print(
                    "  " * (depth + 1)
                    + f"{key_path} = "
                    + text
                )

    elif isinstance(obj, list):

        print(
            indent +
            f"{path}: LIST "
            f"({len(obj)} items)"
        )

        # 只打印前3个
        for i, value in enumerate(
            obj[:3]
        ):

            print_structure(
                value,
                f"{path}[{i}]",
                depth + 1,
                max_depth,
            )

        if len(obj) > 3:

            print(
                "  " * (depth + 1)
                + f"...还有 "
                f"{len(obj) - 3} 项"
            )

    else:

        text = repr(obj)

        if len(text) > 300:
            text = (
                text[:300]
                + "..."
            )

        print(
            indent +
            f"{path} = {text}"
        )


def main():

    print("=" * 80)
    print("六合彩 API 原始数据诊断")
    print("=" * 80)

    print()
    print("请求：")
    print(URL)

    print()
    print("正在获取原始数据...")

    raw = get_raw()

    print()
    print(
        "原始字节数：",
        len(raw),
    )

    text = raw.decode(
        "utf-8",
        errors="replace",
    ).strip()

    text = text.lstrip(
        "\ufeff"
    )

    print()
    print("=" * 80)
    print("原始文本前5000字符")
    print("=" * 80)

    print(
        text[:5000]
    )

    print()
    print("=" * 80)
    print("开始解析JSON")
    print("=" * 80)

    try:

        data = json.loads(
            text
        )

    except Exception as exc:

        print(
            "JSON解析失败：",
            repr(exc),
        )

        return

    print(
        "JSON解析成功"
    )

    print()
    print("=" * 80)
    print("JSON结构")
    print("=" * 80)

    print_structure(
        data
    )

    print()
    print("=" * 80)
    print("诊断结束")
    print("=" * 80)


if __name__ == "__main__":

    main()
