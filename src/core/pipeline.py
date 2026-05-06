"""
Composable Pipeline — 函數式數據處理管道 v2.0

性能優化：
- OHLCV 清洗管道使用 numpy 向量化操作
- 去重使用 numpy unique 而非 Python set
- 異常值過濾使用 numpy z-score
"""

from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar
from collections.abc import Callable

import numpy as np

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PipelineStep(Generic[T]):
    """Pipeline 步驟：接受 T，返回 T（可修改）。"""

    def __init__(
        self,
        func: Callable[[T], T],
        name: str = "",
        skip_on_error: bool = False,
    ) -> None:
        self._func = func
        self.name = name or func.__name__
        self.skip_on_error = skip_on_error

    def __call__(self, data: T) -> T:
        return self._func(data)


class Pipeline(Generic[T]):
    """函數式管道：將數據依次通過多個步驟。"""

    def __init__(self, name: str = "pipeline") -> None:
        self.name = name
        self._steps: list[PipelineStep[T]] = []

    def add(
        self,
        func: Callable[[T], T],
        name: str = "",
        skip_on_error: bool = False,
    ) -> Pipeline[T]:
        """添加步驟，支持鏈式調用."""
        self._steps.append(PipelineStep(func, name=name, skip_on_error=skip_on_error))
        return self

    def run(self, data: T) -> T:
        """執行管道."""
        result = data
        for step in self._steps:
            try:
                result = step(result)
            except Exception:
                if step.skip_on_error:
                    logger.warning("Pipeline [%s] step [%s] failed (skipped)", self.name, step.name)
                else:
                    logger.exception("Pipeline [%s] step [%s] failed", self.name, step.name)
                    raise
        return result

    def __len__(self) -> int:
        return len(self._steps)


# ─── 常用管道工廠 ───


def ohlcv_clean_pipeline() -> Pipeline[list[dict[str, Any]]]:
    """K 線數據清洗管道 — numpy 向量化版。"""
    p = Pipeline[list[dict[str, Any]]](name="ohlcv_clean")

    def _remove_duplicates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """去重（numpy 向量化）。"""
        if not rows:
            return rows
        timestamps = np.array([r["timestamp"] for r in rows], dtype=np.int64)
        _, unique_indices = np.unique(timestamps, return_index=True)
        unique_indices.sort()
        return [rows[i] for i in unique_indices]

    def _sort_by_time(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """按時間排序（numpy argsort）。"""
        if not rows:
            return rows
        timestamps = np.array([r["timestamp"] for r in rows], dtype=np.int64)
        sorted_indices = np.argsort(timestamps)
        return [rows[i] for i in sorted_indices]

    def _fill_gaps(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """填充缺失值（前向填充 close 到 open/high/low）。"""
        for r in rows:
            c = r.get("close", 0)
            if r.get("open") is None or r.get("open") == 0:
                r["open"] = c
            if r.get("high") is None or r.get("high") == 0:
                r["high"] = c
            if r.get("low") is None or r.get("low") == 0:
                r["low"] = c
        return rows

    def _validate_ohlcv(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """驗證 OHLCV 數據完整性，過濾無效記錄 — 批量處理。"""
        if not rows:
            return rows

        # 批量提取為 numpy 數組
        n = len(rows)
        timestamps = np.empty(n, dtype=np.int64)
        opens = np.empty(n, dtype=np.float64)
        highs = np.empty(n, dtype=np.float64)
        lows = np.empty(n, dtype=np.float64)
        closes = np.empty(n, dtype=np.float64)

        for i, r in enumerate(rows):
            timestamps[i] = r.get("timestamp", 0) or 0
            opens[i] = r.get("open", 0) or 0
            highs[i] = r.get("high", 0) or 0
            lows[i] = r.get("low", 0) or 0
            closes[i] = r.get("close", 0) or 0

        # 向量化有效性檢查
        valid = (timestamps > 0) & (closes > 0) & (highs > 0) & (lows > 0) & (highs >= lows) & (closes > 0)

        # 修正高低點
        max_oc = np.maximum(opens, closes)
        min_oc = np.minimum(opens, closes)
        highs = np.maximum(highs, max_oc)
        lows = np.minimum(lows, min_oc)

        # 批量寫回
        validated = []
        for i, r in enumerate(rows):
            if valid[i]:
                r["high"] = float(highs[i])
                r["low"] = float(lows[i])
                validated.append(r)
        return validated

    def _remove_zero_volume(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """移除零成交量記錄。"""
        return [r for r in rows if r.get("volume", 0) > 0]

    p.add(_remove_duplicates, name="deduplicate")
    p.add(_sort_by_time, name="sort")
    p.add(_fill_gaps, name="fill_gaps", skip_on_error=True)
    p.add(_validate_ohlcv, name="validate")
    p.add(_remove_zero_volume, name="remove_zero_volume")
    return p


def ohlcv_outlier_pipeline(multiplier: float = 3.0) -> Pipeline[list[dict[str, Any]]]:
    """K 線異常值過濾管道（基於成交量 Z-Score，numpy 向量化）。"""
    p = Pipeline[list[dict[str, Any]]](name="ohlcv_outlier")

    def _filter_outliers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(rows) < 10:
            return rows
        volumes = np.array([r["volume"] for r in rows], dtype=np.float64)
        mean_v = float(np.mean(volumes))
        std_v = float(np.std(volumes))
        if std_v <= 0:
            return rows
        threshold = mean_v + multiplier * std_v
        mask = volumes <= threshold
        return [r for r, keep in zip(rows, mask) if keep]

    p.add(_filter_outliers, name="zscore_outlier")
    return p
