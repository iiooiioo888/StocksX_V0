"""
Signal System — 事件驅動交易信號

取代散落在各處的硬編碼信號邏輯。
Signal = 方向 + 信心度 + 元數據
SignalBus = 發布/訂閱，支持多策略組合
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any
from collections.abc import Callable

logger = logging.getLogger(__name__)


class Direction(IntEnum):
    """交易方向."""

    FLAT = 0
    LONG = 1
    SHORT = -1


@dataclass(slots=True)
class Signal:
    """交易信號."""

    symbol: str
    strategy: str
    direction: Direction
    confidence: float = 0.0  # 0.0 ~ 1.0
    price: float = 0.0
    timestamp: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def action(self) -> str:
        if self.direction == Direction.LONG:
            return "BUY"
        elif self.direction == Direction.SHORT:
            return "SELL"
        return "HOLD"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy,
            "direction": int(self.direction),
            "action": self.action,
            "confidence": self.confidence,
            "price": self.price,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


# ─── Signal Bus (Pub/Sub) ───

SignalHandler = Callable[[Signal], None]


class SignalBus:
    """
    信號總線：發布/訂閱模式。
    多策略可發布信號，訂閱者（交易執行器、通知系統）自動接收。
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[SignalHandler]] = {}
        self._global_handlers: list[SignalHandler] = []
        self._history: list[Signal] = []
        self._max_history = 1000

    def subscribe(self, handler: SignalHandler, pattern: str | None = None) -> None:
        """訂閱信號。pattern=None 表示訂閱全部。"""
        if pattern is None:
            self._global_handlers.append(handler)
        else:
            self._handlers.setdefault(pattern, []).append(handler)

    def publish(self, signal: Signal) -> None:
        """發布信號."""
        self._history.append(signal)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # 通知全局訂閱者
        for handler in self._global_handlers:
            try:
                handler(signal)
            except Exception:
                logger.exception("Signal handler error (global)")

        # 通知 pattern 訂閱者
        key = f"{signal.symbol}:{signal.strategy}"
        for pattern, handlers in self._handlers.items():
            if pattern == key or pattern == signal.symbol or pattern == signal.strategy:
                for handler in handlers:
                    try:
                        handler(signal)
                    except Exception:
                        logger.exception("Signal handler error (%s)", pattern)

    def history(self, limit: int = 100) -> list[Signal]:
        """取得最近 N 條信號."""
        return self._history[-limit:]


# ─── 全域實例 ───

_global_bus: SignalBus | None = None


def get_signal_bus() -> SignalBus:
    """取得全域 SignalBus."""
    global _global_bus
    if _global_bus is None:
        _global_bus = SignalBus()
    return _global_bus
