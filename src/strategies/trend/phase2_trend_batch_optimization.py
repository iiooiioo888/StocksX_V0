"""
Phase 2 中優先級策略批量優化

優化任務：OPT-042 ~ OPT-058 (17 個中優先級策略)
目標：批量回測驗證趨勢、振盪器、突破策略
執行日期：2026-03-23
"""

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime
import warnings
from src.strategies.base_strategy import BaseStrategy
warnings.filterwarnings('ignore')


# ============================================================================
# 1. EMA 指數交叉
# ============================================================================

class EMACrossOptimized(BaseStrategy):
    """優化的 EMA 交叉策略"""
    
    def __init__(self, short_period: int = 12, long_period: int = 26,
                 use_ema_filter: bool = True, signal_smoothing: bool = True):
        super().__init__('EMA Cross Optimized', {
            'short_period': short_period,
            'long_period': long_period,
            'use_ema_filter': use_ema_filter,
            'signal_smoothing': signal_smoothing
        }, category='trend')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        short = self.params['short_period']
        long = self.params['long_period']
        
        ema_short = data['close'].ewm(span=short, adjust=False).mean()
        ema_long = data['close'].ewm(span=long, adjust=False).mean()
        
        signals = pd.Series(0, index=data.index)
        
        # 金叉 → 買入
        golden_cross = (ema_short > ema_long) & (ema_short.shift(1) <= ema_long.shift(1))
        signals[golden_cross] = 1
        
        # 死叉 → 賣出
        death_cross = (ema_short < ema_long) & (ema_short.shift(1) >= ema_long.shift(1))
        signals[death_cross] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0
        
        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade
        
        if volatility > 0:
            shares = risk_amount / (2 * volatility)
        else:
            shares = 0
        
        return round(shares, 2)

# ============================================================================
# 2. Parabolic SAR
# ============================================================================

class ParabolicSAROptimized(BaseStrategy):
    """優化的 Parabolic SAR 策略"""
    
    def __init__(self, af_start: float = 0.02, af_step: float = 0.02,
                 af_max: float = 0.2, use_trend_filter: bool = True):
        super().__init__('Parabolic SAR Optimized', {
            'af_start': af_start,
            'af_step': af_step,
            'af_max': af_max,
            'use_trend_filter': use_trend_filter
        }, category='trend')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        af_start = self.params['af_start']
        af_step = self.params['af_step']
        af_max = self.params['af_max']
        
        high = data['high']
        low = data['low']
        close = data['close']
        
        # 簡化 PSAR 計算
        psar = pd.Series(0.0, index=data.index)
        trend = pd.Series(1, index=data.index)
        
        psar.iloc[0] = low.iloc[0]
        ep = high.iloc[0]
        af = af_start
        
        for i in range(1, len(data)):
            if trend.iloc[i-1] == 1:
                psar.iloc[i] = psar.iloc[i-1] + af * (ep - psar.iloc[i-1])
                if high.iloc[i] > ep:
                    ep = high.iloc[i]
                    af = min(af + af_step, af_max)
                if low.iloc[i] < psar.iloc[i]:
                    trend.iloc[i] = -1
                    psar.iloc[i] = ep
                    ep = low.iloc[i]
                    af = af_start
            else:
                psar.iloc[i] = psar.iloc[i-1] - af * (ep - psar.iloc[i-1])
                if low.iloc[i] < ep:
                    ep = low.iloc[i]
                    af = min(af + af_step, af_max)
                if high.iloc[i] > psar.iloc[i]:
                    trend.iloc[i] = 1
                    psar.iloc[i] = ep
                    ep = high.iloc[i]
                    af = af_start
        
        signals = pd.Series(0, index=data.index)
        signals[trend == 1] = 1
        signals[trend == -1] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0
        
        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade
        
        if volatility > 0:
            shares = risk_amount / (2 * volatility)
        else:
            shares = 0
        
        return round(shares, 2)

# ============================================================================
# 3. Donchian 通道
# ============================================================================

class DonchianChannelOptimized(BaseStrategy):
    """優化的 Donchian 通道策略"""
    
    def __init__(self, period: int = 20, use_breakout_filter: bool = True,
                 volume_confirmation: bool = True):
        super().__init__('Donchian Channel Optimized', {
            'period': period,
            'use_breakout_filter': use_breakout_filter,
            'volume_confirmation': volume_confirmation
        }, category='trend')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        period = self.params['period']
        
        upper = data['high'].rolling(window=period).max()
        lower = data['low'].rolling(window=period).min()
        
        signals = pd.Series(0, index=data.index)
        
        # 突破上軌 → 買入
        breakout_up = data['close'] > upper.shift(1)
        signals[breakout_up] = 1
        
        # 跌破下軌 → 賣出
        breakout_down = data['close'] < lower.shift(1)
        signals[breakout_down] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0
        
        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade
        
        if volatility > 0:
            shares = risk_amount / (2 * volatility)
        else:
            shares = 0
        
        return round(shares, 2)

# ============================================================================
# 4. 均線帶 Ribbon
# ============================================================================

class MARibbonOptimized(BaseStrategy):
    """優化的均線帶策略"""
    
    def __init__(self, short_period: int = 10, long_period: int = 30,
                 num_mas: int = 5, use_ribbon_alignment: bool = True):
        super().__init__('MA Ribbon Optimized', {
            'short_period': short_period,
            'long_period': long_period,
            'num_mas': num_mas,
            'use_ribbon_alignment': use_ribbon_alignment
        }, category='trend')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        short = self.params['short_period']
        long = self.params['long_period']
        num_mas = self.params['num_mas']
        
        # 創建均線帶
        mas = []
        for i in range(num_mas):
            period = short + (long - short) * i / (num_mas - 1)
            ma = data['close'].ewm(span=int(period), adjust=False).mean()
            mas.append(ma)
        
        # 均線帶多頭排列
        bullish = pd.Series(True, index=data.index)
        for i in range(len(mas)-1):
            bullish = bullish & (mas[i] > mas[i+1])
        
        # 均線帶空頭排列
        bearish = pd.Series(True, index=data.index)
        for i in range(len(mas)-1):
            bearish = bearish & (mas[i] < mas[i+1])
        
        signals = pd.Series(0, index=data.index)
        signals[bullish] = 1
        signals[bearish] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0
        
        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade
        
        if volatility > 0:
            shares = risk_amount / (2 * volatility)
        else:
            shares = 0
        
        return round(shares, 2)

# ============================================================================
# 回測引擎
# ============================================================================

class StrategyBacktester:
    """策略回測引擎"""
    
    def __init__(self, initial_capital: float = 100000.0,
                 commission_rate: float = 0.001, slippage: float = 0.001):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
    
    def backtest(self, data: pd.DataFrame, strategy: BaseStrategy) -> Dict:
        signals = strategy.generate_signals(data)
        close = data['close']
        
        capital = self.initial_capital
        position = 0
        trades = []
        portfolio_values = []
        
        for i in range(1, len(data)):
            signal = signals.iloc[i]
            price = close.iloc[i]
            
            if signal == 1 and position == 0:
                position = capital / price * (1 - self.commission_rate - self.slippage)
                capital = 0
                trades.append({'type': 'buy', 'price': price, 'index': i})
            
            elif signal == -1 and position > 0:
                capital = position * price * (1 - self.commission_rate - self.slippage)
                position = 0
                trades.append({'type': 'sell', 'price': price, 'index': i})
            
            portfolio_value = capital + position * price
            portfolio_values.append(portfolio_value)
        
        if position > 0:
            capital = position * close.iloc[-1] * (1 - self.commission_rate - self.slippage)
            portfolio_values.append(capital)
        
        portfolio_values = pd.Series(portfolio_values)
        returns = portfolio_values.pct_change().dropna()
        
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        cumulative = (portfolio_values / self.initial_capital).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        total_return = (portfolio_values.iloc[-1] - self.initial_capital) / self.initial_capital
        num_trades = len([t for t in trades if t['type'] == 'sell'])
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'num_trades': num_trades,
            'final_value': portfolio_values.iloc[-1]
        }

def load_data(start_date: str = '2020-01-01', end_date: str = '2023-12-31') -> pd.DataFrame:
    """加載歷史數據"""
    try:
        import akshare as ak
        
        df = ak.stock_zh_a_hist(symbol='000001.SZ', period="daily", 
                                start_date=start_date.replace('-', ''),
                                end_date=end_date.replace('-', ''),
                                adjust="qfq")
        
        df = df.rename(columns={
            '日期': 'date', '開盤': 'open', '收盤': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        })
        df.set_index('date', inplace=True)
        
        print(f"成功加載數據：{len(df)} 天")
        return df
    
    except Exception as e:
        print(f"加載數據失敗：{e}")
        print("使用模擬數據...")
        
        dates = pd.date_range(start_date, end_date, freq='B')
        np.random.seed(42)
        prices = 10 + np.cumsum(np.random.randn(len(dates)) * 0.2)
        
        df = pd.DataFrame({
            'open': prices + np.random.randn(len(dates)) * 0.1,
            'high': prices + np.abs(np.random.randn(len(dates))) * 0.3,
            'low': prices - np.abs(np.random.randn(len(dates))) * 0.3,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        df.index.name = 'date'
        
        return df

def optimize_strategy(data: pd.DataFrame, strategy_class, param_grid: Dict, strategy_name: str):
    """優化單一策略"""
    from itertools import product
    
    backtester = StrategyBacktester()
    results = []
    
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    
    total = np.prod([len(v) for v in param_values])
    print(f"\n開始 {strategy_name} 參數網格搜索，總共 {total} 種組合...")
    
    for i, values in enumerate(product(*param_values)):
        params = dict(zip(param_names, values))
        strategy = strategy_class(**params)
        result = backtester.backtest(data, strategy)
        result.update(params)
        results.append(result)
        
        if (i + 1) % 5 == 0:
            print(f"進度：{i+1}/{total}, 當前 Sharpe: {result['sharpe_ratio']:.3f}")
    
    df_results = pd.DataFrame(results).sort_values('sharpe_ratio', ascending=False)
    
    best = df_results.iloc[0]
    print(f"\n🏆 {strategy_name} 最佳結果:")
    print(f"  Sharpe: {best['sharpe_ratio']:.3f}")
    print(f"  總回報：{best['total_return']*100:.2f}%")
    print(f"  最大回撤：{best['max_drawdown']*100:.2f}%")
    
    return best, df_results

def main():
    """主函數"""
    print("=" * 60)
    print("Phase 2 中優先級策略批量優化 - 趨勢策略")
    print("=" * 60)
    
    # 加載數據
    print("\n[1/6] 加載歷史數據...")
    data = load_data()
    
    # 優化 EMA Cross
    print("\n[2/6] 優化 EMA Cross...")
    ema_best, ema_results = optimize_strategy(
        data, EMACrossOptimized,
        {
            'short_period': [9, 12, 15],
            'long_period': [21, 26, 30]
        },
        'EMA Cross'
    )
    
    # 優化 Parabolic SAR
    print("\n[3/6] 優化 Parabolic SAR...")
    psar_best, psar_results = optimize_strategy(
        data, ParabolicSAROptimized,
        {
            'af_start': [0.01, 0.02],
            'af_step': [0.01, 0.02],
            'af_max': [0.15, 0.20]
        },
        'Parabolic SAR'
    )
    
    # 優化 Donchian
    print("\n[4/6] 優化 Donchian Channel...")
    donchian_best, donchian_results = optimize_strategy(
        data, DonchianChannelOptimized,
        {
            'period': [15, 20, 25]
        },
        'Donchian Channel'
    )
    
    # 優化 MA Ribbon
    print("\n[5/6] 優化 MA Ribbon...")
    ribbon_best, ribbon_results = optimize_strategy(
        data, MARibbonOptimized,
        {
            'short_period': [8, 10, 12],
            'long_period': [25, 30, 35],
            'num_mas': [4, 5, 6]
        },
        'MA Ribbon'
    )
    
    # 生成報告
    print("\n[6/6] 生成批量優化報告...")
    
    report = f"""# Phase 2 趨勢策略批量優化報告

**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**優化任務**: OPT-042, OPT-043, OPT-044, OPT-045  
**回測期間**: 3 年歷史數據

---

## 📊 優化結果總覽

| 策略 | Sharpe | 總回報 | 最大回撤 | 交易次數 |
|------|--------|--------|----------|----------|
| EMA Cross | {ema_best['sharpe_ratio']:.3f} | {ema_best['total_return']*100:.2f}% | {ema_best['max_drawdown']*100:.2f}% | - |
| Parabolic SAR | {psar_best['sharpe_ratio']:.3f} | {psar_best['total_return']*100:.2f}% | {psar_best['max_drawdown']*100:.2f}% | - |
| Donchian | {donchian_best['sharpe_ratio']:.3f} | {donchian_best['total_return']*100:.2f}% | {donchian_best['max_drawdown']*100:.2f}% | - |
| MA Ribbon | {ribbon_best['sharpe_ratio']:.3f} | {ribbon_best['total_return']*100:.2f}% | {ribbon_best['max_drawdown']*100:.2f}% | - |

---

## 🔧 最佳參數

### EMA Cross
| 參數 | 值 |
|------|-----|
| short_period | {int(ema_best['short_period'])} |
| long_period | {int(ema_best['long_period'])} |

### Parabolic SAR
| 參數 | 值 |
|------|-----|
| af_start | {psar_best['af_start']:.3f} |
| af_step | {psar_best['af_step']:.3f} |
| af_max | {psar_best['af_max']:.3f} |

### Donchian Channel
| 參數 | 值 |
|------|-----|
| period | {int(donchian_best['period'])} |

### MA Ribbon
| 參數 | 值 |
|------|-----|
| short_period | {int(ribbon_best['short_period'])} |
| long_period | {int(ribbon_best['long_period'])} |
| num_mas | {int(ribbon_best['num_mas'])} |

---

**報告完成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open('phase2_trend_optimization_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n✅ 報告已生成：phase2_trend_optimization_report.md")
    
    print("\n" + "=" * 60)
    print("Phase 2 趨勢策略批量優化完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
