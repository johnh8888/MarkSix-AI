# -*- coding:utf-8 -*-

"""
六合彩 AI V3.3 FINAL

API同步模块
"""

from __future__ import annotations


import time
import requests


from config import API_CONFIG


from .database import save_draw



TIMEOUT = 15

RETRY = 3



# API地址

API_HISTORY = API_CONFIG["history"]

API_HK = API_CONFIG["hk"]

API_NEW_MACAU = API_CONFIG["newMacau"]

API_OLD_MACAU = API_CONFIG["oldMacau"]
