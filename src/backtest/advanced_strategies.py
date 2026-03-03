# 高級交易策略庫
# 新增 10+ 專業策略

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Tuple


# ════════════════════════════════════════════════════════════
# 策略 16: Ichimoku Cloud（一目均衡表）
# ════════════════════════════════════════════════════════════

def ichimoku_strategy(
    ohlcv: List[Dict[str, Any]],
    exchange: str,
    symbol: str,
    timeframe: str,
    initial_equity: float = 10000,
    leverage: float = 1.0,
    fee_rate: float = 0.001,
    slippage: float = 0.001,
    tenkan_period: int = 9,
    kijun_period: int = 26,
    senkou_b_period: int = 52,
) -> Dict[str, Any]:
    """
    一目均衡表策略
    
    原理：
    - 轉換線（Tenkan-sen）：9 期間最高價和最低價的平均
    - 基準線（Kijun-sen）：26 期間最高價和最低價的平均
    - 先行帶 A（Senkou Span A）：轉換線和基準線的平均，向前 26 期
    - 先行帶 B（Senkou Span B）：52 期間最高價和最低價的平均，向前 26 期
    
    信號：
    - 買入：價格向上突破雲層，或轉換線向上穿越基準線
    - 賣出：價格向下跌破雲層，或轉換線向下穿越基準線
    """
    df = pd.DataFrame(ohlcv)
    
    # 計算一目均衡表
    high_9 = df['high'].rolling(window=tenkan_period).max()
    low_9 = df['low'].rolling(window=tenkan_period).min()
    high_26 = df['high'].rolling(window=kijun_period).max()
    low_26 = df['low'].rolling(window=kijun_period).min()
    high_52 = df['high'].rolling(window=senkou_b_period).max()
    low_52 = df['low'].rolling(window=senkou_b_period).min()
    
    # 轉換線
    df['tenkan'] = (high_9 + low_9) / 2
    # 基準線
    df['kijun'] = (high_26 + low_26) / 2
    # 先行帶 A
    df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(kijun_period)
    # 先行帶 B
    df['senkou_b'] = ((high_52 + low_52) / 2).shift(kijun_period)
    
    # 交易邏輯
    position = 0
    entry_price = 0
    trades = []
    equity_curve = [{'timestamp': df.iloc[0]['timestamp'], 'equity': initial_equity}]
    equity = initial_equity
    
    for i in range(kijun_period + 1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # 買入信號：價格向上突破雲層 或 轉換線向上穿越基準線
        if position == 0:
            if (row['close'] > max(row['senkou_a'], row['senkou_b']) and 
                prev_row['close'] <= max(prev_row['senkou_a'], prev_row['senkou_b'])):
                # 開多倉
                position = 1
                entry_price = row['close'] * (1 + slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'BUY',
                    'price': entry_price,
                    'type': 'LONG'
                })
            
            elif (row['close'] < min(row['senkou_a'], row['senkou_b']) and 
                  prev_row['close'] >= min(prev_row['senkou_a'], prev_row['senkou_b'])):
                # 開空倉
                position = -1
                entry_price = row['close'] * (1 - slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'SELL',
                    'price': entry_price,
                    'type': 'SHORT'
                })
        
        # 平倉信號
        elif position == 1:
            # 轉換線向下穿越基準線
            if row['tenkan'] < row['kijun'] and prev_row['tenkan'] >= prev_row['kijun']:
                exit_price = row['close'] * (1 - slippage)
                pnl = (exit_price - entry_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'LONG'
                })
                position = 0
                entry_price = 0
        
        elif position == -1:
            # 轉換線向上穿越基準線
            if row['tenkan'] > row['kijun'] and prev_row['tenkan'] <= prev_row['kijun']:
                exit_price = row['close'] * (1 + slippage)
                pnl = (entry_price - exit_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'SHORT'
                })
                position = 0
                entry_price = 0
        
        equity_curve.append({
            'timestamp': row['timestamp'],
            'equity': equity
        })
    
    # 計算績效指標
    from .engine import compute_metrics
    metrics = compute_metrics(equity_curve, trades, initial_equity, df.iloc[0]['timestamp'], df.iloc[-1]['timestamp'])
    
    return {
        'equity_curve': equity_curve,
        'trades': trades,
        'metrics': metrics,
        'raw_ohlcv': ohlcv,
        'error': None
    }


# ════════════════════════════════════════════════════════════
# 策略 17: Hull MA（赫爾移動平均）
# ════════════════════════════════════════════════════════════

def hull_ma_strategy(
    ohlcv: List[Dict[str, Any]],
    exchange: str,
    symbol: str,
    timeframe: str,
    initial_equity: float = 10000,
    leverage: float = 1.0,
    fee_rate: float = 0.001,
    slippage: float = 0.001,
    hull_period: int = 9,
) -> Dict[str, Any]:
    """
    赫爾移動平均策略
    
    原理：
    HMA = WMA(2*WMA(n/2) - WMA(n)), sqrt(n)
    比傳統 MA 更平滑，延遲更小
    
    信號：
    - 買入：價格向上穿越 HMA
    - 賣出：價格向下穿越 HMA
    """
    df = pd.DataFrame(ohlcv)
    
    def wma(series, period):
        """加權移動平均"""
        weights = np.arange(1, period + 1)
        return series.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    
    # 計算 HMA
    half_period = int(hull_period / 2)
    sqrt_period = int(np.sqrt(hull_period))
    
    wma_half = wma(df['close'], half_period)
    wma_full = wma(df['close'], hull_period)
    
    df['hma'] = wma(2 * wma_half - wma_full, sqrt_period)
    
    # 交易邏輯
    position = 0
    entry_price = 0
    trades = []
    equity_curve = [{'timestamp': df.iloc[0]['timestamp'], 'equity': initial_equity}]
    equity = initial_equity
    
    for i in range(hull_period + sqrt_period + 1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        if position == 0:
            # 價格向上穿越 HMA
            if prev_row['close'] <= prev_row['hma'] and row['close'] > row['hma']:
                position = 1
                entry_price = row['close'] * (1 + slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'BUY',
                    'price': entry_price,
                    'type': 'LONG'
                })
            
            # 價格向下穿越 HMA
            elif prev_row['close'] >= prev_row['hma'] and row['close'] < row['hma']:
                position = -1
                entry_price = row['close'] * (1 - slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'SELL',
                    'price': entry_price,
                    'type': 'SHORT'
                })
        
        elif position == 1:
            # 價格向下穿越 HMA
            if prev_row['close'] >= prev_row['hma'] and row['close'] < row['hma']:
                exit_price = row['close'] * (1 - slippage)
                pnl = (exit_price - entry_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'LONG'
                })
                position = 0
                entry_price = 0
        
        elif position == -1:
            # 價格向上穿越 HMA
            if prev_row['close'] <= prev_row['hma'] and row['close'] > row['hma']:
                exit_price = row['close'] * (1 + slippage)
                pnl = (entry_price - exit_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'SHORT'
                })
                position = 0
                entry_price = 0
        
        equity_curve.append({
            'timestamp': row['timestamp'],
            'equity': equity
        })
    
    from .engine import compute_metrics
    metrics = compute_metrics(equity_curve, trades, initial_equity, df.iloc[0]['timestamp'], df.iloc[-1]['timestamp'])
    
    return {
        'equity_curve': equity_curve,
        'trades': trades,
        'metrics': metrics,
        'raw_ohlcv': ohlcv,
        'error': None
    }


# ════════════════════════════════════════════════════════════
# 策略 18: VWAP（成交量加權平均價格）
# ════════════════════════════════════════════════════════════

def vwap_reversion_strategy(
    ohlcv: List[Dict[str, Any]],
    exchange: str,
    symbol: str,
    timeframe: str,
    initial_equity: float = 10000,
    leverage: float = 1.0,
    fee_rate: float = 0.001,
    slippage: float = 0.001,
    vwap_period: int = 20,
    threshold: float = 2.0,
) -> Dict[str, Any]:
    """
    VWAP 均值回歸策略
    
    原理：
    VWAP = Σ(價格 × 成交量) / Σ(成交量)
    價格偏離 VWAP 過遠時會回歸
    
    信號：
    - 買入：價格低於 VWAP - threshold 標準差
    - 賣出：價格高於 VWAP + threshold 標準差
    """
    df = pd.DataFrame(ohlcv)
    
    # 計算 VWAP
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (typical_price * df['volume']).rolling(window=vwap_period).sum() / df['volume'].rolling(window=vwap_period).sum()
    
    # 計算標準差
    df['vwap_std'] = typical_price.rolling(window=vwap_period).std()
    df['upper_band'] = df['vwap'] + threshold * df['vwap_std']
    df['lower_band'] = df['vwap'] - threshold * df['vwap_std']
    
    # 交易邏輯
    position = 0
    entry_price = 0
    trades = []
    equity_curve = [{'timestamp': df.iloc[0]['timestamp'], 'equity': initial_equity}]
    equity = initial_equity
    
    for i in range(vwap_period + 1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        if position == 0:
            # 價格低於下軌（超賣）
            if row['close'] < row['lower_band']:
                position = 1
                entry_price = row['close'] * (1 + slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'BUY',
                    'price': entry_price,
                    'type': 'LONG'
                })
            
            # 價格高於上軌（超買）
            elif row['close'] > row['upper_band']:
                position = -1
                entry_price = row['close'] * (1 - slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'SELL',
                    'price': entry_price,
                    'type': 'SHORT'
                })
        
        elif position == 1:
            # 價格回歸 VWAP
            if row['close'] >= row['vwap']:
                exit_price = row['close'] * (1 - slippage)
                pnl = (exit_price - entry_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'LONG'
                })
                position = 0
                entry_price = 0
        
        elif position == -1:
            # 價格回歸 VWAP
            if row['close'] <= row['vwap']:
                exit_price = row['close'] * (1 + slippage)
                pnl = (entry_price - exit_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'SHORT'
                })
                position = 0
                entry_price = 0
        
        equity_curve.append({
            'timestamp': row['timestamp'],
            'equity': equity
        })
    
    from .engine import compute_metrics
    metrics = compute_metrics(equity_curve, trades, initial_equity, df.iloc[0]['timestamp'], df.iloc[-1]['timestamp'])
    
    return {
        'equity_curve': equity_curve,
        'trades': trades,
        'metrics': metrics,
        'raw_ohlcv': ohlcv,
        'error': None
    }


# ════════════════════════════════════════════════════════════
# 策略 19: ATR Channel Breakout（ATR 通道突破）
# ════════════════════════════════════════════════════════════

def atr_channel_strategy(
    ohlcv: List[Dict[str, Any]],
    exchange: str,
    symbol: str,
    timeframe: str,
    initial_equity: float = 10000,
    leverage: float = 1.0,
    fee_rate: float = 0.001,
    slippage: float = 0.001,
    atr_period: int = 14,
    channel_multiplier: float = 2.0,
) -> Dict[str, Any]:
    """
    ATR 通道突破策略
    
    原理：
    ATR = 平均真實波幅
    上軌 = 收盤價 + multiplier × ATR
    下軌 = 收盤價 - multiplier × ATR
    
    信號：
    - 買入：價格向上突破上軌
    - 賣出：價格向下跌破下軌
    """
    df = pd.DataFrame(ohlcv)
    
    # 計算 ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(atr_period).mean()
    
    # 計算通道
    df['upper_channel'] = df['close'].shift() + channel_multiplier * df['atr']
    df['lower_channel'] = df['close'].shift() - channel_multiplier * df['atr']
    
    # 交易邏輯
    position = 0
    entry_price = 0
    trades = []
    equity_curve = [{'timestamp': df.iloc[0]['timestamp'], 'equity': initial_equity}]
    equity = initial_equity
    
    for i in range(atr_period + 2, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        if position == 0:
            # 價格向上突破上軌
            if row['close'] > row['upper_channel']:
                position = 1
                entry_price = row['close'] * (1 + slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'BUY',
                    'price': entry_price,
                    'type': 'LONG'
                })
            
            # 價格向下跌破下軌
            elif row['close'] < row['lower_channel']:
                position = -1
                entry_price = row['close'] * (1 - slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'SELL',
                    'price': entry_price,
                    'type': 'SHORT'
                })
        
        elif position == 1:
            # 價格向下跌破下軌或穿越中軸
            if row['close'] < row['lower_channel'] or row['close'] < df['close'].shift(atr_period):
                exit_price = row['close'] * (1 - slippage)
                pnl = (exit_price - entry_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'LONG'
                })
                position = 0
                entry_price = 0
        
        elif position == -1:
            # 價格向上突破上軌或穿越中軸
            if row['close'] > row['upper_channel'] or row['close'] > df['close'].shift(atr_period):
                exit_price = row['close'] * (1 + slippage)
                pnl = (entry_price - exit_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'SHORT'
                })
                position = 0
                entry_price = 0
        
        equity_curve.append({
            'timestamp': row['timestamp'],
            'equity': equity
        })
    
    from .engine import compute_metrics
    metrics = compute_metrics(equity_curve, trades, initial_equity, df.iloc[0]['timestamp'], df.iloc[-1]['timestamp'])
    
    return {
        'equity_curve': equity_curve,
        'trades': trades,
        'metrics': metrics,
        'raw_ohlcv': ohlcv,
        'error': None
    }


# ════════════════════════════════════════════════════════════
# 策略 20: Keltner Channel（肯特納通道）
# ════════════════════════════════════════════════════════════

def keltner_channel_strategy(
    ohlcv: List[Dict[str, Any]],
    exchange: str,
    symbol: str,
    timeframe: str,
    initial_equity: float = 10000,
    leverage: float = 1.0,
    fee_rate: float = 0.001,
    slippage: float = 0.001,
    ema_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0,
) -> Dict[str, Any]:
    """
    肯特納通道策略
    
    原理：
    中軌 = EMA(20)
    上軌 = 中軌 + multiplier × ATR(10)
    下軌 = 中軌 - multiplier × ATR(10)
    
    信號：
    - 買入：價格向上突破上軌
    - 賣出：價格向下跌破下軌
    """
    df = pd.DataFrame(ohlcv)
    
    # 計算 EMA
    df['ema'] = df['close'].ewm(span=ema_period, adjust=False).mean()
    
    # 計算 ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(atr_period).mean()
    
    # 計算通道
    df['upper'] = df['ema'] + multiplier * df['atr']
    df['lower'] = df['ema'] - multiplier * df['atr']
    
    # 交易邏輯
    position = 0
    entry_price = 0
    trades = []
    equity_curve = [{'timestamp': df.iloc[0]['timestamp'], 'equity': initial_equity}]
    equity = initial_equity
    
    for i in range(max(ema_period, atr_period) + 2, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        if position == 0:
            # 價格向上突破上軌
            if row['close'] > row['upper']:
                position = 1
                entry_price = row['close'] * (1 + slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'BUY',
                    'price': entry_price,
                    'type': 'LONG'
                })
            
            # 價格向下跌破下軌
            elif row['close'] < row['lower']:
                position = -1
                entry_price = row['close'] * (1 - slippage)
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'SELL',
                    'price': entry_price,
                    'type': 'SHORT'
                })
        
        elif position == 1:
            # 價格回歸中軌
            if row['close'] < row['ema']:
                exit_price = row['close'] * (1 - slippage)
                pnl = (exit_price - entry_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'LONG'
                })
                position = 0
                entry_price = 0
        
        elif position == -1:
            # 價格回歸中軌
            if row['close'] > row['ema']:
                exit_price = row['close'] * (1 + slippage)
                pnl = (entry_price - exit_price) / entry_price * 100
                fee = fee_rate * 2 * 100
                net_pnl = pnl - fee
                equity *= (1 + net_pnl / 100)
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'CLOSE',
                    'price': exit_price,
                    'pnl_pct': net_pnl,
                    'type': 'SHORT'
                })
                position = 0
                entry_price = 0
        
        equity_curve.append({
            'timestamp': row['timestamp'],
            'equity': equity
        })
    
    from .engine import compute_metrics
    metrics = compute_metrics(equity_curve, trades, initial_equity, df.iloc[0]['timestamp'], df.iloc[-1]['timestamp'])
    
    return {
        'equity_curve': equity_curve,
        'trades': trades,
        'metrics': metrics,
        'raw_ohlcv': ohlcv,
        'error': None
    }


# 策略註冊表
ADVANCED_STRATEGIES = {
    'ichimoku': {
        'name': '一目均衡表',
        'function': ichimoku_strategy,
        'category': '趨勢',
        'params': {
            'tenkan_period': {'type': 'int', 'default': 9, 'min': 5, 'max': 20},
            'kijun_period': {'type': 'int', 'default': 26, 'min': 20, 'max': 50},
            'senkou_b_period': {'type': 'int', 'default': 52, 'min': 40, 'max': 100}
        }
    },
    'hull_ma': {
        'name': '赫爾移動平均',
        'function': hull_ma_strategy,
        'category': '趨勢',
        'params': {
            'hull_period': {'type': 'int', 'default': 9, 'min': 5, 'max': 50}
        }
    },
    'vwap_reversion': {
        'name': 'VWAP 回歸',
        'function': vwap_reversion_strategy,
        'category': '均值回歸',
        'params': {
            'vwap_period': {'type': 'int', 'default': 20, 'min': 10, 'max': 50},
            'threshold': {'type': 'float', 'default': 2.0, 'min': 1.0, 'max': 5.0}
        }
    },
    'atr_channel': {
        'name': 'ATR 通道突破',
        'function': atr_channel_strategy,
        'category': '突破',
        'params': {
            'atr_period': {'type': 'int', 'default': 14, 'min': 7, 'max': 30},
            'channel_multiplier': {'type': 'float', 'default': 2.0, 'min': 1.0, 'max': 5.0}
        }
    },
    'keltner_channel': {
        'name': '肯特納通道',
        'function': keltner_channel_strategy,
        'category': '趨勢',
        'params': {
            'ema_period': {'type': 'int', 'default': 20, 'min': 10, 'max': 50},
            'atr_period': {'type': 'int', 'default': 10, 'min': 5, 'max': 30},
            'multiplier': {'type': 'float', 'default': 2.0, 'min': 1.0, 'max': 5.0}
        }
    }
}
