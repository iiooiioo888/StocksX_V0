"""
現代投資組合優化 — Markowitz / 風險平價 / Black-Litterman

功能：
- 有效前沿 (Efficient Frontier) 計算
- 最小方差組合 (Minimum Variance)
- 最大 Sharpe 比率組合 (Max Sharpe)
- 風險平價 (Risk Parity / Equal Risk Contribution)
- Black-Litterman 模型（結合市場均衡 + 主觀觀點）
- 限制條件優化（單一資產上限、行業限制等）

用法：
    from src.utils.portfolio_optimizer import PortfolioOptimizer

    optimizer = PortfolioOptimizer(returns_df)
    weights = optimizer.max_sharpe()
    frontier = optimizer.efficient_frontier(n_points=50)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    from scipy.optimize import minimize

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


@dataclass(slots=True)
class PortfolioResult:
    """優化結果."""

    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    risk_contributions: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "weights": {k: round(v, 6) for k, v in self.weights.items()},
            "expected_return_pct": round(self.expected_return * 100, 2),
            "volatility_pct": round(self.volatility * 100, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "risk_contributions": {k: round(v * 100, 2) for k, v in self.risk_contributions.items()},
        }


@dataclass(slots=True)
class FrontierPoint:
    """有效前沿上的一個點."""

    target_return: float
    volatility: float
    sharpe_ratio: float
    weights: dict[str, float]


class PortfolioOptimizer:
    """
    投資組合優化器.

    Args:
        returns: DataFrame, 每列為一個資產的日報酬率
        risk_free_rate: 無風險利率（年化），預設 0.05 (5%)
    """

    def __init__(
        self,
        returns: np.ndarray,
        asset_names: list[str] | None = None,
        risk_free_rate: float = 0.05,
        annualization_factor: int = 252,
    ) -> None:
        if returns.ndim == 1:
            returns = returns.reshape(-1, 1)

        self._returns = np.asarray(returns, dtype=np.float64)
        self._n_assets = self._returns.shape[1]
        self._names = asset_names or [f"Asset_{i}" for i in range(self._n_assets)]
        self._rf_daily = risk_free_rate / annualization_factor
        self._ann_factor = annualization_factor

        # 預計算
        self._mean_returns = np.mean(self._returns, axis=0) * annualization_factor
        self._cov_matrix = np.cov(self._returns, rowvar=False) * annualization_factor
        if self._n_assets == 1:
            self._cov_matrix = np.array([[self._cov_matrix]])

    @property
    def mean_returns(self) -> np.ndarray:
        return self._mean_returns

    @property
    def cov_matrix(self) -> np.ndarray:
        return self._cov_matrix

    @property
    def asset_names(self) -> list[str]:
        return self._names

    def _portfolio_stats(self, weights: np.ndarray) -> tuple[float, float, float]:
        """計算組合的 (return, volatility, sharpe)."""
        ret = np.dot(weights, self._mean_returns)
        vol = math.sqrt(np.dot(weights.T, np.dot(self._cov_matrix, weights)))
        sharpe = (ret - self._rf_daily * self._ann_factor) / vol if vol > 0 else 0
        return ret, vol, sharpe

    def _risk_contributions(self, weights: np.ndarray) -> np.ndarray:
        """計算各資產的風險貢獻."""
        cov_w = np.dot(self._cov_matrix, weights)
        port_vol = math.sqrt(np.dot(weights, cov_w))
        if port_vol == 0:
            return np.zeros(self._n_assets)
        marginal_risk = cov_w / port_vol
        return weights * marginal_risk / port_vol

    def _to_dict(self, weights: np.ndarray) -> PortfolioResult:
        """將權重 array 轉為 PortfolioResult."""
        ret, vol, sharpe = self._portfolio_stats(weights)
        rc = self._risk_contributions(weights)
        return PortfolioResult(
            weights={self._names[i]: float(weights[i]) for i in range(self._n_assets)},
            expected_return=ret,
            volatility=vol,
            sharpe_ratio=sharpe,
            risk_contributions={self._names[i]: float(rc[i]) for i in range(self._n_assets)},
        )

    def equal_weight(self) -> PortfolioResult:
        """等權重組合."""
        w = np.ones(self._n_assets) / self._n_assets
        return self._to_dict(w)

    def min_variance(self) -> PortfolioResult:
        """最小方差組合."""
        if not HAS_SCIPY:
            return self._min_variance_analytical()

        def neg_sharpe_obj(w):
            return np.dot(w.T, np.dot(self._cov_matrix, w))

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0, 1)] * self._n_assets
        x0 = np.ones(self._n_assets) / self._n_assets

        result = minimize(
            neg_sharpe_obj,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        return self._to_dict(result.x)

    def _min_variance_analytical(self) -> PortfolioResult:
        """解析解最小方差（無 scipy fallback）."""
        cov_inv = np.linalg.pinv(self._cov_matrix)
        ones = np.ones(self._n_assets)
        w = cov_inv @ ones / (ones @ cov_inv @ ones)
        w = np.maximum(w, 0)
        w /= w.sum()
        return self._to_dict(w)

    def max_sharpe(self) -> PortfolioResult:
        """最大 Sharpe 比率組合."""
        if not HAS_SCIPY:
            return self._max_sharpe_grid()

        def neg_sharpe(w):
            ret, vol, _ = self._portfolio_stats(w)
            return -(ret - self._rf_daily * self._ann_factor) / vol if vol > 0 else 0

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0, 1)] * self._n_assets
        x0 = np.ones(self._n_assets) / self._n_assets

        result = minimize(
            neg_sharpe,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        return self._to_dict(result.x)

    def _max_sharpe_grid(self, n_samples: int = 10000) -> PortfolioResult:
        """網格搜索最大 Sharpe（無 scipy fallback）."""
        best_sharpe = -np.inf
        best_w = np.ones(self._n_assets) / self._n_assets
        rng = np.random.default_rng(42)

        for _ in range(n_samples):
            w = rng.dirichlet(np.ones(self._n_assets))
            _, _, sharpe = self._portfolio_stats(w)
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_w = w

        return self._to_dict(best_w)

    def risk_parity(self) -> PortfolioResult:
        """
        風險平價組合 (Equal Risk Contribution).
        每個資產對總風險的貢獻相同.
        """
        if not HAS_SCIPY:
            return self._risk_parity_iterative()

        def risk_budget_obj(w):
            rc = self._risk_contributions(w)
            target = 1.0 / self._n_assets
            return np.sum((rc - target) ** 2)

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0.001, 1)] * self._n_assets
        x0 = np.ones(self._n_assets) / self._n_assets

        result = minimize(
            risk_budget_obj,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        return self._to_dict(result.x)

    def _risk_parity_iterative(self, max_iter: int = 500, tol: float = 1e-10) -> PortfolioResult:
        """迭代法風險平價（無 scipy fallback）."""
        w = np.ones(self._n_assets) / self._n_assets
        for _ in range(max_iter):
            cov_w = self._cov_matrix @ w
            sigma = math.sqrt(w @ cov_w)
            if sigma == 0:
                break
            mrc = cov_w / sigma
            w = 1.0 / (self._n_assets * mrc)
            w = w / w.sum()
            # 檢查收斂
            rc = self._risk_contributions(w)
            target = 1.0 / self._n_assets
            if np.max(np.abs(rc - target)) < tol:
                break
        return self._to_dict(w)

    def efficient_frontier(self, n_points: int = 50) -> list[FrontierPoint]:
        """
        計算有效前沿.

        Returns:
            FrontierPoint 列表，按目標報酬排序.
        """
        min_ret = np.min(self._mean_returns)
        max_ret = np.max(self._mean_returns)
        target_returns = np.linspace(min_ret, max_ret, n_points)

        points: list[FrontierPoint] = []
        for target in target_returns:
            try:
                if HAS_SCIPY:
                    result = self._optimize_for_return(target)
                    if result is not None:
                        ret, vol, sharpe = self._portfolio_stats(result)
                        points.append(FrontierPoint(
                            target_return=float(target),
                            volatility=float(vol),
                            sharpe_ratio=float(sharpe),
                            weights={self._names[i]: float(result[i]) for i in range(self._n_assets)},
                        ))
                else:
                    # Fallback: 隨機採樣
                    rng = np.random.default_rng(42)
                    best_vol = np.inf
                    best_w = None
                    for _ in range(5000):
                        w = rng.dirichlet(np.ones(self._n_assets))
                        ret, vol, _ = self._portfolio_stats(w)
                        if abs(ret - target) < (max_ret - min_ret) * 0.02 and vol < best_vol:
                            best_vol = vol
                            best_w = w
                    if best_w is not None:
                        ret, vol, sharpe = self._portfolio_stats(best_w)
                        points.append(FrontierPoint(
                            target_return=float(target),
                            volatility=float(vol),
                            sharpe_ratio=float(sharpe),
                            weights={self._names[i]: float(best_w[i]) for i in range(self._n_assets)},
                        ))
            except Exception:
                continue

        return points

    def _optimize_for_return(self, target_return: float) -> np.ndarray | None:
        """最小化波動率，同時滿足目標報酬."""
        def objective(w):
            return np.dot(w.T, np.dot(self._cov_matrix, w))

        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, t=target_return: np.dot(w, self._mean_returns) - t},
        ]
        bounds = [(0, 1)] * self._n_assets
        x0 = np.ones(self._n_assets) / self._n_assets

        result = minimize(
            objective, x0,
            method="SLSQP", bounds=bounds, constraints=constraints,
            options={"maxiter": 500, "ftol": 1e-12},
        )
        return result.x if result.success else None

    def black_litterman(
        self,
        market_cap_weights: np.ndarray,
        views: dict[str, float],
        tau: float = 0.05,
        view_confidence: float = 0.5,
    ) -> PortfolioResult:
        """
        Black-Litterman 模型.

        結合市場均衡（先驗）與投資者觀點（後驗）.

        Args:
            market_cap_weights: 市值加權權重（市場均衡）
            views: 主觀觀點，如 {"AAPL": 0.05, "GOOGL": -0.02} 表示超配/低配
            tau: 不確定性參數（通常 0.025 ~ 0.1）
            view_confidence: 觀點信心度 (0~1)
        """
        # 市場均衡隱含報酬 (reverse optimization)
        risk_aversion = 3.0  # 典型值
        pi = risk_aversion * np.dot(self._cov_matrix, market_cap_weights)

        # 構建觀點矩陣 P 和觀點報酬 Q
        n_views = len(views)
        P = np.zeros((n_views, self._n_assets))
        Q = np.zeros(n_views)
        view_asset_map = {name: i for i, name in enumerate(self._names)}

        for i, (asset, view_return) in enumerate(views.items()):
            if asset in view_asset_map:
                idx = view_asset_map[asset]
                P[i, idx] = 1.0
                Q[i] = view_return

        # 觀點不確定性矩陣 Omega
        omega = np.diag(np.diag(tau * P @ self._cov_matrix @ P.T)) / view_confidence

        # Black-Litterman 公式
        tau_cov = tau * self._cov_matrix
        tau_cov_inv = np.linalg.pinv(tau_cov)
        omega_inv = np.linalg.pinv(omega)

        # 後驗報酬
        posterior_cov_inv = tau_cov_inv + P.T @ omega_inv @ P
        posterior_cov = np.linalg.pinv(posterior_cov_inv)
        posterior_mean = posterior_cov @ (tau_cov_inv @ pi + P.T @ omega_inv @ Q)

        # 用後驗分佈計算最優組合
        w = np.linalg.pinv(posterior_cov) @ posterior_mean / risk_aversion
        w = np.maximum(w, 0)
        w /= w.sum()

        # 更新 mean_returns 以反映後驗
        old_mean = self._mean_returns.copy()
        self._mean_returns = posterior_mean
        result = self._to_dict(w)
        self._mean_returns = old_mean

        return result
