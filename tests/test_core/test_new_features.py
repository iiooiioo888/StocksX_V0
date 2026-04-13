"""
測試新功能模組 — 向量化策略、投資組合優化、因子模型、狀態檢測
"""

from __future__ import annotations

import math

import numpy as np
import pytest

# ════════════════════════════════════════════════════════════
# 向量化策略測試
# ════════════════════════════════════════════════════════════

class TestVectorizedStrategies:
    """測試向量化策略引擎."""

    @pytest.fixture
    def sample_rows(self):
        """生成樣本 K 線數據."""
        np.random.seed(42)
        n = 200
        base_price = 100.0
        prices = base_price + np.cumsum(np.random.randn(n) * 0.5)
        prices = np.maximum(prices, 10)  # 確保正數

        rows = []
        for i, p in enumerate(prices):
            rows.append(
                {
                    "timestamp": i * 3600000,
                    "open": float(p),
                    "high": float(p + abs(np.random.randn() * 0.3)),
                    "low": float(p - abs(np.random.randn() * 0.3)),
                    "close": float(p + np.random.randn() * 0.1),
                    "volume": float(abs(np.random.randn() * 1000) + 100),
                }
            )
        return rows

    def test_sma_cross_returns_correct_length(self, sample_rows):
        from src.backtest.strategies_vectorized import sma_cross_vec

        signals = sma_cross_vec(sample_rows, fast=10, slow=30)
        assert len(signals) == len(sample_rows)
        assert all(s in (-1, 0, 1) for s in signals)

    def test_rsi_signal_returns_correct_length(self, sample_rows):
        from src.backtest.strategies_vectorized import rsi_signal_vec

        signals = rsi_signal_vec(sample_rows, period=14)
        assert len(signals) == len(sample_rows)
        assert all(s in (-1, 0, 1) for s in signals)

    def test_macd_cross_returns_correct_length(self, sample_rows):
        from src.backtest.strategies_vectorized import macd_cross_vec

        signals = macd_cross_vec(sample_rows)
        assert len(signals) == len(sample_rows)

    def test_bollinger_signal_returns_correct_length(self, sample_rows):
        from src.backtest.strategies_vectorized import bollinger_signal_vec

        signals = bollinger_signal_vec(sample_rows)
        assert len(signals) == len(sample_rows)

    def test_buy_and_hold(self):
        from src.backtest.strategies_vectorized import buy_and_hold_vec

        rows = [{"close": 100}] * 10
        signals = buy_and_hold_vec(rows)
        assert signals == [1] * 10

    def test_empty_rows(self):
        from src.backtest.strategies_vectorized import sma_cross_vec, rsi_signal_vec

        assert sma_cross_vec([]) == []
        assert rsi_signal_vec([]) == []

    def test_insufficient_data(self):
        from src.backtest.strategies_vectorized import sma_cross_vec

        rows = [{"close": 100}] * 5
        signals = sma_cross_vec(rows, fast=10, slow=30)
        assert signals == [0] * 5

    def test_vectorized_matches_original_sma(self, sample_rows):
        """驗證向量化版本與原版邏輯一致."""
        from src.backtest.strategies import sma_cross as sma_original
        from src.backtest.strategies_vectorized import sma_cross_vec

        original = sma_original(sample_rows, fast=10, slow=30)
        vectorized = sma_cross_vec(sample_rows, fast=10, slow=30)
        assert original == vectorized

    def test_vectorized_matches_original_rsi(self, sample_rows):
        """驗證向量化 RSI 與原版邏輯一致."""
        from src.backtest.strategies import rsi_signal as rsi_original
        from src.backtest.strategies_vectorized import rsi_signal_vec

        original = rsi_original(sample_rows, period=14)
        vectorized = rsi_signal_vec(sample_rows, period=14)
        assert original == vectorized

    def test_get_vectorized_signal(self, sample_rows):
        from src.backtest.strategies_vectorized import get_vectorized_signal

        signals = get_vectorized_signal("sma_cross", sample_rows, fast=10, slow=30)
        assert len(signals) == len(sample_rows)

        unknown = get_vectorized_signal("unknown_strategy", sample_rows)
        assert unknown == [0] * len(sample_rows)

# ════════════════════════════════════════════════════════════
# 投資組合優化測試
# ════════════════════════════════════════════════════════════

class TestPortfolioOptimizer:
    """測試投資組合優化器."""

    @pytest.fixture
    def sample_returns(self):
        np.random.seed(42)
        n_days = 252
        n_assets = 5
        returns = np.random.randn(n_days, n_assets) * 0.02 + 0.0005
        names = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        return returns, names

    def test_equal_weight(self, sample_returns):
        from src.utils.portfolio_optimizer import PortfolioOptimizer

        returns, names = sample_returns
        opt = PortfolioOptimizer(returns, names)
        result = opt.equal_weight()

        assert len(result.weights) == 5
        assert abs(sum(result.weights.values()) - 1.0) < 1e-6
        assert result.expected_return != 0
        assert result.volatility > 0

    def test_max_sharpe(self, sample_returns):
        from src.utils.portfolio_optimizer import PortfolioOptimizer

        returns, names = sample_returns
        opt = PortfolioOptimizer(returns, names)
        result = opt.max_sharpe()

        assert len(result.weights) == 5
        assert abs(sum(result.weights.values()) - 1.0) < 1e-4
        assert result.sharpe_ratio > 0

    def test_min_variance(self, sample_returns):
        from src.utils.portfolio_optimizer import PortfolioOptimizer

        returns, names = sample_returns
        opt = PortfolioOptimizer(returns, names)
        result = opt.min_variance()

        # 最小方差組合的波動率應該 <= 等權重
        eq = opt.equal_weight()
        assert result.volatility <= eq.volatility + 1e-6

    def test_risk_parity(self, sample_returns):
        from src.utils.portfolio_optimizer import PortfolioOptimizer

        returns, names = sample_returns
        opt = PortfolioOptimizer(returns, names)
        result = opt.risk_parity()

        assert len(result.risk_contributions) == 5
        # 風險貢獻應該大致相等
        rc_values = list(result.risk_contributions.values())
        if all(v > 0 for v in rc_values):
            expected_rc = 1.0 / 5
            for v in rc_values:
                assert abs(v - expected_rc) < 0.05  # 5% tolerance

    def test_efficient_frontier(self, sample_returns):
        from src.utils.portfolio_optimizer import PortfolioOptimizer

        returns, names = sample_returns
        opt = PortfolioOptimizer(returns, names)
        frontier = opt.efficient_frontier(n_points=10)

        assert len(frontier) > 0
        # 波動率應該大致遞增
        vols = [p.volatility for p in frontier]
        assert vols == sorted(vols) or len(vols) < 3  # 允許少量例外

    def test_to_dict(self, sample_returns):
        from src.utils.portfolio_optimizer import PortfolioOptimizer

        returns, names = sample_returns
        opt = PortfolioOptimizer(returns, names)
        result = opt.max_sharpe()
        d = result.to_dict()

        assert "weights" in d
        assert "expected_return_pct" in d
        assert "volatility_pct" in d
        assert "sharpe_ratio" in d

    def test_single_asset(self):
        from src.utils.portfolio_optimizer import PortfolioOptimizer

        returns = np.random.randn(100) * 0.02
        opt = PortfolioOptimizer(returns, ["SPY"])
        result = opt.equal_weight()
        assert result.weights["SPY"] == 1.0

# ════════════════════════════════════════════════════════════
# 因子模型測試
# ════════════════════════════════════════════════════════════

class TestFactorModel:
    """測試因子模型."""

    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n_days = 252
        # 因子報酬
        market = np.random.randn(n_days) * 0.01 + 0.0003
        smb = np.random.randn(n_days) * 0.005
        hml = np.random.randn(n_days) * 0.005
        factors = np.column_stack([market, smb, hml])

        # 資產報酬 = alpha + beta * market + noise
        alpha = 0.0002
        asset = alpha + 1.2 * market + 0.3 * smb - 0.1 * hml + np.random.randn(n_days) * 0.005

        return asset, factors, ["MKT", "SMB", "HML"]

    def test_fit_returns_result(self, sample_data):
        from src.utils.factor_model import FactorModel

        asset, factors, names = sample_data
        model = FactorModel(asset, factors, names)
        result = model.fit()

        assert len(result.beta) == 3
        assert result.r_squared > 0.3  # 有解釋力
        assert "MKT" in result.beta

    def test_alpha_positive_for_positive_signal(self, sample_data):
        from src.utils.factor_model import FactorModel

        asset, factors, names = sample_data
        model = FactorModel(asset, factors, names)
        result = model.fit()

        # 因為構造時 alpha > 0，應該能估出正 alpha
        assert result.alpha > 0

    def test_market_beta_close_to_true(self, sample_data):
        from src.utils.factor_model import FactorModel

        asset, factors, names = sample_data
        model = FactorModel(asset, factors, names)
        result = model.fit()

        # 市場 Beta 應該接近 1.2
        assert 0.8 < result.beta["MKT"] < 1.6

    def test_to_dict(self, sample_data):
        from src.utils.factor_model import FactorModel

        asset, factors, names = sample_data
        result = FactorModel(asset, factors, names).fit()
        d = result.to_dict()

        assert "alpha_pct" in d
        assert "beta" in d
        assert "r_squared" in d

    def test_rolling_beta(self, sample_data):
        from src.utils.factor_model import FactorModel

        asset, factors, names = sample_data
        model = FactorModel(asset, factors, names)
        rolling = model.rolling_beta(window=60)

        assert "MKT" in rolling
        assert "alpha" in rolling
        assert len(rolling["MKT"]) > 0

    def test_generate_factor_features(self):
        from src.utils.factor_model import generate_factor_features

        np.random.seed(42)
        returns = np.random.randn(100) * 0.02
        features = generate_factor_features(returns, lookback_windows=[5, 20])

        assert "momentum_5d" in features
        assert "volatility_20d" in features
        assert len(features["momentum_5d"]) == 100

# ════════════════════════════════════════════════════════════
# 市場狀態檢測測試
# ════════════════════════════════════════════════════════════

class TestRegimeDetection:
    """測試市場狀態檢測."""

    @pytest.fixture
    def trending_returns(self):
        """構造一個牛市序列."""
        np.random.seed(42)
        bull = np.random.randn(100) * 0.01 + 0.002
        bear = np.random.randn(100) * 0.015 - 0.003
        return np.concatenate([bull, bear])

    def test_detect_returns_result(self, trending_returns):
        from src.utils.regime_detection import RegimeDetector

        detector = RegimeDetector(trending_returns)
        result = detector.detect()

        assert len(result.regimes) == len(trending_returns)
        assert len(result.stats) == 4  # 4 種狀態
        assert result.confidence >= 0

    def test_regime_distribution_sums_to_one(self, trending_returns):
        from src.utils.regime_detection import RegimeDetector

        result = RegimeDetector(trending_returns).detect()
        total_pct = sum(s.pct for s in result.stats)
        assert abs(total_pct - 1.0) < 1e-6

    def test_transition_matrix(self, trending_returns):
        from src.utils.regime_detection import RegimeDetector

        result = RegimeDetector(trending_returns).detect()

        # 每行的轉移概率之和應該為 1
        for transitions in result.transition_matrix.values():
            total = sum(transitions.values())
            if total > 0:
                assert abs(total - 1.0) < 0.05

    def test_to_dict(self, trending_returns):
        from src.utils.regime_detection import RegimeDetector

        result = RegimeDetector(trending_returns).detect()
        d = result.to_dict()

        assert "current_regime" in d
        assert "regime_distribution" in d
        assert "transition_matrix" in d

    def test_current_regime(self, trending_returns):
        from src.utils.regime_detection import RegimeDetector, Regime

        detector = RegimeDetector(trending_returns)
        regime = detector.current_regime()
        assert isinstance(regime, Regime)

    def test_kmeans_method(self, trending_returns):
        from src.utils.regime_detection import RegimeDetector

        result = RegimeDetector(trending_returns).detect(method="kmeans")
        assert len(result.regimes) == len(trending_returns)

    def test_short_series(self):
        from src.utils.regime_detection import RegimeDetector

        returns = np.random.randn(10) * 0.01
        result = RegimeDetector(returns).detect()
        assert result.current_regime is not None

# ════════════════════════════════════════════════════════════
# 風險分析測試
# ════════════════════════════════════════════════════════════

class TestRiskAnalyzer:
    """測試優化後的風險分析器."""

    @pytest.fixture
    def sample_returns(self):
        np.random.seed(42)
        return list(np.random.randn(252) * 0.02)

    def test_var(self, sample_returns):
        from src.utils.risk import RiskAnalyzer

        analyzer = RiskAnalyzer(sample_returns)
        var_95 = analyzer.var(0.95)
        assert var_95 < 0  # VaR 是負值

    def test_cvar(self, sample_returns):
        from src.utils.risk import RiskAnalyzer

        analyzer = RiskAnalyzer(sample_returns)
        cvar_95 = analyzer.cvar(0.95)
        var_95 = analyzer.var(0.95)
        assert cvar_95 <= var_95  # CVaR <= VaR (更保守)

    def test_monte_carlo_vectorized(self, sample_returns):
        """驗證向量化 Monte Carlo 正確性."""
        from src.utils.risk import RiskAnalyzer

        analyzer = RiskAnalyzer(sample_returns)
        result = analyzer.monte_carlo(n_simulations=1000, horizon=30)

        assert result.mean_final_equity > 0
        assert 0 <= result.prob_loss <= 1
        assert "p50" in result.percentiles
        assert "p95" in result.max_drawdown_dist

    def test_compute_all(self, sample_returns):
        from src.utils.risk import RiskAnalyzer

        metrics = RiskAnalyzer(sample_returns).compute_all()
        d = metrics.to_dict()

        assert "var_95_pct" in d
        assert "sharpe_ratio" not in d  # 這個在 backtest.metrics 裡
        assert d["volatility"] >= 0
