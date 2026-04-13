"""
Hull MA 赫尔移动平均策略
低延迟的移动平均指标，几乎零滞后

作者：StocksX Team
创建日期：2026-03-20
状态：✅ 已完成
"""

import pandas as pd
import numpy as np
from ..base_strategy import TrendFollowingStrategy


class HullMA(TrendFollowingStrategy):
    """
    Hull 移动平均策略

    Hull MA 通过加权计算实现极低的延迟，
    比传统 SMA/EMA 更敏感，同时保持平滑。

    计算方法：
    1. 计算 n/2 周期的 WMA
    2. 计算 n 周期的 WMA
    3. HullMA = WMA(2*WMA(n/2) - WMA(n), sqrt(n))
    """

    def __init__(self, period: int = 20, signal_period: int = 5):
        """
        初始化 Hull MA 策略

        Args:
            period: Hull MA 主周期（默认 20）
            signal_period: 信号线周期（默认 5，用于生成交叉信号）
        """
        super().__init__("Hull MA", {"period": period, "signal_period": signal_period})

    def _calculate_wma(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算加权移动平均（WMA）

        Args:
            data: 价格数据
            period: 周期

        Returns:
            WMA 序列
        """
        weights = np.arange(1, period + 1)
        wma = data.rolling(window=period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
        return wma

    def calculate_hull_ma(self, data: pd.DataFrame) -> pd.Series:
        """
        计算 Hull MA

        Args:
            data: 包含 OHLCV 数据的 DataFrame

        Returns:
            Hull MA 序列
        """
        n = self.params["period"]
        close = data["close"]

        # 计算 n/2 周期的 WMA
        wma_half = self._calculate_wma(close, n // 2)

        # 计算 n 周期的 WMA
        wma_full = self._calculate_wma(close, n)

        # 计算 Hull MA
        hull_ma = self._calculate_wma(2 * wma_half - wma_full, int(np.sqrt(n)))

        return hull_ma

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号

        信号规则：
        - 价格上穿 Hull MA → 买入信号 (1)
        - 价格下穿 Hull MA → 卖出信号 (-1)
        - 其他情况 → 持有 (0)

        Args:
            data: 包含 OHLCV 数据的 DataFrame

        Returns:
            信号 Series（1=买入，-1=卖出，0=持有）
        """
        # 计算 Hull MA
        hull_ma = self.calculate_hull_ma(data)
        close = data["close"]

        # 初始化信号
        signals = pd.Series(0, index=data.index)

        # 生成交叉信号
        # 价格上穿 Hull MA
        cross_above = (close > hull_ma) & (close.shift(1) < hull_ma.shift(1))
        signals[cross_above] = 1

        # 价格下穿 Hull MA
        cross_below = (close < hull_ma) & (close.shift(1) > hull_ma.shift(1))
        signals[cross_below] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """
        计算仓位大小

        使用固定分数法：每次交易承担 2% 风险

        Args:
            signal: 交易信号（1/-1/0）
            capital: 可用资金
            price: 当前价格
            volatility: 波动率（ATR 或标准差）

        Returns:
            仓位大小（股数/合约数）
        """
        if signal == 0:
            return 0

        # 风险参数
        risk_per_trade = 0.02  # 每笔交易风险 2%
        stop_loss_distance = 2 * volatility  # 止损距离为 2 倍波动率

        # 计算风险金额
        risk_amount = capital * risk_per_trade

        # 计算仓位大小
        if stop_loss_distance > 0:
            position_size = risk_amount / stop_loss_distance
        else:
            position_size = 0

        # 转换为股数/合约数
        shares = int(position_size / price)

        return max(0, shares)

    def get_strategy_info(self) -> dict:
        """
        获取策略信息

        Returns:
            策略信息字典
        """
        return {
            "name": self.name,
            "category": self.category,
            "params": self.params.copy(),
            "description": "Hull 移动平均策略 - 低延迟趋势指标",
            "signals": "价格上穿 Hull MA 买入，下穿卖出",
            "risk_management": "固定分数法，每笔交易风险 2%",
        }


class TEMA(TrendFollowingStrategy):
    """
    TEMA 三重指数移动平均策略

    TEMA 通过三次 EMA 叠加消除延迟，
    比传统 EMA 更敏感，适合快速趋势。
    """

    def __init__(self, period: int = 21):
        """
        初始化 TEMA 策略

        Args:
            period: TEMA 周期（默认 21）
        """
        super().__init__("TEMA 三重指数", {"period": period})

    def calculate_tema(self, data: pd.DataFrame) -> pd.Series:
        """
        计算 TEMA

        TEMA = 3*EMA1 - 3*EMA2 + EMA3
        其中 EMA1, EMA2, EMA3 分别为 1 次、2 次、3 次 EMA

        Args:
            data: 包含 OHLCV 数据的 DataFrame

        Returns:
            TEMA 序列
        """
        n = self.params["period"]
        close = data["close"]

        # 计算三次 EMA
        ema1 = close.ewm(span=n, adjust=False).mean()
        ema2 = ema1.ewm(span=n, adjust=False).mean()
        ema3 = ema2.ewm(span=n, adjust=False).mean()

        # 计算 TEMA
        tema = 3 * ema1 - 3 * ema2 + ema3

        return tema

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号

        信号规则：
        - 价格上穿 TEMA → 买入信号
        - 价格下穿 TEMA → 卖出信号

        Args:
            data: 包含 OHLCV 数据的 DataFrame

        Returns:
            信号 Series
        """
        tema = self.calculate_tema(data)
        close = data["close"]

        signals = pd.Series(0, index=data.index)

        # 上穿买入
        cross_above = (close > tema) & (close.shift(1) < tema.shift(1))
        signals[cross_above] = 1

        # 下穿卖出
        cross_below = (close < tema) & (close.shift(1) > tema.shift(1))
        signals[cross_below] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """计算仓位大小（同 Hull MA）"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        stop_loss_distance = 2 * volatility

        risk_amount = capital * risk_per_trade
        if stop_loss_distance > 0:
            position_size = risk_amount / stop_loss_distance
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)


# 策略注册表
ADVANCED_TREND_STRATEGIES = {
    "hull_ma": HullMA,
    "tema": TEMA,
}


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    import numpy as np

    np.random.seed(42)
    n = 200
    dates = pd.date_range("2024-01-01", periods=n, freq="D")

    # 生成随机价格数据
    returns = np.random.randn(n) * 0.02
    close = 100 * np.cumprod(1 + returns)
    high = close * (1 + np.abs(np.random.randn(n) * 0.01))
    low = close * (1 - np.abs(np.random.randn(n) * 0.01))
    volume = np.random.randint(1000000, 10000000, n)

    data = pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume}, index=dates)

    # 测试 Hull MA 策略
    strategy = HullMA(period=20)
    signals = strategy.generate_signals(data)

    print("\nHull MA 策略测试")
    print(f"周期：{strategy.params['period']}")
    print(f"信号数量：{(signals != 0).sum()}")
    print(f"买入信号：{(signals == 1).sum()}")
    print(f"卖出信号：{(signals == -1).sum()}")

    # 测试 TEMA 策略
    strategy_tema = TEMA(period=21)
    signals_tema = strategy_tema.generate_signals(data)

    print("\nTEMA 策略测试")
    print(f"周期：{strategy_tema.params['period']}")
    print(f"信号数量：{(signals_tema != 0).sum()}")
    print(f"买入信号：{(signals_tema == 1).sum()}")
    print(f"卖出信号：{(signals_tema == -1).sum()}")

    print("\n✅ 策略测试完成！")
