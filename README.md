<div align="center">

<img src="https://github.com/iiooiioo888/StocksX_V0/blob/main/assets/logo.png" alt="StocksX" width="120" />

# StocksX

### 機構級量化交易與投資組合管理平台

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![CI/CD](https://github.com/iiooiioo888/StocksX_V0/actions/workflows/ci.yml/badge.svg)](https://github.com/iiooiioo888/StocksX_V0/actions)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)

**18 種量化策略 · 多市場回測 · 投資組合優化 · 即時監控 · AI 驅動**

[快速開始](#-快速開始) · [功能](#-核心功能) · [架構](#️-技術架構) · [部署](#-部署)

</div>

---

## ⚡ 30 秒啟動

```bash
git clone https://github.com/iiooiioo888/StocksX_V0.git && cd StocksX_V0
cp .env.example .env && docker compose up -d
# 👉 http://localhost:8501
```

---

## 🎯 核心功能

### 📊 18 種量化策略

| 類別 | 策略 | 適用場景 |
|:---:|------|------|
| 📈 **趨勢** | 雙均線 · EMA交叉 · MACD · ADX · 超級趨勢 · 拋物線 SAR | 趨勢明確的市場 |
| 🔀 **擺盪** | RSI · KD · 威廉指標 · 布林帶 · 一目均衡表 | 區間震盪市場 |
| 💥 **突破** | 唐奇安通道 · 雙推力 · VWAP 回歸 | 波動率擴張階段 |
| 📐 **均值回歸** | Z-Score 回歸 · Keltner Channel | 超買超賣反轉 |
| 📏 **動量** | ROC 變動率 | 強勢品種追蹤 |
| 🧠 **AI/ML** | LSTM · 情緒分析 · 多因子 · 配對交易 · 強化學習 | 複雜市場環境 |

> 💡 所有核心策略已通過 **NumPy 向量化優化**，回測速度提升 10-100x。

### 🏗️ 投資組合優化（v6.0 新增）

| 方法 | 說明 | 適用 |
|------|------|------|
| **Markowitz 均值-方差** | 最大夏普比率最優配置 | 追求最佳風險調整收益 |
| **風險平價** | 各資產風險貢獻相等 | 穩健型資產配置 |
| **有效前沿** | 風險-收益帕累托最優 | 視覺化配置選擇 |
| **VaR / CVaR** | 風險價值與條件風險價值 | 風險度量與監控 |
| **最大回撤分析** | 回撤深度與恢復時間 | 尾部風險評估 |

### 🔍 市場狀態檢測（v6.0 新增）

- **牛市 / 熊市 / 震盪** 自動識別
- 基於趨勢強度、波動率特徵、均線系統
- 各 regime 的收益率與波動率統計
- **波動率建模**：EWMA 波動率、波動率 regime、波動率趨勢

### 🌐 多市場支援

| 市場 | 數據源 | 覆蓋範圍 |
|------|--------|---------|
| ₿ 加密貨幣 | CCXT (11 交易所) | 現貨 + 永續合約，500+ 交易對 |
| 🇺🇸 美股 | Yahoo Finance | AAPL, MSFT, NVDA, SPY 等 |
| 🇹🇼 台股 | Yahoo Finance | 2330.TW, 2317.TW 等 |
| 📈 ETF | Yahoo Finance | SPY, QQQ, GLD, TLT 等 |

### ⚡ 即時監控

- WebSocket 幣安即時推送
- 策略信號訂閱與持倉追蹤
- 即時 P&L 監控
- 自動重連與心跳保活

### 🤖 AI 增強

- FinBERT 市場情緒分析
- LSTM 價格預測
- DashScope / Qwen AI 整合
- 恐懼貪婪指數 + VIX 波動率

---

## 🏗️ 技術架構

### 分層架構（六層分離）

```
┌─────────────────────────────────────────────────────────┐
│  🎨 表現層 (Presentation)                                │
│  Streamlit Dashboard │ FastAPI REST+WS │ Plotly 圖表     │
├─────────────────────────────────────────────────────────┤
│  ⚙️ 應用層 (Application)                                 │
│  Orchestrator 編排 │ StrategyRegistry │ SignalBus │ Auth │
├─────────────────────────────────────────────────────────┤
│  📐 領域層 (Domain)                                      │
│  回測引擎(向量化) │ 18+策略 │ 風控 │ 投資組合優化          │
├─────────────────────────────────────────────────────────┤
│  🧩 基礎設施層 (Infrastructure)                          │
│  DI容器 │ 中間件管道 │ 快取管理 │ Repository │ 任務隊列    │
├─────────────────────────────────────────────────────────┤
│  📡 數據層 (Data)                                        │
│  CCXT Gateway │ Yahoo Finance │ CoinGecko │ WebSocket    │
├─────────────────────────────────────────────────────────┤
│  💾 持久化層 (Persistence)                                │
│  SQLite │ Redis 7 │ PostgreSQL (可選)                    │
└─────────────────────────────────────────────────────────┘
```

### 設計模式

| 模式 | 實現 | 說明 |
|:---:|------|------|
| **Orchestrator** | `src/core/orchestrator.py` | 統一業務入口，屏蔽複雜度 |
| **Registry** | `src/core/registry.py` | `@register_strategy` 裝飾器自動註冊 |
| **Repository** | `src/core/repository.py` | 數據存取抽象，SQLite ↔ PostgreSQL |
| **DI Container** | `src/core/container.py` | 輕量依賴注入，便於測試 |
| **Middleware Pipeline** | `src/core/middleware.py` | 日誌/重試/限流管道化 |
| **Provider Composite** | `src/core/adapters.py` | 多數據源組合，自動故障轉移 |

### 數據流

```
用戶請求 → Orchestrator → Provider(數據源)
    ↓                        ↓
Pipeline(清洗)  ←  原始 OHLCV
    ↓
Registry(策略信號) → BacktestEngine(回測)
    ↓
SignalBus(即時推送) → 用戶
```

### 技術棧

| 層級 | 技術 |
|------|------|
| 前端 | Streamlit · Plotly · Glassmorphism CSS |
| API | FastAPI · Uvicorn · WebSockets |
| 數據 | Pandas · NumPy · yfinance · CCXT · CoinGecko |
| AI/ML | scikit-learn · DashScope |
| 存儲 | SQLite · Redis 7 · SQLAlchemy |
| 任務 | Celery · Redis Broker |
| 監控 | Prometheus · Grafana · psutil |
| 打包 | pyproject.toml (PEP 621) |
| DevOps | Docker · GitHub Actions · Dependabot |
| 品質 | Ruff · pytest · bandit · mypy · pre-commit |

---

## 📁 專案結構

```
StocksX_V0/
├── app.py                          # 主頁儀表板
├── pyproject.toml                  # PEP 621 現代打包
├── requirements.txt                # 核心依賴
├── Dockerfile                      # 多階段構建
├── docker-compose.yml              # Docker 編排
├── .env.example                    # 環境變數模板
├── Makefile                        # 開發快捷命令
│
├── pages/                          # Streamlit 多頁應用
│   ├── 1_🔐_登入.py
│   ├── 2_₿_加密回測.py
│   ├── 2_🏛️_傳統回測.py
│   ├── 5_📡_交易監控.py
│   ├── 9_🧠_AI 策略.py
│   ├── 10_📊_策略回测对比.py
│   ├── 13_📈_组合优化.py            # v6.0 新增
│   └── ...
│
├── src/
│   ├── core/                       # 核心架構
│   │   ├── orchestrator.py         # 統一編排層
│   │   ├── middleware.py           # 中間件管道
│   │   ├── cache_manager.py        # 快取管理
│   │   ├── repository.py           # Repository Pattern
│   │   ├── container.py            # DI 容器
│   │   └── ...
│   │
│   ├── backtest/                   # 回測引擎 & 策略
│   │   ├── strategies.py           # 18 種策略 (NumPy 向量化)
│   │   ├── engine.py               # 回測引擎
│   │   ├── indicators.py           # 技術指標
│   │   └── ...
│   │
│   ├── strategies/                 # 進階策略
│   │   ├── regime_detection.py     # 市場狀態檢測 (v6.0)
│   │   ├── ml_strategies/          # LSTM / 配對交易
│   │   ├── nlp_strategies/         # NLP 情緒分析
│   │   └── rl_strategies/          # 強化學習
│   │
│   ├── utils/
│   │   ├── portfolio_optimizer.py  # 投資組合優化 (v6.0)
│   │   ├── risk.py                 # 風險計算
│   │   └── ...
│   │
│   ├── data/                       # 數據源
│   │   ├── sources/                # CCXT / Yahoo / API Hub
│   │   ├── crypto/                 # 加密貨幣服務
│   │   └── traditional/            # 傳統市場
│   │
│   └── trading/                    # 自動交易引擎
│
├── tests/                          # pytest 測試
└── .github/workflows/ci.yml        # CI/CD
```

---

## 🚀 快速開始

### Docker（推薦）

```bash
git clone https://github.com/iiooiioo888/StocksX_V0.git
cd StocksX_V0
cp .env.example .env
# 編輯 .env 設定 SECRET_KEY 和 ADMIN_PASSWORD
docker compose up -d
# 主應用: http://localhost:8501
# WebSocket: ws://localhost:8001/ws
```

### 本地開發

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
streamlit run app.py
```

### 含監控

```bash
docker compose --profile monitoring up -d
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```

---

## ⚙️ 配置

### 環境變數

| 變數 | 說明 | 必填 |
|------|------|:---:|
| `SECRET_KEY` | JWT 簽名密鑰 | ✅ |
| `ADMIN_PASSWORD` | 管理員密碼（不設定則自動生成） | ✅ |
| `DATABASE_URL` | 資料庫連接 | |
| `REDIS_URL` | Redis 連接 | |
| `CORS_ORIGINS` | CORS 允許的來源 | |
| `BINANCE_API_KEY` | 幣安 API | |
| `DASHSCOPE_API_KEY` | DashScope AI | |

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/health` | GET | 系統健康檢查 |
| `/ws` | WebSocket | 即時行情推送 |

---

## 📊 績效指標

| 類別 | 指標 |
|------|------|
| 報酬 | 總報酬、年化報酬、平均報酬 |
| 風險 | 最大回撤、VaR (95%)、CVaR |
| 風險調整 | Sharpe、Sortino、Calmar |
| 交易 | 勝率、利潤因子、最大連勝/連敗 |
| 進階 | Omega Ratio、Tail Ratio |
| 組合 | 投資組合權重、風險貢獻度 |

---

## 🔐 安全

- 密碼：PBKDF2-SHA256 + 隨機 salt（無硬編碼預設值）
- Session：JWT 令牌、超時機制
- CORS：環境變數白名單配置
- 限流：令牌桶演算法
- CI：bandit 安全掃描 + safety 依賴漏洞檢查
- Docker：非 root 使用者 + tini init

---

## 🛠️ 開發

```bash
# 安裝
pip install -e ".[dev]"

# 代碼檢查
ruff check src/ pages/ app.py tests/
ruff format src/ pages/ app.py tests/

# 測試
pytest tests/ -v --cov=src --cov-report=term-missing

# 安全掃描
bandit -r src/ -ll
```

---

## 📝 更新日誌

### v6.0.0 (2026-03-20)
- 🔒 **安全加固** — 消除硬編碼管理員密碼、CORS 白名單、環境變數隔離
- ⚡ **策略引擎向量化** — NumPy 優化全部核心策略，回測提速 10-100x
- 📊 **投資組合優化** — Markowitz 均值-方差、風險平價、有效前沿
- 🔍 **市場狀態檢測** — 牛/熊/震盪自動識別 + 波動率建模
- 📈 **新增策略** — Z-Score 均值回歸、ROC 動量、Keltner Channel
- 📐 **風險分析** — VaR、CVaR、最大回撤分析
- 📖 **README 全面重構** — 更現代化、更有邏輯的技術文檔

<details>
<summary>📜 更早版本</summary>

- **v5.3.0** — pyproject.toml · Dependabot · Docker 優化 · CI/CD
- **v5.2.0** — 架構優化 · README 現代化 · 結構化日誌
- **v5.1.0** — 配置統一 · CI/CD 增強
- **v5.0.0** — 核心架構重構 · Orchestrator · Middleware
- **v4.0.0** — CCXT / Yahoo Finance · WebSocket
- **v3.0.0** — FastAPI · Celery 任務隊列

</details>

---

## 📄 授權

[MIT License](LICENSE)

---

<div align="center">

⚠️ **本軟體僅供學習與研究，不構成投資建議。**

回測結果基於歷史數據，不代表未來表現。

**Made with ❤️ by StocksX Team** · © 2024–2026

</div>
