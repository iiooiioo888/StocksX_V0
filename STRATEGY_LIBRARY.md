# 📚 StocksX 策略庫完整文檔

**版本**: 2.0.0  
**最後更新**: 2026-03-23  
**策略總數**: 130  
**測試通過率**: 130/130 (100%)  

---

## 📋 目錄

1. [概述](#概述)
2. [架構設計](#架構設計)
3. [策略分類總覽](#策略分類總覽)
4. [趨勢跟隨與動量（17 策略）](#1-趨勢跟隨與動量17-策略)
5. [超買超賣振盪器（16 策略）](#2-超買超賣振盪器16-策略)
6. [突破與均值回歸（16 策略）](#3-突破與均值回歸16-策略)
7. [AI/機器學習（16 策略）](#4-ai機器學習16-策略)
8. [風險管理（9 策略）](#5-風險管理9-策略)
9. [微結構與訂單流（11 策略）](#6-微結構與訂單流11-策略)
10. [跨市場與宏觀（12 策略）](#7-跨市場與宏觀12-策略)
11. [進階計量與統計（10 策略）](#8-進階計量與統計10-策略)
12. [形態與圖表模式（10 策略）](#9-形態與圖表模式10-策略)
13. [執行演算法與高頻（13 策略）](#10-執行演算法與高頻13-策略)
14. [使用指南](#使用指南)
15. [回測結果](#回測結果)

---

## 概述

StocksX 策略庫包含 **130 個專業量化交易策略**，涵蓋 10 大類別，從經典技術指標到前沿 AI/ML 模型。所有策略：

- ✅ 繼承自 `BaseStrategy` 基類
- ✅ 實現 `generate_signals()` 和 `calculate_position_size()` 方法
- ✅ 通過策略工廠統一管理
- ✅ 支援參數配置和回測
- ✅ 100% 功能測試通過

### 核心設計原則

```
BaseStrategy (抽象基類)
├── TrendFollowingStrategy    → 趨勢策略基類
├── OscillatorStrategy        → 振盪器策略基類
├── BreakoutStrategy          → 突破策略基類
├── MeanReversionStrategy     → 均值回歸基類
├── AIMLStrategy              → AI/ML 策略基類
└── RiskManagementStrategy    → 風險管理基類
```

### 策略接口

```python
class BaseStrategy(ABC):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        Returns: Series (1=買入, -1=賣出, 0=持有)
        """
    
    def calculate_position_size(self, signal: int, capital: float,
                                 price: float, volatility: float) -> float:
        """
        計算倉位大小
        Returns: 倉位數量
        """
```

---

## 架構設計

### 目錄結構

```
src/strategies/
├── __init__.py              # 策略庫入口（導出所有策略）
├── base_strategy.py         # 基類定義（6 個基類）
├── strategy_factory.py      # 策略工廠（統一管理）
├── regime_detection.py      # 市場體制偵測
│
├── trend/                   # 趨勢策略（17 個）
│   ├── advanced_trend_strategies.py  # 進階趨勢
│   ├── hull_ma_strategy.py           # Hull MA / TEMA 等
│   └── trend_complete.py             # SMA/EMA/MACD 等
│
├── oscillator/              # 振盪器策略（16 個）
│   ├── advanced_oscillators.py       # 進階振盪器
│   ├── complete_oscillators.py       # 完整振盪器
│   └── final_oscillators.py          # 最終批次
│
├── breakout/                # 突破策略（16 個）
│   ├── breakout_strategies.py        # 突破策略集 1
│   ├── breakout_strategies_complete.py # 完整突破
│   └── breakout_final.py             # 最終突破
│
├── ai_ml/                   # AI/ML 策略（16 個）
│   ├── ai_strategies.py              # 基礎 AI
│   ├── ai_complete.py                # 完整 AI
│   └── ai_final.py                   # 最終 AI
│
├── risk_management/         # 風險管理（9 個）
│   ├── risk_strategies.py            # 基礎風險
│   └── advanced_risk_strategies.py   # 進階風險
│
├── microstructure/          # 微結構（11 個）
│   └── micro_strategies.py
│
├── macro/                   # 宏觀策略（12 個）
│   ├── macro_strategies.py           # 宏觀策略集 1
│   └── macro_complete.py             # 完整宏觀
│
├── statistical/             # 統計策略（10 個）
│   ├── stat_strategies.py            # 統計策略集 1
│   └── stat_complete.py              # 完整統計
│
├── pattern/                 # 形態策略（10 個）
│   ├── pattern_strategies.py         # 形態策略集 1
│   └── pattern_complete.py           # 完整形態
│
└── execution/               # 執行算法（13 個）
    ├── execution_strategies.py       # 執行策略集 1
    ├── execution_complete.py         # 完整執行
    └── execution_final.py            # 最終執行
```

### 策略工廠

```python
from strategies import get_strategy, list_all_strategies

# 創建策略
rsi = get_strategy('multi_rsi', {'period': 14})
macd = get_strategy('macd_cross', {'fast': 12, 'slow': 26, 'signal': 9})

# 列出所有策略
all_strats = list_all_strategies()
print(f"共 {len(all_strats)} 個策略")
```

---

## 策略分類總覽

| # | 類別 | 策略數 | 程式碼行數 | 描述 |
|---|------|--------|-----------|------|
| 1 | 趨勢跟隨與動量 | 17 | ~2,400 | SMA/EMA/MACD/ADX/Supertrend 等 |
| 2 | 超買超賣振盪器 | 16 | ~3,100 | RSI/Stochastic/RSI Stochastic 等 |
| 3 | 突破與均值回歸 | 16 | ~2,000 | Bollinger/Donchian/Fibonacci 等 |
| 4 | AI/機器學習 | 16 | ~2,500 | LSTM/GNN/GAN/Transformer 等 |
| 5 | 風險管理 | 9 | ~1,600 | Kelly/CVaR/Delta Hedge 等 |
| 6 | 微結構與訂單流 | 11 | ~640 | Order Flow/VPIN/Iceberg 等 |
| 7 | 跨市場與宏觀 | 12 | ~940 | Carry Trade/季節性/VIX 等 |
| 8 | 進階計量與統計 | 10 | ~930 | Cointegration/GARCH/Kalman 等 |
| 9 | 形態與圖表模式 | 10 | ~780 | Head & Shoulders/Elliott 等 |
| 10 | 執行演算法與高頻 | 13 | ~1,300 | Market Making/Stat Arb 等 |
| | **合計** | **130** | **~16,040** | |

---

## 1. 趨勢跟隨與動量（17 策略）

### 基礎趨勢（8 策略）

| # | 策略名 | 鍵名 | 基類 | 核心參數 | 說明 |
|---|--------|------|------|---------|------|
| 1 | SMA 均線交叉 | `sma_cross` | Trend | short=10, long=30 | 短/長 SMA 金叉死叉 |
| 2 | EMA 指數交叉 | `ema_cross` | Trend | short=12, long=26 | EMA 金叉死叉，更敏感 |
| 3 | MACD 交叉 | `macd_cross` | Trend | fast=12, slow=26, sig=9 | MACD 線與信號線交叉 |
| 4 | ADX 趨勢強度 | `adx` | Trend | period=14, threshold=25 | DI+/DI- 方向判斷 |
| 5 | Supertrend | `supertrend` | Trend | period=10, mult=3.0 | ATR 趨勢通道 |
| 6 | Parabolic SAR | `parabolic_sar` | Trend | af=0.02, step=0.02, max=0.2 | 拋物線停損反轉 |
| 7 | Donchian 通道 | `donchian` | Trend | period=20 | N日高低點突破 |
| 8 | VWAP 均值回歸 | `vwap_reversion` | Trend | std=2.0, lookback=20 | VWAP ±nσ 通道 |

### 進階趨勢（9 策略）

| # | 策略名 | 鍵名 | 基類 | 核心參數 | 說明 |
|---|--------|------|------|---------|------|
| 9 | Hull MA | `hull_ma` | Trend | period=20 | 零滯後移動平均 |
| 10 | T3 均線 | `t3` | Trend | period=5, vfactor=0.7 | 平滑 T3 均線 |
| 11 | KAMA 自適應 | `kama` | Trend | period=30, fast=2, slow=30 | 效率比率自適應 |
| 12 | Tillson T3 | `tillson_t3` | Trend | period=8, vfactor=0.7 | Tillson 版 T3 |
| 13 | ZLEMA 零滯後 | `zlema` | Trend | period=20 | 去除滯後的 EMA |
| 14 | TEMA 三重指數 | `tema` | Trend | period=20 | 三重 EMA 平滑 |
| 15 | 均線帶 Ribbon | `ribbon` | Trend | periods=[5,10,20,30,50] | 多條均線排列 |
| 16 | 海龜交易法 | `turtle` | Trend | fast=20, slow=55, atr=20 | Donchian + ATR 倉位 |
| 17 | CCI 商品通道 | `cci` | Trend | period=20 | CCI 趨勢信號 |

### 使用範例

```python
# SMA 交叉策略
strategy = get_strategy('sma_cross', {'short_period': 10, 'long_period': 30})
signals = strategy.generate_signals(data)

# Supertrend 策略
strategy = get_strategy('supertrend', {'period': 10, 'multiplier': 3.0})
signals = strategy.generate_signals(data)
```

---

## 2. 超買超賣振盪器（16 策略）

| # | 策略名 | 鍵名 | 基類 | 核心參數 | 說明 |
|---|--------|------|------|---------|------|
| 1 | RSI 相對強弱 | `multi_rsi` | Osc | period=14, ob=70, os=30 | 經典 RSI 超買超賣 |
| 2 | Stochastic | `adaptive_kd` | Osc | k=14, d=3, smooth=3 | 自適應 KD 隨機指標 |
| 3 | Stochastic RSI | `stoch_rsi` | Osc | rsi_period=14, stoch=14 | RSI 的隨機化版本 |
| 4 | MACD 振盪 | `bollinger_pct_b` | Osc | fast=12, slow=26 | Bollinger %B 振盪 |
| 5 | CCI 商品通道 | `custom_oscillator` | Osc | period=20 | 自定義振盪器 |
| 6 | Williams %R | `awesome` | Osc | period=14 | Awesome Oscillator |
| 7 | Chande 動量 | `chande_momentum` | Osc | period=14 | Chande 動量振盪 |
| 8 | Fisher Transform | `fisher` | Osc | period=9 | Fisher 變換 |
| 9 | DPO 去趨勢 | `dpo` | Osc | period=20 | 去趨勢價格振盪 |
| 10 | Ulcer Index | `ulcer_index` | Osc | period=14 | 潰瘍指數 |
| 11 | Vortex 振盪 | `vortex` | Osc | period=14 | Vortex 指標 |
| 12 | Elder Ray | `elder_ray` | Osc | period=13 | Bull/Bear Power |
| 13 | Mass Index | `mass_index` | Osc | period=25, ema=9 | 質量指數 |
| 14 | TRIX | `trix` | Osc | period=15, signal=9 | TRIX 三重平滑 |
| 15 | Klinger 振盪 | `klinger` | Osc | fast=34, slow=55 | 成交量振盪 |
| 16 | 一目均衡表 | `ichimoku` | Osc | tenkan=9, kijun=26, senkou=52 | Ichimoku 雲層 |

### 使用範例

```python
# RSI 策略
rsi = get_strategy('multi_rsi', {'period': 14, 'ob_level': 70, 'os_level': 30})

# 一目均衡表
ichimoku = get_strategy('ichimoku', {'tenkan': 9, 'kijun': 26, 'senkou': 52})
```

---

## 3. 突破與均值回歸（16 策略）

| # | 策略名 | 鍵名 | 基類 | 核心參數 | 說明 |
|---|--------|------|------|---------|------|
| 1 | 布林帶突破 | `bollinger_squeeze` | Break | period=20, std=2.0 | 布林帶擠壓突破 |
| 2 | Dual Thrust | `dual_thrust` | Break/Trend | lookback=4, k1=0.7 | 雙推力突破 |
| 3 | 開盤區間突破 | `orb` | Break | range_min=30 | 開盤 N 分鐘突破 |
| 4 | 樞軸點突破 | `pivot` | Break | type='classic' | 樞軸點突破 |
| 5 | Fibonacci 回撤 | `fibonacci` | Break | levels=[0.382,0.5,0.618] | 斐波那契回撤突破 |
| 6 | 成交量突破 | `volume_breakout` | Break | lookback=20, mult=2.0 | 成交量異常突破 |
| 7 | 杯柄形態 | `cup_handle` | Break | min_bars=30 | 杯柄形態偵測 |
| 8 | 三重頂/底 | `triple_top_bottom` | Break | tolerance=0.02 | 三重頂底突破 |
| 9 | NR7/NR4 | `nr7_nr4` | Break | periods=[7,4] | 窄幅整理突破 |
| 10 | TTO 開盤區間 | `tto_or` | Break | range_min=15 | TTO 開盤突破 |
| 11 | 水平通道 | `horizontal_channel` | Break | lookback=20 | 水平通道突破 |
| 12 | 旗形/三角旗形 | `flag_pennant` | Break | min_bars=10 | 旗形突破 |
| 13 | W底/M頂 | `w_m_pattern` | Break | tolerance=0.02 | W 底 M 頂突破 |
| 14 | 橫盤均值回歸 | `sideways_reversion` | Break | lookback=20, z=2.0 | 橫盤均值回歸 |
| 15 | 三角形收斂 | `triangle` | Break | min_touches=3 | 三角形突破 |
| 16 | 內含柱突破 | `inside_bar` | Break | lookback=10 | Inside Bar 突破 |

---

## 4. AI/機器學習（16 策略）

| # | 策略名 | 鍵名 | 基類 | 核心參數 | 說明 |
|---|--------|------|------|---------|------|
| 1 | LSTM 預測 | `lstm_predictor` | AIML | lookback=60, hidden=50 | LSTM 價格預測 |
| 2 | GNN 圖神經網路 | `gnn` | AIML | hidden=64 | 圖神經網路關聯 |
| 3 | Transformer | `transformer` | AIML | d_model=64, heads=4 | Transformer 注意力 |
| 4 | DQN 強化學習 | `dqn_agent` | AIML | hidden=128, lr=0.001 | DQN 交易代理 |
| 5 | GAN 價格生成 | `gan` | AIML | latent=32, epochs=100 | GAN 價格場景 |
| 6 | 遺傳算法優化 | `genetic_opt` | AIML | pop=50, gens=10 | 遺傳算法參數優化 |
| 7 | 集成學習 | `ensemble` | AIML | n_models=5 | 多模型集成 |
| 8 | 集成投票 | `ensemble_voting_final` | AIML | method='weighted' | 加權投票集成 |
| 9 | 異常偵測 | `anomaly` | AIML | contamination=0.05 | 異常行為偵測 |
| 10 | NLP 事件驅動 | `nlp_event` | AIML | lookback=5 | NLP 新聞事件 |
| 11 | 在線學習 | `online_learning` | AIML | lr=0.01, decay=0.999 | 在線增量學習 |
| 12 | 貝葉斯優化 | `bayesian` | AIML | n_init=5, n_iter=25 | 貝葉斯超參數 |
| 13 | 遷移學習 | `transfer_learning` | AIML | source_dim=64 | 跨市場遷移 |
| 14 | 對比學習 | `contrastive_learning` | AIML | temperature=0.1 | 對比表徵學習 |
| 15 | 多因子模型 | `multi_factor` | AIML | factors=['momentum','value'] | 多因子 Alpha |
| 16 | 配對交易 ML | `pair_trading` | AIML | lookback=60, z=2.0 | ML 配對交易 |

---

## 5. 風險管理（9 策略）

| # | 策略名 | 鍵名 | 基類 | 核心參數 | 說明 |
|---|--------|------|------|---------|------|
| 1 | Kelly 公式 | `kelly` | Risk | fraction=0.25 | Kelly 最優倉位 |
| 2 | 固定分數法 | `fixed_fractional` | Risk | fraction=0.02 | 固定比例倉位 |
| 3 | 固定比率法 | `fixed_ratio` | Risk | delta=1000 | 固定比率倉位 |
| 4 | Anti-Martingale | `anti_martingale` | Risk | base=0.02, mult=1.5 | 盈利加碼 |
| 5 | CVaR 倉位控制 | `cvar` | Risk | alpha=0.95, target_vol=0.15 | CVaR 風險限制 |
| 6 | 最優停損 | `optimal_stop` | Risk | lookback=20 | 動態最優停損 |
| 7 | 尾部風險對沖 | `tail_hedge` | Risk | lookback=60, z=2.5 | 尾部風險偵測對沖 |
| 8 | Delta 中性對沖 | `delta_hedge` | Risk | delta_target=0, rebalance=0.05 | Delta 動態對沖 |
| 9 | 波動率目標 | `vol_target` | Risk | target_vol=0.15, lookback=20 | 波動率目標倉位 |

---

## 6. 微結構與訂單流（11 策略）

| # | 策略名 | 鍵名 | 核心參數 | 說明 |
|---|--------|------|---------|------|
| 1 | 訂單流分析 | `order_flow` | lookback=20 | 買賣盤力量分析 |
| 2 | Delta 累積 | `cum_delta` | lookback=20 | 累積 Delta 偏向 |
| 3 | POC/Value Area | `poc_va` | lookback=50 | 價值區域交易 |
| 4 | VPIN | `vpin` | bucket_size=50 | 知情交易概率 |
| 5 | Amihud 非流動性 | `amihud` | lookback=20 | 非流動性指標 |
| 6 | 冰山訂單偵測 | `iceberg` | lookback=20 | 隱藏訂單偵測 |
| 7 | Kyle's Lambda | `kyle_lambda` | lookback=20 | 市場衝擊係數 |
| 8 | Tick Rule | `tick_rule` | lookback=20 | Tick 方向判定 |
| 9 | Quote Stuffing | `quote_stuffing` | lookback=10 | 報價塞爆偵測 |
| 10 | Level 2 深度 | `level2` | depth_levels=5 | 訂單簿深度分析 |
| 11 | 微價格偏移 | `micro_price` | lookback=20 | 微價格偏移信號 |

---

## 7. 跨市場與宏觀（12 策略）

| # | 策略名 | 鍵名 | 核心參數 | 說明 |
|---|--------|------|---------|------|
| 1 | 利差交易 | `carry_trade` | threshold=0.02, lookback=60 | 利率差交易 |
| 2 | 季節性策略 | `seasonal` | lookback_years=10 | 月度季節效應 |
| 3 | 跨品種價差 | `cross_commodity` | lookback=60, z=2.0 | 商品價差交易 |
| 4 | 美元指數聯動 | `dxy_corr` | lookback=60 | DXY 相關性 |
| 5 | 動態避險比率 | `dynamic_hedge` | base=0.5, vol_lb=30 | 波動率避險 |
| 6 | 收益率曲線 | `yield_curve` | lookback=252 | 曲線斜率策略 |
| 7 | 跨國權益輪動 | `country_rotation` | lookback=60 | 國家輪動 |
| 8 | 商品超級週期 | `super_cycle` | short=120, long=480 | 長期週期 |
| 9 | 恐慌指數交易 | `vix` | ob=30, os=15 | VIX 反向交易 |
| 10 | 信用利差交易 | `credit_spread` | lookback=60, z=1.5 | 信用利差 |
| 11 | 黃金/實際利率 | `gold_real_rate` | lookback=60 | 黃金利率套利 |
| 12 | 跨資產風險平價 | `cross_asset_parity` | lookback=252 | 風險平價 |

---

## 8. 進階計量與統計（10 策略）

| # | 策略名 | 鍵名 | 核心參數 | 說明 |
|---|--------|------|---------|------|
| 1 | 協整配對 | `cointegration` | lookback=60, z=2.0 | 協整關係交易 |
| 2 | Kalman 濾波 | `kalman` | Q=1e-5, R=0.01 | Kalman 狀態估計 |
| 3 | GARCH 波動率 | `garch` | p=1, q=1 | GARCH 波動率模型 |
| 4 | 馬可夫體制 | `markov` | n_states=2 | 體制轉換偵測 |
| 5 | 小波分析 | `wavelet` | wavelet='db4' | 小波分解交易 |
| 6 | 分數差分 | `arfima` | d=0.4, threshold=1e-4 | ARFIMA 分數差分 |
| 7 | Copula 模型 | `copula` | lookback=60 | 相依結構 |
| 8 | SDE 均值回歸 | `sde_mean` | kappa=0.5, theta=0.02 | OU 過程 |
| 9 | 自助法 | `bootstrap` | n_boot=1000, alpha=0.05 | Bootstrap 信賴區間 |
| 10 | 變點偵測 | `changepoint` | lookback=200 | CUSUM 變點 |

---

## 9. 形態與圖表模式（10 策略）

| # | 策略名 | 鍵名 | 核心參數 | 說明 |
|---|--------|------|---------|------|
| 1 | 頭肩頂/底 | `head_shoulders` | tolerance=0.02 | 頭肩形態 |
| 2 | 楔形收斂 | `wedge` | min_touches=3 | 楔形突破 |
| 3 | 鑽石頂/底 | `diamond` | lookback=30 | 鑽石形態 |
| 4 | 跳空回補 | `gap_fill` | min_gap=0.01 | 缺口回補 |
| 5 | K 線組合 | `candlestick` | patterns=['doji','hammer'] | K 線形態 |
| 6 | Elliott 波浪 | `elliott` | degree=5 | Elliott 波浪計數 |
| 7 | 諧波模式 | `harmonic` | patterns=['gartley','butterfly'] | 諧波交易 |
| 8 | Wyckoff 方法 | `wyckoff` | lookback=50 | Wyckoff 累積派發 |
| 9 | 市場結構 | `market_structure` | lookback=20 | 高低點結構 |
| 10 | Volume Profile | `volume_profile` | bins=50 | 成交量分佈形態 |

---

## 10. 執行演算法與高頻（13 策略）

| # | 策略名 | 鍵名 | 核心參數 | 說明 |
|---|--------|------|---------|------|
| 1 | 做市策略 | `market_making` | spread=0.001, inventory=100 | 雙邊報價做市 |
| 2 | 統計套利 | `stat_arb` | lookback=60, z=2.0 | 統計套利 |
| 3 | 延遲套利 | `latency_arb` | threshold=0.0005 | 延遲套利 |
| 4 | 閃崩偵測 | `flash_crash` | threshold=0.03 | 閃崩預警 |
| 5 | VWAP 被動執行 | `vwap` | participation=0.1 | VWAP 執行 |
| 6 | TWAP 被動執行 | `twap` | intervals=10 | TWAP 執行 |
| 7 | Implementation Shortfall | `implementation_shortfall` | urgency=0.5 | IS 最優執行 |
| 8 | Sniper 策略 | `sniper` | threshold=0.001 | Sniper 進場 |
| 9 | ETF NAV 套利 | `etf_nav` | threshold=0.001 | ETF 淨值套利 |
| 10 | POV 被動執行 | `pov` | rate=0.1 | POV 比例執行 |
| 11 | 到價 Arrival Price | `arrival_price` | urgency=0.5 | 到價執行 |
| 12 | 加強 IS | `is_enhanced` | urgency=0.7 | 加強版 IS |
| 13 | 冰山訂單偵測 | `iceberg` | lookback=20 | 隱藏量偵測 |

---

## 使用指南

### 快速開始

```python
from src.strategies import get_strategy, list_all_strategies
import pandas as pd
import numpy as np

# 1. 準備數據
data = pd.DataFrame({
    'open': [...], 'high': [...], 'low': [...],
    'close': [...], 'volume': [...]
})

# 2. 創建策略
strategy = get_strategy('macd_cross', {'fast': 12, 'slow': 26, 'signal': 9})

# 3. 生成信號
signals = strategy.generate_signals(data)

# 4. 計算倉位
for i, sig in enumerate(signals):
    if sig != 0:
        size = strategy.calculate_position_size(
            signal=sig,
            capital=100000,
            price=data['close'].iloc[i],
            volatility=0.02
        )
        print(f"Signal: {sig}, Size: {size}")
```

### 批量回測

```python
from src.strategies import list_all_strategies

all_strats = list_all_strategies()
results = []

for name, info in all_strats.items():
    strategy = get_strategy(name)
    signals = strategy.generate_signals(data)
    buy_count = (signals == 1).sum()
    sell_count = (signals == -1).sum()
    results.append({
        'strategy': name,
        'category': info['category'],
        'buys': buy_count,
        'sells': sell_count,
        'total': buy_count + sell_count
    })
```

### 自定義策略

```python
from src.strategies.base_strategy import TrendFollowingStrategy
import pandas as pd

class MyCustomStrategy(TrendFollowingStrategy):
    def __init__(self, param1=10, param2=20):
        super().__init__('My Strategy', {
            'param1': param1, 'param2': param2
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # 你的策略邏輯
        signals = pd.Series(0, index=data.index)
        # ...
        return signals
    
    def calculate_position_size(self, signal, capital, price, volatility):
        if signal == 0: return 0
        return capital * 0.02 / (price * volatility)
```

---

## 回測結果

### 測試環境
- **數據**: 模擬 OHLCV（200 根 K 線）
- **測試日期**: 2026-03-23
- **結果**: 130/130 策略通過功能測試（100%）

### 按類別統計

| 類別 | 策略數 | 買入信號 | 賣出信號 | 平均信號/策略 |
|------|--------|---------|---------|-------------|
| 趨勢 | 17 | ~120 | ~115 | ~14 |
| 振盪器 | 16 | ~200 | ~190 | ~24 |
| 突破 | 16 | ~150 | ~140 | ~18 |
| AI/ML | 16 | ~100 | ~90 | ~12 |
| 風險 | 9 | ~50 | ~45 | ~11 |
| 微結構 | 11 | ~80 | ~75 | ~14 |
| 宏觀 | 12 | ~90 | ~85 | ~15 |
| 統計 | 10 | ~70 | ~65 | ~14 |
| 形態 | 10 | ~60 | ~55 | ~12 |
| 執行 | 13 | ~100 | ~95 | ~15 |

---

## 附錄

### A. 策略鍵名速查

```
趨勢: sma_cross, ema_cross, macd_cross, adx, supertrend, parabolic_sar,
      donchian, vwap_reversion, hull_ma, t3, kama, tillson_t3, zlema,
      tema, ribbon, turtle, cci

振盪: multi_rsi, adaptive_kd, stoch_rsi, bollinger_pct_b, custom_oscillator,
      awesome, chande_momentum, fisher, dpo, ulcer_index, vortex, elder_ray,
      mass_index, trix, klinger, ichimoku

突破: bollinger_squeeze, dual_thrust, orb, pivot, fibonacci, volume_breakout,
      cup_handle, triple_top_bottom, nr7_nr4, tto_or, horizontal_channel,
      flag_pennant, w_m_pattern, sideways_reversion, triangle, inside_bar

AI/ML: lstm_predictor, gnn, transformer, dqn_agent, gan, genetic_opt, ensemble,
       ensemble_voting_final, anomaly, nlp_event, online_learning, bayesian,
       transfer_learning, contrastive_learning, multi_factor, pair_trading

風險: kelly, fixed_fractional, fixed_ratio, anti_martingale, cvar,
      optimal_stop, tail_hedge, delta_hedge, vol_target

微結構: order_flow, cum_delta, poc_va, vpin, amihud, iceberg, kyle_lambda,
        tick_rule, quote_stuffing, level2, micro_price

宏觀: carry_trade, seasonal, cross_commodity, dxy_corr, dynamic_hedge,
      yield_curve, country_rotation, super_cycle, vix, credit_spread,
      gold_real_rate, cross_asset_parity

統計: cointegration, kalman, garch, markov, wavelet, arfima, copula,
      sde_mean, bootstrap, changepoint

形態: head_shoulders, wedge, diamond, gap_fill, candlestick, elliott,
      harmonic, wyckoff, market_structure, volume_profile

執行: market_making, stat_arb, latency_arb, flash_crash, vwap, twap,
      implementation_shortfall, sniper, etf_nav, pov, arrival_price,
      is_enhanced, iceberg
```

### B. 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| 1.0.0 | 2026-03-20 | 初始版本，27 策略 |
| 2.0.0 | 2026-03-23 | 完整版，130 策略全部通過測試 |

---

**文檔維護**: StocksX Team  
**聯絡**: GitHub Issues  
**授權**: MIT License
