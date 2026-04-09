"""
布林帶擠壓 (Bollinger Band Squeeze) 策略優化

優化任務：OPT-015 / Issue #15
目標：3 年回測 + 擠壓閾值參數優化
執行日期：2026-03-23

優化內容：
1. 參數網格搜索（period: 18-22, std_dev: 1.8-2.2, threshold: 0.03-0.08）
2. 3 年歷史數據回測
3. Sharpe 比率、最大回撤計算
4. 最優參數組合推薦
5. 添加自適應閾值機制

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

class BollingerSqueezeOptimized(BreakoutStrategy):
    """
    優化的布林帶擠壓策略
    
    改進點：
    1. 支持參數動態配置
    2. 添加自適應擠壓閾值（基於歷史帶寬分位數）
    3. 添加成交量確認
    4. 添加趨勢過濾（可選）
    """
    
    def __init__(self, 
                 period: int = 20,
                 std_dev: float = 2.0,
                 squeeze_threshold: float = 0.05,
                 use_adaptive_threshold: bool = False,
                 lookback_percentile: int = 250,
                 use_volume_filter: bool = False,
                 volume_multiplier: float = 1.5,
                 use_trend_filter: bool = False):
        """
        初始化優化的布林帶擠壓策略
        
        Args:
            period: 布林帶週期（默认 20）
            std_dev: 標準差倍數（默认 2.0）
            squeeze_threshold: 擠壓閾值（默认 0.05）
            use_adaptive_threshold: 是否使用自適應閾值（默认 False）
            lookback_percentile: 歷史帶寬計算周期（默认 250）
            use_volume_filter: 是否使用成交量過濾（默认 False）
            volume_multiplier: 成交量放大倍數（默认 1.5）
            use_trend_filter: 是否使用趨勢過濾（默认 False）
        """
        super().__init__('Bollinger Squeeze Optimized', {
            'period': period,
            'std_dev': std_dev,
            'squeeze_threshold': squeeze_threshold,
            'use_adaptive_threshold': use_adaptive_threshold,
            'lookback_percentile': lookback_percentile,
            'use_volume_filter': use_volume_filter,
            'volume_multiplier': volume_multiplier,
            'use_trend_filter': use_trend_filter
        })
    
    def calculate_bollinger(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算布林帶
        
        Args:
            data: OHLCV 數據
            
        Returns:
            包含布林帶各組件的字典
        """
        period = self.params['period']
        std_dev = self.params['std_dev']
        
        close = data['close']
        
        # 中軌（SMA）
        sma = close.rolling(window=period).mean()
        
        # 標準差
        std = close.rolling(window=period).std()
        
        # 上軌和下軌
        upper = sma + std_dev * std
        lower = sma - std_dev * std
        
        # 帶寬（Bandwidth）
        bandwidth = (upper - lower) / sma
        
        # %B 指標
        percent_b = (close - lower) / (upper - lower)
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower,
            'std': std,
            'bandwidth': bandwidth,
            'percent_b': percent_b
        }
    
    def calculate_adaptive_threshold(self, data: pd.DataFrame) -> pd.Series:
        """
        計算自適應擠壓閾值（基於歷史帶寬分位數）
        
        Args:
            data: OHLCV 數據
            
        Returns:
            自適應閾值序列
        """
        lookback = self.params['lookback_percentile']
        bollinger = self.calculate_bollinger(data)
        bandwidth = bollinger['bandwidth']
        
        # 計算歷史帶寬的百分位數（20% 分位數作為閾值）
        adaptive_threshold = bandwidth.rolling(window=lookback).quantile(0.2)
        
        return adaptive_threshold
    
    def calculate_volume_ratio(self, data: pd.DataFrame) -> pd.Series:
        """
        計算成交量比率（相對於移動平均）
        
        Args:
            data: OHLCV 數據
            
        Returns:
            成交量比率序列
        """
        volume = data['volume']
        volume_ma = volume.rolling(window=self.params['period']).mean()
        volume_ratio = volume / volume_ma
        
        return volume_ratio
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號（多條件確認）
        
        信號規則：
        基礎信號：
        - 擠壓結束（帶寬從低到高）
        - 價格突破上軌 → 買入
        - 價格跌破下軌 → 賣出
        
        過濾條件（可選）：
        - 成交量過濾：突破時成交量放大
        - 趨勢過濾：順應 200 日均線趨勢
        
        Args:
            data: OHLCV 數據
            
        Returns:
            信號 Series（1=買入，-1=賣出，0=持有）
        """
        bollinger = self.calculate_bollinger(data)
        close = data['close']
        upper = bollinger['upper']
        lower = bollinger['lower']
        bandwidth = bollinger['bandwidth']
        
        # 計算擠壓閾值
        if self.params['use_adaptive_threshold']:
            threshold = self.calculate_adaptive_threshold(data)
        else:
            threshold = self.params['squeeze_threshold']
        
        # 檢測擠壓（帶寬小於閾值）
        squeeze = bandwidth < threshold
        
        # 擠壓結束（從擠壓狀態恢復）
        squeeze_ended = squeeze.shift(1) & ~squeeze
        
        signals = pd.Series(0, index=data.index)
        
        # 買入信號：擠壓結束 + 突破上軌
        buy_signal = squeeze_ended & (close > upper)
        
        # 成交量過濾
        if self.params['use_volume_filter']:
            volume_ratio = self.calculate_volume_ratio(data)
            volume_confirmed = volume_ratio > self.params['volume_multiplier']
            buy_signal = buy_signal & volume_confirmed
        
        # 趨勢過濾
        if self.params['use_trend_filter']:
            sma_200 = close.rolling(window=200).mean()
            trend_up = close > sma_200
            buy_signal = buy_signal & trend_up
        
        # 賣出信號：擠壓結束 + 跌破下軌
        sell_signal = squeeze_ended & (close < lower)
        
        if self.params['use_volume_filter']:
            volume_ratio = self.calculate_volume_ratio(data)
            volume_confirmed = volume_ratio > self.params['volume_multiplier']
            sell_signal = sell_signal & volume_confirmed
        
        if self.params['use_trend_filter']:
            sma_200 = close.rolling(window=200).mean()
            trend_down = close < sma_200
            sell_signal = sell_signal & trend_down
        
        signals[buy_signal] = 1
        signals[sell_signal] = -1
        
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
        
        # 根據信號方向調整
        position_value = capital * risk_per_trade
        
        # 計算股數
        shares = position_value / price
        
        return round(shares, 2)
    
    def get_squeeze_strength(self, data: pd.DataFrame) -> pd.Series:
        """
        計算擠壓強度（帶寬的歷史百分位數）
        
        Args:
            data: OHLCV 數據
            
        Returns:
            擠壓強度序列（0-100，越低表示擠壓越緊）
        """
        lookback = self.params['lookback_percentile']
        bollinger = self.calculate_bollinger(data)
        bandwidth = bollinger['bandwidth']
        
        # 計算歷史百分位數
        squeeze_strength = bandwidth.rolling(window=lookback).apply(
            lambda x: (x.iloc[-1] < x).mean() * 100
        )
        
        return squeeze_strength

class BollingerSqueezeBacktester:
    """
    布林帶擠壓回測引擎
    
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
    
    def backtest(self, data: pd.DataFrame, strategy: BollingerSqueezeOptimized) -> Dict:
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
            strategy = BollingerSqueezeOptimized(**params)
            
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
    
    Args:
        start_date: 開始日期
        end_date: 結束日期
        symbol: 股票代碼
        
    Returns:
        OHLCV 數據
    """
    try:
        import akshare as ak
        
        # 獲取 A 股歷史數據
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                start_date=start_date.replace('-', ''),
                                end_date=end_date.replace('-', ''),
                                adjust="qfq")
        
        # 重命名列
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
        
        # 生成模擬數據
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

def generate_report(results: pd.DataFrame, output_file: str = 'bollinger_squeeze_optimization_report.md'):
    """
    生成優化報告
    
    Args:
        results: 回測結果 DataFrame
        output_file: 輸出文件路徑
    """
    # 最佳參數
    best = results.iloc[0]
    
    report = f"""# 布林帶擠壓 (Bollinger Band Squeeze) 參數優化報告

**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**優化任務**: OPT-015 / Issue #15  
**回測期間**: 3 年歷史數據

---

## 📊 最佳參數組合

| 參數 | 值 | 說明 |
|------|-----|------|
| period | {int(best['period'])} | 布林帶週期 |
| std_dev | {best['std_dev']:.2f} | 標準差倍數 |
| squeeze_threshold | {best['squeeze_threshold']:.3f} | 擠壓閾值 |

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

| 排名 | Period | Std_Dev | Threshold | Sharpe | 總回報 | 最大回撤 |
|------|--------|---------|-----------|--------|--------|----------|
"""
    
    for i, row in results.head(10).iterrows():
        report += f"| {i+1} | {int(row['period'])} | {row['std_dev']:.2f} | {row['squeeze_threshold']:.3f} | {row['sharpe_ratio']:.3f} | {row['total_return']*100:.2f}% | {row['max_drawdown']*100:.2f}% |\n"
    
    report += f"""
---

## 💡 優化建議

### 參數選擇
- **週期 (Period)**: 最佳範圍 {results['period'].quantile(0.25):.0f} - {results['period'].quantile(0.75):.0f}
- **標準差 (Std_Dev)**: 最佳範圍 {results['std_dev'].quantile(0.25):.2f} - {results['std_dev'].quantile(0.75):.2f}
- **擠壓閾值 (Threshold)**: 最佳範圍 {results['squeeze_threshold'].quantile(0.25):.3f} - {results['squeeze_threshold'].quantile(0.75):.3f}

### 使用建議
1. **震盪市場**: 使用較小閾值（threshold < 0.05）提高靈敏度
2. **趨勢市場**: 使用較大閾值（threshold > 0.06）減少假信號
3. **過濾條件**: 建議啟用成交量過濾（use_volume_filter=True）
4. **風險管理**: 配合停損策略，控制最大回撤

---

## 📝 技術說明

### 回測設置
- 初始資金：¥100,000
- 手續費率：0.1%
- 滑點：0.1%
- 交易頻率：日線

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
    print("布林帶擠壓 (Bollinger Band Squeeze) 參數優化")
    print("=" * 60)
    
    # 加載數據
    print("\n[1/4] 加載歷史數據...")
    data = load_data('2020-01-01', '2023-12-31', '000001.SZ')
    
    # 創建回測引擎
    print("\n[2/4] 初始化回測引擎...")
    backtester = BollingerSqueezeBacktester(
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001
    )
    
    # 參數網格搜索
    print("\n[3/4] 執行參數網格搜索...")
    param_grid = {
        'period': [18, 20, 22],
        'std_dev': [1.8, 2.0, 2.2],
        'squeeze_threshold': [0.03, 0.05, 0.07, 0.09]
    }
    
    results = backtester.grid_search(data, param_grid)
    
    # 顯示最佳結果
    print("\n[4/4] 生成優化報告...")
    best = results.iloc[0]
    print(f"\n🏆 最佳參數組合:")
    print(f"  Period: {int(best['period'])}")
    print(f"  Std Dev: {best['std_dev']:.2f}")
    print(f"  Squeeze Threshold: {best['squeeze_threshold']:.3f}")
    print(f"\n📊 回測表現:")
    print(f"  Sharpe 比率：{best['sharpe_ratio']:.3f}")
    print(f"  總回報：{best['total_return']*100:.2f}%")
    print(f"  最大回撤：{best['max_drawdown']*100:.2f}%")
    print(f"  交易次數：{int(best['num_trades'])}")
    
    # 生成報告
    generate_report(results, 'bollinger_squeeze_optimization_report.md')
    
    print("\n" + "=" * 60)
    print("優化完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
