"""
Orchestrator — 統一編排層

取代散落在各 Page 中的業務邏輯。
提供高階 API，屏蔽 Provider / Pipeline / Registry 的組合細節。

用法：
    from src.core.orchestrator import Orchestrator

    orch = Orchestrator()
    result = orch.run_backtest("BTC/USDT:USDT", "1h", "sma_cross", fast=10, slow=30)
    ticker = orch.get_ticker("AAPL")
    signals = orch.compute_signals("ETH/USDT", "rsi_signal")
"""

from __future__ import annotations

import logging
import time
from typing import Any

from .adapters import CompositeProvider
from .backtest import BacktestConfig, BacktestEngine, BacktestReport
from .config import Settings, get_settings
from .provider import CacheBackend, MarketProvider, OrderBook, Ticker, make_cache
from .registry import registry
from .signals import Direction, Signal, get_signal_bus

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    統一編排器：業務邏輯入口。

    職責：
    1. 管理 Provider 生命週期
    2. 執行回測
    3. 計算信號
    4. 發布信號到 SignalBus
    """

    def __init__(
        self,
        settings: Settings | None = None,
        provider: MarketProvider | None = None,
        cache: CacheBackend | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._cache = cache or make_cache(self._settings.cache.redis_url)
        self._provider = provider or self._build_provider()
        self._signal_bus = get_signal_bus()

        # 自動觸發策略橋接（import 時自動註冊）
        try:
            from . import strategies_bridge  # noqa: F401
        except Exception:
            logger.warning("Strategy bridge not available")

    def _build_provider(self) -> CompositeProvider:
        """構建默認 Provider 組合."""
        composite = CompositeProvider()
        # 加密貨幣
        for ex in ["binance", "okx", "bybit", "bitget", "gate"]:
            try:
                from .adapters import CCXTProvider

                composite.add(CCXTProvider(ex, cache=self._cache))
            except Exception:
                pass
        # 傳統市場
        try:
            from .adapters import YahooProvider

            composite.add(YahooProvider(cache=self._cache))
        except Exception:
            pass
        return composite

    # ─── 數據 ───

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        since: int | None = None,
        limit: int = 500,
        clean: bool = True,
    ) -> list[dict[str, Any]]:
        """取得 K 線數據（自動路由 Provider）."""
        rows_ohlcv = self._provider.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        rows = [r.to_dict() for r in rows_ohlcv]

        if clean and rows:
            from .pipeline import ohlcv_clean_pipeline

            pipeline = ohlcv_clean_pipeline()
            rows = pipeline.run(rows)

        return rows

    def get_ticker(self, symbol: str) -> Ticker | None:
        """取得即時行情."""
        return self._provider.fetch_ticker(symbol)

    def get_orderbook(self, symbol: str, limit: int = 20) -> OrderBook | None:
        """取得訂單簿."""
        return self._provider.fetch_orderbook(symbol, limit=limit)

    # ─── 策略 ───

    def list_strategies(self) -> list[dict[str, Any]]:
        """列出所有已註冊策略."""
        return [
            {
                "name": m.name,
                "label": m.label,
                "category": m.category,
                "description": m.description,
                "params": m.params,
                "defaults": m.defaults,
            }
            for m in registry.list_all()
        ]

    def compute_signals(
        self,
        symbol: str,
        strategy: str,
        timeframe: str = "1h",
        limit: int = 500,
        **params: Any,
    ) -> list[int]:
        """計算策略信號."""
        rows = self.fetch_ohlcv(symbol, timeframe, limit=limit, clean=True)
        if not rows:
            return []
        return registry.get_signal(strategy, rows, **params)

    # ─── 回測 ───

    def run_backtest(
        self,
        symbol: str,
        timeframe: str,
        strategy: str,
        since_ms: int | None = None,
        until_ms: int | None = None,
        config: BacktestConfig | None = None,
        clean: bool = True,
        **strategy_params: Any,
    ) -> BacktestReport:
        """
        執行回測（一站式）.

        1. 取得數據（Provider）
        2. 清洗（Pipeline）
        3. 計算信號（Registry）
        4. 模擬交易（BacktestEngine）
        5. 返回報告（BacktestReport）
        """
        until_ms = until_ms or int(time.time() * 1000)
        if since_ms is None:
            since_ms = until_ms - 180 * 86400 * 1000  # 預設 180 天

        # Step 1: 取得數據
        rows = self.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=5000, clean=clean)
        if not rows:
            return BacktestReport(error="無 K 線資料")

        # 過濾時間範圍
        rows = [r for r in rows if since_ms <= r["timestamp"] <= until_ms]
        if not rows:
            return BacktestReport(error="指定時間範圍內無數據")

        # Step 2: 計算信號
        signals = registry.get_signal(strategy, rows, **strategy_params)
        if not signals:
            signals = [0] * len(rows)

        # Step 3: 執行回測
        bt_config = config or BacktestConfig(
            initial_equity=self._settings.backtest.initial_equity,
            leverage=self._settings.backtest.leverage,
            fee_rate_pct=self._settings.backtest.default_fee_pct,
            slippage_pct=self._settings.backtest.default_slippage_pct,
        )

        engine = BacktestEngine(config=bt_config)
        report = engine.run(rows, signals, since_ms, until_ms)

        # Step 4: 發布信號（如果有最新信號）
        if signals and signals[-1] != 0:
            signal = Signal(
                symbol=symbol,
                strategy=strategy,
                direction=Direction(signals[-1]),
                price=rows[-1]["close"],
                timestamp=rows[-1]["timestamp"],
            )
            self._signal_bus.publish(signal)

        return report

    def run_multi_backtest(
        self,
        symbol: str,
        timeframe: str,
        strategies: list[str],
        since_ms: int | None = None,
        until_ms: int | None = None,
        config: BacktestConfig | None = None,
        **strategy_params: Any,
    ) -> dict[str, BacktestReport]:
        """多策略對比回測."""
        results: dict[str, BacktestReport] = {}
        for strat in strategies:
            results[strat] = self.run_backtest(
                symbol,
                timeframe,
                strat,
                since_ms=since_ms,
                until_ms=until_ms,
                config=config,
                **strategy_params,
            )
        return results


# ─── 全域便捷入口 ───

_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """取得全域 Orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
