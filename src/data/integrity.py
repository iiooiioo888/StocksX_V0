# 數據完整性校驗
from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_data_hash(rows: list[dict[str, Any]]) -> str:
    """計算 K 線數據的 hash，用於校驗快取完整性"""
    if not rows:
        return ""
    key_data = f"{len(rows)}:{rows[0].get('timestamp', 0)}:{rows[-1].get('timestamp', 0)}:{rows[-1].get('close', 0)}"
    return hashlib.md5(key_data.encode()).hexdigest()[:12]


def validate_ohlcv(rows: list[dict[str, Any]]) -> list[str]:
    """校驗 K 線數據完整性，回傳問題列表"""
    issues = []
    if not rows:
        return ["數據為空"]

    required = ["timestamp", "open", "high", "low", "close"]
    for i, r in enumerate(rows[:5]):
        for k in required:
            if k not in r:
                issues.append(f"第 {i} 根缺少欄位 {k}")

    for i in range(1, len(rows)):
        if rows[i]["timestamp"] <= rows[i - 1]["timestamp"]:
            issues.append(f"時間戳亂序：第 {i} 根 ({rows[i]['timestamp']}) <= 第 {i-1} 根")
            break

    for i, r in enumerate(rows):
        h, l = r.get("high", 0), r.get("low", 0)
        if h < l and h > 0:
            issues.append(f"第 {i} 根 high({h}) < low({l})")
            break

    zero_close = sum(1 for r in rows if not r.get("close"))
    if zero_close > len(rows) * 0.1:
        issues.append(f"超過 10% 的 K 線 close=0（{zero_close}/{len(rows)}）")

    return issues
