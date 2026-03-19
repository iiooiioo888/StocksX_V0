# WebSocket 即時推送服務（FastAPI）
# 用於策略監控的即時價格和信號推送

from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt

logger = logging.getLogger(__name__)

# 安全配置（從環境變數讀取）
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    # 開發環境自動生成（每次重啟失效，提醒使用者設定正式密鑰）
    SECRET_KEY = secrets.token_hex(32)
    logger.warning("SECRET_KEY 未設定，已自動生成臨時密鑰（重啟後失效）。生產環境請在 .env 中配置固定密鑰。")
ALGORITHM = "HS256"

app = FastAPI(title="StocksX WebSocket Service")

# 連接管理器
class ConnectionManager:
    def __init__(self):
        # {user_id: {symbol: websocket}}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, symbol: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        self.active_connections[user_id][symbol] = websocket
        logger.info(f"WebSocket 連接：user_id={user_id}, symbol={symbol}")
    
    def disconnect(self, user_id: int, symbol: str):
        if user_id in self.active_connections:
            if symbol in self.active_connections[user_id]:
                del self.active_connections[user_id][symbol]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket 斷開：user_id={user_id}, symbol={symbol}")
    
    async def send_personal_message(self, message: dict, user_id: int, symbol: Optional[str] = None):
        if user_id not in self.active_connections:
            return
        
        if symbol:
            websocket = self.active_connections[user_id].get(symbol)
            if websocket:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"發送失敗：{e}")
        else:
            # 發送給用戶的所有連接
            for ws in self.active_connections[user_id].values():
                try:
                    await ws.send_json(message)
                except Exception:
                    pass
    
    async def broadcast(self, message: dict):
        """廣播給所有連接"""
        for user_connections in self.active_connections.values():
            for websocket in user_connections.values():
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


# ════════════════════════════════════════════════════════════
# 幣安價格數據（真實 API）
# ════════════════════════════════════════════════════════════

# 全域交易所實例（避免重複建立）
_binance_spot = None
_binance_future = None

def get_binance_exchange(market_type: str = "spot"):
    """取得幣安交易所實例"""
    global _binance_spot, _binance_future
    
    try:
        import ccxt
        
        if market_type == "spot":
            if _binance_spot is None:
                _binance_spot = ccxt.binance({
                    'options': {'defaultType': 'spot'},
                    'timeout': 10000,
                })
            return _binance_spot
        else:  # future
            if _binance_future is None:
                _binance_future = ccxt.binance({
                    'options': {'defaultType': 'future'},
                    'timeout': 10000,
                })
            return _binance_future
    except Exception as e:
        logger.error(f"建立交易所實例失敗：{e}")
        return None


async def fetch_price(symbol: str) -> Optional[Dict[str, Any]]:
    """
    取得即時價格（使用幣安 API）
    
    Args:
        symbol: 交易對（如 BTC/USDT, BTC/USDT:USDT）
    
    Returns:
        {
            "symbol": str,
            "price": float,
            "change_pct": float,
            "high_24h": float,
            "low_24h": float,
            "volume_24h": float,
            "timestamp": int
        }
    """
    try:
        # 判斷市場類型
        if ":" in symbol:
            # 永續合約 BTC/USDT:USDT
            market_type = "future"
            binance_symbol = symbol.replace("/", "")
        else:
            # 現貨 BTC/USDT
            market_type = "spot"
            binance_symbol = symbol.replace("/", "")
        
        # 取得交易所實例
        exchange = get_binance_exchange(market_type)
        if not exchange:
            return None
        
        # 取得行情數據
        ticker = exchange.fetch_ticker(symbol)
        
        # 提取數據
        last_price = ticker.get('last', 0)
        change_pct = ticker.get('percentage', 0)
        high_24h = ticker.get('high', 0)
        low_24h = ticker.get('low', 0)
        volume_24h = ticker.get('baseVolume', 0)
        
        if last_price and last_price > 0:
            return {
                "symbol": symbol,
                "price": round(last_price, 2),
                "change_pct": round(change_pct, 2) if change_pct else 0,
                "high_24h": round(high_24h, 2) if high_24h else 0,
                "low_24h": round(low_24h, 2) if low_24h else 0,
                "volume_24h": round(volume_24h, 2) if volume_24h else 0,
                "timestamp": int(time.time() * 1000),
                "market_type": market_type
            }
        else:
            logger.warning(f"無效的價格數據：{symbol}")
            return None
            
    except ccxt.NetworkError as e:
        logger.warning(f"網路錯誤 {symbol}: {e}")
        return None
    except ccxt.ExchangeError as e:
        logger.warning(f"交易所錯誤 {symbol}: {e}")
        return None
    except Exception as e:
        logger.error(f"取得價格失敗 {symbol}: {type(e).__name__}: {e}")
        return None


# 模擬信號生成
async def generate_signal(symbol: str, price: float) -> Optional[Dict[str, Any]]:
    """模擬生成交易信號（實際應從策略引擎取得）"""
    import random
    
    # 隨機生成信號
    if random.random() < 0.1:  # 10% 機率生成信號
        signal_type = random.choice(["BUY", "SELL"])
        return {
            "symbol": symbol,
            "action": signal_type,
            "price": price,
            "strategy": "sma_cross",
            "confidence": round(random.uniform(0.6, 0.95), 2),
            "timestamp": int(time.time() * 1000)
        }
    return None


# 價格推送任務
async def price_push_task():
    """定期推送價格更新"""
    # 預設監控的交易對列表
    monitor_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]

    while True:
        try:
            # 取得所有已訂閱的交易對
            all_subscribed = set()
            for user_connections in manager.active_connections.values():
                all_subscribed.update(user_connections.keys())
            
            # 如果沒有訂閱，使用預設列表
            symbols_to_fetch = all_subscribed if all_subscribed else set(monitor_symbols)
            
            for symbol in symbols_to_fetch:
                price_data = await fetch_price(symbol)
                if price_data:
                    # 推送給所有訂閱該交易對的用戶
                    for user_id, connections in list(manager.active_connections.items()):
                        if symbol in connections:
                            # 直接通過 WebSocket 發送
                            websocket = connections[symbol]
                            try:
                                await websocket.send_json({
                                    "type": "price_update",
                                    "data": price_data
                                })
                            except Exception:
                                pass
        except Exception as e:
            logger.error(f"價格推送任務錯誤：{e}")

        await asyncio.sleep(1)  # 每秒推送一次


# 信號推送任務
async def signal_push_task():
    """監聽並推送交易信號"""
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    
    while True:
        for symbol in symbols:
            try:
                price_data = await fetch_price(symbol)
                if price_data:
                    signal = await generate_signal(symbol, price_data["price"])
                    if signal:
                        # 推送給所有訂閱該交易對的用戶
                        for user_id, connections in list(manager.active_connections.items()):
                            if symbol in connections:
                                await manager.send_personal_message(
                                    message={
                                        "type": "signal",
                                        "data": signal
                                    },
                                    user_id=user_id,
                                    symbol=symbol
                                )
            except Exception as e:
                logger.error(f"信號推送錯誤 {symbol}: {e}")
        
        await asyncio.sleep(5)  # 每 5 秒檢查一次


@app.on_event("startup")
async def startup_event():
    """啟動時開始推送任務"""
    asyncio.create_task(price_push_task())
    asyncio.create_task(signal_push_task())
    logger.info("WebSocket 服務已啟動")


def verify_token(token: str) -> Optional[dict]:
    """驗證 JWT 令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket 端點 - 訂閱即時價格/信號

    連接範例：
    ws://localhost:8001/ws
    ws://localhost:8001/ws?token=YOUR_JWT_TOKEN

    客戶端需要發送訂閱訊息：
    {"action": "subscribe", "symbols": ["BTC/USDT", "ETH/USDT"]}
    """
    # 驗證令牌
    user_id = 1  # 預設用戶 ID

    if token:
        payload = verify_token(token)
        if payload:
            user_id = int(payload.get("sub", 1))

    # 接受連接
    await websocket.accept()
    logger.info("WebSocket 連接：user_id=%s", user_id)

    # 發送歡迎訊息
    await websocket.send_json({
        "type": "connected",
        "symbol": "*",
        "message": "已連接 WebSocket 服務，請發送訂閱訊息",
        "timestamp": int(time.time() * 1000)
    })

    # 等待客戶端發送訂閱
    subscribed_symbols = set()

    try:
        while True:
            # 接收客戶端訊息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 處理訂閱/取消訂閱
            action = message.get("action")

            if action == "subscribe":
                symbols = message.get("symbols", [])
                for symbol in symbols:
                    subscribed_symbols.add(symbol)
                    # 將連接添加到管理器
                    if user_id not in manager.active_connections:
                        manager.active_connections[user_id] = {}
                    manager.active_connections[user_id][symbol] = websocket
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": list(subscribed_symbols)
                })
                logger.info(f"用戶 %s 訂閱：{subscribed_symbols}")

            elif action == "unsubscribe":
                symbols = message.get("symbols", [])
                for symbol in symbols:
                    if symbol in subscribed_symbols:
                        subscribed_symbols.remove(symbol)
                        if user_id in manager.active_connections:
                            if symbol in manager.active_connections[user_id]:
                                del manager.active_connections[user_id][symbol]
                await websocket.send_json({
                    "type": "unsubscribed",
                    "symbols": list(subscribed_symbols)
                })

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket 斷開連接：user_id=%s", user_id)
        # 清理連接
        if user_id in manager.active_connections:
            del manager.active_connections[user_id]
    except Exception as e:
        logger.error(f"WebSocket 錯誤：{e}")
        # 清理連接
        if user_id in manager.active_connections:
            del manager.active_connections[user_id]


@app.get("/subscriptions/{user_id}")
async def get_subscriptions(user_id: int):
    """取得用戶的訂閱列表"""
    subscriptions = list(manager.active_connections.get(user_id, {}).keys())
    return {
        "user_id": user_id,
        "subscriptions": subscriptions,
        "count": len(subscriptions)
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "active_connections": sum(len(conns) for conns in manager.active_connections.values()),
        "users": len(manager.active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
