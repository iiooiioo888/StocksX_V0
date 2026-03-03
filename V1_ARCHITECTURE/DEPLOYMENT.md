# StocksX V1 - 前後端分離架構部署指南

## 📁 專案結構

```
V1_ARCHITECTURE/
├── backend/                    # FastAPI 後端
│   ├── app/
│   │   ├── api/                # API 路由
│   │   ├── core/               # 核心配置
│   │   ├── models/             # 資料庫模型
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # 業務邏輯
│   │   ├── workers/            # Celery 任務
│   │   └── main.py             # 應用入口
│   ├── tests/                  # 測試
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── api/                # API 客戶端
│   │   ├── components/         # React 元件
│   │   ├── hooks/              # 自訂 hooks
│   │   ├── pages/              # 頁面
│   │   ├── store/              # 狀態管理
│   │   └── App.tsx
│   ├── Dockerfile
│   ├── package.json
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 快速開始

### 方法一：Docker Compose（推薦）

```bash
# 1. 複製環境變數
cp .env.example .env

# 2. 修改 .env 中的配置（特別是 SECRET_KEY）

# 3. 啟動所有服務
docker-compose up -d

# 4. 查看日誌
docker-compose logs -f

# 5. 訪問應用
# 前端：http://localhost:3000
# 後端 API：http://localhost:8000
# API 文件：http://localhost:8000/docs
```

### 方法二：本機開發

#### 啟動後端

```bash
cd backend

# 安裝依賴
pip install -r requirements.txt

# 複製環境變數
cp .env.example .env

# 啟動 FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 啟動前端

```bash
cd frontend

# 安裝依賴
npm install

# 啟動開發伺服器
npm run dev
```

#### 啟動 Redis

```bash
# Docker
docker run -d -p 6379:6379 --name stocksx_redis redis:7-alpine

# 或本機安裝
redis-server
```

## 📊 API 端點

### 認證

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/auth/register` | POST | 用戶註冊 |
| `/api/auth/login` | POST | 用戶登入 |
| `/api/auth/refresh` | POST | 刷新令牌 |
| `/api/auth/me` | GET | 取得當前用戶 |
| `/api/auth/change-password` | POST | 修改密碼 |

### 回測

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/backtest/run` | POST | 執行回測 |
| `/api/backtest/status/{task_id}` | GET | 查詢任務狀態 |
| `/api/backtest/result/{task_id}` | GET | 取得回測結果 |
| `/api/backtest/history` | GET | 回測歷史 |
| `/api/backtest/optimize` | POST | 參數優化 |

### 數據

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/data/symbols` | GET | 交易對列表 |
| `/api/data/kline` | GET | K 線數據 |
| `/api/data/fear-greed` | GET | 恐懼貪婪指數 |
| `/api/data/strategies` | GET | 策略列表 |

### 監控

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/monitor/ws/{symbol}` | WebSocket | 即時價格推送 |
| `/api/monitor/subscriptions` | GET | 訂閱列表 |

## 🔧 配置說明

### 後端配置（.env）

```bash
# 資料庫
DATABASE_URL=sqlite:///./stocksx.db  # 開發環境
DATABASE_URL=postgresql://user:pass@localhost:5432/stocksx  # 生產環境

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 前端配置

建立 `.env` 檔案：

```bash
VITE_API_URL=http://localhost:8000/api
```

## 🐳 Docker 部署

### 開發環境

```bash
# 僅啟動後端和 Redis
docker-compose up -d redis backend
```

### 生產環境

```bash
# 啟動所有服務（含 PostgreSQL）
docker-compose --profile production up -d

# 啟動監控服務
docker-compose --profile monitoring up -d
```

### 擴展 Worker

```bash
# 擴展 3 個 Worker
docker-compose up -d --scale worker=3
```

## 🧪 測試

### 後端測試

```bash
cd backend
pytest tests/ -v --cov=app
```

### API 測試

使用 Swagger UI：http://localhost:8000/docs

或使用 curl：

```bash
# 註冊
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}'

# 登入
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}'
```

## 📈 監控

### Celery Flower

訪問 http://localhost:5555 查看 Celery 任務監控面板。

### 日誌

```bash
# 查看後端日誌
docker-compose logs -f backend

# 查看 Worker 日誌
docker-compose logs -f worker

# 查看前端日誌
docker-compose logs -f frontend
```

## ⚠️ 注意事項

### 1. 生產環境配置

- 務必修改 `SECRET_KEY`
- 使用 PostgreSQL 替代 SQLite
- 啟用 HTTPS
- 設定適當的 CORS 來源

### 2. 資料庫迁移

從 SQLite 迁移到 PostgreSQL：

```bash
# 匯出 SQLite 數據
sqlite3 stocksx.db ".dump" > dump.sql

# 匯入 PostgreSQL
psql -U stocksx -d stocksx < dump.sql
```

### 3. 令牌過期

Access Token 預設 30 分鐘過期，Refresh Token 7 天過期。
前端已自動處理令牌刷新。

## 🔄 與 Streamlit 版本比較

| 層面 | Streamlit | FastAPI + React |
|------|-----------|-----------------|
| 前端技術 | Streamlit | React + TypeScript |
| 後端技術 | Streamlit | FastAPI |
| 認證 | Session | JWT |
| 即時通訊 | 輪詢 | WebSocket |
| 部署 | 單應用 | 容器化微服務 |
| 擴展性 | 低 | 高 |
| 開發速度 | 快 | 中 |

## 📚 下一步

1. **完善前端頁面**：回測頁面、歷史頁面等
2. **整合 Celery 任務**：實際執行回測
3. **單元測試**：提高測試覆蓋率
4. **CI/CD**：自動化測試和部署

---

**版本**: 1.0.0
**更新日期**: 2024-03-03
