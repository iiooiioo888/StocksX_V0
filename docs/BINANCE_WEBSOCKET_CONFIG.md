# StocksX 幣安 WebSocket 配置指南

## 🎯 配置完成狀態

✅ **WebSocket 服務**: 已配置使用幣安（Binance）
✅ **數據來源**: CCXT Binance API
✅ **支援市場**: 現貨（Spot）+ 永續合約（Futures）
✅ **更新頻率**: 每秒 1 次
✅ **24h 數據**: 最高價、最低價、成交量

---

## 📊 支援的交易對

### 現貨（Spot）

| 類型 | 交易對範例 |
|------|-----------|
| **主流幣** | BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT |
| **DeFi** | UNI/USDT, AAVE/USDT, LINK/USDT |
| **Layer2** | ARB/USDT, OP/USDT |
| **Meme** | DOGE/USDT, SHIB/USDT, PEPE/USDT |

### 永續合約（Futures）

| 類型 | 交易對範例 |
|------|-----------|
| **主流幣** | BTC/USDT:USDT, ETH/USDT:USDT, SOL/USDT:USDT |
| **熱門幣** | BNB/USDT:USDT, XRP/USDT:USDT, DOGE/USDT:USDT |

---

## 🚀 啟動步驟

### 1. 啟動 WebSocket 服務

**Windows**:
```bash
# 雙擊啟動
start_websocket.bat

# 或命令列
python -m src.websocket_server
```

**Linux/Mac**:
```bash
python -m src.websocket_server
```

### 2. 啟動 Streamlit

```bash
streamlit run app.py
```

### 3. 連接 WebSocket

1. 開啟「⚡ 即時監控」頁面
2. 在側邊欄輸入：`ws://localhost:8001/ws`
3. 點擊「🔌 連接 WebSocket」
4. 新增訂閱交易對（如 BTC/USDT）

---

## 🔧 幣安 API 配置

### 預設配置

WebSocket 服務已預設配置為幣安：

```python
# src/websocket_server.py

# 現貨市場
_binance_spot = ccxt.binance({
    'options': {'defaultType': 'spot'},
    'timeout': 10000,  # 10 秒超時
})

# 永續合約市場
_binance_future = ccxt.binance({
    'options': {'defaultType': 'future'},
    'timeout': 10000,
})
```

### 自訂配置

如需修改，編輯 `src/websocket_server.py`:

```python
# 使用代理（如果在中國大陸）
_binance_spot = ccxt.binance({
    'options': {'defaultType': 'spot'},
    'proxies': {
        'https': 'http://your-proxy:port'
    },
    'timeout': 10000,
})
```

---

## 📈 數據欄位說明

### 價格更新訊息格式

```json
{
    "type": "price_update",
    "data": {
        "symbol": "BTC/USDT",
        "price": 67500.00,          // 最新價格
        "change_pct": 2.5,           // 24h 漲跌幅 %
        "high_24h": 68500.00,        // 24h 最高價
        "low_24h": 65500.00,         // 24h 最低價
        "volume_24h": 125000.50,     // 24h 成交量（幣）
        "timestamp": 1709467200000,  // 時間戳
        "market_type": "spot"        // 市場類型
    }
}
```

### 顯示內容

即時監控頁面會顯示：

| 欄位 | 說明 | 顏色 |
|------|------|------|
| **最新價格** | 當前成交價 | 白色 |
| **24h 漲跌** | 漲跌幅百分比 | 綠漲/紅跌 |
| **24h 高** | 24 小時最高價 | 綠色 |
| **24h 低** | 24 小時最低價 | 紅色 |
| **24h 量** | 24 小時成交量 | 藍色 |
| **更新時間** | 最後更新時間 | 灰色 |

---

## 🧪 測試幣安連接

### 測試腳本

```python
# test_binance.py
import ccxt

# 建立交易所實例
exchange = ccxt.binance({
    'options': {'defaultType': 'spot'}
})

# 測試取得價格
try:
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"BTC 價格：${ticker['last']:,.2f}")
    print(f"24h 漲跌：{ticker['percentage']:.2f}%")
    print(f"24h 高：${ticker['high']:,.2f}")
    print(f"24h 低：${ticker['low']:,.2f}")
    print(f"24h 量：{ticker['baseVolume']:,.2f}")
except Exception as e:
    print(f"錯誤：{e}")
```

### 預期輸出

```
BTC 價格：$67,500.00
24h 漲跌：2.50%
24h 高：$68,500.00
24h 低：$65,500.00
24h 量：125,000.50
```

---

## ⚠️ 注意事項

### 1. API 限制

幣安公共 API 限制：
- **現貨**: 1200 次/分鐘（權重）
- **合約**: 2400 次/分鐘（權重）

WebSocket 服務已優化：
- ✅ 每秒只請求 1 次
- ✅ 重複使用交易所實例
- ✅ 10 秒超時設定

### 2. 地區限制

某些地區可能無法直接訪問幣安：

**解決方案**:
```python
# 使用代理
exchange = ccxt.binance({
    'proxies': {
        'https': 'http://proxy-server:port'
    }
})

# 或使用幣安 US
exchange = ccxt.binanceus({
    'options': {'defaultType': 'spot'}
})
```

### 3. 錯誤處理

常見錯誤及解決方法：

| 錯誤 | 原因 | 解決方法 |
|------|------|----------|
| `NetworkError` | 網路連接問題 | 檢查網路/使用代理 |
| `ExchangeError` | 幣安 API 錯誤 | 等待重試 |
| `InvalidSymbol` | 交易對不存在 | 檢查交易對名稱 |
| `Timeout` | 請求超時 | 增加 timeout 值 |

---

## 🔍 故障排除

### WebSocket 連接成功但無數據

**檢查**:
1. 幣安 API 是否可訪問
2. 交易對名稱是否正確
3. 查看 WebSocket 服務日誌

```bash
# 查看日誌
tail -f logs/websocket.log

# 或在前台執行查看輸出
python -m src.websocket_server
```

### 價格更新緩慢

**原因**: 網路延遲或幣安 API 限制

**解決**:
1. 檢查網路連接
2. 減少訂閱的交易對數量
3. 增加推送間隔

```python
# src/websocket_server.py
# 修改推送間隔（預設 1 秒）
await asyncio.sleep(2)  # 改為 2 秒
```

### 某些交易對無法取得價格

**原因**: 該交易對在幣安不存在

**解決**: 使用正確的幣安交易對名稱

```python
# 正確範例
BTC/USDT      # 現貨
BTC/USDT:USDT # 永續合約

# 錯誤範例
BTCUSDT       # 缺少斜槓
BTC/USD       # 幣種錯誤
```

---

## 📚 相關資源

- [幣安 API 文件](https://binance-docs.github.io/apidocs/)
- [CCXT 幣安文件](https://docs.ccxt.com/en/latest/manual/exchanges/binance.html)
- [幣安交易對列表](https://www.binance.com/en/markets)

---

## 🎯 下一步

1. **測試連接**: 開啟即時監控頁面，連接 WebSocket
2. **訂閱交易對**: 新增 BTC/USDT, ETH/USDT 等
3. **查看數據**: 確認價格、24h 數據正確顯示
4. **優化配置**: 根據需求調整推送頻率

---

**更新日期**: 2024-03-03  
**數據源**: Binance (via CCXT)  
**狀態**: ✅ 生產就緒
