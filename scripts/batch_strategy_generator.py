#!/usr/bin/env python3
"""
StocksX 批量策略生成器
自動生成剩餘策略的骨架和實現

使用方式：
python3 scripts/batch_strategy_generator.py --category breakout --batch 1
"""

import argparse
from pathlib import Path
from datetime import datetime

# 策略模板
STRATEGY_TEMPLATE = '''
# ============================================================================
# {strategy_num}. {strategy_name}
# ============================================================================

class {class_name}(OscillatorStrategy):
    """
    {strategy_name}

    {description}

    信號規則：
    {signal_rules}
    """

    def __init__(self, {params}):
        """
        初始化{strategy_name}

        Args:
            {param_docs}
        """
        super().__init__('{strategy_name}', {{
            {param_dict}
        }})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series
        """
        {calculations}

        signals = pd.Series(0, index=data.index)

        {signal_logic}

        return signals

    def calculate_position_size(self, signal: int, capital: float,
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = {risk_per_trade}
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / ({stop_loss} * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

'''

# 策略定義
STRATEGIES = {
    "breakout": [
        {
            "name": "雙推力突破",
            "class": "DualThrustBreakout",
            "description": "雙推力突破策略，基於開盤區間和波動率計算上下軌",
            "params": "lookback: int = 4, k1: float = 0.5, k2: float = 0.5",
            "param_dict": "'lookback': lookback,\n            'k1': k1,\n            'k2': k2",
            "calculations": """lookback = self.params['lookback']
        k1 = self.params['k1']
        k2 = self.params['k2']

        # 計算過去 N 日的 HH, LL, Close
        hh = data['high'].rolling(window=lookback).max()
        ll = data['low'].rolling(window=lookback).min()
        close_prev = data['close'].shift(1)

        # 計算上下軌
        upper_bound = close_prev + k1 * (hh - ll)
        lower_bound = close_prev - k2 * (hh - ll)""",
            "signal_logic": """# 上穿買入
        cross_above = (data['close'] > upper_bound) & (data['close'].shift(1) < upper_bound)
        signals[cross_above] = 1

        # 下穿賣出
        cross_below = (data['close'] < lower_bound) & (data['close'].shift(1) > lower_bound)
        signals[cross_below] = -1""",
            "risk_per_trade": "0.02",
            "stop_loss": "2",
        },
        {
            "name": "開盤區間突破",
            "class": "OpeningRangeBreakout",
            "description": "開盤區間突破策略（ORB），基於開盤後固定時間的區間突破",
            "params": "range_minutes: int = 30, stop_loss_pct: float = 0.02",
            "param_dict": "'range_minutes': range_minutes,\n            'stop_loss_pct': stop_loss_pct",
            "calculations": """# 簡化版：使用前一日高低點作為區間
        prev_high = data['high'].shift(1)
        prev_low = data['low'].shift(1)""",
            "signal_logic": """# 突破買入
        breakout_long = (data['high'] > prev_high) & (data['high'].shift(1) <= prev_high)
        signals[breakout_long] = 1

        # 突破賣出
        breakout_short = (data['low'] < prev_low) & (data['low'].shift(1) >= prev_low)
        signals[breakout_short] = -1""",
            "risk_per_trade": "0.02",
            "stop_loss": "2.5",
        },
    ],
    "risk": [
        {
            "name": "凱利公式倉位",
            "class": "KellyCriterion",
            "description": "凱利公式計算最優倉位比例",
            "params": "max_kelly: float = 0.25, lookback: int = 60",
            "param_dict": "'max_kelly': max_kelly,\n            'lookback': lookback",
            "calculations": """lookback = self.params['lookback']
        max_kelly = self.params['max_kelly']

        # 計算歷史勝率和盈虧比
        returns = data['close'].pct_change()
        winning_trades = (returns > 0).rolling(window=lookback).sum()
        total_trades = returns.rolling(window=lookback).count()

        win_rate = winning_trades / (total_trades + 1)

        avg_win = returns[returns > 0].rolling(window=lookback).mean()
        avg_loss = -returns[returns < 0].rolling(window=lookback).mean()

        win_loss_ratio = avg_win / (avg_loss + 1e-10)

        # 凱利公式：f = W - (1-W)/R
        kelly = win_rate - (1 - win_rate) / (win_loss_ratio + 1e-10)
        kelly = kelly.clip(0, max_kelly)""",
            "signal_logic": """# 凱利值高時買入
        signals[kelly > 0.1] = 1
        signals[kelly < 0.05] = 0""",
            "risk_per_trade": "0.015",
            "stop_loss": "2",
        },
    ],
}

def generate_strategy_file(category: str, batch: int = 1):
    """生成策略文件"""

    if category not in STRATEGIES:
        print(f"❌ 不支持的類別：{category}")
        return

    strategies = STRATEGIES[category]
    start_idx = (batch - 1) * 5

    # 創建文件內容
    header = f'''"""
{category.title()} 策略包 - Batch {batch}
包含 {len(strategies[start_idx : start_idx + 5])} 個策略

生成時間：{datetime.now().strftime("%Y-%m-%d %H:%M")}
狀態：🔄 已生成
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from ..base_strategy import BaseStrategy, OscillatorStrategy, BreakoutStrategy, RiskManagementStrategy

'''

    # 添加策略類
    strategy_classes = []
    for i, strat in enumerate(strategies[start_idx : start_idx + 5], start=start_idx + 1):
        template = STRATEGY_TEMPLATE.format(
            strategy_num=i,
            strategy_name=strat["name"],
            class_name=strat["class"],
            description=strat["description"],
            signal_rules=strat["description"],
            params=strat["params"],
            param_docs=strat["params"].replace(",", "\n            "),
            param_dict=strat["param_dict"],
            calculations=strat["calculations"],
            signal_logic=strat["signal_logic"],
            risk_per_trade=strat["risk_per_trade"],
            stop_loss=strat["stop_loss"],
        )
        strategy_classes.append(template)

    # 註冊表
    registry_name = f"{category.upper()}_STRATEGIES_BATCH_{batch}"
    registry = f"\n{registry_name} = {{\n"
    for strat in strategies[start_idx : start_idx + 5]:
        class_name = strat["class"]
        key = class_name[0].lower() + "".join(word[0].upper() + word[1:] for word in class_name.split("_")[1:])
        registry += f"    '{key.lower()}': {class_name},\n"
    registry += "}\n"

    # 寫入文件
    content = header + "\n".join(strategy_classes) + "\n" + registry

    # 確定文件路徑
    category_map = {
        "breakout": "breakout",
        "risk": "risk_management",
        "oscillator": "oscillator",
    }

    output_dir = Path(
        f"/home/admin/openclaw/workspace/StocksX_V0/src/strategies/{category_map.get(category, category)}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"batch_{batch}_strategies.py"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 已生成：{output_file}")
    print(f"   包含 {len(strategies[start_idx : start_idx + 5])} 個策略")

    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量生成策略")
    parser.add_argument(
        "--category",
        type=str,
        required=True,
        choices=["breakout", "risk", "oscillator", "macro", "statistical"],
        help="策略類別",
    )
    parser.add_argument("--batch", type=int, default=1, help="批次號")

    args = parser.parse_args()

    generate_strategy_file(args.category, args.batch)
