"""
Typed Configuration — 統一、安全、可驗證的設定管理

取代散落在 config.py / config_secrets.py / .env 的碎片化配置。
所有設定有預設值、型別驗證、文檔。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ─── 環境變數讀取 ───


def _env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes")


def _env_int(key: str, default: int = 0) -> int:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _env_float(key: str, default: float = 0.0) -> float:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


# ─── 子設定 ───


@dataclass(frozen=True, slots=True)
class AppSettings:
    """應用層設定."""

    env: str = "production"
    debug: bool = False
    port: int = 8501
    ws_port: int = 8001
    tz: str = "Asia/Shanghai"
    log_level: str = "INFO"
    secret_key: str = ""

    @classmethod
    def from_env(cls) -> AppSettings:
        sk = _env("SECRET_KEY", "") or ""
        if not sk:
            import logging as _logging

            _logging.getLogger(__name__).error(
                "❌ SECRET_KEY 未設定！JWT 認證將無法正常工作。"
                '請在 .env 中設定：python -c "import secrets; print(secrets.token_hex(32))"'
            )
        return cls(
            env=_env("APP_ENV", "production") or "production",
            debug=_env_bool("APP_DEBUG", False),
            port=_env_int("APP_PORT", 8501),
            ws_port=_env_int("WS_PORT", 8001),
            tz=_env("TZ", "Asia/Shanghai") or "Asia/Shanghai",
            log_level=_env("LOG_LEVEL", "INFO") or "INFO",
            secret_key=sk,
        )


@dataclass(frozen=True, slots=True)
class CacheSettings:
    """快取設定."""

    redis_url: str = "redis://localhost:6379/0"
    price_ttl: int = 1  # 秒
    kline_ttl: int = 300
    orderbook_ttl: int = 1
    user_ttl: int = 30

    @classmethod
    def from_env(cls) -> CacheSettings:
        return cls(
            redis_url=_env("REDIS_URL", "redis://localhost:6379/0") or "redis://localhost:6379/0",
            price_ttl=_env_int("CACHE_PRICE_TTL", 1),
            kline_ttl=_env_int("CACHE_KLINE_TTL", 300),
            orderbook_ttl=_env_int("CACHE_ORDERBOOK_TTL", 1),
            user_ttl=_env_int("CACHE_USER_TTL", 30),
        )


@dataclass(frozen=True, slots=True)
class ExchangeSettings:
    """交易所 API 金鑰."""

    binance_api_key: str | None = None
    binance_secret: str | None = None
    bybit_api_key: str | None = None
    bybit_secret: str | None = None

    @classmethod
    def from_env(cls) -> ExchangeSettings:
        return cls(
            binance_api_key=_env("BINANCE_API_KEY"),
            binance_secret=_env("BINANCE_SECRET_KEY"),
            bybit_api_key=_env("BYBIT_API_KEY"),
            bybit_secret=_env("BYBIT_SECRET_KEY"),
        )


@dataclass(frozen=True, slots=True)
class DataApiSettings:
    """第三方數據 API 金鑰."""

    dashscope: str | None = None
    coingecko: str | None = None
    coinmarketcap: str | None = None
    fred: str | None = None
    alpha_vantage: str | None = None
    fmp: str | None = None
    polygon: str | None = None
    glassnode: str | None = None

    @classmethod
    def from_env(cls) -> DataApiSettings:
        return cls(
            dashscope=_env("DASHSCOPE_API_KEY"),
            coingecko=_env("COINGECKO_API_KEY"),
            coinmarketcap=_env("COINMARKETCAP_API_KEY"),
            fred=_env("FRED_API_KEY"),
            alpha_vantage=_env("ALPHA_VANTAGE_API_KEY"),
            fmp=_env("FMP_API_KEY"),
            polygon=_env("POLYGON_API_KEY"),
            glassnode=_env("GLASSNODE_API_KEY"),
        )


@dataclass(frozen=True, slots=True)
class BacktestDefaults:
    """回測預設參數."""

    initial_equity: float = 10_000.0
    leverage: float = 1.0
    default_fee_pct: float = 0.05
    default_slippage_pct: float = 0.01

    @classmethod
    def from_env(cls) -> BacktestDefaults:
        return cls(
            initial_equity=_env_float("BT_INITIAL_EQUITY", 10_000.0),
            leverage=_env_float("BT_LEVERAGE", 1.0),
            default_fee_pct=_env_float("BT_FEE_PCT", 0.05),
            default_slippage_pct=_env_float("BT_SLIPPAGE_PCT", 0.01),
        )


# ─── 統一入口 ───


@dataclass(frozen=True, slots=True)
class Settings:
    """應用統一設定入口."""

    app: AppSettings = field(default_factory=AppSettings.from_env)
    cache: CacheSettings = field(default_factory=CacheSettings.from_env)
    exchange: ExchangeSettings = field(default_factory=ExchangeSettings.from_env)
    data_api: DataApiSettings = field(default_factory=DataApiSettings.from_env)
    backtest: BacktestDefaults = field(default_factory=BacktestDefaults.from_env)

    @property
    def db_path(self) -> Path:
        return Path("data") / "stocksx.db"

    @property
    def cache_dir(self) -> Path:
        return Path("cache")

    # ─── 向後兼容屬性（舊 src.config.Settings 的屬性）──

    @property
    def secret_key(self) -> str:
        return self.app.secret_key

    @property
    def admin_password(self) -> str:
        import secrets as _secrets
        import logging as _logging

        pw = _env("ADMIN_PASSWORD")
        if not pw:
            _auto_pw = _secrets.token_urlsafe(16)
            _logging.getLogger(__name__).warning(
                "ADMIN_PASSWORD 未設定，已自動生成隨機密碼。請查看日誌獲取密碼並盡快設定環境變數。"
            )
            _logging.getLogger(__name__).warning("臨時管理員密碼: %s", _auto_pw)
            return _auto_pw
        return pw

    @property
    def log_level(self) -> str:
        return self.app.log_level

    @property
    def redis_url(self) -> str:
        return self.cache.redis_url


_settings: Settings | None = None


def get_settings() -> Settings:
    """取得全域設定（單例）."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
