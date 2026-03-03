# 幣安 WebSocket 服務（專業版）
# 根據幣安官方文檔優化更新頻率和數據流管理

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import websockets as ws_client  # 用於連接幣安

app = FastAPI(title="StocksX Binance WebSocket Service")

# ════════════════════════════════════════════════════════════
# 幣安 WebSocket 配置
# ════════════════════════════════════════════════════════════

# 幣安 WebSocket 端點
BINANCE_WS = "wss://stream.binance.com:9443/ws"
BINANCE_WS_TESTNET = "wss://testnet.binance.vision/ws"

# 數據流更新頻率配置（毫秒）
STREAM_INTERVALS = {
    "trade": 0,           # 實時（事件驅動）
    "aggTrade": 0,        # 實時（事件驅動）
    "bookTicker": 0,      # 實時（事件驅動）
    "ticker": 1000,       # 24h Ticker - 1 秒
    "miniTicker": 1000,   # Mini Ticker - 1 秒
    "kline_1s": 1000,     # 1s K 線 - 1 秒
    "kline": 2000,        # 其他 K 線 - 2 秒
    "depth": 1000,        # 深度 - 1 秒
    "depth_100ms": 100,   # 深度 - 100ms
    "avgPrice": 1000,     # 平均價格 - 1 秒
}

# 連接管理器
class ConnectionManager:
    def __init__(self):
        # {user_id: {symbol: websocket}}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        # 幣安連接池
        self.binance_connections: Dict[str, ws_client.WebSocketClientProtocol] = {}
        # 訂閱管理
        self.subscriptions: Dict[int, Set[str]] = {}  # {user_id: {symbols}}
        # 數據流類型
        self.stream_types: Dict[str, str] = {}  # {symbol: stream_type}
    
    async def connect(self, websocket: WebSocket, user_id: int, symbol: str):
        """接受用戶 WebSocket 連接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
            self.subscriptions[user_id] = set()
        self.active_connections[user_id][symbol] = websocket
        self.subscriptions[user_id].add(symbol)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 用戶 {user_id} 連接：{symbol}")
    
    def disconnect(self, user_id: int, symbol: str = None):
        """斷開用戶連接"""
        if user_id in self.active_connections:
            if symbol:
                if symbol in self.active_connections[user_id]:
                    del self.active_connections[user_id][symbol]
                if symbol in self.subscriptions[user_id]:
                    self.subscriptions[user_id].remove(symbol)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    del self.subscriptions[user_id]
            else:
                del self.active_connections[user_id]
                del self.subscriptions[user_id]
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 用戶 {user_id} 斷開：{symbol or '所有'}")
    
    async def broadcast_to_subscribers(self, symbol: str, message: dict):
        """廣播數據給所有訂閱該交易對的用戶"""
        for user_id, symbols in self.subscriptions.items():
            if symbol in symbols or "*" in symbols:  # * 表示訂閱所有
                if user_id in self.active_connections:
                    for sym, ws in self.active_connections[user_id].items():
                        if sym == symbol or sym == "*":
                            try:
                                await ws.send_json(message)
                            except Exception as e:
                                print(f"發送失敗 {symbol} -> 用戶{user_id}: {e}")


manager = ConnectionManager()


# ════════════════════════════════════════════════════════════
# 幣安數據流解析
# ════════════════════════════════════════════════════════════

def parse_binance_message(stream_type: str, data: dict) -> Optional[Dict[str, Any]]:
    """
    解析幣安 WebSocket 數據
    
    Args:
        stream_type: 數據流類型（trade, ticker, kline, depth 等）
        data: 幣安原始數據
    
    Returns:
        統一格式的數據字典
    """
    try:
        if stream_type == "trade" or stream_type == "aggTrade":
            # 逐筆交易
            return {
                "type": "trade",
                "symbol": data.get("s", ""),
                "price": float(data.get("p", 0)),
                "quantity": float(data.get("q", 0)),
                "side": data.get("m", False),  # true=賣方，false=買方
                "timestamp": data.get("T", int(time.time() * 1000))
            }
        
        elif stream_type == "bookTicker":
            # 最優掛單
            return {
                "type": "bookTicker",
                "symbol": data.get("s", ""),
                "bid_price": float(data.get("b", 0)),
                "bid_qty": float(data.get("B", 0)),
                "ask_price": float(data.get("a", 0)),
                "ask_qty": float(data.get("A", 0)),
                "timestamp": data.get("u", int(time.time() * 1000))
            }
        
        elif stream_type == "ticker" or stream_type == "miniTicker":
            # 24h Ticker
            return {
                "type": "ticker",
                "symbol": data.get("s", ""),
                "price": float(data.get("c", 0)),  # 最新價
                "change_pct": float(data.get("P", 0)),  # 24h 漲跌幅
                "high_24h": float(data.get("h", 0)),
                "low_24h": float(data.get("l", 0)),
                "volume_24h": float(data.get("v", 0)),
                "quote_volume_24h": float(data.get("q", 0)),
                "timestamp": data.get("E", int(time.time() * 1000))
            }
        
        elif stream_type.startswith("kline"):
            # K 線數據
            kline = data.get("k", {})
            return {
                "type": "kline",
                "symbol": data.get("s", ""),
                "interval": kline.get("i", "1m"),
                "open": float(kline.get("o", 0)),
                "high": float(kline.get("h", 0)),
                "low": float(kline.get("l", 0)),
                "close": float(kline.get("c", 0)),
                "volume": float(kline.get("v", 0)),
                "is_closed": kline.get("x", False),  # K 線是否收盤
                "timestamp": data.get("E", int(time.time() * 1000))
            }
        
        elif stream_type.startswith("depth"):
            # 深度數據
            return {
                "type": "depth",
                "symbol": data.get("s", ""),
                "bids": data.get("bids", []),  # [[price, qty], ...]
                "asks": data.get("asks", []),
                "timestamp": data.get("E", int(time.time() * 1000))
            }
        
        elif stream_type == "avgPrice":
            # 平均價格
            return {
                "type": "avgPrice",
                "symbol": data.get("s", ""),
                "price": float(data.get("w", 0)),
                "timestamp": int(time.time() * 1000)
            }
        
    except Exception as e:
        print(f"解析錯誤 {stream_type}: {e}")
    
    return None


# ════════════════════════════════════════════════════════════
# 幣安連接管理
# ════════════════════════════════════════════════════════════

async def binance_data_stream(stream_url: str, stream_type: str):
    """
    連接幣安 WebSocket 並轉發數據
    
    Args:
        stream_url: 幣安 WebSocket URL（含 stream 參數）
        stream_type: 數據流類型
    """
    ping_interval = 20  # 幣安每 20 秒發送 Ping
    
    async with ws_client.connect(stream_url, ping_interval=ping_interval) as ws:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 幣安連接成功：{stream_url}")
        
        async for message in ws:
            try:
                data = json.loads(message)
                
                # 解析數據
                parsed = parse_binance_message(stream_type, data)
                
                if parsed:
                    symbol = parsed.get("symbol", "")
                    
                    # 轉發給訂閱用戶
                    await manager.broadcast_to_subscribers(symbol, {
                        "type": "price_update" if stream_type in ["ticker", "miniTicker"] else stream_type,
                        "data": parsed
                    })
                    
            except Exception as e:
                print(f"幣安數據處理錯誤 {stream_url}: {e}")


async def manage_binance_connections():
    """管理幣安連接池（根據用戶訂閱動態調整）"""
    last_subscriptions = set()
    
    while True:
        try:
            # 取得當前所有訂閱
            current_subscriptions = set()
            for symbols in manager.subscriptions.values():
                current_subscriptions.update(symbols)
            
            # 移除不再需要的連接
            to_remove = last_subscriptions - current_subscriptions
            for symbol in to_remove:
                if symbol in manager.binance_connections:
                    await manager.binance_connections[symbol].close()
                    del manager.binance_connections[symbol]
                    print(f"[-] 移除幣安連接：{symbol}")
            
            # 添加新的連接
            to_add = current_subscriptions - last_subscriptions
            for symbol in to_add:
                if symbol not in manager.binance_connections:
                    # 建立幣安連接（使用 miniTicker 以獲取 24h 數據）
                    stream_name = f"{symbol.lower()}@miniTicker"
                    stream_url = f"{BINANCE_WS}/{stream_name}"
                    
                    # 啟動異步任務
                    asyncio.create_task(binance_data_stream(stream_url, "miniTicker"))
                    print(f"[+] 新增幣安連接：{symbol} -> {stream_name}")
            
            last_subscriptions = current_subscriptions
            
        except Exception as e:
            print(f"管理幣安連接錯誤：{e}")
        
        await asyncio.sleep(1)  # 每秒檢查一次


# ════════════════════════════════════════════════════════════
# WebSocket 端點
# ════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    用戶 WebSocket 端點
    
    連接範例：
    ws://localhost:8001/ws
    """
    user_id = 1  # 預設用戶 ID（實際應從 token 解析）
    
    # 接受連接
    await websocket.accept()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 用戶 {user_id} 連接 WebSocket")
    
    # 發送歡迎訊息
    await websocket.send_json({
        "type": "connected",
        "symbol": "*",
        "message": "已連接 StocksX WebSocket 服務，請發送訂閱訊息",
        "timestamp": int(time.time() * 1000)
    })
    
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
                    manager.subscriptions.setdefault(user_id, set()).add(symbol)
                    manager.active_connections.setdefault(user_id, {})[symbol] = websocket
                
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": list(subscribed_symbols)
                })
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 用戶 {user_id} 訂閱：{subscribed_symbols}")
            
            elif action == "unsubscribe":
                symbols = message.get("symbols", [])
                for symbol in symbols:
                    if symbol in subscribed_symbols:
                        subscribed_symbols.remove(symbol)
                        manager.disconnect(user_id, symbol)
                
                await websocket.send_json({
                    "type": "unsubscribed",
                    "symbols": list(subscribed_symbols)
                })
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 用戶 {user_id} 斷開 WebSocket")
        manager.disconnect(user_id)
    
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] WebSocket 錯誤：{e}")
        manager.disconnect(user_id)


# ════════════════════════════════════════════════════════════
# 啟動事件
# ════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """啟動時開始管理幣安連接"""
    asyncio.create_task(manage_binance_connections())
    print("=" * 60)
    print("StocksX Binance WebSocket Service 已啟動")
    print(f"幣安 WebSocket: {BINANCE_WS}")
    print("數據流類型：miniTicker (1 秒更新)")
    print("=" * 60)


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "active_users": len(manager.active_connections),
        "total_subscriptions": sum(len(syms) for syms in manager.subscriptions.values()),
        "binance_connections": len(manager.binance_connections)
    }


@app.get("/subscriptions/{user_id}")
async def get_subscriptions(user_id: int):
    """取得用戶訂閱列表"""
    subscriptions = list(manager.subscriptions.get(user_id, set()))
    return {
        "user_id": user_id,
        "subscriptions": subscriptions,
        "count": len(subscriptions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
