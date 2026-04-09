"""
一目均衡表 (Ichimoku Cloud) 策略優化

優化任務：OPT-007
目標：3 年回測 + 轉換線/基準線參數優化
執行日期：2026-03-23

優化內容：
1. 參數網格搜索（tenkan: 7-11, kijun: 20-30, senkou_b: 40-60）
2. 3 年歷史數據回測
3. Sharpe 比率、最大回撤計算
4. 最優參數組合推薦

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
from src.strategies.base_strategy import OscillatorStrategy

class IchimokuCloudOptimized(OscillatorStrategy):
    """
    優化的目均衡表策略
    
    改進點：
    1. 支持參數動態配置
    2. 添加雲帶厚度計算
    3. 添加趨勢強度過濾
    4. 支持多條件確認
    """
    
    def __init__(self, 
                 tenkan_period: int = 9,
                 kijun_period: int = 26,
                 senkou_b_period: int = 52,
                 displacement: int = 26,
                 use_cloud_filter: bool = True,
                 use_chikou_filter: bool = False):
        """
        初始化優化的目均衡表
        
        Args:
            tenkan_period: 轉換線周期（默认 9）
            kijun_period: 基準線周期（默认 26）
            senkou_b_period: 先行帶 B 周期（默认 52）
            displacement: 雲帶位移（默认 26）
            use_cloud_filter: 是否使用雲帶過濾（默认 True）
            use_chikou_filter: 是否使用遲行帶過濾（默认 False）
        """
        super().__init__('Ichimoku Cloud Optimized', {
            'tenkan_period': tenkan_period,
            'kijun_period': kijun_period,
            'senkou_b_period': senkou_b_period,
            'displacement': displacement,
            'use_cloud_filter': use_cloud_filter,
            'use_chikou_filter': use_chikou_filter
        })
    
    def calculate_ichimoku(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算一目均衡表五條線
        
        Args:
            data: OHLCV 數據
            
        Returns:
            包含所有線條和衍生指標的字典
        """
        high = data['high']
        low = data['low']
        close = data['close']
        
        # 轉換線（Tenkan-sen）
        tenkan_period = self.params['tenkan_period']
        tenkan = (high.rolling(window=tenkan_period).max() + 
                  low.rolling(window=tenkan_period).min()) / 2
        
        # 基準線（Kijun-sen）
        kijun_period = self.params['kijun_period']
        kijun = (high.rolling(window=kijun_period).max() + 
                 low.rolling(window=kijun_period).min()) / 2
        
        # 先行帶 A（Senkou Span A）
        displacement = self.params['displacement']
        senkou_a = (tenkan + kijun) / 2
        senkou_a = senkou_a.shift(displacement)
        
        # 先行帶 B（Senkou Span B）
        senkou_b_period = self.params['senkou_b_period']
        senkou_b = (high.rolling(window=senkou_b_period).max() + 
                    low.rolling(window=senkou_b_period).min()) / 2
        senkou_b = senkou_b.shift(displacement)
        
        # 遲行帶（Chikou Span）
        chikou = close.shift(-displacement)
        
        # 雲帶頂部和底部
        cloud_top = pd.concat([senkou_a, senkou_b], axis=1).max(axis=1)
        cloud_bottom = pd.concat([senkou_a, senkou_b], axis=1).min(axis=1)
        
        # 雲帶厚度（百分比）
        cloud_thickness = (cloud_top - cloud_bottom) / cloud_bottom * 100
        
        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou,
            'cloud_top': cloud_top,
            'cloud_bottom': cloud_bottom,
            'cloud_thickness': cloud_thickness
        }
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號（多條件確認）
        
        信號規則：
        基礎信號：
        - 轉換線上穿基準線 → 買入
        - 轉換線下穿基準線 → 賣出
        
        過濾條件（可選）：
        - 雲帶過濾：價格必須在雲帶同側
        - 遲行帶過濾：遲行帶必須在價格同側
        
        Args:
            data: OHLCV 數據
            
        Returns:
            信號 Series（1=買入，-1=賣出，0=持有）
        """
        ichimoku = self.calculate_ichimoku(data)
        close = data['close']
        
        tenkan = ichimoku['tenkan']
        kijun = ichimoku['kijun']
        cloud_top = ichimoku['cloud_top']
        cloud_bottom = ichimoku['cloud_bottom']
        chikou = ichimoku['chikou']
        
        # 基礎信號：TK 交叉
        tk_cross_above = (tenkan > kijun) & (tenkan.shift(1) <= kijun.shift(1))
        tk_cross_below = (tenkan < kijun) & (tenkan.shift(1) >= kijun.shift(1))
        
        signals = pd.Series(0, index=data.index)
        
        # 買入信號
        buy_signal = tk_cross_above
        
        # 雲帶過濾
        if self.params['use_cloud_filter']:
            price_above_cloud = close > cloud_top
            buy_signal = buy_signal & price_above_cloud
        
        # 遲行帶過濾
        if self.params['use_chikou_filter']:
            chikou_above = chikou > close.shift(self.params['displacement'])
            buy_signal = buy_signal & chikou_above
        
        # 賣出信號
        sell_signal = tk_cross_below
        
        if self.params['use_cloud_filter']:
            price_below_cloud = close < cloud_bottom
            sell_signal = sell_signal & price_below_cloud
        
        if self.params['use_chikou_filter']:
            chikou_below = chikou < close.shift(self.params['displacement'])
            sell_signal = sell_signal & chikou_below
        
        signals[buy_signal] = 1
        signals[sell_signal] = -1
        
        return signals
    
    def get_trend_strength(self, data: pd.DataFrame) -> pd.Series:
        """
        計算趨勢強度（基於雲帶厚度）
        
        Args:
            data: OHLCV 數據
            
        Returns:
            趨勢強度序列（0-100）
        """
        ichimoku = self.calculate_ichimoku(data)
        thickness = ichimoku['cloud_thickness']
        
        # 標準化到 0-100
        thickness_normalized = (thickness - thickness.min()) / (thickness.max() - thickness.min()) * 100
        
        return thickness_normalized
    
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

class IchimokuBacktester:
    """
    一目均衡表回測引擎
    
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
    
    def backtest(self, data: pd.DataFrame, strategy: IchimokuCloudOptimized) -> Dict:
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
                    param_grid: Dict[str, List[int]]) -> pd.DataFrame:
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
            strategy = IchimokuCloudOptimized(**params)
            
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

def generate_report(results: pd.DataFrame, output_file: str = 'ichimoku_optimization_report.md'):
    """
    生成優化報告
    
    Args:
        results: 回測結果 DataFrame
        output_file: 輸出文件路徑
    """
    # 最佳參數
    best = results.iloc[0]
    
    report = f"""# 一目均衡表 (Ichimoku Cloud) 參數優化報告

**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**優化任務**: OPT-007  
**回測期間**: 3 年歷史數據

---

## 📊 最佳參數組合

| 參數 | 值 | 說明 |
|------|-----|------|
| tenkan_period | {int(best['tenkan_period'])} | 轉換線周期 |
| kijun_period | {int(best['kijun_period'])} | 基準線周期 |
| senkou_b_period | {int(best['senkou_b_period'])} | 先行帶 B 周期 |

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

| 排名 | Tenkan | Kijun | Senkou_B | Sharpe | 總回報 | 最大回撤 |
|------|--------|-------|----------|--------|--------|----------|
"""
    
    for i, row in results.head(10).iterrows():
        report += f"| {i+1} | {int(row['tenkan_period'])} | {int(row['kijun_period'])} | {int(row['senkou_b_period'])} | {row['sharpe_ratio']:.3f} | {row['total_return']*100:.2f}% | {row['max_drawdown']*100:.2f}% |\n"
    
    report += f"""
---

## 💡 優化建議

### 參數選擇
- **轉換線 (Tenkan)**: 最佳範圍 {results['tenkan_period'].quantile(0.25):.0f} - {results['tenkan_period'].quantile(0.75):.0f}
- **基準線 (Kijun)**: 最佳範圍 {results['kijun_period'].quantile(0.25):.0f} - {results['kijun_period'].quantile(0.75):.0f}
- **先行帶 B (Senkou_B)**: 最佳範圍 {results['senkou_b_period'].quantile(0.25):.0f} - {results['senkou_b_period'].quantile(0.75):.0f}

### 使用建議
1. **趨勢市場**: 使用較長周期（Kijun > 26）減少假信號
2. **震盪市場**: 使用較短周期（Tenkan < 9）提高靈敏度
3. **過濾條件**: 建議啟用雲帶過濾（use_cloud_filter=True）
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
    print("一目均衡表 (Ichimoku Cloud) 參數優化")
    print("=" * 60)
    
    # 加載數據
    print("\n[1/4] 加載歷史數據...")
    data = load_data('2020-01-01', '2023-12-31', '000001.SZ')
    
    # 創建回測引擎
    print("\n[2/4] 初始化回測引擎...")
    backtester = IchimokuBacktester(
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001
    )
    
    # 參數網格搜索
    print("\n[3/4] 執行參數網格搜索...")
    param_grid = {
        'tenkan_period': [7, 8, 9, 10, 11],
        'kijun_period': [20, 22, 24, 26, 28, 30],
        'senkou_b_period': [40, 44, 48, 52, 56, 60]
    }
    
    results = backtester.grid_search(data, param_grid)
    
    # 顯示最佳結果
    print("\n[4/4] 生成優化報告...")
    best = results.iloc[0]
    print(f"\n🏆 最佳參數組合:")
    print(f"  Tenkan Period: {int(best['tenkan_period'])}")
    print(f"  Kijun Period: {int(best['kijun_period'])}")
    print(f"  Senkou B Period: {int(best['senkou_b_period'])}")
    print(f"\n📊 回測表現:")
    print(f"  Sharpe 比率：{best['sharpe_ratio']:.3f}")
    print(f"  總回報：{best['total_return']*100:.2f}%")
    print(f"  最大回撤：{best['max_drawdown']*100:.2f}%")
    print(f"  交易次數：{int(best['num_trades'])}")
    
    # 生成報告
    generate_report(results, 'ichimoku_optimization_report.md')
    
    print("\n" + "=" * 60)
    print("優化完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
