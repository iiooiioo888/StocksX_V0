# StocksX API 後端

FastAPI 驅動的 RESTful API + WebSocket 實時推送

## 功能

- ✅ RESTful API (策略、回測、評分)
- ✅ WebSocket 實時信號推送
- ✅ SQLite 數據庫
- ✅ JWT 認證
- ✅ Swagger 文檔
- ✅ CORS 支持

## 快速開始

```bash
# 安裝依賴
pip install fastapi uvicorn websockets sqlalchemy pyjwt

# 啟動服務
python3 backend/main.py

# 訪問 API 文檔
http://localhost:8000/docs
```

## API 端點

### 策略
- `GET /api/strategies` - 獲取所有策略
- `GET /api/strategies/{name}` - 獲取策略詳情
- `GET /api/strategies/{name}/signals` - 獲取策略信號
- `POST /api/strategies/{name}/backtest` - 執行回測

### 組合
- `GET /api/portfolio` - 獲取組合信息
- `POST /api/portfolio/backtest` - 組合回測
- `PUT /api/portfolio/weights` - 調整權重

### 評分
- `GET /api/scores` - 獲取所有評分
- `GET /api/scores/ranking` - 獲取排名
- `GET /api/scores/{name}` - 獲取策略評分

### 實時
- `WebSocket /ws/signals` - 實時信號推送
- `WebSocket /ws/quotes` - 實時行情推送

## 目錄結構

```
backend/
├── main.py              # 應用入口
├── config.py            # 配置
├── database.py          # 數據庫
├── models.py            # 數據模型
├── schemas.py           # Pydantic 模式
├── api/
│   ├── strategies.py    # 策略 API
│   ├── portfolio.py     # 組合 API
│   ├── scores.py        # 評分 API
│   └── ws.py            # WebSocket
├── services/
│   ├── strategy_service.py
│   ├── backtest_service.py
│   └── score_service.py
└── utils/
    └── auth.py          # 認證工具
```
