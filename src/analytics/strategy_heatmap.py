#!/usr/bin/env python3
"""
策略信號熱力圖
可視化所有策略的信號分佈

作者：StocksX Team
創建日期：2026-03-22
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path

def generate_strategy_signals(all_strategies: Dict, data: pd.DataFrame) -> pd.DataFrame:
    """
    生成所有策略的信號矩陣
    
    Args:
        all_strategies: 策略字典 {name: class}
        data: OHLCV 數據
    
    Returns:
        信號矩陣 DataFrame (日期 x 策略)
    """
    signals_df = pd.DataFrame(index=data.index)
    
    for name, strategy_class in all_strategies.items():
        try:
            strategy = strategy_class()
            signals = strategy.generate_signals(data)
            signals_df[name] = signals
        except Exception as e:
            print(f"❌ {name}: {e}")
            signals_df[name] = 0
    
    return signals_df

def calculate_signal_statistics(signals_df: pd.DataFrame) -> pd.DataFrame:
    """
    計算信號統計
    
    Args:
        signals_df: 信號矩陣
    
    Returns:
        統計 DataFrame
    """
    stats = []
    
    for col in signals_df.columns:
        signals = signals_df[col]
        total = len(signals)
        non_zero = (signals != 0).sum()
        buy = (signals == 1).sum()
        sell = (signals == -1).sum()
        long_ratio = buy / non_zero if non_zero > 0 else 0
        
        # 信號連續性
        signal_changes = (signals.diff() != 0).sum()
        avg_holding = total / signal_changes if signal_changes > 0 else total
        
        stats.append({
            'strategy': col,
            'total_signals': non_zero,
            'buy_signals': buy,
            'sell_signals': sell,
            'signal_rate': non_zero / total * 100,
            'long_ratio': long_ratio * 100,
            'avg_holding_days': avg_holding
        })
    
    return pd.DataFrame(stats)

def generate_heatmap_html(signals_df: pd.DataFrame, output_path: str):
    """
    生成 HTML 熱力圖
    
    Args:
        signals_df: 信號矩陣
        output_path: 輸出路徑
    """
    # 簡化：只顯示最近 30 天
    recent_signals = signals_df.tail(30)
    
    # 生成顏色
    def color_map(val):
        if val == 1:
            return 'background-color: #4CAF50; color: white'  # 綠色買入
        elif val == -1:
            return 'background-color: #f44336; color: white'  # 紅色賣出
        else:
            return 'background-color: #f5f5f5; color: #999'  # 灰色無信號
    
    # 創建 HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>StocksX 策略信號熱力圖</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; font-size: 12px; }}
        th {{ background-color: #4CAF50; color: white; position: sticky; top: 0; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .legend {{ margin: 20px 0; }}
        .legend span {{ display: inline-block; width: 20px; height: 20px; margin-right: 10px; }}
        .buy {{ background-color: #4CAF50; }}
        .sell {{ background-color: #f44336; }}
        .hold {{ background-color: #f5f5f5; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1>🔥 StocksX 策略信號熱力圖</h1>
    <p>顯示最近 30 天所有策略的交易信號</p>
    
    <div class="legend">
        <strong>圖例:</strong>
        <span class="buy"></span>買入
        <span class="sell"></span>賣出
        <span class="hold"></span>無信號
    </div>
    
    <table>
        <thead>
            <tr>
                <th>日期</th>
"""
    
    # 添加策略列頭
    for col in recent_signals.columns:
        html += f"                <th>{col}</th>\n"
    
    html += "            </tr>\n        </thead>\n        <tbody>\n"
    
    # 添加數據行
    for date, row in recent_signals.iterrows():
        html += f"            <tr>\n"
        html += f"                <td style='text-align: left; font-weight: bold;'>{date.strftime('%Y-%m-%d')}</td>\n"
        for val in row:
            if val == 1:
                html += f"                <td style='background-color: #4CAF50; color: white;'>📈</td>\n"
            elif val == -1:
                html += f"                <td style='background-color: #f44336; color: white;'>📉</td>\n"
            else:
                html += f"                <td style='background-color: #f5f5f5; color: #999;'>-</td>\n"
        html += "            </tr>\n"
    
    html += """        </tbody>
    </table>
    
    <script>
        // 添加滾動和交互
        document.querySelectorAll('tr').forEach(row => {
            row.addEventListener('click', () => {
                row.style.outline = '2px solid #2196F3';
                setTimeout(() => row.style.outline = '', 1000);
            });
        });
    </script>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 熱力圖已保存：{output_path}")

def main():
    """主函數"""
    print("=" * 80)
    print("🔥 StocksX 策略信號熱力圖生成器")
    print("=" * 80)
    
    # 導入策略
    from strategies.trend import ALL_TREND_STRATEGIES
    from strategies.oscillator import ALL_OSCILLATOR_STRATEGIES
    from strategies.breakout import ALL_BREAKOUT_STRATEGIES
    from strategies.ai_ml import ALL_AI_ML_STRATEGIES
    from strategies.risk_management import ALL_RISK_STRATEGIES
    from strategies.microstructure import ALL_MICRO_STRATEGIES
    from strategies.macro import ALL_MACRO_STRATEGIES
    from strategies.statistical import ALL_STAT_STRATEGIES
    from strategies.pattern import ALL_PATTERN_STRATEGIES
    from strategies.execution import ALL_EXECUTION_STRATEGIES
    
    # 合併所有策略
    all_strategies = {}
    all_strategies.update(ALL_TREND_STRATEGIES)
    all_strategies.update(ALL_OSCILLATOR_STRATEGIES)
    all_strategies.update(ALL_BREAKOUT_STRATEGIES)
    all_strategies.update(ALL_AI_ML_STRATEGIES)
    all_strategies.update(ALL_RISK_STRATEGIES)
    all_strategies.update(ALL_MICRO_STRATEGIES)
    all_strategies.update(ALL_MACRO_STRATEGIES)
    all_strategies.update(ALL_STAT_STRATEGIES)
    all_strategies.update(ALL_PATTERN_STRATEGIES)
    all_strategies.update(ALL_EXECUTION_STRATEGIES)
    
    print(f"\n📊 策略數量：{len(all_strategies)}")
    
    # 生成測試數據
    print("\n⏳ 生成測試數據...")
    np.random.seed(42)
    n = 300
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
    
    # 生成信號
    print("\n⏳ 生成所有策略信號...")
    signals_df = generate_strategy_signals(all_strategies, data)
    print(f"✅ 信號矩陣：{signals_df.shape}")
    
    # 計算統計
    print("\n⏳ 計算信號統計...")
    stats_df = calculate_signal_statistics(signals_df)
    print(f"✅ 統計完成")
    
    # 顯示 Top 10 活躍策略
    print("\n📊 Top 10 最活躍策略:")
    top_10 = stats_df.nlargest(10, 'total_signals')
    for i, row in top_10.iterrows():
        print(f"  {i+1:2d}. {row['strategy']:<30s} {row['total_signals']:4d} 個信號 ({row['signal_rate']:.1f}%)")
    
    # 顯示 Top 10 最安靜策略
    print("\n📊 Top 10 最安靜策略:")
    bottom_10 = stats_df.nsmallest(10, 'total_signals')
    for i, row in bottom_10.iterrows():
        print(f"  {i+1:2d}. {row['strategy']:<30s} {row['total_signals']:4d} 個信號 ({row['signal_rate']:.1f}%)")
    
    # 生成熱力圖
    print("\n⏳ 生成 HTML 熱力圖...")
    output_dir = Path(__file__).parent.parent.parent / 'docs' / 'analytics'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    heatmap_path = output_dir / 'strategy_heatmap.html'
    generate_heatmap_html(signals_df, str(heatmap_path))
    
    # 保存統計數據
    stats_path = output_dir / 'strategy_signal_statistics.csv'
    stats_df.to_csv(stats_path, index=False)
    print(f"✅ 統計數據：{stats_path}")
    
    print("\n" + "=" * 80)
    print("✅ 策略信號熱力圖生成完成！")
    print("=" * 80)

if __name__ == '__main__':
    main()
