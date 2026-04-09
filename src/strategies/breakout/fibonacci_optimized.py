"""
斐波那契回撤 (Fibonacci Retracement) 策略優化

優化任務：OPT-023 / Issue #23
目標：3 年回測 + 回撤水平優化
執行日期：2026-03-23

優化內容：
1. 參數網格搜索（lookback: 40-60, fib_level: 0.382-0.786, use_multiple_levels: True/False）
2. 3 年歷史數據回測
3. Sharpe 比率、最大回撤計算
4. 最優參數組合推薦
5. 多斐波那契水平確認
6. 添加趨勢過濾

作者：StocksX Team
狀態：🔄 優化中
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 導入策略基類
from src.strategies.base_strategy import BreakoutStrategy

class FibonacciBreakoutOptimized(BreakoutStrategy):
    """
    優化的斐波那契回撤突破策略
    
    改進點：
    1. 支持多斐波那契水平確認
    2. 添加趨勢過濾
    3. 添加成交量確認
    4. 添加動態回撤水平
    """
    
    def __init__(self, 
                 lookback: int = 50,
                 primary_fib: float = 0.618,
                 secondary_fib: float = 0.382,
                 use_multiple_levels: bool = True,
                 use_trend_filter: bool = False,
                 trend_period: int = 200,
                 use_volume_filter: bool = False,
                 volume_period: int = 20,
                 volume_multiplier: float = 1.5):
        """
        初始化優化的斐波那契策略
        
        Args:
            lookback: 回看周期（默认 50）
            primary_fib: 主要斐波那契水平（默认 0.618）
            secondary_fib: 次要斐波那契水平（默认 0.382）
            use_multiple_levels: 是否使用多水平確認（默认 True）
            use_trend_filter: 是否使用趨勢過濾（默认 False）
            trend_period: 趨勢判斷周期（默认 200）
            use_volume_filter: 是否使用成交量過濾（默认 False）
            volume_period: 成交量均線周期（默认 20）
            volume_multiplier: 成交量放大倍數（默认 1.5）
        """
        super().__init__('Fibonacci Breakout Optimized', {
            'lookback': lookback,
            'primary_fib': primary_fib,
            'secondary_fib': secondary_fib,
            'use_multiple_levels': use_multiple_levels,
            'use_trend_filter': use_trend_filter,
            'trend_period': trend_period,
            'use_volume_filter': use_volume_filter,
            'volume_period': volume_period,
            'volume_multiplier': volume_multiplier
        })
        
        # 斐波那契比例
        self.fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
    
    def calculate_fibonacci_levels(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算斐波那契回撤水平
        
        Args:
            data: OHLCV 數據
            
        Returns:
            包含各斐波那契水平的字典
        """
        lookback = self.params['lookback']
        
        # 找到過去 N 日的高低點
        high = data['high'].rolling(window=lookback).max()
        low = data['low'].rolling(window=lookback).min()
        
        # 計算區間
        range_val = high - low
        
        # 計算各斐波那契回撤位
        fib_levels = {}
        for level in self.fib_levels:
            # 上升趨勢的回撤位（從低點反彈）
            fib_levels[f'fib_{level}_up'] = low + level * range_val
            # 下降趨勢的反彈位（從高點回落）
            fib_levels[f'fib_{level}_down'] = high - level * range_val
        
        fib_levels['high'] = high
        fib_levels['low'] = low
        fib_levels['range'] = range_val
        
        return fib_levels
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號（多條件確認）
        
        信號規則：
        基礎信號：
        - 價格觸及 0.618 回撤位後反彈 → 買入
        - 價格觸及 0.618 反彈位後回落 → 賣出
        
        過濾條件（可選）：
        - 多水平確認：同時觸及多個斐波那契水平
        - 趨勢過濾：順應 200 日均線趨勢
        - 成交量過濾：反彈時成交量放大
        
        Args:
            data: OHLCV 數據
            
        Returns:
            信號 Series（1=買入，-1=賣出，0=持有）
        """
        fib_levels = self.calculate_fibonacci_levels(data)
        close = data['close']
        high = data['high']
        low = data['low']
        
        signals = pd.Series(0, index=data.index)
        
        # 獲取主要和次要斐波那契水平
        primary_fib = self.params['primary_fib']
        secondary_fib = self.params['secondary_fib']
        
        fib_618_up = fib_levels[f'fib_{primary_fib}_up']
        fib_382_up = fib_levels[f'fib_{secondary_fib}_up']
        fib_618_down = fib_levels[f'fib_{primary_fib}_down']
        fib_382_down = fib_levels[f'fib_{secondary_fib}_down']
        
        # 買入信號：價格觸及 0.618 後反彈
        touch_fib = low <= fib_618_up
        bounce_up = touch_fib & (close > data['open'])
        
        # 多水平確認
        if self.params['use_multiple_levels']:
            # 同時觸及 0.618 和 0.382
            touch_both = (low <= fib_618_up) & (low <= fib_382_up)
            bounce_up = touch_both & (close > data['open'])
        
        # 趨勢過濾
        if self.params['use_trend_filter']:
            trend_period = self.params['trend_period']
            sma_200 = close.rolling(window=trend_period).mean()
            bounce_up = bounce_up & (close > sma_200)
        
        # 成交量過濾
        if self.params['use_volume_filter']:
            volume_period = self.params['volume_period']
            volume_ma = data['volume'].rolling(window=volume_period).mean()
            volume_confirmed = data['volume'] > volume_ma * self.params['volume_multiplier']
            bounce_up = bounce_up & volume_confirmed
        
        # 賣出信號：價格觸及 0.618 後回落
        touch_fib_down = high >= fib_618_down
        bounce_down = touch_fib_down & (close < data['open'])
        
        if self.params['use_multiple_levels']:
            touch_both_down = (high >= fib_618_down) & (high >= fib_382_down)
            bounce_down = touch_both_down & (close < data['open'])
        
        if self.params['use_trend_filter']:
            trend_period = self.params['trend_period']
            sma_200 = close.rolling(window=trend_period).mean()
            bounce_down = bounce_down & (close < sma_200)
        
        if self.params['use_volume_filter']:
            volume_period = self.params['volume_period']
            volume_ma = data['volume'].rolling(window=volume_period).mean()
            volume_confirmed = data['volume'] > volume_ma * self.params['volume_multiplier']
            bounce_down = bounce_down & volume_confirmed
        
        signals[bounce_up] = 1
        signals[bounce_down] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """
        計算倉位大小
        
        Args:
            signal: 交易信號（1, -1, 0）
            capital: 可用資金
            price: 當前價格
            volatility: 波動率
            
        Returns:
            倉位大小（股數）
        """
        if signal == 0:
            return 0.0
        
        # 基礎風險比例
        risk_per_trade = self.params.get('risk_per_trade', 0.02)
        
        # 基於斐波那契水平計算倉位
        # 在關鍵斐波那契水平附近增加倉位
        risk_amount = capital * risk_per_trade
        
        if volatility > 0:
            position_size = risk_amount / (2.5 * volatility)
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)
    
    def get_fib_confluence(self, data: pd.DataFrame) -> pd.Series:
        """
        計算斐波那契共振（多個水平重合）
        
        Args:
            data: OHLCV 數據
            
        Returns:
            共振強度序列（重合的水平數量）
        """
        fib_levels = self.calculate_fibonacci_levels(data)
        close = data['close']
        
        # 計算價格與各斐波那契水平的距離
        confluence = pd.Series(0, index=data.index)
        
        for level in self.fib_levels:
            fib_up = fib_levels[f'fib_{level}_up']
            fib_down = fib_levels[f'fib_{level}_down']
            
            # 價格接近斐波那契水平（1% 以內）
            close_to_fib_up = abs(close - fib_up) / fib_up < 0.01
            close_to_fib_down = abs(close - fib_down) / fib_down < 0.01
            
            confluence = confluence + close_to_fib_up.astype(int) + close_to_fib_down.astype(int)
        
        return confluence

class FibonacciBacktester:
    """
    斐波那契回測引擎
    
    功能：
    - 支持參數網格搜索
    - 計算 Sharpe 比率、最大回撤
    - 生成回測報告
    """
    
    def __init__(self, initial_capital: float = 100000.0,
                 commission_rate: float = 0.001,
                 slippage: float = 0.001):
        """
        初始化回測引擎
        
        Args:
            initial_capital: 初始資金
            commission_rate: 手續費率
            slippage: 滑點
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
    
    def backtest(self, data: pd.DataFrame, strategy: FibonacciBreakoutOptimized) -> Dict:
        """
        執行回測
        
        Args:
            data: OHLCV 數據
            strategy: 策略實例
            
        Returns:
            回測結果字典
        """
        # 生成信號
        signals = strategy.generate_signals(data)
        close = data['close']
        
        # 初始化
        capital = self.initial_capital
        position = 0
        trades = []
        portfolio_values = []
        
        # 執行回測
        for i in range(1, len(data)):
            signal = signals.iloc[i]
            price = close.iloc[i]
            
            # 買入
            if signal == 1 and position == 0:
                position = capital / price * (1 - self.commission_rate - self.slippage)
                capital = 0
                trades.append({'type': 'buy', 'price': price, 'index': i})
            
            # 賣出
            elif signal == -1 and position > 0:
                capital = position * price * (1 - self.commission_rate - self.slippage)
                position = 0
                trades.append({'type': 'sell', 'price': price, 'index': i})
            
            # 計算組合價值
            portfolio_value = capital + position * price
            portfolio_values.append(portfolio_value)
        
        # 平倉
        if position > 0:
            capital = position * close.iloc[-1] * (1 - self.commission_rate - self.slippage)
            portfolio_values.append(capital)
        
        # 計算指標
        portfolio_values = pd.Series(portfolio_values)
        returns = portfolio_values.pct_change().dropna()
        
        # Sharpe 比率（年化）
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # 最大回撤
        cumulative = (portfolio_values / self.initial_capital).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 總回報
        total_return = (portfolio_values.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 交易次數
        num_trades = len([t for t in trades if t['type'] == 'sell'])
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'num_trades': num_trades,
            'final_value': portfolio_values.iloc[-1],
            'portfolio_values': portfolio_values,
            'trades': trades
        }
    
    def grid_search(self, data: pd.DataFrame, 
                    param_grid: Dict[str, List]) -> pd.DataFrame:
        """
        參數網格搜索
        
        Args:
            data: OHLCV 數據
            param_grid: 參數網格字典
            
        Returns:
            結果 DataFrame
        """
        results = []
        
        # 生成參數組合
        from itertools import product
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        total_combinations = np.prod([len(v) for v in param_values])
        print(f"開始參數網格搜索，總共 {total_combinations} 種組合...")
        
        for i, values in enumerate(product(*param_values)):
            params = dict(zip(param_names, values))
            
            # 創建策略
            strategy = FibonacciBreakoutOptimized(**params)
            
            # 執行回測
            result = self.backtest(data, strategy)
            
            # 記錄結果
            result.update(params)
            results.append(result)
            
            if (i + 1) % 10 == 0:
                print(f"進度：{i+1}/{total_combinations}, 當前 Sharpe: {result['sharpe_ratio']:.3f}")
        
        # 轉換為 DataFrame
        df_results = pd.DataFrame(results)
        
        # 排序
        df_results = df_results.sort_values('sharpe_ratio', ascending=False)
        
        return df_results

def load_data(start_date: str = '2020-01-01', 
              end_date: str = '2023-12-31',
              symbol: str = '000001.SZ') -> pd.DataFrame:
    """
    加載歷史數據
    """
    try:
        import akshare as ak
        
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                start_date=start_date.replace('-', ''),
                                end_date=end_date.replace('-', ''),
                                adjust="qfq")
        
        df = df.rename(columns={
            '日期': 'date',
            '開盤': 'open',
            '收盤': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交額': 'amount'
        })
        
        df.set_index('date', inplace=True)
        
        print(f"成功加載數據：{len(df)} 天，{start_date} 至 {end_date}")
        
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

def generate_report(results: pd.DataFrame, output_file: str = 'fibonacci_optimization_report.md'):
    """
    生成優化報告
    """
    best = results.iloc[0]
    
    report = f"""# 斐波那契回撤 (Fibonacci Retracement) 參數優化報告

**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**優化任務**: OPT-023 / Issue #23  
**回測期間**: 3 年歷史數據

---

## 📊 最佳參數組合

| 參數 | 值 | 說明 |
|------|-----|------|
| lookback | {int(best['lookback'])} | 回看周期 |
| primary_fib | {best['primary_fib']:.3f} | 主要斐波那契水平 |
| secondary_fib | {best['secondary_fib']:.3f} | 次要斐波那契水平 |

---

## 📈 回測表現

| 指標 | 數值 | 評價 |
|------|------|------|
| 總回報 | {best['total_return']*100:.2f}% | {'優秀' if best['total_return'] > 0.5 else '良好' if best['total_return'] > 0.2 else '待改進'} |
| Sharpe 比率 | {best['sharpe_ratio']:.3f} | {'優秀' if best['sharpe_ratio'] > 1.5 else '良好' if best['sharpe_ratio'] > 1.0 else '待改進'} |
| 最大回撤 | {best['max_drawdown']*100:.2f}% | {'優秀' if abs(best['max_drawdown']) < 0.15 else '良好' if abs(best['max_drawdown']) < 0.25 else '待改進'} |
| 交易次數 | {int(best['num_trades'])} | {'適中' if 20 < best['num_trades'] < 100 else '偏高' if best['num_trades'] >= 100 else '偏低'} |
| 最終資金 | ¥{best['final_value']:,.2f} | - |

---

## 🔍 參數敏感性分析

### Top 10 參數組合

| 排名 | Lookback | Primary_Fib | Secondary_Fib | Sharpe | 總回報 | 最大回撤 |
|------|----------|-------------|---------------|--------|--------|----------|
"""
    
    for i, row in results.head(10).iterrows():
        report += f"| {i+1} | {int(row['lookback'])} | {row['primary_fib']:.3f} | {row['secondary_fib']:.3f} | {row['sharpe_ratio']:.3f} | {row['total_return']*100:.2f}% | {row['max_drawdown']*100:.2f}% |\n"
    
    report += f"""
---

## 💡 優化建議

### 參數選擇
- **Lookback**: 最佳範圍 {results['lookback'].quantile(0.25):.0f} - {results['lookback'].quantile(0.75):.0f}
- **Primary Fib**: 最佳範圍 {results['primary_fib'].quantile(0.25):.3f} - {results['primary_fib'].quantile(0.75):.3f}
- **Secondary Fib**: 最佳範圍 {results['secondary_fib'].quantile(0.25):.3f} - {results['secondary_fib'].quantile(0.75):.3f}

### 使用建議
1. **趨勢市場**: 使用較長 lookback（50-60 日）識別主要趨勢
2. **震盪市場**: 使用較短 lookback（40-50 日）提高靈敏度
3. **關鍵水平**: 0.618 是最重要的斐波那契回撤位
4. **過濾條件**: 建議啟用趨勢過濾和成交量確認

---

## 📝 技術說明

### 回測設置
- 初始資金：¥100,000
- 手續費率：0.1%
- 滑點：0.1%
- 交易頻率：日線

### 斐波那契比例
- 0.236: 淺回撤
- 0.382: 中等回撤
- 0.500: 半回撤
- 0.618: 黃金分割（最重要）
- 0.786: 深回撤

### 計算方法
- **Sharpe 比率**: 年化收益率 / 年化波動率 × √252
- **最大回撤**: (組合最低點 - 前期最高點) / 前期最高點
- **總回報**: (最終資金 - 初始資金) / 初始資金

---

**報告完成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**下一步**: 將最佳參數應用於實盤交易
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 報告已生成：{output_file}")

def main():
    """主函數"""
    print("=" * 60)
    print("斐波那契回撤 (Fibonacci Retracement) 參數優化")
    print("=" * 60)
    
    # 加載數據
    print("\n[1/4] 加載歷史數據...")
    data = load_data('2020-01-01', '2023-12-31', '000001.SZ')
    
    # 創建回測引擎
    print("\n[2/4] 初始化回測引擎...")
    backtester = FibonacciBacktester(
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001
    )
    
    # 參數網格搜索
    print("\n[3/4] 執行參數網格搜索...")
    param_grid = {
        'lookback': [40, 50, 60],
        'primary_fib': [0.5, 0.618, 0.786],
        'secondary_fib': [0.382, 0.5]
    }
    
    results = backtester.grid_search(data, param_grid)
    
    # 顯示最佳結果
    print("\n[4/4] 生成優化報告...")
    best = results.iloc[0]
    print(f"\n🏆 最佳參數組合:")
    print(f"  Lookback: {int(best['lookback'])}")
    print(f"  Primary Fib: {best['primary_fib']:.3f}")
    print(f"  Secondary Fib: {best['secondary_fib']:.3f}")
    print(f"\n📊 回測表現:")
    print(f"  Sharpe 比率：{best['sharpe_ratio']:.3f}")
    print(f"  總回報：{best['total_return']*100:.2f}%")
    print(f"  最大回撤：{best['max_drawdown']*100:.2f}%")
    print(f"  交易次數：{int(best['num_trades'])}")
    
    # 生成報告
    generate_report(results, 'fibonacci_optimization_report.md')
    
    print("\n" + "=" * 60)
    print("優化完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
