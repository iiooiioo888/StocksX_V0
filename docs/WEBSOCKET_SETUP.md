# StocksX WebSocket 即時監控服務

## 🚀 啟動 WebSocket 服務

### 方法 1: 直接啟動

```bash
cd E:\Jerry_python\doc\StocksX_V0
python -m src.websocket_server
```

### 方法 2: 使用 uvicorn

```bash
cd E:\Jerry_python\doc\StocksX_V0
uvicorn src.websocket_server:app --host 0.0.0.0 --port 8001 --reload
```

### 方法 3: 背景執行（Linux/Mac）

```bash
nohup python -m src.websocket_server > logs/websocket.log 2>&1 &
```

---

## 📡 訪問 WebSocket

**WebSocket URL**: `ws://localhost:8001/ws/{symbol}`

**範例**:
```
ws://localhost:8001/ws/BTC/USDT
ws://localhost:8001/ws/ETH/USDT
```

**帶令牌連接**:
```
ws://localhost:8001/ws/BTC/USDT?token=YOUR_JWT_TOKEN
```

---

## 🔧 配置 WebSocket

編輯 `src/websocket_server.py`:

```python
# JWT 配置
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

# 推送間隔（秒）
PRICE_PUSH_INTERVAL = 1      # 價格推送間隔
SIGNAL_CHECK_INTERVAL = 5    # 信號檢查間隔
```

---

## 📊 使用即時監控頁面

1. **啟動 WebSocket 服務**
   ```bash
   python -m src.websocket_server
   ```

2. **啟動 Streamlit**
   ```bash
   streamlit run app.py
   ```

3. **開啟即時監控頁面**
   - 點擊「⚡ 即時監控」頁面
   - 在側邊欄輸入 WebSocket URL: `ws://localhost:8001/ws`
   - 點擊「🔌 連接 WebSocket」
   - 在側邊欄新增訂閱交易對

4. **查看即時數據**
   - 📊 即時價格：每秒更新
   - 🔔 最新信號：當策略產生信號時推送
   - 📈 持倉監控：顯示未實現 P&L

---

## 🧪 測試 WebSocket 連接

### 使用 Python 測試

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8001/ws/BTC/USDT"
    async with websockets.connect(uri) as websocket:
        # 發送訂閱訊息
        await websocket.send(json.dumps({
            "action": "subscribe",
            "symbols": ["BTC/USDT", "ETH/USDT"]
        }))
        
        # 接收訊息
        for _ in range(5):
            response = await websocket.recv()
            print(f"收到：{response}")

asyncio.run(test_websocket())
```

### 使用 wscat 測試

```bash
# 安裝 wscat
npm install -g wscat

# 連接 WebSocket
wscat -c ws://localhost:8001/ws/BTC/USDT

# 發送訂閱訊息
{"action": "subscribe", "symbols": ["BTC/USDT"]}
```

---

## 📋 WebSocket 訊息格式

### 客戶端 → 服務端

**訂閱**:
```json
{
    "action": "subscribe",
    "symbols": ["BTC/USDT", "ETH/USDT"]
}
```

**取消訂閱**:
```json
{
    "action": "unsubscribe",
    "symbols": ["BTC/USDT"]
}
```

**Ping**:
```json
{
    "action": "ping"
}
```

### 服務端 → 客戶端

**價格更新**:
```json
{
    "type": "price_update",
    "data": {
        "symbol": "BTC/USDT",
        "price": 67500.00,
        "change_pct": 2.5,
        "timestamp": 1709467200000
    }
}
```

**交易信號**:
```json
{
    "type": "signal",
    "data": {
        "symbol": "BTC/USDT",
        "action": "BUY",
        "strategy": "sma_cross",
        "confidence": 0.85,
        "price": 67500.00,
        "timestamp": 1709467200000
    }
}
```

**連接成功**:
```json
{
    "type": "connected",
    "symbol": "BTC/USDT",
    "message": "已訂閱 BTC/USDT 的即時數據",
    "timestamp": 1709467200000
}
```

---

## 🔍 故障排除

### WebSocket 無法連接

**檢查**:
1. WebSocket 服務是否啟動
2. 端口 8001 是否被佔用
3. 防火牆設置

```bash
# 檢查端口
netstat -ano | findstr :8001

# 檢查服務進程
ps aux | grep websocket
```

### 沒有收到價格更新

**檢查**:
1. 是否已訂閱交易對
2. 交易對名稱是否正確
3. WebSocket 連接狀態

```python
# 在 WebSocket 服務中添加日誌
# src/websocket_server.py
print(f"推送價格：{symbol} -> {price}")
```

### Streamlit 沒有更新

**解決方法**:
1. 確認 WebSocket 連接成功
2. 檢查瀏覽器控制台錯誤
3. 重新整理頁面

---

## 🛠️ 進階配置

### 添加新的價格來源

編輯 `src/websocket_server.py`:

```python
async def fetch_price(symbol: str) -> Optional[Dict[str, Any]]:
    """從實際 API 取得價格"""
    try:
        # 使用 CCXT 取得價格
        import ccxt
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker(symbol)
        
        return {
            "symbol": symbol,
            "price": ticker['last'],
            "change_pct": ticker['percentage'],
            "timestamp": int(time.time() * 1000)
        }
    except Exception as e:
        print(f"取得價格失敗：{e}")
        return None
```

### 添加實際策略信號

編輯 `src/websocket_server.py`:

```python
async def generate_signal(symbol: str, price: float) -> Optional[Dict[str, Any]]:
    """從實際策略生成信號"""
    try:
        # 取得 K 線數據
        import ccxt
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        
        # 計算指標
        import pandas as pd
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        
        # 計算 SMA
        df['sma_fast'] = df['close'].rolling(window=5).mean()
        df['sma_slow'] = df['close'].rolling(window=20).mean()
        
        # 檢查交叉
        if len(df) >= 2:
            if df['sma_fast'].iloc[-1] > df['sma_slow'].iloc[-1] and \
               df['sma_fast'].iloc[-2] <= df['sma_slow'].iloc[-2]:
                return {
                    "symbol": symbol,
                    "action": "BUY",
                    "strategy": "sma_cross",
                    "confidence": 0.85,
                    "price": price,
                    "timestamp": int(time.time() * 1000)
                }
    except Exception as e:
        print(f"生成信號失敗：{e}")
    
    return None
```

---

## 📚 相關資源

- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [WebSockets API](https://websockets.readthedocs.io/)
- [CCXT 文件](https://docs.ccxt.com/)

---

**更新日期**: 2024-03-03
**版本**: v1.0
