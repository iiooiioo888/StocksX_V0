"""
配对交易策略

统计套利策略，寻找协整的股票对进行均值回归交易
- 协整检验
- 价差 Z-score
- 均值回归信号
"""

from __future__ import annotations

import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")


class PairsTrading:
    """配对交易策略"""

    def __init__(
        self,
        lookback_window: int = 60,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.5,
        stoploss_zscore: float = 3.0,
    ):
        """
        初始化配对交易策略

        Args:
            lookback_window: 回溯窗口（用于计算均值和标准差）
            entry_zscore: 入场 Z-score 阈值
            exit_zscore: 出场 Z-score 阈值
            stoploss_zscore: 止损 Z-score 阈值
        """
        self.lookback_window = lookback_window
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.stoploss_zscore = stoploss_zscore

        self.spread = None
        self.hedge_ratio = None
        self.zscore = None

    def cointegration_test(self, price1: pd.Series, price2: pd.Series, max_lag: int = 10) -> tuple[float, float, bool]:
        """
        协整检验（Engle-Granger 两步法）

        Args:
            price1: 价格序列 1
            price2: 价格序列 2
            max_lag: 最大滞后阶数

        Returns:
            (hedge_ratio, p_value, is_cointegrated)
        """
        # 确保对齐
        df = pd.DataFrame({"p1": price1, "p2": price2}).dropna()

        if len(df) < self.lookback_window:
            return 0.0, 1.0, False

        # 第一步：OLS 回归
        p1 = df["p1"].values
        p2 = df["p2"].values

        # 计算对冲比率
        slope, intercept, r_value, p_value, std_err = stats.linregress(p2, p1)
        self.hedge_ratio = slope

        # 计算价差（残差）
        spread = p1 - (slope * p2 + intercept)

        # 第二步：ADF 检验（单位根检验）
        from statsmodels.tsa.stattools import adfuller

        adf_result = adfuller(spread, maxlag=max_lag, regression="c")
        p_value_adf = adf_result[1]

        # p < 0.05 表示拒绝原假设，存在协整关系
        is_cointegrated = p_value_adf < 0.05

        return self.hedge_ratio, p_value_adf, is_cointegrated

    def calculate_spread(self, price1: pd.Series, price2: pd.Series, hedge_ratio: float | None = None) -> pd.Series:
        """
        计算价差

        Args:
            price1: 价格序列 1
            price2: 价格序列 2
            hedge_ratio: 对冲比率（可选，不提供则自动计算）

        Returns:
            价差序列
        """
        df = pd.DataFrame({"p1": price1, "p2": price2}).dropna()

        if hedge_ratio is None:
            slope, intercept, _, _, _ = stats.linregress(df["p2"], df["p1"])
            hedge_ratio = slope

        self.hedge_ratio = hedge_ratio
        self.spread = df["p1"] - (hedge_ratio * df["p2"])

        return self.spread

    def calculate_zscore(self, spread: pd.Series | None = None) -> pd.Series:
        """
        计算 Z-score

        Args:
            spread: 价差序列（可选，不提供则使用已计算的）

        Returns:
            Z-score 序列
        """
        if spread is None:
            spread = self.spread

        if spread is None:
            raise ValueError("请先计算价差")

        # 滚动均值和标准差
        rolling_mean = spread.rolling(window=self.lookback_window).mean()
        rolling_std = spread.rolling(window=self.lookback_window).std()

        # Z-score
        self.zscore = (spread - rolling_mean) / (rolling_std + 1e-10)

        return self.zscore

    def generate_signal(self, price1: pd.Series, price2: pd.Series, update_hedge_ratio: bool = True) -> dict:
        """
        生成交易信号

        Args:
            price1: 价格序列 1
            price2: 价格序列 2
            update_hedge_ratio: 是否更新对冲比率

        Returns:
            交易信号字典
        """
        # 计算价差
        if update_hedge_ratio or self.hedge_ratio is None:
            hedge_ratio, p_value, is_coint = self.cointegration_test(price1, price2)

            if not is_coint:
                return {
                    "strategy": "pairs_trading",
                    "signal": 0,
                    "action": "HOLD",
                    "reason": "not_cointegrated",
                    "p_value": p_value,
                }
        else:
            self.calculate_spread(price1, price2, self.hedge_ratio)

        # 计算 Z-score
        if self.spread is None:
            self.calculate_spread(price1, price2, self.hedge_ratio)
        self.calculate_zscore()

        current_zscore = self.zscore.iloc[-1]

        # 生成信号
        if current_zscore > self.entry_zscore:
            # 价差过高：做空价差（做空 p1，做多 p2）
            signal = -1
            action = "SHORT_SPREAD"
            position = {"short": "p1", "long": "p2"}
        elif current_zscore < -self.entry_zscore:
            # 价差过低：做多价差（做多 p1，做空 p2）
            signal = 1
            action = "LONG_SPREAD"
            position = {"long": "p1", "short": "p2"}
        elif abs(current_zscore) < self.exit_zscore:
            # 价差回归：平仓
            signal = 0
            action = "CLOSE"
            position = {}
        else:
            # 持有
            signal = 0
            action = "HOLD"
            position = {}

        # 止损检查
        if abs(current_zscore) > self.stoploss_zscore:
            action = "STOP_LOSS"
            position = {}

        return {
            "strategy": "pairs_trading",
            "signal": signal,
            "action": action,
            "position": position,
            "zscore": float(current_zscore),
            "hedge_ratio": float(self.hedge_ratio) if self.hedge_ratio else None,
            "spread": float(self.spread.iloc[-1]) if self.spread is not None else None,
            "entry_threshold": self.entry_zscore,
            "exit_threshold": self.exit_zscore,
            "timestamp": int(datetime.now().timestamp() * 1000),
        }

    def backtest(
        self, price1: pd.Series, price2: pd.Series, initial_capital: float = 100000, transaction_cost: float = 0.001
    ) -> dict:
        """
        回测配对交易策略

        Args:
            price1: 价格序列 1
            price2: 价格序列 2
            initial_capital: 初始资金
            transaction_cost: 交易成本

        Returns:
            回测结果
        """
        # 计算对冲比率和价差
        hedge_ratio, p_value, is_coint = self.cointegration_test(price1, price2)

        if not is_coint:
            return {"error": "价格序列不协整", "p_value": p_value}

        self.calculate_spread(price1, price2, hedge_ratio)
        self.calculate_zscore(self.spread)  # 传入 spread 参数

        # 模拟交易
        capital = initial_capital
        position = 0  # 0=空仓，1=多价差，-1=空价差
        trades = []
        portfolio_values = []

        for i in range(self.lookback_window, len(price1)):
            zscore = self.zscore.iloc[i]
            p1_price = price1.iloc[i]
            p2_price = price2.iloc[i]

            # 开仓信号
            if position == 0:
                if zscore > self.entry_zscore:
                    # 空价差
                    position = -1
                    shares_p1 = (capital * 0.5) / p1_price
                    shares_p2 = (capital * 0.5) / p2_price
                    entry_p1 = p1_price
                    entry_p2 = p2_price
                    trades.append(
                        {"type": "OPEN_SHORT", "zscore": zscore, "shares_p1": shares_p1, "shares_p2": shares_p2}
                    )
                elif zscore < -self.entry_zscore:
                    # 多价差
                    position = 1
                    shares_p1 = (capital * 0.5) / p1_price
                    shares_p2 = (capital * 0.5) / p2_price
                    entry_p1 = p1_price
                    entry_p2 = p2_price
                    trades.append(
                        {"type": "OPEN_LONG", "zscore": zscore, "shares_p1": shares_p1, "shares_p2": shares_p2}
                    )

            # 平仓信号
            elif position != 0 and abs(zscore) < self.exit_zscore:
                if position == 1:
                    pnl = shares_p1 * (p1_price - entry_p1) - shares_p2 * (p2_price - entry_p2)
                else:
                    pnl = shares_p1 * (entry_p1 - p1_price) - shares_p2 * (entry_p2 - p2_price)

                capital += pnl * (1 - transaction_cost)
                trades.append({"type": "CLOSE", "zscore": zscore, "pnl": pnl})
                position = 0

            # 记录组合价值
            portfolio_values.append(capital)

        # 计算绩效指标
        portfolio_values = np.array(portfolio_values)
        returns = np.diff(portfolio_values) / portfolio_values[:-1]

        total_return = (portfolio_values[-1] - initial_capital) / initial_capital
        sharpe_ratio = np.sqrt(252) * returns.mean() / (returns.std() + 1e-10)
        max_drawdown = np.max(np.maximum.accumulate(portfolio_values) - portfolio_values) / np.max(portfolio_values)

        return {
            "strategy": "pairs_trading",
            "is_cointegrated": True,
            "hedge_ratio": hedge_ratio,
            "p_value": p_value,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "final_capital": portfolio_values[-1],
            "num_trades": len(trades),
            "trades": trades,
        }


# ════════════════════════════════════════════════════════════
# 使用示例
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 创建示例数据（两个相关的价格序列）
    np.random.seed(42)
    n = 500

    # 生成协整序列
    base = np.random.randn(n).cumsum()
    price1 = base + np.random.randn(n) * 0.5
    price2 = base * 0.8 + np.random.randn(n) * 0.3

    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    price1 = pd.Series(price1, index=dates)
    price2 = pd.Series(price2, index=dates)

    # 配对交易
    pt = PairsTrading(lookback_window=60, entry_zscore=2.0, exit_zscore=0.5)

    # 协整检验
    hedge_ratio, p_value, is_coint = pt.cointegration_test(price1, price2)
    print(f"对冲比率：{hedge_ratio:.4f}")
    print(f"ADF p-value: {p_value:.6f}")
    print(f"是否协整：{is_coint}")

    # 生成信号
    signal = pt.generate_signal(price1, price2)
    print(f"\n当前信号：{signal['action']}")
    print(f"Z-score: {signal['zscore']:.2f}")

    # 回测
    results = pt.backtest(price1, price2)
    print("\n回测结果:")
    print(f"  总收益：{results['total_return']:.2%}")
    print(f"  Sharpe: {results['sharpe_ratio']:.2f}")
    print(f"  最大回撤：{results['max_drawdown']:.2%}")
    print(f"  交易次数：{results['num_trades']}")
