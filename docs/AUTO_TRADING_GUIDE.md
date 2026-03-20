# StocksX 自動交易功能使用指南

## 📋 目錄

1. [功能概述](#功能概述)
2. [快速開始](#快速開始)
3. [配置說明](#配置說明)
4. [風險管理](#風險管理)
5. [API 金鑰配置](#api-金鑰配置)
6. [使用範例](#使用範例)
7. [常見問題](#常見問題)

---

## 功能概述

### 已實現功能 ✅

| 功能 | 說明 | 狀態 |
|------|------|------|
| **交易執行** | 透過 CCXT 連接多家交易所 | ✅ 完成 |
| **風險管理** | 停損/停利/倉位控制 | ✅ 完成 |
| **自動交易** | 策略信號自動執行 | ✅ 完成 |
| **持倉追蹤** | 即時損益計算 | ✅ 完成 |
| **交易日誌** | 完整交易記錄 | ✅ 完成 |
| **Celery 異步** | 後台執行交易任務 | ✅ 完成 |

### 待實現功能 🔴

| 功能 | 說明 | 優先級 |
|------|------|--------|
| **前端配置頁面** | 圖形化配置界面 | 🔴 高 |
| **交易所 API 整合** | 用戶 API 金鑰管理 | 🔴 高 |
| **回測驗證** | 策略歷史驗證 | 🟡 中 |
| **移動通知** | Telegram/Discord 推送 | 🟡 中 |
| **投資組合優化** | 多策略資金配置 | 🟢 低 |

---

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

確保已安裝 `ccxt>=4.0.0`。

### 2. 配置 API 金鑰

在 `.env` 文件中添加：

```bash
# 幣安 API 金鑰（測試網絡）
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret

# 生產環境（可選）
BINANCE_PROD_API_KEY=your_prod_api_key
BINANCE_PROD_API_SECRET=your_prod_api_secret
```

### 3. 啟動自動交易

#### 方法 1：直接執行（測試用）

```python
from src.trading import AutoTrader

# 創建自動交易器
trader = AutoTrader(user_id=1)

# 載入配置
config = {
    "exchange": {
        "exchange_id": "binance",
        "api_key": "your_api_key",
        "api_secret": "your_api_secret",
        "sandbox": True,  # 使用測試網絡
    },
    "risk_management": {
        "risk_per_trade": 0.02,      # 每筆風險 2%
        "stop_loss_pct": 2.0,        # 停損 2%
        "take_profit_pct": 4.0,      # 停利 4%
        "max_open_positions": 3,     # 最多 3 個持倉
    },
    "subscriptions": [
        {
            "symbol": "BTC/USDT:USDT",
            "strategy": "sma_cross",
            "params": {"fast": 5, "slow": 20},
            "timeframe": "1h",
        }
    ],
    "initial_equity": 10000,
}

# 初始化並啟動
if trader.initialize(config):
    trader.start(strategy_id=1)
```

#### 方法 2：使用 Celery 任務（生產用）

```python
from src.trading.worker import execute_auto_trade

# 非同步執行自動交易
result = execute_auto_trade.delay(
    user_id=1,
    strategy_id=1,
    duration_minutes=60,  # 執行 60 分鐘
)

# 查詢結果
print(result.get())
```

---

## 配置說明

### 完整配置範例

```json
{
  "exchange": {
    "exchange_id": "binance",
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "sandbox": true,
    "options": {
      "defaultType": "future",
      "adjustForTimeDifference": true
    }
  },
  
  "risk_management": {
    "risk_per_trade": 0.02,
    "max_position_size": 0.25,
    "position_sizing_method": "fixed_fraction",
    "stop_loss_pct": 2.0,
    "take_profit_pct": 4.0,
    "trailing_stop": false,
    "trailing_stop_pct": 1.5,
    "max_daily_loss_pct": 5.0,
    "max_drawdown_pct": 10.0,
    "max_open_positions": 3,
    "leverage": 5.0,
    "max_leverage": 10.0
  },
  
  "subscriptions": [
    {
      "symbol": "BTC/USDT:USDT",
      "strategy": "sma_cross",
      "params": {"fast": 5, "slow": 20},
      "timeframe": "1h"
    },
    {
      "symbol": "ETH/USDT:USDT",
      "strategy": "rsi_signal",
      "params": {"period": 14, "oversold": 30, "overbought": 70},
      "timeframe": "1h"
    }
  ],
  
  "initial_equity": 10000,
  "close_on_stop": true
}
```

### 配置參數詳解

#### 交易所配置 (`exchange`)

| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `exchange_id` | string | "binance" | 交易所 ID（binance/okx/bybit） |
| `api_key` | string | - | API Key |
| `api_secret` | string | - | API Secret |
| `sandbox` | boolean | true | 是否使用測試網絡 |
| `options.defaultType` | string | "spot" | 交易類型（spot/future） |

#### 風險管理配置 (`risk_management`)

| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `risk_per_trade` | float | 0.02 | 每筆交易風險（2%） |
| `max_position_size` | float | 0.25 | 最大倉位比例（25%） |
| `position_sizing_method` | string | "fixed_fraction" | 倉位計算方法 |
| `stop_loss_pct` | float | 2.0 | 停損百分比（2%） |
| `take_profit_pct` | float | 4.0 | 停利百分比（4%） |
| `trailing_stop` | boolean | false | 是否啟用移動停損 |
| `trailing_stop_pct` | float | 1.5 | 移動停損百分比 |
| `max_daily_loss_pct` | float | 5.0 | 每日最大虧損（5%） |
| `max_drawdown_pct` | float | 10.0 | 最大回撤（10%） |
| `max_open_positions` | int | 5 | 最大同時持倉數 |
| `leverage` | float | 1.0 | 槓桿倍數 |
| `max_leverage` | float | 10.0 | 最大槓桿限制 |

#### 訂閱配置 (`subscriptions`)

| 參數 | 類型 | 說明 |
|------|------|------|
| `symbol` | string | 交易對（BTC/USDT:USDT） |
| `strategy` | string | 策略名稱（見策略列表） |
| `params` | object | 策略參數 |
| `timeframe` | string | 時間框架（1m/5m/15m/1h/4h/1d） |

---

## 風險管理

### 倉位計算方法

#### 1. 固定比例（Fixed Fraction）- **預設**

```
倉位 = (權益 × 風險比例) / (進場價 - 停損價)

範例：
- 權益：$10,000
- 風險比例：2%
- 進場價：$50,000 (BTC)
- 停損價：$49,000

風險金額 = $10,000 × 2% = $200
價格差 = $50,000 - $49,000 = $1,000
倉位 = $200 / $1,000 = 0.2 BTC
```

#### 2. 凱利公式（Kelly）

```
f* = (p × b - q) / b

其中：
- p = 勝率（預設 50%）
- q = 1 - p（失敗率）
- b = 盈虧比（預設 2:1）

凱利比例通常較激進，建議設置上限 25%
```

#### 3. 固定金額（Fixed Amount）

```
倉位 = 權益 × 最大倉位比例 / 進場價
```

### 停損/停利計算

#### 多頭（Long）

```
停損價 = 進場價 × (1 - 停損% / 100)
停利價 = 進場價 × (1 + 停利% / 100)

範例：
- 進場價：$50,000
- 停損：2%
- 停利：4%

停損價 = 50,000 × (1 - 2/100) = $49,000
停利價 = 50,000 × (1 + 4/100) = $52,000
```

#### 空頭（Short）

```
停損價 = 進場價 × (1 + 停損% / 100)
停利價 = 進場價 × (1 - 停利% / 100)
```

### 風險限制檢查

自動交易前會檢查：

1. ✅ 每日虧損是否超過限制
2. ✅ 回撤是否超過限制
3. ✅ 持倉數是否達到上限
4. ✅ 槓桿是否超過限制

任一條件不滿足，將**停止開新倉**。

---

## API 金鑰配置

### 幣安測試網絡

1. 訪問：https://testnet.binance.vision/
2. 註冊帳號
3. 生成 API Key
4. 在 `.env` 中配置：

```bash
BINANCE_API_KEY=your_testnet_key
BINANCE_API_SECRET=your_testnet_secret
```

### 幣安生產環境

1. 訪問：https://www.binance.com/
2. 進入 API 管理
3. 創建 API Key（需 KYC）
4. 勾選「啟用現貨/合約交易」
5. 設置 IP 白名單（建議）

```bash
BINANCE_PROD_API_KEY=your_prod_key
BINANCE_PROD_API_SECRET=your_prod_secret
```

### 其他交易所

在代碼中指定 `exchange_id`：

```python
# OKX
exchange_id = "okx"

# Bybit
exchange_id = "bybit"

# Gate.io
exchange_id = "gateio"
```

---

## 使用範例

### 範例 1：保守型配置

```json
{
  "exchange": {
    "exchange_id": "binance",
    "sandbox": true
  },
  "risk_management": {
    "risk_per_trade": 0.01,
    "stop_loss_pct": 1.5,
    "take_profit_pct": 3.0,
    "max_open_positions": 2,
    "leverage": 1.0
  },
  "subscriptions": [
    {
      "symbol": "BTC/USDT:USDT",
      "strategy": "sma_cross",
      "params": {"fast": 10, "slow": 30},
      "timeframe": "4h"
    }
  ],
  "initial_equity": 5000
}
```

**特點**：
- 每筆風險 1%
- 低槓桿（1x）
- 寬鬆停損（1.5%）
- 最多 2 個持倉

### 範例 2：積極型配置

```json
{
  "exchange": {
    "exchange_id": "binance",
    "sandbox": true
  },
  "risk_management": {
    "risk_per_trade": 0.03,
    "stop_loss_pct": 2.0,
    "take_profit_pct": 6.0,
    "max_open_positions": 5,
    "leverage": 5.0
  },
  "subscriptions": [
    {
      "symbol": "BTC/USDT:USDT",
      "strategy": "macd_cross",
      "params": {"fast": 12, "slow": 26, "signal": 9},
      "timeframe": "1h"
    },
    {
      "symbol": "ETH/USDT:USDT",
      "strategy": "rsi_signal",
      "params": {"period": 14, "oversold": 30, "overbought": 70},
      "timeframe": "1h"
    },
    {
      "symbol": "SOL/USDT:USDT",
      "strategy": "bollinger_signal",
      "params": {"period": 20, "std_dev": 2},
      "timeframe": "1h"
    }
  ],
  "initial_equity": 20000
}
```

**特點**：
- 每筆風險 3%
- 中等槓桿（5x）
- 多策略並行
- 較高停利（6%）

### 範例 3：多交易所配置

```python
# 同時在多個交易所執行
from src.trading import AutoTrader

# 幣安配置
binance_config = {
    "exchange": {"exchange_id": "binance", ...},
    "subscriptions": [...],
}

# OKX 配置
okx_config = {
    "exchange": {"exchange_id": "okx", ...},
    "subscriptions": [...],
}

# 分別啟動
trader1 = AutoTrader(user_id=1)
trader1.initialize(binance_config)

trader2 = AutoTrader(user_id=1)
trader2.initialize(okx_config)
```

---

## 常見問題

### Q1: 自動交易安全嗎？

**A**: 系統提供多層保護：

1. **測試網絡支援**：先用測試網絡驗證
2. **風險限制**：停損/停利/倉位控制
3. **緊急停止**：可隨時手動平倉
4. **日誌記錄**：完整交易記錄

但**加密貨幣交易具有高風險**，請謹慎使用。

### Q2: 如何停止自動交易？

**A**: 三種方式：

```python
# 1. 正常停止
trader.stop()

# 2. Celery 任務停止
from src.trading.worker import stop_auto_trade
stop_auto_trade.delay(user_id=1, strategy_id=1)

# 3. 緊急停止
from src.trading.worker import emergency_stop
emergency_stop.delay(user_id=1)
```

### Q3: 如何查看交易記錄？

**A**: 從數據庫查詢：

```python
from src.auth.user_db import UserDB

db = UserDB()
watchlist = db.get_watchlist(user_id=1)

for w in watchlist:
    trades = db.get_trade_log(w["id"])
    for t in trades:
        print(f"{t['symbol']} | {t['action']} | {t['pnl_pct']:.2f}%")
```

### Q4: 策略失效怎麼辦？

**A**: 建議定期檢視：

1. **每日報告**：查看 `daily_report` 任務結果
2. **回測驗證**：使用回測系統驗證策略
3. **參數調整**：根據市場狀況優化參數

### Q5: 支援哪些策略？

**A**: 所有回測系統的策略都支援：

- `sma_cross` - 雙均線交叉
- `macd_cross` - MACD 交叉
- `rsi_signal` - RSI 超買超賣
- `bollinger_signal` - 布林帶
- `supertrend` - 超級趨勢
- `donchian_channel` - 唐奇安通道
- 等 15+ 種策略

### Q6: 需要多少資金？

**A**: 建議：

- **測試網絡**：無要求（虛擬資金）
- **生產環境**：至少 $1,000 USDT
- **保守配置**：$5,000+ USDT
- **積極配置**：$10,000+ USDT

### Q7: 手續費如何計算？

**A**: 自動計入交易成本：

```
幣安合約手續費：
- Maker: 0.02%
- Taker: 0.04%

範例：
- 開倉：$10,000
- 手續費：$10,000 × 0.04% = $4
- 平倉：$10,200
- 手續費：$10,200 × 0.04% = $4.08
- 總手續費：$8.08
```

---

## 下一步開發計劃

### 短期（1-2 週）

- [ ] 前端配置頁面
- [ ] API 金鑰管理界面
- [ ] 即時持倉監控
- [ ] 手動平倉按鈕

### 中期（1 月）

- [ ] 回測驗證整合
- [ ] 策略績效排名
- [ ] Telegram 通知
- [ ] 移動端支援

### 長期（3 月+）

- [ ] AI 策略優化
- [ ] 投資組合管理
- [ ] 多帳戶支援
- [ ] 社交交易功能

---

## 免責聲明

⚠️ **重要提醒**：

1. 本軟體僅供學習與研究
2. 自動交易涉及高風險
3. 過去績效不代表未來表現
4. 請使用閒置資金投資
5. 開發者不對任何損失負責

**建議先用測試網絡充分測試後，再考慮使用真實資金。**

---

**版本**: 1.0
**更新日期**: 2024-03-04
**狀態**: 生產就緒（測試網絡）
