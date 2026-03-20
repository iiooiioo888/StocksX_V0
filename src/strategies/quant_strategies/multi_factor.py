"""
多因子策略

基于 Fama-French 三因子模型 + 动量/质量/低波因子
- 市场因子（MKT）
- 规模因子（SMB）
- 价值因子（HML）
- 动量因子（MOM）
- 质量因子（QMJ）
- 低波因子（BAB）
"""

from __future__ import annotations

import warnings
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class MultiFactorModel:
    """多因子模型"""

    def __init__(self, factors: list[str] = ["market", "size", "value", "momentum", "quality", "low_volatility"]):
        """
        初始化多因子模型

        Args:
            factors: 因子列表
        """
        self.factors = factors
        self.factor_loadings = {}
        self.factor_returns = {}
        self.alpha = None
        self.r_squared = None

    def calculate_market_factor(self, returns: pd.Series, benchmark_returns: pd.Series) -> pd.Series:
        """
        计算市场因子（MKT）

        Args:
            returns: 资产收益率
            benchmark_returns: 基准收益率（如大盘指数）

        Returns:
            市场因子暴露
        """
        # 市场因子 = 资产收益率 - 无风险利率（简化为基准收益率）
        excess_returns = returns - benchmark_returns
        return excess_returns

    def calculate_size_factor(self, market_cap: float, median_market_cap: float) -> float:
        """
        计算规模因子（SMB - Small Minus Big）

        Args:
            market_cap: 市值
            median_market_cap: 中位市值

        Returns:
            规模因子得分
        """
        # 小市值得分高
        if market_cap < median_market_cap:
            return 1.0
        else:
            return -1.0

    def calculate_value_factor(
        self, pe_ratio: float, pb_ratio: float, sector_median_pe: float, sector_median_pb: float
    ) -> float:
        """
        计算价值因子（HML - High Minus Low）

        Args:
            pe_ratio: 市盈率
            pb_ratio: 市净率
            sector_median_pe: 行业中位 PE
            sector_median_pb: 行业中位 PB

        Returns:
            价值因子得分
        """
        # 低估值得分高
        pe_score = 1.0 if pe_ratio < sector_median_pe else -1.0
        pb_score = 1.0 if pb_ratio < sector_median_pb else -1.0

        return (pe_score + pb_score) / 2

    def calculate_momentum_factor(self, returns: pd.Series, lookback: int = 252, skip: int = 21) -> float:
        """
        计算动量因子（MOM）

        Args:
            returns: 收益率序列
            lookback: 回溯天数（通常 1 年）
            skip: 跳过最近天数（通常 1 个月，避免短期反转）

        Returns:
            动量因子得分
        """
        if len(returns) < lookback + skip:
            return 0.0

        # 过去 12 个月收益率（跳过最近 1 个月）
        momentum_return = returns.iloc[-lookback - skip : -skip].sum()

        # 标准化
        return np.sign(momentum_return) * min(abs(momentum_return), 1.0)

    def calculate_quality_factor(
        self, roe: float, roa: float, debt_to_equity: float, sector_median_roe: float, sector_median_de: float
    ) -> float:
        """
        计算质量因子（QMJ - Quality Minus Junk）

        Args:
            roe: ROE
            roa: ROA
            debt_to_equity: 负债权益比
            sector_median_roe: 行业中位 ROE
            sector_median_de: 行业中位 D/E

        Returns:
            质量因子得分
        """
        # 高 ROE、低负债得分高
        roe_score = 1.0 if roe > sector_median_roe else -1.0
        de_score = 1.0 if debt_to_equity < sector_median_de else -1.0

        return (roe_score + de_score) / 2

    def calculate_low_volatility_factor(self, returns: pd.Series, lookback: int = 252) -> float:
        """
        计算低波因子（BAB - Betting Against Beta）

        Args:
            returns: 收益率序列
            lookback: 回溯天数

        Returns:
            低波因子得分
        """
        if len(returns) < lookback:
            return 0.0

        # 低波动率得分高
        volatility = returns.iloc[-lookback:].std()

        # 标准化（假设年化波动率 20% 为中性）
        annualized_vol = volatility * np.sqrt(252)
        score = 1.0 - (annualized_vol - 0.2) / 0.2

        return max(-1.0, min(1.0, score))

    def calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        计算 Beta 系数

        Args:
            returns: 资产收益率
            benchmark_returns: 基准收益率

        Returns:
            Beta 系数
        """
        # 对齐数据
        df = pd.DataFrame({"returns": returns, "benchmark": benchmark_returns}).dropna()

        if len(df) < 60:
            return 1.0

        # 计算协方差和方差
        covariance = df["returns"].cov(df["benchmark"])
        variance = df["benchmark"].var()

        beta = covariance / variance if variance > 0 else 1.0

        return beta

    def factor_regression(self, returns: pd.Series, factor_returns: pd.DataFrame) -> dict:
        """
        因子回归（计算因子载荷）

        Args:
            returns: 资产收益率
            factor_returns: 因子收益率 DataFrame

        Returns:
            回归结果（alpha, betas, r_squared）
        """
        # 对齐数据
        df = pd.DataFrame(
            {
                "returns": returns,
                **{f"factor_{i}": factor_returns.iloc[:, i] for i in range(len(factor_returns.columns))},
            }
        ).dropna()

        if len(df) < 60:
            return {"error": "数据不足"}

        # OLS 回归
        from sklearn.linear_model import LinearRegression

        X = df[[c for c in df.columns if c.startswith("factor_")]].values
        y = df["returns"].values

        model = LinearRegression()
        model.fit(X, y)

        y_pred = model.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        return {
            "alpha": model.intercept_,
            "betas": dict(zip(factor_returns.columns, model.coef_)),
            "r_squared": r_squared,
        }

    def calculate_composite_score(
        self, factor_scores: dict[str, float], weights: dict[str, float] | None = None
    ) -> float:
        """
        计算综合因子得分

        Args:
            factor_scores: 各因子得分
            weights: 因子权重

        Returns:
            综合得分
        """
        if weights is None:
            weights = {
                "market": 0.0,  # 市场因子通常不作为选股因子
                "size": 0.15,
                "value": 0.25,
                "momentum": 0.25,
                "quality": 0.20,
                "low_volatility": 0.15,
            }

        total_score = 0.0
        total_weight = 0.0

        for factor, score in factor_scores.items():
            weight = weights.get(factor, 0.0)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0


class MultiFactorStrategy:
    """多因子交易策略"""

    def __init__(
        self,
        model: MultiFactorModel | None = None,
        rebalance_freq: int = 21,  # 21 天 = 1 个月
        top_quantile: float = 0.2,  # 选择前 20%
        bottom_quantile: float = 0.2,  # 做空后 20%
    ):
        """
        初始化多因子策略

        Args:
            model: 多因子模型
            rebalance_freq: 再平衡频率（天）
            top_quantile: 做多分位数
            bottom_quantile: 做空头分位数
        """
        self.model = model or MultiFactorModel()
        self.rebalance_freq = rebalance_freq
        self.top_quantile = top_quantile
        self.bottom_quantile = bottom_quantile

        self.portfolio = {}
        self.last_rebalance = None

    def rank_stocks(self, stock_data: pd.DataFrame, benchmark_data: pd.DataFrame | None = None) -> pd.DataFrame:
        """
        对股票进行因子打分排序

        Args:
            stock_data: 股票数据（包含价格、市值、财务指标等）
            benchmark_data: 基准数据（可选）

        Returns:
            排序后的股票数据
        """
        df = stock_data.copy()

        # 计算各因子得分
        factor_scores = {}

        # 规模因子
        if "market_cap" in df.columns:
            median_cap = df["market_cap"].median()
            df["size_score"] = df["market_cap"].apply(lambda x: self.model.calculate_size_factor(x, median_cap))
            factor_scores["size"] = df["size_score"]

        # 价值因子
        if "pe_ratio" in df.columns and "pb_ratio" in df.columns:
            median_pe = df["pe_ratio"].median()
            median_pb = df["pb_ratio"].median()
            df["value_score"] = df.apply(
                lambda row: self.model.calculate_value_factor(row["pe_ratio"], row["pb_ratio"], median_pe, median_pb),
                axis=1,
            )
            factor_scores["value"] = df["value_score"]

        # 动量因子
        if "returns" in df.columns:
            df["momentum_score"] = df["returns"].apply(
                lambda x: self.model.calculate_momentum_factor(x) if isinstance(x, pd.Series) else 0
            )
            factor_scores["momentum"] = df["momentum_score"]

        # 质量因子
        if "roe" in df.columns and "debt_to_equity" in df.columns:
            median_roe = df["roe"].median()
            median_de = df["debt_to_equity"].median()
            df["quality_score"] = df.apply(
                lambda row: self.model.calculate_quality_factor(
                    row["roe"], row.get("roa", 0), row["debt_to_equity"], median_roe, median_de
                ),
                axis=1,
            )
            factor_scores["quality"] = df["quality_score"]

        # 低波因子
        if "volatility" in df.columns:
            df["low_vol_score"] = df["volatility"].apply(
                lambda x: 1.0 - (x - 0.2) / 0.2 if isinstance(x, (int, float)) else 0
            )
            factor_scores["low_volatility"] = df["low_vol_score"]

        # 计算综合得分
        df["composite_score"] = 0.0
        for factor, scores in factor_scores.items():
            weight = {"size": 0.15, "value": 0.25, "momentum": 0.25, "quality": 0.20, "low_volatility": 0.15}.get(
                factor, 0
            )
            df["composite_score"] += scores * weight

        # 排序
        df = df.sort_values("composite_score", ascending=False)

        return df

    def generate_signal(self, stock_data: pd.DataFrame, current_prices: pd.Series) -> dict:
        """
        生成交易信号

        Args:
            stock_data: 股票数据
            current_prices: 当前价格

        Returns:
            交易信号
        """
        # 排序股票
        ranked = self.rank_stocks(stock_data)

        n_stocks = len(ranked)
        top_n = int(n_stocks * self.top_quantile)
        bottom_n = int(n_stocks * self.bottom_quantile)

        # 做多股票（前 20%）
        long_stocks = ranked.head(top_n).index.tolist()

        # 做空股票（后 20%）
        short_stocks = ranked.tail(bottom_n).index.tolist()

        # 生成信号
        signals = {}
        for stock in ranked.index:
            if stock in long_stocks:
                signals[stock] = {"action": "BUY", "weight": 1.0 / top_n}
            elif stock in short_stocks:
                signals[stock] = {"action": "SELL", "weight": 1.0 / bottom_n}
            else:
                signals[stock] = {"action": "HOLD", "weight": 0}

        return {
            "strategy": "multi_factor",
            "signals": signals,
            "long_count": len(long_stocks),
            "short_count": len(short_stocks),
            "rebalance_date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": int(datetime.now().timestamp() * 1000),
        }

    def backtest(
        self,
        stock_data_history: dict[str, pd.DataFrame],
        initial_capital: float = 1000000,
        transaction_cost: float = 0.001,
    ) -> dict:
        """
        回测多因子策略

        Args:
            stock_data_history: 历史股票数据 {date: DataFrame}
            initial_capital: 初始资金
            transaction_cost: 交易成本

        Returns:
            回测结果
        """
        dates = sorted(stock_data_history.keys())

        capital = initial_capital
        portfolio = {}  # {stock: shares}
        portfolio_values = []

        for i, date in enumerate(dates):
            df = stock_data_history[date]

            # 再平衡
            if i % self.rebalance_freq == 0 or i == 0:
                # 生成信号
                signal = self.generate_signal(df, df["close"])

                # 平仓
                for stock, shares in portfolio.items():
                    if stock in df.index:
                        price = df.loc[stock, "close"]
                        capital += shares * price * (1 - transaction_cost)

                portfolio = {}

                # 开仓
                for stock, sig in signal["signals"].items():
                    if sig["action"] == "BUY" and stock in df.index:
                        price = df.loc[stock, "close"]
                        target_value = capital * sig["weight"]
                        shares = int(target_value / price)
                        if shares > 0:
                            cost = shares * price * (1 + transaction_cost)
                            if cost <= capital:
                                portfolio[stock] = shares
                                capital -= cost

            # 计算组合价值
            total_value = capital
            for stock, shares in portfolio.items():
                if stock in df.index:
                    total_value += shares * df.loc[stock, "close"]

            portfolio_values.append(total_value)

        # 计算绩效指标
        portfolio_values = np.array(portfolio_values)
        returns = np.diff(portfolio_values) / portfolio_values[:-1]

        total_return = (portfolio_values[-1] - initial_capital) / initial_capital
        sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252) if len(returns) > 1 else 0

        cummax = np.maximum.accumulate(portfolio_values)
        max_drawdown = np.max((cummax - portfolio_values) / cummax)

        return {
            "strategy": "multi_factor",
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "final_value": portfolio_values[-1],
            "num_rebalances": len(dates) // self.rebalance_freq,
            "portfolio_values": portfolio_values.tolist(),
        }


# ════════════════════════════════════════════════════════════
# 使用示例
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 创建示例数据
    np.random.seed(42)

    stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "JNJ"]
    n_stocks = len(stocks)

    # 生成股票数据
    stock_data = pd.DataFrame(
        {
            "market_cap": np.random.uniform(50, 2000, n_stocks) * 1e9,
            "pe_ratio": np.random.uniform(10, 50, n_stocks),
            "pb_ratio": np.random.uniform(1, 10, n_stocks),
            "roe": np.random.uniform(0.1, 0.4, n_stocks),
            "debt_to_equity": np.random.uniform(0.1, 2.0, n_stocks),
            "volatility": np.random.uniform(0.15, 0.5, n_stocks),
            "close": np.random.uniform(50, 500, n_stocks),
        },
        index=stocks,
    )

    # 多因子模型
    model = MultiFactorModel()

    print("=== 多因子分析 ===\n")

    # 计算各因子得分
    for stock in stocks[:3]:
        row = stock_data.loc[stock]
        print(f"{stock}:")

        size_score = model.calculate_size_factor(row["market_cap"], stock_data["market_cap"].median())
        print(f"  规模因子：{size_score:.2f}")

        value_score = model.calculate_value_factor(
            row["pe_ratio"], row["pb_ratio"], stock_data["pe_ratio"].median(), stock_data["pb_ratio"].median()
        )
        print(f"  价值因子：{value_score:.2f}")

        low_vol_score = model.calculate_low_volatility_factor(pd.Series(np.random.randn(252)), 252)
        print(f"  低波因子：{low_vol_score:.2f}")

    # 多因子策略
    strategy = MultiFactorStrategy(model)

    print("\n=== 交易信号 ===\n")
    signal = strategy.generate_signal(stock_data, stock_data["close"])

    print(f"做多股票数：{signal['long_count']}")
    print(f"做空股票数：{signal['short_count']}")
    print("\n信号详情:")
    for stock, sig in list(signal["signals"].items())[:5]:
        print(f"  {stock}: {sig['action']} (权重：{sig['weight']:.2%})")
