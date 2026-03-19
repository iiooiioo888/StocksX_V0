"""config.py 單元測試 — Settings, AppSettings, CacheSettings, BacktestDefaults."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.config import (
    AppSettings,
    BacktestDefaults,
    CacheSettings,
    ExchangeSettings,
    DataApiSettings,
    Settings,
    _env,
    _env_bool,
    _env_float,
    _env_int,
    get_settings,
)


# ─── 環境變數讀取輔助函式測試 ───


class TestEnvHelpers:
    """測試 _env, _env_bool, _env_int, _env_float 輔助函式."""

    def test_env_returns_default_when_not_set(self):
        """當環境變數不存在時，應返回預設值."""
        os.environ.pop("__TEST_CONFIG_KEY__", None)
        assert _env("__TEST_CONFIG_KEY__", "fallback") == "fallback"

    def test_env_returns_none_when_no_default(self):
        """無預設值且環境變數不存在時，返回 None."""
        os.environ.pop("__TEST_CONFIG_KEY__", None)
        assert _env("__TEST_CONFIG_KEY__") is None

    def test_env_returns_value_when_set(self, monkeypatch):
        """環境變數存在時，返回其值."""
        monkeypatch.setenv("__TEST_CONFIG_KEY__", "hello")
        assert _env("__TEST_CONFIG_KEY__", "fallback") == "hello"

    def test_env_bool_true_values(self, monkeypatch):
        """'1', 'true', 'yes' 應返回 True."""
        for val in ("1", "true", "yes", "True", "YES"):
            monkeypatch.setenv("__TEST_BOOL__", val)
            assert _env_bool("__TEST_BOOL__") is True

    def test_env_bool_false_values(self, monkeypatch):
        """其他值應返回 False."""
        for val in ("0", "false", "no", "random"):
            monkeypatch.setenv("__TEST_BOOL__", val)
            assert _env_bool("__TEST_BOOL__") is False

    def test_env_bool_default_when_not_set(self):
        """未設定時返回預設值."""
        os.environ.pop("__TEST_BOOL__", None)
        assert _env_bool("__TEST_BOOL__", True) is True
        assert _env_bool("__TEST_BOOL__", False) is False

    def test_env_int_valid(self, monkeypatch):
        """有效整數字串應正確轉換."""
        monkeypatch.setenv("__TEST_INT__", "42")
        assert _env_int("__TEST_INT__") == 42

    def test_env_int_invalid_returns_default(self, monkeypatch):
        """無效整數字串應返回預設值."""
        monkeypatch.setenv("__TEST_INT__", "abc")
        assert _env_int("__TEST_INT__", 99) == 99

    def test_int_not_set_returns_default(self):
        """未設定時返回預設值."""
        os.environ.pop("__TEST_INT__", None)
        assert _env_int("__TEST_INT__", 7) == 7

    def test_env_float_valid(self, monkeypatch):
        """有效浮點數字串應正確轉換."""
        monkeypatch.setenv("__TEST_FLOAT__", "3.14")
        assert _env_float("__TEST_FLOAT__") == pytest.approx(3.14)

    def test_env_float_invalid_returns_default(self, monkeypatch):
        """無效浮點數字串應返回預設值."""
        monkeypatch.setenv("__TEST_FLOAT__", "xyz")
        assert _env_float("__TEST_FLOAT__", 1.5) == pytest.approx(1.5)

    def test_float_not_set_returns_default(self):
        """未設定時返回預設值."""
        os.environ.pop("__TEST_FLOAT__", None)
        assert _env_float("__TEST_FLOAT__", 2.5) == pytest.approx(2.5)


# ─── AppSettings 測試 ───


class TestAppSettings:
    """測試 AppSettings 資料類別."""

    def test_default_values(self):
        """驗證預設值."""
        s = AppSettings()
        assert s.env == "production"
        assert s.debug is False
        assert s.port == 8501
        assert s.ws_port == 8001
        assert s.tz == "Asia/Shanghai"
        assert s.log_level == "INFO"
        assert s.secret_key == ""

    def test_from_env_reads_env_vars(self, monkeypatch):
        """from_env 應從環境變數讀取設定."""
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.setenv("APP_DEBUG", "true")
        monkeypatch.setenv("APP_PORT", "3000")
        monkeypatch.setenv("WS_PORT", "9001")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        s = AppSettings.from_env()
        assert s.env == "development"
        assert s.debug is True
        assert s.port == 3000
        assert s.ws_port == 9001
        assert s.log_level == "DEBUG"

    def test_frozen(self):
        """AppSettings 是 frozen dataclass，不可修改."""
        s = AppSettings()
        with pytest.raises(AttributeError):
            s.env = "test"


# ─── CacheSettings 測試 ───


class TestCacheSettings:
    """測試 CacheSettings 資料類別."""

    def test_default_values(self):
        """驗證預設值."""
        s = CacheSettings()
        assert s.redis_url == "redis://localhost:6379/0"
        assert s.price_ttl == 1
        assert s.kline_ttl == 300
        assert s.orderbook_ttl == 1
        assert s.user_ttl == 30

    def test_from_env(self, monkeypatch):
        """from_env 應從環境變數讀取 TTL."""
        monkeypatch.setenv("CACHE_PRICE_TTL", "5")
        monkeypatch.setenv("CACHE_KLINE_TTL", "600")
        s = CacheSettings.from_env()
        assert s.price_ttl == 5
        assert s.kline_ttl == 600


# ─── BacktestDefaults 測試 ───


class TestBacktestDefaults:
    """測試 BacktestDefaults 資料類別."""

    def test_default_values(self):
        """驗證預設值."""
        b = BacktestDefaults()
        assert b.initial_equity == 10_000.0
        assert b.leverage == 1.0
        assert b.default_fee_pct == 0.05
        assert b.default_slippage_pct == 0.01

    def test_from_env(self, monkeypatch):
        """from_env 應從環境變數讀取回測參數."""
        monkeypatch.setenv("BT_INITIAL_EQUITY", "50000")
        monkeypatch.setenv("BT_LEVERAGE", "5.0")
        b = BacktestDefaults.from_env()
        assert b.initial_equity == pytest.approx(50000.0)
        assert b.leverage == pytest.approx(5.0)


# ─── Settings 整合測試 ───


class TestSettings:
    """測試統一 Settings 入口."""

    def test_default_construction(self):
        """Settings 可以用預設值構造."""
        s = Settings()
        assert isinstance(s.app, AppSettings)
        assert isinstance(s.cache, CacheSettings)
        assert isinstance(s.exchange, ExchangeSettings)
        assert isinstance(s.data_api, DataApiSettings)
        assert isinstance(s.backtest, BacktestDefaults)

    def test_db_path(self):
        """db_path 屬性應返回正確路徑."""
        s = Settings()
        assert str(s.db_path) == os.path.join("data", "stocksx.db")

    def test_cache_dir(self):
        """cache_dir 屬性應返回 'cache'."""
        s = Settings()
        assert str(s.cache_dir) == "cache"


# ─── get_settings 單例測試 ───


class TestGetSettings:
    """測試 get_settings 單例模式."""

    def test_returns_same_instance(self, monkeypatch):
        """多次呼叫應返回同一實例."""
        # 重置全域單例
        import src.core.config as cfg_mod
        cfg_mod._settings = None
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
