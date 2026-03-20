"""
現代投資組合優化引擎
======================
支援：Markowitz 均值-方差、風險平價、Black-Litterman、有效前沿

v6.0 新增功能
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class PortfolioResult:
    """投資組合優化結果。"""

    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    allocation: dict[str, float]  # 每個資產的金額分配


def _annualize_return(returns: np.ndarray, periods_per_year: int = 252) -> float:
    """年化收益率。"""
    cum_return = np.prod(1 + returns) - 1
    n_periods = len(returns)
    if n_periods == 0:
        return 0.0
    return (1 + cum_return) ** (periods_per_year / n_periods) - 1


def _annualize_volatility(returns: np.ndarray, periods_per_year: int = 252) -> float:
    """年化波動率。"""
    return returns.std() * np.sqrt(periods_per_year)


def mean_variance_optimize(
    returns_matrix: dict[str, list[float]],
    risk_free_rate: float = 0.04,
    target_return: float | None = None,
    max_weight: float = 0.4,
) -> PortfolioResult:
    """
    Markowitz 均值-方差優化。

    Args:
        returns_matrix: {asset_name: [daily_returns...]}
        risk_free_rate: 無風險利率（年化）
        target_return: 目標收益率（None = 最大夏普）
        max_weight: 單一資產最大權重

    Returns:
        PortfolioResult with optimal weights
    """
    assets = list(returns_matrix.keys())
    n = len(assets)
    if n < 2:
        raise ValueError("至少需要 2 個資產進行優化")

    # 構建收益率矩陣
    ret_arrays = [np.array(returns_matrix[a], dtype=np.float64) for a in assets]
    min_len = min(len(r) for r in ret_arrays)
    ret_matrix = np.column_stack([r[:min_len] for r in ret_arrays])

    # 年化統計量
    mean_returns = np.array([_annualize_return(ret_matrix[:, i]) for i in range(n)])
    cov_matrix = np.cov(ret_matrix, rowvar=False) * 252  # 年化協方差

    # 簡化版優化：使用解析解（最大夏普）
    daily_rf = risk_free_rate / 252
    excess = mean_returns - risk_free_rate

    try:
        inv_cov = np.linalg.inv(cov_matrix)
        raw_weights = inv_cov @ excess
        weights = raw_weights / raw_weights.sum()

        # 應用權重限制
        weights = np.clip(weights, 0, max_weight)
        weights = weights / weights.sum()  # 重新正規化
    except np.linalg.LinAlgError:
        # 協方差矩陣奇異時，使用等權重
        weights = np.ones(n) / n

    weight_dict = {assets[i]: round(float(weights[i]), 4) for i in range(n)}

    port_return = float(weights @ mean_returns)
    port_vol = float(np.sqrt(weights @ cov_matrix @ weights))
    sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else 0

    return PortfolioResult(
        weights=weight_dict,
        expected_return=round(port_return, 4),
        volatility=round(port_vol, 4),
        sharpe_ratio=round(sharpe, 4),
        allocation={},  # 可由外部根據總資金計算
    )


def risk_parity(
    returns_matrix: dict[str, list[float]],
    risk_free_rate: float = 0.04,
) -> PortfolioResult:
    """
    風險平價配置：使每個資產對組合總風險的貢獻相等。

    Args:
        returns_matrix: {asset_name: [daily_returns...]}
        risk_free_rate: 無風險利率（年化）
    """
    assets = list(returns_matrix.keys())
    n = len(assets)
    if n < 2:
        raise ValueError("至少需要 2 個資產")

    ret_arrays = [np.array(returns_matrix[a], dtype=np.float64) for a in assets]
    min_len = min(len(r) for r in ret_arrays)
    ret_matrix = np.column_stack([r[:min_len] for r in ret_arrays])
    mean_returns = np.array([_annualize_return(ret_matrix[:, i]) for i in range(n)])
    cov_matrix = np.cov(ret_matrix, rowvar=False) * 252

    # 風險平價迭代求解
    w = np.ones(n) / n
    for _ in range(100):
        port_vol = np.sqrt(w @ cov_matrix @ w)
        if port_vol == 0:
            break
        mrc = cov_matrix @ w / port_vol  # 邊際風險貢獻
        rc = w * mrc  # 風險貢獻
        target_rc = port_vol / n
        w = w * (target_rc / (rc + 1e-10))
        w = np.maximum(w, 0)
        w = w / w.sum()

    weight_dict = {assets[i]: round(float(w[i]), 4) for i in range(n)}
    port_return = float(w @ mean_returns)
    port_vol = float(np.sqrt(w @ cov_matrix @ w))
    sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else 0

    return PortfolioResult(
        weights=weight_dict,
        expected_return=round(port_return, 4),
        volatility=round(port_vol, 4),
        sharpe_ratio=round(sharpe, 4),
        allocation={},
    )


def efficient_frontier(
    returns_matrix: dict[str, list[float]],
    n_points: int = 50,
    risk_free_rate: float = 0.04,
    max_weight: float = 0.5,
) -> list[dict[str, Any]]:
    """
    計算有效前沿上的點。

    Returns:
        [{"return": float, "volatility": float, "sharpe": float, "weights": {...}}, ...]
    """
    assets = list(returns_matrix.keys())
    n = len(assets)

    ret_arrays = [np.array(returns_matrix[a], dtype=np.float64) for a in assets]
    min_len = min(len(r) for r in ret_arrays)
    ret_matrix = np.column_stack([r[:min_len] for r in ret_arrays])
    mean_returns = np.array([_annualize_return(ret_matrix[:, i]) for i in range(n)])
    cov_matrix = np.cov(ret_matrix, rowvar=False) * 252

    # 隨機權重組合生成有效前沿近似
    results = []
    rng = np.random.default_rng(42)
    for _ in range(n_points * 100):
        w = rng.dirichlet(np.ones(n))
        if w.max() > max_weight:
            continue
        port_ret = float(w @ mean_returns)
        port_vol = float(np.sqrt(w @ cov_matrix @ w))
        sharpe = (port_ret - risk_free_rate) / port_vol if port_vol > 0 else 0
        results.append(
            {
                "return": round(port_ret, 4),
                "volatility": round(port_vol, 4),
                "sharpe": round(sharpe, 4),
                "weights": {assets[i]: round(float(w[i]), 4) for i in range(n)},
            }
        )

    # 按波動率排序並取 n_points 個均勻分佈的點
    results.sort(key=lambda x: x["volatility"])
    if len(results) <= n_points:
        return results
    step = len(results) // n_points
    return results[::step][:n_points]


def calculate_var(
    returns: list[float],
    confidence: float = 0.95,
    method: str = "historical",
) -> float:
    """
    計算 Value at Risk (VaR)。

    Args:
        returns: 日收益率序列
        confidence: 信心水準（0.95 = 95%）
        method: "historical" | "parametric"
    """
    arr = np.array(returns, dtype=np.float64)
    if len(arr) < 10:
        return 0.0

    if method == "historical":
        return round(float(np.percentile(arr, (1 - confidence) * 100)), 6)
    else:
        # 參數法（假設常態分佈）
        mu, sigma = arr.mean(), arr.std()
        from scipy import stats

        z = stats.norm.ppf(1 - confidence)
        return round(float(mu + z * sigma), 6)


def calculate_cvar(returns: list[float], confidence: float = 0.95) -> float:
    """
    計算 Conditional VaR (CVaR / Expected Shortfall)。
    """
    arr = np.array(returns, dtype=np.float64)
    var = calculate_var(returns, confidence, method="historical")
    tail = arr[arr <= var]
    if len(tail) == 0:
        return var
    return round(float(tail.mean()), 6)


def calculate_max_drawdown(equity_curve: list[float]) -> dict[str, float]:
    """
    計算最大回撤及相關指標。

    Returns:
        {"max_drawdown": float, "max_dd_duration": int, "peak": float, "trough": float}
    """
    arr = np.array(equity_curve, dtype=np.float64)
    if len(arr) < 2:
        return {"max_drawdown": 0.0, "max_dd_duration": 0, "peak": 0.0, "trough": 0.0}

    peak = np.maximum.accumulate(arr)
    drawdown = (arr - peak) / peak
    max_dd = float(drawdown.min())
    max_dd_idx = int(drawdown.argmin())

    # 計算最大回撤持續時間
    peak_idx = int(np.argmax(arr[: max_dd_idx + 1]))
    # 找回撤結束（創新高）的時間
    recovery_idx = max_dd_idx
    for i in range(max_dd_idx, len(arr)):
        if arr[i] >= peak[peak_idx]:
            recovery_idx = i
            break
    else:
        recovery_idx = len(arr) - 1

    duration = recovery_idx - peak_idx

    return {
        "max_drawdown": round(max_dd, 6),
        "max_dd_duration": duration,
        "peak": round(float(peak[peak_idx]), 2),
        "trough": round(float(arr[max_dd_idx]), 2),
    }
