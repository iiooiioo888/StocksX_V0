"""
自動交易主程式 - 整合信號、風險管理和交易執行
==================================================
功能：
- 監聽交易信號
- 風險檢查
- 自動執行訂單
- 持倉管理（停損/停利）
- 交易日誌記錄
"""

from __future__ import annotations

import logging
import time

from src.auth.user_db import UserDB
from src.backtest.strategies import get_signal
from src.data.service import data_service

from .executor import TradeExecutor, create_executor_from_config
from .risk_manager import RiskManager, create_risk_manager_from_config

logger = logging.getLogger(__name__)


class AutoTrader:
    """
    自動交易器

    工作流程：
    1. 從數據庫載入用戶的自動策略配置
    2. 初始化交易執行器和風險管理器
    3. 循環監聽市場數據和交易信號
    4. 當信號觸發時，執行風險檢查
    5. 通過檢查後，執行交易訂單
    6. 記錄交易日誌並更新持倉狀態
    """

    def __init__(
        self,
        user_id: int,
        db: UserDB | None = None,
    ):
        """
        初始化自動交易器

        Args:
            user_id: 用戶 ID
            db: 用戶數據庫實例
        """
        self.user_id = user_id
        self.db = db or UserDB()
        self.executor: TradeExecutor | None = None
        self.risk_manager: RiskManager | None = None
        self._running = False
        self._check_interval = 5  # 信號檢查間隔（秒）

    def load_config(self, strategy_id: int) -> dict:
        """
        從數據庫載入自動策略配置

        Args:
            strategy_id: 策略配置 ID

        Returns:
            配置字典
        """
        strategies = self.db.get_auto_strategies(self.user_id)
        for strategy in strategies:
            if strategy["id"] == strategy_id:
                return strategy["config"]
        raise ValueError(f"找不到策略配置 ID: {strategy_id}")

    def initialize(
        self,
        config: dict,
    ) -> bool:
        """
        初始化交易執行器和風險管理器

        Args:
            config: 策略配置

        Returns:
            是否成功
        """
        try:
            # 初始化交易執行器
            exchange_config = config.get("exchange", {})
            self.executor = create_executor_from_config(self.user_id, exchange_config)

            # 初始化風險管理器
            risk_config = config.get("risk_management", {})
            self.risk_manager = create_risk_manager_from_config(risk_config)

            # 設定初始權益
            initial_equity = config.get("initial_equity", 10000)
            self.risk_manager.reset_daily_pnl(initial_equity)

            logger.info(f"✅ 自動交易器初始化成功 (user_id={self.user_id})")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失敗：{e}")
            return False

    def start(self, strategy_id: int):
        """
        啟動自動交易循環

        Args:
            strategy_id: 策略配置 ID
        """
        config = self.load_config(strategy_id)

        if not self.initialize(config):
            logger.error("無法啟動自動交易：初始化失敗")
            return

        self._running = True
        logger.info(f"🚀 自動交易已啟動 (strategy_id={strategy_id})")

        # 主交易循環
        while self._running:
            try:
                self._trading_loop(config)
            except Exception as e:
                logger.error(f"交易循環錯誤：{e}")

            time.sleep(self._check_interval)

    def stop(self):
        """停止自動交易"""
        self._running = False
        logger.info("⏹️ 自動交易已停止")

    def _trading_loop(self, config: dict):
        """
        交易循環核心邏輯

        流程：
        1. 獲取訂閱的交易對列表
        2. 計算每個交易對的策略信號
        3. 檢查是否有信號變化
        4. 執行交易（如有需要）
        5. 管理現有持倉（檢查停損/停利）
        """
        # 獲取訂閱列表
        subscriptions = config.get("subscriptions", [])
        if not subscriptions:
            logger.warning("⚠️ 沒有訂閱的交易對")
            return

        for sub in subscriptions:
            symbol = sub.get("symbol")
            strategy = sub.get("strategy")
            strategy_params = sub.get("params", {})
            timeframe = sub.get("timeframe", "1h")

            if not symbol or not strategy:
                continue

            # 獲取當前持倉狀態
            position_info = self._get_position_info(symbol)

            # 計算策略信號
            signal = self._calculate_signal(symbol, strategy, strategy_params, timeframe)

            if signal is None:
                continue

            # 處理信號
            self._process_signal(
                symbol=symbol,
                signal=signal,
                strategy=strategy,
                position_info=position_info,
                config=config,
            )

    def _get_position_info(self, symbol: str) -> dict | None:
        """獲取當前持倉資訊"""
        try:
            # 從數據庫獲取
            watchlist = self.db.get_watchlist(self.user_id)
            for w in watchlist:
                if w["symbol"] == symbol:
                    return {
                        "position": w["position"],  # 1=多頭，-1=空頭，0=空倉
                        "entry_price": w["entry_price"],
                        "pnl_pct": w["pnl_pct"],
                    }
            return None
        except Exception as e:
            logger.error(f"獲取持倉資訊失敗 {symbol}: {e}")
            return None

    def _calculate_signal(
        self,
        symbol: str,
        strategy: str,
        params: dict,
        timeframe: str,
    ) -> int | None:
        """
        計算策略信號

        Returns:
            信號：1=買入，-1=賣出，0=觀望，None=計算失敗
        """
        try:
            # 獲取 K 線數據
            df = data_service.get_kline(symbol, timeframe=timeframe, limit=100)

            if df is None or len(df) < 50:
                logger.warning(f"數據不足 {symbol} {timeframe}")
                return None

            # 轉換為 OHLCV 格式
            ohlcv = []
            for _, row in df.iterrows():
                ohlcv.append(
                    {
                        "timestamp": int(row["timestamp"]),
                        "open": row["open"],
                        "high": row["high"],
                        "low": row["low"],
                        "close": row["close"],
                        "volume": row["volume"],
                    }
                )

            # 計算信號
            signals = get_signal(ohlcv, strategy, params)
            current_signal = signals[-1] if signals else 0

            return current_signal

        except Exception as e:
            logger.error(f"計算信號失敗 {symbol}: {e}")
            return None

    def _process_signal(
        self,
        symbol: str,
        signal: int,
        strategy: str,
        position_info: dict | None,
        config: dict,
    ):
        """
        處理交易信號

        Args:
            symbol: 交易對
            signal: 信號 (1=買入，-1=賣出，0=觀望)
            strategy: 策略名稱
            position_info: 當前持倉資訊
            config: 策略配置
        """
        if not position_info:
            # 無持倉記錄，檢查是否開倉
            if signal != 0:
                self._try_open_position(symbol, signal, strategy, config)
        else:
            current_position = position_info["position"]

            if current_position == 0:
                # 空倉，檢查是否開倉
                if signal != 0:
                    self._try_open_position(symbol, signal, strategy, config)
            else:
                # 有持倉，檢查是否平倉或反轉
                if signal == 0:
                    # 信號消失，平倉
                    self._close_position(symbol, current_position, strategy, "信號消失", config)
                elif signal == -current_position:
                    # 信號反轉，平倉並反向開倉
                    self._reverse_position(symbol, current_position, signal, strategy, config)
                else:
                    # 信號維持，檢查停損/停利
                    self._check_stop_loss_take_profit(symbol, current_position, position_info, config)

    def _try_open_position(
        self,
        symbol: str,
        signal: int,
        strategy: str,
        config: dict,
    ):
        """嘗試開倉"""
        # 風險檢查
        can_open, reason = self.risk_manager.can_open_position()
        if not can_open:
            logger.warning(f"⚠️ 無法開倉 {symbol}: {reason}")
            return

        # 獲取當前價格
        ticker = self.executor.get_ticker(symbol)
        if not ticker:
            logger.error(f"無法獲取價格 {symbol}")
            return

        current_price = ticker["last"]

        # 計算倉位大小
        equity = self.risk_manager._current_equity
        stop_loss_price = self.risk_manager.calculate_stop_loss(current_price, "long" if signal > 0 else "short")

        position_size = self.risk_manager.calculate_position_size(equity, current_price, stop_loss_price)

        if position_size <= 0:
            logger.warning(f"倉位大小無效 {symbol}")
            return

        # 執行訂單
        side = "buy" if signal > 0 else "sell"
        result = self.executor.create_market_order(symbol, side, position_size)

        if result.success:
            # 更新持倉記錄
            self._update_position(
                symbol=symbol,
                position=signal,
                entry_price=current_price,
                pnl_pct=0,
            )

            # 記錄交易日誌
            self._log_trade(
                symbol=symbol,
                action="開倉",
                side=signal,
                price=current_price,
                pnl_pct=0,
                fee=result.fee or 0,
                reason=f"策略信號：{strategy}",
            )

            # 更新風險管理器
            self.risk_manager.increment_position()

            logger.info(f"✅ 開倉成功：{side.upper()} {position_size} {symbol} @ {current_price} (策略：{strategy})")
        else:
            logger.error(f"❌ 開倉失敗 {symbol}: {result.error}")

    def _close_position(
        self,
        symbol: str,
        position: int,
        strategy: str,
        reason: str,
        config: dict,
    ):
        """平倉"""
        # 獲取當前價格
        ticker = self.executor.get_ticker(symbol)
        if not ticker:
            logger.error(f"無法獲取價格 {symbol}")
            return

        current_price = ticker["last"]

        # 執行平倉訂單
        side = "sell" if position > 0 else "buy"  # 多頭賣出，空頭買回
        position_info = self._get_position_info(symbol)

        # 計算平倉損益
        entry_price = position_info.get("entry_price", current_price) if position_info else current_price
        if position > 0:
            pnl_pct = (current_price - entry_price) / entry_price * 100
        else:
            pnl_pct = (entry_price - current_price) / entry_price * 100

        # 估算平倉數量（從持倉資訊）
        equity = self.risk_manager._current_equity
        estimated_size = equity / current_price  # 簡化估算

        result = self.executor.create_market_order(symbol, side, estimated_size)

        if result.success:
            # 更新持倉記錄
            self._update_position(
                symbol=symbol,
                position=0,
                entry_price=0,
                pnl_pct=0,
            )

            # 記錄交易日誌
            self._log_trade(
                symbol=symbol,
                action="平倉",
                side=position,
                price=current_price,
                pnl_pct=pnl_pct,
                pnl_amount=equity * pnl_pct / 100,
                fee=result.fee or 0,
                reason=reason,
            )

            # 更新風險管理器
            self.risk_manager.add_daily_pnl(equity * pnl_pct / 100)
            self.risk_manager.decrement_position()

            logger.info(f"✅ 平倉成功：{symbol} {reason} | 損益：{pnl_pct:+.2f}% (${equity * pnl_pct / 100:+,.2f})")
        else:
            logger.error(f"❌ 平倉失敗 {symbol}: {result.error}")

    def _reverse_position(
        self,
        symbol: str,
        current_position: int,
        new_signal: int,
        strategy: str,
        config: dict,
    ):
        """反轉持倉（先平倉再反向開倉）"""
        logger.info(f"🔄 反轉持倉 {symbol}: {current_position} -> {new_signal}")

        # 先平倉
        self._close_position(symbol, current_position, strategy, "信號反轉", config)

        # 再反向開倉
        time.sleep(1)  # 避免 API 頻率限制
        self._try_open_position(symbol, new_signal, strategy, config)

    def _check_stop_loss_take_profit(
        self,
        symbol: str,
        position: int,
        position_info: dict,
        config: dict,
    ):
        """檢查停損/停利"""
        entry_price = position_info.get("entry_price", 0)
        if not entry_price:
            return

        # 獲取當前價格
        ticker = self.executor.get_ticker(symbol)
        if not ticker:
            return

        current_price = ticker["last"]

        # 計算停損/停利價格
        if position > 0:  # 多頭
            stop_loss = entry_price * (1 - self.risk_manager.config.stop_loss_pct / 100)
            take_profit = entry_price * (1 + self.risk_manager.config.take_profit_pct / 100)

            if current_price <= stop_loss:
                self._close_position(symbol, position, "STP", "觸發停損", config)
            elif current_price >= take_profit:
                self._close_position(symbol, position, "TP", "觸發停利", config)

        else:  # 空頭
            stop_loss = entry_price * (1 + self.risk_manager.config.stop_loss_pct / 100)
            take_profit = entry_price * (1 - self.risk_manager.config.take_profit_pct / 100)

            if current_price >= stop_loss:
                self._close_position(symbol, position, "STP", "觸發停損", config)
            elif current_price <= take_profit:
                self._close_position(symbol, position, "TP", "觸發停利", config)

    def _update_position(
        self,
        symbol: str,
        position: int,
        entry_price: float,
        pnl_pct: float,
    ):
        """更新持倉記錄到數據庫"""
        try:
            watchlist = self.db.get_watchlist(self.user_id)
            watch_id = None

            for w in watchlist:
                if w["symbol"] == symbol:
                    watch_id = w["id"]
                    break

            if watch_id:
                self.db.update_watch(
                    watch_id,
                    position=position,
                    entry_price=entry_price,
                    pnl_pct=pnl_pct,
                )
            else:
                # 創建新的 watchlist 記錄
                self.db.add_watchlist(
                    user_id=self.user_id,
                    symbol=symbol,
                    strategy="auto_trading",
                    timeframe="1h",
                    initial_equity=self.risk_manager._current_equity,
                    position=position,
                    entry_price=entry_price,
                )
        except Exception as e:
            logger.error(f"更新持倉記錄失敗：{e}")

    def _log_trade(
        self,
        symbol: str,
        action: str,
        side: int,
        price: float,
        pnl_pct: float = 0,
        pnl_amount: float = 0,
        fee: float = 0,
        reason: str = "",
    ):
        """記錄交易日誌到數據庫"""
        try:
            watchlist = self.db.get_watchlist(self.user_id)
            watch_id = None

            for w in watchlist:
                if w["symbol"] == symbol:
                    watch_id = w["id"]
                    break

            if watch_id:
                equity = self.risk_manager._current_equity
                self.db.log_trade(
                    watch_id=watch_id,
                    user_id=self.user_id,
                    symbol=symbol,
                    action=action,
                    side=side,
                    price=price,
                    equity_before=equity,
                    equity_after=equity + pnl_amount,
                    pnl_pct=pnl_pct,
                    pnl_amount=pnl_amount,
                    fee=fee,
                    reason=reason,
                )
        except Exception as e:
            logger.error(f"記錄交易日誌失敗：{e}")

    def get_status(self) -> dict:
        """獲取自動交易狀態"""
        return {
            "running": self._running,
            "user_id": self.user_id,
            "risk_report": self.risk_manager.get_risk_report() if self.risk_manager else None,
        }


def execute_auto_trade(user_id: int, strategy_id: int):
    """
    Celery 任務：執行自動交易

    這是一個異步任務入口，可由 Celery 調度

    Args:
        user_id: 用戶 ID
        strategy_id: 策略配置 ID
    """
    trader = AutoTrader(user_id)
    trader.start(strategy_id)
