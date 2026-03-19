"""
Composable Pipeline — 函數式數據處理管道

取代散落的 if/else 邏輯串接。
Pipeline = [Step₁ → Step₂ → ... → Stepₙ]

用途：
  - 數據清洗：raw → 清洗 → 標準化 → 輸出
  - 信號生成：OHLCV → 指標計算 → 信號判定 → Signal
  - 回測流程：數據 → 策略 → 風控 → 報告
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PipelineStep(Generic[T]):
    """
    Pipeline 步驟：接受 T，返回 T（可修改）。
    實現 __call__ 或傳入 func。
    """

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
    """
    函數式管道：將數據依次通過多個步驟。

    用法：
        pipeline = Pipeline(name="data_clean")
        pipeline.add(lambda rows: [r for r in rows if r["volume"] > 0])
        pipeline.add(lambda rows: sorted(rows, key=lambda r: r["timestamp"]))
        clean_rows = pipeline.run(raw_rows)
    """

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
    """K 線數據清洗管道."""
    p = Pipeline[list[dict[str, Any]]](name="ohlcv_clean")

    def _remove_zero_volume(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [r for r in rows if r.get("volume", 0) > 0]

    def _remove_duplicates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[int] = set()
        out = []
        for r in rows:
            ts = r["timestamp"]
            if ts not in seen:
                seen.add(ts)
                out.append(r)
        return out

    def _sort_by_time(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(rows, key=lambda r: r["timestamp"])

    p.add(_remove_duplicates, name="deduplicate")
    p.add(_sort_by_time, name="sort")
    p.add(_remove_zero_volume, name="remove_zero_volume")
    return p


def ohlcv_outlier_pipeline(multiplier: float = 3.0) -> Pipeline[list[dict[str, Any]]]:
    """K 線異常值過濾管道（基於成交量 Z-Score）."""
    p = Pipeline[list[dict[str, Any]]](name="ohlcv_outlier")

    def _filter_outliers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(rows) < 10:
            return rows
        volumes = [r["volume"] for r in rows]
        mean_v = sum(volumes) / len(volumes)
        var_v = sum((v - mean_v) ** 2 for v in volumes) / len(volumes)
        std_v = var_v**0.5 if var_v > 0 else 1
        threshold = mean_v + multiplier * std_v
        return [r for r in rows if r["volume"] <= threshold]

    p.add(_filter_outliers, name="zscore_outlier")
    return p
