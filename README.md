<div align="center">

<img src="https://github.com/iiooiioo888/StocksX_V0/blob/main/assets/logo.png" alt="StocksX Logo" width="120" />

# 📊 StocksX

### 機構級量化回測與交易監控平台

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![CI/CD](https://github.com/iiooiioo888/StocksX_V0/actions/workflows/ci.yml/badge.svg)](https://github.com/iiooiioo888/StocksX_V0/actions)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)
[![pytest](https://img.shields.io/badge/test-pytest-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)

跨市場回測 · 15+ 專業策略 · 即時監控 · WebSocket 推送 · AI 情緒分析

</div>

---

## 🚀 快速開始

```bash
git clone https://github.com/iiooiioo888/StocksX_V0.git && cd StocksX_V0
cp .env.example .env   # 編輯 SECRET_KEY / ADMIN_PASSWORD
docker compose up -d   # 👉 http://localhost:8501
```

<details>
<summary>本地開發</summary>

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

</details>

<details>
<summary>含監控部署（Prometheus + Grafana）</summary>

```bash
docker compose --profile monitoring up -d
# Grafana: http://localhost:3000 | Prometheus: http://localhost:9090
```

</details>

---

## ✨ 功能亮點

| 領域 | 能力 |
|------|------|
| 🔍 **多市場回測** | 11 個交易所 · 美股/台股/ETF/期貨 · 真實手續費模擬 · Walk-Forward 分析 |
| ⚡ **即時監控** | WebSocket 幣安推送 · 策略訂閱 · 自動交易 · 即時 P&L |
| 🤖 **AI 增強** | FinBERT 情緒分析 · LSTM 預測 · 恐懼貪婪指數 |
| 📊 **專業圖表** | K 線圖 · 深度圖 · 權益曲線 · 多策略對比 |
| 🏗️ **現代架構** | Orchestrator 編排 · DI 容器 · 中間件管道 · Repository 模式 |

---

## 🏗️ 技術架構

### 核心設計理念

StocksX v5.1 採用**分層模組化架構**，所有業務邏輯通過 `Orchestrator` 統一編排，橫切關注點由中間件管道處理，數據存取通過 Repository 抽象隔離。

```
┌──────────────────────────────────────────────────────────┐
│                    📱 Pages (Streamlit UI)                │
│   回測 · 監控 · AI · 歷史 · 新聞 · 管理 · 自動交易        │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                  🔗 Orchestrator（統一編排層）              │
│  run_backtest() · fetch_ohlcv() · compute_signals()       │
└──┬──────────┬──────────┬──────────┬──────────┬───────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌────────┐ ┌──────┐ ┌──────────┐
│Provider│ │Pipeline│ │Registry│ │Signal│ │Backtest  │
│數據源  │ │清洗管道│ │策略中心│ │信號匯│ │回測引擎  │
└──────┘ └────────┘ └────────┘ └──────┘ └──────────┘
   │          │          │          │          │
┌──▼──────────▼──────────▼──────────▼──────────▼───────────┐
│                  🧩 基礎設施層                              │
│  Middleware · CacheManager · Repository · TaskQueue        │
│  AlertManager · DI Container · Config                     │
└──────────────────────────────────────────────────────────┘
```

### 技術棧

| 層級 | 技術 |
|:----:|------|
| **前端** | Streamlit · Plotly · Glassmorphism CSS |
| **後端** | Python 3.10+ · FastAPI · SQLite / PostgreSQL |
| **即時** | WebSocket · CCXT · Binance API |
| **數據** | Pandas · NumPy · yfinance · CoinGecko |
| **AI/ML** | scikit-learn · TensorFlow · FinBERT |
| **基礎設施** | Docker · Redis · Celery · Prometheus · Grafana |
| **品質** | Ruff · pytest · GitHub Actions · bandit · mypy |

---

## 🧩 核心架構模組 (`src/core/`)

<details>
<summary><b>Orchestrator</b> — 統一編排層</summary>

所有操作通過 `Orchestrator` 入口，屏蔽 Provider / Pipeline / Registry 組合細節：

```python
from src.core import get_orchestrator
orch = get_orchestrator()

report = orch.run_backtest("BTC/USDT:USDT", "1h", "sma_cross", fast=10, slow=30)
ticker = orch.get_ticker("AAPL")
signals = orch.compute_signals("ETH/USDT", "rsi_signal")
results = orch.run_multi_backtest("BTC/USDT:USDT", "1h", ["sma_cross", "rsi_signal"])
```

</details>

<details>
<summary><b>Middleware Pipeline</b> — 橫切關注點</summary>

日誌、重試、限流、耗時統計通過中間件鏈處理：

```python
from src.core import MiddlewarePipeline, LoggingMiddleware, RetryMiddleware, RateLimitMiddleware

pipe = MiddlewarePipeline(name="data_fetch")
pipe.use(LoggingMiddleware())
pipe.use(RetryMiddleware(max_retries=3, delay=1.0, backoff=2.0))
pipe.use(RateLimitMiddleware(rps=10))
result = pipe.execute(lambda: provider.fetch_ohlcv("BTC/USDT", "1h"))
```

**可用中間件：** `LoggingMiddleware` · `RetryMiddleware` · `RateLimitMiddleware` · `TimingMiddleware`

也支持裝飾器語法：
```python
from src.core import with_middleware, LoggingMiddleware, RetryMiddleware

@with_middleware(LoggingMiddleware(), RetryMiddleware(max_retries=3))
def fetch_data(symbol):
    return provider.fetch_ohlcv(symbol, "1h")
```

</details>

<details>
<summary><b>CacheManager</b> — 統一快取管理</summary>

支援 Redis 與記憶體兩種後端，TTL 自動過期，多命名空間隔離：

```python
from src.core import get_cache_manager

cache = get_cache_manager()
ns = cache.namespace("ohlcv")
ns.set("BTC/USDT:1h", data, ttl=300)
data = ns.get("BTC/USDT:1h")
stats = cache.stats()  # CacheStats(hits=100, misses=5, hit_rate=95.2)
```

</details>

<details>
<summary><b>Repository Pattern</b> — 數據存取抽象</summary>

通過 Protocol 定義存取介面，可替換為 PostgreSQL / Redis / In-Memory：

```python
from src.core import get_backtest_repository, BacktestRecord

repo = get_backtest_repository()
rid = repo.save(BacktestRecord(id=None, user_id=1, symbol="BTC/USDT", ...))
record = repo.find_by_id(rid)
records = repo.find_by_user(user_id=1, limit=20)
repo.delete(rid)
```

</details>

<details>
<summary><b>Task Queue</b> — 後台任務系統</summary>

輕量線程池任務隊列，無需 Redis 即可執行非同步回測：

```python
from src.core import get_task_queue

queue = get_task_queue()
task_id = queue.submit("backtest", run_backtest, args=("BTC/USDT", "sma_cross"))
info = queue.status(task_id)     # TaskInfo(status=RUNNING, ...)
result = queue.result(task_id, timeout=60)
```

</details>

<details>
<summary><b>Alert System</b> — 監控告警</summary>

規則引擎 + 多渠道通知（日誌 / Bark / Webhook）：

```python
from src.core import get_alert_manager, AlertRule, AlertSeverity

mgr = get_alert_manager()
mgr.add_rule(AlertRule(
    name="high_drawdown",
    condition=lambda m: m.get("max_drawdown_pct", 0) > 20,
    message_template="⚠️ 最大回撤超過 20%: {max_drawdown_pct:.1f}%",
    severity=AlertSeverity.CRITICAL,
    cooldown_seconds=600,
))
fired = mgr.check({"max_drawdown_pct": 25.0})
```

**預設規則：** `high_drawdown` · `low_winrate` · `negative_sharpe` · `high_consecutive_loss`

</details>

<details>
<summary><b>DI Container</b> — 依賴注入容器</summary>

取代散落的全局單例，所有組件通過 Container 註冊和獲取：

```python
from src.core import get_container, Settings, MarketProvider

container = get_container()
settings = container.get(Settings)
provider = container.get(MarketProvider)

# 測試時替換
container.register(MarketProvider, MockProvider())
```

</details>

<details>
<summary><b>Strategy Registry</b> — 策略註冊中心</summary>

通過裝飾器自動註冊策略，支持查詢、信號計算：

```python
from src.core import register_strategy, registry

@register_strategy("my_strategy", label="我的策略", category="trend")
def my_strategy(rows, **params):
    return [1 if r["close"] > r["open"] else -1 for r in rows]

strategies = registry.list_all()
signals = registry.get_signal("my_strategy", ohlcv_data)
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

## 📁 專案結構

```
StocksX_V0/
├── app.py                          # 主頁儀表板
├── pages/                          # Streamlit 多頁應用
│   ├── 1_🔐_登入.py                # 用戶認證
│   ├── 2_₿_加密回測.py             # 加密貨幣回測（Orchestrator）
│   ├── 2_🏛️_傳統回測.py           # 美股/台股/ETF（Orchestrator）
│   ├── 3_📜_歷史.py                # 歷史記錄 & 對比
│   ├── 4_🛠️_管理.py               # 管理後台
│   ├── 5_📡_交易監控.py            # 策略訂閱監控
│   ├── 6_📰_新聞.py               # RSS 新聞聚合
│   ├── 7_🏥_健康檢查.py            # 系統健康監控
│   ├── 8_⚡_即時監控.py            # WebSocket 即時
│   ├── 9_🧠_AI 策略.py             # AI 情緒分析
│   ├── 10_📊_策略回测对比.py        # 多策略對比
│   └── 11_🤖_自動交易.py           # 自動交易配置
├── src/
│   ├── core/                       # 🏗️ 核心架構
│   │   ├── orchestrator.py         # 統一編排層
│   │   ├── middleware.py           # 中間件管道
│   │   ├── cache_manager.py        # 快取管理
│   │   ├── repository.py           # Repository Pattern
│   │   ├── tasks.py                # 後台任務隊列
│   │   ├── alerts.py               # 告警系統
│   │   ├── container.py            # DI 容器
│   │   ├── config.py               # 配置管理
│   │   ├── provider.py             # 數據源抽象
│   │   ├── pipeline.py             # 數據清洗管道
│   │   ├── signals.py              # 信號系統
│   │   ├── registry.py             # 策略註冊中心
│   │   ├── backtest.py             # 回測引擎
│   │   └── adapters.py             # Provider 實現
│   ├── auth/                       # 用戶認證 & SQLite
│   ├── backtest/                   # 回測引擎 & 策略庫
│   ├── data/                       # 數據源整合
│   ├── strategies/                 # 進階策略（ML/NLP/RL）
│   ├── trading/                    # 自動交易引擎
│   ├── utils/                      # 工具（日誌/限流/健康檢查）
│   └── ui_*.py                     # UI 組件
├── tests/                          # pytest 測試
│   └── test_core/                  # 核心模組測試（100% 覆蓋目標）
├── .github/workflows/ci.yml        # CI/CD（Lint + Test + Security + Docker）
├── docker-compose.yml              # Docker 編排
└── Dockerfile                      # 多階段構建
```

---

## ⚙️ 配置

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

---

## 📊 績效指標

| 類別 | 指標 |
|------|------|
| **報酬** | 總報酬、年化報酬、平均報酬 |
| **風險** | 最大回撤、標準差、VaR (95%) |
| **風險調整** | Sharpe、Sortino、Calmar |
| **交易** | 勝率、利潤因子、最大連勝/連敗 |
| **進階** | Omega Ratio、Tail Ratio |

---

## 🔐 安全

- 🔒 密碼 — PBKDF2-SHA256（100,000 iterations）
- 🔑 Session — JWT 令牌、1 小時超時
- 🛡️ 限流 — 令牌桶演算法、登入鎖定機制
- 📝 審計 — 完整登入日誌
- 🔍 CI — bandit 靜態安全分析 + safety 依賴漏洞掃描

---

## 🤝 貢獻

```bash
pip install -r requirements-dev.txt
pre-commit install

# 程式碼檢查
ruff check src/ pages/ app.py tests/
ruff format src/ pages/ app.py tests/

# 測試
pytest tests/ -v --cov=src --cov-report=term-missing
```

提交規範：`feat:` · `fix:` · `docs:` · `refactor:` · `test:` · `chore:`

---

## 📝 更新日誌

### v5.1.0 (2026-03-20)
- 🏗️ **配置統一** — 消除 `src/config.py` 與 `src/core/config.py` 的重複 Settings 類
- 🚀 **CI/CD 增強** — 加入 bandit 安全掃描、mypy 類型檢查、GHCR 推送、SSH 部署
- 📖 **README 現代化** — 精簡結構、折疊式技術文檔、清晰架構圖
- 🧪 **測試強化** — pytest-timeout 防掛起、Python 3.10/3.11/3.12 矩陣測試

### v5.0.0 (2026-03-19)
- 🏗️ **核心架構重構** — `src/core/` 模組化設計
- ⚡ **Orchestrator** — 統一編排層，取代散落業務邏輯
- 🔄 **Middleware Pipeline** — 日誌、重試、限流中間件
- 💾 **CacheManager** — Redis / 記憶體快取管理
- 📦 **Repository Pattern** — 數據存取抽象
- 📋 **TaskQueue** — 輕量線程池後台任務
- 🚨 **Alert System** — 規則引擎 + 多渠道告警
- 🧩 **DI Container** — 依賴注入容器

<details>
<summary>📜 更早版本</summary>

### v4.2.0 — 記憶體快取、pytest 測試、UI 共用元件
### v4.1.0 — 安全強化、結構化日誌、GitHub Actions CI/CD
### v4.0.0 — CCXT / Yahoo Finance 真實數據、WebSocket 即時推送
### v3.0.0 — FastAPI 後端分離、Celery 任務隊列

</details>

---

## 📄 授權

[MIT License](LICENSE)

---

<div align="center">

⚠️ **免責聲明：本軟體僅供學習與研究，不構成投資建議。**

回測結果基於歷史數據，不代表未來表現。

**Made with ❤️ by StocksX Team** · © 2024–2026

</div>
