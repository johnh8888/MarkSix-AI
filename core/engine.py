# core/engine.py
# -*- coding: utf-8 -*-

"""
MarkSix-AI
核心运行引擎
兼容 main.py:
    from core.engine import run_system

作用：
1. 统一调用数据同步
2. 统一执行三彩种分析
3. 尽量兼容旧版模块
4. 即使部分高级模型不存在，也不会因为导入失败直接退出
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# 基础工具
# ============================================================

def _log(message: str = "") -> None:
    print(message, flush=True)


def _safe_import(module_name: str):
    """
    安全导入模块。
    某个高级模块不存在时，不让整个系统直接崩溃。
    """
    try:
        return __import__(module_name, fromlist=["*"])
    except Exception as exc:
        _log(f"[WARN] 模块 {module_name} 导入失败：{exc}")
        return None


def _call_if_exists(
    module: Any,
    function_names: List[str],
    *args,
    **kwargs
) -> Any:
    """
    在模块中寻找可用函数并调用。
    """
    if module is None:
        return None

    for name in function_names:
        func = getattr(module, name, None)

        if callable(func):
            try:
                return func(*args, **kwargs)
            except TypeError:
                # 参数不兼容时尝试无参数调用
                try:
                    return func()
                except Exception as exc:
                    _log(
                        f"[WARN] 调用 {name}() 失败：{exc}"
                    )
            except Exception as exc:
                _log(
                    f"[WARN] 调用 {name}() 失败：{exc}"
                )

    return None


# ============================================================
# 数据库 / 数据同步
# ============================================================

def sync_data() -> Any:
    """
    尝试调用项目中现有的数据同步模块。

    兼容：
        core.data
        core.sync
        data
        sync
    """

    candidates = [
        "core.sync",
        "core.data",
        "core.data_sync",
        "sync",
        "data",
    ]

    functions = [
        "sync_all",
        "sync_data",
        "update_all",
        "update_data",
        "fetch_and_save",
        "fetch_online",
        "run_sync",
    ]

    for module_name in candidates:
        module = _safe_import(module_name)

        if module is None:
            continue

        result = _call_if_exists(
            module,
            functions,
        )

        if result is not None:
            return result

    _log("[INFO] 未找到独立数据同步函数，继续使用已有数据。")
    return None


# ============================================================
# 单彩种分析
# ============================================================

def analyze_lottery(
    lottery_name: str,
    data: Any = None,
) -> Dict[str, Any]:
    """
    单个彩种分析。

    尽量兼容项目中已有的分析模块。
    """

    result: Dict[str, Any] = {
        "lottery": lottery_name,
        "time": datetime.now().isoformat(),
        "success": False,
    }

    module_candidates = [
        "core.predictor",
        "core.prediction",
        "core.analyzer",
        "core.analysis",
        "core.model",
        "core.models",
        "predictor",
        "prediction",
        "analyzer",
        "analysis",
    ]

    function_candidates = [
        "predict",
        "predict_next",
        "predict_lottery",
        "run_prediction",
        "analyze",
        "analyze_lottery",
        "run_analysis",
    ]

    for module_name in module_candidates:

        module = _safe_import(module_name)

        if module is None:
            continue

        # ----------------------------------------------------
        # 第一种：带 lottery_name + data
        # ----------------------------------------------------

        for function_name in function_candidates:

            func = getattr(module, function_name, None)

            if not callable(func):
                continue

            attempts = [
                (lottery_name, data),
                (lottery_name,),
                (data,),
                (),
            ]

            for args in attempts:

                try:
                    value = func(*args)

                    if value is not None:
                        result["success"] = True
                        result["result"] = value
                        return result

                except TypeError:
                    continue

                except Exception as exc:
                    _log(
                        f"[WARN] {module_name}.{function_name} "
                        f"执行失败：{exc}"
                    )
                    continue

    # --------------------------------------------------------
    # 没有高级预测器时，返回基础状态
    # --------------------------------------------------------

    result["result"] = {
        "lottery": lottery_name,
        "message": "暂无可用预测模块，已完成引擎初始化。",
    }

    return result


# ============================================================
# 三彩种统一分析
# ============================================================

def run_all_lotteries(
    data: Any = None,
) -> Dict[str, Any]:

    lotteries = [
        "新澳门彩",
        "老澳门彩",
        "香港彩",
    ]

    results: Dict[str, Any] = {}

    for lottery in lotteries:

        _log("")
        _log("=" * 70)
        _log(f"正在分析：{lottery}")
        _log("=" * 70)

        try:
            results[lottery] = analyze_lottery(
                lottery,
                data,
            )

        except Exception as exc:

            _log(
                f"[ERROR] {lottery} 分析失败：{exc}"
            )

            results[lottery] = {
                "lottery": lottery,
                "success": False,
                "error": str(exc),
            }

    return results


# ============================================================
# 结果输出
# ============================================================

def print_results(results: Dict[str, Any]) -> None:

    _log("")
    _log("=" * 70)
    _log("预测系统运行结果")
    _log("=" * 70)

    for lottery, result in results.items():

        _log("")
        _log(f"【{lottery}】")

        if not isinstance(result, dict):
            _log(str(result))
            continue

        success = result.get("success", False)

        if success:
            _log("状态：分析完成")
        else:
            _log("状态：基础引擎完成")

        prediction = result.get("result")

        if prediction is not None:
            _log(f"结果：{prediction}")

        if result.get("error"):
            _log(f"错误：{result['error']}")

    _log("")
    _log("=" * 70)
    _log("运行结束")
    _log("=" * 70)


# ============================================================
# 主入口
# ============================================================

def run_system(
    sync: bool = True,
    data: Any = None,
    auto_sync: Optional[bool] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    主系统入口。

    main.py 可以直接：

        from core.engine import run_system

        run_system()

    也兼容：

        run_system(sync=True)

        run_system(auto_sync=True)

        run_system(data=data)
    """

    _log("")
    _log("=" * 70)
    _log("六合彩综合预测系统")
    _log("=" * 70)
    _log(f"启动时间：{datetime.now().isoformat()}")
    _log("=" * 70)

    # --------------------------------------------------------
    # 兼容 auto_sync 参数
    # --------------------------------------------------------

    if auto_sync is not None:
        sync = auto_sync

    # --------------------------------------------------------
    # 数据同步
    # --------------------------------------------------------

    if sync and data is None:

        _log("")
        _log("正在更新在线数据...")

        try:
            sync_result = sync_data()

            if sync_result is not None:
                data = sync_result

        except Exception as exc:

            _log(
                f"[WARN] 在线数据更新失败：{exc}"
            )

            _log(
                "继续使用本地已有数据。"
            )

    # --------------------------------------------------------
    # 执行三彩种分析
    # --------------------------------------------------------

    try:

        results = run_all_lotteries(
            data=data,
        )

    except Exception as exc:

        _log("")
        _log("[ERROR] 核心分析引擎异常")
        _log(str(exc))

        traceback.print_exc()

        results = {
            "success": False,
            "error": str(exc),
        }

    # --------------------------------------------------------
    # 输出
    # --------------------------------------------------------

    if isinstance(results, dict):
        print_results(results)

    return results


# ============================================================
# 兼容旧版本可能使用的函数名称
# ============================================================

def run(*args, **kwargs):
    return run_system(*args, **kwargs)


def start(*args, **kwargs):
    return run_system(*args, **kwargs)


def main(*args, **kwargs):
    return run_system(*args, **kwargs)


# ============================================================
# 直接运行 engine.py
# ============================================================

if __name__ == "__main__":
    run_system()
