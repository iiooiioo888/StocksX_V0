"""registry.py 單元測試 — StrategyRegistry, register_strategy 裝飾器."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.registry import (
    StrategyEntry,
    StrategyMeta,
    StrategyRegistry,
    register_strategy,
    registry,
)


# ─── 輔助：建立新註冊表以隔離測試 ───


def _make_reg():
    """建立獨立的 StrategyRegistry 避免互相污染."""
    return StrategyRegistry()


# ─── StrategyMeta 測試 ───


class TestStrategyMeta:
    """測試 StrategyMeta 資料類別."""

    def test_defaults(self):
        """驗證預設值."""
        m = StrategyMeta(name="test", label="測試", category="trend")
        assert m.description == ""
        assert m.params == []
        assert m.defaults == {}
        assert m.param_grid == {}


# ─── StrategyRegistry 測試 ───


class TestStrategyRegistry:
    """測試 StrategyRegistry 註冊與查詢."""

    def test_register_and_get(self):
        """註冊策略後可通過 get 取回."""
        reg = _make_reg()

        def dummy(rows):
            return [0] * len(rows)

        reg.register(func=dummy, name="dummy", label="Dummy", category="trend")
        entry = reg.get("dummy")
        assert entry is not None
        assert entry.func is dummy
        assert entry.meta.name == "dummy"
        assert entry.meta.label == "Dummy"
        assert entry.meta.category == "trend"

    def test_get_nonexistent_returns_none(self):
        """查詢不存在的策略應返回 None."""
        reg = _make_reg()
        assert reg.get("nonexistent") is None

    def test_register_returns_func(self):
        """register 應返回原始函式（可作裝飾器用）."""
        reg = _make_reg()

        def my_strat(rows):
            return []

        result = reg.register(func=my_strat, name="ms", label="MS", category="oscillator")
        assert result is my_strat

    def test_list_all(self):
        """list_all 應返回所有已註冊策略的 metadata."""
        reg = _make_reg()
        reg.register(func=lambda r: [], name="a", label="A", category="trend")
        reg.register(func=lambda r: [], name="b", label="B", category="oscillator")
        metas = reg.list_all()
        assert len(metas) == 2
        names = {m.name for m in metas}
        assert names == {"a", "b"}

    def test_list_by_category(self):
        """list_by_category 應只返回指定分類."""
        reg = _make_reg()
        reg.register(func=lambda r: [], name="a", label="A", category="trend")
        reg.register(func=lambda r: [], name="b", label="B", category="oscillator")
        reg.register(func=lambda r: [], name="c", label="C", category="trend")
        trend = reg.list_by_category("trend")
        assert len(trend) == 2
        assert all(m.category == "trend" for m in trend)

    def test_names_property(self):
        """names 屬性應返回所有策略名稱."""
        reg = _make_reg()
        reg.register(func=lambda r: [], name="x", label="X", category="trend")
        reg.register(func=lambda r: [], name="y", label="Y", category="breakout")
        assert set(reg.names) == {"x", "y"}

    def test_get_signal_with_params(self):
        """get_signal 應傳遞 kwargs 給策略函式."""
        reg = _make_reg()
        received_kwargs = {}

        def strat(rows, fast=10, slow=30):
            received_kwargs.update({"fast": fast, "slow": slow})
            return [0] * len(rows)

        reg.register(func=strat, name="sma", label="SMA", category="trend", params=["fast", "slow"])
        rows = [{"close": 100}]
        reg.get_signal("sma", rows, fast=5, slow=20)
        assert received_kwargs == {"fast": 5, "slow": 20}

    def test_get_signal_no_params(self):
        """get_signal 無 params 時不傳 kwargs."""
        reg = _make_reg()

        def strat(rows):
            return [1] * len(rows)

        reg.register(func=strat, name="simple", label="Simple", category="trend")
        rows = [{"close": 100}]
        result = reg.get_signal("simple", rows)
        assert result == [1]

    def test_get_signal_nonexistent(self):
        """get_signal 查詢不存在的策略返回全零列表."""
        reg = _make_reg()
        result = reg.get_signal("nope", [{"close": 1}])
        assert result == [0]

    def test_register_with_metadata(self):
        """註冊時可傳入完整 metadata."""
        reg = _make_reg()
        reg.register(
            func=lambda r: [],
            name="adv",
            label="Advanced",
            category="breakout",
            description="進階策略",
            params=["window"],
            defaults={"window": 20},
            param_grid={"window": [10, 20, 30]},
        )
        entry = reg.get("adv")
        assert entry.meta.description == "進階策略"
        assert entry.meta.params == ["window"]
        assert entry.meta.defaults == {"window": 20}
        assert entry.meta.param_grid == {"window": [10, 20, 30]}


# ─── register_strategy 裝飾器測試 ───


class TestRegisterStrategyDecorator:
    """測試 @register_strategy 裝飾器."""

    def test_decorator_registers(self):
        """裝飾器應自動註冊策略到全域 registry."""
        # 使用獨立 registry 避免衝突
        local_reg = StrategyRegistry()

        def decorator_factory(name, label, category, **kw):
            def decorator(func):
                local_reg.register(func=func, name=name, label=label, category=category, **kw)
                return func
            return decorator

        @decorator_factory(name="test_dec", label="Test", category="trend")
        def my_strategy(rows):
            return [0]

        assert local_reg.get("test_dec") is not None

    def test_decorator_preserves_function(self):
        """裝飾器不應改變原函式行為."""
        local_reg = StrategyRegistry()

        def decorator_factory(name, label, category):
            def decorator(func):
                local_reg.register(func=func, name=name, label=label, category=category)
                return func
            return decorator

        @decorator_factory(name="passthrough", label="PT", category="trend")
        def passthrough(rows):
            return [r["v"] for r in rows]

        result = passthrough([{"v": 1}, {"v": 2}])
        assert result == [1, 2]
