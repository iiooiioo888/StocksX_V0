"""測試投資組合分析與報告模組"""

from __future__ import annotations

import math
import os
import tempfile


# ════════════════════════════════════════════════════════════
# Portfolio Analyzer
# ════════════════════════════════════════════════════════════


class TestPortfolioAnalyzer:
    def _make_returns(self):
        """創建測試用的報酬數據."""
        import random

        random.seed(42)
        return {
            "BTC": [random.gauss(0.001, 0.03) for _ in range(100)],
            "ETH": [random.gauss(0.002, 0.04) for _ in range(100)],
            "SOL": [random.gauss(0.003, 0.05) for _ in range(100)],
        }

    def test_equal_weight(self):
        from src.utils.portfolio import PortfolioAnalyzer

        pa = PortfolioAnalyzer(self._make_returns())
        ew = pa.equal_weight()
        assert len(ew.weights) == 3
        assert abs(sum(ew.weights) - 1.0) < 1e-6
        assert all(abs(w - 1 / 3) < 1e-6 for w in ew.weights)

    def test_inverse_volatility(self):
        from src.utils.portfolio import PortfolioAnalyzer

        pa = PortfolioAnalyzer(self._make_returns())
        iv = pa.inverse_volatility_weight()
        assert abs(sum(iv.weights) - 1.0) < 1e-6
        # BTC 應該有最高權重（波動率最低）
        btc_idx = iv.assets.index("BTC")
        assert iv.weights[btc_idx] > 0.25

    def test_risk_parity(self):
        from src.utils.portfolio import PortfolioAnalyzer

        pa = PortfolioAnalyzer(self._make_returns())
        rp = pa.risk_parity_weight()
        assert abs(sum(rp.weights) - 1.0) < 1e-3  # 收斂精度

    def test_min_variance(self):
        from src.utils.portfolio import PortfolioAnalyzer

        pa = PortfolioAnalyzer(self._make_returns())
        mv = pa.min_variance_weight()
        assert abs(sum(mv.weights) - 1.0) < 1e-3
        assert all(w >= 0 for w in mv.weights)

    def test_portfolio_metrics(self):
        from src.utils.portfolio import PortfolioAnalyzer

        pa = PortfolioAnalyzer(self._make_returns())
        metrics = pa.portfolio_metrics([0.4, 0.3, 0.3])
        assert metrics.annual_volatility > 0
        assert metrics.max_drawdown >= 0

    def test_correlation_matrix(self):
        from src.utils.portfolio import PortfolioAnalyzer

        pa = PortfolioAnalyzer(self._make_returns())
        corr = pa.correlation_matrix
        # 對角線應為 1
        for a in corr:
            assert abs(corr[a][a] - 1.0) < 1e-6
        # 對稱性
        assert abs(corr["BTC"]["ETH"] - corr["ETH"]["BTC"]) < 1e-6

    def test_efficient_frontier(self):
        from src.utils.portfolio import PortfolioAnalyzer

        pa = PortfolioAnalyzer(self._make_returns())
        frontier = pa.efficient_frontier(n_points=10)
        assert len(frontier) == 10
        assert all("return" in p and "volatility" in p for p in frontier)


# ════════════════════════════════════════════════════════════
# Report Generator
# ════════════════════════════════════════════════════════════


class TestReportGenerator:
    def test_html_generation(self):
        from src.utils.report import BacktestReportGenerator

        data = {
            "metrics": {
                "total_return_pct": 15.5,
                "max_drawdown_pct": -8.2,
                "sharpe_ratio": 1.5,
                "win_rate_pct": 62.0,
                "num_trades": 50,
                "profit_factor": 1.8,
            },
            "trades": [
                {
                    "side": 1,
                    "entry_price": 100,
                    "exit_price": 105,
                    "pnl_pct": 5.0,
                    "profit": 500,
                    "exit_reason": "signal",
                },
            ],
        }

        gen = BacktestReportGenerator(data, strategy_name="SMA Cross", symbol="BTC/USDT")
        html = gen.to_html()
        assert "SMA Cross" in html
        assert "BTC/USDT" in html
        assert "15.50%" in html

    def test_json_generation(self):
        from src.utils.report import BacktestReportGenerator

        data = {"metrics": {"total_return_pct": 10}, "trades": []}
        gen = BacktestReportGenerator(data)
        json_str = gen.to_json()
        assert '"total_return_pct"' in json_str

    def test_save_html(self):
        from src.utils.report import BacktestReportGenerator

        data = {"metrics": {}, "trades": []}
        gen = BacktestReportGenerator(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.save_html(os.path.join(tmpdir, "test_report.html"))
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "<html" in content

    def test_strategy_comparison(self):
        from src.utils.report import StrategyComparisonGenerator

        results = {
            "SMA": {
                "metrics": {
                    "total_return_pct": 10,
                    "sharpe_ratio": 1.2,
                    "max_drawdown_pct": -5,
                    "win_rate_pct": 60,
                    "num_trades": 30,
                }
            },
            "RSI": {
                "metrics": {
                    "total_return_pct": 15,
                    "sharpe_ratio": 1.5,
                    "max_drawdown_pct": -8,
                    "win_rate_pct": 55,
                    "num_trades": 40,
                }
            },
        }

        gen = StrategyComparisonGenerator(results, symbol="BTC/USDT")
        html = gen.to_html()
        assert "RSI" in html
        assert "SMA" in html
