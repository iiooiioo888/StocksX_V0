"""
交易執行器 - 負責與交易所 API 交互執行買賣訂單
============================================
支援交易所：Binance、OKX、Bybit、Gate.io 等（透過 CCXT）
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import ccxt

logger = logging.getLogger(__name__)


@dataclass
class OrderResult:
    """訂單執行結果"""

    success: bool
    order_id: str | None = None
    symbol: str | None = None
    side: str | None = None  # 'buy' or 'sell'
    type: str | None = None  # 'market' or 'limit'
    price: float | None = None
    amount: float | None = None
    filled: float | None = None
    remaining: float | None = None
    fee: float | None = None
    error: str | None = None


class TradeExecutor:
    """
    交易執行器

    功能：
    - 連接多個交易所（透過 CCXT）
    - 執行市價單/限價單
    - 支援現貨和合約交易
    - 自動重試機制
    """

    def __init__(
        self,
        exchange_id: str = "binance",
        api_key: str | None = None,
        api_secret: str | None = None,
        sandbox: bool = True,
        options: dict | None = None,
    ):
        """
        初始化交易執行器

        Args:
            exchange_id: 交易所 ID (binance, okx, bybit, etc.)
            api_key: API Key
            api_secret: API Secret
            sandbox: 是否使用測試網絡
            options: CCXT 額外配置選項
        """
        self.exchange_id = exchange_id
        self.sandbox = sandbox
        self.exchange = self._create_exchange(exchange_id, api_key, api_secret, sandbox, options)
        self._max_retries = 3
        self._retry_delay = 1.0  # 秒

    def _create_exchange(
        self,
        exchange_id: str,
        api_key: str | None,
        api_secret: str | None,
        sandbox: bool,
        options: dict | None,
    ) -> ccxt.Exchange:
        """創建交易所連接"""
        exchange_class = getattr(ccxt, exchange_id)

        config = {
            "enableRateLimit": True,
            "timeout": 30000,
        }

        if api_key and api_secret:
            config.update(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                }
            )

        if options:
            config.setdefault("options", {}).update(options)

        # 配置測試網絡
        if sandbox and exchange_id in ["binance", "okx", "bybit"]:
            if exchange_id == "binance":
                config["urls"] = {
                    "api": {
                        "public": "https://testnet.binance.vision/api",
                        "private": "https://testnet.binance.vision/api",
                    }
                }

        exchange = exchange_class(config)
        logger.info(f"✅ 交易所連接成功：{exchange_id} (sandbox={sandbox})")
        return exchange

    def load_markets(self) -> dict:
        """載入交易市場資訊"""
        return self.exchange.load_markets()

    def get_balance(self, currency: str | None = None) -> dict:
        """
        取得帳戶餘額

        Args:
            currency: 指定幣種，None 返回全部

        Returns:
            餘額字典 {free: 可用，used: 凍結，total: 總計}
        """
        try:
            balance = self.exchange.fetch_balance()
            if currency:
                return balance.get(currency, {})
            return balance
        except Exception as e:
            logger.error(f"取得餘額失敗：{e}")
            return {}

    def get_position(self, symbol: str) -> dict | None:
        """
        取得持倉資訊（合約）

        Args:
            symbol: 交易對 (e.g., "BTC/USDT:USDT")

        Returns:
            持倉資訊 {side, size, entryPrice, unrealizedPnl, ...}
        """
        try:
            positions = self.exchange.fetch_positions([symbol])
            for pos in positions:
                if pos["symbol"] == symbol:
                    return pos
            return None
        except Exception as e:
            logger.error(f"取得持倉失敗 {symbol}: {e}")
            return None

    def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        params: dict | None = None,
    ) -> OrderResult:
        """
        創建市價單

        Args:
            symbol: 交易對 (e.g., "BTC/USDT" 或 "BTC/USDT:USDT")
            side: 'buy' 或 'sell'
            amount: 數量
            params: 額外參數（如槓桿）

        Returns:
            OrderResult 訂單結果
        """
        return self._create_order("market", symbol, side, amount, None, params)

    def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        params: dict | None = None,
    ) -> OrderResult:
        """
        創建限價單

        Args:
            symbol: 交易對
            side: 'buy' 或 'sell'
            amount: 數量
            price: 價格
            params: 額外參數

        Returns:
            OrderResult 訂單結果
        """
        return self._create_order("limit", symbol, side, amount, price, params)

    def _create_order(
        self,
        order_type: str,
        symbol: str,
        side: str,
        amount: float,
        price: float | None,
        params: dict | None,
    ) -> OrderResult:
        """訂單執行核心邏輯（含重試機制）"""
        for attempt in range(self._max_retries):
            try:
                # 執行訂單
                order = self.exchange.create_order(
                    symbol=symbol,
                    type=order_type,
                    side=side,
                    amount=amount,
                    price=price,
                    params=params or {},
                )

                # 計算手續費
                fee = None
                if order.get("fee"):
                    fee = order["fee"].get("cost", 0)

                logger.info(
                    f"📝 訂單執行成功：{side.upper()} {amount} {symbol} "
                    f"@ {order.get('price', 'MARKET')} (ID: {order['id']})"
                )

                return OrderResult(
                    success=True,
                    order_id=order["id"],
                    symbol=order.get("symbol", symbol),
                    side=order.get("side", side),
                    type=order.get("type", order_type),
                    price=order.get("price", price),
                    amount=order.get("amount", amount),
                    filled=order.get("filled", 0),
                    remaining=order.get("remaining", amount),
                    fee=fee,
                )

            except ccxt.InsufficientFunds as e:
                error_msg = f"餘額不足：{e!s}"
                logger.error(error_msg)
                return OrderResult(success=False, error=error_msg)

            except ccxt.InvalidOrder as e:
                error_msg = f"無效訂單：{e!s}"
                logger.error(error_msg)
                return OrderResult(success=False, error=error_msg)

            except (ccxt.NetworkError, ccxt.ExchangeError) as e:
                error_msg = f"交易所錯誤：{e!s}"
                logger.warning(f"嘗試 {attempt + 1}/{self._max_retries}: {error_msg}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
                else:
                    return OrderResult(success=False, error=error_msg)

            except Exception as e:
                error_msg = f"未知錯誤：{e!s}"
                logger.error(error_msg)
                return OrderResult(success=False, error=error_msg)

        return OrderResult(success=False, error="未知錯誤")

    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """取消訂單"""
        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"✅ 訂單已取消：{order_id}")
            return True
        except Exception as e:
            logger.error(f"取消訂單失敗 {order_id}: {e}")
            return False

    def cancel_all_orders(self, symbol: str) -> int:
        """
        取消所有掛單

        Returns:
            取消的訂單數量
        """
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            count = 0
            for order in orders:
                if self.cancel_order(symbol, order["id"]):
                    count += 1
            return count
        except Exception as e:
            logger.error(f"取消所有訂單失敗 {symbol}: {e}")
            return 0

    def get_ticker(self, symbol: str) -> dict | None:
        """取得即時價格"""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"取得價格失敗 {symbol}: {e}")
            return None

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        設定槓桿（合約）

        Args:
            symbol: 交易對
            leverage: 槓桿倍數

        Returns:
            是否成功
        """
        try:
            self.exchange.set_leverage(leverage, symbol)
            logger.info(f"✅ 槓桿已設定：{symbol} {leverage}x")
            return True
        except Exception as e:
            logger.error(f"設定槓桿失敗 {symbol}: {e}")
            return False

    def set_margin_mode(self, symbol: str, mode: str = "cross") -> bool:
        """
        設定保證金模式（合約）

        Args:
            symbol: 交易對
            mode: 'cross' 或 'isolated'

        Returns:
            是否成功
        """
        try:
            self.exchange.set_margin_mode(mode, symbol)
            logger.info(f"✅ 保證金模式已設定：{symbol} {mode}")
            return True
        except Exception as e:
            logger.error(f"設定保證金模式失敗 {symbol}: {e}")
            return False


def create_executor_from_config(user_id: int, exchange_config: dict) -> TradeExecutor:
    """
    從配置創建交易執行器

    Args:
        user_id: 用戶 ID
        exchange_config: 交易所配置 {
            'exchange_id': 'binance',
            'api_key': '...',
            'api_secret': '...',
            'sandbox': True,
            'options': {...}
        }

    Returns:
        TradeExecutor 實例
    """
    return TradeExecutor(
        exchange_id=exchange_config.get("exchange_id", "binance"),
        api_key=exchange_config.get("api_key"),
        api_secret=exchange_config.get("api_secret"),
        sandbox=exchange_config.get("sandbox", True),
        options=exchange_config.get("options"),
    )
