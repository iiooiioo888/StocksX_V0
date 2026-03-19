# 幣安 WebSocket 完整指南

## 📊 數據流類型與更新頻率

### 1. 逐筆交易流（Trade Stream）

**Stream 名稱**: `<symbol>@trade` 或 `<symbol>@aggTrade`

**更新頻率**: **實時**（有成交即推送）

**數據格式**:
```json
{
  "e": "trade",
  "E": 123456789,
  "s": "BNBBTC",
  "t": 12345,
  "p": "0.001",
  "q": "100",
  "b": 88,
  "a": 88,
  "T": 123456785,
  "m": true,
  "M": true
}
```

**使用場景**:
- 即時成交監控
- 大單追蹤
- 交易分析

**Python 範例**:
```python
import websockets
import json

async def listen_trades():
    uri = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"成交：{data['s']} @ {data['p']} - {data['q']}")
```

---

### 2. 最優掛單流（Book Ticker）

**Stream 名稱**: `<symbol>@bookTicker`

**更新頻率**: **實時**（掛單變動即推送）

**數據格式**:
```json
{
  "u": 400900217,
  "s": "BNBUSDT",
  "b": "0.0024",
  "B": "10",
  "a": "0.0026",
  "A": "100"
}
```

**欄位說明**:
- `b`: 最佳買價（Highest bid）
- `B`: 最佳買量
- `a`: 最佳賣價（Lowest ask）
- `A`: 最佳賣量

**使用場景**:
- 即時買賣價監控
- 價差計算
- 流動性分析

---

### 3. 24 小時 Ticker 流

**Stream 名稱**: `<symbol>@ticker` 或 `<symbol>@miniTicker`

**更新頻率**: **1000ms (1 秒)**

**數據格式** (miniTicker):
```json
{
  "e": "24hrMiniTicker",
  "E": 123456789,
  "s": "BNBBTC",
  "c": "0.0025",
  "o": "0.0024",
  "h": "0.0025",
  "l": "0.0024",
  "v": "10000",
  "q": "18"
}
```

**欄位說明**:
- `c`: 最新價格（Close）
- `o`: 24 小時前價格（Open）
- `h`: 24 小時最高價（High）
- `l`: 24 小時最低價（Low）
- `v`: 24 小時成交量（Volume）
- `q`: 24 小時成交額（Quote Volume）

**使用場景**:
- **即時價格監控**（推薦）
- 24 小時漲跌幅計算
- 交易量統計

**Python 範例**:
```python
async def listen_ticker():
    # 使用 miniTicker 以減少數據量
    uri = "wss://stream.binance.com:9443/ws/btcusdt@miniTicker"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"{data['s']}: ${data['c']} ({data['P']}%)")
```

---

### 4. K 線流（Candlestick）

**Stream 名稱**: `<symbol>@kline_<interval>`

**更新頻率**:
- **1s K 線**: 1000ms
- **其他間隔**: 2000ms

**可用間隔**:
| 間隔 | 名稱 |
|------|------|
| 1s | 1 秒 |
| 1m | 1 分鐘 |
| 3m | 3 分鐘 |
| 5m | 5 分鐘 |
| 15m | 15 分鐘 |
| 30m | 30 分鐘 |
| 1h | 1 小時 |
| 2h | 2 小時 |
| 4h | 4 小時 |
| 6h | 6 小時 |
| 8h | 8 小時 |
| 12h | 12 小時 |
| 1d | 1 天 |
| 3d | 3 天 |
| 1w | 1 週 |
| 1M | 1 月 |

**數據格式**:
```json
{
  "e": "kline",
  "E": 123456789,
  "s": "BNBBTC",
  "k": {
    "t": 123400000,
    "T": 123460000,
    "s": "BNBBTC",
    "i": "1m",
    "f": 100,
    "L": 200,
    "o": "0.0010",
    "c": "0.0020",
    "h": "0.0025",
    "l": "0.0015",
    "v": "1000",
    "n": 100,
    "x": false,
    "q": "1.00",
    "V": "500",
    "Q": "0.500",
    "B": "123456"
  }
}
```

**關鍵欄位**:
- `x`: K 線是否收盤（true=已收盤，false=更新中）
- `o/h/l/c`: 開/高/低/收
- `v`: 成交量
- `q`: 成交額

**使用場景**:
- K 線圖表繪製
- 技術指標計算
- 策略回測

**Python 範例**:
```python
async def listen_kline(interval="1m"):
    uri = f"wss://stream.binance.com:9443/ws/btcusdt@kline_{interval}"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            k = data["k"]
            if k["x"]:  # 只處理已收盤 K 線
                print(f"{k['i']} K 線收盤：{k['c']}")
```

---

### 5. 深度流（Depth）

**Stream 名稱**: 
- `<symbol>@depth` - 1000ms 更新
- `<symbol>@depth@100ms` - **100ms 高頻更新**

**更新頻率**: 1000ms 或 100ms（需指定 @100ms 後綴）

**數據格式**:
```json
{
  "e": "depthUpdate",
  "E": 123456789,
  "s": "BNBBTC",
  "U": 157,
  "u": 160,
  "b": [
    ["0.0024", "10"],
    ["0.0023", "50"]
  ],
  "a": [
    ["0.0026", "100"],
    ["0.0027", "200"]
  ]
}
```

**欄位說明**:
- `b`: 買單（bids）- [[價格，數量], ...]
- `a`: 賣單（asks）- [[價格，數量], ...]

**使用場景**:
- 訂單簿深度圖
- 支撐/壓力位分析
- 高頻交易

**Python 範例**:
```python
async def listen_depth():
    # 100ms 高頻更新
    uri = "wss://stream.binance.com:9443/ws/btcusdt@depth@100ms"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            best_bid = data['bids'][0] if data['bids'] else None
            best_ask = data['asks'][0] if data['asks'] else None
            print(f"買一：{best_bid} | 賣一：{best_ask}")
```

---

### 6. 平均價格流

**Stream 名稱**: `<symbol>@avgPrice`

**更新頻率**: **1000ms (1 秒)**

**數據格式**:
```json
{
  "e": "avgPrice",
  "E": 123456789,
  "s": "BNBBTC",
  "p": "0.0025",
  "w": "0.0024",
  "x": 123456789
}
```

**欄位說明**:
- `p`: 當前平均價格
- `w`: 加權平均價格

**使用場景**:
- 公平價格計算
- 資金費率計算
- 現貨/期貨價差分析

---

## 🔧 實作範例

### 完整服務端（FastAPI + 幣安）

```python
from fastapi import FastAPI, WebSocket
import websockets as ws_client
import asyncio
import json

app = FastAPI()

BINANCE_WS = "wss://stream.binance.com:9443/ws"

class BinanceManager:
    def __init__(self):
        self.user_connections = {}
        self.binance_connections = {}
    
    async def connect_binance(self, symbol: str, stream_type: str = "miniTicker"):
        """連接幣安 WebSocket"""
        stream_name = f"{symbol.lower()}@{stream_type}"
        uri = f"{BINANCE_WS}/{stream_name}"
        
        async with ws_client.connect(uri) as ws:
            self.binance_connections[symbol] = ws
            print(f"Connected to Binance: {stream_name}")
            
            async for message in ws:
                data = json.loads(message)
                # 轉發給訂閱用戶
                await self.broadcast(symbol, data)
    
    async def broadcast(self, symbol: str, data: dict):
        """廣播給所有訂閱用戶"""
        if symbol in self.user_connections:
            for ws in self.user_connections[symbol]:
                try:
                    await ws.send_json({"type": "price_update", "data": data})
                except:
                    pass

manager = BinanceManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        data = await websocket.receive_text()
        message = json.loads(data)
        
        if message.get("action") == "subscribe":
            symbols = message.get("symbols", [])
            for symbol in symbols:
                # 啟動幣安連接
                asyncio.create_task(manager.connect_binance(symbol))
                manager.user_connections.setdefault(symbol, []).append(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 前端連接（JavaScript）

```javascript
// 連接 WebSocket
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onopen = () => {
    console.log('Connected');
    
    // 訂閱交易對
    ws.send(JSON.stringify({
        action: 'subscribe',
        symbols: ['BTC/USDT', 'ETH/USDT']
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === 'price_update') {
        const data = message.data;
        console.log(`${data.s}: $${data.c} (${data.P}%)`);
        
        // 更新 UI
        updatePriceDisplay(data);
    }
};
```

---

## ⚠️ 注意事項

### 1. 連接限制

**單個 IP 限制**:
- 每 IP 最多 **300 個連接**
- 建議使用 **組合 Stream** 減少連接數

**組合 Stream 範例**:
```python
# 單一連接訂閱多個交易對
streams = "btcusdt@miniTicker/ethusdt@miniTicker/solusdt@miniTicker"
uri = f"wss://stream.binance.com:9443/stream?streams={streams}"
```

### 2. Ping/Pong 機制

**幣安**: 每 **20 秒** 發送 Ping

**回應**:
```python
# websockets 庫會自動回應
# 如需手動控制：
async with websockets.connect(uri, ping_interval=20) as ws:
    async for message in ws:
        # 處理數據
        pass
```

### 3. 錯誤處理

**重連機制**:
```python
async def connect_with_retry(uri):
    while True:
        try:
            async with websockets.connect(uri) as ws:
                async for message in ws:
                    # 處理數據
                    pass
        except Exception as e:
            print(f"Connection error: {e}")
            await asyncio.sleep(5)  # 等待 5 秒後重連
```

### 4. 數據驗證

**檢查時間戳**:
```python
def validate_timestamp(data):
    server_time = data.get("E", 0)
    local_time = int(time.time() * 1000)
    
    # 允許 5 秒誤差
    if abs(server_time - local_time) > 5000:
        print("警告：時間戳差異過大")
        return False
    return True
```

---

## 📊 更新頻率總表

| 數據流 | Stream 名稱 | 更新頻率 | 推薦用途 |
|--------|-----------|----------|----------|
| **逐筆交易** | `@trade` | 實時 | 成交監控 |
| **歸集交易** | `@aggTrade` | 實時 | 大單追蹤 |
| **最優掛單** | `@bookTicker` | 實時 | 即時買賣價 |
| **24h Ticker** | `@ticker` | 1 秒 | 完整 24h 數據 |
| **Mini Ticker** | `@miniTicker` | 1 秒 | **即時價格（推薦）** |
| **K 線 1s** | `@kline_1s` | 1 秒 | 秒級 K 線 |
| **K 線其他** | `@kline_1m` | 2 秒 | 分鐘/小時 K 線 |
| **深度** | `@depth` | 1 秒 | 訂單簿 |
| **深度高頻** | `@depth@100ms` | 100ms | 高頻交易 |
| **平均價格** | `@avgPrice` | 1 秒 | 公平價格 |

---

## 🎯 推薦配置

### 即時監控（低延遲）

```python
# 使用 miniTicker（1 秒更新，數據量小）
streams = [
    "btcusdt@miniTicker",
    "ethusdt@miniTicker",
    "solusdt@miniTicker"
]
```

### K 線分析（技術指標）

```python
# 使用 kline（2 秒更新，包含完整 OHLCV）
streams = [
    "btcusdt@kline_1m",
    "btcusdt@kline_5m",
    "ethusdt@kline_1m"
]
```

### 深度圖（高頻）

```python
# 使用 depth@100ms（100ms 更新）
streams = [
    "btcusdt@depth@100ms",
    "ethusdt@depth@100ms"
]
```

---

## 📚 參考資源

- [幣安 WebSocket 官方文檔](https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams)
- [幣安測試網絡](https://testnet.binance.vision/)
- [websockets 庫文檔](https://websockets.readthedocs.io/)

---

**更新日期**: 2024-03-03
**版本**: v1.0
**狀態**: 生產就緒
