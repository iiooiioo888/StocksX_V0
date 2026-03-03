# StocksX 架構優化實作指南

## 📋 更新內容總覽

本次實作了您提出的 12 項架構優化建議中的 4 項高優先級項目：

| # | 項目 | 狀態 | 檔案 |
|---|------|------|------|
| 1 | ✅ 日誌系統 | 完成 | `src/utils/logger.py` |
| 2 | ✅ API 限流器 | 完成 | `src/utils/rate_limiter.py`, `src/data/sources/api_hub.py` |
| 3 | ✅ 任務隊列 | 完成 | `src/tasks/`, `docker-compose.yml` |
| 4 | ✅ 健康檢查 | 完成 | `src/utils/health_check.py` |

---

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
# 複製範例
cp .env.example .env

# 編輯 .env（填入 API 金鑰等配置）
```

### 3. 啟動 Redis（任務隊列必需）

**Windows (使用 Docker):**
```bash
docker run -d -p 6379:6379 --name stocksx_redis redis:7-alpine
```

**Linux/Mac:**
```bash
# 使用 Homebrew
brew install redis
redis-server

# 或直接使用 Docker
docker run -d -p 6379:6379 --name stocksx_redis redis:7-alpine
```

### 4. 啟動應用

```bash
# 啟動 Streamlit
streamlit run app.py

# 啟動 Celery Worker（新終端視窗）
celery -A src.tasks worker --loglevel=info -Q backtest,optimizer,notify

# 啟動 Celery Beat 定時任務（新終端視窗）
celery -A src.tasks beat --loglevel=info
```

---

## 📁 新增檔案結構

```
StocksX_V0/
├── src/
│   ├── utils/
│   │   ├── logger.py          # 結構化日誌系統
│   │   ├── rate_limiter.py    # API 限流器（令牌桶）
│   │   └── health_check.py    # 健康檢查端點
│   └── tasks/
│       ├── __init__.py        # Celery 配置
│       └── backtest_tasks.py  # 回測任務定義
├── logs/                       # 日誌目錄（自動建立）
├── .env.example               # 環境變數範例
├── docker-compose.yml         # Docker Compose 配置
├── requirements.txt           # 更新後的依賴
└── ARCHITECTURE_UPDATE.md     # 本檔案
```

---

## 🔧 使用指南

### 1. 日誌系統

```python
from src.utils.logger import setup_logger, get_logger, log_backtest, log_api_call

# 初始化（在 app.py 或入口處）
setup_logger(name='stocksx', level='INFO', log_dir='logs')

# 在模組中使用
logger = get_logger('stocksx.my_module')

logger.info("一般訊息")
logger.warning("警告訊息")
logger.error("錯誤訊息", exc_info=True)

# 記錄回測
log_backtest(
    logger,
    symbol="BTC/USDT",
    strategy="sma_cross",
    timeframe="1h",
    metrics={"total_return": 0.15},
    duration_ms=1234.5,
    status="completed"
)

# 記錄 API 呼叫
log_api_call(
    logger,
    api_name="alpha_vantage",
    endpoint="TIME_SERIES_DAILY",
    params={"symbol": "AAPL"},
    response_time_ms=150.5,
    status="success"
)
```

**日誌輸出格式：**

控制台（人類可讀）:
```
2024-03-03 10:30:45 | INFO     | stocksx.api_hub | API call: alpha_vantage.TIME_SERIES_DAILY
```

JSON 檔案（機器分析）:
```json
{
  "timestamp": "2024-03-03T10:30:45Z",
  "level": "INFO",
  "logger": "stocksx.api_hub",
  "message": "API call: alpha_vantage.TIME_SERIES_DAILY",
  "extra": {
    "api_name": "alpha_vantage",
    "endpoint": "TIME_SERIES_DAILY",
    "response_time_ms": 150.5,
    "status": "success"
  }
}
```

### 2. API 限流器

```python
from src.utils.rate_limiter import (
    RateLimiter,
    get_api_limiter,
    rate_limit,
    RateLimitExceeded
)

# 方法 1: 使用裝飾器
limiter = RateLimiter(default_capacity=10, default_refill_rate=1.0)

@rate_limit(limiter, key="polymarket_api", capacity=10, refill_rate=1.0/6)
def fetch_polymarket_data():
    return requests.get(url)

# 方法 2: 手動檢查
limiter, config = get_api_limiter("alpha_vantage")
allowed, wait_time = limiter.allow_request(
    key="alpha_vantage",
    capacity=config["capacity"],
    refill_rate=config["refill_rate"]
)

if not allowed:
    print(f"限流中，請等待 {wait_time:.1f} 秒")
else:
    fetch_data()

# 方法 3: 自動整合（已在 api_hub.py 中實作）
# 直接呼叫 fetch_alpha_vantage() 會自動進行限流檢查
```

**預設限流配置：**

| API | 容量 | 補充速率 | 說明 |
|-----|------|----------|------|
| polymarket | 10 | 1/6 秒 | 約 10 次/分鐘 |
| alpha_vantage | 5 | 1/12 秒 | 約 5 次/分鐘 |
| fred | 100 | 1/144 秒 | 約 600 次/天 |
| polygon | 5 | 1/12 秒 | 約 5 次/分鐘 |
| coingecko | 30 | 0.5 秒 | 約 30 次/分鐘 |
| yfinance | 20 | 1 秒 | 保守配置 |

### 3. Celery 任務隊列

```python
from src.tasks.backtest_tasks import run_backtest, run_param_optimizer

# 非同步執行回測（不阻塞 UI）
result = run_backtest.delay(
    symbol="BTC/USDT:USDT",
    exchange="binance",
    timeframe="1h",
    strategy="sma_cross",
    params={"fast_period": 5, "slow_period": 20},
    start_date="2024-01-01",
    end_date="2024-03-01",
    user_id=1
)

# 檢查任務狀態
print(f"Task ID: {result.id}")
print(f"Task State: {result.state}")

# 等待結果（可設定 timeout）
output = result.get(timeout=300)
print(output)

# 參數優化任務
optimizer_result = run_param_optimizer.delay(
    symbol="BTC/USDT:USDT",
    exchange="binance",
    timeframe="1h",
    strategy="sma_cross",
    param_grid={
        "fast_period": [5, 10, 20],
        "slow_period": [20, 50, 100]
    },
    start_date="2024-01-01",
    end_date="2024-03-01",
    metric="sharpe",
    n_best=5
)
```

**在 Streamlit 中使用：**

```python
# pages/2_₿_加密回測.py

import streamlit as st
from src.tasks.backtest_tasks import run_backtest
from celery.result import AsyncResult

if st.button("執行回測"):
    # 非同步執行
    task = run_backtest.delay(...)
    
    # 顯示任務 ID
    st.info(f"回測任務已提交，Task ID: `{task.id}`")
    st.info("您可以在歷史頁面查看結果")
    
    # 或使用進度條等待
    with st.spinner("執行回測中..."):
        progress = st.progress(0)
        for i in range(100):
            if task.ready():
                progress.progress(100)
                break
            progress.progress(i + 1)
            time.sleep(0.5)
        
        result = task.get()
        st.success("回測完成！")
```

### 4. 健康檢查

**在 Streamlit 中使用：**

```python
# pages/7_🏥_健康檢查.py

import streamlit as st
from src.utils.health_check import render_health_page

render_health_page()
```

**API 端點（FastAPI/Flask）：**

```python
from flask import Flask, jsonify
from src.utils.health_check import get_system_health

app = Flask(__name__)

@app.route('/health')
def health():
    health = get_system_health(include_external=True, include_system=True)
    status_code = 200 if health.status == 'healthy' else 503
    return jsonify(health.to_dict()), status_code
```

---

## 🐳 Docker 部署

### 開發環境（僅 Redis + Web）

```bash
# 啟動 Redis
docker run -d -p 6379:6379 --name stocksx_redis redis:7-alpine

# 啟動應用
streamlit run app.py
```

### 生產環境（完整堆疊）

```bash
# 啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f web
docker-compose logs -f worker

# 擴展 Worker 數量
docker-compose up -d --scale worker=3

# 停止所有服務
docker-compose down

# 清除數據（慎用）
docker-compose down -v
```

### 監控（含 Flower）

```bash
# 啟動含監控服務
docker-compose --profile monitoring up -d

# 訪問 Flower 監控面板
# http://localhost:5555
```

---

## 📊 架構對比

### 優化前

```
┌─────────────────┐
│   Streamlit     │
│      (UI)       │
└────────┬────────┘
         │ 同步執行
         ▼
┌─────────────────┐
│   SQLite +      │
│   記憶體快取     │
└─────────────────┘
```

**問題：**
- ❌ 回測阻塞 UI
- ❌ 無 API 限流保護
- ❌ 無結構化日誌
- ❌ 無法監控系統健康

### 優化後

```
┌─────────────────────────────────────────┐
│          Streamlit (UI)                 │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────┼─────────┐
         │         │         │
         ▼         ▼         ▼
   ┌──────────┐ ┌──────┐ ┌──────────┐
   │  日誌系統 │ │ 限流 │ │ 健康檢查 │
   └──────────┘ └──────┘ └──────────┘
         │         │         │
         └─────────┼─────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│  Celery Worker  │  │   Redis         │
│  (非同步任務)    │  │  (隊列 + 快取)   │
└─────────────────┘  └─────────────────┘
```

**優勢：**
- ✅ 非同步任務，不阻塞 UI
- ✅ API 限流保護，避免觸發頻率限制
- ✅ 結構化日誌，便於除錯與審計
- ✅ 健康檢查，即時監控系統狀態

---

## ⚠️ 注意事項

### 1. SQLite 限制

當前仍使用 SQLite，**多用戶併發寫入時可能遇到鎖定問題**。建議：

- **開發環境**: 继续使用 SQLite
- **生產環境**: 遷移至 PostgreSQL（見 `docker-compose.yml` 中的 `postgres` 服務）

### 2. Redis 必需

Celery 任務隊列需要 Redis：

```bash
# 檢查 Redis 是否運行
redis-cli ping
# 應回傳：PONG
```

### 3. 日誌輪轉

日誌檔案會自動輪轉：
- 文字日誌：每日輪轉，保留 7 天
- JSON 日誌：10MB 輪轉，保留 7 個備份

### 4. 任務超時

預設任務超時設定：
- 軟限制：4 分鐘
- 硬限制：5 分鐘

超過限制的任务會被終止。

---

## 📈 下一步建議

### 短期（1-2 週）

1. **整合任務隊列到現有回測頁面**
   - 修改 `pages/2_₿_加密回測.py` 使用 Celery 任務
   - 新增任務狀態查詢頁面

2. **完善日誌記錄**
   - 在關鍵路徑添加日誌
   - 設定日誌警報（錯誤率超過閾值）

3. **API 限流測試**
   - 驗證各 API 限流配置是否合理
   - 根據實際使用情況調整

### 中期（1-2 個月）

4. **PostgreSQL 遷移**
   - 測試 SQLite → PostgreSQL 遷移
   - 更新 `user_db.py` 使用 SQLAlchemy

5. **單元測試覆蓋**
   ```bash
   pytest tests/
   ```

6. **監控儀表板**
   - 整合 Prometheus + Grafana
   - 監控 Celery 任務執行時間、失敗率

### 長期（3 個月+）

7. **微服務拆分**
   - 回測引擎獨立服務
   - 數據抓取獨立服務

8. **CI/CD 流程**
   - GitHub Actions 自動測試
   - 自動部署到生產環境

---

## 🆘 故障排除

### Redis 連接失敗

```bash
# 檢查 Redis 是否運行
docker ps | grep redis

# 重啟 Redis
docker restart stocksx_redis

# 查看 Redis 日誌
docker logs stocksx_redis
```

### Celery Worker 無回應

```bash
# 檢查 Worker 狀態
celery -A src.tasks inspect ping

# 查看 Worker 日誌
celery -A src.tasks worker --loglevel=debug

# 重啟 Worker
docker-compose restart worker
```

### 日誌不輸出

```python
# 確認已初始化
from src.utils.logger import init_default_logger
init_default_logger(level='DEBUG')
```

### 限流過於嚴格

```python
# 調整限流配置
from src.utils.rate_limiter import API_LIMIT_CONFIG

API_LIMIT_CONFIG["alpha_vantage"]["capacity"] = 10  # 提高容量
API_LIMIT_CONFIG["alpha_vantage"]["refill_rate"] = 1.0 / 6  # 加快補充
```

---

## 📚 參考資源

- [Celery 官方文件](https://docs.celeryq.dev/)
- [Redis 官方文件](https://redis.io/docs/)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [令牌桶演算法](https://en.wikipedia.org/wiki/Token_bucket)

---

**最後更新**: 2024-03-03
**版本**: v2.0
