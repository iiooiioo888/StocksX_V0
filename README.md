<div align="center">

<img src="https://github.com/iiooiioo888/StocksX_V0/blob/main/assets/logo.png" alt="StocksX Logo" width="120" />

# 📊 StocksX

### 機構級量化回測與即時交易監控平台

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![CI/CD](https://github.com/iiooiioo888/StocksX_V0/actions/workflows/ci.yml/badge.svg)](https://github.com/iiooiioo888/StocksX_V0/actions)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)
[![pytest](https://img.shields.io/badge/test-pytest-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Dependabot](https://img.shields.io/badge/deps-Dependabot-0066D?logo=dependabot&logoColor=white)](https://docs.github.com/en/code-security/dependabot)

**跨市場回測 · 15+ 專業策略 · 即時監控 · WebSocket 推送 · AI 情緒分析**

[快速開始](#-快速開始) · [功能亮點](#-功能亮點) · [架構設計](#️-架構設計) · [部署指南](#-部署指南)

</div>

---

## ⚡ 一鍵啟動

```bash
git clone https://github.com/iiooiioo888/StocksX_V0.git && cd StocksX_V0
cp .env.example .env && docker compose up -d
# 👉 http://localhost:8501
```

---

## ✨ 功能亮點

<table>
<tr>
<td width="50%">

### 🔍 多市場回測
- 11 個交易所 · 美股/台股/ETF/期貨
- 真實手續費模擬 · Walk-Forward 分析
- 多策略對比 · 參數網格搜索

### ⚡ 即時監控
- WebSocket 幣安推送 · 策略訂閱
- 自動交易 · 即時 P&L 追蹤
- 連接斷線自動重試

</td>
<td width="50%">

### 🤖 AI 增強
- FinBERT 情緒分析 · LSTM 預測
- 恐懼貪婪指數 · VIX 波動率
- DashScope / OpenAI 整合

### 🏗️ 現代架構
- Orchestrator 編排 · DI 容器
- 中間件管道 · Repository 模式
- 結構化日誌 · Prometheus 監控

</td>
</tr>
</table>

### 📊 策略庫（15+ 策略）

| 類別 | 策略 | 說明 |
|:---:|------|------|
| 📈 趨勢 | 雙均線交叉 · EMA 交叉 · MACD · ADX · 超級趨勢 · 拋物線 SAR | 趨勢跟隨與動量 |
| 🔀 擺盪 | RSI · KD · 威廉指標 · 布林帶 · 一目均衡表 | 超買超賣振盪 |
| 💥 突破 | 唐奇安通道 · 雙推力 · VWAP 回歸 | 區間突破與均值回歸 |
| 🧠 AI/ML | LSTM 預測 · 情緒分析 · 多因子策略 · 配對交易 | 機器學習增強 |

---

## 🏗️ 架構設計

### 技術架構（六層分離）

```mermaid
graph TB
    subgraph PRESENTATION["🎨 表現層 (Presentation)"]
        direction LR
        ST[Streamlit Dashboard<br/>Glassmorphism UI]
        FE[FastAPI REST + WebSocket<br/>即時行情推送]
        PLT[Plotly 互動圖表<br/>K線 / 權益曲線 / 指標]
    end

    subgraph APPLICATION["⚙️ 應用層 (Application)"]
        direction LR
        ORCH[Orchestrator<br/>統一業務編排]
        REG[StrategyRegistry<br/>裝飾器策略註冊]
        SIG[SignalBus<br/>信號發布訂閱]
        AUTH[JWT Auth<br/>RBAC 權限管理]
    end

    subgraph DOMAIN["📐 領域層 (Domain)"]
        direction LR
        BT[BacktestEngine<br/>向量化回測]
        STRAT[Strategy Logic<br/>15+ 量化策略]
        RISK[RiskManager<br/>VaR / 倉位管理]
        PORT[Portfolio<br/>風險平價 / 有效前沿]
    end

    subgraph INFRASTRUCTURE["🧩 基礎設施層 (Infrastructure)"]
        direction LR
        DI[DI Container<br/>依賴注入]
        MW[Middleware Pipeline<br/>日誌·重試·限流]
        CACHE[CacheManager<br/>Redis / Memory]
        REPO[Repository Pattern<br/>SQLAlchemy 抽象]
        TASK[TaskQueue<br/>Celery 異步任務]
        ALERT[AlertManager<br/>Bark / Webhook]
    end

    subgraph DATA["🌐 數據層 (Data)"]
        direction LR
        CCXT[CCXT Gateway<br/>11 交易所統一介面]
        YF[Yahoo Finance<br/>美股/台股/ETF]
        CG[CoinGecko<br/>市場情緒 & 價格]
        WS[WebSocket Server<br/>Binance 即時推送]
        RSS[RSS Aggregator<br/>加密新聞聚合]
    end

    subgraph PERSISTENCE["💾 持久化層 (Persistence)"]
        direction LR
        SQLite[SQLite<br/>本地輕量存儲]
        REDIS[(Redis 7<br/>高速緩存 & 消息)]
        PG[(PostgreSQL<br/>生產級數據庫)]
    end

    PRESENTATION --> APPLICATION
    APPLICATION --> DOMAIN
    APPLICATION --> INFRASTRUCTURE
    DOMAIN --> INFRASTRUCTURE
    INFRASTRUCTURE --> DATA
    INFRASTRUCTURE --> PERSISTENCE

    style PRESENTATION fill:#1a1a2e,stroke:#667eea,color:#e0e0e0
    style APPLICATION fill:#16213e,stroke:#009688,color:#e0e0e0
    style DOMAIN fill:#0f3460,stroke:#f39c12,color:#e0e0e0
    style INFRASTRUCTURE fill:#1a1a2e,stroke:#764ba2,color:#e0e0e0
    style DATA fill:#16213e,stroke:#e94560,color:#e0e0e0
    style PERSISTENCE fill:#0f3460,stroke:#58a6ff,color:#e0e0e0
```

### 核心設計模式

| 模式 | 實現 | 優勢 |
|:---:|------|------|
| **Orchestrator** | `src/core/orchestrator.py` | 統一業務入口，屏蔽組合複雜度 |
| **Registry** | `src/core/registry.py` | `@register_strategy` 裝飾器自動註冊 |
| **Repository** | `src/core/repository.py` | 數據存取抽象，SQLite ↔ PostgreSQL 無縫切換 |
| **DI Container** | `src/core/container.py` | 輕量依賴注入，便於測試替換 |
| **Middleware Pipeline** | `src/core/middleware.py` | 橫切關注點（日誌/重試/限流）管道化 |
| **Signal Bus** | `src/core/signals.py` | 發布訂閱模式，策略信號實時推送 |
| **Provider Composite** | `src/core/adapters.py` | 多數據源組合，自動故障轉移 |

### 數據流

```mermaid
sequenceDiagram
    participant U as 📱 UI
    participant O as ⚙️ Orchestrator
    participant P as 📡 Provider
    participant C as 🧹 Pipeline
    participant R as 📋 Registry
    participant B as 💹 BacktestEngine
    participant S as 📊 SignalBus

    U->>O: run_backtest("BTC/USDT", "1h", "sma_cross")
    O->>P: fetch_ohlcv(symbol, timeframe)
    P-->>O: raw OHLCV data
    O->>C: clean(raw_data)
    C-->>O: cleaned data
    O->>R: get_signal(strategy, data)
    R-->>O: signals [1, -1, 0, ...]
    O->>B: run(data, signals)
    B-->>O: BacktestReport
    O->>S: publish(latest_signal)
    O-->>U: report + metrics
```

### 技術棧

| 層級 | 技術 | 用途 |
|:---:|------|------|
| **前端** | Streamlit · Plotly · Glassmorphism CSS | 互動式 Web UI |
| **API** | FastAPI · Uvicorn · WebSockets | REST API & 即時推送 |
| **即時** | CCXT · Binance API · aiohttp | 多交易所行情 |
| **數據** | Pandas · NumPy · yfinance · CoinGecko | 數據處理與來源 |
| **AI/ML** | scikit-learn · DashScope · TensorFlow | 機器學習 & 深度學習 |
| **存儲** | SQLite · Redis 7 · SQLAlchemy · PostgreSQL | 數據持久化 & 高速緩存 |
| **任務** | Celery · Redis Broker | 後台異步任務 |
| **監控** | Prometheus · Grafana · psutil | 系統監控告警 |
| **打包** | pyproject.toml · pip install -e . | PEP 621 現代打包 |
| **DevOps** | Docker · Docker Compose · GitHub Actions · Dependabot | CI/CD & 自動化 |
| **品質** | Ruff · pytest · bandit · mypy · pre-commit | 代碼品質全鏈路 |

---

## 🚀 快速開始

### 方式一：Docker（推薦）

```bash
# 1. 克隆專案
git clone https://github.com/iiooiioo888/StocksX_V0.git
cd StocksX_V0

# 2. 配置環境
cp .env.example .env
# 編輯 .env，至少設定：
#   SECRET_KEY=<隨機字串>     # python -c "import secrets; print(secrets.token_hex(32))"
#   ADMIN_PASSWORD=<你的密碼>

# 3. 啟動服務
docker compose up -d

# 4. 訪問
# 主應用：http://localhost:8501
# WebSocket：ws://localhost:8001/ws
```

### 方式二：本地開發

```bash
# 1. 建立虛擬環境
python -m venv .venv && source .venv/bin/activate

# 2. 安裝依賴（使用 pyproject.toml）
pip install -e ".[dev]"

# 3. 配置環境
cp .env.example .env

# 4. 啟動
streamlit run app.py
# 或使用便捷腳本：./start.sh
```

### 方式三：含監控部署

```bash
docker compose --profile monitoring up -d
# Grafana：http://localhost:3000
# Prometheus：http://localhost:9090
```

---

## 📁 專案結構

```
StocksX_V0/
├── app.py                              # 🏠 主頁儀表板
├── pyproject.toml                      # ⚙️ PEP 621 現代打包 & 工具配置
├── requirements.txt                    # 📦 核心依賴
├── requirements-dev.txt                # 🛠️ 開發依賴
├── Dockerfile                          # 🐳 多階段構建
├── docker-compose.yml                  # 🐳 Docker 編排（含監控 profile）
├── .dockerignore                       # 🐳 構建優化
├── .env.example                        # 🔐 環境變數模板
├── Makefile                            # 🔨 開發快捷命令
├── start.sh                            # 🚀 Unix 啟動腳本
├── pages/                              # 📱 Streamlit 多頁應用
│   ├── 1_🔐_登入.py                    #   用戶認證
│   ├── 2_₿_加密回測.py                #   加密貨幣回測
│   ├── 2_🏛️_傳統回測.py               #   美股/台股/ETF
│   ├── 3_📜_歷史.py                    #   歷史記錄 & 對比
│   ├── 4_🛠️_管理.py                   #   管理後台
│   ├── 5_📡_交易監控.py                #   策略訂閱監控
│   ├── 6_📰_新聞.py                    #   RSS 新聞聚合
│   ├── 7_🏥_健康檢查.py                #   系統健康監控
│   ├── 8_⚡_即時監控.py                #   WebSocket 即時
│   ├── 9_🧠_AI 策略.py                 #   AI 情緒分析
│   ├── 10_📊_策略回测对比.py            #   多策略對比
│   └── 11_🤖_自動交易.py               #   自動交易配置
├── src/
│   ├── core/                           # 🏗️ 核心架構
│   │   ├── orchestrator.py             #   統一編排層
│   │   ├── middleware.py               #   中間件管道
│   │   ├── cache_manager.py            #   快取管理
│   │   ├── repository.py               #   Repository Pattern
│   │   ├── container.py                #   DI 容器
│   │   ├── config.py                   #   配置管理
│   │   ├── provider.py                 #   數據源抽象
│   │   ├── pipeline.py                 #   數據清洗管道
│   │   ├── signals.py                  #   信號系統
│   │   ├── registry.py                 #   策略註冊中心
│   │   ├── backtest.py                 #   回測引擎
│   │   ├── adapters.py                 #   Provider 實現
│   │   ├── alerts.py                   #   告警系統
│   │   ├── tasks.py                    #   後台任務隊列
│   │   └── walk_forward.py             #   Walk-Forward 分析
│   ├── auth/                           # 🔐 用戶認證（JWT + PBKDF2）
│   ├── backtest/                       # 💹 回測引擎 & 策略庫
│   │   ├── engine.py                   #   主回測引擎
│   │   ├── engine_vec.py               #   向量化引擎
│   │   ├── strategies.py               #   策略函數庫
│   │   ├── indicators.py               #   技術指標
│   │   ├── position_sizing.py          #   倉位管理
│   │   └── walk_forward.py             #   Walk-Forward
│   ├── data/                           # 📡 數據源整合
│   │   ├── sources/                    #   數據來源（CCXT / Yahoo / API Hub）
│   │   ├── crypto/                     #   加密貨幣服務
│   │   ├── traditional/                #   傳統市場服務
│   │   ├── storage/                    #   存儲抽象
│   │   └── models.py                   #   數據模型
│   ├── strategies/                     # 🧠 進階策略
│   │   ├── ml_strategies/              #   ML 策略（LSTM / 配對交易）
│   │   ├── nlp_strategies/             #   NLP 情緒分析
│   │   ├── rl_strategies/              #   強化學習交易
│   │   └── quant_strategies/           #   量化多因子 / 配對交易
│   ├── trading/                        # 🤖 自動交易引擎
│   │   ├── auto_trader.py              #   自動交易主邏輯
│   │   ├── executor.py                 #   訂單執行
│   │   ├── risk_manager.py             #   風控管理
│   │   └── circuit_breaker.py          #   熔斷機制
│   ├── utils/                          # 🔧 工具集
│   │   ├── logging_config.py           #   結構化日誌
│   │   ├── cache.py                    #   快取工具
│   │   ├── risk.py                     #   風險計算
│   │   ├── portfolio.py                #   投資組合分析
│   │   └── health_check.py             #   健康檢查
│   ├── ai/                             # 🤖 AI 整合（DashScope / Qwen）
│   ├── notify/                         # 📬 推播通知（Bark）
│   └── ui_*.py                         # 🎨 UI 組件
├── tests/                              # 🧪 pytest 測試
│   ├── test_core/                      #   核心模組測試
│   └── conftest.py                     #   測試配置
├── .github/
│   ├── workflows/ci.yml                # 🔄 CI/CD（Lint + Test + Docker）
│   └── dependabot.yml                  # 🔄 自動依賴更新
└── .pre-commit-config.yaml             # 🔒 Pre-commit hooks
```

---

## ⚙️ 配置

### 環境變數 (.env)

| 變數 | 說明 | 預設值 | 必填 |
|------|------|--------|:---:|
| `SECRET_KEY` | JWT 簽名密鑰 | — | ✅ |
| `ADMIN_PASSWORD` | 管理員密碼 | 自動生成 | ✅ |
| `DATABASE_URL` | 資料庫連接 | `sqlite:///data/stocksx.db` | |
| `REDIS_URL` | Redis 連接 | `redis://localhost:6379/0` | |
| `LOG_LEVEL` | 日誌等級 | `INFO` | |
| `BARK_KEY` | iOS Bark 推播 | — | |
| `BINANCE_API_KEY` | 幣安 API Key | — | |
| `DASHSCOPE_API_KEY` | DashScope AI Key | — | |

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/health` | GET | 系統健康檢查 |
| `/api/v1/health/detailed` | GET | 詳細健康狀態 |
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

- 🔒 **密碼** — PBKDF2-SHA256（100,000 iterations）+ 隨機 salt
- 🔑 **Session** — JWT 令牌、1 小時超時
- 🛡️ **限流** — 令牌桶演算法、登入鎖定機制
- 📝 **審計** — 完整登入日誌
- 🔍 **CI** — bandit 靜態安全分析 + safety 依賴漏洞掃描
- 🐳 **Docker** — 非 root 使用者運行、tini init 系統
- 🔄 **Dependabot** — 自動依賴安全更新

---

## 🛠️ 開發指南

```bash
# 安裝開發依賴（使用 pyproject.toml）
pip install -e ".[dev]"

# 代碼檢查
ruff check src/ pages/ app.py tests/
ruff format src/ pages/ app.py tests/

# 運行測試
pytest tests/ -v --cov=src --cov-report=term-missing

# 安全掃描
bandit -r src/ -ll

# Pre-commit（首次）
pre-commit install
```

**提交規範：** `feat:` · `fix:` · `docs:` · `refactor:` · `test:` · `chore:`

---

## 🚢 部署指南

### Docker Compose（推薦）

```bash
# 基本部署
docker compose up -d

# 含監控（Prometheus + Grafana）
docker compose --profile monitoring up -d

# 查看日誌
docker compose logs -f app

# 更新部署
docker compose pull && docker compose up -d --remove-orphans
```

### 生產環境建議

1. **設定固定 SECRET_KEY**：`python -c "import secrets; print(secrets.token_hex(32))"`
2. **啟用 HTTPS**：使用 Nginx/Caddy 反向代理
3. **配置 Redis 持久化**：預設已啟用 AOF
4. **設定監控告警**：`docker compose --profile monitoring up -d`
5. **定期備份**：備份 `volumes: app_data`
6. **啟用 Dependabot**：已配置自動依賴更新

---

## 📝 更新日誌

### v5.3.0 (2026-03-20)
- 📦 **現代化打包** — `pyproject.toml`（PEP 621），支持 `pip install -e ".[dev]"`
- 🔄 **Dependabot** — 自動依賴安全更新（pip / GitHub Actions / Docker）
- 🐳 **Docker 優化** — `.dockerignore`、更好的緩存層、安全加固
- 🚀 **CI/CD 增強** — Docker 構建推送 GHCR、Python 3.13 支援
- 🔧 **Unix 腳本** — `start.sh` 替代 Windows-only `start_auto_trading.bat`
- 📖 **README 重構** — 六層分離架構圖、設計模式表、更清晰的結構

### v5.2.0 (2026-03-20)
- 🏗️ **架構優化** — 新增 `requirements-dev.txt`、完善開發工具鏈
- 📖 **README 現代化** — Mermaid 架構圖、更清晰的結構
- 🔧 **代碼品質** — 改進錯誤處理、結構化日誌
- 🐳 **Docker 優化** — 更好的 healthcheck、非 root 運行

### v5.1.0 (2026-03-20)
- 🏗️ **配置統一** — 消除 `src/config.py` 與 `src/core/config.py` 的重複 Settings 類
- 🚀 **CI/CD 增強** — bandit 安全掃描、mypy 類型檢查、GHCR 推送
- 🧪 **測試強化** — pytest-timeout、Python 3.10/3.11/3.12 矩陣測試

### v5.0.0 (2026-03-19)
- 🏗️ **核心架構重構** — `src/core/` 模組化設計
- ⚡ **Orchestrator** — 統一編排層，取代散落業務邏輯
- 🔄 **Middleware Pipeline** — 日誌、重試、限流中間件
- 💾 **CacheManager** — Redis / 記憶體快取管理
- 📦 **Repository Pattern** — 數據存取抽象

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
