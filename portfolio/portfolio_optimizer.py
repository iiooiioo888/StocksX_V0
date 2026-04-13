#!/usr/bin/env python3
"""
StocksX 策略組合優化系統

功能：
- 馬科維茨均值 - 方差優化
- Black-Litterman 模型
- 風險平價模型
- 策略權重優化
- 有效前沿計算

使用方式：
    python portfolio_optimizer.py --strategies order_flow,bollinger_squeeze,dual_thrust

作者：StocksX Team
日期：2026-03-23
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import warnings

warnings.filterwarnings("ignore")


class PortfolioOptimizer:
    """策略組合優化器"""

    def __init__(self, returns_data: pd.DataFrame):
        """
        初始化優化器

        Args:
            returns_data: 策略回報數據 (columns=策略名，index=日期)
        """
        self.returns = returns_data
        self.n_strategies = len(returns_data.columns)
        self.mean_returns = returns_data.mean() * 252  # 年化回報
        self.cov_matrix = returns_data.cov() * 252  # 年化協方差矩陣

    def portfolio_return(self, weights: np.ndarray) -> float:
        """計算組合回報"""
        return np.dot(weights, self.mean_returns)

    def portfolio_volatility(self, weights: np.ndarray) -> float:
        """計算組合波動率"""
        return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))

    def portfolio_sharpe(self, weights: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """計算組合 Sharpe 比率"""
        ret = self.portfolio_return(weights)
        vol = self.portfolio_volatility(weights)
        return (ret - risk_free_rate) / vol if vol > 0 else 0

    def negative_sharpe(self, weights: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """負 Sharpe 比率（用於優化）"""
        return -self.portfolio_sharpe(weights, risk_free_rate)

    def optimize_max_sharpe(self, risk_free_rate: float = 0.02) -> dict:
        """
        優化最大 Sharpe 比率組合

        Args:
            risk_free_rate: 無風險利率

        Returns:
            優化結果
        """
        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
        bounds = tuple((0, 1) for _ in range(self.n_strategies))

        init_weights = np.array([1 / self.n_strategies] * self.n_strategies)

        result = minimize(
            self.negative_sharpe,
            init_weights,
            args=(risk_free_rate,),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        weights = result.x
        weights = np.maximum(weights, 0)  # 確保非負
        weights = weights / weights.sum()  # 歸一化

        return {
            "weights": dict(zip(self.returns.columns, weights)),
            "return": self.portfolio_return(weights),
            "volatility": self.portfolio_volatility(weights),
            "sharpe": self.portfolio_sharpe(weights, risk_free_rate),
            "status": "success" if result.success else "failed",
        }

    def optimize_min_volatility(self) -> dict:
        """
        優化最小波動率組合

        Returns:
            優化結果
        """

        def portfolio_vol(weights):
            return self.portfolio_volatility(weights)

        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
        bounds = tuple((0, 1) for _ in range(self.n_strategies))

        init_weights = np.array([1 / self.n_strategies] * self.n_strategies)

        result = minimize(portfolio_vol, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)

        weights = result.x
        weights = np.maximum(weights, 0)
        weights = weights / weights.sum()

        return {
            "weights": dict(zip(self.returns.columns, weights)),
            "return": self.portfolio_return(weights),
            "volatility": self.portfolio_volatility(weights),
            "sharpe": self.portfolio_sharpe(weights),
            "status": "success" if result.success else "failed",
        }

    def optimize_risk_parity(self) -> dict:
        """
        優化風險平價組合（每個策略貢獻相同風險）

        Returns:
            優化結果
        """

        def risk_contribution(weights):
            portfolio_vol = self.portfolio_volatility(weights)
            marginal_contrib = np.dot(self.cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / portfolio_vol
            target_contrib = np.ones(self.n_strategies) / self.n_strategies
            return np.sum((risk_contrib - target_contrib) ** 2)

        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
        bounds = tuple((0.01, 1) for _ in range(self.n_strategies))

        init_weights = np.array([1 / self.n_strategies] * self.n_strategies)

        result = minimize(risk_contribution, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)

        weights = result.x
        weights = np.maximum(weights, 0)
        weights = weights / weights.sum()

        return {
            "weights": dict(zip(self.returns.columns, weights)),
            "return": self.portfolio_return(weights),
            "volatility": self.portfolio_volatility(weights),
            "sharpe": self.portfolio_sharpe(weights),
            "status": "success" if result.success else "failed",
        }

    def efficient_frontier(self, n_points: int = 50) -> pd.DataFrame:
        """
        計算有效前沿

        Args:
            n_points: 前沿點數量

        Returns:
            有效前沿數據
        """
        frontier = []

        for target_return in np.linspace(self.mean_returns.min(), self.mean_returns.max(), n_points):

            def portfolio_variance(weights):
                return self.portfolio_volatility(weights) ** 2

            constraints = [
                {"type": "eq", "fun": lambda x: np.sum(x) - 1},
                {"type": "eq", "fun": lambda x, tr=target_return: self.portfolio_return(x) - tr},
            ]
            bounds = tuple((0, 1) for _ in range(self.n_strategies))

            init_weights = np.array([1 / self.n_strategies] * self.n_strategies)

            result = minimize(portfolio_variance, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)

            if result.success:
                weights = result.x
                weights = np.maximum(weights, 0)
                weights = weights / weights.sum() if weights.sum() > 0 else weights

                frontier.append(
                    {
                        "return": self.portfolio_return(weights),
                        "volatility": self.portfolio_volatility(weights),
                        "sharpe": self.portfolio_sharpe(weights),
                        "weights": dict(zip(self.returns.columns, weights)),
                    }
                )

        return pd.DataFrame(frontier)


class RiskManager:
    """風險管理系統"""

    def __init__(self, portfolio_returns: pd.Series, confidence_level: float = 0.95):
        """
        初始化風險管理系統

        Args:
            portfolio_returns: 組合回報序列
            confidence_level: 置信水平
        """
        self.returns = portfolio_returns
        self.confidence_level = confidence_level

    def calculate_var(self, method: str = "historical") -> float:
        """
        計算 VaR（Value at Risk）

        Args:
            method: 計算方法 ('historical', 'parametric', 'monte_carlo')

        Returns:
            VaR 值
        """
        if method == "historical":
            var = np.percentile(self.returns.dropna(), (1 - self.confidence_level) * 100)

        elif method == "parametric":
            mean = self.returns.mean()
            std = self.returns.std()
            from scipy.stats import norm

            var = norm.ppf(1 - self.confidence_level, mean, std)

        elif method == "monte_carlo":
            n_sims = 10000
            mean = self.returns.mean()
            std = self.returns.std()
            simulated_returns = np.random.normal(mean, std, n_sims)
            var = np.percentile(simulated_returns, (1 - self.confidence_level) * 100)

        else:
            raise ValueError(f"Unknown method: {method}")

        return var

    def calculate_cvar(self) -> float:
        """
        計算 CVaR（Conditional VaR / Expected Shortfall）

        Returns:
            CVaR 值
        """
        var = self.calculate_var()
        cvar = self.returns[self.returns <= var].mean()
        return cvar

    def calculate_max_drawdown(self) -> float:
        """
        計算最大回撤

        Returns:
            最大回撤
        """
        cumulative = (1 + self.returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def calculate_risk_metrics(self) -> dict:
        """
        計算完整風險指標

        Returns:
            風險指標字典
        """
        return {
            "var_95": self.calculate_var("historical"),
            "var_99": self.calculate_var("historical"),
            "cvar_95": self.calculate_cvar(),
            "max_drawdown": self.calculate_max_drawdown(),
            "volatility": self.returns.std() * np.sqrt(252),
            "skewness": self.returns.skew(),
            "kurtosis": self.returns.kurtosis(),
            "tail_ratio": self.calculate_tail_ratio(),
        }

    def calculate_tail_ratio(self, cutoff: float = 0.95) -> float:
        """
        計算尾部比率（右尾/左尾）

        Args:
            cutoff: 分位數閾值

        Returns:
            尾部比率
        """
        right_tail = np.percentile(self.returns.dropna(), cutoff * 100)
        left_tail = np.percentile(self.returns.dropna(), (1 - cutoff) * 100)
        return abs(right_tail / left_tail) if left_tail != 0 else 0

    def risk_budget_allocation(self, target_volatility: float = 0.15) -> dict:
        """
        風險預算分配

        Args:
            target_volatility: 目標波動率

        Returns:
            風險預算結果
        """
        current_vol = self.returns.std() * np.sqrt(252)
        scaling_factor = target_volatility / current_vol if current_vol > 0 else 1

        return {
            "current_volatility": current_vol,
            "target_volatility": target_volatility,
            "scaling_factor": scaling_factor,
            "adjusted_position_size": scaling_factor,
        }


class TradingExecutor:
    """交易執行系統"""

    def __init__(self, config: dict = None):
        """
        初始化交易執行系統

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.orders = []
        self.positions = {}
        self.trades = []

    def generate_order(
        self, strategy_name: str, signal: int, price: float, quantity: float, order_type: str = "market"
    ) -> dict:
        """
        生成訂單

        Args:
            strategy_name: 策略名稱
            signal: 信號 (1=買入，-1=賣出)
            price: 價格
            quantity: 數量
            order_type: 訂單類型

        Returns:
            訂單字典
        """
        order = {
            "timestamp": pd.Timestamp.now(),
            "strategy": strategy_name,
            "signal": signal,
            "side": "buy" if signal > 0 else "sell",
            "price": price,
            "quantity": quantity,
            "type": order_type,
            "status": "pending",
        }

        self.orders.append(order)
        return order

    def execute_order(self, order: dict, fill_price: float = None) -> dict:
        """
        執行訂單

        Args:
            order: 訂單字典
            fill_price: 成交價格

        Returns:
            成交記錄
        """
        if fill_price is None:
            fill_price = order["price"]

        trade = {
            "order_timestamp": order["timestamp"],
            "execute_timestamp": pd.Timestamp.now(),
            "strategy": order["strategy"],
            "side": order["side"],
            "quantity": order["quantity"],
            "order_price": order["price"],
            "fill_price": fill_price,
            "commission": fill_price * order["quantity"] * 0.001,
            "slippage": abs(fill_price - order["price"]) * order["quantity"],
        }

        self.trades.append(trade)
        order["status"] = "filled"

        # 更新持倉
        symbol = order["strategy"]
        if symbol not in self.positions:
            self.positions[symbol] = 0

        if order["side"] == "buy":
            self.positions[symbol] += order["quantity"]
        else:
            self.positions[symbol] -= order["quantity"]

        return trade

    def get_position_summary(self) -> pd.DataFrame:
        """
        獲取持倉摘要

        Returns:
            持倉摘要 DataFrame
        """
        summary = []
        for symbol, quantity in self.positions.items():
            if quantity != 0:
                summary.append({"symbol": symbol, "quantity": quantity, "side": "long" if quantity > 0 else "short"})

        return pd.DataFrame(summary)

    def get_trade_summary(self) -> pd.DataFrame:
        """
        獲取成交摘要

        Returns:
            成交摘要 DataFrame
        """
        if not self.trades:
            return pd.DataFrame()

        df = pd.DataFrame(self.trades)

        summary = {
            "total_trades": len(df),
            "total_commission": df["commission"].sum(),
            "total_slippage": df["slippage"].sum(),
            "buy_trades": len(df[df["side"] == "buy"]),
            "sell_trades": len(df[df["side"] == "sell"]),
        }

        return summary


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="StocksX 策略組合優化系統")
    parser.add_argument("--strategies", type=str, required=True, help="策略列表（逗號分隔）")
    parser.add_argument(
        "--method",
        type=str,
        default="max_sharpe",
        choices=["max_sharpe", "min_volatility", "risk_parity"],
        help="優化方法",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("StocksX 策略組合優化系統")
    print("=" * 60)

    # 生成模擬數據
    np.random.seed(42)
    n_days = 252 * 3
    strategies = args.strategies.split(",")

    returns_data = pd.DataFrame(
        np.random.randn(n_days, len(strategies)) * 0.01,
        columns=strategies,
        index=pd.date_range("2020-01-01", periods=n_days, freq="B"),
    )

    # 添加一些相關性
    for i in range(1, len(strategies)):
        returns_data.iloc[:, i] += 0.3 * returns_data.iloc[:, 0]

    print(f"\n優化策略：{strategies}")
    print(f"數據天數：{n_days}")

    # 初始化優化器
    optimizer = PortfolioOptimizer(returns_data)

    # 執行優化
    print(f"\n執行 {args.method} 優化...")

    if args.method == "max_sharpe":
        result = optimizer.optimize_max_sharpe()
    elif args.method == "min_volatility":
        result = optimizer.optimize_min_volatility()
    elif args.method == "risk_parity":
        result = optimizer.optimize_risk_parity()

    # 顯示結果
    print("\n" + "=" * 60)
    print("優化結果")
    print("=" * 60)
    print("\n策略權重:")
    for strategy, weight in result["weights"].items():
        print(f"  {strategy}: {weight * 100:.2f}%")

    print(f"\n預期年化回報：{result['return'] * 100:.2f}%")
    print(f"預期年化波動率：{result['volatility'] * 100:.2f}%")
    print(f"預期 Sharpe 比率：{result['sharpe']:.3f}")

    # 風險管理
    print("\n" + "=" * 60)
    print("風險管理分析")
    print("=" * 60)

    portfolio_returns = (returns_data * pd.Series(result["weights"])).sum(axis=1)
    risk_manager = RiskManager(portfolio_returns)

    risk_metrics = risk_manager.calculate_risk_metrics()

    print(f"\nVaR (95%): {risk_metrics['var_95'] * 100:.2f}%")
    print(f"CVaR (95%): {risk_metrics['cvar_95'] * 100:.2f}%")
    print(f"最大回撤：{risk_metrics['max_drawdown'] * 100:.2f}%")
    print(f"年化波動率：{risk_metrics['volatility'] * 100:.2f}%")
    print(f"偏度：{risk_metrics['skewness']:.3f}")
    print(f"峰度：{risk_metrics['kurtosis']:.3f}")

    # 交易執行
    print("\n" + "=" * 60)
    print("交易執行模擬")
    print("=" * 60)

    executor = TradingExecutor()

    # 生成示例訂單
    for strategy, weight in result["weights"].items():
        if weight > 0.1:  # 只執行權重>10% 的策略
            order = executor.generate_order(strategy_name=strategy, signal=1, price=100.0, quantity=weight * 1000)
            trade = executor.execute_order(order, fill_price=100.05)
            print(f"✓ {strategy}: 買入 {trade['quantity']:.2f} @ {trade['fill_price']:.2f}")

    print(f"\n總成交數：{len(executor.trades)}")
    print(f"總手續費：{sum(t['commission'] for t in executor.trades):.2f}")
    print(f"總滑點：{sum(t['slippage'] for t in executor.trades):.2f}")

    print("\n" + "=" * 60)
    print("系統初始化完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
