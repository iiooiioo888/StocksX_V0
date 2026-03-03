# WebSocket 即時監控測試指南

## 🧪 測試步驟

### 步驟 1: 啟動 WebSocket 服務

```bash
cd E:\Jerry_python\doc\StocksX_V0
python -m src.websocket_server
```

**預期輸出**:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
WebSocket 服務已啟動
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 步驟 2: 啟動 Streamlit

```bash
streamlit run app.py
```

### 步驟 3: 開啟即時監控頁面

1. 在瀏覽器開啟 http://localhost:8501
2. 點擊側邊欄「⚡ 即時監控」
3. 或直接在瀏覽器開啟 http://localhost:8501/即時監控

### 步驟 4: 連接 WebSocket

1. 在側邊欄確認 WebSocket URL: `ws://localhost:8001/ws`
2. 點擊「🔌 連接 WebSocket」按鈕
3. 展開「🔍 WebSocket 調試資訊」查看狀態

### 步驟 5: 查看瀏覽器控制台

按 `F12` 開啟開發者工具，切換到 `Console` 標籤，應該看到：

```
=== WebSocket 連接資訊 ===
URL: ws://localhost:8001/ws
訂閱: ['BTC/USDT', 'ETH/USDT']
=== WebSocket 初始化完成 ===
✅ WebSocket connected
📤 發送訂閱：{"action":"subscribe","symbols":["BTC/USDT","ETH/USDT"]}
📋 已訂閱：['BTC/USDT', 'ETH/USDT']
📥 收到訊息：{"type":"price_update","data":{...}}
💰 價格更新：BTC/USDT 67500.00
```

### 步驟 6: 查看價格更新

在「📊 即時價格」標籤頁，應該看到：

```
BTC/USDT
$67,500.00
🟢 +2.50%
24h 高：$68,500.00
24h 低：$65,500.00
24h 量：125,000.50
更新：10:30:45
```

---

## 🔍 故障排除

### 問題 1: WebSocket 連接失敗

**症狀**: 點擊「連接 WebSocket」後顯示「❌ 未連接」

**檢查**:
1. WebSocket 服務是否啟動
2. 端口 8001 是否被佔用
3. 防火牆設置

**解決方法**:
```bash
# 檢查端口
netstat -ano | findstr :8001

# 重啟 WebSocket 服務
# Ctrl+C 停止
python -m src.websocket_server
```

### 問題 2: 連接成功但無數據

**症狀**: 顯示「等待數據...」或價格不更新

**檢查**:
1. 瀏覽器控制台是否有 `📥 收到訊息` 訊息
2. WebSocket 服務控制台是否有 `用戶 x 訂閱：[...]` 訊息
3. 幣安 API 是否可訪問

**解決方法**:
```python
# 測試幣安 API
import ccxt
exchange = ccxt.binance()
ticker = exchange.fetch_ticker('BTC/USDT')
print(f"BTC: ${ticker['last']:,.2f}")
```

### 問題 3: 某些交易對無數據

**症狀**: BTC/USDT 有數據，但其他交易對無數據

**原因**: 該交易對在幣安不存在

**解決方法**: 使用正確的幣安交易對名稱

```python
# 正確範例
BTC/USDT      # 現貨
BTC/USDT:USDT # 永續合約

# 錯誤範例
BTCUSDT       # 缺少斜槓
```

---

## 📊 WebSocket 調試資訊

在即時監控頁面展開「🔍 WebSocket 調試資訊」：

**正常狀態**:
```
WebSocket URL: ws://localhost:8001/ws
訂閱交易對：['BTC/USDT', 'ETH/USDT']
連接狀態：✅ 已連接
已更新價格：2 個交易對
- BTC/USDT: $67,500.00 (+2.50%)
- ETH/USDT: $3,450.00 (+1.20%)
```

**異常狀態**:
```
WebSocket URL: ws://localhost:8001/ws
訂閱交易對：['BTC/USDT']
連接狀態：❌ 未連接
已更新價格：0 個交易對
```

---

## 🧪 使用 Python 測試 WebSocket

建立測試腳本 `test_ws.py`:

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8001/ws"
    
    async with websockets.connect(uri) as ws:
        # 等待歡迎訊息
        welcome = await ws.recv()
        print(f"歡迎：{welcome}")
        
        # 發送訂閱
        await ws.send(json.dumps({
            "action": "subscribe",
            "symbols": ["BTC/USDT", "ETH/USDT"]
        }))
        
        # 等待訂閱確認
        subscribed = await ws.recv()
        print(f"訂閱：{subscribed}")
        
        # 接收 5 筆價格更新
        for i in range(5):
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('type') == 'price_update':
                price_data = data.get('data', {})
                print(f"💰 {price_data.get('symbol')}: "
                      f"${price_data.get('price', 0):,.2f} "
                      f"({price_data.get('change_pct', 0):+.2f}%)")

asyncio.run(test_websocket())
```

**執行**:
```bash
python test_ws.py
```

**預期輸出**:
```
歡迎：{"type":"connected","symbol":"*","message":"已連接 WebSocket 服務，請發送訂閱訊息",...}
訂閱：{"type":"subscribed","symbols":["BTC/USDT","ETH/USDT"]}
💰 BTC/USDT: $67,500.00 (+2.50%)
💰 ETH/USDT: $3,450.00 (+1.20%)
💰 BTC/USDT: $67,520.00 (+2.53%)
💰 ETH/USDT: $3,451.00 (+1.23%)
💰 BTC/USDT: $67,480.00 (+2.47%)
```

---

## 📋 檢查清單

- [ ] WebSocket 服務已啟動（端口 8001）
- [ ] Streamlit 已啟動（端口 8501）
- [ ] 瀏覽器控制台顯示 `✅ WebSocket connected`
- [ ] 瀏覽器控制台顯示 `📋 已訂閱：[...]`
- [ ] 瀏覽器控制台顯示 `📥 收到訊息` 和 `💰 價格更新`
- [ ] 頁面顯示實際價格（不是「等待數據...」）
- [ ] 價格每秒自動更新
- [ ] 調試資訊顯示「✅ 已連接」和已更新價格

---

## ⚠️ 常見問題

### Q1: 404 Not Found 錯誤

**問題**: `%E5%8D%B3%E6%99%82%E7%9B%A3%E6%8E%A7/_stcore/host-config:1 Failed to load resource`

**說明**: 這是 Streamlit 的內部資源載入錯誤，不影響功能。

**解決**: 忽略此錯誤，專注於 WebSocket 連接狀態。

### Q2: iframe 警告

**問題**: `Unrecognized feature: 'ambient-light-sensor'` 等警告

**說明**: 這是瀏覽器的安全警告，不影響功能。

**解決**: 忽略這些警告。

### Q3: WebSocket 連接成功但頁面无數據

**可能原因**:
1. Streamlit 組件值未正確設置
2. session_state 未正確更新

**解決方法**:
```python
# 在即時監控頁面添加調試
st.write("ws_prices:", st.session_state.ws_prices)
st.write("ws_connected:", st.session_state.ws_connected)
```

---

## 🎯 成功指標

**完全正常的標誌**:

1. ✅ WebSocket 服務控制台顯示：`用戶 1 訂閱：{{'BTC/USDT', 'ETH/USDT'}}`
2. ✅ 瀏覽器控制台顯示：`📥 收到訊息` 和 `💰 價格更新`
3. ✅ 頁面顯示實際價格和 24h 數據
4. ✅ 價格每秒自動更新
5. ✅ 調試資訊顯示「✅ 已連接」和已更新價格數量

---

**更新日期**: 2024-03-03
**版本**: v1.0
**狀態**: 生產就緒
