<div align="center">

<img src="https://github.com/iiooiioo888/StocksX_V0/blob/main/assets/logo.png" alt="StocksX Logo" width="120" />

# 📊 StocksX

### 機構級回測與交易監控平台

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://github.com/iiooiioo888/StocksX_V0)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/iiooiioo888/StocksX_V0/actions/workflows/ci.yml/badge.svg)](https://github.com/iiooiioo888/StocksX_V0/actions)

跨市場回測 · 15+ 專業策略 · 即時監控 · WebSocket 推送 · AI 情緒分析

</div>

---

StocksX 是一個開源的量化交易回測與即時監控平台，支援加密貨幣、美股、台股、ETF 與期貨。整合 11 個交易所的真實數據、15+ 經典與機器學習策略、WebSocket 即時推送以及 AI 情緒分析，讓你以機構級的標準打造與驗證交易系統。從策略開發、回測驗證到即時監控的全流程皆可在單一平台完成。

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

## 📸 截圖 / Demo

> **[截圖待添加]**
>
> 請在此處加入平台實際操作截圖或 GIF 動畫，展示：
> - 回測結果儀表板
> - 即時監控介面
> - K 線圖與技術指標
> - AI 情緒分析面板

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

```
┌─────────────────────────────────────────────────────────────────┐
│                        使用者層 (User Layer)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ 回測頁面  │  │ 監控頁面  │  │ AI 分析  │  │ 歷史記錄 & 對比  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────┘ │
└───────┼──────────────┼──────────────┼────────────────┼──────────┘
        │              │              │                │
┌───────▼──────────────▼──────────────▼────────────────▼──────────┐
│                      前端層 (Frontend)                            │
│         Streamlit · Plotly.js · Glassmorphism 主題               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       API 層 (Backend)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  FastAPI      │  │  WebSocket   │  │  Celery 任務隊列      │  │
│  │  REST API     │  │  即時推送     │  │  (非同步回測)         │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘  │
└─────────┼─────────────────┼───────────────────────┼─────────────┘
          │                 │                       │
┌─────────▼─────────────────▼───────────────────────▼─────────────┐
│                      核心引擎層 (Core Engine)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  回測引擎     │  │  策略引擎     │  │  交易引擎 (自動下單)   │  │
│  │  14+ 策略     │  │  參數優化     │  │  風控模組             │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  ML / LSTM    │  │  NLP 情緒    │  │  強化學習 (RL)        │  │
│  │  預測模型     │  │  FinBERT     │  │  Gymnasium            │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      數據層 (Data Layer)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  CCXT         │  │  yfinance    │  │  CoinGecko / 鏈上     │  │
│  │  (11 交易所)   │  │  (美股/台股)  │  │  (巨鯨/流量)          │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │  API Hub      │  │  Redis 快取  │                              │
│  │  (限流+重試)   │  │  (TTL 緩存)  │                              │
│  └──────────────┘  └──────────────┘                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┘
│                     基礎設施層 (Infrastructure)                    │
│      Docker · Prometheus · Grafana · GitHub Actions CI/CD        │
└─────────────────────────────────────────────────────────────────┘
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
| **品質** | Ruff · pytest · GitHub Actions · pre-commit |

---

## 📁 專案結構

```
StocksX_V0/
├── app.py                       # 主頁儀表板
├── pages/                       # Streamlit 多頁應用
│   ├── 1_🔐_登入.py              # 用戶認證
│   ├── 2_₿_加密回測.py           # 加密貨幣回測
│   ├── 2_🏛️_傳統回測.py         # 美股 / 台股 / ETF
│   ├── 3_📜_歷史.py              # 歷史記錄 & 對比
│   ├── 5_📡_監控.py              # 策略訂閱監控
│   ├── 8_⚡_即時監控.py          # WebSocket 即時
│   └── 9_🧠_AI 策略.py           # AI 情緒分析
├── src/
│   ├── auth/                    # 用戶認證 & SQLite
│   ├── backtest/                # 回測引擎 & 策略庫
│   ├── data/                    # 數據源整合
│   │   ├── sources/             # API Hub（快取 + 限流）
│   │   ├── crypto/              # CCXT 加密數據
│   │   └── traditional/         # Yahoo Finance
│   ├── strategies/              # 進階策略
│   │   ├── ml_strategies/       # LSTM / 機器學習
│   │   ├── nlp_strategies/      # NLP 情緒分析
│   │   ├── quant_strategies/    # 多因子 / 配對交易
│   │   └── rl_strategies/       # 強化學習
│   ├── trading/                 # 自動交易引擎
│   ├── utils/                   # 工具（快取 / 日誌 / 限流）
│   ├── websocket_server.py      # FastAPI WebSocket
│   └── ui_modern.py             # Glassmorphism 主題
├── tests/                       # pytest 測試
├── docker-compose.yml           # Docker 編排
├── Dockerfile                   # 多階段構建
└── .github/workflows/ci.yml    # CI/CD 自動化
```

---

## ⚙️ API & 配置說明

### 環境變數 (.env)

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `SECRET_KEY` | JWT 簽名密鑰（**必填**） | — |
| `ADMIN_PASSWORD` | 管理員密碼（**必填**） | — |
| `DATABASE_URL` | 資料庫連接字串 | `sqlite:///data/stocksx.db` |
| `REDIS_URL` | Redis 連接字串 | `redis://localhost:6379/0` |
| `LOG_LEVEL` | 日誌等級 | `INFO` |
| `STREAMLIT_SERVER_PORT` | Streamlit 連接埠 | `8501` |
| `WEBSOCKET_PORT` | WebSocket 連接埠 | `8001` |

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/health` | GET | 健康檢查 |
| `/ws` | WebSocket | 即時行情推送 |
| `/api/v1/backtest` | POST | 提交回測任務 |
| `/api/v1/strategies` | GET | 策略列表 |

---

## 🚀 部署指南

### Docker Compose 服務

| 服務 | 端口 | 說明 |
|------|------|------|
| `app` | 8501 | Streamlit 主應用 |
| `websocket` | 8001 | WebSocket 即時推送 |
| `redis` | 6379 | 快取 & 消息隊列 |
| `prometheus` | 9090 | 指標採集（選配） |
| `grafana` | 3000 | 監控面板（選配） |

```bash
# 基本服務
docker compose up -d

# 含 WebSocket + 監控
docker compose --profile websocket --profile monitoring up -d
```

<details>
<summary>🔧 生產環境手動部署</summary>

```bash
# 1. 環境
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. 配置
cp .env.example .env  # 設定 SECRET_KEY, ADMIN_PASSWORD

# 3. 啟動服務
celery -A src.tasks worker --loglevel=info &
uvicorn src.websocket_server:app --host 0.0.0.0 --port 8001 &
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

</details>

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

詳見 [SECURITY.md](SECURITY.md)

---

## 📝 更新日誌

### v4.2.0 (2026-03-19)
- ⚡ 記憶體快取層（API 響應 TTL）
- 🧪 pytest 測試體系（UserDB / 策略 / 快取）
- 🛠️ UI 共用元件庫（錯誤邊界 / 狀態卡片）
- 📊 資料庫查詢助手（減少重複程式碼）

### v4.1.0 (2026-03-19)
- 🔒 安全強化（.gitignore / Docker secrets）
- 📝 結構化日誌系統（取代 print()）
- 🚀 GitHub Actions CI/CD
- 🐳 Docker 最佳化（tini / Redis LRU）

<details>
<summary>📜 更早版本</summary>

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

# 測試
pytest tests/ -v
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
