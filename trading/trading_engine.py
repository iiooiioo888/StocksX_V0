#!/usr/bin/env python3
"""
StocksX 自動化交易引擎
自動跟隨策略信號執行交易

作者：StocksX Team
創建日期：2026-03-22
"""

import asyncio
import json
from datetime import datetime
from typing import Optional
from pathlib import Path
import yaml
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("trading_engine")


class TradingEngine:
    """自動化交易引擎"""

    def __init__(self, config_path: str = "trading/config.yaml"):
        """
        初始化交易引擎

        Args:
            config_path: 配置文件路徑
        """
        self.config = self._load_config(config_path)
        self.api_base = "http://localhost:8000/api"
        self.ws_url = "ws://localhost:8000/ws/signals"

        # 交易狀態
        self.positions: dict[str, dict] = {}  # 持倉
        self.orders: list[dict] = []  # 訂單記錄
        self.daily_pnl = 0.0  # 當日盈虧
        self.total_trades = 0  # 總交易數

        # WebSocket 連接
        self.ws = None
        self.running = False

        logger.info("✅ 交易引擎初始化完成")
        logger.info(f"📊 模擬交易：{self.config['trading']['paper_trading']}")

    def _load_config(self, config_path: str) -> dict:
        """加載配置文件"""
        path = Path(config_path)
        if not path.exists():
            # 創建默認配置
            default_config = {
                "trading": {"enabled": True, "paper_trading": True},
                "broker": {"name": "paper", "api_key": "", "api_secret": ""},
                "risk": {
                    "max_position_size": 10000,
                    "stop_loss_pct": 2.0,
                    "take_profit_pct": 5.0,
                    "max_daily_loss": 1000,
                },
                "strategies": [
                    {"name": "sma_cross", "weight": 0.3, "enabled": True},
                    {"name": "macd_cross", "weight": 0.3, "enabled": True},
                    {"name": "rsi", "weight": 0.4, "enabled": True},
                ],
            }

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                yaml.dump(default_config, f)

            logger.info(f"📝 創建默認配置：{config_path}")
            return default_config

        with open(path) as f:
            return yaml.safe_load(f)

    async def start(self):
        """啟動交易引擎"""
        logger.info("=" * 80)
        logger.info("🚀 StocksX 自動化交易引擎啟動")
        logger.info("=" * 80)

        self.running = True

        # 連接 WebSocket
        await self._connect_websocket()

        # 啟動風險監控
        asyncio.create_task(self._risk_monitor())

        # 啟動性能報告
        asyncio.create_task(self._performance_report())

        logger.info("✅ 交易引擎已啟動")
        logger.info(f"📡 WebSocket: {self.ws_url}")
        logger.info(f"💹 策略數量：{len(self.config['strategies'])}")
        logger.info("=" * 80)

    async def stop(self):
        """停止交易引擎"""
        logger.info("⏹️  停止交易引擎...")
        self.running = False

        if self.ws:
            await self.ws.close()

        logger.info("✅ 交易引擎已停止")

    async def _connect_websocket(self):
        """連接 WebSocket 接收信號"""
        import websockets

        try:
            self.ws = await websockets.connect(self.ws_url)
            logger.info("✅ WebSocket 已連接")

            # 開始接收信號
            await self._receive_signals()

        except Exception as e:
            logger.error(f"❌ WebSocket 連接失敗：{e}")
            # 5 秒後重連
            await asyncio.sleep(5)
            await self._connect_websocket()

    async def _receive_signals(self):
        """接收並處理交易信號"""
        try:
            async for message in self.ws:
                if not self.running:
                    break

                data = json.loads(message)

                if data.get("type") == "signals":
                    await self._process_signals(data["data"])

        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️  WebSocket 連接斷開")
            await asyncio.sleep(3)
            await self._connect_websocket()

    async def _process_signals(self, signals: list[dict]):
        """
        處理交易信號

        Args:
            signals: 信號列表 [{strategy, signal, price, timestamp}, ...]
        """
        logger.info(f"📡 收到 {len(signals)} 個信號")

        for signal_data in signals:
            strategy_name = signal_data.get("strategy")
            signal_type = signal_data.get("signal")  # BUY/SELL
            price = signal_data.get("price")

            # 檢查策略是否啟用
            strategy_config = self._get_strategy_config(strategy_name)
            if not strategy_config or not strategy_config.get("enabled"):
                continue

            # 執行交易
            if signal_type == "BUY":
                await self._execute_buy(strategy_name, price, signal_data)
            elif signal_type == "SELL":
                await self._execute_sell(strategy_name, price, signal_data)

    async def _execute_buy(self, strategy: str, price: float, signal_data: dict):
        """執行買入"""
        symbol = signal_data.get("symbol", "STOCKX")
        quantity = self._calculate_quantity(price)

        if quantity <= 0:
            logger.warning("⚠️  數量為 0，跳過買入")
            return

        # 風險檢查
        if not await self._check_risk(symbol, quantity, price):
            logger.warning("⚠️  風險檢查失敗，跳過買入")
            return

        # 下單
        order = {
            "strategy": strategy,
            "symbol": symbol,
            "side": "BUY",
            "quantity": quantity,
            "price": price,
            "timestamp": datetime.now().isoformat(),
            "type": "MARKET",
        }

        if self.config["trading"]["paper_trading"]:
            # 模擬交易
            await self._place_paper_order(order)
        else:
            # 真實交易（需要對接券商 API）
            await self._place_real_order(order)

        logger.info(f"📈 買入：{symbol} x {quantity} @ ${price}")

    async def _execute_sell(self, strategy: str, price: float, signal_data: dict):
        """執行賣出"""
        symbol = signal_data.get("symbol", "STOCKX")

        # 檢查是否有持倉
        if symbol not in self.positions:
            logger.info(f"ℹ️  無持倉，跳過賣出：{symbol}")
            return

        position = self.positions[symbol]
        quantity = position["quantity"]

        # 計算盈虧
        pnl = (price - position["avg_price"]) * quantity
        pnl_pct = ((price / position["avg_price"]) - 1) * 100

        # 平倉
        order = {
            "strategy": strategy,
            "symbol": symbol,
            "side": "SELL",
            "quantity": quantity,
            "price": price,
            "timestamp": datetime.now().isoformat(),
            "type": "MARKET",
        }

        if self.config["trading"]["paper_trading"]:
            await self._place_paper_order(order)
        else:
            await self._place_real_order(order)

        # 更新持倉
        del self.positions[symbol]
        self.daily_pnl += pnl
        self.total_trades += 1

        logger.info(f"📉 賣出：{symbol} x {quantity} @ ${price} | 盈虧：${pnl:.2f} ({pnl_pct:+.2f}%)")

    def _calculate_quantity(self, price: float) -> int:
        """計算下單數量"""
        max_size = self.config["risk"]["max_position_size"]
        quantity = int(max_size / price)
        return max(0, quantity)

    async def _check_risk(self, symbol: str, quantity: int, price: float) -> bool:
        """
        風險檢查

        Returns:
            bool: 是否通過檢查
        """
        # 檢查持倉
        if symbol in self.positions:
            logger.info(f"ℹ️  已持有 {symbol}，跳過")
            return False

        # 檢查每日最大虧損
        if self.daily_pnl < -self.config["risk"]["max_daily_loss"]:
            logger.warning("⚠️  達到每日最大虧損限制")
            return False

        # 檢查總持倉
        total_value = sum(p["quantity"] * p["price"] for p in self.positions.values())
        if total_value + quantity * price > self.config["risk"]["max_position_size"] * 10:
            logger.warning("⚠️  總持倉超限")
            return False

        return True

    async def _place_paper_order(self, order: dict):
        """下模擬訂單"""
        self.orders.append(order)

        if order["side"] == "BUY":
            # 更新持倉
            self.positions[order["symbol"]] = {
                "strategy": order["strategy"],
                "quantity": order["quantity"],
                "avg_price": order["price"],
                "entry_time": order["timestamp"],
            }

        logger.info(f"📝 [模擬] {order['side']} {order['symbol']} x {order['quantity']} @ ${order['price']}")

    async def _place_real_order(self, order: dict):
        """下真實訂單（需要對接券商 API）"""
        # TODO: 對接 Alpaca/Binance 等券商 API
        logger.info(f"💹 [真實] {order['side']} {order['symbol']} x {order['quantity']} @ ${order['price']}")

    def _get_strategy_config(self, name: str) -> Optional[dict]:
        """獲取策略配置"""
        for strategy in self.config["strategies"]:
            if strategy["name"] == name:
                return strategy
        return None

    async def _risk_monitor(self):
        """風險監控（每分鐘）"""
        while self.running:
            await asyncio.sleep(60)

            # 檢查止損/止盈
            for symbol, position in list(self.positions.items()):
                current_price = position["price"]  # 實際應該從市場獲取
                avg_price = position["avg_price"]

                # 止損檢查
                loss_pct = ((current_price / avg_price) - 1) * 100
                if loss_pct < -self.config["risk"]["stop_loss_pct"]:
                    logger.warning(f"🚨 止損：{symbol} ({loss_pct:.2f}%)")
                    # 觸發止損賣出
                    # await self._execute_sell(...)

                # 止盈檢查
                if loss_pct > self.config["risk"]["take_profit_pct"]:
                    logger.info(f"✅ 止盈：{symbol} ({loss_pct:.2f}%)")
                    # 觸發止盈賣出

    async def _performance_report(self):
        """性能報告（每小時）"""
        while self.running:
            await asyncio.sleep(3600)

            total_pnl = (
                sum((p.get("price", 0) - p["avg_price"]) * p["quantity"] for p in self.positions.values())
                + self.daily_pnl
            )

            logger.info("=" * 60)
            logger.info("📊 性能報告")
            logger.info("=" * 60)
            logger.info(f"總交易數：{self.total_trades}")
            logger.info(f"當日盈虧：${self.daily_pnl:.2f}")
            logger.info(f"持倉數：{len(self.positions)}")
            logger.info(f"未平盈虧：${total_pnl:.2f}")
            logger.info(f"訂單總數：{len(self.orders)}")
            logger.info("=" * 60)


async def main():
    """主函數"""
    engine = TradingEngine()

    try:
        await engine.start()

        # 保持運行
        while engine.running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        await engine.stop()
    except Exception as e:
        logger.error(f"❌ 交易引擎錯誤：{e}")
        await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())
