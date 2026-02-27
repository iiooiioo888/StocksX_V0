from __future__ import annotations

"""
IOS Bark 推播工具。

使用前請先在環境變數設定：
    BARK_KEY=你的裝置 key
    （可選）BARK_SERVER=https://api.day.app 或自架伺服器位址
"""

from typing import Optional
import os

import requests


def send_bark(
    title: str,
    body: str,
    group: Optional[str] = None,
    url: Optional[str] = None,
    level: Optional[str] = None,  # active / timeSensitive / critical
) -> None:
    """
    發送一則 Bark 通知。若未設定 BARK_KEY，則安靜略過不做任何事。
    """
    key = os.getenv("BARK_KEY")
    if not key:
        return

    server = os.getenv("BARK_SERVER", "https://api.day.app").rstrip("/")
    api = f"{server}/{key}/{requests.utils.quote(title)}/{requests.utils.quote(body)}"
    params: dict[str, str] = {}
    if group:
        params["group"] = group
    if url:
        params["url"] = url
    if level:
        params["level"] = level

    try:
        requests.get(api, params=params, timeout=5)
    except Exception:
        # 通知失敗不影響主流程，可視需要加上 logging
        pass

