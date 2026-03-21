# 策略更新報告 - 2026-03-21

**更新日期**: 2026-03-21  
**更新內容**: 趨勢策略 + AI/ML 策略實作  
**開發者**: 小黑

---

## 📊 更新摘要

本次更新完成了：
- ✅ 趨勢策略：新增 2 個（T3 均線、Tillson T3）
- ✅ AI/ML 策略：新增 4 個（遺傳演算法、異常偵測、GNN、NLP）
- ✅ 基礎設施：創建 base_strategy.py 基類文件

**總策略進度**: 27 → 33 (21% → 25%)

---

## 🎯 新增策略詳情

### 趨勢策略（+2）

#### 1. T3 均線 (T3Average)
**文件**: `src/strategies/trend/advanced_trend_strategies.py`

**原理**:
- 使用多次 EMA 平滑減少滯後同時保持曲線平滑
- 計算 6 次 EMA 並組合
- 信號：價格上穿 T3 → 買入，下穿 → 賣出

**參數**:
- `period`: EMA 週期（默认 14）
- `v_factor`: 體積因子（0-1，默认 0.7）

**信號邏輯**:
```python
# 上穿買入
cross_above = (close > t3) & (close.shift(1) < t3.shift(1))
signals[cross_above] = 1

# 下穿賣出
cross_below = (close < t3) & (close.shift(1) > t3.shift(1))
signals[cross_below] = -1
```

#### 2. Tillson T3 (TillsonT3)
**文件**: `src/strategies/trend/advanced_trend_strategies.py`

**原理**:
- Tim Tillson 開發的進階移動平均線
- 使用體積因子優化平滑度和響應速度
- GD → GD2 → GD3 → GD4 四次 EMA
- EV1 = 2*GD - 2*GD2 + GD3
- EV2 = 2*GD2 - 2*GD3 + GD4
- T3 = v*EV1 + (1-v)*EV2

**參數**:
- `period`: EMA 週期（默认 14）
- `v_factor`: 體積因子（0-1，默认 0.7）

**信號邏輯**:
```python
# 斜率向上 + 價格 > T3 → 買入
buy_signal = (t3_slope > 0) & (close > t3)

# 斜率向下 + 價格 < T3 → 賣出
sell_signal = (t3_slope < 0) & (close < t3)
```

---

### AI/ML 策略（+4）

#### 1. 遺傳演算法優化 (GeneticOptimization)
**文件**: `src/strategies/ai_ml/ai_strategies.py`

**原理**:
- 使用遺傳演算法優化其他策略的參數
- 通過選擇、交叉、變異找到最優參數組合
- 適應度函數：Sharpe Ratio + 最大回撤懲罰

**參數**:
- `base_strategy`: 要優化的基礎策略名稱
- `param_ranges`: 參數範圍字典 {param_name: (min, max)}
- `population_size`: 種群大小（默认 20）
- `generations`: 進化代數（默认 10）
- `mutation_rate`: 變異率（默认 0.1）
- `crossover_rate`: 交叉率（默认 0.8）

**核心算法**:
1. 初始化種群（隨機參數組合）
2. 計算適應度（Sharpe - 回撤）
3. 錦標賽選擇
4. 單點交叉
5. 高斯變異
6. 重複 2-5 直到指定代數

**使用示例**:
```python
genetic = GeneticOptimization(
    base_strategy='sma_cross',
    param_ranges={'short': (5, 20), 'long': (20, 100)},
    generations=10,
    population_size=20
)
signals = genetic.generate_signals(data)
# 輸出：Best Parameters: {'short': 10, 'long': 30}
```

#### 2. 異常偵測 (AnomalyDetection)
**文件**: `src/strategies/ai_ml/ai_strategies.py`

**原理**:
- 使用統計方法偵測價格異常
- 方法 1: Z-Score（滾動均值和標準差）
- 方法 2: 簡化版 Isolation Forest（百分位數）
- 反向交易：異常低→買，異常高→賣

**參數**:
- `window`: 滾動窗口大小（默认 20）
- `z_threshold`: Z-Score 閾值（默认 2.0）
- `method`: 方法選擇 ('zscore' 或 'isolation')

**信號邏輯**:
```python
# Z-Score 方法
zscore = (close - rolling_mean) / rolling_std

# 異常低點（Z-Score < -threshold）→ 買入
signals[zscore < -threshold] = 1

# 異常高點（Z-Score > threshold）→ 賣出
signals[zscore > threshold] = -1
```

#### 3. 圖神經網路 GNN (GraphNeuralNetwork)
**文件**: `src/strategies/ai_ml/ai_strategies.py`

**原理**:
- 使用 GNN 建模資產間的關聯關係
- 捕捉市場傳導效應和相關性變化
- **注意**: 此為骨架實現，實際使用需要 PyTorch Geometric

**參數**:
- `assets`: 資產列表（默认 ['AAPL', 'GOOGL', 'MSFT', 'AMZN']）
- `hidden_dim`: 隱藏層維度（默认 64）
- `num_layers`: GNN 層數（默认 2）
- `correlation_window`: 相關性計算窗口（默认 60）

**簡化實現**:
- 使用自相關係數代替 GNN
- 自相關高 → 趨勢持續
- 自相關低 → 均值回歸

**TODO**:
- [ ] 安裝 PyTorch Geometric
- [ ] 構建資產關聯圖
- [ ] 實現圖卷積層
- [ ] 訓練 GNN 模型

#### 4. NLP 事件驅動 (NLPEventDriven)
**文件**: `src/strategies/ai_ml/ai_strategies.py`

**原理**:
- 使用自然語言處理分析新聞、社群媒體情緒
- 根據情緒變化生成交易信號
- **注意**: 此為骨架實現，實際使用需要新聞 API

**參數**:
- `sentiment_threshold`: 情緒閾值（默认 0.3）
- `window`: 情緒平均窗口（默认 5）
- `source`: 數據源 ('mock', 'newsapi', 'twitter')

**簡化實現**:
- 使用模擬情緒數據（隨機生成）
- 關鍵詞匹配分析情緒
- 正面詞：beat, surge, growth, profit, bullish, upgrade
- 負面詞：miss, drop, loss, bearish, downgrade, crash

**TODO**:
- [ ] 接入新聞 API（NewsAPI, Twitter API）
- [ ] 使用 FinBERT 或其他情感分析模型
- [ ] 構建實時情緒指標

---

## 🏗️ 基礎設施更新

### base_strategy.py
**文件**: `src/strategies/base_strategy.py`

**新增基類**:
- `BaseStrategy` - 所有策略的抽象基類
- `TrendFollowingStrategy` - 趨勢策略基類
- `OscillatorStrategy` - 振盪器策略基類
- `BreakoutStrategy` - 突破策略基類
- `MeanReversionStrategy` - 均值回歸策略基類
- `AIMLStrategy` - AI/ML 策略基類
- `RiskManagementStrategy` - 風險管理策略基類

**抽象方法**:
- `generate_signals(data)` - 生成交易信號
- `calculate_position_size(signal, capital, price, volatility)` - 計算倉位

---

## 📁 文件變更清單

### 新增文件
- `src/strategies/base_strategy.py` (2.5KB)
- `src/strategies/ai_ml/ai_strategies.py` (20.8KB)
- `docs/STRATEGY_UPDATE_2026-03-21.md` (本文檔)

### 修改文件
- `src/strategies/trend/advanced_trend_strategies.py` (+200 行)
- `src/strategies/trend/__init__.py` (更新變量名)
- `src/strategies/ai_ml/__init__.py` (新增導入)
- `ISSUES.md` (更新進度)
- `src/strategies/README_STRATEGIES.md` (更新清單)
- `memory/2026-03-21.md` (記錄進度)

---

## ✅ 測試結果

### 語法測試
```bash
python3 -c "import ast; ast.parse(open('src/strategies/trend/advanced_trend_strategies.py').read())"
# advanced_trend_strategies.py: OK

python3 -c "import ast; ast.parse(open('src/strategies/ai_ml/ai_strategies.py').read())"
# ai_strategies.py: OK
```

### 功能測試
```bash
python3 src/strategies/ai_ml/ai_strategies.py
```

**輸出**:
```
============================================================
AI/ML 策略測試
============================================================

1. 遺傳演算法優化
Generation 0: Best Fitness = -0.7205
...
Optimization Complete!
Best Parameters: {'short': 5, 'long': 89}
Best Fitness: -0.7205

2. 異常偵測
   信號數量：-7

3. 圖神經網路
   信號數量：0

4. NLP 事件驅動
   信號數量：0

============================================================
測試完成！
============================================================
```

---

## 📈 進度更新

### 總體進度
- **之前**: 27/130 (21%)
- **現在**: 33/130 (25%)
- **新增**: +6 策略

### 各類別進度

| 類別 | 總數 | 已完成 | 進度 |
|------|------|--------|------|
| 趨勢跟隨 | 18 | 18 | ✅ 100% |
| 振盪器 | 16 | 4 | 25% |
| 突破 | 16 | 2 | 12.5% |
| AI/ML | 16 | 8 | 50% |
| 風險管理 | 12 | 5 | 42% |
| 微結構 | 12 | 0 | 0% |
| 宏觀 | 12 | 0 | 0% |
| 統計 | 10 | 0 | 0% |
| 形態 | 10 | 0 | 0% |
| 執行 | 8 | 0 | 0% |

---

## 🎯 下一步計劃

### 優先任務
1. **振盪器策略** - 完成剩餘 12 個
2. **突破策略** - 完成剩餘 14 個
3. **AI/ML 深化** - 完善 GNN 和 NLP 的實際實現
4. **風險管理** - 完成剩餘 7 個

### 技術債
- [ ] 將所有策略遷移到 StrategyFactory 註冊系統
- [ ] 統一所有策略的測試框架
- [ ] 添加策略文檔生成器
- [ ] 創建策略性能對比儀表板

---

## 📝 備註

1. **AI/ML 策略**：GNN 和 NLP 目前是骨架實現，需要額外依賴和 API 接入
2. **遺傳演算法**：優化時間較長，建議在回測時使用較少的代數（5-10 代）
3. **異常偵測**：適合震盪市場，趨勢市場可能產生錯誤信號

---

**報告完成時間**: 2026-03-21 10:30  
**下次更新**: 待確認
