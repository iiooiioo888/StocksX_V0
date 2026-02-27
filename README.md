# StocksX — 通用回測平台

跨市場策略回測平台，支援加密貨幣、美股、台股、ETF、期貨、指數。內建 10 種交易策略、23 個交易所手續費資料庫、即時策略監控、用戶系統與管理員後台。

## 功能總覽

### 📊 回測引擎
- **10 種策略**：雙均線交叉、EMA 交叉、MACD 交叉、RSI、布林帶、唐奇安通道、超級趨勢、雙推力、VWAP 回歸、買入持有
- **Mark-to-Market**：權益曲線即時反映未實現盈虧
- **手續費系統**：23 個交易所/協議費率（CEX、DEX、傳統市場），含滑點模擬
- **批量最優搜尋**：窮舉 策略 × K線週期 × 參數，找出全局最優組合
- **自訂策略參數**：每個策略的參數均可在 UI 中調整

### 🌍 多市場支援

| 大類 | 細類 | 數據來源 |
|------|------|----------|
| ₿ 加密貨幣 | 主流永續、主流現貨、DeFi、Layer2/新幣、Meme | CCXT（11 交易所） |
| 🏛️ 傳統市場 | 美股、台股、ETF、期貨/商品、指數 | Yahoo Finance |

**支援交易所**：OKX、Bitget、Gate.io、KuCoin、MEXC、HTX、BingX、WOO X、Crypto.com、Binance*、Bybit*（*受地區限制，自動回退）

## 數據 API 申請與來源

以下是依「數據類型」分類的主要 API 來源，方便日後擴充實盤數據或宏觀/情緒指標：

### API Key 設定與統一入口

- **環境變數 / .env**：  
  - 所有外部 API 金鑰一律走環境變數，建議在專案根目錄建立 `.env`（不納入 git）並搭配 `python-dotenv` 自動載入。  
  - 主要變數名稱（對應上列服務）：  
    - `FRED_API_KEY`  
    - `TRADING_ECONOMICS_API_KEY`  
    - `COINGECKO_API_KEY`  
    - `COINMARKETCAP_API_KEY`  
    - `GLASSNODE_API_KEY`  
    - `ALPHA_VANTAGE_API_KEY`  
    - `FMP_API_KEY`  
    - `POLYGON_API_KEY`  
    - `ALPACA_API_KEY` / `ALPACA_API_SECRET`  
    - `DASHSCOPE_API_KEY`（Qwen AI，用於 `src/ai/qwen_client.py`）
- **程式端入口**：  
  - 統一由 `src/config_secrets.py` 讀取與檢查金鑰，避免在各模組重複處理。  
  - 數據抓取函式集中在 `src/data/sources/api_hub.py`，例如：  
    - `fetch_fred_series(...)`  
    - `fetch_alpha_vantage(...)`  
    - `fetch_polygon(...)`  
    - `fetch_coingecko(...)`  
    - `fetch_coinmarketcap(...)`  
    - `fetch_glassnode(...)`  
    - `fetch_trading_economics(...)`  
    - `fetch_polymarket_markets(...)`

### 1. 宏觀經濟數據 (Macro Economic)

- **FRED (Federal Reserve Economic Data)**  
  - **網址**：[`https://fred.stlouisfed.org/`](https://fred.stlouisfed.org/)  
  - **費用**：免費（需註冊 API Key）  
  - **數據**：美國 CPI、非農就業、利率、GDP 等權威宏觀數據。
- **TradingEconomics**  
  - **網址**：[`https://tradingeconomics.com/`](https://tradingeconomics.com/)  
  - **費用**：有限免費 / 付費  
  - **數據**：全球各國宏觀指標與經濟日曆。

### 2. 加密貨幣市場與鏈上數據 (Crypto & On-Chain)

- **CoinGecko**  
  - **網址**：[`https://www.coingecko.com/`](https://www.coingecko.com/)  
  - **費用**：免費層級有限 / 付費  
  - **數據**：代幣價格、市值、交易量等基本市場數據。
- **CoinMarketCap**  
  - **網址**：[`https://coinmarketcap.com/`](https://coinmarketcap.com/)  
  - **費用**：免費層級有限 / 付費  
  - **數據**：代幣價格、排名、交易所資訊。
- **Glassnode**  
  - **網址**：[`https://glassnode.com/`](https://glassnode.com/)  
  - **費用**：免費層級有限 / 付費  
  - **數據**：鏈上指標（活躍地址、哈希率、MVRV 等）。

### 3. 股市與綜合金融數據 (Stocks & General)

- **Alpha Vantage**  
  - **網址**：[`https://www.alphavantage.co/`](https://www.alphavantage.co/)  
  - **費用**：免費（有每日呼叫上限）/ 付費  
  - **數據**：美股、匯率、常用技術指標。
- **Financial Modeling Prep (FMP)**  
  - **網址**：[`https://financialmodelingprep.com/`](https://financialmodelingprep.com/)  
  - **費用**：免費層級有限 / 付費  
  - **數據**：財報、股價、部分經濟數據。
- **Polygon.io**  
  - **網址**：[`https://polygon.io/`](https://polygon.io/)  
  - **費用**：免費層級有限 / 付費  
  - **數據**：美股、外匯、加密的即時與歷史數據。

### 4. 券商交易接口 (Brokerage API)

- **Interactive Brokers (IBKR)**  
  - **網址**：[`https://www.interactivebrokers.com/`](https://www.interactivebrokers.com/)  
  - **費用**：需開戶（市場數據可能需額外付費）  
  - **數據**：全球市場即時行情與下單交易接口。
- **Alpaca**  
  - **網址**：[`https://alpaca.markets/`](https://alpaca.markets/)  
  - **費用**：免費（美股）  
  - **數據**：美股即時數據與交易（適合程式交易 / 模擬帳戶）。

### 5. 情緒與另類數據 (Sentiment & Alternative)

- **Alternative.me — Crypto Fear & Greed Index**  
  - **網址**：[`https://alternative.me/crypto/fear-and-greed-index/`](https://alternative.me/crypto/fear-and-greed-index/)  
  - **費用**：免費（無需 API Key，直接存取 URL）  
  - **數據**：加密貨幣恐懼與貪婪情緒指標。
- **CBOE**  
  - **網址**：[`https://www.cboe.com/`](https://www.cboe.com/)  
  - **費用**：部分公開 / 付費  
  - **數據**：VIX 波動率指數與相關衍生商品數據。

### 6. 預測市場 (Prediction Markets)

- **Polymarket / Gamma API**  
  - **Base URL**：[`https://gamma-api.polymarket.com`](https://gamma-api.polymarket.com)  
  - **權限**：公開市場數據無需 API Key，下單/持倉相關需錢包簽名。  
  - **限制**：有頻率限制，實務上建議在應用端增加快取（例如記憶體 / SQLite / Redis）。  
  - **數據內容**：事件概率、成交量、開盤/結算狀態、結果等。  
  - **常見端點**（社群整理，非官方文件）：  
    - 取得市場列表：`GET /markets`  
    - 取得事件詳情：`GET /events/{id}`  
    - 取得使用者相關通知/持倉：`GET /notifications`（需認證）  
  - **Python 抓取範例**（簡化版）：

    ```python
    import requests
    from typing import List, Dict, Any

    BASE_URL = "https://gamma-api.polymarket.com"

    def get_polymarket_markets(query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """從 Polymarket Gamma API 抓取市場列表（僅示意用）"""
        url = f"{BASE_URL}/markets"
        params = {"limit": limit}
        if query:
            params["search"] = query

        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # 依常見欄位做基本整理（實際欄位可能會有變動）
        markets: List[Dict[str, Any]] = []
        for m in data:
            markets.append(
                {
                    "title": m.get("title"),
                    "yes_bid": m.get("yesBid"),
                    "volume": m.get("volume"),
                    "status": m.get("status"),
                }
            )
        return markets
    ```

  - **整合建議**：  
    - 可在 `MARKET_HIERARCHY` 中新增一個大類，例如：  
      - `🎲 預測市場` → `加密事件 / 宏觀事件` 等子分類，只儲存自定義代碼（例如 `POLY_BTC_100K`）與顯示名稱。  
    - 在數據層以這些代碼對應到實際 Polymarket 查詢條件或市場 ID，由獨立模組（例如 `src/data/sources/polymarket.py`）負責呼叫 Gamma API 並轉換成平台統一格式。  
    - 需注意端點屬「非官方文件」，可能隨時間變動，建議加上錯誤處理與快取機制。

### 📈 互動圖表
- Plotly K 線圖（Candlestick）+ 成交量 + 買賣點標記
- 多策略權益曲線對比
- 回撤分析圖
- 交易損益分佈直方圖
- 持倉時長分佈圖
- 每日報酬率熱力圖
- 策略信號視覺化

### 👤 用戶系統
- 註冊/登入（PBKDF2 密碼雜湊、帳號鎖定、Rate Limiting）
- 回測歷史自動保存、備註標籤
- 策略收藏 & 對比圖
- 策略參數預設儲存/載入
- 回測提醒（報酬率/回撤/夏普閾值通知）
- 偏好設定、修改密碼

### 📡 策略監控
- 訂閱任意交易對 × 策略組合
- 即時價格、策略信號、持倉狀態
- 帳戶價值 & 未實現 P&L 追蹤
- 暫停/啟用/刪除訂閱

### 🛠️ 管理員後台
- 系統統計（用戶數、回測數、熱門標的）
- 用戶 CRUD（新增、修改角色、重設密碼、停用、刪除）
- 安全日誌（登入記錄、失敗次數）
- 數據快取管理

### 🔒 安全防護
- PBKDF2 密碼雜湊（100k 迭代）
- 登入失敗 5 次鎖定 5 分鐘
- 輸入消毒（XSS/SQL Injection 防護）
- Session 1 小時自動過期
- Rate Limiting（登入 10次/分、註冊 5次/5分）

## 安裝

```bash
pip install -r requirements.txt
```

依賴：`ccxt`、`streamlit`、`pandas`、`plotly`、`yfinance`、`python-dotenv`、`dashscope`（可選）

## 啟動

```bash
streamlit run app.py
```

瀏覽器開啟後：
1. 預設管理員帳號：`admin` / `admin123`
2. 選擇市場大類（加密貨幣 / 傳統市場）→ 細類 → 交易對
3. 點擊「🚀 執行回測」

## 專案結構

```
StocksX_V0/
├── app.py                        # 多頁面入口（Landing Page）
├── pages/
│   ├── 1_🔐_登入.py              # 登入/註冊
│   ├── 2_📊_回測.py              # 回測主頁（10策略、K線圖、績效分析）
│   ├── 3_📜_歷史.py              # 回測歷史、收藏、預設、提醒、設定
│   ├── 4_🛠️_管理.py             # 管理員後台
│   └── 5_📡_監控.py              # 策略訂閱 & 即時監控
├── src/
│   ├── auth/                     # 用戶認證系統
│   │   └── user_db.py            # SQLite 用戶 DB、登入日誌、Rate Limiting
│   ├── backtest/                 # 回測引擎
│   │   ├── engine.py             # 回測核心（含手續費、Mark-to-Market）
│   │   ├── strategies.py         # 10 種交易策略
│   │   ├── optimizer.py          # 批量最優搜尋
│   │   └── fees.py               # 23 交易所手續費資料庫
│   ├── data/                     # 數據層
│   │   ├── crypto/               # 加密貨幣數據（CCXT + SQLite 快取）
│   │   ├── traditional/          # 傳統市場數據（Yahoo Finance + SQLite 快取）
│   │   ├── sources/              # 數據來源（CCXT、yfinance）
│   │   ├── storage/              # SQLite 儲存層
│   │   └── live.py               # 即時價格 & 策略信號
│   └── ai/                       # Qwen AI 客戶端（可選）
├── cache/                        # SQLite 快取（gitignored）
├── requirements.txt
├── AGENTS.md                     # Cloud Agent 開發指引
└── README.md
```

## 交易策略

| 策略 | 類型 | 說明 |
|------|------|------|
| 雙均線交叉 | 趨勢 | 快慢 SMA 交叉做多空 |
| EMA 交叉 | 趨勢 | 指數均線交叉，反應更快 |
| MACD 交叉 | 趨勢 | MACD 線與信號線交叉 |
| RSI | 擺盪 | 超買賣反轉信號 |
| 布林帶 | 均值回歸 | 突破上下軌反向交易 |
| 唐奇安通道 | 突破 | N 期高低突破做多空 |
| 超級趨勢 | 趨勢 | 基於 ATR 的動態趨勢帶 |
| 雙推力 | 突破 | 開盤價 ± Range 突破 |
| VWAP 回歸 | 均值回歸 | 偏離成交量加權均價反轉 |
| 買入持有 | 基準 | 持續持有作為對照基準 |

## 手續費

回測引擎支援真實手續費模擬，每筆交易扣除 `(手續費 + 滑點) × 2`（開倉+平倉）。

內建 23 個交易所/協議費率：
- **CEX**：Binance 0.04%、OKX 0.05%、MEXC 0.03%…
- **DEX**：Uniswap 0.3%、Curve 0.04%、GMX 0.07%…
- **DEX-Perp**：dYdX 0.05%、Hyperliquid 0.035%…
- **傳統**：美股零佣金、台股 0.1425%+0.3%稅

## 免責聲明

本專案僅供學習與回測研究使用，不構成投資建議。回測結果基於歷史數據，不代表未來表現。實盤交易請以交易所為準。

## 授權

依專案設定為準。
