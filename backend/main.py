#!/usr/bin/env python3
"""
StocksX API 後端主入口
FastAPI + WebSocket + SQLite

作者：StocksX Team
創建日期：2026-03-22
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import json
from typing import List, Dict
from datetime import datetime
import sys
from pathlib import Path

import os

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import init_db, get_db
from models import Strategy, Signal, Portfolio
from schemas import StrategyResponse, SignalResponse, ScoreResponse
from api.strategies import router as strategies_router
from api.portfolio import router as portfolio_router
from api.scores import router as scores_router

# 創建 FastAPI 應用
app = FastAPI(
    title="StocksX API",
    description="130 策略量化交易系統 API",
    version="8.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態文件（前端）
frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

# 掛載 API 路由
app.include_router(strategies_router, prefix="/api/strategies", tags=["策略"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["組合"])
app.include_router(scores_router, prefix="/api/scores", tags=["評分"])

# WebSocket 連接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ 新連接：{websocket.client.host}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ 斷開連接：{websocket.client.host}")
    
    async def broadcast(self, message: dict):
        """廣播消息給所有連接"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """發送個人消息"""
        await websocket.send_json(message)

manager = ConnectionManager()

# 模擬實時信號推送（每 5 秒）
async def signal_pusher():
    """定時推送模擬信號"""
    import random
    
    while True:
        await asyncio.sleep(5)
        
        # 隨機選擇 3-5 個策略生成信號
        num_signals = random.randint(3, 5)
        signals = []
        
        for i in range(num_signals):
            strategy_name = f"strategy_{random.randint(1, 130)}"
            signal = random.choice([1, -1, 0])
            
            if signal != 0:
                signals.append({
                    "strategy": strategy_name,
                    "signal": "BUY" if signal == 1 else "SELL",
                    "price": round(random.uniform(100, 200), 2),
                    "timestamp": datetime.now().isoformat()
                })
        
        if signals:
            await manager.broadcast({
                "type": "signals",
                "data": signals,
                "count": len(signals)
            })

# 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時執行"""
    print("=" * 80)
    print("🚀 StocksX API 啟動中...")
    print("=" * 80)
    
    # 初始化數據庫
    init_db()
    print("✅ 數據庫初始化完成")
    
    # 啟動信號推送任務
    asyncio.create_task(signal_pusher())
    print("✅ 信號推送任務已啟動")
    
    print("=" * 80)
    print("📡 API 文檔：http://localhost:8000/docs")
    print("📊 前端界面：http://localhost:8000")
    print("=" * 80)

# WebSocket 端點
@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """實時信號推送 WebSocket（需認證）"""
    # 從 query param 或 header 獲取 token
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token or not _verify_ws_token(token):
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket)
    try:
        while True:
            # 接收客戶端消息（心跳等）
            data = await websocket.receive_text()
            
            # 可以處理客戶端請求
            if data == "ping":
                await manager.send_personal({"type": "pong"}, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast({
            "type": "system",
            "message": f"用戶 {websocket.client.host} 離線"
        })

@app.websocket("/ws/quotes")
async def websocket_quotes(websocket: WebSocket):
    """實時行情推送 WebSocket（需認證）"""
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token or not _verify_ws_token(token):
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 處理行情訂閱請求
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def _verify_ws_token(token: str) -> bool:
    """驗證 WebSocket 連接 token"""
    import hashlib
    expected_token = os.getenv("WS_AUTH_TOKEN", "")
    if not expected_token:
        # 未配置 WS_AUTH_TOKEN 時，開發模式允許所有連接
        return os.getenv("ENVIRONMENT", "development") == "development"
    return hashlib.compare_digest(token, expected_token)

# 健康檢查
@app.get("/api/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "8.0.0",
        "strategies": 130
    }

# 首頁
@app.get("/", response_class=HTMLResponse)
async def root():
    """首頁"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StocksX - 130 策略量化系統</title>
        <meta charset="UTF-8">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 48px; margin-bottom: 10px; }
            .subtitle { font-size: 24px; opacity: 0.9; margin-bottom: 30px; }
            .links { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                margin-top: 30px;
            }
            .link-card {
                background: rgba(255,255,255,0.2);
                padding: 20px;
                border-radius: 10px;
                text-decoration: none;
                color: white;
                transition: transform 0.2s;
            }
            .link-card:hover {
                transform: translateY(-5px);
                background: rgba(255,255,255,0.3);
            }
            .link-card h3 { margin: 0 0 10px 0; }
            .link-card p { margin: 0; opacity: 0.8; font-size: 14px; }
            .stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin: 30px 0;
            }
            .stat {
                text-align: center;
                background: rgba(255,255,255,0.15);
                padding: 20px;
                border-radius: 10px;
            }
            .stat-value { font-size: 36px; font-weight: bold; }
            .stat-label { opacity: 0.8; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 StocksX</h1>
            <div class="subtitle">130 策略量化交易系統 v8.0.0</div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">130</div>
                    <div class="stat-label">策略數量</div>
                </div>
                <div class="stat">
                    <div class="stat-value">100%</div>
                    <div class="stat-label">驗證通過</div>
                </div>
                <div class="stat">
                    <div class="stat-value">v8.0.0</div>
                    <div class="stat-label">版本</div>
                </div>
            </div>
            
            <div class="links">
                <a href="/docs" class="link-card">
                    <h3>📚 API 文檔</h3>
                    <p>Swagger/OpenAPI 交互式文檔</p>
                </a>
                <a href="/redoc" class="link-card">
                    <h3>📖 ReDoc</h3>
                    <p>美觀的 API 參考文檔</p>
                </a>
                <a href="/api/health" class="link-card">
                    <h3>💚 健康檢查</h3>
                    <p>查看系統狀態</p>
                </a>
            </div>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
                <p style="opacity: 0.7; font-size: 14px;">
                    📡 WebSocket: ws://localhost:8000/ws/signals<br>
                    📊 前端：開發中...
                </p>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🚀 StocksX API Server")
    print("=" * 80)
    print("\n啟動服務：http://localhost:8000")
    print("API 文檔：http://localhost:8000/docs")
    print("ReDoc:    http://localhost:8000/redoc")
    print("=" * 80 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
