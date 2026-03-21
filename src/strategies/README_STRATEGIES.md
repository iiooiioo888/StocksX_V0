# 📚 StocksX 策略庫開發指南

**策略總數**: 130+  
**類別數量**: 10 大類  
**開發進度**: 27/130 (21%)  

---

## 📁 目錄結構

```
src/strategies/
├── __init__.py                    # 策略庫入口
├── base_strategy.py               # 策略基類
├── strategy_factory.py            # 策略工廠
├── README_STRATEGIES.md          # 本文檔
│
├── trend/                         # 趨勢跟隨策略（18 個）
│   ├── __init__.py
│   ├── trend_strategies.py        # 已實作 5 個
│   ├── advanced_trend.py          # 待實作 9 個
│   └── README.md
│
├── oscillator/                    # 振盪器策略（16 個）
│   ├── __init__.py
│   ├── oscillator_strategies.py   # 已實作 4 個
│   ├── advanced_oscillator.py     # 待實作 12 個
│   └── README.md
│
├── breakout/                      # 突破策略（16 個）
│   ├── __init__.py
│   ├── breakout_strategies.py     # 待實作 16 個
│   └── README.md
│
├── ai_ml/                         # AI/ML 策略（16 個）
│   ├── __init__.py
│   ├── ai_strategies.py           # 待實作 8 個
│   ├── lstm_strategy.py           # LSTM
│   ├── rl_strategy.py             # 強化學習
│   └── README.md
│
├── risk_management/               # 風險管理（12 個）
│   ├── __init__.py
│   ├── risk_strategies.py         # 待實作 7 個
│   └── README.md
│
├── microstructure/                # 微結構策略（12 個）
│   ├── __init__.py
│   ├── micro_strategies.py        # 待實作 12 個
│   └── README.md
│
├── macro/                         # 宏觀策略（12 個）
│   ├── __init__.py
│   ├── macro_strategies.py        # 待實作 12 個
│   └── README.md
│
├── statistical/                   # 統計策略（10 個）
│   ├── __init__.py
│   ├── stat_strategies.py         # 待實作 10 個
│   └── README.md
│
├── pattern/                       # 形態策略（10 個）
│   ├── __init__.py
│   ├── pattern_strategies.py      # 待實作 10 個
│   └── README.md
│
└── execution/                     # 執行算法（8 個）
    ├── __init__.py
    ├── execution_strategies.py    # 待實作 8 個
    └── README.md
```

---

## 🎯 策略開發模板

### 1. 創建策略文件

在對應類別目錄下創建文件，例如：
```python
# src/strategies/trend/advanced_trend.py
"""
進階趨勢策略
包含：Hull MA, T3, KAMA 等
"""

import pandas as pd
import numpy as np
from ..base_strategy import TrendFollowingStrategy


class HullMA(TrendFollowingStrategy):
    """Hull 移動平均策略"""
    
    def __init__(self, period: int = 20):
        super().__init__('Hull MA', {
            'period': period
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # 實作策略邏輯
        pass


# 策略註冊表
ADVANCED_TREND_STRATEGIES = {
    'hull_ma': HullMA,
}
```

### 2. 策略必須實現的方法

```python
class MyStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（必須實現）"""
        pass
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小（必須實現）"""
        pass
```

### 3. 註冊策略

在策略文件末尾添加註冊表：
```python
MY_STRATEGIES = {
    'my_strategy': MyStrategy,
}
```

並在 `strategy_factory.py` 中導入。

---

## 📊 策略開發優先級

### Phase 1（已完成）✅
- ✅ 基礎趨勢策略（5 個）
- ✅ 基礎振盪器（4 個）
- ✅ 基礎 AI/ML（8 個）
- ✅ 基礎風險管理（5 個）

### Phase 2（進行中）🔄
- 🔄 進階趨勢指標（9 個）
- 🔄 進階振盪器（12 個）
- 🔄 突破策略（15 個）

### Phase 3（待開發）📋
- 📋 微結構策略（12 個）
- 📋 宏觀策略（12 個）
- 📋 統計策略（10 個）
- 📋 形態策略（10 個）
- 📋 執行算法（8 個）

---

## 🔧 開發工具

### 測試策略

```python
from strategies import get_strategy

# 創建策略
strategy = get_strategy('rsi', {'period': 14})

# 回測
from backtest import backtest_strategy
results = backtest_strategy(strategy, data)
print(results)
```

### 批量回測

```python
from strategies import list_all_strategies

# 獲取所有策略
all_strategies = list_all_strategies()

# 批量回測
for name, info in all_strategies.items():
    strategy = get_strategy(name)
    results = backtest_strategy(strategy, data)
    print(f"{name}: {results['sharpe_ratio']}")
```

---

## 📝 開發清單

### 趨勢策略（✅ 全部完成）
- [x] 均線帶（Ribbon）
- [x] 海龜交易法
- [x] CCI 商品通道
- [x] Hull MA
- [x] T3 均線
- [x] KAMA 自適應均線
- [x] Tillson T3
- [x] ZLEMA 零滯後 EMA
- [x] TEMA 三重指數

### 振盪器策略（12 個待開發）
- [ ] 一目均衡表
- [ ] Stochastic RSI
- [ ] Awesome Oscillator
- [ ] Chande 動量振盪
- [ ] Fisher Transform
- [ ] Detrended Price Oscillator
- [ ] Ulcer Index
- [ ] Vortex 振盪
- [ ] Elder Ray
- [ ] Mass Index
- [ ] TRIX
- [ ] Klinger 振盪

### 突破策略（15 個待開發）
- [ ] 雙推力
- [ ] VWAP 回歸
- [ ] 開盤區間突破
- [ ] 樞軸點突破
- [ ] 布林帶擠壓
- [ ] 斐波那契回撤突破
- [ ] 成交量突破
- [ ] 杯柄形態
- [ ] 三重頂/底突破
- [ ] NR7/NR4
- [ ] TTO Opening Range
- [ ] 水平通道突破
- [ ] 旗形/三角旗形
- [ ] W 底/M 頂突破
- [ ] 橫盤均值回歸

### AI/ML 策略（4 個已完成，5 個待開發）
- [x] 遺傳演算法優化
- [x] 圖神經網路 GNN（骨架）
- [ ] GAN 價格生成
- [x] 異常偵測
- [ ] 在線學習
- [ ] 貝葉斯優化
- [x] NLP 事件驅動（骨架）
- [ ] 遷移學習
- [ ] 對比學習

### 風險管理（7 個待開發）
- [ ] Anti-Martingale
- [ ] 固定比率法
- [ ] CVaR/ES 倉位控制
- [ ] 最優停損
- [ ] 尾部風險對沖
- [ ] 動態對沖 Delta Neutral

### 微結構策略（12 個待開發）
- [ ] 訂單流分析
- [ ] Delta 累積
- [ ] POC / Value Area
- [ ] TWAP
- [ ] 冰山訂單偵測
- [ ] VPIN
- [ ] Amihud 非流動性
- [ ] Kyle's Lambda
- [ ] Tick 規則
- [ ] Quote Stuffing 偵測
- [ ] Level 2 深度分析
- [ ] 微價格偏移

### 宏觀策略（12 個待開發）
- [ ] 利差交易
- [ ] 季節性策略
- [ ] 跨品種價差
- [ ] 美元指數聯動
- [ ] 避險比率動態調整
- [ ] 收益率曲線策略
- [ ] 跨國權益輪動
- [ ] 商品超級週期
- [ ] 恐慌指數交易
- [ ] 信用利差交易
- [ ] 黃金/實際利率套利
- [ ] 跨資產風險平價

### 統計策略（10 個待開發）
- [ ] 協整配對
- [ ] Kalman 濾波
- [ ] GARCH 波動率模型
- [ ] 馬可夫體制轉換
- [ ] 小波分析
- [ ] 分數差分
- [ ] Copula 模型
- [ ] 隨機微分方程
- [ ] 自助法
- [ ] 變點偵測

### 形態策略（10 個待開發）
- [ ] 頭肩頂/底
- [ ] 楔形收斂/擴張
- [ ] 鑽石頂/底
- [ ] 跳空回補
- [ ] 日本 K 線組合
- [ ] Elliott 波浪計數
- [ ] 諧波模式
- [ ] Wyckoff 方法
- [ ] 市場結構
- [ ] Volume Profile 形態

### 執行算法（8 個待開發）
- [ ] 做市策略
- [ ] 統計套利
- [ ] 延遲套利
- [ ] 閃崩偵測
- [ ] VWAP/TWAP 被動執行
- [ ] Implementation Shortfall
- [ ] Sniper 策略
- [ ] ETF 套利

---

## 🎓 學習資源

- [技術指標文檔](https://www.investopedia.com/technical-analysis-4689657)
- [量化交易指南](https://www.quantstart.com/)
- [Python for Finance](https://www.oreilly.com/library/view/python-for-finance/9781491945360/)

---

**最後更新**: 2026-03-20
