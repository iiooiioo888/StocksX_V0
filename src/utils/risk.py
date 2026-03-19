"""
風險分析模組 — 進階風險指標 & 蒙特卡羅模擬

功能：
- VaR (Value at Risk) — 歷史法、參數法
- CVaR (Conditional VaR / Expected Shortfall)
- 最大回撤持續時間
- 蒙特卡羅模擬未來回撤分佈
- 相關性矩陣
- 波動率錐

用法：
    from src.utils.risk import RiskAnalyzer

    analyzer = RiskAnalyzer(returns)
    var_95 = analyzer.var(0.95)
    cvar_95 = analyzer.cvar(0.95)
    sim = analyzer.monte_carlo(n_simulations=10000, horizon=30)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RiskMetrics:
    """風險指標集合."""

    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    cvar_99: float = 0.0
    max_drawdown: float = 0.0
    max_dd_duration: int = 0  # 最大回撤持續天數
    volatility: float = 0.0
    annualized_vol: float = 0.0
    downside_vol: float = 0.0
    ulcer_index: float = 0.0
    pain_index: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "var_95_pct": round(self.var_95 * 100, 4),
            "var_99_pct": round(self.var_99 * 100, 4),
            "cvar_95_pct": round(self.cvar_95 * 100, 4),
            "cvar_99_pct": round(self.cvar_99 * 100, 4),
            "max_drawdown_pct": round(self.max_drawdown * 100, 2),
            "max_dd_duration_bars": self.max_dd_duration,
            "volatility": round(self.volatility, 6),
            "annualized_vol_pct": round(self.annualized_vol * 100, 2),
            "downside_vol_pct": round(self.downside_vol * 100, 2),
            "ulcer_index": round(self.ulcer_index, 4),
            "pain_index": round(self.pain_index, 4),
        }


@dataclass(slots=True)
class MonteCarloResult:
    """蒙特卡羅模擬結果."""

    percentiles: dict[str, float] = field(default_factory=dict)
    mean_final_equity: float = 0.0
    median_final_equity: float = 0.0
    prob_loss: float = 0.0  # 虧損機率
    max_drawdown_dist: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "percentiles": {k: round(v, 2) for k, v in self.percentiles.items()},
            "mean_final_equity": round(self.mean_final_equity, 2),
            "median_final_equity": round(self.median_final_equity, 2),
            "prob_loss_pct": round(self.prob_loss * 100, 2),
            "max_drawdown_dist": {k: round(v * 100, 2) for k, v in self.max_drawdown_dist.items()},
        }


class RiskAnalyzer:
    """風險分析器."""

    def __init__(self, returns: list[float]) -> None:
        self._returns = returns
        self._n = len(returns)
        self._sorted = sorted(returns) if returns else []

    @property
    def mean(self) -> float:
        if not self._n:
            return 0.0
        return sum(self._returns) / self._n

    @property
    def std(self) -> float:
        if self._n < 2:
            return 0.0
        m = self.mean
        var = sum((r - m) ** 2 for r in self._returns) / (self._n - 1)
        return math.sqrt(var)

    def var(self, confidence: float = 0.95) -> float:
        """歷史 VaR（負值表示損失）."""
        if not self._sorted:
            return 0.0
        idx = int(len(self._sorted) * (1 - confidence))
        idx = max(0, min(idx, len(self._sorted) - 1))
        return self._sorted[idx]

    def cvar(self, confidence: float = 0.95) -> float:
        """CVaR / Expected Shortfall."""
        if not self._sorted:
            return 0.0
        idx = int(len(self._sorted) * (1 - confidence))
        idx = max(0, min(idx, len(self._sorted) - 1))
        tail = self._sorted[: idx + 1]
        return sum(tail) / len(tail) if tail else 0.0

    @property
    def max_drawdown(self) -> float:
        """最大回撤（正數）."""
        if not self._returns:
            return 0.0
        peak = 1.0
        equity = 1.0
        max_dd = 0.0
        for r in self._returns:
            equity *= 1 + r
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd

    @property
    def max_drawdown_duration(self) -> int:
        """最大回撤持續期數."""
        if not self._returns:
            return 0
        peak = 1.0
        equity = 1.0
        max_dur = 0
        cur_dur = 0
        for r in self._returns:
            equity *= 1 + r
            if equity > peak:
                peak = equity
                cur_dur = 0
            else:
                cur_dur += 1
                max_dur = max(max_dur, cur_dur)
        return max_dur

    @property
    def downside_volatility(self) -> float:
        """下行波動率."""
        if self._n < 2:
            return 0.0
        neg = [r for r in self._returns if r < 0]
        if not neg:
            return 0.0
        mean_neg = sum(neg) / len(neg)
        var = sum((r - mean_neg) ** 2 for r in neg) / len(neg)
        return math.sqrt(var)

    @property
    def ulcer_index(self) -> float:
        """Ulcer Index — 回撤的 RMS."""
        if not self._returns:
            return 0.0
        peak = 1.0
        equity = 1.0
        dd_squares: list[float] = []
        for r in self._returns:
            equity *= 1 + r
            if equity > peak:
                peak = equity
            dd_pct = ((peak - equity) / peak) * 100 if peak else 0
            dd_squares.append(dd_pct ** 2)
        return math.sqrt(sum(dd_squares) / len(dd_squares)) if dd_squares else 0.0

    @property
    def pain_index(self) -> float:
        """Pain Index — 平均回撤百分比."""
        if not self._returns:
            return 0.0
        peak = 1.0
        equity = 1.0
        total_dd = 0.0
        for r in self._returns:
            equity *= 1 + r
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak else 0
            total_dd += dd
        return total_dd / len(self._returns)

    def compute_all(self) -> RiskMetrics:
        """計算全部風險指標."""
        return RiskMetrics(
            var_95=self.var(0.95),
            var_99=self.var(0.99),
            cvar_95=self.cvar(0.95),
            cvar_99=self.cvar(0.99),
            max_drawdown=self.max_drawdown,
            max_dd_duration=self.max_drawdown_duration,
            volatility=self.std,
            annualized_vol=self.std * math.sqrt(252),
            downside_vol=self.downside_volatility,
            ulcer_index=self.ulcer_index,
            pain_index=self.pain_index,
        )

    def monte_carlo(
        self,
        n_simulations: int = 10000,
        horizon: int = 30,
        initial_equity: float = 10000.0,
    ) -> MonteCarloResult:
        """
        蒙特卡羅模擬 — 基於歷史報酬分佈.

        Args:
            n_simulations: 模擬次數
            horizon: 預測天數
            initial_equity: 初始資金
        """
        if not self._returns:
            return MonteCarloResult()

        final_equities: list[float] = []
        max_dds: list[float] = []

        for _ in range(n_simulations):
            equity = initial_equity
            peak = equity
            max_dd = 0.0

            for _ in range(horizon):
                r = random.choice(self._returns)
                equity *= 1 + r
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak if peak else 0
                if dd > max_dd:
                    max_dd = dd

            final_equities.append(equity)
            max_dds.append(max_dd)

        final_equities.sort()
        max_dds.sort()

        def percentile(data: list[float], p: float) -> float:
            idx = int(len(data) * p)
            return data[max(0, min(idx, len(data) - 1))]

        return MonteCarloResult(
            percentiles={
                "p5": percentile(final_equities, 0.05),
                "p25": percentile(final_equities, 0.25),
                "p50": percentile(final_equities, 0.50),
                "p75": percentile(final_equities, 0.75),
                "p95": percentile(final_equities, 0.95),
            },
            mean_final_equity=sum(final_equities) / len(final_equities),
            median_final_equity=percentile(final_equities, 0.50),
            prob_loss=sum(1 for e in final_equities if e < initial_equity) / n_simulations,
            max_drawdown_dist={
                "p50": percentile(max_dds, 0.50),
                "p95": percentile(max_dds, 0.95),
                "max": max(max_dds),
            },
        )


def compute_correlation(returns_a: list[float], returns_b: list[float]) -> float:
    """計算兩個報酬序列的相關係數."""
    n = min(len(returns_a), len(returns_b))
    if n < 2:
        return 0.0
    a, b = returns_a[:n], returns_b[:n]
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / (n - 1)
    std_a = math.sqrt(sum((x - mean_a) ** 2 for x in a) / (n - 1))
    std_b = math.sqrt(sum((x - mean_b) ** 2 for x in b) / (n - 1))
    if std_a == 0 or std_b == 0:
        return 0.0
    return cov / (std_a * std_b)
