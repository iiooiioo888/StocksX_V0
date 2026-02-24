# StocksX_V0 — 通用回測平台 MVP（免費數據源版）

本專案提供**加密貨幣數據採集模塊**，透過 CCXT 統一取得 Binance、Bybit 永續合約的 K 線與資金費率，並以 SQLite 本地緩存、限流保護與數據清洗，供後續回測使用。

## 功能摘要

- **多交易所**：支援 Binance、Bybit（永續合約），透過 CCXT 統一接口。
- **本地緩存**：首次拉取後寫入 SQLite（鍵：`exchange_symbol_timeframe`），之後優先讀本地，減少 API 請求。
- **數據內容**：K 線 (OHLCV)、資金費率 (funding rate)，可選 open_interest、mark_price。
- **數據清洗**：時間戳統一 UTC 毫秒、去重、缺失 K 線前向填充 (FFill)、插針標記（偏離均價 5% 可標記為異常）。
- **限流保護**：遇 HTTP 429 自動指數退避重試。

## 安裝

```bash
cd e:\Jerry_python\doc\StocksX_V0
pip install -r requirements.txt
```

依賴：`ccxt`、`python-dotenv`（可選）。

## 使用範例

### 拉取 BTC/USDT 永續 K 線與資金費率並寫入緩存

```python
from src.data.crypto import CryptoDataFetcher
import time

# Binance 永續
fetcher = CryptoDataFetcher("binance")
symbol = "BTC/USDT:USDT"

# 拉取最近 500 根 1h K 線（首次會請求交易所，之後可從緩存讀）
since_ms = int((time.time() - 30 * 86400) * 1000)  # 約 30 天前
fetcher.fetch_ohlcv(symbol, "1h", since=since_ms, limit=500)

# 拉取資金費率
fetcher.fetch_funding_rate(symbol, since=since_ms, limit=200)
```

### 緩存優先讀取（缺段自動補拉）

```python
# 讀取 [since, until] 區間，若本地有缺口會自動向交易所補拉
since_ms = int((time.time() - 7 * 86400) * 1000)
until_ms = int(time.time() * 1000)
rows = fetcher.get_ohlcv(
    symbol,
    "1h",
    since=since_ms,
    until=until_ms,
    fill_gaps=True,       # 缺失 K 線用前一根收盤價填充（filled=1）
    exclude_outliers=False  # 若 True 則排除插針標記的資料
)
print(f"共 {len(rows)} 根 K 線")
```

### 僅從本地緩存讀取（不發 API）

```python
cached = fetcher.get_cached_ohlcv(symbol, "1h", since_ms, until_ms, fill_gaps=True)
```

## 回測頁面與報告

在專案根目錄執行：

```bash
streamlit run app.py
```

瀏覽器會開啟回測頁面，可設定：

- **交易所**：Binance / Bybit  
- **標的**：永續合約代碼（如 `BTC/USDT:USDT`）  
- **K 線週期**、**開始/結束日期**  
- **策略**：雙均線交叉、買入持有、**RSI**、**MACD 交叉**、**布林帶**（各有參數可調）  
- **初始資金**、是否**排除插針資料**

執行後會顯示**回測報告**：總報酬、年化報酬、最大回撤、夏普、Sortino、Calmar、交易次數與勝率、權益曲線圖、交易明細表。

**找出最優策略**：側邊欄可選擇「優化目標」（夏普、總報酬、年化報酬、Calmar、Sortino、最小回撤），點擊「找出最優策略」後會**並行窮舉所有可能性**（所有策略 × 所有 K 線週期 × 各策略參數網格），以多進程加速計算，找出全局最優並顯示最優組合與各策略×K線的比較表。若在搜尋過程中關閉瀏覽器分頁或重新整理，終端可能會出現多筆 `WebSocketClosedError`，可忽略或重啟 `streamlit run app.py`。

## 專案結構

```
StocksX_V0/
├── app.py                    # Streamlit 回測頁面與報告
├── src/
│   ├── data/                 # 數據層（與回測引擎解耦）
│   │   ├── models.py         # OhlcvBar, FundingRateRecord 等領域模型
│   │   ├── storage/          # 儲存實作（目前為 SQLite）
│   │   │   ├── base.py       # MarketDataStorage 介面（Protocol）
│   │   │   └── sqlite_storage.py  # SQLiteMarketDataStorage
│   │   ├── sources/          # 外部資料來源
│   │   │   └── crypto_ccxt.py     # CcxtOhlcvSource, CcxtFundingSource
│   │   └── crypto/           # 加密貨幣專用組合服務與兼容層
│   │       ├── __init__.py   # 匯出 CryptoDataFetcher
│   │       ├── db.py         # SQLite schema/init
│   │       ├── fetcher.py    # 對外兼容層（舊 API），內部呼叫 service
│   │       ├── rate_limiter.py
│   │       └── service.py    # CryptoMarketDataService（緩存 + 缺口補齊 + 插針）
│   └── backtest/             # 回測引擎
│       ├── __init__.py
│       ├── engine.py         # run_backtest, BacktestResult
│       └── strategies.py     # sma_cross, buy_and_hold, rsi_signal, macd_cross, bollinger_signal
├── cache/                    # SQLite 緩存（crypto_cache.sqlite）
├── examples/
├── requirements.txt
└── README.md
```

## 數據存儲 Schema（SQLite）

- **ohlcv**：`exchange`, `symbol`, `timeframe`, `timestamp` (UTC 毫秒), `open`, `high`, `low`, `close`, `volume`, `filled`, `is_outlier`；主鍵 `(exchange, symbol, timeframe, timestamp)`。
- **funding_rates**：`exchange`, `symbol`, `timestamp`, `funding_rate`, `open_interest`, `mark_price`；主鍵 `(exchange, symbol, timestamp)`。

## 免責聲明與風險提示

- **數據差異**：不同交易所價格存在價差，回測結果僅代表該交易所之表現。
- **免費限制**：歷史數據深度可能受限（例如部分交易所分鐘級數據年份有限），請以各交易所官方說明為準。
- **免費數據可能存在誤差，實盤交易請以交易所為準。** 本模塊僅供學習與回測研究使用。

## 授權

依專案設定為準。
