"""cache_manager.py 單元測試 — CacheNamespace, CacheManager, CacheStats."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.provider import DictCache
from src.core.cache_manager import CacheManager, CacheNamespace, CacheStats, get_cache_manager


# ─── CacheStats 測試 ───


class TestCacheStats:
    """測試 CacheStats 統計."""

    def test_initial_values(self):
        """初始值全為零."""
        s = CacheStats()
        assert s.hits == 0
        assert s.misses == 0
        assert s.sets == 0
        assert s.evictions == 0

    def test_hit_rate_zero_when_no_access(self):
        """無存取時 hit_rate 為 0."""
        s = CacheStats()
        assert s.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """hit_rate 計算."""
        s = CacheStats()
        s.hits = 7
        s.misses = 3
        assert s.hit_rate == pytest.approx(0.7)

    def test_to_dict(self):
        """to_dict 應返回完整統計."""
        s = CacheStats()
        s.hits = 10
        s.misses = 5
        s.sets = 8
        s.evictions = 2
        d = s.to_dict()
        assert d["hits"] == 10
        assert d["misses"] == 5
        assert d["sets"] == 8
        assert d["evictions"] == 2
        assert d["hit_rate"] == pytest.approx(0.6667, abs=0.001)


# ─── CacheNamespace 測試 ───


class TestCacheNamespace:
    """測試 CacheNamespace 命名空間快取."""

    @pytest.fixture
    def ns(self):
        """建立帶 DictCache 後端的 CacheNamespace."""
        backend = DictCache()
        return CacheNamespace("test", backend, default_ttl=60)

    def test_set_and_get(self, ns):
        """set 後 get 應返回值."""
        ns.set("key1", "value1")
        assert ns.get("key1") == "value1"

    def test_get_miss_returns_none(self, ns):
        """不存在的 key 應返回 None."""
        assert ns.get("nonexistent") is None

    def test_delete(self, ns):
        """delete 後 get 應返回 None."""
        ns.set("key1", "value1")
        ns.delete("key1")
        assert ns.get("key1") is None

    def test_get_or_set_cache_hit(self, ns):
        """快取命中時不應呼叫 factory."""
        ns.set("key1", "existing")
        called = []
        result = ns.get_or_set("key1", lambda: called.append(1) or "new")
        assert result == "existing"
        assert len(called) == 0

    def test_get_or_set_cache_miss(self, ns):
        """快取未命中時應呼叫 factory 並存入."""
        result = ns.get_or_set("key1", lambda: "computed")
        assert result == "computed"
        assert ns.get("key1") == "computed"

    def test_get_or_set_non_callable(self, ns):
        """factory 為非 callable 時直接作為值存入."""
        result = ns.get_or_set("key1", "static_value")
        assert result == "static_value"

    def test_invalidate_clears_namespace(self, ns):
        """invalidate 應清空此命名空間的資料."""
        ns.set("a", 1)
        ns.set("b", 2)
        ns.invalidate()
        assert ns.get("a") is None
        assert ns.get("b") is None

    def test_stats_tracking(self, ns):
        """統計數據應正確追蹤."""
        ns.set("k", "v")
        ns.get("k")       # hit
        ns.get("missing")  # miss
        ns.delete("k")
        assert ns.stats.hits == 1
        assert ns.stats.misses == 1
        assert ns.stats.sets == 1
        assert ns.stats.evictions == 1

    def test_namespace_key_prefix(self):
        """不同命名空間的相同 key 應互不干擾."""
        backend = DictCache()
        ns1 = CacheNamespace("ns1", backend, default_ttl=60)
        ns2 = CacheNamespace("ns2", backend, default_ttl=60)
        ns1.set("key", "value1")
        ns2.set("key", "value2")
        assert ns1.get("key") == "value1"
        assert ns2.get("key") == "value2"


# ─── CacheManager 測試 ───


class TestCacheManager:
    """測試 CacheManager 統一快取管理."""

    def test_default_namespaces(self):
        """CacheManager 應有預設命名空間."""
        cm = CacheManager()
        assert cm.price.name == "price"
        assert cm.kline.name == "kline"
        assert cm.orderbook.name == "orderbook"
        assert cm.user.name == "user"
        assert cm.api.name == "api"

    def test_namespace_creates_new(self):
        """namespace() 可建立新命名空間."""
        cm = CacheManager()
        ns = cm.namespace("custom", default_ttl=120)
        assert ns.name == "custom"
        assert ns._default_ttl == 120

    def test_namespace_returns_existing(self):
        """重複呼叫 namespace() 返回同一實例."""
        cm = CacheManager()
        ns1 = cm.namespace("custom")
        ns2 = cm.namespace("custom")
        assert ns1 is ns2

    def test_all_stats(self):
        """all_stats 應返回所有命名空間的統計."""
        cm = CacheManager()
        cm.price.set("BTC", 50000)
        stats = cm.all_stats()
        assert "price" in stats
        assert stats["price"]["sets"] == 1

    def test_clear_all(self):
        """clear_all 應清空所有命名空間."""
        cm = CacheManager()
        cm.price.set("BTC", 50000)
        cm.kline.set("ETH:1h", [1, 2, 3])
        cm.clear_all()
        assert cm.price.get("BTC") is None
        assert cm.kline.get("ETH:1h") is None


# ─── get_cache_manager 單例測試 ───


class TestGetCacheManager:
    """測試 get_cache_manager 單例."""

    def test_singleton(self):
        """應返回同一實例."""
        import src.core.cache_manager as cm_mod
        cm_mod._cache_manager = None
        cm1 = get_cache_manager()
        cm2 = get_cache_manager()
        assert cm1 is cm2
