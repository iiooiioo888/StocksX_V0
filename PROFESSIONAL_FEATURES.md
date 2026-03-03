# StocksX 專業功能升級指南

## 📊 新增專業功能總覽

### v4.0 專業版功能

| 類別 | 功能 | 說明 |
|------|------|------|
| **數據** | 真實市場數據 | CCXT、Yahoo Finance、Blockchain.com |
| **圖表** | 專業 K 線圖 | 蠟燭圖、技術指標、互動式 |
| **圖表** | 訂單簿深度圖 | 真實訂單簿、買賣累積曲線 |
| **數據** | 鏈上數據 | 巨鯨動向、交易所流量 |
| **數據** | 情緒分析 | 恐懼貪婪、社群情緒、新聞情緒 |
| **功能** | 唯一帳戶號碼 | ACC-YYYYMMDD-XXXXXX 格式 |
| **功能** | 交易記錄列表 | 完整交易歷史、CSV 匯出 |
| **效能** | 智能快取 | TTL 快取、批量加載 |
| **UI** | 現代化設計 | 玻璃擬態、動畫效果 |

---

## 📈 專業圖表升級

### 1. K 線圖表（真實數據）

**功能**:
- ✅ 真實 K 線數據（CCXT Binance）
- ✅ 多種圖表類型（蠟燭圖、線圖、面積圖）
- ✅ 時間框架選擇（1m~1w）
- ✅ 技術指標疊加

**技術指標**:
```python
# SMA（簡單移動平均）
df['SMA20'] = df['close'].rolling(window=20).mean()
df['SMA50'] = df['close'].rolling(window=50).mean()

# EMA（指數移動平均）
df['EMA20'] = df['close'].ewm(span=20).mean()

# 布林帶
df['BB_middle'] = df['close'].rolling(window=20).mean()
df['BB_upper'] = df['BB_middle'] + 2 * df['close'].rolling(window=20).std()
df['BB_lower'] = df['BB_middle'] - 2 * df['close'].rolling(window=20).std()

# MACD
exp1 = df['close'].ewm(span=12).mean()
exp2 = df['close'].ewm(span=26).mean()
df['MACD'] = exp1 - exp2
df['Signal'] = df['MACD'].ewm(span=9).mean()

# RSI
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))
```

**使用方式**:
```python
# 在即時監控頁面
df = data_manager.get_kline("BTC/USDT", timeframe="1h", periods=100)

if df is not None:
    st.success(f"✅ 已載入 {len(df)} 筆 K 線數據")
    # 繪製圖表
    st.plotly_chart(fig, use_container_width=True)
```

---

### 2. 訂單簿深度圖（真實數據）

**功能**:
- ✅ 真實訂單簿數據（CCXT）
- ✅ 買單/賣單累積曲線
- ✅ 即時更新（1 秒）
- ✅ 訂單簿統計

**數據結構**:
```python
depth = data_manager.get_depth("BTC/USDT", limit=20)

# 返回：
{
    "symbol": "BTC/USDT",
    "bids": [[67499, 1.5], [67498, 2.0], ...],  # [價格，數量]
    "asks": [[67501, 1.2], [67502, 3.5], ...],
    "timestamp": 1709467200000
}
```

**統計指標**:
```python
# 買賣比
bid_ask_ratio = sum(bids_sizes) / sum(asks_sizes)

# 價差
spread = asks_prices[0] - bids_prices[0]
spread_pct = spread / current_price * 100
```

---

### 3. 鏈上數據（真實 API）

**功能**:
- ✅ BTC 鏈上數據（Blockchain.com）
- ✅ 巨鯨交易監控
- ✅ 交易所流量

**數據來源**:
```python
# Blockchain.com API
onchain = data_manager.get_onchain_data("BTC/USDT")

# 返回：
{
    "symbol": "BTC/USDT",
    "price_usd": 67500.00,
    "volume_24h": 25000000000,
    "timestamp": 1709467200000
}
```

**巨鯨數據**:
```python
whale_df = data_manager.get_whale_data("BTC/USDT")

# 返回 DataFrame：
# 時間 | 巨鯨買入 | 巨鯨賣出
```

---

### 4. 情緒分析（真實 API）

**恐懼貪婪指數**:
```python
fg_data = data_manager.get_fear_greed()

# 返回：
{
    "value": 65,
    "classification": "Greed",
    "timestamp": 1709467200
}
```

**情緒分級**:
| 範圍 | 分類 | 顏色 |
|------|------|------|
| 0-24 | Extreme Fear | 🔴 紅色 |
| 25-44 | Fear | 🟠 橙色 |
| 45-55 | Neutral | ⚪ 灰色 |
| 56-75 | Greed | 🟢 綠色 |
| 76-100 | Extreme Greed | 🔵 藍色 |

**社群情緒**:
```python
social_data = data_manager.get_social_sentiment("BTC/USDT")

# 返回：
{
    "twitter_positive": 65.5,
    "twitter_negative": 34.5,
    "reddit_positive": 58.2,
    "reddit_negative": 41.8
}
```

---

## 🎯 交易信號系統

### 信號計算（真實數據）

**SMA 交叉策略**:
```python
def calculate_sma_cross(df):
    sma_fast = df['close'].rolling(window=5).mean()
    sma_slow = df['close'].rolling(window=20).mean()
    
    # 檢查交叉
    if sma_fast.iloc[-2] <= sma_slow.iloc[-2] and sma_fast.iloc[-1] > sma_slow.iloc[-1]:
        return "BUY", abs(sma_fast.iloc[-1] - sma_slow.iloc[-1]) / sma_slow.iloc[-1] * 1000
    elif sma_fast.iloc[-2] >= sma_slow.iloc[-2] and sma_fast.iloc[-1] < sma_slow.iloc[-1]:
        return "SELL", abs(sma_fast.iloc[-1] - sma_slow.iloc[-1]) / sma_slow.iloc[-1] * 1000
    else:
        return "HOLD", 0
```

**RSI 策略**:
```python
def calculate_rsi_signal(df):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    current_rsi = rsi.iloc[-1]
    
    if current_rsi < 30:
        return "BUY", abs(50 - current_rsi) / 50 * 100
    elif current_rsi > 70:
        return "SELL", abs(50 - current_rsi) / 50 * 100
    else:
        return "HOLD", 0
```

**信號顯示**:
```
🟢 BUY  BTC/USDT
策略：雙均線交叉
信心度：85%
價格：$67,500.00
RSI: 28.5
```

---

## 📋 唯一帳戶號碼系統

### 帳戶號碼格式

```
ACC-YYYYMMDD-XXXXXX
│   │        │
│   │        └─ 6 位隨機字元
│   └────────── 日期
└────────────── 前綴
```

**範例**:
- `ACC-20240303-A1B2C3`
- `ACC-20240303-XYZ789`

### 生成邏輯

```python
def _generate_account_id(self, watch_id: int = None) -> str:
    import random
    import string
    from datetime import datetime
    
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=6
    ))
    
    account_id = f"ACC-{date_str}-{random_str}"
    return account_id
```

### 用途

| 用途 | 說明 |
|------|------|
| **唯一識別** | 每個訂閱策略都有唯一 ID |
| **交易追蹤** | 透過帳戶號碼追蹤交易記錄 |
| **客服支援** | 用戶提供帳戶號碼快速查詢 |
| **報表生成** | 按帳戶號碼生成績效報表 |

---

## 📊 交易記錄系統

### 交易記錄欄位

| 欄位 | 說明 | 範例 |
|------|------|------|
| **時間** | 交易時間 | 2024-03-03 10:30:45 |
| **操作** | 開倉/平倉 | 開倉、平倉 |
| **方向** | 多頭/空頭 | 🟢 多頭、🔴 空頭 |
| **價格** | 成交價格 | $67,500.00 |
| **數量** | 成交數量 | 0.1500 |
| **P&L** | 實現損益 | $+520.00 |
| **P&L%** | 實現損益% | +5.20% |
| **費用** | 手續費 | $0.50 |
| **原因** | 交易原因 | 手動做多、停損 |

### 匯出功能

**CSV 格式**:
```csv
時間，操作，方向，價格，數量，P&L,P&L%,費用，原因
2024-03-03 10:30:45，平倉，🟢 多頭，67500.00,0.1500,+520.00,+5.20%,0.50，手動平倉
2024-03-03 09:15:30，開倉，🟢 多頭，64000.00,0.1563,-,-,0.50，手動做多
```

**使用方式**:
```python
# 匯出按鈕
csv = trade_df.to_csv(index=False, encoding='utf-8-sig')
st.download_button(
    label="📥 匯出交易記錄 (CSV)",
    data=csv,
    file_name=f"{symbol}_trade_log_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
```

---

## ⚡ 效能優化

### 智能快取

```python
@st.cache_data(ttl=5, show_spinner=False)
def get_watchlist_cached(user_id: int):
    """快取 watchlist 數據（5 秒）"""
    db = UserDB()
    return db.get_watchlist(user_id)

@st.cache_data(ttl=30, show_spinner=False)
def get_products_cached(user_id: int, market_type: str = "", category: str = ""):
    """快取產品數據（30 秒）"""
    db = UserDB()
    return db.get_products(user_id, market_type, category)
```

### 批量加載

```python
def batch_get_live_prices(symbols: list) -> dict:
    """批量取得價格（減少 API 呼叫）"""
    prices = {}
    for symbol in symbols:
        try:
            price_data = get_live_price(symbol)
            if price_data:
                prices[symbol] = price_data
        except Exception:
            pass
    return prices

# 使用
prices = batch_get_live_prices(symbols_to_load)
```

### 類型安全

```python
def get_watchlist(self, user_id: int) -> list[dict]:
    cur = self._conn.execute("SELECT * FROM watchlist WHERE user_id=?", (user_id,))
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        
        # 確保數值欄位正確轉換
        d["initial_equity"] = float(d.get("initial_equity", 10000) or 10000)
        d["leverage"] = float(d.get("leverage", 1.0) or 1.0)
        d["last_price"] = float(d.get("last_price", 0) or 0)
        d["entry_price"] = float(d.get("entry_price", 0) or 0)
        d["position"] = int(d.get("position", 0) or 0)
        d["pnl_pct"] = float(d.get("pnl_pct", 0) or 0)
        
        rows.append(d)
    return rows
```

---

## 🎨 UI/UX 升級

### 現代化設計

**玻璃擬態卡片**:
```css
.pro-card {
    background: linear-gradient(135deg, rgba(30,30,58,0.95), rgba(37,37,69,0.95));
    border: 1px solid rgba(58,58,92,0.5);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}

.pro-card:hover {
    border-color: rgba(110,168,254,0.5);
    box-shadow: 0 8px 32px rgba(110,168,254,0.2);
    transform: translateY(-2px);
}
```

### 動畫效果

**Shimmer 載入動畫**:
```css
.loading-shimmer {
    background: linear-gradient(90deg, 
        rgba(255,255,255,0.05) 0%, 
        rgba(255,255,255,0.1) 50%, 
        rgba(255,255,255,0.05) 100%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
}
```

**損益顏色**:
```python
def color_pnl(val):
    if isinstance(val, str):
        if val.startswith('$+'):
            return 'color: #00cc96'  # 綠色
        elif val.startswith('$-'):
            return 'color: #ef553b'  # 紅色
    return ''
```

---

## 📊 數據流程

```
用戶請求
   ↓
檢查快取（TTL: 1-300 秒）
   ↓
[命中] → 返回數據
   ↓
[未命中] → 呼叫真實 API
   ├─ CCXT（價格、K 線、訂單簿）
   ├─ Blockchain.com（鏈上數據）
   └─ Alternative.me（情緒數據）
   ↓
更新緩存
   ↓
返回數據
   ↓
渲染 UI（Plotly 圖表）
```

---

## 🚀 使用建議

### 初學者

1. **從主頁開始** - 了解平台功能
2. **嘗試回測** - 選擇 BTC/USDT，使用預設策略
3. **查看結果** - 閱讀績效指標說明
4. **訂閱策略** - 新增第一個監控策略

### 進階用戶

1. **參數優化** - 使用網格搜索尋找最佳參數
2. **多策略對比** - 同時回測多個策略
3. **Walk-Forward** - 驗證策略穩定性
4. **即時監控** - 訂閱多個交易對

### 專業用戶

1. **自訂策略** - 開發自有策略
2. **API 整合** - 串接外部數據源
3. **自動交易** - 設定自動開平倉
4. **風險管理** - 設定停損/停利

---

## 📚 相關文件

- **README.md** - 專案總覽
- **REAL_DATA_INTEGRATION.md** - 真實數據整合指南
- **BINANCE_WEBSOCKET_GUIDE.md** - 幣安 WebSocket 指南
- **PREMIUM_FEATURES.md** - 收費功能說明

---

**更新日期**: 2024-03-03  
**版本**: v4.0 Professional  
**狀態**: 生產就緒
