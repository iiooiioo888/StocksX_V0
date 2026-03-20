"""
熔斷器模式 — 交易系統保護

當連續虧損或異常發生時自動暫停交易，防止災難性損失。

功能：
- 連續虧損熔斷
- 日虧損熔斷
- 回撤熔斷
- 異常率熔斷
- 自動恢復（冷卻期後）

用法：
    from src.trading.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

    config = CircuitBreakerConfig(max_consecutive_losses=3, max_daily_loss_pct=5.0)
    breaker = CircuitBreaker(config)

    if breaker.can_trade():
        # 執行交易
        breaker.record_trade(result)
    else:
        print(f"熔斷中: {breaker.trip_reason}")
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class BreakerState(Enum):
    """熔斷器狀態."""

    CLOSED = auto()  # 正常運行
    OPEN = auto()  # 熔斷中（禁止交易）
    HALF_OPEN = auto()  # 冷卻後試探


@dataclass(slots=True)
class CircuitBreakerConfig:
    """熔斷器配置."""

    # 連續虧損
    max_consecutive_losses: int = 3

    # 日虧損限制
    max_daily_loss_pct: float = 5.0

    # 最大回撤限制
    max_drawdown_pct: float = 10.0

    # 異常率限制（最近 N 筆中錯誤比例）
    error_window: int = 20
    max_error_rate: float = 0.5

    # 冷卻期（秒）
    cooldown_seconds: float = 300.0

    # 半開狀態允許的試探交易數
    half_open_max_trades: int = 1


@dataclass(slots=True)
class TradeRecord:
    """交易記錄."""

    pnl_pct: float = 0.0
    profit: float = 0.0
    is_error: bool = False
    timestamp: float = field(default_factory=time.time)


class CircuitBreaker:
    """交易熔斷器."""

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self._state = BreakerState.CLOSED
        self._trip_reason: str = ""
        self._trip_time: float = 0.0
        self._half_open_trades: int = 0

        # 統計
        self._consecutive_losses: int = 0
        self._daily_trades: list[TradeRecord] = []
        self._all_trades: list[TradeRecord] = []
        self._daily_start_equity: float = 0.0
        self._peak_equity: float = 0.0
        self._current_equity: float = 0.0
        self._last_day_reset: float = time.time()

    @property
    def state(self) -> BreakerState:
        return self._state

    @property
    def is_open(self) -> bool:
        if self._state == BreakerState.OPEN:
            # 檢查冷卻期是否結束
            if time.time() - self._trip_time >= self.config.cooldown_seconds:
                self._state = BreakerState.HALF_OPEN
                self._half_open_trades = 0
                logger.info("breaker_half_open", extra={"reason": "cooldown_ended"})
                return False
            return True
        return False

    @property
    def trip_reason(self) -> str:
        return self._trip_reason

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "state": self._state.name,
            "consecutive_losses": self._consecutive_losses,
            "total_trades": len(self._all_trades),
            "daily_trades": len(self._daily_trades),
            "trip_reason": self._trip_reason,
            "current_equity": self._current_equity,
            "peak_equity": self._peak_equity,
        }

    def can_trade(self) -> bool:
        """檢查是否可以交易."""
        if self._state == BreakerState.CLOSED:
            return True

        if self._state == BreakerState.HALF_OPEN:
            return self._half_open_trades < self.config.half_open_max_trades

        # OPEN 狀態：檢查冷卻
        return not self.is_open

    def update_equity(self, equity: float) -> None:
        """更新權益（用於回撤計算）."""
        self._current_equity = equity
        if equity > self._peak_equity:
            self._peak_equity = equity

        # 日重置
        now = time.time()
        if now - self._last_day_reset > 86400:
            self._daily_trades = []
            self._daily_start_equity = equity
            self._last_day_reset = now

    def record_trade(self, pnl_pct: float, profit: float = 0.0, is_error: bool = False) -> None:
        """
        記錄交易結果並檢查熔斷條件.

        Args:
            pnl_pct: 報酬率（%）
            profit: 損益金額
            is_error: 是否為執行錯誤
        """
        record = TradeRecord(pnl_pct=pnl_pct, profit=profit, is_error=is_error)
        self._all_trades.append(record)
        self._daily_trades.append(record)

        # 半開狀態計數
        if self._state == BreakerState.HALF_OPEN:
            self._half_open_trades += 1

        # 連續虧損
        if pnl_pct < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0

        # 更新權益
        self._current_equity += profit

        # 檢查熔斷條件
        self._check_break()

    def _trip(self, reason: str) -> None:
        """觸發熔斷."""
        self._state = BreakerState.OPEN
        self._trip_reason = reason
        self._trip_time = time.time()
        logger.warning("circuit_breaker_tripped", extra={"reason": reason, "state": "OPEN"})

    def _check_break(self) -> None:
        """檢查所有熔斷條件."""
        cfg = self.config

        # 1. 連續虧損
        if self._consecutive_losses >= cfg.max_consecutive_losses:
            self._trip(f"連續虧損 {self._consecutive_losses} 筆")
            return

        # 2. 日虧損
        if self._daily_start_equity > 0:
            daily_loss = (self._daily_start_equity - self._current_equity) / self._daily_start_equity * 100
            if daily_loss > cfg.max_daily_loss_pct:
                self._trip(f"日虧損 {daily_loss:.1f}% 超限 {cfg.max_daily_loss_pct}%")
                return

        # 3. 最大回撤
        if self._peak_equity > 0:
            dd = (self._peak_equity - self._current_equity) / self._peak_equity * 100
            if dd > cfg.max_drawdown_pct:
                self._trip(f"回撤 {dd:.1f}% 超限 {cfg.max_drawdown_pct}%")
                return

        # 4. 異常率
        if len(self._all_trades) >= cfg.error_window:
            recent = self._all_trades[-cfg.error_window :]
            errors = sum(1 for t in recent if t.is_error)
            error_rate = errors / len(recent)
            if error_rate > cfg.max_error_rate:
                self._trip(f"異常率 {error_rate:.0%} 超限 {cfg.max_error_rate:.0%}")
                return

    def reset(self) -> None:
        """手動重置熔斷器."""
        self._state = BreakerState.CLOSED
        self._trip_reason = ""
        self._consecutive_losses = 0
        self._half_open_trades = 0
        logger.info("breaker_reset", extra={"state": "CLOSED"})

    def force_open(self, reason: str = "manual") -> None:
        """手動觸發熔斷."""
        self._trip(f"手動熔斷: {reason}")
