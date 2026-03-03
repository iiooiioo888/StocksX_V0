# StocksX 真實數據整合指南

## 📊 數據源總覽

### 1. 即時價格
**數據源**: CCXT (Binance)
**更新頻率**: 1 秒
**API**: `data_service.get_ticker(symbol)`

```python
# 取得真實價格
ticker = data_service.get_ticker("BTC/USDT")
# 返回：
{
    "symbol": "BTC/USDT",
    "price": 67500.00,
    "change_pct": 2.5,
    "high_24h": 68500.00,
    "low_24h": 65500.00,
    "volume_24h": 125000.50,
    "timestamp": 1709467200000
}
```

---

### 2. K 線圖表
**數據源**: CCXT (Binance)
**更新頻率**: 根據時間框架
**API**: `data_service.get_kline(symbol, timeframe, limit)`

```python
# 取得真實 K 線
df = data_service.get_kline("BTC/USDT", timeframe="1h", limit=100)
# 返回 DataFrame，包含：
# timestamp, open, high, low, close, volume, time
```

**支援時間框架**:
- 1m, 5m, 15m, 30m
- 1h, 2h, 4h, 6h, 8h, 12h
- 1d, 3d, 1w, 1M

---

### 3. 訂單簿深度
**數據源**: CCXT (Binance)
**更新頻率**: 1 秒
**API**: `data_service.get_orderbook(symbol, limit)`

```python
# 取得真實訂單簿
depth = data_service.get_orderbook("BTC/USDT", limit=20)
# 返回：
{
    "symbol": "BTC/USDT",
    "bids": [[67499, 1.5], [67498, 2.0], ...],
    "asks": [[67501, 1.2], [67502, 3.5], ...],
    "timestamp": 1709467200000
}
```

---

### 4. 鏈上數據
**數據源**: Blockchain.com API
**更新頻率**: 5 分鐘
**API**: `data_service.get_onchain_data(symbol)`

```python
# 取得 BTC 鏈上數據
onchain = data_service.get_onchain_data("BTC/USDT")
# 返回：
{
    "symbol": "BTC/USDT",
    "price_usd": 67500.00,
    "volume_24h": 25000000000,
    "timestamp": 1709467200000
}
```

---

### 5. 恐懼貪婪指數
**數據源**: Alternative.me API
**更新頻率**: 1 小時
**API**: `data_service.get_fear_greed_index()`

```python
# 取得恐懼貪婪指數
fg = data_service.get_fear_greed_index()
# 返回：
{
    "value": 65,
    "classification": "Greed",
    "timestamp": 1709467200
}
```

**指數範圍**:
- 0-24: Extreme Fear
- 25-44: Fear
- 45-55: Neutral
- 56-75: Greed
- 76-100: Extreme Greed

---

### 6. 交易信號
**數據源**: 計算自真實 K 線
**更新頻率**: 根據 K 線更新
**API**: `data_service.calculate_signal(symbol, strategy)`

```python
# 計算 SMA 交叉信號
signal = data_service.calculate_signal("BTC/USDT", strategy="sma_cross")
# 返回：
{
    "symbol": "BTC/USDT",
    "strategy": "sma_cross",
    "signal": 1,  # 1=買入，-1=賣出，0=觀望
    "action": "BUY",
    "confidence": 85.5,
    "price": 67500.00,
    "timestamp": 1709467200000
}
```

**支援策略**:
- `sma_cross`: 雙均線交叉
- `rsi`: RSI 超買超賣

---

## 🚀 使用方式

### 1. 啟動服務

```bash
# 不需要額外啟動服務，直接運行 Streamlit 即可
streamlit run app.py
```

### 2. 開啟即時監控

```
http://localhost:8501/即時監控
```

### 3. 查看真實數據

所有標籤頁都使用真實數據：

| 標籤頁 | 數據源 | 更新頻率 |
|--------|--------|----------|
| 📊 即時價格 | CCXT Binance | 1 秒 |
| 📈 K 線圖表 | CCXT Binance | 根據時間框架 |
| 🔔 交易信號 | 計算自真實 K 線 | 實時 |
| 💼 持倉監控 | 資料庫 + 真實價格 | 1 秒 |
| 📉 深度圖 | CCXT Binance | 1 秒 |
| 🔗 鏈上數據 | Blockchain.com | 5 分鐘 |
| 💭 情緒分析 | Alternative.me | 1 小時 |
| 📊 績效分析 | 資料庫計算 | 實時 |

---

## 📦 依賴安裝

```bash
# 安裝必要依賴
pip install ccxt requests pandas plotly

# 可選：安裝更多數據源
pip install python-dotenv
```

---

## ⚠️ 注意事項

### 1. API 限制

**Binance (CCXT)**:
- 未登入：1200 權重/分鐘
- 有 API Key：更高限制

**Alternative.me**:
- 免費層：100 次/天

**Blockchain.com**:
- 免費層：無限制

### 2. 錯誤處理

所有 API 呼叫都有錯誤處理：

```python
try:
    ticker = data_service.get_ticker("BTC/USDT")
    if ticker:
        st.write(f"BTC: ${ticker['price']:,.2f}")
    else:
        st.warning("無法取得價格數據")
except Exception as e:
    st.error(f"發生錯誤：{e}")
```

### 3. 緩存策略

| 數據類型 | 緩存時間 | 說明 |
|----------|----------|------|
| 價格 | 1 秒 | 避免重複 API 呼叫 |
| K 線 | 5 分鐘 | 減少計算開銷 |
| 訂單簿 | 1 秒 | 保持即時性 |
| 鏈上數據 | 5 分鐘 | 減少外部 API 呼叫 |
| 情緒數據 | 1 小時 | 情緒變化較慢 |

---

## 📊 數據流程

```
用戶請求
   ↓
檢查緩存
   ↓
[命中] → 返回數據
   ↓
[未命中] → 呼叫真實 API
   ↓
更新緩存
   ↓
返回數據
   ↓
渲染 UI
```

---

## 🎯 效能優化

### 1. 批量請求

```python
# 批量取得多個交易對價格
tickers = data_service.get_tickers_batch(["BTC/USDT", "ETH/USDT"])
```

### 2. 異步更新

```python
# WebSocket 即時推送價格
# 前端自動更新，無需手動刷新
```

### 3. 智能緩存

```python
# 根據數據類型設定不同 TTL
cache_ttl = {
    "price": 1.0,      # 1 秒
    "kline": 300,      # 5 分鐘
    "depth": 1.0,      # 1 秒
    "onchain": 300,    # 5 分鐘
    "sentiment": 3600  # 1 小時
}
```

---

## 🔍 故障排除

### 問題 1: 無法取得價格數據

**原因**: 網路連接問題或 API 限制

**解決方法**:
```bash
# 檢查網路連接
ping binance.com

# 檢查 API 狀態
curl https://api.binance.com/api/v3/ping
```

### 問題 2: K 線數據載入慢

**原因**: 首次載入需要呼叫 API

**解決方法**:
- 使用緩存（已自動處理）
- 減少 limit 參數
- 使用較長的時間框架

### 問題 3: 恐懼貪婪指數無法顯示

**原因**: Alternative.me API 不可用

**解決方法**:
- 等待 API 恢復
- 使用模擬數據作為備案

---

## 📚 參考資源

- [CCXT 文件](https://docs.ccxt.com/)
- [Binance API 文檔](https://binance-docs.github.io/apidocs/)
- [Alternative.me API](https://alternative.me/crypto/fear-and-greed-index-api/)
- [Blockchain.com API](https://www.blockchain.com/api)

---

**更新日期**: 2024-03-03
**版本**: v8.0
**狀態**: 生產就緒
