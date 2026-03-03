# API Routers - 監控相關（WebSocket）
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set
import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.security import HTTPBearer

from ..core import security, logger

router = APIRouter(prefix="/monitor", tags=["監控"])
security_scheme = HTTPBearer()
log = logger.get_logger("stocksx.api.monitor")


class ConnectionManager:
    """WebSocket 連接管理器"""
    
    def __init__(self):
        # {user_id: {symbol: websocket}}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        symbol: str
    ):
        """接受連接"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][symbol] = websocket
        
        log.info(f"WebSocket 連接：user_id={user_id}, symbol={symbol}")
    
    def disconnect(self, user_id: int, symbol: str):
        """斷開連接"""
        if user_id in self.active_connections:
            if symbol in self.active_connections[user_id]:
                del self.active_connections[user_id][symbol]
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        log.info(f"WebSocket 斷開：user_id={user_id}, symbol={symbol}")
    
    async def send_personal_message(
        self,
        message: Dict[str, Any],
        user_id: int,
        symbol: Optional[str] = None
    ):
        """發送個人訊息"""
        if user_id not in self.active_connections:
            return
        
        if symbol:
            websocket = self.active_connections[user_id].get(symbol)
            if websocket:
                await websocket.send_json(message)
        else:
            # 發送給用戶的所有連接
            for ws in self.active_connections[user_id].values():
                try:
                    await ws.send_json(message)
                except Exception:
                    pass
    
    async def broadcast(self, message: Dict[str, Any]):
        """廣播訊息給所有連接"""
        for user_connections in self.active_connections.values():
            for websocket in user_connections.values():
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass


# 全域連接管理器
manager = ConnectionManager()


@router.websocket("/ws/{symbol}")
async def websocket_endpoint(
    websocket: WebSocket,
    symbol: str,
    token: Optional[str] = None
):
    """
    WebSocket 端點 - 訂閱即時價格/信號
    
    連接範例：
    ```
    ws://localhost:8000/api/monitor/ws/BTC/USDT?token=YOUR_JWT_TOKEN
    ```
    
    訂閱多個交易對：
    ```python
    await websocket.send_json({
        "action": "subscribe",
        "symbols": ["BTC/USDT", "ETH/USDT"]
    })
    ```
    """
    # 驗證令牌（從 query parameter）
    user_id = 1  # 預設用戶 ID（實際應從 token 解析）
    
    if token:
        payload = security.verify_token(token, token_type="access")
        if payload:
            user_id = int(payload.get("sub", 1))
    
    await manager.connect(websocket, user_id, symbol)
    
    # 發送歡迎訊息
    await websocket.send_json({
        "type": "connected",
        "symbol": symbol,
        "message": f"已訂閱 {symbol} 的即時數據"
    })
    
    try:
        while True:
            # 接收客戶端訊息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 處理訂閱/取消訂閱
            action = message.get("action")
            
            if action == "subscribe":
                symbols = message.get("symbols", [])
                for s in symbols:
                    await manager.connect(websocket, user_id, s)
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": symbols
                })
            
            elif action == "unsubscribe":
                symbols = message.get("symbols", [])
                for s in symbols:
                    manager.disconnect(user_id, s)
                await websocket.send_json({
                    "type": "unsubscribed",
                    "symbols": symbols
                })
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(user_id, symbol)
        log.info(f"WebSocket 斷開連接：user_id={user_id}, symbol={symbol}")
    except Exception as e:
        log.error(f"WebSocket 錯誤：{e}")
        manager.disconnect(user_id, symbol)


# 模擬價格推送任務
async def price_push_task():
    """模擬價格推送（實際應從市場數據服務取得）"""
    import random
    import time
    
    while True:
        # 模擬價格更新
        for user_id, connections in list(manager.active_connections.items()):
            for symbol, websocket in list(connections.items()):
                try:
                    # 模擬價格數據
                    base_price = 45000 if "BTC" in symbol else 2500
                    price = base_price * random.uniform(0.99, 1.01)
                    change = random.uniform(-2, 2)
                    
                    await websocket.send_json({
                        "type": "price_update",
                        "symbol": symbol,
                        "data": {
                            "price": round(price, 2),
                            "change_pct": round(change, 2),
                            "timestamp": int(time.time() * 1000)
                        }
                    })
                except Exception:
                    pass
        
        await asyncio.sleep(5)  # 每 5 秒推送一次


@router.on_event("startup")
async def startup_event():
    """啟動時開始價格推送任務"""
    asyncio.create_task(price_push_task())


@router.get("/subscriptions")
async def get_subscriptions(
    credentials: HTTPBearer = Depends(security_scheme)
) -> Any:
    """
    取得當前訂閱列表
    """
    token = credentials.credentials
    payload = security.verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效令牌"
        )
    
    user_id = int(payload.get("sub", 0))
    
    subscriptions = list(manager.active_connections.get(user_id, {}).keys())
    
    return {
        "user_id": user_id,
        "subscriptions": subscriptions,
        "total": len(subscriptions)
    }
