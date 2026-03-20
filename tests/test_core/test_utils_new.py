"""測試新工具模組 — decorators, risk, config_validator"""

from __future__ import annotations

import math
import time


# ════════════════════════════════════════════════════════════
# Decorators
# ════════════════════════════════════════════════════════════


class TestRetry:
    def test_retry_succeeds_on_second_attempt(self):
        from src.utils.decorators import retry

        call_count = 0

        @retry(max_retries=3, delay=0.01)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 2

    def test_retry_exhausted(self):
        from src.utils.decorators import retry

        @retry(max_retries=2, delay=0.01)
        def always_fail():
            raise RuntimeError("boom")

        try:
            always_fail()
            raise AssertionError("Should have raised")
        except RuntimeError:
            pass


class TestTimed:
    def test_timed_returns_result(self):
        from src.utils.decorators import timed

        @timed
        def add(a, b):
            return a + b

        assert add(2, 3) == 5


class TestCached:
    def test_cached_returns_same_value(self):
        from src.utils.decorators import cached

        call_count = 0

        @cached(ttl=60)
        def compute(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert compute(5) == 10
        assert compute(5) == 10
        assert call_count == 1  # cached


class TestSuppressErrors:
    def test_suppress_returns_default(self):
        from src.utils.decorators import suppress_errors

        @suppress_errors(default=42, log=False)
        def fail():
            raise ValueError("oops")

        assert fail() == 42


# ════════════════════════════════════════════════════════════
# Risk Analyzer
# ════════════════════════════════════════════════════════════


class TestRiskAnalyzer:
    def test_basic_metrics(self):
        from src.utils.risk import RiskAnalyzer

        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01]
        ra = RiskAnalyzer(returns)

        metrics = ra.compute_all()
        assert metrics.volatility > 0
        assert metrics.max_drawdown > 0
        assert metrics.var_95 != 0

    def test_empty_returns(self):
        from src.utils.risk import RiskAnalyzer

        ra = RiskAnalyzer([])
        assert ra.max_drawdown == 0
        assert ra.std == 0

    def test_monte_carlo(self):
        from src.utils.risk import RiskAnalyzer

        returns = [0.01, -0.02, 0.03, -0.01, 0.02] * 10
        ra = RiskAnalyzer(returns)

        result = ra.monte_carlo(n_simulations=100, horizon=10, initial_equity=10000)
        assert result.mean_final_equity > 0
        assert 0 <= result.prob_loss <= 1
        assert "p50" in result.percentiles

    def test_correlation(self):
        from src.utils.risk import compute_correlation

        a = [0.01, 0.02, -0.01, 0.03]
        b = [0.02, 0.03, -0.02, 0.04]
        corr = compute_correlation(a, b)
        assert -1 <= corr <= 1


# ════════════════════════════════════════════════════════════
# Config Validator
# ════════════════════════════════════════════════════════════


class TestConfigValidator:
    def test_validate_config_returns_report(self):
        from src.utils.config_validator import validate_config

        report = validate_config()
        assert report.checks_total > 0
        assert isinstance(report.summary(), str)

    def test_config_report_properties(self):
        from src.utils.config_validator import ConfigReport, ConfigIssue

        report = ConfigReport()
        report.checks_total = 5
        report.checks_passed = 3
        report.issues.append(
            ConfigIssue(
                field="TEST",
                severity="warning",
                message="test warning",
            )
        )

        assert report.error_count == 0
        assert report.warning_count == 1
        assert report.is_valid  # no errors
