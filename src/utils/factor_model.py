"""
多因子模型 — Fama-French 風格因子歸因 & Alpha/Beta 分解

功能：
- Fama-French 3 因子模型 (Market, Size, Value)
- Alpha / Beta 計算與統計顯著性檢定
- 因子暴露分析 (Factor Exposure)
- 迴歸歸因 (Regression Attribution)
- 特徵工程管道 (自動生成因子特徵)

用法：
    from src.utils.factor_model import FactorModel

    model = FactorModel(asset_returns, factor_returns)
    result = model.fit()
    print(result.alpha, result.beta, result.r_squared)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class FactorResult:
    """因子模型迴歸結果."""

    alpha: float  # 年化 Alpha
    alpha_tstat: float  # Alpha t-statistic
    beta: dict[str, float]  # 各因子 Beta
    r_squared: float
    adj_r_squared: float
    residual_vol: float  # 殘差波動率（年化）
    tracking_error: float  # 追蹤誤差（年化）
    information_ratio: float
    factor_contributions: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alpha_pct": round(self.alpha * 100, 4),
            "alpha_tstat": round(self.alpha_tstat, 3),
            "alpha_significant": abs(self.alpha_tstat) > 1.96,
            "beta": {k: round(v, 4) for k, v in self.beta.items()},
            "r_squared": round(self.r_squared, 4),
            "adj_r_squared": round(self.adj_r_squared, 4),
            "residual_vol_pct": round(self.residual_vol * 100, 2),
            "tracking_error_pct": round(self.tracking_error * 100, 2),
            "information_ratio": round(self.information_ratio, 3),
            "factor_contributions": {k: round(v * 100, 4) for k, v in self.factor_contributions.items()},
        }


class FactorModel:
    """
    多因子模型.

    Args:
        asset_returns: 資產日報酬率 (n_days,)
        factor_returns: 因子日報酬率 DataFrame/ndarray (n_days, n_factors)
        factor_names: 因子名稱
        annualization_factor: 年化因子，預設 252
    """

    def __init__(
        self,
        asset_returns: np.ndarray,
        factor_returns: np.ndarray,
        factor_names: list[str] | None = None,
        annualization_factor: int = 252,
    ) -> None:
        self._y = np.asarray(asset_returns, dtype=np.float64).flatten()
        if factor_returns.ndim == 1:
            factor_returns = factor_returns.reshape(-1, 1)
        self._X = np.asarray(factor_returns, dtype=np.float64)
        self._n_days = len(self._y)
        self._n_factors = self._X.shape[1]
        self._names = factor_names or [f"Factor_{i}" for i in range(self._n_factors)]
        self._ann = annualization_factor

    def fit(self) -> FactorResult:
        """
        OLS 迴歸: asset_return = alpha + beta1*factor1 + beta2*factor2 + ... + epsilon
        """
        # 加入截距項
        X = np.column_stack([np.ones(self._n_days), self._X])
        n_params = X.shape[1]

        # OLS: (X'X)^-1 X'y
        XtX = X.T @ X
        XtX_inv = np.linalg.pinv(XtX)
        beta_hat = XtX_inv @ X.T @ self._y

        alpha_daily = beta_hat[0]
        betas = beta_hat[1:]

        # 預測值與殘差
        y_pred = X @ beta_hat
        residuals = self._y - y_pred
        n = self._n_days
        p = n_params

        # 殘差標準誤
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((self._y - np.mean(self._y)) ** 2)
        mse = ss_res / (n - p) if n > p else 0

        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p) if n > p else 0

        # Alpha t-statistic
        se_alpha = math.sqrt(mse * XtX_inv[0, 0]) if mse > 0 else 0
        alpha_tstat = alpha_daily / se_alpha if se_alpha > 0 else 0

        # 殘差波動率 & 追蹤誤差
        residual_vol = math.sqrt(np.var(residuals, ddof=1)) * math.sqrt(self._ann)
        tracking_error = residual_vol

        # Information Ratio
        alpha_annual = alpha_daily * self._ann
        ir = alpha_annual / tracking_error if tracking_error > 0 else 0

        # 因子貢獻 = beta * factor_mean_return
        factor_means = np.mean(self._X, axis=0) * self._ann
        factor_contributions = {self._names[i]: float(betas[i] * factor_means[i]) for i in range(self._n_factors)}

        return FactorResult(
            alpha=float(alpha_annual),
            alpha_tstat=float(alpha_tstat),
            beta={self._names[i]: float(betas[i]) for i in range(self._n_factors)},
            r_squared=float(r_squared),
            adj_r_squared=float(adj_r_squared),
            residual_vol=float(residual_vol),
            tracking_error=float(tracking_error),
            information_ratio=float(ir),
            factor_contributions=factor_contributions,
        )

    def rolling_beta(self, window: int = 60) -> dict[str, list[float]]:
        """
        滾動窗口 Beta 估計.

        Returns:
            {factor_name: [beta_t1, beta_t2, ...]}
        """
        result: dict[str, list[float]] = {name: [] for name in self._names}
        result["alpha"] = []

        for i in range(window, self._n_days):
            y_window = self._y[i - window : i]
            X_window = self._X[i - window : i]
            X_aug = np.column_stack([np.ones(window), X_window])

            try:
                XtX_inv = np.linalg.pinv(X_aug.T @ X_aug)
                beta_hat = XtX_inv @ X_aug.T @ y_window
                result["alpha"].append(float(beta_hat[0]))
                for j, name in enumerate(self._names):
                    result[name].append(float(beta_hat[j + 1]))
            except np.linalg.LinAlgError:
                result["alpha"].append(0.0)
                for name in self._names:
                    result[name].append(0.0)

        return result


# ════════════════════════════════════════════════════════════
# Fama-French 3 因子構建器
# ════════════════════════════════════════════════════════════


def build_fama_french_factors(
    returns_matrix: np.ndarray,
    market_caps: np.ndarray,
    book_to_market: np.ndarray,
) -> dict[str, np.ndarray]:
    """
    從股票報酬率構建 Fama-French 3 因子.

    Args:
        returns_matrix: (n_days, n_stocks) 各股票日報酬
        market_caps: (n_stocks,) 各股票市值
        book_to_market: (n_stocks,) 各股票 B/M ratio

    Returns:
        {"MKT": ..., "SMB": ..., "HML": ...}
    """
    n_days, n_stocks = returns_matrix.shape

    # MKT: 市值加權市場報酬 - 無風險利率（簡化為等權）
    market_return = np.mean(returns_matrix, axis=1)

    # Size 分組: 小盤 vs 大盤
    median_cap = np.median(market_caps)
    small_mask = market_caps < median_cap
    big_mask = ~small_mask

    # Value 分組: 高 B/M vs 低 B/M
    median_bm = np.median(book_to_market)
    value_mask = book_to_market >= median_bm
    growth_mask = ~value_mask

    # SMB = Small - Big
    small_ret = np.mean(returns_matrix[:, small_mask], axis=1) if np.any(small_mask) else np.zeros(n_days)
    big_ret = np.mean(returns_matrix[:, big_mask], axis=1) if np.any(big_mask) else np.zeros(n_days)
    smb = small_ret - big_ret

    # HML = High B/M - Low B/M
    value_ret = np.mean(returns_matrix[:, value_mask], axis=1) if np.any(value_mask) else np.zeros(n_days)
    growth_ret = np.mean(returns_matrix[:, growth_mask], axis=1) if np.any(growth_mask) else np.zeros(n_days)
    hml = value_ret - growth_ret

    return {
        "MKT": market_return,
        "SMB": smb,
        "HML": hml,
    }


# ════════════════════════════════════════════════════════════
# 特徵工程管道
# ════════════════════════════════════════════════════════════


def generate_factor_features(
    returns: np.ndarray,
    lookback_windows: list[int] | None = None,
) -> dict[str, np.ndarray]:
    """
    自動生成因子特徵.

    Args:
        returns: 日報酬率 (n_days,)
        lookback_windows: 回看窗口列表

    Returns:
        {feature_name: feature_values}
    """
    if lookback_windows is None:
        lookback_windows = [5, 10, 20, 60]

    features: dict[str, np.ndarray] = {}
    n = len(returns)

    for w in lookback_windows:
        if w >= n:
            continue

        # 動量 (Momentum): 過去 w 天累積報酬
        momentum = np.full(n, np.nan)
        for i in range(w, n):
            momentum[i] = np.prod(1 + returns[i - w : i]) - 1
        features[f"momentum_{w}d"] = momentum

        # 波動率 (Volatility): 過去 w 天報酬標準差
        vol = np.full(n, np.nan)
        for i in range(w, n):
            vol[i] = np.std(returns[i - w : i], ddof=1)
        features[f"volatility_{w}d"] = vol

        # 偏度 (Skewness)
        skew = np.full(n, np.nan)
        for i in range(w, n):
            r = returns[i - w : i]
            m = np.mean(r)
            s = np.std(r, ddof=1)
            if s > 0:
                skew[i] = np.mean(((r - m) / s) ** 3)
        features[f"skewness_{w}d"] = skew

        # 峰度 (Kurtosis)
        kurt = np.full(n, np.nan)
        for i in range(w, n):
            r = returns[i - w : i]
            m = np.mean(r)
            s = np.std(r, ddof=1)
            if s > 0:
                kurt[i] = np.mean(((r - m) / s) ** 4) - 3
        features[f"kurtosis_{w}d"] = kurt

        # 最大回撤
        max_dd = np.full(n, np.nan)
        for i in range(w, n):
            cum = np.cumprod(1 + returns[i - w : i])
            peak = np.maximum.accumulate(cum)
            dd = (peak - cum) / peak
            max_dd[i] = np.max(dd)
        features[f"max_drawdown_{w}d"] = max_dd

        # 正報酬天數佔比
        pos_ratio = np.full(n, np.nan)
        for i in range(w, n):
            pos_ratio[i] = np.mean(returns[i - w : i] > 0)
        features[f"positive_ratio_{w}d"] = pos_ratio

    return features
