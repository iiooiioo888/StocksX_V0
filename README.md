<div align="center">

<img src="https://github.com/iiooiioo888/StocksX_V0/blob/main/assets/logo.png" alt="StocksX Logo" width="120" />

# 📊 StocksX

### 機構級量化回測與交易監控平台

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://github.com/iiooiioo888/StocksX_V0)
[![CI/CD](https://github.com/iiooiioo888/StocksX_V0/actions/workflows/ci.yml/badge.svg)](https://github.com/iiooiioo888/StocksX_V0/actions)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)
[![pytest](https://img.shields.io/badge/test-pytest-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)

跨市場回測 · 15+ 專業策略 · 即時監控 · WebSocket 推送 · AI 情緒分析

</div>

---

StocksX 是一個開源的量化交易回測與即時監控平台，支援加密貨幣、美股、台股、ETF 與期貨。整合 11 個交易所的真實數據、15+ 經典與機器學習策略、WebSocket 即時推送以及 AI 情緒分析，讓你以機構級的標準打造與驗證交易系統。

---

## ✨ 功能亮點

<table>
<tr>
<td width="50%">

### 🔍 多市場回測

- **11 個交易所** — Binance、OKX、Bybit、Gate.io...
- **美股 / 台股 / ETF / 期貨** — Yahoo Finance 數據
- **真實手續費模擬** — 31 個交易所費率
- **參數優化** — 網格搜索 + Walk-Forward 分析

</td>
<td width="50%">

### ⚡ 即時監控

- **WebSocket 推送** — 幣安真實數據、1 秒更新
- **策略訂閱** — 多交易對 × 多策略組合
- **自動交易** — 信號自動開平倉
- **持倉追蹤** — 即時損益、未實現 P&L

</td>
</tr>
<tr>
<td width="50%">

### 🤖 AI 增強

- **情緒分析** — FinBERT 新聞情緒
- **LSTM 預測** — 價格走勢預測
- **鏈上數據** — 巨鯨動向、交易所流量
- **恐懼貪婪指數** — 即時市場情緒

</td>
<td width="50%">

### 📊 專業圖表

- **K 線圖** — 蠟燭圖 + 技術指標
- **深度圖** — 真實訂單簿可視化
- **權益曲線** — 累積報酬、收益分佈
- **多策略對比** — 5 條權益曲線同框

</td>
</tr>
</table>

---

## 🚀 快速開始

### Docker（推薦）

```bash
# 克隆專案
git clone https://github.com/iiooiioo888/StocksX_V0.git
cd StocksX_V0

# 配置環境變數
cp .env.example .env
# ⚠️ 編輯 .env，設定 SECRET_KEY 和 ADMIN_PASSWORD

# 啟動
docker compose up -d

# 👉 打開 http://localhost:8501
```

### 本地開發

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

### 開發工具

```bash
# 程式碼檢查
ruff check src/ pages/ app.py
ruff format src/ pages/ app.py

# 執行測試（含覆蓋率）
pytest tests/ -v --cov=src --cov-report=term-missing
```

<details>
<summary>🐳 含監控的完整部署（Prometheus + Grafana）</summary>

```bash
docker compose --profile monitoring up -d

# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```

</details>

---

## 🧠 策略庫

<details>
<summary><b>📈 趨勢策略</b>（6 個）</summary>

| 策略 | 說明 | 核心參數 |
|------|------|----------|
| 雙均線交叉 | 快線穿越慢線 | `fast`, `slow` |
| EMA 交叉 | 指數移動平均 | `fast`, `slow` |
| MACD 交叉 | 趨勢動能 | `fast`, `slow`, `signal` |
| ADX 趨勢 | 趨勢強度過濾 | `period`, `threshold` |
| 超級趨勢 | ATR 趨勢跟隨 | `period`, `multiplier` |
| 拋物線 SAR | 趨勢反轉點 | `acceleration`, `maximum` |

</details>

<details>
<summary><b>🔀 擺盪策略</b>（5 個）</summary>

| 策略 | 說明 | 核心參數 |
|------|------|----------|
| RSI | 相對強弱指標 | `period`, `oversold`, `overbought` |
| KD 隨機指標 | 隨機振盪器 | `k_period`, `d_period` |
| 威廉指標 | 超買超賣 | `period`, `oversold`, `overbought` |
| 布林帶 | 波動率通道 | `period`, `std_dev` |
| 一目均衡表 | 綜合趨勢系統 | `tenkan`, `kijun` |

</details>

<details>
<summary><b>💥 突破 + 均值回歸</b>（3 個）</summary>

| 策略 | 說明 | 核心參數 |
|------|------|----------|
| 唐奇安通道 | N 日高低突破 | `period` |
| 雙推力 | 區間突破 | `lookback`, `k1`, `k2` |
| VWAP 回歸 | 成交量加權回歸 | `period`, `threshold` |

</details>

---

## 🏗️ 技術架構

### 核心架構（v5.0 — 模組化重構）

```
┌─────────────────────────────────────────────────────────────────────┐
│                         使用者層 (User Layer)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐│
│  │ 回測頁面  │  │ 監控頁面  │  │ AI 分析  │  │ 歷史記錄 & 對比      ││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────────┘│
└───────┼──────────────┼──────────────┼────────────────┼──────────────┘
        │              │              │                │
        ▼              ▼              ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Orchestrator（統一編排層）                         │
│         run_backtest() · fetch_ohlcv() · compute_signals()          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│  Provider     │  │  Pipeline    │  │  Strategy Registry   │
│  數據源路由    │  │  數據清洗     │  │  策略註冊 & 信號計算  │
└──────────────┘  └──────────────┘  └──────────────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│  Backtest     │  │  Middleware  │  │  SignalBus           │
│  回測引擎     │  │  中間件管道   │  │  信號發布訂閱         │
└──────────────┘  └──────────────┘  └──────────────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│  CacheManager │  │  Repository  │  │  TaskQueue           │
│  快取管理     │  │  數據存取     │  │  後台任務             │
└──────────────┘  └──────────────┘  └──────────────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│  AlertManager │  │  Container   │  │  Config              │
│  告警系統     │  │  DI 容器     │  │  配置管理             │
└──────────────┘  └──────────────┘  └──────────────────────┘
```

### 技術棧一覽

| 層級 | 技術 |
|:----:|------|
| **前端** | Streamlit · Plotly.js · Glassmorphism CSS |
| **後端** | Python 3.10+ · FastAPI · SQLite / PostgreSQL |
| **即時** | WebSocket · CCXT · Binance API |
| **數據** | Pandas · NumPy · yfinance · CoinGecko |
| **AI/ML** | scikit-learn · TensorFlow · FinBERT · Gymnasium |
| **基礎設施** | Docker · Redis · Celery · Prometheus · Grafana |
| **品質** | Ruff · pytest · GitHub Actions CI/CD · pre-commit |

---

## 🧩 核心架構模組 (`src/core/`)

### Orchestrator — 統一編排層

取代散落在各頁面中的業務邏輯。所有操作通過 `Orchestrator` 入口，屏蔽 Provider / Pipeline / Registry 的組合細節。

```python
from src.core import get_orchestrator

orch = get_orchestrator()

# 一鍵回測
report = orch.run_backtest("BTC/USDT:USDT", "1h", "sma_cross", fast=10, slow=30)

# 取得即時行情
ticker = orch.get_ticker("AAPL")

# 計算信號
signals = orch.compute_signals("ETH/USDT", "rsi_signal")

# 多策略對比
results = orch.run_multi_backtest("BTC/USDT:USDT", "1h", ["sma_cross", "rsi_signal"])

# 列出所有策略
strategies = orch.list_strategies()
```

### Middleware Pipeline — 中間件管道

橫切關注點（日誌、重試、限流、耗時統計）通過中間件鏈處理，取代散落的 `try/except` 和重複邏輯。

```python
from src.core import MiddlewarePipeline, LoggingMiddleware, RetryMiddleware, RateLimitMiddleware

pipe = MiddlewarePipeline(name="data_fetch")
pipe.use(LoggingMiddleware())
pipe.use(RetryMiddleware(max_retries=3, delay=1.0, backoff=2.0))
pipe.use(RateLimitMiddleware(rps=10))

result = pipe.execute(lambda: provider.fetch_ohlcv("BTC/USDT", "1h"))
```

**可用中間件：**
- `LoggingMiddleware` — 自動日誌記錄
- `RetryMiddleware` — 指數退避自動重試
- `RateLimitMiddleware` — 速率限制
- `TimingMiddleware` — 耗時統計

也支持裝飾器語法：

```python
from src.core import with_middleware, LoggingMiddleware, RetryMiddleware

@with_middleware(LoggingMiddleware(), RetryMiddleware(max_retries=3))
def fetch_data(symbol):
    return provider.fetch_ohlcv(symbol, "1h")
```

### CacheManager — 快取管理

支援 Redis 與記憶體兩種後端，TTL 自動過期，多命名空間隔離。

```python
from src.core import get_cache_manager

cache = get_cache_manager()
ns = cache.namespace("ohlcv")

ns.set("BTC/USDT:1h", data, ttl=300)
data = ns.get("BTC/USDT:1h")
stats = cache.stats()  # CacheStats(hits=100, misses=5, hit_rate=95.2)
```

### Repository Pattern — 數據存取抽象

通過 Protocol 定義存取介面，可替換為 PostgreSQL / Redis / In-Memory。

```python
from src.core import get_backtest_repository, BacktestRecord

repo = get_backtest_repository()

# 建立
record = BacktestRecord(id=None, user_id=1, symbol="BTC/USDT", strategy="sma_cross", ...)
rid = repo.save(record)

# 查詢
record = repo.find_by_id(rid)
records = repo.find_by_user(user_id=1, limit=20)
records = repo.find_by_symbol("BTC/USDT:USDT")

# 刪除
repo.delete(rid)
```

### Task Queue — 後台任務系統

輕量線程池任務隊列，無需 Redis 即可執行非同步回測。

```python
from src.core import get_task_queue

queue = get_task_queue()

# 提交任務
task_id = queue.submit("backtest", run_backtest, args=("BTC/USDT", "sma_cross"))

# 查詢狀態
info = queue.status(task_id)  # TaskInfo(status=RUNNING, ...)

# 等待結果
result = queue.result(task_id, timeout=60)
```

### Alert System — 監控告警

規則引擎 + 多渠道通知（日誌 / Bark / Webhook）。

```python
from src.core import get_alert_manager, AlertRule, AlertSeverity

mgr = get_alert_manager()

# 添加自定義規則
mgr.add_rule(AlertRule(
    name="high_drawdown",
    condition=lambda m: m.get("max_drawdown_pct", 0) > 20,
    message_template="⚠️ 最大回撤超過 20%: {max_drawdown_pct:.1f}%",
    severity=AlertSeverity.CRITICAL,
    cooldown_seconds=600,
))

# 檢查指標
fired = mgr.check({"max_drawdown_pct": 25.0})

# 查看歷史
history = mgr.history(limit=10)
```

**預設告警規則：**
- `high_drawdown` — 最大回撤 > 20%
- `low_winrate` — 勝率 < 30%（>10 筆交易）
- `negative_sharpe` — Sharpe Ratio < -1
- `high_consecutive_loss` — 連續虧損 > 5 次

### DI Container — 依賴注入容器

取代散落的全局單例，所有組件通過 Container 註冊和獲取。

```python
from src.core import get_container, Settings, MarketProvider

container = get_container()

# 取得核心組件
settings = container.get(Settings)
provider = container.get(MarketProvider)

# 替換（測試用）
from tests.mocks import MockProvider
container.register(MarketProvider, MockProvider())
```

### Provider — 數據源路由

自動路由到最佳 Provider（CCXT 交易所 / Yahoo Finance），統一介面。

```python
from src.core import CCXTProvider, YahooProvider, CompositeProvider

composite = CompositeProvider()
composite.add(CCXTProvider("binance"))
composite.add(YahooProvider())

ohlcv = composite.fetch_ohlcv("BTC/USDT:USDT", "1h", limit=100)
ticker = composite.fetch_ticker("AAPL")
```

### Strategy Registry — 策略註冊中心

通過裝飾器自動註冊策略，支持查詢、信號計算。

```python
from src.core import register_strategy, registry

@register_strategy("my_strategy", label="我的策略", category="趨勢")
def my_strategy(rows, **params):
    # 計算信號：1=做多, -1=做空, 0=觀望
    signals = []
    for i, row in enumerate(rows):
        signals.append(1 if row["close"] > row["open"] else -1)
    return signals

# 使用
strategies = registry.list_all()
signals = registry.get_signal("my_strategy", ohlcv_data)
```

---

## 📁 專案結構

```
StocksX_V0/
├── app.py                          # 主頁儀表板
├── pages/                          # Streamlit 多頁應用
│   ├── 1_🔐_登入.py                # 用戶認證
│   ├── 2_₿_加密回測.py             # 加密貨幣回測（Orchestrator）
│   ├── 2_🏛️_傳統回測.py           # 美股 / 台股 / ETF（Orchestrator）
│   ├── 3_📜_歷史.py                # 歷史記錄 & 對比
│   ├── 5_📡_交易監控.py            # 策略訂閱監控
│   ├── 6_📰_新聞.py               # RSS 新聞聚合
│   ├── 7_🏥_健康檢查.py            # 系統健康監控
│   ├── 8_⚡_即時監控.py            # WebSocket 即時
│   ├── 9_🧠_AI 策略.py             # AI 情緒分析
│   ├── 10_📊_策略回测对比.py        # 多策略對比
│   └── 11_🤖_自動交易.py           # 自動交易配置
├── src/
│   ├── core/                       # 🏗️ 核心架構（v5.0）
│   │   ├── __init__.py             # 統一導出
│   │   ├── orchestrator.py         # 統一編排層
│   │   ├── provider.py             # 數據源抽象
│   │   ├── pipeline.py             # 數據清洗管道
│   │   ├── backtest.py             # 回測引擎
│   │   ├── signals.py              # 信號系統
│   │   ├── registry.py             # 策略註冊中心
│   │   ├── middleware.py           # 中間件管道
│   │   ├── cache_manager.py        # 快取管理
│   │   ├── repository.py           # Repository Pattern
│   │   ├── tasks.py                # 後台任務隊列
│   │   ├── alerts.py               # 告警系統
│   │   ├── container.py            # DI 容器
│   │   ├── config.py               # 配置管理
│   │   ├── adapters.py             # Provider 實現
│   │   └── strategies_bridge.py    # 舊策略橋接
│   ├── auth/                       # 用戶認證 & SQLite
│   ├── backtest/                   # 回測引擎 & 策略庫
│   ├── data/                       # 數據源整合
│   │   ├── sources/                # API Hub（快取 + 限流）
│   │   ├── crypto/                 # CCXT 加密數據
│   │   └── traditional/            # Yahoo Finance
│   ├── strategies/                 # 進階策略
│   │   ├── ml_strategies/          # LSTM / 機器學習
│   │   ├── nlp_strategies/         # NLP 情緒分析
│   │   ├── quant_strategies/       # 多因子 / 配對交易
│   │   └── rl_strategies/          # 強化學習
│   ├── trading/                    # 自動交易引擎
│   ├── utils/                      # 工具（快取 / 日誌 / 限流）
│   ├── websocket_server.py         # FastAPI WebSocket
│   └── ui_modern.py                # Glassmorphism 主題
├── tests/                          # pytest 測試
│   └── test_core/                  # 核心模組測試
│       ├── test_repository.py      # Repository CRUD
│       ├── test_tasks.py           # TaskQueue
│       ├── test_alerts.py          # AlertManager
│       ├── test_container.py       # DI Container
│       ├── test_orchestrator.py    # Orchestrator 整合
│       ├── test_middleware.py       # Middleware Pipeline
│       └── test_backtest.py        # 回測引擎
├── .github/workflows/ci.yml       # CI/CD（Ruff + pytest + Docker）
├── docker-compose.yml              # Docker 編排
└── Dockerfile                      # 多階段構建
```

---

## ⚙️ 配置說明

### 環境變數 (.env)

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `SECRET_KEY` | JWT 簽名密鑰（**必填**） | — |
| `ADMIN_PASSWORD` | 管理員密碼（**必填**） | — |
| `DATABASE_URL` | 資料庫連接字串 | `sqlite:///data/stocksx.db` |
| `REDIS_URL` | Redis 連接字串 | `redis://localhost:6379/0` |
| `LOG_LEVEL` | 日誌等級 | `INFO` |
| `BARK_KEY` | iOS Bark 推播 Key | — |
| `TASK_WORKERS` | 後台任務執行緒數 | `4` |

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/health` | GET | 健康檢查 |
| `/ws` | WebSocket | 即時行情推送 |
| `/api/v1/backtest` | POST | 提交回測任務 |
| `/api/v1/strategies` | GET | 策略列表 |

---

## 📊 績效指標

平台自動計算以下指標：

| 類別 | 指標 |
|------|------|
| **報酬** | 總報酬、年化報酬、平均報酬 |
| **風險** | 最大回撤、標準差、VaR (95%) |
| **風險調整** | Sharpe、Sortino、Calmar |
| **交易** | 勝率、利潤因子、最大連勝/連敗 |
| **進階** | Omega Ratio、Tail Ratio |

---

## 🔐 安全

- 🔒 **密碼** — PBKDF2-SHA256（100,000 iterations）
- 🔑 **Session** — JWT 令牌、1 小時超時
- 🛡️ **限流** — 令牌桶演算法、登入鎖定機制
- 📝 **審計** — 完整登入日誌
- 🐳 **容器** — 非 root 運行、tini init

---

## 📝 更新日誌

### v5.0.0 (2026-03-19)
- 🏗️ **核心架構重構** — `src/core/` 模組化設計
- ⚡ **Orchestrator** — 統一編排層，取代散落業務邏輯
- 🔄 **Middleware Pipeline** — 日誌、重試、限流中間件
- 💾 **CacheManager** — Redis / 記憶體快取管理
- 📦 **Repository Pattern** — 數據存取抽象（SQLite）
- 📋 **TaskQueue** — 輕量線程池後台任務
- 🚨 **Alert System** — 規則引擎 + 多渠道告警
- 🧩 **DI Container** — 依賴注入容器
- 🧪 **測試擴展** — Repository / TaskQueue / Alert / Container / Orchestrator
- 🚀 **CI/CD 增強** — Python 3.10/3.11/3.12 矩陣測試 + 覆蓋率

### v4.2.0 (2026-03-19)
- ⚡ 記憶體快取層（API 響應 TTL）
- 🧪 pytest 測試體系（UserDB / 策略 / 快取）
- 🛠️ UI 共用元件庫（錯誤邊界 / 狀態卡片）
- 📊 資料庫查詢助手（減少重複程式碼）

<details>
<summary>📜 更早版本</summary>

### v4.1.0
- 🔒 安全強化（.gitignore / Docker secrets）
- 📝 結構化日誌系統
- 🚀 GitHub Actions CI/CD
- 🐳 Docker 最佳化（tini / Redis LRU）

### v4.0.0
- CCXT / Yahoo Finance 真實數據
- WebSocket 即時推送
- Plotly 專業圖表
- 情緒分析 & 鏈上數據

### v3.0.0
- FastAPI 後端分離
- Celery 任務隊列
- 健康檢查端點

</details>

---

## 🤝 貢獻指南

歡迎貢獻！請閱讀 [CONTRIBUTING.md](CONTRIBUTING.md) 了解詳細流程。

### 開發環境設置

```bash
# 安裝開發依賴
pip install -r requirements-dev.txt
pre-commit install

# 程式碼檢查
ruff check src/ app.py pages/
ruff format src/ app.py pages/

# 測試（含覆蓋率）
pytest tests/ -v --cov=src --cov-report=term-missing
```

### 提交規範

```
feat: 新增功能
fix: 修復 bug
docs: 文件更新
refactor: 重構
test: 測試相關
chore: 建置 / 工具變更
```

---

## 📄 授權

本專案採用 [MIT License](LICENSE) 授權。

---

## ⚠️ 免責聲明

**本軟體僅供學習與研究，不構成投資建議。**

回測結果基於歷史數據，不代表未來表現。交易涉及風險，請謹慎評估。

---

<div align="center">

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=iiooiioo888/StocksX_V0&type=Date)](https://star-history.com/#iiooiioo888/StocksX_V0&Date)

---

**Made with ❤️ by StocksX Team** · © 2024–2026

[⬆ 回到頂部](#-stocksx)

</div>
