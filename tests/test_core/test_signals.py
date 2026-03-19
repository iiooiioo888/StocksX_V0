"""signals.py 單元測試 — Signal, SignalBus, Direction."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.signals import Direction, Signal, SignalBus, get_signal_bus


# ─── Direction 測試 ───


class TestDirection:
    """測試 Direction 枚舉."""

    def test_values(self):
        """驗證枚舉值."""
        assert Direction.FLAT == 0
        assert Direction.LONG == 1
        assert Direction.SHORT == -1

    def test_int_comparison(self):
        """Direction 可與整數比較（IntEnum）."""
        assert Direction.LONG == 1
        assert Direction.SHORT == -1


# ─── Signal 測試 ───


class TestSignal:
    """測試 Signal 資料類別."""

    def test_construction(self):
        """Signal 建構基本測試."""
        s = Signal(
            symbol="BTC/USDT",
            strategy="sma_cross",
            direction=Direction.LONG,
            confidence=0.85,
            price=50000.0,
            timestamp=1700000000,
        )
        assert s.symbol == "BTC/USDT"
        assert s.strategy == "sma_cross"
        assert s.direction == Direction.LONG
        assert s.confidence == pytest.approx(0.85)

    def test_action_buy(self):
        """LONG 方向 action 應為 BUY."""
        s = Signal(symbol="X", strategy="Y", direction=Direction.LONG)
        assert s.action == "BUY"

    def test_action_sell(self):
        """SHORT 方向 action 應為 SELL."""
        s = Signal(symbol="X", strategy="Y", direction=Direction.SHORT)
        assert s.action == "SELL"

    def test_action_hold(self):
        """FLAT 方向 action 應為 HOLD."""
        s = Signal(symbol="X", strategy="Y", direction=Direction.FLAT)
        assert s.action == "HOLD"

    def test_to_dict(self):
        """to_dict 應返回完整字典."""
        s = Signal(
            symbol="ETH/USDT",
            strategy="rsi",
            direction=Direction.SHORT,
            confidence=0.7,
            price=3000.0,
            timestamp=1700000001,
            metadata={"rsi": 75},
        )
        d = s.to_dict()
        assert d["symbol"] == "ETH/USDT"
        assert d["strategy"] == "rsi"
        assert d["direction"] == -1
        assert d["action"] == "SELL"
        assert d["confidence"] == pytest.approx(0.7)
        assert d["price"] == pytest.approx(3000.0)
        assert d["metadata"]["rsi"] == 75

    def test_default_metadata(self):
        """metadata 預設為空字典."""
        s = Signal(symbol="X", strategy="Y", direction=Direction.FLAT)
        assert s.metadata == {}


# ─── SignalBus 測試 ───


class TestSignalBus:
    """測試 SignalBus 發布/訂閱."""

    def test_publish_to_global_handler(self):
        """全域訂閱者應收到所有信號."""
        bus = SignalBus()
        received = []
        bus.subscribe(lambda sig: received.append(sig))
        sig = Signal(symbol="BTC/USDT", strategy="test", direction=Direction.LONG)
        bus.publish(sig)
        assert len(received) == 1
        assert received[0] is sig

    def test_publish_to_pattern_handler(self):
        """pattern 訂閱者應只收到匹配的信號."""
        bus = SignalBus()
        received = []
        bus.subscribe(lambda sig: received.append(sig), pattern="BTC/USDT")
        sig_btc = Signal(symbol="BTC/USDT", strategy="sma", direction=Direction.LONG)
        sig_eth = Signal(symbol="ETH/USDT", strategy="sma", direction=Direction.LONG)
        bus.publish(sig_btc)
        bus.publish(sig_eth)
        assert len(received) == 1
        assert received[0].symbol == "BTC/USDT"

    def test_subscribe_by_strategy_pattern(self):
        """按策略名稱 pattern 訂閱."""
        bus = SignalBus()
        received = []
        bus.subscribe(lambda sig: received.append(sig), pattern="rsi")
        sig1 = Signal(symbol="BTC/USDT", strategy="rsi", direction=Direction.LONG)
        sig2 = Signal(symbol="BTC/USDT", strategy="sma", direction=Direction.LONG)
        bus.publish(sig1)
        bus.publish(sig2)
        assert len(received) == 1
        assert received[0].strategy == "rsi"

    def test_subscribe_by_composite_key(self):
        """按 'symbol:strategy' 組合鍵訂閱."""
        bus = SignalBus()
        received = []
        bus.subscribe(lambda sig: received.append(sig), pattern="BTC/USDT:rsi")
        sig = Signal(symbol="BTC/USDT", strategy="rsi", direction=Direction.LONG)
        bus.publish(sig)
        assert len(received) == 1

    def test_history(self):
        """history 應返回最近的信號."""
        bus = SignalBus()
        for i in range(5):
            bus.publish(Signal(symbol=f"S{i}", strategy="t", direction=Direction.FLAT))
        h = bus.history(limit=3)
        assert len(h) == 3
        assert h[-1].symbol == "S4"

    def test_history_all(self):
        """不指定 limit 時返回所有信號（最多 100）."""
        bus = SignalBus()
        for i in range(10):
            bus.publish(Signal(symbol=f"S{i}", strategy="t", direction=Direction.FLAT))
        h = bus.history()
        assert len(h) == 10

    def test_max_history_trim(self):
        """超過 _max_history 時應自動裁剪."""
        bus = SignalBus()
        bus._max_history = 5
        for i in range(10):
            bus.publish(Signal(symbol=f"S{i}", strategy="t", direction=Direction.FLAT))
        assert len(bus._history) == 5

    def test_handler_exception_does_not_break_others(self):
        """某個 handler 出錯不影響其他 handler."""
        bus = SignalBus()
        results = []

        def bad_handler(sig):
            raise RuntimeError("fail")

        def good_handler(sig):
            results.append(sig)

        bus.subscribe(bad_handler)
        bus.subscribe(good_handler)
        sig = Signal(symbol="X", strategy="Y", direction=Direction.FLAT)
        bus.publish(sig)
        assert len(results) == 1


# ─── get_signal_bus 單例測試 ───


class TestGetSignalBus:
    """測試 get_signal_bus 單例."""

    def test_singleton(self):
        """應返回同一實例."""
        import src.core.signals as sig_mod
        sig_mod._global_bus = None
        b1 = get_signal_bus()
        b2 = get_signal_bus()
        assert b1 is b2
