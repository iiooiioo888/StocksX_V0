# StocksX 功能升級總結

## 📊 新增功能總覽

### v5.0 專業版升級

| 類別 | 功能 | 說明 | 狀態 |
|------|------|------|------|
| **策略** | 5 種高級策略 | 一目均衡表、Hull MA、VWAP、ATR、肯特納 | ✅ |
| **指數** | 全球市場指數 | 美股、歐股、亞股、商品、債券、匯率 | ✅ |
| **新聞** | 多來源新聞 | CoinDesk、Bloomberg、TechCrunch 等 15+ 來源 | ✅ |
| **情緒** | 新聞情緒分析 | Positive/Neutral/Negative 自動分類 | ✅ |
| **數據** | 經濟日曆 | 非農、FOMC、PMI 等重要數據 | ✅ |

---

## 📈 新增策略詳情

### 策略 16: Ichimoku Cloud（一目均衡表）

**原理**:
- 轉換線（Tenkan-sen）：9 期間最高價和最低價的平均
- 基準線（Kijun-sen）：26 期間最高價和最低價的平均
- 先行帶 A/B：形成雲層，預測未來走勢

**信號**:
- 🟢 **買入**：價格向上突破雲層，或轉換線向上穿越基準線
- 🔴 **賣出**：價格向下跌破雲層，或轉換線向下穿越基準線

**參數**:
```python
{
    "tenkan_period": 9,      # 轉換線週期
    "kijun_period": 26,      # 基準線週期
    "senkou_b_period": 52    # 先行帶 B 週期
}
```

---

### 策略 17: Hull MA（赫爾移動平均）

**原理**:
```
HMA = WMA(2*WMA(n/2) - WMA(n)), sqrt(n)
```
比傳統 MA 更平滑，延遲更小

**信號**:
- 🟢 **買入**：價格向上穿越 HMA
- 🔴 **賣出**：價格向下穿越 HMA

**參數**:
```python
{
    "hull_period": 9    # HMA 週期
}
```

---

### 策略 18: VWAP 均值回歸

**原理**:
```
VWAP = Σ(價格 × 成交量) / Σ(成交量)
```
價格偏離 VWAP 過遠時會回歸

**信號**:
- 🟢 **買入**：價格低於 VWAP - threshold 標準差（超賣）
- 🔴 **賣出**：價格高於 VWAP + threshold 標準差（超買）

**參數**:
```python
{
    "vwap_period": 20,     # VWAP 週期
    "threshold": 2.0       # 標準差閾值
}
```

---

### 策略 19: ATR Channel Breakout

**原理**:
```
ATR = 平均真實波幅
上軌 = 收盤價 + multiplier × ATR
下軌 = 收盤價 - multiplier × ATR
```

**信號**:
- 🟢 **買入**：價格向上突破上軌
- 🔴 **賣出**：價格向下跌破下軌

**參數**:
```python
{
    "atr_period": 14,          # ATR 週期
    "channel_multiplier": 2.0  # 通道倍數
}
```

---

### 策略 20: Keltner Channel

**原理**:
```
中軌 = EMA(20)
上軌 = 中軌 + multiplier × ATR(10)
下軌 = 中軌 - multiplier × ATR(10)
```

**信號**:
- 🟢 **買入**：價格向上突破上軌
- 🔴 **賣出**：價格向下跌破下軌
- ⚪ **平倉**：價格回歸中軌

**參數**:
```python
{
    "ema_period": 20,      # EMA 週期
    "atr_period": 10,      # ATR 週期
    "multiplier": 2.0      # 通道倍數
}
```

---

## 🌍 新增指數數據

### 美股指數

| 代碼 | 名稱 | 類型 |
|------|------|------|
| ^GSPC | S&P 500 | 股票 |
| ^DJI | 道瓊工業平均 | 股票 |
| ^IXIC | 那斯達克綜合 | 股票 |
| ^RUT | 羅素 2000 | 股票 |
| ^VIX | VIX 波動率指數 | 波動率 |

### 歐洲指數

| 代碼 | 名稱 | 地區 |
|------|------|------|
| ^FTSE | 富時 100 | 英國 |
| ^GDAXI | DAX | 德國 |
| ^FCHI | CAC 40 | 法國 |
| ^STOXX50E | 歐洲斯托克 50 | 歐洲 |

### 亞洲指數

| 代碼 | 名稱 | 地區 |
|------|------|------|
| ^N225 | 日經 225 | 日本 |
| ^HSI | 恆生指數 | 香港 |
| ^SSEC | 上證綜合 | 中國 |
| ^KS11 | 韓國綜合 | 韓國 |
| ^TWII | 台灣加權 | 台灣 |

### 商品指數

| 代碼 | 名稱 | 類別 | 單位 |
|------|------|------|------|
| GC=F | 黃金 | 貴金屬 | USD/oz |
| SI=F | 白銀 | 貴金屬 | USD/oz |
| CL=F | WTI 原油 | 能源 | USD/bbl |
| BZ=F | Brent 原油 | 能源 | USD/bbl |
| NG=F | 天然氣 | 能源 | USD/MMBtu |

### 債券指數

| 代碼 | 名稱 | 地區 | 單位 |
|------|------|------|------|
| ^TNX | 10 年期國債殖利率 | 美國 | % |
| ^TYX | 30 年期國債殖利率 | 美國 | % |
| ^FVX | 5 年期國債殖利率 | 美國 | % |

### 匯率指數

| 代碼 | 名稱 | 類型 |
|------|------|------|
| DX-Y.NYB | 美元指數 | 指數 |
| EURUSD=X | 歐元/美元 | 匯率 |
| GBPUSD=X | 英鎊/美元 | 匯率 |
| USDJPY=X | 美元/日圓 | 匯率 |
| BTCUSD=X | 比特幣/美元 | 加密 |

---

## 📰 新增新聞來源

### 加密貨幣新聞（5 個來源）

| 來源 | 語言 | 類別 |
|------|------|------|
| CoinDesk | EN | 加密貨幣 |
| Cointelegraph | EN | 加密貨幣 |
| The Block | EN | 加密貨幣 |
| Decrypt | EN | 加密貨幣 |
| BlockBeats | ZH | 加密貨幣 |

### 財經新聞（5 個來源）

| 來源 | 語言 | 類別 |
|------|------|------|
| Bloomberg | EN | 財經 |
| Reuters Business | EN | 財經 |
| CNBC | EN | 財經 |
| Financial Times | EN | 財經 |
| Wall Street Journal | EN | 財經 |

### 科技新聞（3 個來源）

| 來源 | 語言 | 類別 |
|------|------|------|
| TechCrunch | EN | 科技 |
| The Verge | EN | 科技 |
| Wired | EN | 科技 |

### 台灣財經新聞（3 個來源）

| 來源 | 語言 | 類別 |
|------|------|------|
| 鉅亨網 | ZH | 台灣財經 |
| 經濟日報 | ZH | 台灣財經 |
| 工商時報 | ZH | 台灣財經 |

---

## 🎯 新聞情緒分析

### 情緒分類

| 情緒 | 說明 | 顏色 |
|------|------|------|
| **Positive** | 利多消息 | 🟢 綠色 |
| **Neutral** | 中性消息 | ⚪ 灰色 |
| **Negative** | 利空消息 | 🔴 紅色 |

### 情緒關鍵字

**利多**:
```
surge, soar, jump, rally, gain, rise, increase, boom,
bullish, optimistic, positive, breakthrough, success,
上漲，飆升，大漲，利多，樂觀，突破
```

**利空**:
```
crash, plunge, drop, fall, decline, loss, bearish,
pessimistic, negative, concern, risk, warning,
下跌，暴跌，重挫，利空，悲觀，風險
```

### 情緒分數計算

```python
sentiment_score = (Positive 數量 - Negative 數量) / 總新聞數

# 解讀
sentiment_score > 0.2  → Bullish（多頭）
sentiment_score < -0.2 → Bearish（空頭）
-0.2 ≤ sentiment_score ≤ 0.2 → Neutral（中性）
```

---

## 📊 新聞分類標籤

| 分類 | 關鍵字 |
|------|--------|
| **市場動態** | market, trading, price, 指數，行情 |
| **政策監管** | regulation, policy, SEC, 監管，政策 |
| **技術發展** | technology, blockchain, innovation, 技術，區塊鏈 |
| **企業新聞** | company, business, partnership, 企業，合作 |
| **投資融資** | investment, funding, VC, 投資，融資 |
| **安全事件** | security, hack, exploit, 安全，駭客 |
| **DeFi** | defi, yield, liquidity, 去中心化，流動性 |
| **NFT** | nft, collectible, digital art, 非同質化 |
| **交易所** | exchange, binance, coinbase, 交易所，平台 |
| **宏觀經濟** | macro, fed, inflation, 總經，聯準會 |

---

## 📅 經濟日曆

### 重要經濟數據

| 數據名稱 | 頻率 | 重要性 | 影響 |
|----------|------|--------|------|
| **非農就業人口** | 每月 | ⭐⭐⭐ | 美元、美股 |
| **失業率** | 每月 | ⭐⭐⭐ | 美元、債券 |
| **FOMC 利率決策** | 每季 | ⭐⭐⭐ | 全球市場 |
| **CPI 通脹** | 每月 | ⭐⭐⭐ | 貨幣政策 |
| **GDP** | 每季 | ⭐⭐⭐ | 經濟成長 |
| **製造業 PMI** | 每月 | ⭐⭐ | 經濟景氣 |
| **零售銷售** | 每月 | ⭐⭐ | 消費力道 |

### 重要性標記

| 標記 | 說明 | 市場影響 |
|------|------|----------|
| **High** | 高重要性 | 重大波動 |
| **Medium** | 中重要性 | 中度波動 |
| **Low** | 低重要性 | 輕微波動 |

---

## 🔧 技術實作

### 策略整合

```python
# 在 strategies.py 中註冊新策略
from .advanced_strategies import ADVANCED_STRATEGIES

ALL_STRATEGIES = {
    **BASE_STRATEGIES,  # 原有 15 種
    **ADVANCED_STRATEGIES  # 新增 5 種
}

# 總計：20 種策略
```

### 指數數據獲取

```python
from src.data.indices import get_global_market_overview

# 取得全球市場概覽
overview = get_global_market_overview()

# 包含：
# - market_status: 市場開收盤狀態
# - major_indices: 主要指數
# - commodities: 商品
# - currencies: 匯率
# - bonds: 債券
```

### 新聞聚合

```python
from src.data.news_aggregator import get_all_news

# 取得所有新聞
news = get_all_news(category="all", limit=100)

# 包含：
# - crypto: 加密貨幣新聞
# - finance: 財經新聞
# - tech: 科技新聞
# - tw_finance: 台灣財經新聞
```

### 情緒分析

```python
from src.data.news_aggregator import get_news_sentiment_summary

# 取得情緒摘要
sentiment = get_news_sentiment_summary(news_list)

# 返回：
# {
#     "positive": 25,
#     "neutral": 50,
#     "negative": 25,
#     "sentiment_score": 0.0,
#     "overall": "Neutral"
# }
```

---

## 📊 使用場景

### 場景 1: 多策略回測

```python
# 同時回測 20 種策略
strategies = [
    "sma_cross", "macd_cross", "rsi_signal",
    "ichimoku", "hull_ma", "vwap_reversion",
    "atr_channel", "keltner_channel"
]

for strategy in strategies:
    result = run_backtest(symbol, strategy, params)
    compare_results(results)
```

### 場景 2: 全球市場監控

```python
# 監控全球市場
overview = get_global_market_overview()

# 檢查市場狀態
if overview["market_status"]["US"]:
    print("美股開盤中")

# 監控 VIX
if overview["major_indices"]["^VIX"]["change_pct"] > 5:
    print("VIX 大漲，市場恐慌")
```

### 場景 3: 新聞情緒交易

```python
# 取得加密貨幣新聞
crypto_news = get_crypto_news(limit=50)

# 分析情緒
sentiment = get_news_sentiment_summary(crypto_news)

# 根據情緒交易
if sentiment["overall"] == "Bullish":
    execute_trade("BUY", "BTC/USDT")
elif sentiment["overall"] == "Bearish":
    execute_trade("SELL", "BTC/USDT")
```

---

## 📈 效能優化

### 新聞快取

```python
@st.cache_data(ttl=300, show_spinner=False)
def get_cached_news(category, limit):
    """快取新聞（5 分鐘）"""
    return get_all_news(category, limit)
```

### 指數數據批處理

```python
def get_indices_batch(symbols):
    """批量取得指數報價"""
    result = {}
    for symbol in symbols:
        data = get_index_quote(symbol)
        if data:
            result[symbol] = data
    return result
```

---

## 🎯 下一步規劃

### 短期（1-2 週）

- [ ] 將新策略整合到回測頁面
- [ ] 新增指數監控儀表板
- [ ] 新聞頁面UI 優化
- [ ] 情緒分析視覺化

### 中期（1 個月）

- [ ] 加入更多新聞來源（Twitter、Reddit）
- [ ] 進階情緒分析（BERT、AI）
- [ ] 經濟日曆整合
- [ ] 即時新聞推送

### 長期（3 個月）

- [ ] 自訂新聞來源
- [ ] 策略自動優化
- [ ] 投資組合管理
- [ ] 風險評估系統

---

## 📚 相關文件

- **README.md** - 專案總覽
- **PROFESSIONAL_FEATURES.md** - 專業功能指南
- **src/backtest/advanced_strategies.py** - 高級策略源碼
- **src/data/indices.py** - 指數數據源碼
- **src/data/news_aggregator.py** - 新聞聚合源碼

---

**更新日期**: 2024-03-03  
**版本**: v5.0 Professional  
**策略總數**: 20 種  
**新聞來源**: 16 個  
**指數覆蓋**: 40+ 個
