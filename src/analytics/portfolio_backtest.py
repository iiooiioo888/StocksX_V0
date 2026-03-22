#!/usr/bin/env python3
"""
策略組合回測引擎
多策略組合績效分析

作者：StocksX Team
創建日期：2026-03-22
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class PortfolioBacktester:
    """策略組合回測器"""
    
    def __init__(self, initial_capital: float = 1000000):
        """
        初始化回測器
        
        Args:
            initial_capital: 初始資金
        """
        self.initial_capital = initial_capital
        self.results = {}
    
    def backtest_single_strategy(self, strategy, data: pd.DataFrame) -> Dict:
        """
        單一策略回測
        
        Args:
            strategy: 策略實例
            data: OHLCV 數據
        
        Returns:
            回測結果字典
        """
        # 生成信號
        signals = strategy.generate_signals(data)
        
        # 計算收益
        returns = data['close'].pct_change()
        
        # 策略持倉：1=多頭，-1=空頭，0=空倉
        positions = signals.shift(1)  # 信號隔日生效
        
        # 策略收益
        strategy_returns = positions * returns
        
        # 計算績效指標
        total_return = (1 + strategy_returns).cumprod().iloc[-1] - 1
        sharpe = self._calculate_sharpe(strategy_returns)
        max_dd = self._calculate_max_drawdown((1 + strategy_returns).cumprod())
        win_rate = self._calculate_win_rate(strategy_returns)
        
        return {
            'strategy': strategy.name,
            'total_return': total_return * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd * 100,
            'win_rate': win_rate * 100,
            'total_trades': (positions.diff() != 0).sum(),
            'final_value': self.initial_capital * (1 + total_return)
        }
    
    def backtest_portfolio(self, strategies: Dict, data: pd.DataFrame, 
                          weights: Optional[Dict] = None) -> Dict:
        """
        組合回測
        
        Args:
            strategies: 策略字典 {name: class}
            data: OHLCV 數據
            weights: 權重字典 {name: weight}
        
        Returns:
            組合回測結果
        """
        if weights is None:
            # 等權重
            weights = {name: 1.0 / len(strategies) for name in strategies.keys()}
        
        # 正規化權重
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        portfolio_returns = pd.Series(0, index=data.index)
        all_results = []
        
        for name, strategy_class in strategies.items():
            try:
                strategy = strategy_class()
                result = self.backtest_single_strategy(strategy, data)
                all_results.append(result)
                
                # 生成信號
                signals = strategy.generate_signals(data)
                positions = signals.shift(1)
                returns = data['close'].pct_change()
                
                # 加權收益
                weight = weights.get(name, 0)
                portfolio_returns += weight * positions * returns
                
            except Exception as e:
                print(f"❌ {name}: {e}")
        
        # 組合績效
        total_return = (1 + portfolio_returns).cumprod().iloc[-1] - 1
        sharpe = self._calculate_sharpe(portfolio_returns)
        max_dd = self._calculate_max_drawdown((1 + portfolio_returns).cumprod())
        
        return {
            'portfolio': {
                'total_return': total_return * 100,
                'sharpe_ratio': sharpe,
                'max_drawdown': max_dd * 100,
                'final_value': self.initial_capital * (1 + total_return),
                'num_strategies': len(strategies)
            },
            'strategies': all_results,
            'weights': weights,
            'returns_series': portfolio_returns
        }
    
    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """計算夏普比率"""
        if returns.std() == 0:
            return 0
        excess_returns = returns - risk_free_rate / 252
        return np.sqrt(252) * excess_returns.mean() / returns.std()
    
    def _calculate_max_drawdown(self, cum_returns: pd.Series) -> float:
        """計算最大回撤"""
        rolling_max = cum_returns.expanding().max()
        drawdown = (cum_returns - rolling_max) / rolling_max
        return abs(drawdown.min())
    
    def _calculate_win_rate(self, returns: pd.Series) -> float:
        """計算勝率"""
        non_zero = returns[returns != 0]
        if len(non_zero) == 0:
            return 0
        return (non_zero > 0).sum() / len(non_zero)
    
    def generate_report(self, results: Dict, output_path: str):
        """
        生成回測報告
        
        Args:
            results: 回測結果
            output_path: 輸出路徑
        """
        portfolio = results['portfolio']
        strategies = results['strategies']
        
        # 創建 HTML 報告
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>StocksX 策略組合回測報告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .metric h3 {{ margin: 0; font-size: 14px; opacity: 0.9; }}
        .metric p {{ margin: 10px 0 0; font-size: 28px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .positive {{ color: #27ae60; font-weight: bold; }}
        .negative {{ color: #e74c3c; font-weight: bold; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
        .badge-good {{ background: #d4edda; color: #155724; }}
        .badge-medium {{ background: #fff3cd; color: #856404; }}
        .badge-bad {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 StocksX 策略組合回測報告</h1>
        <p><strong>初始資金</strong>: ${self.initial_capital:,.0f} | <strong>策略數量</strong>: {portfolio['num_strategies']}</p>
        
        <h2>🎯 組合績效</h2>
        <div class="metrics">
            <div class="metric">
                <h3>總回報</h3>
                <p class="{'positive' if portfolio['total_return'] > 0 else 'negative'}">{portfolio['total_return']:+.2f}%</p>
            </div>
            <div class="metric">
                <h3>夏普比率</h3>
                <p>{portfolio['sharpe_ratio']:.2f}</p>
            </div>
            <div class="metric">
                <h3>最大回撤</h3>
                <p class="negative">-{portfolio['max_drawdown']:.2f}%</p>
            </div>
            <div class="metric">
                <h3>最終價值</h3>
                <p class="{'positive' if portfolio['total_return'] > 0 else 'negative'}">${portfolio['final_value']:,.0f}</p>
            </div>
        </div>
        
        <h2>📈 策略詳情</h2>
        <table>
            <thead>
                <tr>
                    <th>策略名</th>
                    <th>權重</th>
                    <th>總回報</th>
                    <th>夏普比率</th>
                    <th>最大回撤</th>
                    <th>勝率</th>
                    <th>交易次數</th>
                    <th>評級</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # 添加策略行
        for strat in sorted(strategies, key=lambda x: x['sharpe_ratio'], reverse=True):
            name = strat['strategy']
            weight = results['weights'].get(name, 0) * 100
            
            # 評級
            if strat['sharpe_ratio'] > 1.5:
                badge = '<span class="badge badge-good">⭐⭐⭐</span>'
            elif strat['sharpe_ratio'] > 0.5:
                badge = '<span class="badge badge-medium">⭐⭐</span>'
            else:
                badge = '<span class="badge badge-bad">⭐</span>'
            
            html += f"""
                <tr>
                    <td><strong>{name}</strong></td>
                    <td>{weight:.1f}%</td>
                    <td class="{'positive' if strat['total_return'] > 0 else 'negative'}">{strat['total_return']:+.2f}%</td>
                    <td>{strat['sharpe_ratio']:.2f}</td>
                    <td class="negative">-{strat['max_drawdown']:.2f}%</td>
                    <td>{strat['win_rate']:.1f}%</td>
                    <td>{strat['total_trades']}</td>
                    <td>{badge}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
        
        <h2>💡 分析建議</h2>
        <ul>
            <li><strong>分散投資</strong>: 使用多個低相關策略可以降低整體風險</li>
            <li><strong>動態調整</strong>: 根據市場環境調整策略權重</li>
            <li><strong>風險管理</strong>: 設置停損點，控制最大回撤</li>
            <li><strong>定期再平衡</strong>: 每月/每季調整策略權重至目標配置</li>
        </ul>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ 回測報告已保存：{output_path}")


def main():
    """主函數"""
    print("=" * 80)
    print("📊 StocksX 策略組合回測引擎")
    print("=" * 80)
    
    # 導入策略
    from strategies.trend import ALL_TREND_STRATEGIES
    from strategies.oscillator import ALL_OSCILLATOR_STRATEGIES
    from strategies.breakout import ALL_BREAKOUT_STRATEGIES
    
    # 選擇部分策略進行測試
    test_strategies = {}
    test_strategies.update(dict(list(ALL_TREND_STRATEGIES.items())[:5]))
    test_strategies.update(dict(list(ALL_OSCILLATOR_STRATEGIES.items())[:5]))
    test_strategies.update(dict(list(ALL_BREAKOUT_STRATEGIES.items())[:5]))
    
    print(f"\n📊 測試策略數量：{len(test_strategies)}")
    
    # 生成測試數據
    print("\n⏳ 生成測試數據...")
    np.random.seed(42)
    n = 500
    returns = np.random.normal(0.0005, 0.02, n)
    price = 100 * np.cumprod(1 + returns)
    
    data = pd.DataFrame({
        'open': price * (1 + np.random.uniform(-0.01, 0.01, n)),
        'high': price * (1 + np.random.uniform(0, 0.02, n)),
        'low': price * (1 - np.random.uniform(0, 0.02, n)),
        'close': price,
        'volume': np.random.uniform(1e6, 1e7, n)
    }, index=pd.date_range('2025-01-01', periods=n, freq='D'))
    
    print(f"✅ 數據生成完成：{len(data)} 天")
    
    # 創建回測器
    backtester = PortfolioBacktester(initial_capital=1000000)
    
    # 組合回測
    print("\n⏳ 執行組合回測...")
    results = backtester.backtest_portfolio(test_strategies, data)
    
    # 顯示結果
    portfolio = results['portfolio']
    print("\n" + "=" * 80)
    print("📊 組合回測結果")
    print("=" * 80)
    print(f"初始資金：${backtester.initial_capital:,.0f}")
    print(f"最終價值：${portfolio['final_value']:,.0f}")
    print(f"總回報：{portfolio['total_return']:+.2f}%")
    print(f"夏普比率：{portfolio['sharpe_ratio']:.2f}")
    print(f"最大回撤：-{portfolio['max_drawdown']:.2f}%")
    print(f"策略數量：{portfolio['num_strategies']}")
    
    # 生成報告
    print("\n⏳ 生成回測報告...")
    output_dir = Path(__file__).parent.parent.parent / 'docs' / 'analytics'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = output_dir / 'portfolio_backtest_report.html'
    backtester.generate_report(results, str(report_path))
    
    print("\n" + "=" * 80)
    print("✅ 策略組合回測完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
