# StocksX V1 - 前後端分離架構

## 📁 專案結構

```
StocksX_V1/
├── backend/                    # FastAPI 後端
│   ├── app/
│   │   ├── api/                # API routers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 認證端點
│   │   │   ├── backtest.py     # 回測端點
│   │   │   ├── data.py         # 數據端點
│   │   │   └── monitor.py      # 監控端點（WebSocket）
│   │   ├── core/               # 核心配置
│   │   │   ├── __init__.py
│   │   │   ├── config.py       # 配置管理
│   │   │   ├── security.py     # JWT/密碼加密
│   │   │   └── logger.py       # 日誌配置
│   │   ├── models/             # 資料庫模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── backtest.py
│   │   ├── schemas/            # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── backtest.py
│   │   │   └── data.py
│   │   ├── services/           # 業務邏輯
│   │   │   ├── __init__.py
│   │   │   ├── backtest_service.py
│   │   │   └── data_service.py
│   │   └── workers/            # Celery 任務
│   │       ├── __init__.py
│   │       └── tasks.py
│   ├── tests/                  # 測試
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/         # React 元件
│   │   ├── pages/              # 頁面
│   │   ├── hooks/              # 自訂 hooks
│   │   ├── api/                # API 客戶端
│   │   └── utils/              # 工具函式
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🚀 快速開始

### 後端啟動

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端啟動

```bash
cd frontend
npm install
npm run dev
```

### 訪問

- API 文件：http://localhost:8000/docs
- 前端：http://localhost:3000
