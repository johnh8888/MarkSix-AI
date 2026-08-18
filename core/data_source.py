# -*- coding: utf-8 -*-
"""在线历史/实时 API 同步兼容层，复用经过验证的 V3 engine 解析器。"""
from .engine import (
    http_json, parse_history_api, parse_realtime_api,
    sync_history, sync_realtime, identify_lottery, parse_numbers,
)

__all__ = ["http_json", "parse_history_api", "parse_realtime_api", "sync_history", "sync_realtime", "identify_lottery", "parse_numbers"]
