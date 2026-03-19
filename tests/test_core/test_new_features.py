"""測試進階指標、異步抓取器、數據驗證、熔斷器"""

from __future__ import annotations

import asyncio


# ════════════════════════════════════════════════════════════
# Technical Indicators
# ════════════════════════════════════════════════════════════

def _make_rows(n=50):
    """生成測試用 K 線."""
    rows = []
    price = 100.0
    for i in range(n):
        import random
        random.seed(i)
        change = random.gauss(0, 2)
        o = price
        c = price + change
        h = max(o, c) + abs(random.gauss(0, 1))
        l = min(o, c) - abs(random.gauss(0, 1))
        rows.append({"timestamp": i * 3600000, "open": o, "high": h, "low": l, "close": c, "volume": random.uniform(100, 10000)})
        price = c
    return rows


class TestATR:
    def test_atr_length(self):
        from src.backtest.indicators import atr
        rows = _make_rows(50)
        result = atr(rows, period=14)
        assert len(result) == 50
        assert result[13] > 0  # ATR starts from period-1

    def test_atr_empty(self):
        from src.backtest.indicators import atr
        assert atr([], 14) == []


class TestOBV:
    def test_obv_starts_zero(self):
        from src.backtest.indicators import obv
        rows = _make_rows(20)
        result = obv(rows)
        assert result[0] == 0.0
        assert len(result) == 20


class TestCCI:
    def test_cci_range(self):
        from src.backtest.indicators import cci
        rows = _make_rows(50)
        result = cci(rows, period=20)
        assert len(result) == 50
        # CCI can be outside ±100 but should be finite
        assert all(isinstance(v, float) for v in result)


class TestMFI:
    def test_mfi_range(self):
        from src.backtest.indicators import mfi
        rows = _make_rows(50)
        result = mfi(rows, period=14)
        assert len(result) == 50
        # MFI should be 0-100 after warmup
        for v in result[14:]:
            assert 0 <= v <= 100


class TestAroon:
    def test_aroon_osc_range(self):
        from src.backtest.indicators import aroon
        rows = _make_rows(50)
        up, down, osc = aroon(rows, period=25)
        assert len(up) == 50
        assert len(osc) == 50


class TestHeikinAshi:
    def test_heikin_ashi_length(self):
        from src.backtest.indicators import heikin_ashi
        rows = _make_rows(30)
        ha = heikin_ashi(rows)
        assert len(ha) == 30
        assert all("open" in r and "close" in r for r in ha)


class TestKeltnerChannel:
    def test_keltner_bands(self):
        from src.backtest.indicators import keltner_channel
        rows = _make_rows(50)
        upper, middle, lower = keltner_channel(rows)
        assert len(upper) == 50
        # Upper > Lower
        for i in range(20, 50):
            assert upper[i] >= lower[i]


class TestVolumeProfile:
    def test_volume_profile_structure(self):
        from src.backtest.indicators import volume_profile
        rows = _make_rows(100)
        vp = volume_profile(rows, n_bins=10)
        assert "poc" in vp
        assert "vah" in vp
        assert "val" in vp
        assert len(vp["bins"]) == 10


# ════════════════════════════════════════════════════════════
# OHLCV Validators
# ════════════════════════════════════════════════════════════

class TestOHLCVValidator:
    def test_valid_data(self):
        from src.data.validators import validate_ohlcv
        rows = _make_rows(20)
        report = validate_ohlcv(rows)
        assert report.is_valid
        assert report.quality_score > 90

    def test_missing_field(self):
        from src.data.validators import validate_ohlcv
        rows = [{"timestamp": 1, "open": 100, "high": 105, "low": 95}]  # missing close
        report = validate_ohlcv(rows, check_timestamps=False)
        assert not report.is_valid
        assert report.error_count > 0

    def test_high_lower_than_low(self):
        from src.data.validators import validate_ohlcv
        rows = [{"timestamp": 1, "open": 100, "high": 90, "low": 95, "close": 100, "volume": 1000}]
        report = validate_ohlcv(rows, check_timestamps=False)
        assert report.error_count > 0

    def test_clean_removes_errors(self):
        from src.data.validators import validate_ohlcv
        rows = _make_rows(10)
        rows.append({"timestamp": 99, "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0})
        report = validate_ohlcv(rows, check_timestamps=False)
        cleaned = report.clean(rows)
        assert len(cleaned) <= len(rows)


# ════════════════════════════════════════════════════════════
# Circuit Breaker
# ════════════════════════════════════════════════════════════

class TestCircuitBreaker:
    def test_initial_state_closed(self):
        from src.trading.circuit_breaker import CircuitBreaker, BreakerState
        cb = CircuitBreaker()
        assert cb.state == BreakerState.CLOSED
        assert cb.can_trade()

    def test_consecutive_loss_trip(self):
        from src.trading.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, BreakerState
        config = CircuitBreakerConfig(max_consecutive_losses=3)
        cb = CircuitBreaker(config)
        cb.update_equity(10000)

        cb.record_trade(-1.0)
        cb.record_trade(-1.0)
        assert cb.can_trade()  # 2 losses, not yet tripped

        cb.record_trade(-1.0)
        assert not cb.can_trade()  # 3 losses, tripped
        assert cb.state == BreakerState.OPEN

    def test_reset(self):
        from src.trading.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, BreakerState
        config = CircuitBreakerConfig(max_consecutive_losses=2)
        cb = CircuitBreaker(config)
        cb.update_equity(10000)
        cb.record_trade(-1.0)
        cb.record_trade(-1.0)
        assert cb.state == BreakerState.OPEN

        cb.reset()
        assert cb.state == BreakerState.CLOSED
        assert cb.can_trade()

    def test_profit_resets_consecutive(self):
        from src.trading.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
        config = CircuitBreakerConfig(max_consecutive_losses=3)
        cb = CircuitBreaker(config)
        cb.update_equity(10000)

        cb.record_trade(-1.0)
        cb.record_trade(2.0)  # profit resets
        cb.record_trade(-1.0)
        cb.record_trade(-1.0)
        assert cb.can_trade()  # only 2 consecutive after reset
