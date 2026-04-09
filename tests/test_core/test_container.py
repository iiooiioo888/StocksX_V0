"""test_container.py — DI Container 單元測試."""

import os

import pytest

from src.core.container import Container

# ─── Register / Get 測試 ───

class TestRegisterAndGet:
    """測試基本註冊與獲取."""

    def test_register_instance(self):
        """register 註冊的實例應可通過 get 取得."""
        c = Container()

        class MyService:
            def __init__(self):
                self.value = 42

        svc = MyService()
        c.register(MyService, svc)
        assert c.get(MyService) is svc
        assert c.get(MyService).value == 42

    def test_register_factory(self):
        """register_factory 應延遲建立實例."""
        c = Container()
        created = []

        class MyService:
            pass

        def factory():
            created.append(True)
            return MyService()

        c.register_factory(MyService, factory)
        assert len(created) == 0  # 還沒建立
        instance = c.get(MyService)
        assert len(created) == 1
        assert isinstance(instance, MyService)

    def test_factory_caches_singleton(self):
        """工廠建立的實例應被快取為單例."""
        c = Container()

        class MyService:
            pass

        c.register_factory(MyService, lambda: MyService())
        a = c.get(MyService)
        b = c.get(MyService)
        assert a is b

# ─── Has 測試 ───

class TestHas:
    """測試 has 方法."""

    def test_has_registered(self):
        """已註冊的類別 has 應返回 True."""
        c = Container()

        class Svc:
            pass

        c.register(Svc, Svc())
        assert c.has(Svc) is True

    def test_has_factory(self):
        """有工廠註冊的 has 應返回 True."""
        c = Container()

        class Svc:
            pass

        c.register_factory(Svc, lambda: Svc())
        assert c.has(Svc) is True

    def test_has_not_registered(self):
        """未註冊的類別 has 應返回 False."""
        c = Container()

        class Svc:
            pass

        assert c.has(Svc) is False

# ─── Remove 測試 ───

class TestRemove:
    """測試 remove 方法."""

    def test_remove_instance(self):
        """remove 應移除已註冊的實例."""
        c = Container()

        class Svc:
            pass

        c.register(Svc, Svc())
        assert c.has(Svc) is True
        c.remove(Svc)
        assert c.has(Svc) is False

    def test_remove_factory(self):
        """remove 應移除已註冊的工廠."""
        c = Container()

        class Svc:
            pass

        c.register_factory(Svc, lambda: Svc())
        c.remove(Svc)
        assert c.has(Svc) is False

# ─── Error 測試 ───

class TestErrors:
    """測試錯誤處理."""

    def test_get_unregistered_raises(self):
        """get 未註冊的類別應拋出 KeyError."""
        c = Container()

        class Svc:
            pass

        with pytest.raises(KeyError, match="No registration"):
            c.get(Svc)
