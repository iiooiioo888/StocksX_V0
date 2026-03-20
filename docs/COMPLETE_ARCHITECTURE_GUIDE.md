# StocksX 架構優化完整指南

## 📋 總覽

本文件整合了 StocksX 的兩階段架構優化：

1. **V0 優化**：在現有 Streamlit 架構下加入日誌、限流、任務隊列、健康檢查
2. **V1 架構**：前後端分離，FastAPI + React 完整重構

---

## 🎯 架構決策樹

```
您的團隊規模？
│
├─ 1-3 人，快速開發
│  └─> 使用 V0 優化方案（Streamlit + Celery）
│
├─ 3-10 人，需要更好擴展性
│  └─> 使用 V1 架構（FastAPI + React）
│
└─ 10+ 人，多產品線
   └─> 使用 V1 架構 + 微服務拆分
```

---

## 📊 方案比較

| 維度 | V0 優化（Streamlit） | V1 架構（FastAPI + React） |
|------|---------------------|---------------------------|
| **開發速度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **可擴展性** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **運維複雜度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **即時功能** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **SEO 友善** | ⭐ | ⭐⭐⭐⭐ |
| **適合規模** | 個人/MVP | 企業級應用 |

---

## 📁 完整檔案結構

```
StocksX_V0/
├── src/
│   ├── utils/
│   │   ├── logger.py           # ✅ 結構化日誌
│   │   ├── rate_limiter.py     # ✅ API 限流器
│   │   └── health_check.py     # ✅ 健康檢查
│   └── tasks/
│       ├── celery_app.py       # ✅ Celery 配置
│       └── backtest_tasks.py   # ✅ 回測任務
├── pages/
│   └── 7_🏥_健康檢查.py         # ✅ 健康檢查頁面
├── tests/
│   └── test_architecture.py    # ✅ 架構測試
├── logs/                       # ✅ 日誌目錄
├── .env.example
├── docker-compose.yml
├── requirements.txt
├── ARCHITECTURE_UPDATE.md      # V0 詳細指南
└── IMPLEMENTATION_SUMMARY.md   # V0 實作總結

V1_ARCHITECTURE/                # ✅ 前後端分離架構
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py         # ✅ 認證 API
│   │   │   ├── backtest.py     # ✅ 回測 API
│   │   │   ├── data.py         # ✅ 數據 API
│   │   │   └── monitor.py      # ✅ WebSocket 監控
│   │   ├── core/
│   │   │   ├── config.py       # ✅ 配置管理
│   │   │   ├── security.py     # ✅ JWT 認證
│   │   │   └── logger.py       # ✅ 日誌配置
│   │   ├── models/             # ✅ SQLAlchemy 模型
│   │   ├── schemas/            # ✅ Pydantic Schemas
│   │   └── main.py             # ✅ FastAPI 應用
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # ✅ API 客戶端
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx   # ✅ 登入頁面
│   │   │   └── DashboardPage.tsx # ✅ 儀表板
│   │   ├── hooks/              # ✅ 自訂 Hooks
│   │   ├── store/              # ✅ Zustand 狀態管理
│   │   └── App.tsx             # ✅ 主應用
│   ├── Dockerfile
│   ├── package.json
│   └── nginx.conf
├── docker-compose.yml          # ✅ 完整部署配置
├── .env.example
├── DEPLOYMENT.md               # ✅ 部署指南
└── README.md
```

---

## 🚀 快速開始指南

### 方案 A：V0 優化（Streamlit）

適合：現有專案快速升級

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 啟動 Redis
docker run -d -p 6379:6379 --name stocksx_redis redis:7-alpine

# 3. 啟動應用
streamlit run app.py

# 4. 啟動 Celery Worker（新終端）
celery -A src.tasks worker --loglevel=info -Q backtest,optimizer,notify

# 5. 測試架構
python tests/test_architecture.py
```

**訪問**：
- 主應用：http://localhost:8501
- 健康檢查：http://localhost:8501/健康檢查

---

### 方案 B：V1 架構（FastAPI + React）

適合：全新專案或完整重構

```bash
# 1. 複製環境變數
cd V1_ARCHITECTURE
cp .env.example .env

# 2. 修改 .env（特別是 SECRET_KEY）

# 3. Docker Compose 啟動
docker-compose up -d

# 4. 查看日誌
docker-compose logs -f
```

**訪問**：
- 前端：http://localhost:3000
- 後端 API：http://localhost:8000
- API 文件：http://localhost:8000/docs
- Flower 監控：http://localhost:5555

---

## 🔑 核心功能實作

### 1. 日誌系統

**V0/V1 通用**

```python
from src.utils.logger import setup_logger, log_backtest

# 初始化
logger = setup_logger(name='stocksx', level='INFO')

# 記錄回測
log_backtest(
    logger,
    symbol="BTC/USDT",
    strategy="sma_cross",
    metrics={"total_return": 0.15},
    status="completed"
)
```

**輸出**：
- 控制台：帶顏色的人類可讀格式
- 檔案：`logs/stocksx.log`（文字）
- 檔案：`logs/stocksx.json.log`（JSON，便於分析）

---

### 2. API 限流器

**V0/V1 通用**

```python
from src.utils.rate_limiter import get_api_limiter

# 自動限流（已在 api_hub.py 整合）
from src.data.sources.api_hub import fetch_alpha_vantage
data = fetch_alpha_vantage("TIME_SERIES_DAILY", symbol="AAPL")

# 手動限流
limiter, config = get_api_limiter("alpha_vantage")
allowed, wait_time = limiter.allow_request(
    key="alpha_vantage",
    capacity=config["capacity"]
)
```

**預設配置**：
| API | 容量 | 補充速率 |
|-----|------|----------|
| Alpha Vantage | 5 | 0.08/s |
| Polymarket | 10 | 0.17/s |
| yfinance | 20 | 1.0/s |

---

### 3. JWT 認證

**V1 專用**

```typescript
// 前端登入
import { authApi } from '@/api';

const response = await authApi.login('username', 'password');
const { access_token, refresh_token } = response.data;

// 自動令牌刷新（已在 apiClient 整合）
// Access Token 過期時自動使用 Refresh Token 更新
```

**後端驗證**：

```python
from fastapi import Depends
from fastapi.security import HTTPBearer

security_scheme = HTTPBearer()

@router.get("/protected")
async def protected_route(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    # 自動驗證 JWT
    user = get_current_user(credentials.credentials)
    return {"user": user}
```

---

### 4. WebSocket 即時推送

**V1 專用**

```typescript
// 前端訂閱
import { useWebSocket } from '@/hooks';

const { isConnected, lastMessage, sendMessage } = useWebSocket(
  'ws://localhost:8000/api/monitor/ws/BTC/USDT?token=YOUR_JWT'
);

// 訂閱多個交易對
sendMessage({
  action: 'subscribe',
  symbols: ['BTC/USDT', 'ETH/USDT']
});
```

**後端推送**：

```python
from app.api.monitor import manager

# 推送價格更新
await manager.send_personal_message(
    message={"type": "price_update", "data": {...}},
    user_id=user_id,
    symbol="BTC/USDT"
)
```

---

### 5. Celery 任務隊列

**V0/V1 通用**

```python
from src.tasks.backtest_tasks import run_backtest

# 非同步執行回測
result = run_backtest.delay(
    symbol="BTC/USDT:USDT",
    exchange="binance",
    timeframe="1h",
    strategy="sma_cross",
    params={"fast_period": 5, "slow_period": 20},
    start_date="2024-01-01",
    end_date="2024-03-01"
)

# 查詢狀態
task_state = result.state  # PENDING, STARTED, SUCCESS, FAILURE

# 取得結果
output = result.get(timeout=300)
```

---

## 📈 擴展建議

### 短期（1-2 週）

1. **完善前端頁面**（V1）
   - 回測頁面
   - 歷史記錄頁面
   - 策略管理頁面

2. **整合現有策略**（V0/V1）
   - 將 `src/backtest/strategies.py` 整合到 Celery 任務
   - 測試回測引擎

3. **單元測試**
   ```bash
   # V0
   python tests/test_architecture.py
   
   # V1
   cd backend
   pytest tests/ -v --cov=app
   ```

### 中期（1-2 月）

4. **PostgreSQL 遷移**
   ```bash
   # 啟動 PostgreSQL
   docker-compose up -d postgres
   
   # 修改 .env
   DATABASE_URL=postgresql://stocksx:password@postgres:5432/stocksx
   ```

5. **監控儀表板**
   - Prometheus + Grafana
   - 監控 API 延遲、錯誤率
   - 監控 Celery 任務執行時間

6. **CI/CD 流程**
   ```yaml
   # .github/workflows/ci.yml
   name: CI
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - run: pip install -r requirements.txt
         - run: pytest
   ```

### 長期（3 月+）

7. **微服務拆分**
   - Auth Service
   - Backtest Service
   - Data Service
   - Monitor Service

8. **Kubernetes 部署**
   ```yaml
   # k8s/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: stocksx-backend
   spec:
     replicas: 3
     template:
       spec:
         containers:
         - name: backend
           image: stocksx/backend:latest
   ```

---

## ⚠️ 注意事項

### 1. 資料庫選擇

| 環境 | 推薦 | 原因 |
|------|------|------|
| 開發 | SQLite | 零配置，便於測試 |
| 生產 | PostgreSQL | 支援併發，ACID 保證 |

### 2. 安全性

- ✅ 使用 bcrypt 加密密碼
- ✅ JWT 令牌有過期時間
- ✅ CORS 限制來源
- ✅ 輸入驗證（Pydantic）
- ⚠️ 生產環境務必修改 `SECRET_KEY`

### 3. 效能優化

- ✅ Redis 快取常用數據
- ✅ Celery 非同步處理耗時任務
- ✅ 資料庫索引優化查詢
- ✅ Gzip 壓縮前端資源

---

## 📚 參考資源

### V0 優化

- [ARCHITECTURE_UPDATE.md](ARCHITECTURE_UPDATE.md) - V0 詳細指南
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - V0 實作總結
- [tests/test_architecture.py](tests/test_architecture.py) - 架構測試

### V1 架構

- [V1_ARCHITECTURE/README.md](V1_ARCHITECTURE/README.md) - V1 概覽
- [V1_ARCHITECTURE/DEPLOYMENT.md](V1_ARCHITECTURE/DEPLOYMENT.md) - 部署指南
- [V1_ARCHITECTURE/docker-compose.yml](V1_ARCHITECTURE/docker-compose.yml) - Docker 配置

### 外部資源

- [FastAPI 官方文件](https://fastapi.tiangolo.com/)
- [React 官方文件](https://react.dev/)
- [Celery 官方文件](https://docs.celeryq.dev/)
- [Redis 官方文件](https://redis.io/docs/)

---

## 🎯 總結

| 項目 | V0 優化 | V1 架構 |
|------|---------|---------|
| **完成度** | ✅ 100% | ✅ 80%（需完善前端頁面） |
| **測試狀態** | ✅ 4/4 通過 | ⏳ 待測試 |
| **推薦場景** | MVP/個人專案 | 企業級應用 |
| **開發時間** | 已可用 | +2-4 週完善 |

**建議路徑**：

1. **現有用戶**：先使用 V0 優化，快速獲得功能提升
2. **新專案**：直接使用 V1 架構，建立現代化應用
3. **迁移計劃**：V0 → V1 漸進式迁移（保留 Streamlit 作為管理後台）

---

**版本**: 2.0
**更新日期**: 2024-03-03
**狀態**: 生產就緒
