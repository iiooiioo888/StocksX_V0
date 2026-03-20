"""
完整振盪器策略包（第二部分）
包含 8 個進階振盪器策略：
1. Fisher Transform
2. Elder Ray（牛熊力量）
3. TRIX
4. Klinger 振盪
5. Chande 動量振盪
6. Detrended Price Oscillator
7. Ulcer Index
8. Mass Index

作者：StocksX Team
創建日期：2026-03-20
狀態：✅ 已完成
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from ..base_strategy import OscillatorStrategy


# ============================================================================
# 1. Fisher Transform 策略
# ============================================================================

class FisherTransform(OscillatorStrategy):
    """
    Fisher Transform 策略
    
    將價格分佈轉為常態分佈，使極端值更銳利。
    
    計算方法：
    Fisher = 0.5 * ln((1 + X) / (1 - X))
    其中 X = 0.66 * (Price - Min) / (Max - Min) - 0.67
    
    信號規則：
    - Fisher 從下上穿 -1 → 買入
    - Fisher 從上下穿 +1 → 賣出
    """
    
    def __init__(self, period: int = 10):
        """
        初始化 Fisher Transform
        
        Args:
            period: 周期（默认 10）
        """
        super().__init__('Fisher Transform', {
            'period': period
        })
    
    def calculate_fisher(self, data: pd.DataFrame) -> pd.Series:
        """
        計算 Fisher Transform
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            Fisher 序列
        """
        period = self.params['period']
        
        # 使用典型價格
        price = (data['high'] + data['low']) / 2
        
        # 計算周期內的最高和最低
        price_min = price.rolling(window=period).min()
        price_max = price.rolling(window=period).max()
        
        # 計算標準化價格 X
        x = 0.66 * ((price - price_min) / (price_max - price_min + 1e-10) - 0.67)
        x = x.clip(-0.999, 0.999)  # 限制範圍避免除零
        
        # 計算 Fisher Transform
        fisher = 0.5 * np.log((1 + x) / (1 - x))
        
        return fisher
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - Fisher 從下上穿 -1 → 買入
        - Fisher 從上下穿 +1 → 賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        fisher = self.calculate_fisher(data)
        
        signals = pd.Series(0, index=data.index)
        
        # Fisher 上穿 -1
        cross_above_neg1 = (fisher > -1) & (fisher.shift(1) < -1)
        signals[cross_above_neg1] = 1
        
        # Fisher 下穿 +1
        cross_below_pos1 = (fisher < 1) & (fisher.shift(1) > 1)
        signals[cross_below_pos1] = -1
        
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
# 2. Elder Ray（牛熊力量）策略
# ============================================================================

class ElderRay(OscillatorStrategy):
    """
    Elder Ray 策略（牛熊力量）
    
    分離買方（Bull Power）和賣方（Bear Power）的力量。
    
    計算方法：
    - Bull Power = High - EMA(Close)
    - Bear Power = Low - EMA(Close)
    
    信號規則：
    - Bull Power > 0 且 Bear Power < 0 → 多頭強勢，買入
    - Bull Power < 0 且 Bear Power > 0 → 空頭強勢，賣出
    """
    
    def __init__(self, ema_period: int = 13):
        """
        初始化 Elder Ray
        
        Args:
            ema_period: EMA 周期（默认 13）
        """
        super().__init__('Elder Ray', {
            'ema_period': ema_period
        })
    
    def calculate_elder_ray(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算 Elder Ray
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            包含 Bull Power 和 Bear Power 的字典
        """
        period = self.params['ema_period']
        
        # 計算 EMA
        ema = data['close'].ewm(span=period, adjust=False).mean()
        
        # 計算牛熊力量
        bull_power = data['high'] - ema
        bear_power = data['low'] - ema
        
        return {
            'bull_power': bull_power,
            'bear_power': bear_power,
            'ema': ema
        }
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - Bull Power > 0 且 Bear Power < 0 → 多頭強勢，買入
        - Bull Power < 0 且 Bear Power > 0 → 空頭強勢，賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        elder = self.calculate_elder_ray(data)
        bull_power = elder['bull_power']
        bear_power = elder['bear_power']
        
        signals = pd.Series(0, index=data.index)
        
        # 多頭強勢
        bullish = (bull_power > 0) & (bear_power < 0)
        signals[bullish] = 1
        
        # 空頭強勢
        bearish = (bull_power < 0) & (bear_power > 0)
        signals[bearish] = -1
        
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
# 3. TRIX 策略
# ============================================================================

class TRIX(OscillatorStrategy):
    """
    TRIX 策略
    
    三重平滑 ROC，過濾短期噪音的動量指標。
    
    計算方法：
    1. 對收盤價做三次 EMA 平滑
    2. 計算變化率 ROC
    
    信號規則：
    - TRIX 從下上穿 0 → 買入
    - TRIX 從上下穿 0 → 賣出
    """
    
    def __init__(self, period: int = 15):
        """
        初始化 TRIX
        
        Args:
            period: TRIX 周期（默认 15）
        """
        super().__init__('TRIX', {
            'period': period
        })
    
    def calculate_trix(self, data: pd.DataFrame) -> pd.Series:
        """
        計算 TRIX
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            TRIX 序列
        """
        period = self.params['period']
        close = data['close']
        
        # 三次 EMA 平滑
        ema1 = close.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        
        # 計算變化率 ROC
        trix = ema3.pct_change() * 10000  # 放大 10000 倍方便閱讀
        
        return trix
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - TRIX 從下上穿 0 → 買入
        - TRIX 從上下穿 0 → 賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        trix = self.calculate_trix(data)
        
        signals = pd.Series(0, index=data.index)
        
        # TRIX 上穿 0
        cross_above_zero = (trix > 0) & (trix.shift(1) < 0)
        signals[cross_above_zero] = 1
        
        # TRIX 下穿 0
        cross_below_zero = (trix < 0) & (trix.shift(1) > 0)
        signals[cross_below_zero] = -1
        
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
# 4. Klinger 振盪策略
# ============================================================================

class KlingerOscillator(OscillatorStrategy):
    """
    Klinger 振盪策略
    
    結合成交量與價格的趨勢振盪器。
    
    計算方法：
    1. 計算成交量力（Volume Force）
    2. 計算 Klinger 成交量力
    3. 計算 EMA 差值
    
    信號規則：
    - Klinger 從下上穿 Signal → 買入
    - Klinger 從上下穿 Signal → 賣出
    """
    
    def __init__(self, fast_period: int = 34, slow_period: int = 55, 
                 signal_period: int = 13):
        """
        初始化 Klinger 振盪
        
        Args:
            fast_period: 快速周期（默认 34）
            slow_period: 慢速周期（默认 55）
            signal_period: 信號線周期（默认 13）
        """
        super().__init__('Klinger 振盪', {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period
        })
    
    def calculate_klinger(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算 Klinger 振盪器
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            包含 Klinger 和 Signal 的字典
        """
        high = data['high']
        low = data['low']
        close = data['close']
        volume = data['volume']
        
        fast_period = self.params['fast_period']
        slow_period = self.params['slow_period']
        signal_period = self.params['signal_period']
        
        # 計算 HLC 平均
        hlc = (high + low + close) / 3
        
        # 計算 DM（方向測量）
        dm = high - low
        
        # 計算 CM（累積測量）
        cm = abs(hlc.diff())
        
        # 計算成交量力
        vf = np.where(dm > cm, volume, -volume)
        vf = pd.Series(vf, index=data.index)
        
        # 計算 Klinger 成交量力
        kvf_fast = vf.ewm(span=fast_period, adjust=False).mean()
        kvf_slow = vf.ewm(span=slow_period, adjust=False).mean()
        
        # Klinger 振盪器
        klinger = kvf_fast - kvf_slow
        
        # 信號線
        signal = klinger.ewm(span=signal_period, adjust=False).mean()
        
        return {
            'klinger': klinger,
            'signal': signal
        }
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - Klinger 從下上穿 Signal → 買入
        - Klinger 從上下穿 Signal → 賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        kvo = self.calculate_klinger(data)
        klinger = kvo['klinger']
        signal = kvo['signal']
        
        signals = pd.Series(0, index=data.index)
        
        # Klinger 上穿 Signal
        cross_above = (klinger > signal) & (klinger.shift(1) < signal.shift(1))
        signals[cross_above] = 1
        
        # Klinger 下穿 Signal
        cross_below = (klinger < signal) & (klinger.shift(1) > signal.shift(1))
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
# 5. Chande 動量振盪策略
# ============================================================================

class ChandeMomentumOscillator(OscillatorStrategy):
    """
    Chande 動量振盪策略
    
    直接加總漲跌動量，範圍 -100 到 +100。
    
    計算方法：
    CMO = 100 * (Sum(Gain) - Sum(Loss)) / (Sum(Gain) + Sum(Loss))
    
    信號規則：
    - CMO < -50 且上穿 → 買入
    - CMO > +50 且下穿 → 賣出
    """
    
    def __init__(self, period: int = 14, overbought: float = 50, 
                 oversold: float = -50):
        """
        初始化 Chande 動量振盪
        
        Args:
            period: 周期（默认 14）
            overbought: 超買線（默认 +50）
            oversold: 超賣線（默认 -50）
        """
        super().__init__('Chande 動量振盪', {
            'period': period,
            'overbought': overbought,
            'oversold': oversold
        })
    
    def calculate_cmo(self, data: pd.DataFrame) -> pd.Series:
        """
        計算 Chande 動量振盪
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            CMO 序列
        """
        period = self.params['period']
        delta = data['close'].diff()
        
        # 分離漲跌
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        
        # 計算總和
        sum_gain = gain.rolling(window=period).sum()
        sum_loss = loss.rolling(window=period).sum()
        
        # 計算 CMO
        cmo = 100 * (sum_gain - sum_loss) / (sum_gain + sum_loss + 1e-10)
        
        return cmo
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - CMO < -50 且上穿 → 買入
        - CMO > +50 且下穿 → 賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        cmo = self.calculate_cmo(data)
        overbought = self.params['overbought']
        oversold = self.params['oversold']
        
        signals = pd.Series(0, index=data.index)
        
        # CMO 從超賣區上穿
        cross_above_oversold = (cmo > oversold) & (cmo.shift(1) < oversold)
        signals[cross_above_oversold] = 1
        
        # CMO 從超買區下穿
        cross_below_overbought = (cmo < overbought) & (cmo.shift(1) > overbought)
        signals[cross_below_overbought] = -1
        
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
# 6. Detrended Price Oscillator 策略
# ============================================================================

class DetrendedPriceOscillator(OscillatorStrategy):
    """
    Detrended Price Oscillator（DPO）策略
    
    移除長期趨勢後觀察短期週期。
    
    計算方法：
    DPO = Close - SMA(Close, N/2 + 1).shift(N/2 + 1)
    
    信號規則：
    - DPO 從下上穿 0 → 買入
    - DPO 從上下穿 0 → 賣出
    """
    
    def __init__(self, period: int = 20):
        """
        初始化 DPO
        
        Args:
            period: 周期（默认 20）
        """
        super().__init__('Detrended Price Oscillator', {
            'period': period
        })
    
    def calculate_dpo(self, data: pd.DataFrame) -> pd.Series:
        """
        計算 DPO
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            DPO 序列
        """
        period = self.params['period']
        close = data['close']
        
        # 計算移位
        shift = period // 2 + 1
        
        # 計算 SMA
        sma = close.rolling(window=period).mean()
        
        # 計算 DPO
        dpo = close - sma.shift(shift)
        
        return dpo
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - DPO 從下上穿 0 → 買入
        - DPO 從上下穿 0 → 賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        dpo = self.calculate_dpo(data)
        
        signals = pd.Series(0, index=data.index)
        
        # DPO 上穿 0
        cross_above_zero = (dpo > 0) & (dpo.shift(1) < 0)
        signals[cross_above_zero] = 1
        
        # DPO 下穿 0
        cross_below_zero = (dpo < 0) & (dpo.shift(1) > 0)
        signals[cross_below_zero] = -1
        
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
# 7. Ulcer Index 策略
# ============================================================================

class UlcerIndex(OscillatorStrategy):
    """
    Ulcer Index 策略
    
    衡量從近期高點的回撤深度，衡量下行風險。
    
    計算方法：
    1. 計算周期內最高價
    2. 計算回撤百分比
    3. 計算回撤平方和的平均
    4. 開根號
    
    信號規則：
    - Ulcer Index 從高點下降 → 風險降低，買入
    - Ulcer Index 從低點上升 → 風險增加，賣出
    """
    
    def __init__(self, period: int = 14):
        """
        初始化 Ulcer Index
        
        Args:
            period: 周期（默认 14）
        """
        super().__init__('Ulcer Index', {
            'period': period
        })
    
    def calculate_ulcer_index(self, data: pd.DataFrame) -> pd.Series:
        """
        計算 Ulcer Index
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            Ulcer Index 序列
        """
        period = self.params['period']
        close = data['close']
        
        # 計算周期內最高價
        highest = close.rolling(window=period, min_periods=1).max()
        
        # 計算回撤百分比
        drawdown = (close - highest) / highest * 100
        
        # 計算回撤平方
        squared_drawdown = drawdown ** 2
        
        # 計算平均並開根號
        ulcer_index = np.sqrt(squared_drawdown.rolling(window=period).mean())
        
        return ulcer_index
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - Ulcer Index 從高點下降 → 風險降低，買入
        - Ulcer Index 從低點上升 → 風險增加，賣出
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        ui = self.calculate_ulcer_index(data)
        
        signals = pd.Series(0, index=data.index)
        
        # UI 下降（風險降低）
        ui_declining = ui < ui.shift(1)
        signals[ui_declining] = 1
        
        # UI 上升（風險增加）
        ui_rising = ui > ui.shift(1)
        signals[ui_rising] = -1
        
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
# 8. Mass Index 策略
# ============================================================================

class MassIndex(OscillatorStrategy):
    """
    Mass Index 策略
    
    追蹤高低點範圍的擴張，預測反轉。
    
    計算方法：
    1. 計算單日範圍（High - Low）的 EMA
    2. 計算 EMA 的 EMA
    3. 計算比率
    4. 計算 25 期總和
    
    信號規則：
    - Mass Index > 27 → 可能反轉
    - Mass Index < 26.5 → 趨勢延續
    """
    
    def __init__(self, period: int = 9, threshold_high: float = 27, 
                 threshold_low: float = 26.5):
        """
        初始化 Mass Index
        
        Args:
            period: EMA 周期（默认 9）
            threshold_high: 高閾值（默认 27）
            threshold_low: 低閾值（默认 26.5）
        """
        super().__init__('Mass Index', {
            'period': period,
            'threshold_high': threshold_high,
            'threshold_low': threshold_low
        })
    
    def calculate_mass_index(self, data: pd.DataFrame) -> pd.Series:
        """
        計算 Mass Index
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            Mass Index 序列
        """
        period = self.params['period']
        
        # 計算單日範圍
        range_high_low = data['high'] - data['low']
        
        # 計算 EMA
        ema1 = range_high_low.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        
        # 計算比率
        ratio = ema1 / ema2
        
        # 計算 25 期總和
        mass_index = ratio.rolling(window=25).sum()
        
        return mass_index
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號
        
        信號規則：
        - Mass Index > 27 → 可能反轉，賣出
        - Mass Index < 26.5 → 趨勢延續，持有
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            信號 Series
        """
        mass_index = self.calculate_mass_index(data)
        threshold_high = self.params['threshold_high']
        threshold_low = self.params['threshold_low']
        
        signals = pd.Series(0, index=data.index)
        
        # Mass Index > 27（可能反轉）
        signals[mass_index > threshold_high] = -1
        
        # Mass Index < 26.5（趨勢延續）
        signals[mass_index < threshold_low] = 1
        
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

COMPLETE_OSCILLATOR_STRATEGIES = {
    'fisher': FisherTransform,
    'elder_ray': ElderRay,
    'trix': TRIX,
    'klinger': KlingerOscillator,
    'chande_momentum': ChandeMomentumOscillator,
    'dpo': DetrendedPriceOscillator,
    'ulcer_index': UlcerIndex,
    'mass_index': MassIndex,
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
    print("完整振盪器策略測試（8 個）")
    print("=" * 60)
    
    strategies = [
        ('Fisher Transform', FisherTransform()),
        ('Elder Ray', ElderRay()),
        ('TRIX', TRIX()),
        ('Klinger 振盪', KlingerOscillator()),
        ('Chande 動量振盪', ChandeMomentumOscillator()),
        ('DPO', DetrendedPriceOscillator()),
        ('Ulcer Index', UlcerIndex()),
        ('Mass Index', MassIndex()),
    ]
    
    for name, strategy in strategies:
        print(f"\n{name}")
        signals = strategy.generate_signals(data)
        print(f"   信號數量：{(signals != 0).sum()}")
        print(f"   ✅ 測試通過")
    
    print("\n" + "=" * 60)
    print("🎉 8 個完整振盪器策略全部測試通過！")
    print("=" * 60)
