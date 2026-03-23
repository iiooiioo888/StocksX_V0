# 📚 StocksX 策略優化完整文檔

**版本**: 3.0.0  
**最後更新**: 2026-03-23  
**策略總數**: 130  
**已完成優化**: 1 (進行中)  
**本文檔目的**: 一個策略一個任務拆分，完整追蹤優化進度

---

## 📋 目錄

1. [優化總覽](#優化總覽)
2. [已完成優化](#已完成優化)
3. [Phase 1: 高優先級策略（🔴 28 策略）](#phase-1-高優先級策略)
4. [Phase 2: 中優先級策略（🟡 38 策略）](#phase-2-中優先級策略)
5. [Phase 3: 低優先級策略（🟢 29 策略）](#phase-3-低優先級策略)
6. [通用優化框架](#通用優化框架)
7. [策略任務拆分明細](#策略任務拆分明細)

---

## 優化總覽

### 進度儀表板

| 階段 | 優先級 | 策略數 | 已完成 | 進行中 | 待開始 | 完成率 |
|------|--------|--------|--------|--------|--------|--------|
| Phase 1 | 🔴 HIGH | 28 | 1 | 0 | 27 | 3.6% |
| Phase 2 | 🟡 MED | 38 | 0 | 0 | 38 | 0% |
| Phase 3 | 🟢 LOW | 29 | 0 | 0 | 29 | 0% |
| **合計** | | **95** | **1** | **0** | **94** | **1.1%** |

### 優化標準

每個策略優化必須達到以下標準才算完成：

| 指標 | 最低要求 | 理想目標 |
|------|----------|----------|
| Sharpe Ratio | > 1.0 | > 1.5 |
| 年化收益 | > 5% | > 15% |
| 最大回撤 | < 30% | < 20% |
| 勝率 | > 45% | > 55% |
| 回測週期 | ≥ 3年 | ≥ 5年 |

---

## 已完成優化

### ✅ #34 訂單流分析 (order_flow) — 2026-03-23

| 項目 | 原始值 | 優化後 | 變化 |
|------|--------|--------|------|
| lookback | 20 | **50** | +150% |
| imbalance_threshold | 0.3 | **0.2** | -33% |
| Sharpe Ratio | 1.832 | **2.033** | +11.0% |
| 年化收益 | 12.63% | **29.96%** | +137% |
| 最大回撤 | -1.51% | **-19.55%** | 注意增加 |
| 交易次數 | 141 | **34** | -76% |
| 勝率 | — | **56.2%** | — |

**關鍵洞察**: 長 lookback (50) 配合低 threshold (0.2) 顯著提升信號質量，減少噪音交易。

---

## Phase 1: 高優先級策略

### 🔴 回測驗證任務（20 策略）

每個任務需要：3年歷史回測 + 核心參數優化 + 穩健性驗證

| Issue | 策略 | 鍵名 | 核心任務 | 驗收標準 |
|-------|------|------|----------|----------|
| #41 | 統計套利 | `stat_arb` | 3年回測 + z-score優化 | Sharpe>1.5, 統計顯著性 |
| #40 | 做市策略 | `market_making` | 3年回測 + 點差優化 | Sharpe>1.5, 盈利穩定 |
| #38 | Kalman 濾波 | `kalman` | 3年回測 + Q/R參數優化 | Sharpe>1.5, 濾波效果驗證 |
| #37 | 協整配對 | `cointegration` | 3年回測 + 協整閾值優化 | Sharpe>1.5, p-value<0.05 |
| #36 | Level 2 深度 | `level2` | 3年回測 + 深度參數優化 | Sharpe>1.0 |
| #35 | VPIN | `vpin` | 3年回測 + 桶大小優化 | Sharpe>1.0 |
| #34 | 訂單流分析 | `order_flow` | 3年回測 + 信號閾值優化 | ✅ **已完成** |
| #32 | Delta 中性對沖 | `delta_hedge` | 3年回測 + 再平衡閾值 | Sharpe>1.5, 對沖效率>80% |
| #31 | 最優停損 | `optimal_stop` | 3年回測 + 停損邏輯驗證 | Sharpe>1.5, 最大回撤<25% |
| #30 | CVaR 倉位控制 | `cvar` | 3年回測 + alpha優化 | Sharpe>1.5, VaR準確率>95% |
| #29 | Kelly 公式 | `kelly` | 3年回測 + 分數優化 | Sharpe>1.5 |
| #26 | DQN 強化學習 | `dqn_agent` | 3年回測 + 獎勵函數調優 | Sharpe>1.0, 收斂穩定 |
| #25 | Transformer | `transformer` | 3年回測 + 注意力優化 | Sharpe>1.0 |
| #24 | LSTM 預測 | `lstm_predictor` | 3年回測 + 網格搜索 | Sharpe>1.0 |
| #23 | Fibonacci 回撤 | `fibonacci` | 3年回測 + 回撤水平優化 | Sharpe>1.0 |
| #22 | 開盤區間突破 | `orb` | 3年回測 + 區間時間優化 | Sharpe>1.5 |
| #20 | 一目均衡表 | `ichimoku` | 3年回測 + 轉換線/基準線 | Sharpe>1.5 |
| #17 | 海龜交易法 | `turtle` | 3年回測 + 海龜參數驗證 | Sharpe>1.5 |
| #16 | Supertrend | `supertrend` | 3年回測 + ATR倍數優化 | Sharpe>1.5 |
| #15 | 布林帶擠壓 | `bollinger_squeeze` | 3年回測 + 擠壓閾值優化 | Sharpe>1.5 |

---

## Phase 2: 中優先級策略

### 🟡 參數優化任務（38 策略）

每個任務需要：參數敏感性分析 + 最優參數組合確定 + 回測結果記錄

#### 趨勢策略優化

| Issue | 策略 | 鍵名 | 優化參數 | 目標 |
|-------|------|------|----------|------|
| #42 | EMA 指數交叉 | `ema_cross` | short/long period | Sharpe>1.0 |
| #43 | Parabolic SAR | `parabolic_sar` | af_start/step/max | Sharpe>1.0 |
| #44 | Donchian 通道 | `donchian` | period | Sharpe>1.0 |
| #45 | 均線帶 Ribbon | `ribbon` | periods array | Sharpe>1.0 |

#### 振盪器策略優化

| Issue | 策略 | 鍵名 | 優化參數 | 目標 |
|-------|------|------|----------|------|
| #46 | CCI 商品通道 | `cci` | period, threshold | Sharpe>1.0 |
| #47 | Stochastic RSI | `stoch_rsi` | RSI+Stoch雙層 | Sharpe>1.0 |
| #48 | Bollinger %B | `bollinger_pct_b` | %B閾值 | Sharpe>1.0 |
| #49 | Chande 動量 | `chande_momentum` | period | Sharpe>1.0 |
| #50 | Fisher Transform | `fisher` | period | Sharpe>1.0 |
| #51 | Vortex 振盪 | `vortex` | period | Sharpe>1.0 |
| #52 | Elder Ray | `elder_ray` | EMA period | Sharpe>1.0 |
| #53 | Klinger 振盪 | `klinger` | Fast/Slow | Sharpe>1.0 |

#### 突破策略優化

| Issue | 策略 | 鍵名 | 優化參數 | 目標 |
|-------|------|------|----------|------|
| #54 | Dual Thrust | `dual_thrust` | K1/K2 | Sharpe>1.0 |
| #55 | 成交量突破 | `volume_breakout` | 成交量倍數 | Sharpe>1.0 |
| #56 | NR7/NR4 | `nr7_nr4` | 窄幅參數 | Sharpe>1.0 |
| #57 | 橫盤均值回歸 | `sideways_reversion` | Z分數 | Sharpe>1.0 |
| #58 | 內含柱突破 | `inside_bar` | Lookback | Sharpe>1.0 |

#### AI/ML 策略優化

| Issue | 策略 | 鍵名 | 優化參數 | 目標 |
|-------|------|------|----------|------|
| #59 | GNN 圖神經網路 | `gnn` | 圖結構 | Sharpe>1.0 |
| #60 | 異常偵測 | `anomaly` | 污染率 | Sharpe>1.0 |
| #61 | NLP 事件驅動 | `nlp_event` | 事件窗口 | Sharpe>1.0 |
| #62 | 在線學習 | `online_learning` | 學習率 | Sharpe>1.0 |
| #63 | 貝葉斯優化 | `bayesian` | 迭代次數 | Sharpe>1.0 |

#### 風險管理優化

| Issue | 策略 | 鍵名 | 優化參數 | 目標 |
|-------|------|------|----------|------|
| #64 | 配對交易 ML | `pair_trading` | Z分數 | Sharpe>1.0 |
| #65 | 固定分數法 | `fixed_fractional` | 分數 | Sharpe>1.0 |
| #66 | Anti-Martingale | `anti_martingale` | 倍數 | Sharpe>1.0 |
| #67 | 尾部風險對沖 | `tail_hedge` | Z分數 | Sharpe>1.0 |

#### 微結構優化

| Issue | 策略 | 鍵名 | 優化參數 | 目標 |
|-------|------|------|----------|------|
| #68 | Delta 累積 | `cum_delta` | Lookback | Sharpe>1.0 |
| #69 | POC/Value Area | `poc_va` | Lookback | Sharpe>1.0 |
| #70 | Amihud 非流動性 | `amihud` | Lookback | Sharpe>1.0 |
| #71 | Kyle's Lambda | `kyle_lambda` | Lookback | Sharpe>1.0 |

#### 宏觀策略優化

| Issue | 策略 | 鍵名 | 優化參數 | 目標 |
|-------|------|------|----------|------|
| #72 | 利差交易 | `carry_trade` | 閾值 | Sharpe>1.0 |
| #73 | 跨品種價差 | `cross_commodity` | Z分數 | Sharpe>1.0 |
| #74 | 動態避險比率 | `dynamic_hedge` | 基礎避險比 | Sharpe>1.0 |
| #75 | 恐慌指數交易 | `vix` | 超買超賣閾值 | Sharpe>1.0 |
| #76 | 信用利差交易 | `credit_spread` | Z分數 | Sharpe>1.0 |
| #77 | 馬可夫體制 | `markov` | 體制數量 | Sharpe>1.0 |
| #78 | 小波分析 | `wavelet` | 小波族 | Sharpe>1.0 |
| #79 | SDE 均值回歸 | `sde_mean` | kappa/theta | Sharpe>1.0 |

---

## Phase 3: 低優先級策略

### 🟢 精細調優任務（29 策略）

每個任務需要：參數微調 + 回測結果記錄

| Issue | 策略 | 鍵名 | 微調參數 |
|-------|------|------|----------|
| #80 | SMA 均線交叉 | `sma_cross` | 交叉週期 |
| #81 | VWAP 均值回歸 | `vwap_reversion` | 標準差閾值 |
| #82 | Hull MA | `hull_ma` | 週期 |
| #83 | T3 均線 | `t3` | vfactor |
| #84 | KAMA 自適應 | `kama` | Fast/Slow |
| #85 | Tillson T3 | `tillson_t3` | vfactor |
| #86 | ZLEMA 零滯後 | `zlema` | 週期 |
| #87 | TEMA 三重指數 | `tema` | 週期 |
| #88 | 自定義振盪器 | `custom_oscillator` | 參數 |
| #89 | Awesome Oscillator | `awesome` | 週期 |
| #90 | DPO 去趨勢 | `dpo` | 週期 |
| #91 | Ulcer Index | `ulcer_index` | 週期 |
| #92 | Mass Index | `mass_index` | 週期 |
| #93 | TRIX | `trix` | 週期 |
| #94 | 杯柄形態 | `cup_handle` | 形態參數 |
| #95 | 三重頂/底 | `triple_top_bottom` | 容差 |
| #96 | TTO 開盤 | `tto_or` | 區間時間 |
| #97 | 水平通道 | `horizontal_channel` | Lookback |
| #98 | 旗形/三角旗形 | `flag_pennant` | 形態參數 |
| #99 | W底/M頂 | `w_m_pattern` | 容差 |
| #100 | 三角形收斂 | `triangle` | 觸點 |
| #101 | GAN 價格生成 | `gan` | 潛在空間 |
| #102 | 遺傳算法優化 | `genetic_opt` | 種群/代數 |
| #103 | 遷移學習 | `transfer_learning` | 維度 |
| #104 | 對比學習 | `contrastive_learning` | 溫度 |
| #105 | 固定比率法 | `fixed_ratio` | Delta |
| #106 | Tick Rule | `tick_rule` | Lookback |
| #107 | Quote Stuffing | `quote_stuffing` | Lookback |

---

## 通用優化框架

### 每個策略的優化工作流

```
1. 確認策略實現完整性
   └── 檢查 generate_signals() 邏輯
   └── 檢查 calculate_position_size() 風險控制

2. 參數空間定義
   └── 識別所有可調參數
   └── 定義每個參數的合理範圍
   └── 確定搜索方法 (Grid / Random / Bayesian)

3. 回測執行
   └── 至少3年歷史數據
   └── Walk-forward 驗證
   └── 蒙特卡羅模擬（可選）

4. 結果分析
   └── Sharpe Ratio / 年化收益 / 最大回撤
   └── 參數敏感性分析
   └── 過擬合檢測

5. 文檔記錄
   └── 更新 Issue 狀態
   └── 記錄最佳參數組合
   └── 記錄風險提示
```

### 回測代碼模板

```python
import sys
sys.path.insert(0, 'src')
from strategies import get_strategy
import pandas as pd
import numpy as np

# 1. 載入策略
strategy = get_strategy('strategy_key', {'param1': value1})

# 2. 載入數據
data = pd.read_csv('data.csv', index_col=0, parse_dates=True)

# 3. 生成信號
signals = strategy.generate_signals(data)

# 4. 計算收益
daily_returns = data['close'].pct_change()
strategy_returns = signals.shift(1) * daily_returns

# 5. 統計
sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
max_dd = (strategy_returns.cumsum().cummax() - strategy_returns.cumsum()).max()
print(f"Sharpe: {sharpe:.4f}, MaxDD: {max_dd:.2%}")
```

---

## 策略任務拆分明細

### 拆分原則

1. **一個策略 = 一個 Issue**：每個策略的優化作為獨立 Issue 追蹤
2. **一個核心任務 + 多個驗收標準**：明確完成條件
3. **按優先級排序**：🔴 → 🟡 → 🟢
4. **互相獨立**：不同策略間無依賴，可並行執行

### 任務執行順序建議

```
第一批（本週）：#41, #40, #38, #37 — 統計套利/做市/Kalman/協整
第二批（下週）：#36, #35, #32, #31 — Level2/VPIN/Delta對沖/最優停損
第三批：       #30, #29, #26, #25 — CVaR/Kelly/DQN/Transformer
第四批：       #24, #23, #22, #20 — LSTM/Fibonacci/ORB/一目均衡表
第五批：       #17, #16, #15, #42~79 — 海龜/Supertrend/布林帶+中優先級
第六批：       #80~107 — 低優先級精細調優
```

---

*本文檔隨優化進度持續更新。每完成一個策略，對應更新此處的「已完成優化」章節和 ISSUES.md。*
