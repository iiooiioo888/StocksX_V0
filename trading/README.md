# StocksX 自動化交易系統

## 功能

- ✅ 自動跟隨策略信號
- ✅ 訂單執行管理
- ✅ 風險控制（止損/止盈）
- ✅ 持倉管理
- ✅ 交易日誌
- ✅ 性能追蹤

## 快速開始

```bash
# 安裝依賴
pip3 install -r trading/requirements.txt

# 配置交易參數
cp trading/config.example.yaml trading/config.yaml

# 啟動交易引擎
python3 trading/trading_engine.py
```

## 架構

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Strategy   │ ──► │   Trading    │ ──► │   Broker    │
│  Signals    │     │    Engine    │     │   (API)     │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Risk Mgmt   │
                    │  Stop Loss   │
                    │  Take Profit │
                    └──────────────┘
```

## 配置示例

```yaml
trading:
  enabled: true
  paper_trading: true  # 模擬交易
  
broker:
  name: "alpaca"  # alpaca, binance, ftmo
  api_key: "your_key"
  api_secret: "your_secret"
  
risk:
  max_position_size: 10000  # 最大持倉
  stop_loss_pct: 2.0  # 止損 2%
  take_profit_pct: 5.0  # 止盈 5%
  max_daily_loss: 1000  # 每日最大虧損
  
strategies:
  - name: "sma_cross"
    weight: 0.3
    enabled: true
  - name: "macd_cross"
    weight: 0.3
    enabled: true
  - name: "rsi"
    weight: 0.4
    enabled: true
```

## API 使用

```python
from trading.trading_engine import TradingEngine

engine = TradingEngine()

# 下單
engine.place_order(
    symbol="AAPL",
    side="BUY",
    quantity=100,
    type="MARKET"
)

# 平倉
engine.close_position("AAPL")

# 獲取持倉
positions = engine.get_positions()
```
