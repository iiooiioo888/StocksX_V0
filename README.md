<div align="center">

# 📊 StocksX

**機構級回測與交易監控平台**

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://github.com/iiooiioo888/StocksX_V0)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/iiooiioo888/StocksX_V0/actions/workflows/ci.yml/badge.svg)](https://github.com/iiooiioo888/StocksX_V0/actions)

跨市場回測 · 15+ 專業策略 · 即時監控 · WebSocket 推送 · AI 情緒分析

[快速開始](#-快速開始) · [策略列表](#-策略庫) · [部署指南](#-部署) · [貢獻指南](CONTRIBUTING.md)

</div>

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

## 🏗️ 技術棧

<div align="center">

| 層級 | 技術 |
|:----:|------|
| **前端** | Streamlit · Plotly.js · Glassmorphism CSS |
| **後端** | Python 3.10+ · FastAPI · SQLite / PostgreSQL |
| **即時** | WebSocket · CCXT · Binance API |
| **數據** | Pandas · NumPy · yfinance · CoinGecko |
| **AI/ML** | scikit-learn · TensorFlow · FinBERT · Gymnasium |
| **基礎設施** | Docker · Redis · Celery · Prometheus · Grafana |
| **品質** | Ruff · pytest · GitHub Actions · pre-commit |

</div>

---

## 🚀 部署

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

## 🤝 貢獻

歡迎貢獻！請閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
# 開發環境
pip install -r requirements-dev.txt
pre-commit install

# 程式碼檢查
ruff check src/ app.py pages/
ruff format src/ app.py pages/

# 測試
pytest tests/ -v
```

---

## 📄 授權

[MIT License](LICENSE)

---

## ⚠️ 免責聲明

**本軟體僅供學習與研究，不構成投資建議。**

回測結果基於歷史數據，不代表未來表現。交易涉及風險，請謹慎評估。

---

<div align="center">

**Made with ❤️ by StocksX Team**

[⬆ 回到頂部](#-stocksx)

</div>
