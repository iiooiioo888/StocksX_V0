# StocksX 自動交易功能實作總結

## 📋 實作狀態

### ✅ 已完成功能

| 模組 | 文件 | 狀態 | 說明 |
|------|------|------|------|
| **交易執行器** | `src/trading/executor.py` | ✅ 完成 | CCXT 下單、重試機制、多交易所 |
| **風險管理** | `src/trading/risk_manager.py` | ✅ 完成 | 停損/停利、倉位計算、風險限制 |
| **自動交易** | `src/trading/auto_trader.py` | ✅ 完成 | 信號處理、持倉管理、交易日誌 |
| **Celery 任務** | `src/trading/worker.py` | ✅ 完成 | 異步執行、緊急停止、每日報告 |
| **前端頁面** | `pages/9_🤖_自動交易.py` | ✅ 完成 | 圖形化配置、監控界面 |
| **使用文件** | `AUTO_TRADING_GUIDE.md` | ✅ 完成 | 完整使用指南 |

---

## 📁 新增文件結構

```
StocksX_V0/
├── src/trading/
│   ├── __init__.py           # 模組導出
│   ├── executor.py           # 交易執行器 (320 行)
│   ├── risk_manager.py       # 風險管理 (280 行)
│   ├── auto_trader.py        # 自動交易 (450 行)
│   └── worker.py             # Celery 任務 (200 行)
│
├── pages/
│   └── 9_🤖_自動交易.py       # 前端配置頁面 (450 行)
│
└── AUTO_TRADING_GUIDE.md     # 使用指南 (500 行)
```

**總代碼行數**: ~1,700 行

---

## 🎯 核心功能詳解

### 1. 交易執行器 (`executor.py`)

**支援功能**:
```python
✅ 創建市價單/限價單
✅ 查詢持倉資訊
✅ 查詢帳戶餘額
✅ 設定槓桿和保證金模式
✅ 取消訂單
✅ 自動重試機制 (3 次)
✅ 錯誤處理與日誌記錄
```

**支援交易所**:
- Binance (含測試網絡)
- OKX
- Bybit
- Gate.io
- 其他 CCXT 支援的交易所

**使用範例**:
```python
from src.trading.executor import TradeExecutor

executor = TradeExecutor(
    exchange_id="binance",
    api_key="your_key",
    api_secret="your_secret",
    sandbox=True,  # 使用測試網絡
)

# 創建市價單
result = executor.create_market_order(
    symbol="BTC/USDT:USDT",
    side="buy",
    amount=0.001,
)

if result.success:
    print(f"✅ 下單成功：{result.order_id}")
else:
    print(f"❌ 下單失敗：{result.error}")
```

---

### 2. 風險管理器 (`risk_manager.py`)

**倉位計算方法**:

| 方法 | 公式 | 適用場景 |
|------|------|----------|
| **固定比例** | `(權益 × 風險%) / (進場價 - 停損價)` | 預設推薦 |
| **凱利公式** | `f* = (p × b - q) / b` | 有歷史統計數據 |
| **固定金額** | `權益 × 倉位比例 / 進場價` | 簡單粗暴 |

**風險限制檢查**:
```python
✅ 每日虧損限制 (預設 5%)
✅ 最大回撤限制 (預設 10%)
✅ 最大持倉數限制 (預設 5 個)
✅ 槓桿倍數限制 (預設 10x)
```

**停損/停利計算**:
```python
# 多頭
停損價 = 進場價 × (1 - 停損% / 100)
停利價 = 進場價 × (1 + 停利% / 100)

# 空頭
停損價 = 進場價 × (1 + 停損% / 100)
停利價 = 進場價 × (1 - 停利% / 100)
```

**使用範例**:
```python
from src.trading.risk_manager import RiskManager, RiskConfig

config = RiskConfig(
    risk_per_trade=0.02,      # 每筆風險 2%
    stop_loss_pct=2.0,        # 停損 2%
    take_profit_pct=4.0,      # 停利 4%
    max_open_positions=3,     # 最多 3 個持倉
)

risk_manager = RiskManager(config)

# 計算倉位
position_size = risk_manager.calculate_position_size(
    equity=10000,
    entry_price=50000,
    stop_loss_price=49000,
)
print(f"建議倉位：{position_size:.4f} BTC")

# 計算停損/停利
stop_loss = risk_manager.calculate_stop_loss(50000, "long")
take_profit = risk_manager.calculate_take_profit(50000, "long")
print(f"停損：${stop_loss:,.2f}, 停利：${take_profit:,.2f}")
```

---

### 3. 自動交易器 (`auto_trader.py`)

**工作流程**:
```
1. 載入用戶策略配置
   ↓
2. 初始化執行器和風控
   ↓
3. 循環監聽市場數據
   ↓
4. 計算策略信號
   ↓
5. 風險檢查
   ↓
6. 執行交易訂單
   ↓
7. 記錄交易日誌
   ↓
8. 管理持倉（停損/停利）
```

**信號處理邏輯**:
```python
信號 = 1 (買入): 開多倉
信號 = -1 (賣出): 開空倉
信號 = 0 (觀望): 平倉

持倉中信號反轉：先平倉，再反向開倉
```

**使用範例**:
```python
from src.trading import AutoTrader

trader = AutoTrader(user_id=1)

config = {
    "exchange": {
        "exchange_id": "binance",
        "api_key": "your_key",
        "api_secret": "your_secret",
        "sandbox": True,
    },
    "risk_management": {
        "risk_per_trade": 0.02,
        "stop_loss_pct": 2.0,
        "take_profit_pct": 4.0,
        "max_open_positions": 3,
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

if trader.initialize(config):
    trader.start(strategy_id=1)
```

---

### 4. Celery 任務 (`worker.py`)

**可用任務**:

| 任務名稱 | 功能 | 使用方式 |
|---------|------|---------|
| `execute_auto_trade` | 執行自動交易 | `execute_auto_trade.delay(user_id, strategy_id, duration_minutes)` |
| `stop_auto_trade` | 停止自動交易 | `stop_auto_trade.delay(user_id, strategy_id)` |
| `emergency_stop` | 緊急停止所有持倉 | `emergency_stop.delay(user_id)` |
| `check_position` | 查詢持倉狀態 | `check_position.delay(user_id, symbol)` |
| `daily_report` | 生成每日報告 | `daily_report.delay(user_id)` |

**使用範例**:
```python
from src.trading.worker import (
    execute_auto_trade,
    emergency_stop,
    daily_report,
)

# 啟動自動交易 (60 分鐘)
result = execute_auto_trade.delay(
    user_id=1,
    strategy_id=1,
    duration_minutes=60,
)

# 查詢任務結果
print(result.get())

# 緊急停止
emergency_stop.delay(user_id=1)

# 生成每日報告
report = daily_report.delay(user_id=1).get(timeout=30)
print(report)
```

---

### 5. 前端頁面 (`pages/9_🤖_自動交易.py`)

**頁面功能**:

#### Tab 1: 新增策略
- 交易所選擇（Binance/OKX/Bybit/Gate.io）
- 測試網絡開關
- API 金鑰輸入
- 策略選擇（15+ 種策略）
- 參數配置
- 風險設定（停損/停利/槓桿）
- 配置預覽
- 一鍵啟動

#### Tab 2: 我的策略
- 查看所有策略配置
- 啟動/停止按鈕
- 查看報告
- 刪除策略

#### Tab 3: 風險設定
- 風險計算器
- 保守/穩健/積極型建議
- 倉位計算演示

#### Tab 4: 交易日誌
- 持倉總覽
- 交易歷史
- 損益統計

#### 側邊欄快速操作
- 🚨 緊急停止所有交易
- 📊 生成每日報告
- 📈 持倉查詢

---

## 🚀 使用流程

### 步驟 1: 取得 API 金鑰

1. 訪問幣安測試網絡：https://testnet.binance.vision/
2. 註冊帳號
3. 生成 API Key 和 Secret

### 步驟 2: 啟動應用

```bash
# 1. 啟動 Redis
docker run -d -p 6379:6379 redis:7-alpine

# 2. 啟動 Celery Worker
celery -A src.tasks worker --loglevel=info -Q celery

# 3. 啟動 Streamlit
streamlit run app.py
```

### 步驟 3: 配置自動交易

1. 訪問：http://localhost:8501
2. 登入帳戶
3. 點擊側邊欄「🤖 自動交易」
4. 填寫配置表單
5. 點擊「儲存策略配置」
6. 點擊「立即啟動」

### 步驟 4: 監控交易

- 在「我的策略」分頁查看運行狀態
- 在「交易日誌」分頁查看交易記錄
- 使用側邊欄「緊急停止」按鈕處理異常

---

## 📊 測試範例

### 測試配置（保守型）

```json
{
  "exchange": {
    "exchange_id": "binance",
    "sandbox": true,
    "api_key": "your_testnet_key",
    "api_secret": "your_testnet_secret"
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
  "initial_equity": 10000
}
```

### 預期結果

1. **啟動成功**: Celery 任務開始執行
2. **信號監聽**: 每 5 秒檢查一次策略信號
3. **開倉**: 當 SMA 快線穿越慢線時，開多倉
4. **平倉**: 當信號反轉或觸發停損/停利時平倉
5. **日誌記錄**: 所有交易記錄到數據庫

---

## ⚠️ 重要注意事項

### 安全性

```python
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

## 🔧 技術細節

### 依賴庫

```python
ccxt>=4.0.0        # 交易所 API
celery>=5.3.0      # 任務隊列
redis>=4.5.0       # 快取與 Broker
streamlit>=1.28.0  # Web UI
pandas>=2.0.0      # 數據處理
```

### 數據庫表

```sql
-- 自動策略配置表
CREATE TABLE IF NOT EXISTS auto_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    config TEXT DEFAULT '{}',
    is_active INTEGER DEFAULT 1,
    last_eval REAL DEFAULT 0,
    current_strategy TEXT DEFAULT '',
    created_at REAL NOT NULL
);

-- 交易日誌表
CREATE TABLE IF NOT EXISTS trade_log (
    watch_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    side INTEGER NOT NULL,
    price REAL NOT NULL,
    pnl_pct REAL DEFAULT 0,
    pnl_amount REAL DEFAULT 0,
    fee REAL DEFAULT 0,
    reason TEXT DEFAULT '',
    created_at REAL NOT NULL
);
```

### 日誌記錄

```python
import logging

logger = logging.getLogger(__name__)

# 資訊等級
logger.info("✅ 訂單執行成功")
logger.warning("⚠️ 餘額不足")
logger.error("❌ 下單失敗")
```

---

## 📈 後續優化方向

### 短期（1-2 週）

- [ ] 增加更多策略支援
- [ ] 優化前端 UI/UX
- [ ] 增加 Telegram/Discord 通知
- [ ] 完善錯誤處理

### 中期（1 月）

- [ ] 回測驗證整合
- [ ] 策略績效排名
- [ ] 移動端適配
- [ ] 多帳戶支援

### 長期（3 月+）

- [ ] AI 策略優化
- [ ] 投資組合管理
- [ ] 社交交易功能
- [ ] 機構級風控系統

---

## 📞 支援與回饋

如有問題或建議，請透過以下方式聯繫：

- 📧 Email: support@stocksx.com
- 💬 GitHub Issues: https://github.com/yourusername/StocksX/issues
- 📖 文件：https://stocksx.com/docs

---

**版本**: 1.0
**更新日期**: 2024-03-04
**狀態**: 生產就緒（測試網絡）

---

## ⚠️ 免責聲明

本軟體僅供學習與研究，不構成投資建議。

自動交易涉及高風險，可能導致資金損失。使用本軟體即表示您同意自行承擔所有風險。

開發者不對任何直接或間接的損失負責。

**投資有風險，入市需謹慎**
