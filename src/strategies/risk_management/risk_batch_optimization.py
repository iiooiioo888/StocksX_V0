"""
風險管理策略批量優化

優化任務：OPT-030, OPT-031, OPT-032
目標：批量回測驗證 CVaR、Optimal Stop、Delta Hedge
執行日期：2026-03-23

優化內容：
1. CVaR 倉位控制 - 置信水平和回看周期優化
2. 最優停損 - ATR 倍數優化
3. Delta 對沖 - 再平衡閾值優化（需期權數據，使用模擬）
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.append('..')
from base_strategy import RiskManagementStrategy


# ============================================================================
# 1. CVaR 倉位控制優化
# ============================================================================

class CVaRPositionOptimized(RiskManagementStrategy):
    """優化的 CVaR 倉位控制"""
    
    def __init__(self, confidence_level: float = 0.95, lookback: int = 252,
                 max_position_pct: float = 0.3, use_dynamic_cvar: bool = True):
        super().__init__('CVaR Position Optimized', {
            'confidence_level': confidence_level,
            'lookback': lookback,
            'max_position_pct': max_position_pct,
            'use_dynamic_cvar': use_dynamic_cvar
        })
    
    def calculate_cvar(self, returns: pd.Series, confidence: float) -> float:
        """計算 CVaR"""
        if len(returns) == 0 or returns.isna().all():
            return 0
        
        var = returns.quantile(1 - confidence)
        cvar = returns[returns <= var].mean()
        
        return abs(cvar) if not pd.isna(cvar) else 0
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        confidence = self.params['confidence_level']
        max_position = self.params['max_position_pct']
        
        returns = data['close'].pct_change()
        volatility = returns.rolling(window=lookback).std()
        
        # 計算 CVaR
        cvar = returns.rolling(window=lookback).apply(
            lambda x: self.calculate_cvar(x, confidence)
        )
        
        signals = pd.Series(0, index=data.index)
        
        # CVaR 低時買入（風險低）
        cvar_low = cvar < cvar.rolling(window=lookback).quantile(0.3)
        signals[cvar_low] = 1
        
        # CVaR 高時賣出（風險高）
        cvar_high = cvar > cvar.rolling(window=lookback).quantile(0.7)
        signals[cvar_high] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0
        
        max_position = self.params['max_position_pct']
        position_value = capital * max_position
        shares = position_value / price
        
        return round(shares, 2)


# ============================================================================
# 2. 最優停損優化
# ============================================================================

class OptimalStopOptimized(RiskManagementStrategy):
    """優化的最優停損策略"""
    
    def __init__(self, atr_period: int = 14, atr_multiplier: float = 2.0,
                 use_trailing_stop: bool = True, trail_pct: float = 0.05):
        super().__init__('Optimal Stop Optimized', {
            'atr_period': atr_period,
            'atr_multiplier': atr_multiplier,
            'use_trailing_stop': use_trailing_stop,
            'trail_pct': trail_pct
        })
        
        self.entry_price = 0
        self.highest_price = 0
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        atr_period = self.params['atr_period']
        atr_mult = self.params['atr_multiplier']
        
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift(1))
        low_close = abs(data['low'] - data['close'].shift(1))
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_period).mean()
        
        # 計算止損位
        stop_loss = data['close'] - atr_mult * atr
        
        signals = pd.Series(0, index=data.index)
        
        # 價格跌破止損位時賣出
        break_stop = data['close'] < stop_loss
        signals[break_stop] = -1
        
        # 價格上漲時買入
        price_up = data['close'] > data['close'].shift(1)
        signals[price_up & ~break_stop] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0
        
        risk_per_trade = 0.02
        atr_mult = self.params['atr_multiplier']
        
        if volatility > 0:
            risk_amount = capital * risk_per_trade
            shares = risk_amount / (atr_mult * volatility)
        else:
            shares = 0
        
        return round(shares, 2)


# ============================================================================
# 3. Delta 對沖優化（簡化版）
# ============================================================================

class DynamicDeltaHedgeOptimized(RiskManagementStrategy):
    """優化的動態 Delta 對沖（簡化版，使用現貨模擬）"""
    
    def __init__(self, rebalance_threshold: float = 0.1, max_delta: float = 0.05,
                 hedge_ratio: float = 0.5, use_dynamic_hedge: bool = True):
        super().__init__('Dynamic Delta Hedge Optimized', {
            'rebalance_threshold': rebalance_threshold,
            'max_delta': max_delta,
            'hedge_ratio': hedge_ratio,
            'use_dynamic_hedge': use_dynamic_hedge
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        rebalance_threshold = self.params['rebalance_threshold']
        hedge_ratio = self.params['hedge_ratio']
        
        returns = data['close'].pct_change()
        volatility = returns.rolling(window=20).std()
        
        # 模擬 Delta（使用波動率作為代理）
        simulated_delta = volatility / volatility.rolling(window=50).mean()
        
        signals = pd.Series(0, index=data.index)
        
        # Delta 高時對沖（賣出）
        high_delta = simulated_delta > (1 + rebalance_threshold)
        signals[high_delta] = -1
        
        # Delta 低時平倉（買入）
        low_delta = simulated_delta < (1 - rebalance_threshold)
        signals[low_delta] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0
        
        hedge_ratio = self.params['hedge_ratio']
        position_value = capital * hedge_ratio
        shares = position_value / price
        
        return round(shares, 2)


# ============================================================================
# 回測引擎
# ============================================================================

class RiskStrategyBacktester:
    """風險管理策略回測引擎"""
    
    def __init__(self, initial_capital: float = 100000.0,
                 commission_rate: float = 0.001, slippage: float = 0.001):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
    
    def backtest(self, data: pd.DataFrame, strategy: RiskManagementStrategy) -> Dict:
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
    
    backtester = RiskStrategyBacktester()
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
    print("風險管理策略批量優化")
    print("=" * 60)
    
    # 加載數據
    print("\n[1/5] 加載歷史數據...")
    data = load_data()
    
    # 優化 CVaR
    print("\n[2/5] 優化 CVaR 倉位控制...")
    cvar_best, cvar_results = optimize_strategy(
        data, CVaRPositionOptimized,
        {
            'confidence_level': [0.95, 0.975, 0.99],
            'lookback': [126, 252],
            'max_position_pct': [0.2, 0.3]
        },
        'CVaR'
    )
    
    # 優化 Optimal Stop
    print("\n[3/5] 優化最優停損...")
    stop_best, stop_results = optimize_strategy(
        data, OptimalStopOptimized,
        {
            'atr_period': [10, 14, 18],
            'atr_multiplier': [1.5, 2.0, 2.5]
        },
        'Optimal Stop'
    )
    
    # 優化 Delta Hedge
    print("\n[4/5] 優化 Delta 對沖...")
    delta_best, delta_results = optimize_strategy(
        data, DynamicDeltaHedgeOptimized,
        {
            'rebalance_threshold': [0.05, 0.1, 0.15],
            'hedge_ratio': [0.3, 0.5]
        },
        'Delta Hedge'
    )
    
    # 生成報告
    print("\n[5/5] 生成批量優化報告...")
    
    report = f"""# 風險管理策略批量優化報告

**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**優化任務**: OPT-030, OPT-031, OPT-032  
**回測期間**: 3 年歷史數據

---

## 📊 優化結果總覽

| 策略 | Sharpe | 總回報 | 最大回撤 | 交易次數 |
|------|--------|--------|----------|----------|
| CVaR | {cvar_best['sharpe_ratio']:.3f} | {cvar_best['total_return']*100:.2f}% | {cvar_best['max_drawdown']*100:.2f}% | - |
| Optimal Stop | {stop_best['sharpe_ratio']:.3f} | {stop_best['total_return']*100:.2f}% | {stop_best['max_drawdown']*100:.2f}% | - |
| Delta Hedge | {delta_best['sharpe_ratio']:.3f} | {delta_best['total_return']*100:.2f}% | {delta_best['max_drawdown']*100:.2f}% | - |

---

## 🔧 最佳參數

### CVaR 倉位控制
| 參數 | 值 |
|------|-----|
| confidence_level | {cvar_best['confidence_level']:.3f} |
| lookback | {int(cvar_best['lookback'])} |
| max_position_pct | {cvar_best['max_position_pct']:.2f} |

### 最優停損
| 參數 | 值 |
|------|-----|
| atr_period | {int(stop_best['atr_period'])} |
| atr_multiplier | {stop_best['atr_multiplier']:.2f} |

### Delta 對沖
| 參數 | 值 |
|------|-----|
| rebalance_threshold | {delta_best['rebalance_threshold']:.3f} |
| hedge_ratio | {delta_best['hedge_ratio']:.2f} |

---

**報告完成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open('risk_management_optimization_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n✅ 報告已生成：risk_management_optimization_report.md")
    
    print("\n" + "=" * 60)
    print("批量優化完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
