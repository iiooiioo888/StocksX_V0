<div align="center">

# 📊 StocksX

**機構級跨市場回測與交易監控平台**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://github.com/iiooiioo888/StocksX_V0/pkgs/container)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[快速開始](#-快速開始) · [功能](#-核心功能) · [部署](#-部署) · [架構](#-技術架構) · [貢獻](#-貢獻)

---

<img src="https://img.shields.io/badge/策略數-15+-blue" alt="strategies"> <img src="https://img.shields.io/badge/交易所-11-orange" alt="exchanges"> <img src="https://img.shields.io/badge/市場-加密%20%7C%20美股%20%7C%20台股%20%7C%20ETF%20%7C%20期貨-green" alt="markets">

</div>

---

## 🎯 核心功能

### 📈 回測引擎

| 特性 | 說明 |
|------|------|
| **多市場** | 加密貨幣（11 交易所）、美股、台股、ETF、期貨、指數 |
| **15+ 策略** | SMA/EMA 交叉、MACD、RSI、布林帶、Supertrend、一目均衡表… |
| **參數優化** | 網格搜索 + Walk-Forward Analysis，避免過擬合 |
| **手續費模擬** | 31 個交易所真實費率，含滑點模擬 |
| **槓桿與風控** | 可調槓桿、止盈止損、爆倉模擬 |

### ⚡ 即時監控

- **WebSocket 推送** — 幣安真實數據，1 秒更新
- **策略訂閱** — 多交易對 × 多策略組合
- **自動交易** — 根據信號自動開平倉，含風控管理
- **持倉追蹤** — 未實現 P&L 即時損益

### 🧠 AI 增強

- **情緒分析** — Fear & Greed Index、社群情緒
- **鏈上數據** — 巨鯨動向、交易所流量
- **LLM 整合** — 通義千問 (Qwen) 策略建議

### 📊 專業圖表

- **K 線圖** — 蠟燭圖、成交量、技術指標疊加
- **深度圖** — 訂單簿累積曲線
- **權益曲線** — 累積報酬、收益分佈圖
- **策略對比** — 多策略雷達圖對比

---

## 🚀 快速開始

```bash
# 1. 克隆專案
git clone https://github.com/iiooiioo888/StocksX_V0.git
cd StocksX_V0

# 2. 建立虛擬環境
python -m venv .venv && source .venv/bin/activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 配置環境變數
cp .env.example .env
# ⚠️ 編輯 .env，至少填入 SECRET_KEY

# 5. 啟動
streamlit run app.py
```

🌐 開啟 `http://localhost:8501`

### Docker 一鍵部署

```bash
cp .env.example .env
# 編輯 .env

# 啟動核心服務
docker compose up -d

# 啟動含監控（Prometheus + Grafana）
docker compose --profile monitoring up -d
```

---

## 📁 專案結構

```
StocksX_V0/
├── app.py                        # 主頁 — 儀表板
├── pages/                        # Streamlit 多頁應用
│   ├── 1_🔐_登入.py              # 用戶認證
│   ├── 2_₿_加密回測.py          # 加密貨幣回測（11 交易所）
│   ├── 2_🏛️_傳統回測.py        # 美股/台股/ETF 回測
│   ├── 3_📜_歷史.py              # 歷史記錄 & 對比
│   ├── 4_🛠️_管理.py             # 管理後台
│   ├── 5_📡_交易監控.py          # 策略訂閱 & 自動交易
│   ├── 6_📰_新聞.py              # 市場新聞
│   ├── 7_🏥_健康檢查.py          # 系統健康
│   ├── 8_⚡_即時監控.py          # WebSocket 即時監控
│   ├── 9_🧠_AI 策略.py           # AI 策略建議
│   ├── 10_📊_策略回测对比.py      # 多策略對比
│   └── 11_🤖_自動交易.py         # 自動交易控制
├── src/
│   ├── auth/                     # 用戶認證 (bcrypt + JWT)
│   ├── backtest/                 # 回測引擎 & 策略庫
│   │   ├── engine.py             # 核心回測邏輯
│   │   ├── strategies.py         # 15+ 策略實現
│   │   ├── optimizer.py          # 參數網格搜索
│   │   └── walk_forward.py       # Walk-Forward 分析
│   ├── data/                     # 數據層
│   │   ├── crypto/               # 加密貨幣 (CCXT)
│   │   ├── traditional/          # 傳統市場 (yfinance)
│   │   ├── sources/              # API Hub (CoinGecko, Fear&Greed…)
│   │   └── service.py            # 統一數據服務（延遲初始化）
│   ├── strategies/               # 進階策略模組
│   │   ├── ml_strategies/        # 機器學習策略 (LSTM, 特徵工程)
│   │   ├── rl_strategies/        # 強化學習策略 (DQN)
│   │   ├── nlp_strategies/       # NLP 情緒分析
│   │   └── quant_strategies/     # 量化策略 (多因子, 配對交易)
│   ├── trading/                  # 自動交易
│   ├── ai/                       # AI / LLM 整合
│   ├── notify/                   # 推播通知 (Bark)
│   ├── utils/                    # 工具 (日誌, 限流, 健康檢查)
│   └── ui_modern.py              # 現代化 UI 元件庫
├── docker-compose.yml            # 多服務編排
├── Dockerfile                    # 多階段構建
└── pyproject.toml                # Ruff lint 配置
```

---

## 📊 策略庫

<details>
<summary><b>趨勢策略 (6)</b></summary>

| 策略 | 指標 | 預設參數 |
|------|------|----------|
| 雙均線交叉 | SMA 快/慢線 | fast=10, slow=30 |
| EMA 交叉 | EMA 快/慢線 | fast=12, slow=26 |
| MACD 交叉 | MACD / Signal | fast=12, slow=26, signal=9 |
| ADX 趨勢 | ADX + DI | period=14, threshold=25 |
| 超級趨勢 | ATR 通道 | period=10, multiplier=3.0 |
| 拋物線 SAR | SAR 點 | af=0.02, step=0.02, max=0.20 |
</details>

<details>
<summary><b>擺盪策略 (5)</b></summary>

| 策略 | 指標 | 預設參數 |
|------|------|----------|
| RSI | 相對強弱 | period=14, 30/70 |
| KD 隨機指標 | K/D 線 | k=14, d=3, 20/80 |
| 威廉指標 | %R | period=14, -80/-20 |
| 布林帶 | 通道 | period=20, std=2.0 |
| 一目均衡表 | 轉換/基準/雲 | 9, 26, 52 |
</details>

<details>
<summary><b>突破 & 均值回歸 (4)</b></summary>

| 策略 | 說明 | 預設參數 |
|------|------|----------|
| 唐奇安通道 | 通道突破 | period=20 |
| 雙推力 | 區間突破 | period=4, k1=0.5, k2=0.5 |
| VWAP 回歸 | 偏離回歸 | period=20, threshold=2.0 |
| 買入持有 | 基準 | — |
</details>

---

## 📈 績效指標

回測結果包含完整的風險調整指標：

| 類別 | 指標 |
|------|------|
| **報酬** | 總報酬、年化報酬、平均報酬 |
| **風險** | 最大回撤、標準差、VaR |
| **風險調整** | Sharpe、Sortino、Calmar |
| **交易統計** | 勝率、利潤因子、Omega Ratio、Tail Ratio |
| **連續統計** | 最大連勝、最大連虧 |

---

## 🔧 技術架構

| 層級 | 技術 |
|------|------|
| **UI** | Streamlit 1.32+ |
| **圖表** | Plotly 5.18+ |
| **數據** | CCXT (加密)、yfinance (傳統)、CoinGecko |
| **即時** | FastAPI + WebSocket |
| **任務** | Celery + Redis |
| **儲存** | SQLite / PostgreSQL |
| **認證** | bcrypt + JWT |
| **監控** | Prometheus + Grafana |
| **部署** | Docker + Docker Compose |

---

## 🔐 安全

- ✅ 密碼 bcrypt 哈希 + JWT 認證
- ✅ API 限流（令牌桶演算法）
- ✅ 環境變數管理（`.env` 不進版控）
- ✅ `.gitignore` 防止敏感文件洩漏
- ✅ Docker 非 root 使用者執行
- ✅ 健康檢查端點

---

## 🚢 部署

### 開發環境

```bash
streamlit run app.py
```

### 生產環境 (Docker)

```bash
# 1. 複製並配置環境變數
cp .env.example .env

# 2. 啟動
docker compose up -d

# 3. 訪問
# App:  http://localhost:8501
# WS:   http://localhost:8001
# Redis: localhost:6379
```

### 生產環境 (完整)

```bash
# 包含 Prometheus + Grafana 監控
docker compose --profile monitoring up -d
```

---

## 🧪 開發

```bash
# 安裝開發依賴
pip install -r requirements.txt

# Lint
ruff check src/ pages/

# 格式化
ruff format src/ pages/
```

---

## 📄 授權

[MIT License](LICENSE)

---

## ⚠️ 免責聲明

> 本軟體僅供學習與研究，不構成投資建議。
> 回測結果基於歷史數據，不代表未來表現。交易涉及風險，請謹慎評估。

---

<div align="center">

**Made with ❤️ by StocksX Team**

</div>
