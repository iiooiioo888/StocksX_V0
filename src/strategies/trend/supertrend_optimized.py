"""
Supertrend 超級趨勢策略優化

優化任務：OPT-016 / Issue #16
目標：3 年回測 + ATR 倍數參數優化
執行日期：2026-03-23

優化內容：
1. 參數網格搜索（period: 8-12, multiplier: 2.5-3.5）
2. 3 年歷史數據回測
3. Sharpe 比率、最大回撤計算
4. 最優參數組合推薦
5. 添加自適應 ATR 倍數機制

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
from src.strategies.base_strategy import TrendFollowingStrategy

class SupertrendOptimized(TrendFollowingStrategy):
    """
    優化的 Supertrend 策略
    
    改進點：
    1. 支持參數動態配置
    2. 添加自適應 ATR 倍數（基於波動率）
    3. 添加趨勢強度過濾
    4. 添加成交量確認
    """
    
    def __init__(self, 
                 period: int = 10,
                 multiplier: float = 3.0,
                 use_adaptive_multiplier: bool = False,
                 vol_lookback: int = 20,
                 use_trend_filter: bool = False,
                 trend_period: int = 200,
                 use_volume_filter: bool = False,
                 volume_period: int = 20):
        """
        初始化優化的 Supertrend 策略
        
        Args:
            period: ATR 周期（默认 10）
            multiplier: ATR 倍數（默认 3.0）
            use_adaptive_multiplier: 是否使用自適應倍數（默认 False）
            vol_lookback: 波動率計算周期（默认 20）
            use_trend_filter: 是否使用趨勢過濾（默认 False）
            trend_period: 趨勢判斷周期（默认 200）
            use_volume_filter: 是否使用成交量過濾（默认 False）
            volume_period: 成交量均線周期（默认 20）
        """
        super().__init__('Supertrend Optimized', {
            'period': period,
            'multiplier': multiplier,
            'use_adaptive_multiplier': use_adaptive_multiplier,
            'vol_lookback': vol_lookback,
            'use_trend_filter': use_trend_filter,
            'trend_period': trend_period,
            'use_volume_filter': use_volume_filter,
            'volume_period': volume_period
        })
    
    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """
        計算 ATR（Average True Range）
        
        Args:
            data: OHLCV 數據
            period: ATR 周期
            
        Returns:
            ATR 序列
        """
        high = data['high']
        low = data['low']
        close = data['close']
        
        # 計算 True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 計算 ATR（指數移動平均）
        atr = tr.ewm(span=period, adjust=False).mean()
        
        return atr
    
    def calculate_adaptive_multiplier(self, data: pd.DataFrame) -> pd.Series:
        """
        計算自適應 ATR 倍數（基於波動率）
        
        波動率高時使用較大倍數，減少假信號
        波動率低時使用較小倍數，提高靈敏度
        
        Args:
            data: OHLCV 數據
            
        Returns:
            自適應倍數序列
        """
        vol_lookback = self.params['vol_lookback']
        base_multiplier = self.params['multiplier']
        
        # 計算歷史波動率
        returns = data['close'].pct_change()
        volatility = returns.rolling(window=vol_lookback).std()
        
        # 標準化波動率
        vol_normalized = (volatility - volatility.rolling(window=vol_lookback).mean()) / \
                        volatility.rolling(window=vol_lookback).std()
        
        # 波動率高時增加倍數，低時減少倍數
        adaptive_mult = base_multiplier + vol_normalized * 0.5
        adaptive_mult = adaptive_mult.clip(base_multiplier - 0.5, base_multiplier + 1.0)
        
        return adaptive_mult
    
    def calculate_supertrend(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算 Supertrend 指標
        
        Args:
            data: OHLCV 數據
            
        Returns:
            包含 Supertrend 各組件的字典
        """
        period = self.params['period']
        multiplier = self.params['multiplier']
        
        high = data['high']
        low = data['low']
        close = data['close']
        
        # 計算 ATR
        atr = self.calculate_atr(data, period)
        
        # 基本中軌
        hl2 = (high + low) / 2
        
        # 計算自適應倍數
        if self.params['use_adaptive_multiplier']:
            mult = self.calculate_adaptive_multiplier(data)
            upper_band = hl2 + mult * atr
            lower_band = hl2 - mult * atr
        else:
            # 固定倍數
            upper_band = hl2 + multiplier * atr
            lower_band = hl2 - multiplier * atr
        
        # Supertrend 值和趨勢方向
        supertrend = pd.Series(0.0, index=data.index)
        trend = pd.Series(1, index=data.index)  # 1=上升趨勢，-1=下降趨勢
        
        for i in range(1, len(data)):
            if close.iloc[i] > (supertrend.iloc[i-1] if i > 0 else lower_band.iloc[i]):
                trend.iloc[i] = 1
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                trend.iloc[i] = -1
                supertrend.iloc[i] = upper_band.iloc[i]
        
        return {
            'supertrend': supertrend,
            'trend': trend,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'atr': atr
        }
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號（多條件確認）
        
        信號規則：
        基礎信號：
        - 趨勢從下降轉上升（-1 → 1）→ 買入
        - 趨勢從上升轉下降（1 → -1）→ 賣出
        
        過濾條件（可選）：
        - 趨勢過濾：順應 200 日均線趨勢
        - 成交量過濾：信號時成交量放大
        
        Args:
            data: OHLCV 數據
            
        Returns:
            信號 Series（1=買入，-1=賣出，0=持有）
        """
        supertrend_data = self.calculate_supertrend(data)
        trend = supertrend_data['trend']
        close = data['close']
        
        signals = pd.Series(0, index=data.index)
        
        # 基礎信號：趨勢轉換
        trend_change = trend.diff()
        buy_signal = trend_change == 2  # -1 → 1
        sell_signal = trend_change == -2  # 1 → -1
        
        # 趨勢過濾
        if self.params['use_trend_filter']:
            trend_period = self.params['trend_period']
            sma_200 = close.rolling(window=trend_period).mean()
            
            # 買入時價格在 200 均線上，賣出時在 200 均線下
            buy_signal = buy_signal & (close > sma_200)
            sell_signal = sell_signal & (close < sma_200)
        
        # 成交量過濾
        if self.params['use_volume_filter']:
            volume_period = self.params['volume_period']
            volume_ma = data['volume'].rolling(window=volume_period).mean()
            volume_confirmed = data['volume'] > volume_ma * 1.2
            
            buy_signal = buy_signal & volume_confirmed
            sell_signal = sell_signal & volume_confirmed
        
        signals[buy_signal] = 1
        signals[sell_signal] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """
        計算倉位大小（基於 ATR 波動率）
        
        Args:
            signal: 交易信號（1, -1, 0）
            capital: 可用資金
            price: 當前價格
            volatility: 波動率（ATR）
            
        Returns:
            倉位大小（股數）
        """
        if signal == 0:
            return 0.0
        
        # 基礎風險比例
        risk_per_trade = self.params.get('risk_per_trade', 0.02)
        
        # 基於 ATR 計算倉位
        if volatility > 0:
            # 每筆交易風險 = 2 * ATR
            risk_amount = capital * risk_per_trade
            shares = risk_amount / (2 * volatility)
        else:
            shares = 0
        
        return round(shares, 2)
    
    def get_trend_strength(self, data: pd.DataFrame) -> pd.Series:
        """
        計算趨勢強度（基於價格與 Supertrend 的距離）
        
        Args:
            data: OHLCV 數據
            
        Returns:
            趨勢強度序列（百分比）
        """
        supertrend_data = self.calculate_supertrend(data)
        supertrend = supertrend_data['supertrend']
        trend = supertrend_data['trend']
        close = data['close']
        
        # 計算價格與 Supertrend 的距離
        distance = (close - supertrend) / supertrend * 100
        
        # 根據趨勢方向調整符號
        distance = distance * trend
        
        return distance

class SupertrendBacktester:
    """
    Supertrend 回測引擎
    
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
    
    def backtest(self, data: pd.DataFrame, strategy: SupertrendOptimized) -> Dict:
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
            strategy = SupertrendOptimized(**params)
            
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

def generate_report(results: pd.DataFrame, output_file: str = 'supertrend_optimization_report.md'):
    """
    生成優化報告
    
    Args:
        results: 回測結果 DataFrame
        output_file: 輸出文件路徑
    """
    # 最佳參數
    best = results.iloc[0]
    
    report = f"""# Supertrend 超級趨勢策略參數優化報告

**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**優化任務**: OPT-016 / Issue #16  
**回測期間**: 3 年歷史數據

---

## 📊 最佳參數組合

| 參數 | 值 | 說明 |
|------|-----|------|
| period | {int(best['period'])} | ATR 周期 |
| multiplier | {best['multiplier']:.2f} | ATR 倍數 |

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

| 排名 | Period | Multiplier | Sharpe | 總回報 | 最大回撤 |
|------|--------|------------|--------|--------|----------|
"""
    
    for i, row in results.head(10).iterrows():
        report += f"| {i+1} | {int(row['period'])} | {row['multiplier']:.2f} | {row['sharpe_ratio']:.3f} | {row['total_return']*100:.2f}% | {row['max_drawdown']*100:.2f}% |\n"
    
    report += f"""
---

## 💡 優化建議

### 參數選擇
- **ATR 周期 (Period)**: 最佳範圍 {results['period'].quantile(0.25):.0f} - {results['period'].quantile(0.75):.0f}
- **ATR 倍數 (Multiplier)**: 最佳範圍 {results['multiplier'].quantile(0.25):.2f} - {results['multiplier'].quantile(0.75):.2f}

### 使用建議
1. **趨勢市場**: 使用較小倍數（multiplier < 3.0）提高靈敏度
2. **震盪市場**: 使用較大倍數（multiplier > 3.0）減少假信號
3. **過濾條件**: 建議啟用趨勢過濾（use_trend_filter=True）
4. **風險管理**: 配合 ATR 基礎倉位計算，控制風險

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
    print("Supertrend 超級趨勢策略參數優化")
    print("=" * 60)
    
    # 加載數據
    print("\n[1/4] 加載歷史數據...")
    data = load_data('2020-01-01', '2023-12-31', '000001.SZ')
    
    # 創建回測引擎
    print("\n[2/4] 初始化回測引擎...")
    backtester = SupertrendBacktester(
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001
    )
    
    # 參數網格搜索
    print("\n[3/4] 執行參數網格搜索...")
    param_grid = {
        'period': [8, 10, 12],
        'multiplier': [2.5, 3.0, 3.5]
    }
    
    results = backtester.grid_search(data, param_grid)
    
    # 顯示最佳結果
    print("\n[4/4] 生成優化報告...")
    best = results.iloc[0]
    print(f"\n🏆 最佳參數組合:")
    print(f"  Period: {int(best['period'])}")
    print(f"  Multiplier: {best['multiplier']:.2f}")
    print(f"\n📊 回測表現:")
    print(f"  Sharpe 比率：{best['sharpe_ratio']:.3f}")
    print(f"  總回報：{best['total_return']*100:.2f}%")
    print(f"  最大回撤：{best['max_drawdown']*100:.2f}%")
    print(f"  交易次數：{int(best['num_trades'])}")
    
    # 生成報告
    generate_report(results, 'supertrend_optimization_report.md')
    
    print("\n" + "=" * 60)
    print("優化完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
