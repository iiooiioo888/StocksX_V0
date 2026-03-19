# WebSocket 即時推送服務（FastAPI）
# 支持心跳保活、自動重連、結構化日誌

from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import time
from typing import Any

import ccxt
import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

# 嘗試導入結構化日誌
try:
    from src.utils.logging_config import get_logger, setup_logging
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

# 安全配置（從環境變數讀取）
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    logger.warning("SECRET_KEY 未設定，已自動生成臨時密鑰。生產環境請在 .env 中配置。")
ALGORITHM = "HS256"

# 心跳間隔（秒）
HEARTBEAT_INTERVAL = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
# 價格推送間隔（秒）
PRICE_INTERVAL = float(os.getenv("WS_PRICE_INTERVAL", "1.0"))
# 最大連接數
MAX_CONNECTIONS = int(os.getenv("WS_MAX_CONNECTIONS", "100"))

app = FastAPI(
    title="StocksX WebSocket Service",
    version="5.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════
# 連接管理器（支持心跳）
# ════════════════════════════════════════════════════════════

class ConnectionManager:
    """WebSocket 連接管理器 — 支持心跳保活、連接統計."""

    def __init__(self) -> None:
        # {user_id: {symbol: {"ws": WebSocket, "last_pong": float}}}
        self.active_connections: dict[int, dict[str, dict[str, Any]]] = {}
        self._total_connections: int = 0
        self._total_messages: int = 0

    @property
    def connection_count(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())

    @property
    def user_count(self) -> int:
        return len(self.active_connections)

    @property
    def total_connections(self) -> int:
        return self._total_connections

    @property
    def total_messages(self) -> int:
        return self._total_messages

    async def connect(self, websocket: WebSocket, user_id: int, symbol: str) -> None:
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        self.active_connections[user_id][symbol] = {
            "ws": websocket,
            "last_pong": time.time(),
        }
        self._total_connections += 1
        logger.info("ws_connect", extra={"user_id": user_id, "symbol": symbol, "total": self.connection_count})

    def disconnect(self, user_id: int, symbol: str) -> None:
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(symbol, None)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info("ws_disconnect", extra={"user_id": user_id, "symbol": symbol, "total": self.connection_count})

    async def send_to_user(self, message: dict, user_id: int, symbol: str | None = None) -> bool:
        """發送消息給指定用戶，返回是否成功."""
        if user_id not in self.active_connections:
            return False

        targets = {}
        if symbol:
            entry = self.active_connections[user_id].get(symbol)
            if entry:
                targets[symbol] = entry
        else:
            targets = self.active_connections[user_id]

        success = False
        for sym, entry in list(targets.items()):
            try:
                await entry["ws"].send_json(message)
                self._total_messages += 1
                success = True
            except Exception as e:
                logger.warning("ws_send_failed", extra={"user_id": user_id, "symbol": sym, "error": str(e)})
                self.disconnect(user_id, sym)
        return success

    async def broadcast(self, message: dict) -> int:
        """廣播消息給所有連接，返回成功發送數."""
        sent = 0
        for user_id in list(self.active_connections):
            for symbol in list(self.active_connections.get(user_id, {})):
                entry = self.active_connections[user_id].get(symbol)
                if not entry:
                    continue
                try:
                    await entry["ws"].send_json(message)
                    self._total_messages += 1
                    sent += 1
                except Exception:
                    self.disconnect(user_id, symbol)
        return sent

    async def cleanup_stale(self, timeout: float = 90.0) -> int:
        """清理超時未回應的連接，返回清理數量."""
        now = time.time()
        cleaned = 0
        for user_id in list(self.active_connections):
            for symbol, entry in list(self.active_connections.get(user_id, {}).items()):
                if now - entry.get("last_pong", 0) > timeout:
                    try:
                        await entry["ws"].close(code=1001, reason="heartbeat_timeout")
                    except Exception:
                        pass
                    self.disconnect(user_id, symbol)
                    cleaned += 1
        if cleaned:
            logger.info("ws_cleanup_stale", extra={"cleaned": cleaned})
        return cleaned

    def pong_received(self, user_id: int, symbol: str) -> None:
        """更新 pong 時間戳."""
        if user_id in self.active_connections:
            entry = self.active_connections[user_id].get(symbol)
            if entry:
                entry["last_pong"] = time.time()


manager = ConnectionManager()


# ════════════════════════════════════════════════════════════
# 幣安價格數據
# ════════════════════════════════════════════════════════════

_binance_spot: ccxt.binance | None = None
_binance_future: ccxt.binance | None = None


def get_binance_exchange(market_type: str = "spot") -> ccxt.binance | None:
    global _binance_spot, _binance_future
    try:
        if market_type == "spot":
            if _binance_spot is None:
                _binance_spot = ccxt.binance({"options": {"defaultType": "spot"}, "timeout": 10000})
            return _binance_spot
        else:
            if _binance_future is None:
                _binance_future = ccxt.binance({"options": {"defaultType": "future"}, "timeout": 10000})
            return _binance_future
    except Exception as e:
        logger.error("exchange_init_failed", extra={"market_type": market_type, "error": str(e)})
        return None


async def fetch_price(symbol: str) -> dict[str, Any] | None:
    """取得即時價格（幣安 API）."""
    try:
        market_type = "future" if ":" in symbol else "spot"
        exchange = get_binance_exchange(market_type)
        if not exchange:
            return None

        ticker = await asyncio.to_thread(exchange.fetch_ticker, symbol)
        last_price = ticker.get("last", 0)

        if last_price and last_price > 0:
            return {
                "symbol": symbol,
                "price": round(last_price, 2),
                "change_pct": round(ticker.get("percentage", 0) or 0, 2),
                "high_24h": round(ticker.get("high", 0) or 0, 2),
                "low_24h": round(ticker.get("low", 0) or 0, 2),
                "volume_24h": round(ticker.get("baseVolume", 0) or 0, 2),
                "bid": round(ticker.get("bid", 0) or 0, 2),
                "ask": round(ticker.get("ask", 0) or 0, 2),
                "timestamp": int(time.time() * 1000),
                "market_type": market_type,
            }
    except ccxt.NetworkError:
        logger.warning("price_fetch_network_error", extra={"symbol": symbol})
    except ccxt.ExchangeError as e:
        logger.warning("price_fetch_exchange_error", extra={"symbol": symbol, "error": str(e)})
    except Exception as e:
        logger.error("price_fetch_error", extra={"symbol": symbol, "error": str(e)})
    return None


# ════════════════════════════════════════════════════════════
# 後台任務
# ════════════════════════════════════════════════════════════

async def price_push_loop() -> None:
    """價格推送主循環."""
    default_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    while True:
        try:
            # 收集所有訂閱的交易對
            subscribed: set[str] = set()
            for user_conns in manager.active_connections.values():
                subscribed.update(user_conns.keys())
            symbols = subscribed if subscribed else set(default_symbols)

            for symbol in symbols:
                price_data = await fetch_price(symbol)
                if not price_data:
                    continue
                msg = {"type": "price_update", "data": price_data}
                for user_id, conns in list(manager.active_connections.items()):
                    entry = conns.get(symbol)
                    if entry:
                        try:
                            await entry["ws"].send_json(msg)
                            manager._total_messages += 1
                        except Exception:
                            manager.disconnect(user_id, symbol)
        except Exception as e:
            logger.error("price_push_error", extra={"error": str(e)})
        await asyncio.sleep(PRICE_INTERVAL)


async def heartbeat_loop() -> None:
    """心跳循環 — 定期發送 ping，清理僵屍連接."""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        try:
            ping_msg = {"type": "ping", "timestamp": int(time.time() * 1000)}
            await manager.broadcast(ping_msg)
            await manager.cleanup_stale(timeout=HEARTBEAT_INTERVAL * 3)
        except Exception as e:
            logger.error("heartbeat_error", extra={"error": str(e)})


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(price_push_loop())
    asyncio.create_task(heartbeat_loop())
    logger.info("ws_service_started", extra={"heartbeat_interval": HEARTBEAT_INTERVAL, "price_interval": PRICE_INTERVAL})


# ════════════════════════════════════════════════════════════
# JWT 驗證
# ════════════════════════════════════════════════════════════

def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ════════════════════════════════════════════════════════════
# WebSocket 端點
# ════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
) -> None:
    """
    WebSocket 端點 — 即時行情 & 信號推送.

    協議：
      客戶端 → 服務端:
        {"action": "subscribe", "symbols": ["BTC/USDT"]}
        {"action": "unsubscribe", "symbols": ["BTC/USDT"]}
        {"action": "pong"}
        {"action": "ping"}

      服務端 → 客戶端:
        {"type": "connected", ...}
        {"type": "price_update", "data": {...}}
        {"type": "signal", "data": {...}}
        {"type": "ping", "timestamp": ...}
        {"type": "pong"}
        {"type": "error", "message": "..."}
    """
    # 驗證
    user_id = 1
    if token:
        payload = verify_token(token)
        if payload:
            user_id = int(payload.get("sub", 1))

    # 連接數限制
    if manager.connection_count >= MAX_CONNECTIONS:
        await websocket.close(code=1013, reason="max_connections_reached")
        logger.warning("ws_max_connections", extra={"limit": MAX_CONNECTIONS})
        return

    await websocket.accept()
    symbol = "*"
    await manager.connect(websocket, user_id, symbol)

    # 歡迎消息
    await websocket.send_json({
        "type": "connected",
        "message": "WebSocket 已連接",
        "heartbeat_interval": HEARTBEAT_INTERVAL,
        "protocol_version": "2.0",
        "timestamp": int(time.time() * 1000),
    })

    subscribed: set[str] = set()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "invalid_json"})
                continue

            action = msg.get("action")

            if action == "subscribe":
                symbols = msg.get("symbols", [])
                for s in symbols:
                    subscribed.add(s)
                    if user_id not in manager.active_connections:
                        manager.active_connections[user_id] = {}
                    manager.active_connections[user_id][s] = {
                        "ws": websocket,
                        "last_pong": time.time(),
                    }
                await websocket.send_json({"type": "subscribed", "symbols": list(subscribed)})
                logger.info("ws_subscribe", extra={"user_id": user_id, "symbols": list(subscribed)})

            elif action == "unsubscribe":
                for s in msg.get("symbols", []):
                    subscribed.discard(s)
                    if user_id in manager.active_connections:
                        manager.active_connections[user_id].pop(s, None)
                await websocket.send_json({"type": "unsubscribed", "symbols": list(subscribed)})

            elif action == "pong":
                for s in subscribed or ["*"]:
                    manager.pong_received(user_id, s)

            elif action == "ping":
                await websocket.send_json({"type": "pong", "timestamp": int(time.time() * 1000)})

            else:
                await websocket.send_json({"type": "error", "message": f"unknown_action: {action}"})

    except WebSocketDisconnect:
        logger.info("ws_client_disconnect", extra={"user_id": user_id})
    except Exception as e:
        logger.error("ws_error", extra={"user_id": user_id, "error": str(e)})
    finally:
        for s in list(subscribed) + ["*"]:
            manager.disconnect(user_id, s)


# ════════════════════════════════════════════════════════════
# REST 端點
# ════════════════════════════════════════════════════════════

@app.get("/health")
async def health() -> dict:
    """輕量健康檢查."""
    return {"status": "healthy", "connections": manager.connection_count}


@app.get("/health/detailed")
async def health_detailed() -> dict:
    """詳細健康狀態."""
    return {
        "status": "healthy",
        "connections": manager.connection_count,
        "users": manager.user_count,
        "total_connections_lifetime": manager.total_connections,
        "total_messages": manager.total_messages,
        "config": {
            "heartbeat_interval": HEARTBEAT_INTERVAL,
            "price_interval": PRICE_INTERVAL,
            "max_connections": MAX_CONNECTIONS,
        },
    }


@app.get("/subscriptions/{user_id}")
async def subscriptions(user_id: int) -> dict:
    """查看用戶訂閱."""
    subs = list(manager.active_connections.get(user_id, {}).keys())
    return {"user_id": user_id, "subscriptions": subs, "count": len(subs)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
