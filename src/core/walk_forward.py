"""
Walk-Forward Analysis — 新架構版本

使用 src.core.backtest.BacktestEngine + src.core.registry
取代舊版 src/backtest/walk_forward.py

功能：
- Walk-Forward 樣本外驗證
- 參數網格搜索（in-sample 最優化）
- Out-of-Sample 績效彙總
- 防過擬合評分

用法：
    from src.core.walk_forward import WalkForwardAnalyzer

    analyzer = WalkForwardAnalyzer(rows, signals_fn, n_splits=5)
    result = analyzer.run(since_ms, until_ms)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from .backtest import BacktestConfig, BacktestEngine, BacktestReport, compute_performance_metrics

logger = logging.getLogger(__name__)

SignalFn = Callable[..., list[int]]


@dataclass(slots=True)
class WFSplit:
    """單個 Walk-Forward 分段結果."""

    fold: int
    train_bars: int
    test_bars: int
    best_params: dict[str, Any]
    in_sample_score: float | None
    oos_return_pct: float
    oos_sharpe: float
    oos_drawdown_pct: float
    oos_trades: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "fold": self.fold,
            "train_bars": self.train_bars,
            "test_bars": self.test_bars,
            "best_params": self.best_params,
            "in_sample_score": self.in_sample_score,
            "oos_return_pct": round(self.oos_return_pct, 2),
            "oos_sharpe": round(self.oos_sharpe, 2),
            "oos_drawdown_pct": round(self.oos_drawdown_pct, 2),
            "oos_trades": self.oos_trades,
        }


@dataclass(slots=True)
class WFResult:
    """Walk-Forward 完整結果."""

    strategy: str
    splits: list[WFSplit] = field(default_factory=list)
    avg_oos_return_pct: float = 0.0
    avg_oos_sharpe: float = 0.0
    avg_oos_drawdown_pct: float = 0.0
    oos_equity_curve: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.error is None and len(self.splits) > 0

    @property
    def stability_score(self) -> float:
        """穩定性評分 — OOS Sharpe 的一致性（0~1）."""
        if not self.splits:
            return 0.0
        sharpes = [s.oos_sharpe for s in self.splits]
        if not sharpes:
            return 0.0
        mean_s = sum(sharpes) / len(sharpes)
        if mean_s <= 0:
            return 0.0
        variance = sum((s - mean_s) ** 2 for s in sharpes) / len(sharpes)
        cv = (variance ** 0.5) / mean_s if mean_s != 0 else float("inf")
        return max(0.0, 1.0 - cv)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "n_splits": len(self.splits),
            "avg_oos_return_pct": round(self.avg_oos_return_pct, 2),
            "avg_oos_sharpe": round(self.avg_oos_sharpe, 2),
            "avg_oos_drawdown_pct": round(self.avg_oos_drawdown_pct, 2),
            "stability_score": round(self.stability_score, 3),
            "splits": [s.to_dict() for s in self.splits],
            "error": self.error,
        }


class WalkForwardAnalyzer:
    """
    Walk-Forward 分析器.

    Args:
        rows: 完整 OHLCV 數據
        signal_fn: 策略信號函數 (rows, **params) -> list[int]
        param_combinations: 參數組合列表
        n_splits: 分段數
        train_ratio: 訓練集比例
        objective: 優化目標欄位名
        config: 回測配置
    """

    def __init__(
        self,
        rows: list[dict[str, Any]],
        signal_fn: SignalFn,
        param_combinations: list[dict[str, Any]],
        n_splits: int = 5,
        train_ratio: float = 0.7,
        objective: str = "sharpe_ratio",
        config: BacktestConfig | None = None,
    ) -> None:
        self._rows = rows
        self._signal_fn = signal_fn
        self._param_combos = param_combinations
        self._n_splits = n_splits
        self._train_ratio = train_ratio
        self._objective = objective
        self._config = config or BacktestConfig()
        self._engine = BacktestEngine(config=self._config)

    def run(self, since_ms: int, until_ms: int, strategy_name: str = "unknown") -> WFResult:
        """執行 Walk-Forward Analysis."""
        result = WFResult(strategy=strategy_name)

        if not self._rows or len(self._rows) < 50:
            result.error = "數據不足（至少 50 根 K 線）"
            return result

        n = len(self._rows)
        split_size = n // self._n_splits
        if split_size < 20:
            result.error = f"每段太短（{split_size} 根），請增加數據或減少分段數"
            return result

        if not self._param_combos:
            self._param_combos = [{}]  # 至少跑一次預設參數

        oos_equities: list[dict[str, Any]] = []

        for fold in range(self._n_splits):
            start_idx = fold * split_size
            end_idx = min(start_idx + split_size, n)
            fold_rows = self._rows[start_idx:end_idx]

            train_end = int(len(fold_rows) * self._train_ratio)
            train_rows = fold_rows[:train_end]
            test_rows = fold_rows[train_end:]

            if len(train_rows) < 10 or len(test_rows) < 5:
                continue

            train_since = train_rows[0]["timestamp"]
            train_until = train_rows[-1]["timestamp"]
            test_since = test_rows[0]["timestamp"]
            test_until = test_rows[-1]["timestamp"]

            # ── In-sample: 尋找最優參數 ──
            best_score = -float("inf")
            best_params: dict[str, Any] = {}

            for params in self._param_combos:
                try:
                    signals = self._signal_fn(train_rows, **params)
                    report = self._engine.run(train_rows, signals, train_since, train_until)
                    if report.error:
                        continue
                    score = report.metrics.get(self._objective, 0)
                    if score is not None and score > best_score:
                        best_score = score
                        best_params = params.copy()
                except Exception as e:
                    logger.debug("wf_in_sample_error", extra={"fold": fold, "params": params, "error": str(e)})
                    continue

            # ── Out-of-sample: 用最優參數驗證 ──
            try:
                oos_signals = self._signal_fn(test_rows, **best_params)
                oos_report = self._engine.run(test_rows, oos_signals, test_since, test_until)
                oos_metrics = oos_report.metrics if not oos_report.error else {}
            except Exception as e:
                logger.warning("wf_oos_error", extra={"fold": fold, "error": str(e)})
                oos_metrics = {}

            split = WFSplit(
                fold=fold + 1,
                train_bars=len(train_rows),
                test_bars=len(test_rows),
                best_params=best_params,
                in_sample_score=round(best_score, 4) if best_score > -float("inf") else None,
                oos_return_pct=oos_metrics.get("total_return_pct", 0),
                oos_sharpe=oos_metrics.get("sharpe_ratio", 0),
                oos_drawdown_pct=oos_metrics.get("max_drawdown_pct", 0),
                oos_trades=oos_metrics.get("num_trades", 0),
            )
            result.splits.append(split)

            # 收集 OOS 權益曲線
            if not oos_report.error and oos_report.equity_curve:
                oos_equities.extend(oos_report.equity_curve)

        if not result.splits:
            result.error = "所有分段均失敗"
            return result

        result.avg_oos_return_pct = sum(s.oos_return_pct for s in result.splits) / len(result.splits)
        result.avg_oos_sharpe = sum(s.oos_sharpe for s in result.splits) / len(result.splits)
        result.avg_oos_drawdown_pct = sum(s.oos_drawdown_pct for s in result.splits) / len(result.splits)
        result.oos_equity_curve = oos_equities

        return result
