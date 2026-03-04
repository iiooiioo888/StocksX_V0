# StocksX 自動交易系統

> 🤖 機構級自動交易解決方案 - 完整實現、安全可控、易於使用

---

## 📋 快速導航

- [功能特點](#功能特點)
- [快速開始](#快速開始)
- [文件說明](#文件說明)
- [使用範例](#使用範例)
- [風險管理](#風險管理)
- [常見問題](#常見問題)

---

## ✨ 功能特點

### 核心功能 ✅

| 功能 | 說明 | 狀態 |
|------|------|------|
| **多交易所支援** | Binance、OKX、Bybit、Gate.io 等 | ✅ 完成 |
| **15+ 交易策略** | SMA、MACD、RSI、布林帶等 | ✅ 完成 |
| **智能風險管理** | 停損/停利/倉位控制/回撤限制 | ✅ 完成 |
| **自動交易執行** | 信號觸發自動下單 | ✅ 完成 |
| **持倉追蹤** | 即時損益計算 | ✅ 完成 |
| **交易日誌** | 完整交易記錄與統計 | ✅ 完成 |
| **Celery 異步** | 後台執行不阻塞 UI | ✅ 完成 |
| **前端配置** | 圖形化界面配置參數 | ✅ 完成 |
| **緊急停止** | 一鍵平倉所有持倉 | ✅ 完成 |

### 技術特色 🚀

- ✅ **CCXT 整合**：統一接口連接多家交易所
- ✅ **測試網絡支援**：先用測試網絡驗證策略
- ✅ **重試機制**：網路錯誤自動重試（3 次）
- ✅ **風險計算器**：多種倉位計算方法（固定比例/凱利公式）
- ✅ **移動通知**：支援 Bark 推送（可擴展 Telegram/Discord）
- ✅ **每日報告**：自動生成交易績效報告

---

## 🚀 快速開始

### 方法 1: 使用啟動腳本（Windows）

```bash
# 雙擊執行或在命令提示字元執行
start_auto_trading.bat
```

### 方法 2: 手動啟動

```bash
# 1. 啟動 Redis
docker run -d -p 6379:6379 --name stocksx_redis redis:7-alpine

# 2. 啟動 Celery Worker
celery -A src.tasks worker --loglevel=info -Q celery

# 3. 啟動 Streamlit
streamlit run app.py

# 4. 訪問自動交易頁面
# http://localhost:8501
```

### 方法 3: 測試功能

```bash
# 運行測試腳本
python tests/test_auto_trading.py
```

---

## 📁 文件說明

### 核心模組

```
src/trading/
├── __init__.py           # 模組導出
├── executor.py           # 交易執行器（320 行）
├── risk_manager.py       # 風險管理（280 行）
├── auto_trader.py        # 自動交易主程式（450 行）
└── worker.py             # Celery 任務（200 行）
```

### 前端頁面

```
pages/
└── 9_🤖_自動交易.py       # 圖形化配置頁面（450 行）
```

### 文件

```
AUTO_TRADING_GUIDE.md             # 完整使用指南（500 行）
AUTO_TRADING_IMPLEMENTATION.md    # 實作總結（400 行）
README_AUTO_TRADING.md            # 本文件（快速開始）
```

### 測試

```
tests/
└── test_auto_trading.py          # 功能測試腳本
```

### 腳本

```
start_auto_trading.bat            # Windows 啟動腳本
```

---

## 📖 使用範例

### 範例 1: 簡單配置（保守型）

```python
from src.trading import AutoTrader

trader = AutoTrader(user_id=1)

config = {
    "exchange": {
        "exchange_id": "binance",
        "api_key": "your_key",
        "api_secret": "your_secret",
        "sandbox": True,  # 使用測試網絡
    },
    "risk_management": {
        "risk_per_trade": 0.01,      # 每筆風險 1%
        "stop_loss_pct": 1.5,        # 停損 1.5%
        "take_profit_pct": 3.0,      # 停利 3%
        "max_open_positions": 2,     # 最多 2 個持倉
        "leverage": 1.0,             # 無槓桿
    },
    "subscriptions": [
        {
            "symbol": "BTC/USDT:USDT",
            "strategy": "sma_cross",
            "params": {"fast": 10, "slow": 30},
            "timeframe": "4h",
        }
    ],
    "initial_equity": 10000,
}

if trader.initialize(config):
    trader.start(strategy_id=1)
```

### 範例 2: Celery 異步執行

```python
from src.trading.worker import execute_auto_trade

# 啟動自動交易（60 分鐘）
result = execute_auto_trade.delay(
    user_id=1,
    strategy_id=1,
    duration_minutes=60,
)

# 查詢結果
print(result.get())

# 緊急停止
from src.trading.worker import emergency_stop
emergency_stop.delay(user_id=1)
```

### 範例 3: 前端配置

1. 訪問：http://localhost:8501
2. 登入帳戶
3. 點擊側邊欄「🤖 自動交易」
4. 填寫配置表單：
   - 選擇交易所（Binance/OKX/Bybit）
   - 輸入 API 金鑰
   - 選擇策略和參數
   - 設定風險參數
5. 點擊「儲存策略配置」
6. 點擊「立即啟動」

---

## 🛡️ 風險管理

### 倉位計算方法

| 方法 | 公式 | 適用 |
|------|------|------|
| **固定比例** | `(權益 × 風險%) / (進場價 - 停損價)` | 預設推薦 |
| **凱利公式** | `f* = (p × b - q) / b` | 有歷史數據 |
| **固定金額** | `權益 × 倉位比例 / 進場價` | 簡單模式 |

### 風險限制

```python
✅ 每筆風險：0.5-5%（預設 2%）
✅ 每日虧損：3-15%（預設 5%）
✅ 最大回撤：5-20%（預設 10%）
✅ 最大持倉：1-10 個（預設 5 個）
✅ 槓桿限制：1-20x（預設 1x）
```

### 停損/停利

```python
# 多頭範例
進場價：$50,000
停損價：$49,000 (-2%)
停利價：$52,000 (+4%)

# 自動計算與執行
```

### 緊急停止

```python
# 方法 1: 前端按鈕
側邊欄 → 🛑 緊急停止所有交易

# 方法 2: Celery 任務
from src.trading.worker import emergency_stop
emergency_stop.delay(user_id=1)

# 方法 3: 代碼控制
trader.stop()
```

---

## 📊 支援的策略

### 趨勢策略

- `sma_cross` - 雙均線交叉
- `ema_cross` - 指數均線交叉
- `macd_cross` - MACD 交叉
- `supertrend` - 超級趨勢
- `adx_trend` - ADX 趨勢強度
- `parabolic_sar` - 拋物線 SAR

### 擺盪策略

- `rsi_signal` - RSI 超買超賣
- `stochastic` - KD 隨機指標
- `williams_r` - 威廉指標
- `bollinger_signal` - 布林帶

### 突破策略

- `donchian_channel` - 唐奇安通道
- `dual_thrust` - 雙推力突破

### 其他策略

- `vwap_reversion` - VWAP 回歸
- `ichimoku` - 一目均衡表
- `buy_and_hold` - 買入持有（基準）

---

## ⚠️ 重要提醒

### 安全性

```
✅ 使用測試網絡驗證（預設）
✅ API 金鑰加密存儲
✅ 風險限制檢查
✅ 緊急停止功能
✅ 完整交易日誌
```

### 風險提示

```
⚠️ 加密貨幣交易具有高風險
⚠️ 可能導致資金損失
⚠️ 過去績效不代表未來表現
⚠️ 建議使用閒置資金
⚠️ 隨時準備手動干預
```

### 建議配置

| 參數 | 新手建議 | 進階建議 |
|------|----------|----------|
| 測試網絡 | ✅ 使用 | ❌ 生產環境 |
| 每筆風險 | 0.5-1% | 1-2% |
| 停損 | 1-1.5% | 2-3% |
| 槓桿 | 1x | 3-5x |
| 最大持倉 | 2-3 | 3-5 |

---

## 🔧 技術架構

```
┌─────────────────────────────────────────────────┐
│              前端（Streamlit）                    │
│  pages/9_🤖_自動交易.py                          │
│  - 配置表單                                      │
│  - 策略管理                                      │
│  - 持倉監控                                      │
│  - 緊急停止                                      │
└─────────────────────────────────────────────────┘
                    ↕ HTTP / Celery
┌─────────────────────────────────────────────────┐
│            後台任務（Celery）                     │
│  src/trading/worker.py                          │
│  - execute_auto_trade                           │
│  - stop_auto_trade                              │
│  - emergency_stop                               │
│  - daily_report                                 │
└─────────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────────┐
│          自動交易核心（AutoTrader）               │
│  src/trading/auto_trader.py                     │
│  - 信號計算                                      │
│  - 風險檢查                                      │
│  - 訂單執行                                      │
│  - 持倉管理                                      │
└─────────────────────────────────────────────────┘
            ↕                      ↕
┌──────────────────────┐  ┌──────────────────────┐
│   交易執行器          │  │   風險管理器          │
│  (executor.py)       │  │  (risk_manager.py)   │
│  - CCXT 下單          │  │  - 倉位計算          │
│  - 訂單管理          │  │  - 停損/停利          │
│  - 持倉查詢          │  │  - 風險檢查          │
└──────────────────────┘  └──────────────────────┘
            ↕
┌─────────────────────────────────────────────────┐
│              交易所 API（CCXT）                   │
│  Binance / OKX / Bybit / Gate.io                │
└─────────────────────────────────────────────────┘
```

---

## ❓ 常見問題

### Q1: 如何取得 API 金鑰？

**A**: 
1. 訪問幣安測試網絡：https://testnet.binance.vision/
2. 註冊帳號
3. 進入 API 管理
4. 生成 API Key 和 Secret

### Q2: 自動交易安全嗎？

**A**: 系統提供多層保護：
- ✅ 測試網絡支援
- ✅ 風險限制檢查
- ✅ 停損/停利自動執行
- ✅ 緊急停止功能
- ✅ 完整交易日誌

但加密貨幣交易本身具有高風險，請謹慎使用。

### Q3: 如何停止自動交易？

**A**: 三種方式：
1. 前端頁面點擊「⏹️ 停止」按鈕
2. 側邊欄「🛑 緊急停止所有交易」
3. 代碼執行：`trader.stop()` 或 `emergency_stop.delay(user_id)`

### Q4: 需要多少資金？

**A**: 
- **測試網絡**: 無要求（虛擬資金）
- **生產環境**: 建議至少 $1,000 USDT
- **保守配置**: $5,000+ USDT
- **積極配置**: $10,000+ USDT

### Q5: 支援哪些交易所？

**A**: 所有 CCXT 支援的交易所，推薦：
- Binance（幣安）- 預設
- OKX
- Bybit
- Gate.io

### Q6: 如何查看交易記錄？

**A**: 
1. 前端頁面 → 「交易日誌」分頁
2. 代碼查詢：
```python
from src.auth.user_db import UserDB
db = UserDB()
trades = db.get_trade_log(watch_id)
```

### Q7: 策略失效怎麼辦？

**A**: 
1. 定期檢視每日報告
2. 使用回測系統驗證策略
3. 根據市場狀況調整參數
4. 切換到其他策略

---

## 📞 支援

- 📧 Email: support@stocksx.com
- 💬 GitHub Issues: https://github.com/yourusername/StocksX/issues
- 📖 完整文件：`AUTO_TRADING_GUIDE.md`

---

## 📄 授權

MIT License

---

## ⚠️ 免責聲明

**本軟體僅供學習與研究，不構成投資建議。**

自動交易涉及高風險，可能導致資金損失。使用本軟體即表示您同意自行承擔所有風險。

開發者不對任何直接或間接的損失負責。

**投資有風險，入市需謹慎**

---

**版本**: 1.0
**更新日期**: 2024-03-04
**狀態**: 生產就緒（測試網絡）
