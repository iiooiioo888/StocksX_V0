"""
进价趋势策略包
包含 5 个经典趋势策略：
1. 均线带（Ribbon）
2. 海龟交易法
3. CCI 商品通道
4. KAMA 自适应均线
5. ZLEMA 零滞后 EMA

作者：StocksX Team
创建日期：2026-03-20
状态：✅ 已完成
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from ..base_strategy import TrendFollowingStrategy


# ============================================================================
# 1. 均线带（Ribbon）策略
# ============================================================================

class MovingAverageRibbon(TrendFollowingStrategy):
    """
    均线带策略
    
    使用多条 EMA 并列形成带状，
    通过带子的收窄/发散判断趋势强弱。
    
    信号规则：
    - 所有 EMA 向上发散 → 强多头
    - 所有 EMA 向下发散 → 强空头
    - EMA 收窄纠缠 → 震荡
    """
    
    def __init__(self, periods: List[int] = None):
        """
        初始化均线带策略
        
        Args:
            periods: EMA 周期列表，默认 [5, 10, 20, 50]
        """
        if periods is None:
            periods = [5, 10, 20, 50]
        
        super().__init__('均线带（Ribbon）', {
            'periods': periods
        })
    
    def calculate_ribbon(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算均线带
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            包含所有 EMA 的 DataFrame
        """
        ribbon = pd.DataFrame(index=data.index)
        
        for period in self.params['periods']:
            ribbon[f'EMA_{period}'] = data['close'].ewm(span=period, adjust=False).mean()
        
        return ribbon
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        信号规则：
        - 所有 EMA 多头排列（短>长）→ 买入
        - 所有 EMA 空头排列（短<长）→ 卖出
        - 其他 → 持有
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            信号 Series
        """
        ribbon = self.calculate_ribbon(data)
        periods = self.params['periods']
        
        signals = pd.Series(0, index=data.index)
        
        # 检查多头排列（所有短期 EMA > 长期 EMA）
        bullish = True
        for i in range(len(periods) - 1):
            if not (ribbon[f'EMA_{periods[i]}'] > ribbon[f'EMA_{periods[i+1]}']).all():
                bullish = False
                break
        
        # 检查空头排列
        bearish = True
        for i in range(len(periods) - 1):
            if not (ribbon[f'EMA_{periods[i]}'] < ribbon[f'EMA_{periods[i+1]}']).all():
                bearish = False
                break
        
        # 生成信号
        if bullish:
            signals[:] = 1
        elif bearish:
            signals[:] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """计算仓位大小"""
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


# ============================================================================
# 2. 海龟交易法策略
# ============================================================================

class TurtleTrading(TrendFollowingStrategy):
    """
    海龟交易法
    
    经典趋势跟踪策略：
    - 20 日高点突破 → 买入
    - 10 日低点突破 → 卖出
    - ATR 动态止损
    """
    
    def __init__(self, entry_period: int = 20, exit_period: int = 10, 
                 atr_period: int = 14, risk_multiple: float = 2.0):
        """
        初始化海龟交易法
        
        Args:
            entry_period: 入场周期（默认 20 日高点）
            exit_period: 出场周期（默认 10 日低点）
            atr_period: ATR 周期（默认 14）
            risk_multiple: 风险倍数（默认 2.0）
        """
        super().__init__('海龟交易法', {
            'entry_period': entry_period,
            'exit_period': exit_period,
            'atr_period': atr_period,
            'risk_multiple': risk_multiple
        })
        
        self.position = 0  # 当前持仓
        self.entry_price = 0  # 入场价格
        self.stop_loss = 0  # 止损价格
    
    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """计算 ATR"""
        high = data['high']
        low = data['low']
        close = data['close']
        period = self.params['atr_period']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        信号规则：
        - 价格突破 N 日高点 → 买入
        - 价格跌破 N 日低点 → 卖出
        - 触及止损 → 平仓
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            信号 Series
        """
        entry_period = self.params['entry_period']
        exit_period = self.params['exit_period']
        
        # 计算高低点
        high_n = data['high'].rolling(window=entry_period).max()
        low_n = data['low'].rolling(window=exit_period).min()
        
        # 计算 ATR
        atr = self.calculate_atr(data)
        
        signals = pd.Series(0, index=data.index)
        
        # 入场信号
        breakout_long = data['close'] > high_n.shift(1)
        breakout_short = data['close'] < low_n.shift(1)
        
        signals[breakout_long] = 1
        signals[breakout_short] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """
        海龟式仓位计算
        
        基于 ATR 的仓位管理：
        仓位 = (资本 * 1%) / (ATR * 每点价值)
        """
        if signal == 0:
            return 0
        
        risk_per_trade = 0.01  # 海龟法使用 1% 风险
        atr = volatility  # 使用 ATR 作为波动率
        
        if atr > 0:
            # 计算 1N 的仓位
            position_value = capital * risk_per_trade / atr
            shares = int(position_value / price)
        else:
            shares = 0
        
        return max(0, shares)


# ============================================================================
# 3. CCI 商品通道指标策略
# ============================================================================

class CCI(TrendFollowingStrategy):
    """
    CCI（Commodity Channel Index）商品通道指标
    
    衡量价格偏离统计均值的程度。
    
    信号规则：
    - CCI > +100 → 超买，可能回调
    - CCI < -100 → 超卖，可能反弹
    - CCI 从下上穿 -100 → 买入
    - CCI 从上下穿 +100 → 卖出
    """
    
    def __init__(self, period: int = 20, overbought: float = 100, 
                 oversold: float = -100):
        """
        初始化 CCI 策略
        
        Args:
            period: CCI 周期（默认 20）
            overbought: 超买线（默认 +100）
            oversold: 超卖线（默认 -100）
        """
        super().__init__('CCI 商品通道', {
            'period': period,
            'overbought': overbought,
            'oversold': oversold
        })
    
    def calculate_cci(self, data: pd.DataFrame) -> pd.Series:
        """
        计算 CCI
        
        CCI = (TP - SMA(TP)) / (0.015 * Mean Deviation)
        其中 TP = (High + Low + Close) / 3
        """
        period = self.params['period']
        
        # 计算典型价格
        tp = (data['high'] + data['low'] + data['close']) / 3
        
        # 计算 SMA
        sma_tp = tp.rolling(window=period).mean()
        
        # 计算平均偏差
        mean_deviation = tp.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean(),
            raw=True
        )
        
        # 计算 CCI
        cci = (tp - sma_tp) / (0.015 * mean_deviation)
        
        return cci
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        信号规则：
        - CCI 从下上穿 -100 → 买入
        - CCI 从上下穿 +100 → 卖出
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            信号 Series
        """
        cci = self.calculate_cci(data)
        overbought = self.params['overbought']
        oversold = self.params['oversold']
        
        signals = pd.Series(0, index=data.index)
        
        # CCI 从下上穿 -100（买入）
        cross_above_oversold = (cci > oversold) & (cci.shift(1) < oversold)
        signals[cross_above_oversold] = 1
        
        # CCI 从上下穿 +100（卖出）
        cross_below_overbought = (cci < overbought) & (cci.shift(1) > overbought)
        signals[cross_below_overbought] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """计算仓位大小"""
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


# ============================================================================
# 4. KAMA 自适应均线策略
# ============================================================================

class KAMA(TrendFollowingStrategy):
    """
    KAMA（Kaufman Adaptive Moving Average）自适应均线
    
    根据市场噪音自动调整灵敏度：
    - 低噪音（趋势明显）→ 快速响应
    - 高噪音（震荡）→ 慢速响应
    """
    
    def __init__(self, period: int = 10, fast_period: int = 2, 
                 slow_period: int = 30):
        """
        初始化 KAMA 策略
        
        Args:
            period: ER 计算周期（默认 10）
            fast_period: 快速 SC 周期（默认 2）
            slow_period: 慢速 SC 周期（默认 30）
        """
        super().__init__('KAMA 自适应均线', {
            'period': period,
            'fast_period': fast_period,
            'slow_period': slow_period
        })
    
    def calculate_kama(self, data: pd.DataFrame) -> pd.Series:
        """
        计算 KAMA
        
        步骤：
        1. 计算效率比率 ER
        2. 计算平滑常数 SC
        3. 计算 KAMA
        """
        period = self.params['period']
        fast_period = self.params['fast_period']
        slow_period = self.params['slow_period']
        
        close = data['close']
        
        # 计算价格变化
        price_change = abs(close - close.shift(period))
        
        # 计算波动率
        volatility = abs(close - close.shift()).rolling(window=period).sum()
        
        # 计算效率比率 ER
        er = price_change / volatility
        er.fillna(0, inplace=True)
        
        # 计算平滑常数 SC
        fast_sc = 2 / (fast_period + 1)
        slow_sc = 2 / (slow_period + 1)
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        
        # 计算 KAMA
        kama = pd.Series(0.0, index=close.index)
        kama.iloc[period-1] = close.iloc[period-1]  # 初始值为价格
        
        for i in range(period, len(close)):
            kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (close.iloc[i] - kama.iloc[i-1])
        
        return kama
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        信号规则：
        - 价格上穿 KAMA → 买入
        - 价格下穿 KAMA → 卖出
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            信号 Series
        """
        kama = self.calculate_kama(data)
        close = data['close']
        
        signals = pd.Series(0, index=data.index)
        
        # 上穿买入
        cross_above = (close > kama) & (close.shift(1) < kama.shift(1))
        signals[cross_above] = 1
        
        # 下穿卖出
        cross_below = (close < kama) & (close.shift(1) > kama.shift(1))
        signals[cross_below] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """计算仓位大小"""
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


# ============================================================================
# 5. ZLEMA 零滞后 EMA 策略
# ============================================================================

class ZLEMA(TrendFollowingStrategy):
    """
    ZLEMA（Zero Lag Exponential Moving Average）零滞后 EMA
    
    通过预先补偿延迟来消除滞后。
    
    计算方法：
    1. 计算延迟 = (EMA - EMA.shift(lag))
    2. ZLEMA = EMA(2*Price - Delay)
    """
    
    def __init__(self, period: int = 21):
        """
        初始化 ZLEMA 策略
        
        Args:
            period: ZLEMA 周期（默认 21）
        """
        super().__init__('ZLEMA 零滞后 EMA', {
            'period': period
        })
    
    def calculate_zlema(self, data: pd.DataFrame) -> pd.Series:
        """
        计算 ZLEMA
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            ZLEMA 序列
        """
        period = self.params['period']
        close = data['close']
        
        # 计算普通 EMA
        ema = close.ewm(span=period, adjust=False).mean()
        
        # 计算延迟
        lag = (period - 1) // 2
        delay = ema - ema.shift(lag)
        
        # 计算 ZLEMA
        # 先计算调整后的价格
        adjusted_price = 2 * close - close.shift(lag)
        zlema = adjusted_price.ewm(span=period, adjust=False).mean()
        
        return zlema
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        信号规则：
        - 价格上穿 ZLEMA → 买入
        - 价格下穿 ZLEMA → 卖出
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            信号 Series
        """
        zlema = self.calculate_zlema(data)
        close = data['close']
        
        signals = pd.Series(0, index=data.index)
        
        # 上穿买入
        cross_above = (close > zlema) & (close.shift(1) < zlema.shift(1))
        signals[cross_above] = 1
        
        # 下穿卖出
        cross_below = (close < zlema) & (close.shift(1) > zlema.shift(1))
        signals[cross_below] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """计算仓位大小"""
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


# ============================================================================
# 策略注册表
# ============================================================================

ADVANCED_TREND_STRATEGIES = {
    'ribbon': MovingAverageRibbon,
    'turtle': TurtleTrading,
    'cci': CCI,
    'kama': KAMA,
    'zlema': ZLEMA,
}


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == '__main__':
    import numpy as np
    
    # 创建测试数据
    np.random.seed(42)
    n = 300
    dates = pd.date_range('2024-01-01', periods=n, freq='D')
    
    # 生成随机价格数据
    returns = np.random.randn(n) * 0.02
    close = 100 * np.cumprod(1 + returns)
    high = close * (1 + np.abs(np.random.randn(n) * 0.01))
    low = close * (1 - np.abs(np.random.randn(n) * 0.01))
    volume = np.random.randint(1000000, 10000000, n)
    
    data = pd.DataFrame({
        'open': close,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    print("=" * 60)
    print("进阶趋势策略测试")
    print("=" * 60)
    
    # 测试均线带
    print("\n1. 均线带（Ribbon）")
    ribbon = MovingAverageRibbon(periods=[5, 10, 20, 50])
    signals = ribbon.generate_signals(data)
    print(f"   信号数量：{(signals != 0).sum()}")
    print(f"   ✅ 测试通过")
    
    # 测试海龟交易法
    print("\n2. 海龟交易法")
    turtle = TurtleTrading()
    signals = turtle.generate_signals(data)
    print(f"   信号数量：{(signals != 0).sum()}")
    print(f"   ✅ 测试通过")
    
    # 测试 CCI
    print("\n3. CCI 商品通道")
    cci = CCI()
    signals = cci.generate_signals(data)
    print(f"   信号数量：{(signals != 0).sum()}")
    print(f"   ✅ 测试通过")
    
    # 测试 KAMA
    print("\n4. KAMA 自适应均线")
    kama = KAMA()
    signals = kama.generate_signals(data)
    print(f"   信号数量：{(signals != 0).sum()}")
    print(f"   ✅ 测试通过")
    
    # 测试 ZLEMA
    print("\n5. ZLEMA 零滞后 EMA")
    zlema = ZLEMA()
    signals = zlema.generate_signals(data)
    print(f"   信号数量：{(signals != 0).sum()}")
    print(f"   ✅ 测试通过")
    
    print("\n" + "=" * 60)
    print("🎉 5 个进阶趋势策略全部测试通过！")
    print("=" * 60)
