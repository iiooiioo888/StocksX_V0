"""
投資組合分析模組 — 多資產配置與優化

功能：
- 等權重 / 最小方差 / 風險平價 配置
- 投資組合層級績效指標
- 資產間相關性分析
- 風險貢獻分解
- 有效前沿計算

用法：
    from src.utils.portfolio import PortfolioAnalyzer

    analyzer = PortfolioAnalyzer(assets_returns)
    weights = analyzer.min_variance_weights()
    metrics = analyzer.portfolio_metrics(weights)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PortfolioWeights:
    """投資組合權重."""

    assets: list[str]
    weights: list[float]

    def to_dict(self) -> dict[str, float]:
        return dict(zip(self.assets, self.weights))

    def __str__(self) -> str:
        parts = [f"  {a}: {w*100:.1f}%" for a, w in zip(self.assets, self.weights) if w > 0.001]
        return "\n".join(parts)


@dataclass(slots=True)
class PortfolioMetrics:
    """投資組合績效指標."""

    annual_return: float = 0.0
    annual_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    diversification_ratio: float = 0.0
    risk_contributions: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "annual_return_pct": round(self.annual_return * 100, 2),
            "annual_volatility_pct": round(self.annual_volatility * 100, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "max_drawdown_pct": round(self.max_drawdown * 100, 2),
            "diversification_ratio": round(self.diversification_ratio, 3),
            "risk_contributions": {k: round(v * 100, 2) for k, v in self.risk_contributions.items()},
        }


def _covariance_matrix(returns: dict[str, list[float]]) -> dict[str, dict[str, float]]:
    """計算共變異數矩陣."""
    assets = list(returns.keys())
    n_periods = min(len(returns[a]) for a in assets)
    n_assets = len(assets)

    means = {}
    for a in assets:
        r = returns[a][:n_periods]
        means[a] = sum(r) / n_periods

    cov = {}
    for a in assets:
        cov[a] = {}
        for b in assets:
            ra = returns[a][:n_periods]
            rb = returns[b][:n_periods]
            c = sum((ra[i] - means[a]) * (rb[i] - means[b]) for i in range(n_periods)) / (n_periods - 1)
            cov[a][b] = c

    return cov


def _matrix_multiply_vector(matrix: dict[str, dict[str, float]], vector: dict[str, float]) -> dict[str, float]:
    """矩陣乘向量."""
    result = {}
    for row in matrix:
        result[row] = sum(matrix[row][col] * vector.get(col, 0) for col in matrix[row])
    return result


def _dot_product(a: dict[str, float], b: dict[str, float]) -> float:
    """內積."""
    return sum(a.get(k, 0) * b.get(k, 0) for k in set(a) | set(b))


class PortfolioAnalyzer:
    """投資組合分析器."""

    def __init__(self, asset_returns: dict[str, list[float]], risk_free_rate: float = 0.0) -> None:
        self._returns = asset_returns
        self._assets = list(asset_returns.keys())
        self._rf = risk_free_rate / 252  # 日化
        self._cov = _covariance_matrix(asset_returns)

    @property
    def covariance_matrix(self) -> dict[str, dict[str, float]]:
        return self._cov

    @property
    def correlation_matrix(self) -> dict[str, dict[str, float]]:
        """相關係數矩陣."""
        corr = {}
        for a in self._assets:
            corr[a] = {}
            std_a = math.sqrt(self._cov[a][a]) if self._cov[a][a] > 0 else 1e-10
            for b in self._assets:
                std_b = math.sqrt(self._cov[b][b]) if self._cov[b][b] > 0 else 1e-10
                corr[a][b] = self._cov[a][b] / (std_a * std_b)
        return corr

    @property
    def mean_returns(self) -> dict[str, float]:
        """日均報酬."""
        means = {}
        for a in self._assets:
            r = self._returns[a]
            means[a] = sum(r) / len(r) if r else 0.0
        return means

    def equal_weight(self) -> PortfolioWeights:
        """等權重配置."""
        n = len(self._assets)
        return PortfolioWeights(assets=self._assets, weights=[1.0 / n] * n)

    def inverse_volatility_weight(self) -> PortfolioWeights:
        """反波動率加權 — 波動率越低，權重越高."""
        inv_vols = {}
        total = 0.0
        for a in self._assets:
            vol = math.sqrt(self._cov[a][a])
            inv_vols[a] = 1.0 / vol if vol > 1e-10 else 1.0
            total += inv_vols[a]

        weights = [inv_vols[a] / total for a in self._assets]
        return PortfolioWeights(assets=self._assets, weights=weights)

    def risk_parity_weight(self, max_iter: int = 100, tol: float = 1e-8) -> PortfolioWeights:
        """
        風險平價 — 每個資產對總風險的貢獻相等.
        使用迭代法求解.
        """
        n = len(self._assets)
        if n == 0:
            return PortfolioWeights(assets=[], weights=[])

        # 初始權重：等權重
        w = {a: 1.0 / n for a in self._assets}

        for _ in range(max_iter):
            # 計算各資產邊際風險貢獻
            cov_w = _matrix_multiply_vector(self._cov, w)
            port_vol = math.sqrt(_dot_product(w, cov_w))
            if port_vol < 1e-10:
                break

            # 風險貢獻
            rc = {}
            for a in self._assets:
                rc[a] = w[a] * cov_w[a] / port_vol

            # 目標：每個資產風險貢獻 = 總風險 / N
            target_rc = port_vol / n

            # 更新權重（比例調整）
            new_w = {}
            total_w = 0.0
            for a in self._assets:
                if rc[a] > 1e-10:
                    new_w[a] = w[a] * (target_rc / rc[a])
                else:
                    new_w[a] = w[a]
                total_w += new_w[a]

            # 正規化
            for a in self._assets:
                new_w[a] /= total_w

            # 收斂檢查
            diff = sum(abs(new_w[a] - w[a]) for a in self._assets)
            w = new_w
            if diff < tol:
                break

        weights = [w[a] for a in self._assets]
        return PortfolioWeights(assets=self._assets, weights=weights)

    def min_variance_weight(self, max_iter: int = 200, learning_rate: float = 0.01) -> PortfolioWeights:
        """
        最小方差配置 — 使用梯度下降.
        目標：最小化 w'Σw，約束：Σw = 1, w >= 0
        """
        n = len(self._assets)
        if n == 0:
            return PortfolioWeights(assets=[], weights=[])

        w = {a: 1.0 / n for a in self._assets}

        for _ in range(max_iter):
            cov_w = _matrix_multiply_vector(self._cov, w)

            # 梯度 = 2 * Σw
            grad = {a: 2 * cov_w[a] for a in self._assets}

            # 梯度下降
            new_w = {a: w[a] - learning_rate * grad[a] for a in self._assets}

            # 投影到 simplex（非負 + 和為1）
            new_w = {a: max(0.001, new_w[a]) for a in self._assets}
            total = sum(new_w.values())
            new_w = {a: new_w[a] / total for a in self._assets}

            # 收斂檢查
            diff = sum(abs(new_w[a] - w[a]) for a in self._assets)
            w = new_w
            if diff < 1e-8:
                break

        weights = [w[a] for a in self._assets]
        return PortfolioWeights(assets=self._assets, weights=weights)

    def portfolio_variance(self, weights: list[float]) -> float:
        """計算投資組合變異數."""
        w = {a: weights[i] for i, a in enumerate(self._assets)}
        cov_w = _matrix_multiply_vector(self._cov, w)
        return _dot_product(w, cov_w)

    def portfolio_metrics(self, weights: list[float]) -> PortfolioMetrics:
        """計算投資組合績效指標."""
        w = {a: weights[i] for i, a in enumerate(self._assets)}
        n_periods = min(len(self._returns[a]) for a in self._assets)

        # 投資組合日報酬
        port_returns = []
        for t in range(n_periods):
            r = sum(w[a] * self._returns[a][t] for a in self._assets)
            port_returns.append(r)

        if not port_returns:
            return PortfolioMetrics()

        mean_r = sum(port_returns) / len(port_returns)
        var_r = sum((r - mean_r) ** 2 for r in port_returns) / (len(port_returns) - 1)
        std_r = math.sqrt(var_r)

        annual_return = mean_r * 252
        annual_vol = std_r * math.sqrt(252)
        sharpe = (mean_r - self._rf) / std_r * math.sqrt(252) if std_r > 0 else 0.0

        # 最大回撤
        equity = 1.0
        peak = 1.0
        max_dd = 0.0
        for r in port_returns:
            equity *= 1 + r
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd

        # 風險貢獻
        cov_w = _matrix_multiply_vector(self._cov, w)
        port_vol = math.sqrt(_dot_product(w, cov_w))
        risk_contributions = {}
        if port_vol > 1e-10:
            for a in self._assets:
                risk_contributions[a] = (w[a] * cov_w[a]) / port_vol

        # 分散化比率
        weighted_vols = sum(w[a] * math.sqrt(self._cov[a][a]) for a in self._assets)
        div_ratio = weighted_vols / port_vol if port_vol > 0 else 1.0

        return PortfolioMetrics(
            annual_return=annual_return,
            annual_volatility=annual_vol,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            diversification_ratio=div_ratio,
            risk_contributions=risk_contributions,
        )

    def efficient_frontier(self, n_points: int = 20) -> list[dict[str, float]]:
        """
        計算有效前沿 — 簡化版（僅兩個資產時精確，多資產時近似）.
        Returns: [{"return": r, "volatility": v, "weights": {...}}, ...]
        """
        results = []

        # 使用最小方差和最大報酬的兩個極端
        mv = self.min_variance_weight()
        mv_metrics = self.portfolio_metrics(mv.weights)

        # 最大報酬（全部配置到最高報酬資產）
        means = self.mean_returns
        best_asset = max(means, key=means.get)
        max_r_weights = [1.0 if a == best_asset else 0.0 for a in self._assets]
        max_r_metrics = self.portfolio_metrics(max_r_weights)

        # 在兩個極端之間插值
        for i in range(n_points):
            t = i / (n_points - 1) if n_points > 1 else 0
            interp_weights = [
                (1 - t) * mv.weights[j] + t * max_r_weights[j]
                for j in range(len(self._assets))
            ]
            # 正規化
            total = sum(interp_weights)
            if total > 0:
                interp_weights = [w / total for w in interp_weights]

            m = self.portfolio_metrics(interp_weights)
            results.append({
                "return": m.annual_return,
                "volatility": m.annual_volatility,
                "sharpe": m.sharpe_ratio,
                "weights": dict(zip(self._assets, interp_weights)),
            })

        return results
