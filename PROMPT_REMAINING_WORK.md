# StocksX V0 — 剩餘任務完整 Prompt

> 複製以下內容，直接發給任何 LLM（Claude / GPT-4 / Gemini），它會接手繼續開發。

---

```
你是 StocksX V0 專案的高級量化工程師。請接手完成 Phase 4 收尾 + 批量實作 130 策略。

## 專案概況

StocksX 是一個機構級量化交易平台，使用 Python + Streamlit + FastAPI。
倉庫路徑：/root/.openclaw/workspace/StocksX_V0

核心目錄結構：
```
src/
├── backtest/
│   ├── strategies.py            # 主策略文件（已有 18 個策略）
│   ├── strategies_vectorized.py # 向量化版本（已有 ~12 個）
│   ├── advanced_strategies.py   # 進階策略（已有 5 個）
│   ├── engine.py / engine_vec.py
│   ├── indicators.py            # 技術指標庫
│   └── ...
├── strategies/
│   ├── ml_strategies/           # LSTM、配對交易
│   ├── nlp_strategies/          # 情緒分析
│   ├── quant_strategies/        # 多因子、配對
│   ├── rl_strategies/           # DQN、交易環境
│   └── regime_detection.py      # 市場狀態檢測
├── data/sources/                # 數據源
│   ├── crypto_ccxt.py           # 加密貨幣 (CCXT)
│   ├── yfinance_source.py       # Yahoo Finance
│   ├── twse_source.py           # 台股
│   ├── a_stock_source.py        # A 股
│   ├── hk_stock_source.py       # 港股
│   ├── glassnode.py             # (在 data/onchain/) 鏈上數據
│   └── api_hub.py               # 數據源聚合
└── trading/
    ├── orders/advanced_orders.py # 5 種高級訂單 ✅
    ├── portfolio/optimization.py # 4 種組合優化 ✅
    └── arbitrage/                # 4 種套利策略 ✅
```

已有策略（在 strategies.py 中，每個函數接收 rows: list[dict] 返回 list[int] 信號）：
sma_cross, buy_and_hold, rsi_signal, macd_cross, bollinger_signal, ema_cross,
donchian_channel, supertrend, dual_thrust, vwap_reversion, ichimoku, stochastic,
williams_r, adx_trend, parabolic_sar, mean_reversion_zscore, momentum_roc, keltner_channel

所有策略遵循同一簽名規範：
```python
def strategy_name(rows: list[dict[str, Any]], **params) -> list[int]:
    """
    Args:
        rows: OHLCV 數據列表，每個元素包含 open/high/low/close/volume
    Returns:
        信號列表：1=做多, -1=做空, 0=無操作
    """
```

向量化版本在 strategies_vectorized.py 中使用 pandas/numpy，簽名相同但內部用 DataFrame 向量運算。

indicators.py 包含常用技術指標工具函數（SMA, EMA, RSI, MACD, ATR, Bollinger, Stochastic 等），策略中可直接 import 使用。

---

## 任務一：補完剩餘數據源（8 個）

在 src/data/sources/ 目錄下新建以下數據源模組。每個數據源需要：
1. 繼承或遵循 api_hub.py 中的 BaseSource 介面模式
2. 實現 fetch_ohlcv(symbol, timeframe, start, end) → pd.DataFrame
3. 實現 fetch_ticker(symbol) → dict
4. 包含錯誤處理、重試邏輯、速率限制
5. 在 api_hub.py 中註冊

### 待建數據源：

1. **alpha_vantage_source.py** — Alpha Vantage（美股/外匯/商品）
   - 免費 API，5 calls/min 限制
   - 支援日線/週線/月線
   - 函數：fetch_ohlcv, fetch_intraday, search_symbol

2. **polygon_source.py** — Polygon.io（美股/期權/外匯）
   - 支援分時數據
   - 函數：fetch_ohlcv, fetch_trades, fetch_snapshots

3. **fred_source.py** — FRED 經濟數據
   - 美聯儲經濟數據：GDP、CPI、利率、失業率
   - 函數：fetch_series, fetch_releases, search_series
   - 用於宏觀策略

4. **binance_ws_source.py** — 幣安 WebSocket 即時數據
   - 實時 K 線推送
   - 函數：subscribe_klines, subscribe_tickers, subscribe_trades
   - 使用 websocket-client 或 websockets 庫

5. **coingecko_source.py** — CoinGecko 數據
   - 免費 API，無需 API Key
   - 歷史價格、市值、社群數據
   - 函數：fetch_ohlcv, fetch_market_data, fetch_coin_info

6. **defi_source.py** — DeFi 協議數據
   - DefiLlama API（TVL、收益率）
   - 函數：fetch_tvl, fetch_yields, fetch_protocol_tvl
   - 用於 DeFi 策略

7. **tushare_source.py** — Tushare Pro（A 股/港股/期貨/基金）
   - 中國市場專業數據
   - 日線/分鐘線/龍虎榜/資金流
   - 函數：fetch_ohlcv, fetch_money_flow, fetch_dragon_tiger

8. **csv_source.py** — 本地 CSV 數據源
   - 導入本地 CSV 歷史數據
   - 自動偵測欄位名（date/open/high/low/close/volume）
   - 支援多種日期格式
   - 函數：load_csv, load_directory, fetch_ohlcv

---

## 任務二：批量實作 130 策略

現有 18 個，需新增約 112 個。按類別批次實作，每個策略需：
1. 在 strategies.py 中新增函數（遵循現有簽名）
2. 在 strategies_vectorized.py 中新增向量化版本（可選擴展）
3. 在 get_signal() 註冊表中添加映射
4. 含 docstring 說明原理和參數

### 批次 1：趨勢跟隨補全（+12，已有 6）

已有：sma_cross, ema_cross, macd, adx, supertrend, parabolic_sar
待建：
- aroon_indicator — Aroon Up/Down 交叉
- dmi_directional — +DI/-DI 方向運動
- ema_ribbon — 多條 EMA 帶狀
- turtle_trading — 海龜交易法（20日突破 + ATR止損）
- cci_signal — CCI 商品通道
- hull_ma — Hull 移動平均（已有advanced版，需加主策略版）
- t3_average — T3 均線
- kama — Kaufman 自適應均線
- tillson_t3 — Tillson T3
- zlema — 零滯後 EMA
- tema — 三重指數移動平均

### 批次 2：振盪器補全（+11，已有 5）

已有：rsi, stochastic, williams_r, bollinger, ichimoku
待建：
- stochastic_rsi — RSI 上的隨機運算
- awesome_oscillator — 5期/34期中點均線差
- chande_momentum — Chande 動量振盪
- fisher_transform — Fisher 變換
- dpo — 去趨勢價格振盪
- ulcer_index — 潰瘍指數
- vortex_indicator — Vortex 振盪
- elder_ray — Bull Power / Bear Power
- mass_index — 質量指數
- trix — 三重平滑 ROC
- klinger_oscillator — Klinger 成交量振盪

### 批次 3：突破與均值回歸補全（+14，已有 2）

已有：donchian_channel, vwap_reversion
待建：
- dual_thrust_strategy — 雙推力突破（已有，需標準化）
- orb_breakout — 開盤區間突破
- pivot_breakout — 樞軸點突破
- bollinger_squeeze — 布林帶擠壓
- fibonacci_breakout — 斐波那契回撤突破
- volume_breakout — 成交量確認突破
- cup_and_handle — 杯柄形態
- triple_top_bottom — 三重頂底突破
- nr7_nr4 — 窄幅K線突破
- tto_breakout — Toby Crabel 開盤突破
- horizontal_channel — 水平通道突破
- flag_pennant — 旗形/三角旗形
- wm_pattern — W底/M頂突破
- sideways_reversion — 橫盤均值回歸

### 批次 4：AI / 機器學習（+11，已有 5）

已有：LSTM, 情緒分析, 多因子, 配對交易, DQN RL
待建：
- transformer_predict — Transformer 預測
- genetic_optimize — 遺傳演算法策略優化
- ensemble_voting — 集成學習投票
- gnn_asset_relation — 圖神經網路資產關聯
- gan_price_gen — GAN 價格場景生成
- anomaly_detection — 異常行情偵測
- online_learning — 在線學習策略
- bayesian_optimize — 貝葉斯超參數優化
- nlp_event_driven — NLP 事件驅動
- transfer_learning — 遷移學習
- contrastive_learning — 對比學習市場狀態

### 批次 5：風險管理（+12，全新類別）

- kelly_criterion — 凱利公式倉位
- fixed_fractional — 固定分數法
- volatility_position — 波動率反向倉位
- max_drawdown_circuit — 最大回撤熔斷
- correlation_monitor — 持倉相關性監控
- anti_martingale — Anti-Martingale
- fixed_ratio — 固定比率法
- risk_parity_signal — 風險平價信號
- cvar_position — CVaR 倉位控制
- optimal_stop — 最優停損
- tail_risk_hedge — 尾部風險對沖
- delta_neutral — Delta 中性對沖

### 批次 6：微結構與訂單流（+12，全新類別）

- order_flow — 訂單流分析
- delta_cumulative — Delta 累積
- poc_value_area — POC / Value Area
- twap_signal — TWAP 執行信號
- iceberg_detect — 冰山訂單偵測
- vpin — VPIN 知情交易機率
- amihud_illiquidity — Amihud 非流動性
- kyle_lambda — Kyle's Lambda
- tick_rule — Lee-Ready Tick Rule
- quote_stuffing — Quote Stuffing 偵測
- level2_analysis — Level 2 深度分析
- micro_price — 微價格偏移

### 批次 7：跨市場與宏觀（+12，全新類別）

- carry_trade — 利差交易
- seasonal_strategy — 季節性效應
- cross_commodity_spread — 跨品種價差
- dxy_correlation — 美元指數聯動
- hedge_ratio_dynamic — 動態避險比率
- yield_curve — 收益率曲線策略
- country_rotation — 跨國權益輪動
- commodity_super_cycle — 商品超級週期
- vix_trading — VIX 期貨交易
- credit_spread — 信用利差交易
- gold_real_rate — 黃金/實際利率
- cross_asset_risk_parity — 跨資產風險平價

### 批次 8：計量統計（+10，全新類別）

- cointegration_pair — 協整配對檢驗
- kalman_filter — Kalman 濾波追蹤
- garch_volatility — GARCH 波動率模型
- markov_regime — 馬可夫體制轉換
- wavelet_analysis — 小波多尺度分解
- arfima — 分數差分 ARFIMA
- copula_dependence — Copula 相依結構
- sde_mean_reversion — SDE 均值回歸
- bootstrap_confidence — Bootstrap 信心區間
- changepoint_detection — 變點偵測 CUSUM/Bayesian

### 批次 9：圖表形態（+10，全新類別）

- head_shoulders — 頭肩頂底
- wedge_pattern — 楔形收斂/擴張
- diamond_pattern — 鑽石頂底
- gap_fill — 跳空回補
- candlestick_patterns — K 線組合（十字星/吞沒/晨星等）
- elliott_wave — Elliott 波浪計數
- harmonic_patterns — 諧波模式（Gartley/Butterfly/Bat/Crab）
- wyckoff_method — Wyckoff 方法
- market_structure — 市場結構 HH/HL/LL/LH
- volume_profile_shape — Volume Profile 形態

### 批次 10：高頻執行（+8，全新類別）

- market_making — 做市策略
- stat_arb_execution — 統計套利執行
- latency_arb — 延遲套利
- flash_crash_detect — 閃崩偵測+反向
- vwap_twap_exec — VWAP/TWAP 被動執行
- implementation_shortfall — Implementation Shortfall
- sniper_strategy — Sniper 大單追蹤
- etf_nav_arb — ETF NAV 套利

---

## 實作規範

### 策略函數簽名
```python
def strategy_name(rows: list[dict[str, Any]], param1: type = default, ...) -> list[int]:
    """
    一句話說明策略原理。
    
    Args:
        rows: OHLCV 數據，每元素含 open/high/low/close/volume/datetime
        param1: 參數說明
    Returns:
        list[int]: 1=買入, -1=賣出, 0=持有
    """
    closes = np.array([r['close'] for r in rows])
    highs = np.array([r['high'] for r in rows])
    lows = np.array([r['low'] for r in rows])
    volumes = np.array([r['volume'] for r in rows])
    n = len(closes)
    
    signals = [0] * n
    # ... 策略邏輯 ...
    return signals
```

### 向量化版本簽名
```python
def strategy_name_vec(rows: list[dict[str, Any]], ...) -> list[int]:
    df = pd.DataFrame(rows)
    # 使用 pandas 向量運算
    return signals.tolist()
```

### 註冊到 get_signal
```python
# 在 strategies.py 的 get_signal() 中添加：
STRATEGY_MAP = {
    'sma_cross': sma_cross,
    'rsi_signal': rsi_signal,
    # ... 現有 ...
    'aroon_indicator': aroon_indicator,  # 新增
    # ...
}

def get_signal(strategy: str, rows: list[dict[str, Any]], **kwargs) -> list[int]:
    func = STRATEGY_MAP.get(strategy)
    if func is None:
        raise ValueError(f"未知策略: {strategy}")
    return func(rows, **kwargs)
```

### 數據源簽名
```python
class NewSource:
    """數據源描述"""
    
    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = '1d',
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Returns:
            DataFrame with columns: datetime, open, high, low, close, volume
        """
        ...
    
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        ...
```

---

## 執行要求

1. **先做任務一**（數據源），因為策略依賴數據
2. **然後按批次 1→10 依序做策略**
3. 每完成一個批次，**立即執行測試**確認語法正確：
   ```bash
   python3 -c "import ast; ast.parse(open('file.py').read()); print('OK')"
   ```
4. 每完成一個批次，**git commit + push**
5. 所有策略使用 numpy 向量化運算，避免 Python for 迴圈
6. 複雜策略（AI/ML 類）可提供骨架 + 接口，實際模型訓練作為 TODO
7. 如遇到需要第三方庫的策略（如 statsmodels, ta-lib），嘗試用 numpy 手動實現核心邏輯，避免新增依賴

---

## 驗收標準

- [ ] 15 個數據源全部就位，api_hub.py 能統一調用
- [ ] 130+ 策略全部在 get_signal() 註冊表中可查
- [ ] 每個策略函數有完整 docstring
- [ ] 所有文件通過 ast.parse 語法檢查
- [ ] git commit 歷史清晰，每批次一個 commit
```
