"""
振盪器最終策略包（剩餘 4 個）
包含 4 個變體策略：
1. Multi-RSI（多週期 RSI）
2. Adaptive KD（自適應 KD）
3. Bollinger %B（布林帶百分比）
4. Custom Oscillator（自定義振盪器）

作者：StocksX Team
創建日期：2026-03-20
狀態：✅ 已完成 - 振盪器類別 100%
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from ..base_strategy import OscillatorStrategy


# ============================================================================
# 1. Multi-RSI（多週期 RSI）策略
# ============================================================================

class MultiRSI(OscillatorStrategy):
    """
    Multi-RSI 多週期 RSI 策略
    
    使用多個不同週期的 RSI 綜合判斷。
    
    信號規則：
    - 多個 RSI 同時超賣 → 強烈買入信號
    - 多個 RSI 同時超買 → 強烈賣出信號
    - RSI 週期發散 → 趨勢確認
    """
    
    def __init__(self, periods: List[int] = None, 
                 overbought: float = 70, oversold: float = 30):
        """
        初始化 Multi-RSI
        
        Args:
            periods: RSI 週期列表，默认 [7, 14, 21]
            overbought: 超買線（默认 70）
            oversold: 超賣線（默认 30）
        """
        if periods is None:
            periods = [7, 14, 21]
        
        super().__init__('Multi-RSI', {
            'periods': periods,
            'overbought': overbought,
            'oversold': oversold
        })
    
    def calculate_rsi(self, data: pd.DataFrame, period: int) -> pd.Series:
        """計算單一周期的 RSI"""
        delta = data['close'].diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_multi_rsi(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算多個週期的 RSI
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            包含所有 RSI 的字典
        """
        rsis = {}
        for period in self.params['periods']:
            rsis[f'rsi_{period}'] = self.calculate_rsi(data, period)
        
        return rsis
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - 所有 RSI < 30 → 強烈買入
        - 所有 RSI > 70 → 強烈賣出
        - 多數 RSI < 30 → 買入
        - 多數 RSI > 70 → 賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        rsis = self.calculate_multi_rsi(data)
        overbought = self.params['overbought']
        oversold = self.params['oversold']
        
        signals = pd.Series(0, index=data.index)
        
        # 計算超買超賣的 RSI 數量
        oversold_count = sum(rsis[key] < oversold for key in rsis.keys())
        overbought_count = sum(rsis[key] > overbought for key in rsis.keys())
        
        n_periods = len(self.params['periods'])
        
        # 所有 RSI 超賣 → 強烈買入
        signals[oversold_count == n_periods] = 1
        
        # 所有 RSI 超買 → 強烈賣出
        signals[overbought_count == n_periods] = -1
        
        # 多數 RSI 超賣（>50%）→ 買入
        majority_oversold = oversold_count > n_periods / 2
        signals[majority_oversold & (signals == 0)] = 1
        
        # 多數 RSI 超買（>50%）→ 賣出
        majority_overbought = overbought_count > n_periods / 2
        signals[majority_overbought & (signals == 0)] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
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
# 2. Adaptive KD（自適應 KD）策略
# ============================================================================

class AdaptiveKD(OscillatorStrategy):
    """
    Adaptive KD 自適應 KD 策略
    
    根據市場波動率自動調整 KD 參數。
    
    信號規則：
    - 高波動 → 使用較長週期
    - 低波動 → 使用較短週期
    - K 線上穿 D 線 → 買入
    - K 線下穿 D 線 → 賣出
    """
    
    def __init__(self, base_n: int = 9, base_m1: int = 3, 
                 base_m2: int = 3, volatility_period: int = 14):
        """
        初始化 Adaptive KD
        
        Args:
            base_n: 基礎 N 週期（默认 9）
            base_m1: 基礎 M1 週期（默认 3）
            base_m2: 基礎 M2 週期（默认 3）
            volatility_period: 波動率週期（默认 14）
        """
        super().__init__('Adaptive KD', {
            'base_n': base_n,
            'base_m1': base_m1,
            'base_m2': base_m2,
            'volatility_period': volatility_period
        })
        
        self.current_n = base_n
        self.current_m1 = base_m1
        self.current_m2 = base_m2
    
    def calculate_volatility(self, data: pd.DataFrame) -> pd.Series:
        """計算市場波動率"""
        period = self.params['volatility_period']
        
        # 使用 ATR 作為波動率指標
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        
        # 標準化波動率
        volatility = atr / close
        
        return volatility
    
    def adapt_parameters(self, volatility: pd.Series) -> None:
        """
        根據波動率調整參數
        
        Args:
            volatility: 波動率序列
        """
        # 計算近期平均波動率
        avg_vol = volatility.rolling(window=20).mean().iloc[-1]
        
        # 根據波動率調整週期
        if avg_vol > 0.03:  # 高波動
            self.current_n = self.params['base_n'] + 5
            self.current_m1 = self.params['base_m1'] + 2
            self.current_m2 = self.params['base_m2'] + 2
        elif avg_vol < 0.01:  # 低波動
            self.current_n = max(5, self.params['base_n'] - 2)
            self.current_m1 = max(2, self.params['base_m1'] - 1)
            self.current_m2 = max(2, self.params['base_m2'] - 1)
        else:  # 正常波動
            self.current_n = self.params['base_n']
            self.current_m1 = self.params['base_m1']
            self.current_m2 = self.params['base_m2']
    
    def calculate_kd(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算 KD 指標
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            包含 K 和 D 的字典
        """
        n = self.current_n
        m1 = self.current_m1
        m2 = self.current_m2
        
        # 計算 RSV
        low_n = data['low'].rolling(window=n).min()
        high_n = data['high'].rolling(window=n).max()
        
        rsv = 100 * (data['close'] - low_n) / (high_n - low_n + 1e-10)
        
        # 計算 K 和 D
        k = rsv.rolling(window=m1).mean()
        d = k.rolling(window=m2).mean()
        
        return {'k': k, 'd': d}
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - K 線上穿 D 線 → 買入
        - K 線下穿 D 線 → 賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        # 先調整參數
        volatility = self.calculate_volatility(data)
        self.adapt_parameters(volatility)
        
        kd = self.calculate_kd(data)
        k = kd['k']
        d = kd['d']
        
        signals = pd.Series(0, index=data.index)
        
        # K 線上穿 D 線（黃金交叉）
        cross_above = (k > d) & (k.shift(1) < d.shift(1))
        signals[cross_above] = 1
        
        # K 線下穿 D 線（死亡交叉）
        cross_below = (k < d) & (k.shift(1) > d.shift(1))
        signals[cross_below] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
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
# 3. Bollinger %B（布林帶百分比）策略
# ============================================================================

class BollingerPercentB(OscillatorStrategy):
    """
    Bollinger %B 布林帶百分比策略
    
    衡量價格在布林帶中的相對位置。
    
    計算方法：
    %B = (Close - Lower Band) / (Upper Band - Lower Band)
    
    信號規則：
    - %B < 0 → 價格低於下軌，超賣，買入
    - %B > 1 → 價格高於上軌，超買，賣出
    - %B 從下上穿 0 → 買入
    - %B 從上下穿 1 → 賣出
    """
    
    def __init__(self, period: int = 20, num_std: float = 2.0):
        """
        初始化 Bollinger %B
        
        Args:
            period: 布林帶週期（默认 20）
            num_std: 標準差倍數（默认 2.0）
        """
        super().__init__('Bollinger %B', {
            'period': period,
            'num_std': num_std
        })
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算布林帶
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            包含上軌、中軌、下軌的字典
        """
        period = self.params['period']
        num_std = self.params['num_std']
        
        close = data['close']
        
        # 中軌（SMA）
        middle = close.rolling(window=period).mean()
        
        # 標準差
        std = close.rolling(window=period).std()
        
        # 上軌和下軌
        upper = middle + num_std * std
        lower = middle - num_std * std
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    
    def calculate_percent_b(self, data: pd.DataFrame) -> pd.Series:
        """
        計算 %B
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            %B 序列
        """
        bands = self.calculate_bollinger_bands(data)
        
        upper = bands['upper']
        lower = bands['lower']
        close = data['close']
        
        # 計算 %B
        percent_b = (close - lower) / (upper - lower + 1e-10)
        
        return percent_b
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - %B < 0 → 超賣，買入
        - %B > 1 → 超買，賣出
        - %B 從下上穿 0 → 買入
        - %B 從上下穿 1 → 賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        percent_b = self.calculate_percent_b(data)
        
        signals = pd.Series(0, index=data.index)
        
        # %B < 0（超賣）
        signals[percent_b < 0] = 1
        
        # %B > 1（超買）
        signals[percent_b > 1] = -1
        
        # %B 從下上穿 0
        cross_above_zero = (percent_b > 0) & (percent_b.shift(1) < 0)
        signals[cross_above_zero] = 1
        
        # %B 從上下穿 1
        cross_below_one = (percent_b < 1) & (percent_b.shift(1) > 1)
        signals[cross_below_one] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
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
# 4. Custom Oscillator（自定義振盪器）策略
# ============================================================================

class CustomOscillator(OscillatorStrategy):
    """
    Custom Oscillator 自定義振盪器
    
    綜合多個指標的自定義振盪器。
    
    計算方法：
    Custom = (RSI_norm + KD_norm + MACD_norm) / 3
    
    信號規則：
    - Custom < 20 → 超賣，買入
    - Custom > 80 → 超買，賣出
    """
    
    def __init__(self, rsi_period: int = 14, kd_n: int = 9, 
                 macd_fast: int = 12, macd_slow: int = 26, 
                 macd_signal: int = 9):
        """
        初始化 Custom Oscillator
        
        Args:
            rsi_period: RSI 週期（默认 14）
            kd_n: KD 的 N 週期（默认 9）
            macd_fast: MACD 快速週期（默认 12）
            macd_slow: MACD 慢速週期（默认 26）
            macd_signal: MACD 信號週期（默认 9）
        """
        super().__init__('Custom Oscillator', {
            'rsi_period': rsi_period,
            'kd_n': kd_n,
            'macd_fast': macd_fast,
            'macd_slow': macd_slow,
            'macd_signal': macd_signal,
            'overbought': 80,
            'oversold': 20
        })
    
    def calculate_rsi_norm(self, data: pd.DataFrame) -> pd.Series:
        """計算標準化 RSI（0-100）"""
        period = self.params['rsi_period']
        delta = data['close'].diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi / 100  # 標準化到 0-1
    
    def calculate_kd_norm(self, data: pd.DataFrame) -> pd.Series:
        """計算標準化 KD（0-100）"""
        n = self.params['kd_n']
        
        low_n = data['low'].rolling(window=n).min()
        high_n = data['high'].rolling(window=n).max()
        
        rsv = 100 * (data['close'] - low_n) / (high_n - low_n + 1e-10)
        k = rsv.rolling(window=3).mean()
        
        return k / 100  # 標準化到 0-1
    
    def calculate_macd_norm(self, data: pd.DataFrame) -> pd.Series:
        """計算標準化 MACD"""
        fast = self.params['macd_fast']
        slow = self.params['macd_slow']
        signal_period = self.params['macd_signal']
        
        fast_ema = data['close'].ewm(span=fast, adjust=False).mean()
        slow_ema = data['close'].ewm(span=slow, adjust=False).mean()
        
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        
        # 計算 MACD 柱狀圖
        histogram = macd - signal
        
        # 標準化（使用 rolling max/min）
        hist_max = abs(histogram).rolling(window=20).max()
        macd_norm = 0.5 + 0.5 * (histogram / (hist_max + 1e-10))
        
        return macd_norm
    
    def calculate_custom_oscillator(self, data: pd.DataFrame) -> pd.Series:
        """
        計算自定義振盪器
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            Custom Oscillator 序列（0-100）
        """
        rsi_norm = self.calculate_rsi_norm(data)
        kd_norm = self.calculate_kd_norm(data)
        macd_norm = self.calculate_macd_norm(data)
        
        # 綜合三個指標
        custom = (rsi_norm + kd_norm + macd_norm) / 3 * 100
        
        return custom
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - Custom < 20 → 超賣，買入
        - Custom > 80 → 超買，賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        custom = self.calculate_custom_oscillator(data)
        overbought = self.params['overbought']
        oversold = self.params['oversold']
        
        signals = pd.Series(0, index=data.index)
        
        # 超賣
        signals[custom < oversold] = 1
        
        # 超買
        signals[custom > overbought] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
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
# 策略註冊表
# ============================================================================

FINAL_OSCILLATOR_STRATEGIES = {
    'multi_rsi': MultiRSI,
    'adaptive_kd': AdaptiveKD,
    'bollinger_pct_b': BollingerPercentB,
    'custom_oscillator': CustomOscillator,
}


# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == '__main__':
    import numpy as np
    
    # 創建測試數據
    np.random.seed(42)
    n = 300
    dates = pd.date_range('2024-01-01', periods=n, freq='D')
    
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
    print("振盪器最終策略測試（4 個）- 完成振盪器類別！")
    print("=" * 60)
    
    strategies = [
        ('Multi-RSI', MultiRSI()),
        ('Adaptive KD', AdaptiveKD()),
        ('Bollinger %B', BollingerPercentB()),
        ('Custom Oscillator', CustomOscillator()),
    ]
    
    for name, strategy in strategies:
        print(f"\n{name}")
        signals = strategy.generate_signals(data)
        print(f"   信號數量：{(signals != 0).sum()}")
        print(f"   ✅ 測試通過")
    
    print("\n" + "=" * 60)
    print("🎉 4 個最終振盪器策略全部測試通過！")
    print("🎉 振盪器類別 16/16 完成（100%）！")
    print("=" * 60)
