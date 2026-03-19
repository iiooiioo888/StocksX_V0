# StocksX — 機構級專業回測與交易監控平台

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/iiooiioo888/StocksX_V0/actions/workflows/ci.yml/badge.svg)](https://github.com/iiooiioo888/StocksX_V0/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://github.com/iiooiioo888/StocksX_V0/pkgs/container)

## 📊 平台概覽

**StocksX** 是一個機構級的專業回測與交易監控平台，整合了：

- 🔍 **多市場回測** - 加密貨幣、美股、台股、ETF、期貨
- 📈 **15+ 專業策略** - 雙均線、MACD、RSI、布林帶等
- ⚡ **即時監控** - WebSocket 實時推送、自動交易
- 🤖 **AI 增強** - 情緒分析、鏈上數據、AI 預測
- 📊 **專業圖表** - Plotly 互動圖表、技術指標

---

## 🎯 核心功能

### 1. 回測系統

| 功能 | 說明 |
|------|------|
| **多市場支援** | 加密貨幣（11 個交易所）、美股、台股、ETF、期貨 |
| **15+ 專業策略** | 趨勢、擺盪、突破、均值回歸 |
| **參數優化** | 網格搜索、最佳化推薦 |
| **績效分析** | Sharpe、Sortino、Calmar、最大回撤 |
| **Walk-Forward** | 向前分析、避免過擬合 |

### 2. 即時監控

| 功能 | 說明 |
|------|------|
| **WebSocket 推送** | 幣安真實數據、1 秒更新 |
| **策略訂閱** | 多交易對 × 多策略組合 |
| **自動交易** | 根據信號自動開平倉 |
| **風險管理** | 停損/停利、倉位控制 |
| **持倉追蹤** | 未實現 P&L、即時損益 |

### 3. 專業圖表

| 圖表 | 說明 |
|------|------|
| **K 線圖** | 蠟燭圖、收盤價線、面積圖 |
| **技術指標** | SMA/EMA、MACD、RSI、布林帶 |
| **深度圖** | 真實訂單簿、買賣累積曲線 |
| **權益曲線** | 累積報酬、收益分佈 |
| **情緒儀表** | 恐懼貪婪、社群情緒、新聞情緒 |

### 4. 數據整合

| 數據源 | 說明 |
|--------|------|
| **CCXT** | 11 個加密交易所（Binance、OKX、Bybit 等） |
| **Yahoo Finance** | 美股、台股、ETF、期貨、指數 |
| **Blockchain.com** | BTC 鏈上數據、巨鯨動向 |
| **Alternative.me** | 恐懼貪婪指數 |
| **WebSocket** | 幣安即時推送（1 秒更新） |

---

## 🚀 快速開始

### 安裝依賴

```bash
# 克隆專案
git clone https://github.com/yourusername/StocksX.git
cd StocksX

# 安裝依賴
pip install -r requirements.txt
```

### 環境配置

```bash
# 複製環境變數範例
cp .env.example .env

# 編輯 .env（填入 API Key 等配置）
```

### 啟動應用

```bash
# 啟動 Streamlit
streamlit run app.py

# 訪問：http://localhost:8501
```

### 啟動 WebSocket（可選）

```bash
# 啟動幣安 WebSocket 服務
python -m src.websocket_binance

# WebSocket URL: ws://localhost:8001/ws
```

---

## 📁 專案結構

```
StocksX_V0/
├── app.py                          # 主頁（儀表板）
├── pages/
│   ├── 1_🔐_登入.py                 # 用戶登入
│   ├── 2_₿_加密回測.py              # 加密貨幣回測
│   ├── 2_🏛️_傳統回測.py            # 傳統市場回測
│   ├── 3_📜_歷史.py                 # 回測歷史
│   ├── 4_🛠️_管理.py                # 管理後台
│   ├── 5_📡_監控.py                 # 策略監控（優化版）
│   ├── 6_📰_新聞.py                 # 市場新聞
│   ├── 7_🏥_健康檢查.py             # 系統健康
│   └── 8_⚡_即時監控.py             # 即時監控（真實數據）
├── src/
│   ├── auth/
│   │   └── user_db.py              # 用戶資料庫
│   ├── backtest/
│   │   ├── engine.py               # 回測引擎
│   │   ├── strategies.py           # 策略庫（15+）
│   │   ├── optimizer.py            # 參數優化
│   │   └── fees.py                 # 手續費計算
│   ├── data/
│   │   ├── crypto/                 # 加密數據
│   │   ├── traditional/            # 傳統數據
│   │   ├── sources/                # 數據源（API Hub）
│   │   └── service.py              # 數據服務（真實 API）
│   ├── utils/
│   │   ├── logger.py               # 日誌系統
│   │   ├── rate_limiter.py         # API 限流
│   │   ├── health_check.py         # 健康檢查
│   │   └── ui_modern.py            # 現代化 UI
│   └── websocket_binance.py        # 幣安 WebSocket
├── requirements.txt                # 依賴配置
├── .env.example                    # 環境範例
└── README.md                       # 本文件
```

---

## 📊 頁面導覽

### 主頁（app.py）

- 🎯 **Hero Banner** - 平台介紹、統計數據
- 📊 **績效儀表板** - 累積報酬、收益分佈、熱門策略
- ⚡ **快捷操作** - 常用回測快捷鍵
- 📈 **市場行情** - 期貨報價、熱門標的、加密貨幣
- 🌡️ **情緒儀表板** - 恐懼貪婪、VIX、BTC 主導性

### 加密回測（pages/2_₿_加密回測.py）

- 📊 **11 個交易所** - Binance、OKX、Bybit、Gate.io 等
- 🧠 **15+ 策略** - 雙均線、MACD、RSI、布林帶等
- ⚙️ **參數管理** - 展開設定、儲存預設、快捷設定
- 📈 **結果展示** - K 線圖、權益曲線、績效表、交易明細

### 傳統回測（pages/2_🏛️_傳統回測.py）

- 📊 **多市場** - 美股、台股、ETF、期貨、指數
- 💰 **Yahoo Finance** - 真實市場數據
- 📈 **財報整合** - 營收、獲利、資產負債（VIP）

### 歷史記錄（pages/3_📜_歷史.py）

- 📋 **分頁/篩選/排序** - 策略、交易對、日期、報酬率
- 📊 **多筆對比** - 5 筆權益曲線對比、績效指標表格
- 📥 **匯出功能** - CSV、Excel、PDF

### 策略監控（pages/5_📡_監控.py）

- 📊 **我的訂閱** - 持倉詳情、即時損益、手動操作
- ➕ **新增訂閱** - 市場選擇、策略設定、資金配置
- 🤖 **自動策略** - 策略池、績效評估、風險管理

### 即時監控（pages/8_⚡_即時監控.py）

- 📊 **即時價格** - WebSocket 真實數據、1 秒更新
- 📈 **K 線圖表** - 真實 K 線、技術指標、互動圖表
- 🔔 **交易信號** - SMA 交叉、RSI 計算、信心度
- 💼 **持倉監控** - 即時損益、自動交易
- 📉 **深度圖** - 真實訂單簿、買賣累積
- 🔗 **鏈上數據** - 巨鯨動向、交易所流量
- 💭 **情緒分析** - 恐懼貪婪、社群情緒、新聞情緒

---

## 🎨 UI/UX 特色

### 現代化設計

- 🌌 **深色主題** - 玻璃擬態、漸變背景
- ✨ **動畫效果** - 淡入、脈衝、滑入、閃爍
- 📱 **響應式** - 桌面/平板/手機自適應
- 🎯 **互動元件** - 懸停效果、點擊反饋

### 專業圖表

- 📊 **Plotly** - 互動式圖表、縮放/平移
- 🕯️ **K 線圖** - 蠟燭圖、成交量、技術指標
- 📉 **深度圖** - 訂單簿累積曲線
- 📈 **權益曲線** - 累積報酬、收益分佈

---

## 🔧 技術架構

### 後端技術

| 技術 | 用途 |
|------|------|
| **Python 3.10+** | 主要語言 |
| **Streamlit** | Web UI |
| **SQLite/PostgreSQL** | 資料庫 |
| **CCXT** | 加密貨幣 API |
| **yfinance** | Yahoo Finance |
| **Plotly** | 圖表可視化 |
| **Pandas** | 數據處理 |
| **FastAPI** | WebSocket 服務 |
| **Redis** | 快取/隊列 |
| **Celery** | 任務隊列 |

### 前端技術

| 技術 | 用途 |
|------|------|
| **Streamlit Components** | UI 元件 |
| **Plotly.js** | 互動圖表 |
| **WebSocket** | 即時推送 |
| **Custom CSS** | 現代化主題 |

---

## 📈 效能優化

### 數據快取

| 數據類型 | TTL | 說明 |
|----------|-----|------|
| **價格** | 1 秒 | WebSocket 即時更新 |
| **K 線** | 5 分鐘 | 減少 API 呼叫 |
| **訂單簿** | 1 秒 | 保持即時性 |
| **用戶數據** | 30 秒 | 減少 DB 查詢 |

### 批量操作

```python
# 批量取得價格（一次性加載）
prices = batch_get_live_prices(symbols_to_load)

# 批量計算信號
signals = batch_get_signals(symbols, strategies)
```

### 異步更新

```python
# WebSocket 即時推送
# 前端自動更新，無需手動刷新
```

---

## 🔐 安全機制

### 用戶認證

- ✅ **密碼加密** - bcrypt 哈希
- ✅ **JWT 令牌** - Access/Refresh Token
- ✅ **Session 管理** - 超時自動登出
- ✅ **登入日誌** - 安全審計

### API 保護

- ✅ **限流機制** - 令牌桶演算法
- ✅ **頻率控制** - 避免觸發 API 限制
- ✅ **錯誤處理** - 優雅降級

---

## 📊 策略庫

### 趨勢策略

| 策略 | 說明 | 參數 |
|------|------|------|
| **雙均線交叉** | 快線穿越慢線 | fast_period, slow_period |
| **EMA 交叉** | 指數移動平均 | fast_period, slow_period |
| **MACD 交叉** | 趨勢動能 | fast_period, slow_period, signal_period |
| **ADX 趨勢** | 趨勢強度 | period, threshold |
| **超級趨勢** | ATR 趨勢跟隨 | period, multiplier |
| **拋物線 SAR** | 趨勢反轉 | acceleration, maximum |

### 擺盪策略

| 策略 | 說明 | 參數 |
|------|------|------|
| **RSI** | 相對強弱指標 | period, oversold, overbought |
| **KD 隨機指標** | 隨機振盪器 | k_period, d_period |
| **威廉指標** | 超買超賣 | period, oversold, overbought |
| **布林帶** | 波動率通道 | period, std_dev |
| **一目均衡表** | 綜合指標 | tenkan_period, kijun_period |

### 突破策略

| 策略 | 說明 | 參數 |
|------|------|------|
| **唐奇安通道** | 通道突破 | period |
| **雙推力** | 區間突破 | lookback, k1, k2 |

### 均值回歸

| 策略 | 說明 | 參數 |
|------|------|------|
| **VWAP 回歸** | 成交量加權回歸 | period, threshold |

### 基準策略

| 策略 | 說明 |
|------|------|
| **買入持有** | 基準比較 |

---

## 📊 績效指標

### 報酬指標

| 指標 | 說明 | 計算方式 |
|------|------|----------|
| **總報酬** | 累積報酬率 | (最終權益 - 初始) / 初始 |
| **年化報酬** | 年化報酬率 | (1 + 總報酬)^(1/年數) - 1 |
| **平均報酬** | 平均每筆報酬 | Σ報酬 / 交易次數 |

### 風險指標

| 指標 | 說明 | 計算方式 |
|------|------|----------|
| **最大回撤** | 最大虧損幅度 | max(peak - trough) / peak |
| **標準差** | 報酬波動 | stdev(報酬) |
| **VaR** | 風險價值 | 95% 信賴區間 |

### 風險調整指標

| 指標 | 說明 | 計算方式 |
|------|------|----------|
| **Sharpe** | 風險調整報酬 | (報酬 - 無風險) / 標準差 |
| **Sortino** | 下行風險調整 | (報酬 - 無風險) / 下行標準差 |
| **Calmar** | 回撤調整 | 年化報酬 / 最大回撤 |

### 交易統計

| 指標 | 說明 | 計算方式 |
|------|------|----------|
| **勝率** | 獲利交易比例 | 獲利次數 / 總次數 |
| **利潤因子** | 盈虧比 | 總獲利 / 總虧損 |
| **平均獲利** | 平均獲利金額 | Σ獲利 / 獲利次數 |
| **平均虧損** | 平均虧損金額 | Σ虧損 / 虧損次數 |
| **最大連勝** | 最長連勝記錄 | max(consecutive wins) |
| **最大連敗** | 最長連敗記錄 | max(consecutive losses) |

---

## 🚀 部署指南

### Docker 部署（推薦）

```bash
# 1. 複製環境變數
cp .env.example .env
# 編輯 .env 填入 SECRET_KEY 和 ADMIN_PASSWORD

# 2. 啟動服務
docker compose up -d

# 3. 訪問：http://localhost:8501

# 啟動含監控的完整服務（Prometheus + Grafana）
docker compose --profile monitoring up -d
```

### Docker 部署（傳統）

```bash
# 建立 Docker 映像
docker build -t stocksx .

# 啟動容器
docker run -d -p 8501:8501 stocksx

# 或使用 Docker Compose
docker-compose up -d
```

### 生產環境

```bash
# 1. 安裝 PostgreSQL
# 2. 配置 Redis
# 3. 設定環境變數
# 4. 啟動 Celery Worker
celery -A src.tasks worker --loglevel=info

# 5. 啟動 Celery Beat
celery -A src.tasks beat --loglevel=info

# 6. 啟動 FastAPI
uvicorn src.websocket_binance:app --host 0.0.0.0 --port 8001

# 7. 啟動 Streamlit
streamlit run app.py --server.port=8501
```

---

## 📚 API 文件

### 數據 API

```python
from src.data.service import data_service

# 取得價格
ticker = data_service.get_ticker("BTC/USDT")

# 取得 K 線
df = data_service.get_kline("BTC/USDT", timeframe="1h", limit=100)

# 取得訂單簿
depth = data_service.get_orderbook("BTC/USDT", limit=20)

# 計算信號
signal = data_service.calculate_signal("BTC/USDT", strategy="sma_cross")
```

### 資料庫 API

```python
from src.auth import UserDB

db = UserDB()

# 取得 watchlist
watchlist = db.get_watchlist(user_id)

# 取得交易記錄
trade_log = db.get_trade_log(watch_id, limit=50)

# 取得統計
stats = db.get_trade_stats(watch_id)
```

---

## 🤝 貢獻指南

### 開發流程

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 程式碼規範

- 遵循 PEP 8
- 添加型別提示
- 撰寫單元測試
- 更新文件

---

## 📝 更新日誌

### v4.1 (2026-03-19) — 優化版

- ✅ **安全性加強**：完善 `.gitignore`，防止 `.env` 和日誌洩漏
- ✅ **結構化日誌**：統一使用 `logging` 模組，取代散落的 `print()`
- ✅ **CI/CD**：新增 GitHub Actions 自動化 lint + test + Docker 構建
- ✅ **Docker 優化**：更新 Compose 配置，移除 deprecated `version`，加入 `tini` init
- ✅ **程式碼品質**：引入 Ruff linter + formatter，pre-commit hooks
- ✅ **開發體驗**：新增 `requirements-dev.txt`、`CONTRIBUTING.md`、`SECURITY.md`
- ✅ **環境配置**：完善 `.env.example`，新增所有可配置項

### v4.0 (2024-03-03)

- ✅ 真實數據整合（CCXT、Yahoo Finance）
- ✅ WebSocket 即時推送
- ✅ 專業圖表（K 線、深度圖、技術指標）
- ✅ 情緒分析（恐懼貪婪、社群情緒）
- ✅ 鏈上數據（巨鯨動向、交易所流量）
- ✅ 唯一帳戶號碼
- ✅ 交易記錄列表與匯出
- ✅ 現代化 UI（玻璃擬態、動畫效果）

### v3.0 (2024-02-01)

- ✅ 架構優化（日誌、限流、任務隊列）
- ✅ 健康檢查端點
- ✅ FastAPI + React 前後端分離

### v2.0 (2024-01-01)

- ✅ 策略訂閱功能
- ✅ 即時監控頁面
- ✅ 自動交易基礎

---

## 📧 聯絡方式

- **專案網址**: https://github.com/yourusername/StocksX
- **問題回報**: https://github.com/yourusername/StocksX/issues
- **電子郵件**: your.email@example.com

---

## 📄 授權條款

本專案採用 [MIT 授權條款](LICENSE)

---

## ⚠️ 免責聲明

**本軟體僅供學習與研究，不構成投資建議。**

- 回測結果基於歷史數據，不代表未來表現
- 交易涉及風險，請謹慎評估
- 開發者不對任何損失負責

---

## 🙏 致謝

感謝以下開源專案：

- [Streamlit](https://streamlit.io)
- [CCXT](https://github.com/ccxt/ccxt)
- [Plotly](https://plotly.com)
- [yfinance](https://github.com/ranaroussi/yfinance)
- [FastAPI](https://fastapi.tiangolo.com)

---

**Made with ❤️ by StocksX Team**
