"""
统计套利与资金费率套利

功能：
- 配对交易（统计套利）
- 资金费率套利（现货 vs 永续合约）

套利类型：
1. 配对交易 — 利用两个相关资产的价差均值回归
2. 资金费率 — 做多现货 + 做空永续合约，赚取资金费率

理论基础：
- 配对交易：Gateau & Geman (2005), Elliott et al. (2005)
- 协整检验：Engle-Granger 两步法
- 资金费率：永续合约的资金费率机制
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# ─────────────────────────────────────
# 配对交易（统计套利）
# ─────────────────────────────────────

class SpreadModel(Enum):
    """价差模型"""
    RATIO = "ratio"           # 价格比值
    DIFFERENCE = "difference" # 价格差
    ZSCORE = "zscore"         # Z-Score 标准化


@dataclass
class PairSignal:
    """配对交易信号"""
    pair: Tuple[str, str]
    signal: str  # long_spread / short_spread / close / neutral
    zscore: float
    spread: float
    half_life: float
    entry_price_a: float
    entry_price_b: float
    timestamp: datetime
    confidence: float = 0.0


class StatisticalArbitrage:
    """
    配对交易 / 统计套利
    
    核心逻辑：
    1. 找到协整的资产对
    2. 监控价差（Spread）偏离均值
    3. 价差过大时做空价差（做空涨得多的，做多跌得多的）
    4. 价差回归时平仓获利
    
    关键指标：
    - 协整性检验（Engle-Granger）
    - 半衰期（Half-life）：价差回归均值的速度
    - Z-Score：当前价差偏离程度
    
    参数：
    - entry_zscore: 入场阈值（如 2.0）
    - exit_zscore: 出场阈值（如 0.5）
    - stop_zscore: 止损阈值（如 4.0）
    - lookback_period: 回看窗口（天）
    """
    
    def __init__(
        self,
        price_data: pd.DataFrame,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.5,
        stop_zscore: float = 4.0,
        lookback_period: int = 60,
        min_half_life: int = 5,
        max_half_life: int = 60,
        spread_model: SpreadModel = SpreadModel.ZSCORE
    ):
        """
        初始化
        
        Args:
            price_data: 价格 DataFrame，每列一个资产
            entry_zscore: 入场 Z-Score 阈值
            exit_zscore: 出场 Z-Score 阈值
            stop_zscore: 止损 Z-Score 阈值
            lookback_period: 回看周期（天）
            min_half_life: 最小半衰期
            max_half_life: 最大半衰期
            spread_model: 价差模型
        """
        self.price_data = price_data
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.stop_zscore = stop_zscore
        self.lookback_period = lookback_period
        self.min_half_life = min_half_life
        self.max_half_life = max_half_life
        self.spread_model = spread_model
        
        # 缓存
        self._cointegration_cache: Dict[Tuple[str, str], Dict] = {}
    
    def test_cointegration(
        self,
        asset_a: str,
        asset_b: str
    ) -> Dict[str, Any]:
        """
        协整性检验（Engle-Granger 两步法）
        
        Args:
            asset_a: 资产 A
            asset_b: 资产 B
        
        Returns:
            协整检验结果
        """
        from statsmodels.tsa.stattools import coint, adfuller
        
        if asset_a not in self.price_data.columns or asset_b not in self.price_data.columns:
            return {'is_cointegrated': False, 'error': '资产不存在'}
        
        series_a = self.price_data[asset_a].dropna()
        series_b = self.price_data[asset_b].dropna()
        
        # 对齐索引
        common_idx = series_a.index.intersection(series_b.index)
        series_a = series_a.loc[common_idx]
        series_b = series_b.loc[common_idx]
        
        if len(series_a) < 30:
            return {'is_cointegrated': False, 'error': '数据不足'}
        
        # Engle-Granger 协整检验
        try:
            coint_stat, p_value, critical_values = coint(series_a, series_b)
        except Exception as e:
            return {'is_cointegrated': False, 'error': str(e)}
        
        # 回归计算对冲比率
        from numpy.polynomial.polynomial import polyfit
        beta = np.polyfit(series_b.values, series_a.values, 1)[0]
        
        # 计算价差
        spread = series_a - beta * series_b
        
        # ADF 检验价差的平稳性
        adf_stat, adf_p, _, _, adf_critical, _ = adfuller(spread.dropna())
        
        # 半衰期
        half_life = self._calculate_half_life(spread)
        
        is_cointegrated = p_value < 0.05 and adf_p < 0.05
        
        result = {
            'asset_a': asset_a,
            'asset_b': asset_b,
            'is_cointegrated': is_cointegrated,
            'coint_p_value': p_value,
            'coint_stat': coint_stat,
            'adf_p_value': adf_p,
            'adf_stat': adf_stat,
            'hedge_ratio': beta,
            'half_life': half_life,
            'critical_values': {
                '1%': critical_values[0],
                '5%': critical_values[1],
                '10%': critical_values[2],
            }
        }
        
        # 缓存
        self._cointegration_cache[(asset_a, asset_b)] = result
        
        return result
    
    def _calculate_half_life(self, spread: pd.Series) -> float:
        """
        计算半衰期
        
        使用 OLS 回归：Δspread_t = α + β * spread_{t-1} + ε
        半衰期 = -ln(2) / β
        """
        spread_lag = spread.shift(1).dropna()
        spread_diff = spread.diff().dropna()
        
        # 对齐
        common_idx = spread_lag.index.intersection(spread_diff.index)
        spread_lag = spread_lag.loc[common_idx]
        spread_diff = spread_diff.loc[common_idx]
        
        if len(spread_lag) < 10:
            return float('inf')
        
        # OLS
        beta = np.polyfit(spread_lag.values, spread_diff.values, 1)[0]
        
        if beta >= 0:
            return float('inf')  # 不是均值回归
        
        half_life = -np.log(2) / beta
        
        return max(1, half_life)
    
    def compute_spread(
        self,
        asset_a: str,
        asset_b: str,
        hedge_ratio: Optional[float] = None
    ) -> pd.Series:
        """
        计算价差序列
        
        Args:
            asset_a: 资产 A
            asset_b: 资产 B
            hedge_ratio: 对冲比率（None = 自动计算）
        
        Returns:
            价差序列
        """
        if hedge_ratio is None:
            # 使用缓存的对冲比率或重新计算
            cache_key = (asset_a, asset_b)
            if cache_key in self._cointegration_cache:
                hedge_ratio = self._cointegration_cache[cache_key]['hedge_ratio']
            else:
                result = self.test_cointegration(asset_a, asset_b)
                hedge_ratio = result.get('hedge_ratio', 1.0)
        
        spread = self.price_data[asset_a] - hedge_ratio * self.price_data[asset_b]
        return spread
    
    def compute_zscore(
        self,
        spread: pd.Series,
        window: Optional[int] = None
    ) -> pd.Series:
        """
        计算 Z-Score
        
        Args:
            spread: 价差序列
            window: 滚动窗口（None = 使用 lookback_period）
        
        Returns:
            Z-Score 序列
        """
        window = window or self.lookback_period
        
        mean = spread.rolling(window=window).mean()
        std = spread.rolling(window=window).std()
        
        zscore = (spread - mean) / std
        return zscore
    
    def scan_pairs(
        self,
        asset_pairs: List[Tuple[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        批量扫描配对
        
        Args:
            asset_pairs: 资产对列表
        
        Returns:
            协整配对列表（按 p-value 排序）
        """
        results = []
        
        for asset_a, asset_b in asset_pairs:
            result = self.test_cointegration(asset_a, asset_b)
            if result['is_cointegrated']:
                # 检查半衰期是否合理
                hl = result['half_life']
                if self.min_half_life <= hl <= self.max_half_life:
                    results.append(result)
        
        # 按 p-value 排序
        results.sort(key=lambda x: x['coint_p_value'])
        
        logger.info(f"扫描 {len(asset_pairs)} 对，找到 {len(results)} 个协整配对")
        
        return results
    
    def generate_signal(
        self,
        asset_a: str,
        asset_b: str,
        current_prices: Optional[Dict[str, float]] = None
    ) -> PairSignal:
        """
        生成交易信号
        
        Args:
            asset_a: 资产 A
            asset_b: 资产 B
            current_prices: 当前价格（None = 使用最新数据）
        
        Returns:
            交易信号
        """
        # 获取协整信息
        cache_key = (asset_a, asset_b)
        if cache_key in self._cointegration_cache:
            coint_info = self._cointegration_cache[cache_key]
        else:
            coint_info = self.test_cointegration(asset_a, asset_b)
        
        hedge_ratio = coint_info.get('hedge_ratio', 1.0)
        half_life = coint_info.get('half_life', float('inf'))
        
        # 计算价差和 Z-Score
        spread = self.compute_spread(asset_a, asset_b, hedge_ratio)
        zscore = self.compute_zscore(spread)
        
        # 当前值
        current_zscore = zscore.iloc[-1] if not zscore.empty else 0
        current_spread = spread.iloc[-1] if not spread.empty else 0
        
        # 获取当前价格
        if current_prices:
            price_a = current_prices.get(asset_a, 0)
            price_b = current_prices.get(asset_b, 0)
        else:
            price_a = self.price_data[asset_a].iloc[-1] if not self.price_data[asset_a].empty else 0
            price_b = self.price_data[asset_b].iloc[-1] if not self.price_data[asset_b].empty else 0
        
        # 判断信号
        if abs(current_zscore) < self.exit_zscore:
            signal = "close"
            confidence = 0.5
        elif current_zscore > self.entry_zscore:
            signal = "short_spread"  # 做空价差（A 太贵 / B 太便宜）
            confidence = min(1.0, abs(current_zscore) / self.stop_zscore)
        elif current_zscore < -self.entry_zscore:
            signal = "long_spread"  # 做多价差（A 太便宜 / B 太贵）
            confidence = min(1.0, abs(current_zscore) / self.stop_zscore)
        else:
            signal = "neutral"
            confidence = 0.0
        
        return PairSignal(
            pair=(asset_a, asset_b),
            signal=signal,
            zscore=current_zscore,
            spread=current_spread,
            half_life=half_life,
            entry_price_a=price_a,
            entry_price_b=price_b,
            timestamp=datetime.now(),
            confidence=confidence
        )
    
    def backtest_pair(
        self,
        asset_a: str,
        asset_b: str,
        initial_capital: float = 100000.0
    ) -> Dict[str, Any]:
        """
        回测配对交易策略
        
        Args:
            asset_a: 资产 A
            asset_b: 资产 B
            initial_capital: 初始资金
        
        Returns:
            回测结果
        """
        spread = self.compute_spread(asset_a, asset_b)
        zscore = self.compute_zscore(spread)
        
        prices_a = self.price_data[asset_a]
        prices_b = self.price_data[asset_b]
        
        # 信号
        position = 0  # 0=空仓, 1=多价差, -1=空价差
        entries = []
        exits = []
        pnl_series = []
        capital = initial_capital
        
        hedge_ratio = self._cointegration_cache.get(
            (asset_a, asset_b), {}
        ).get('hedge_ratio', 1.0)
        
        for i in range(self.lookback_period, len(zscore)):
            z = zscore.iloc[i]
            
            if np.isnan(z):
                pnl_series.append(capital)
                continue
            
            if position == 0:
                if z > self.entry_zscore:
                    position = -1  # 做空价差
                    entries.append({
                        'index': i,
                        'type': 'short_spread',
                        'zscore': z,
                        'price_a': prices_a.iloc[i],
                        'price_b': prices_b.iloc[i],
                    })
                elif z < -self.entry_zscore:
                    position = 1  # 做多价差
                    entries.append({
                        'index': i,
                        'type': 'long_spread',
                        'zscore': z,
                        'price_a': prices_a.iloc[i],
                        'price_b': prices_b.iloc[i],
                    })
            else:
                should_exit = False
                exit_reason = ""
                
                if abs(z) < self.exit_zscore:
                    should_exit = True
                    exit_reason = "mean_reversion"
                elif abs(z) > self.stop_zscore:
                    should_exit = True
                    exit_reason = "stop_loss"
                
                if should_exit:
                    # 计算 PnL
                    entry = entries[-1]
                    ret_a = (prices_a.iloc[i] - entry['price_a']) / entry['price_a']
                    ret_b = (prices_b.iloc[i] - entry['price_b']) / entry['price_b']
                    
                    if position == 1:  # 做多价差：long A, short B
                        trade_pnl = (ret_a - hedge_ratio * ret_b) * capital * 0.5
                    else:  # 做空价差：short A, long B
                        trade_pnl = (-ret_a + hedge_ratio * ret_b) * capital * 0.5
                    
                    capital += trade_pnl
                    
                    exits.append({
                        'index': i,
                        'reason': exit_reason,
                        'zscore': z,
                        'pnl': trade_pnl,
                    })
                    
                    position = 0
            
            pnl_series.append(capital)
        
        # 统计
        trades = min(len(entries), len(exits))
        winning = sum(1 for e in exits if e['pnl'] > 0)
        total_pnl = capital - initial_capital
        
        return {
            'pair': (asset_a, asset_b),
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_pnl': total_pnl,
            'total_return': total_pnl / initial_capital,
            'num_trades': trades,
            'win_rate': winning / trades if trades > 0 else 0,
            'entries': entries,
            'exits': exits,
            'pnl_series': pnl_series,
        }


# ─────────────────────────────────────
# 资金费率套利
# ─────────────────────────────────────

@dataclass
class FundingRateOpportunity:
    """资金费率套利机会"""
    symbol: str
    exchange: str
    funding_rate: float          # 当前资金费率
    annualized_rate: float       # 年化收益率
    spot_price: float
    perpetual_price: float
    basis: float                 # 基差（永续 - 现货）
    basis_pct: float             # 基差百分比
    estimated_profit: float      # 预估利润
    timestamp: datetime


class FundingRateArbitrage:
    """
    资金费率套利
    
    核心逻辑：
    1. 当资金费率为正时：做多现货 + 做空永续合约
       → 收取资金费率
    2. 当资金费率为负时：做空现货 + 做多永续合约
       → 收取资金费率（反向操作）
    
    收益来源：
    - 资金费率收入（每 8 小时结算一次）
    - 基差收敛收益（如果存在基差）
    
    风险：
    - 资金费率波动
    - 现货/合约价格背离
    - 强制平仓风险
    - 手续费侵蚀
    
    年化收益率 ≈ 资金费率 × 3 × 365 × 100%
    """
    
    def __init__(
        self,
        exchanges: Optional[List[str]] = None,
        min_annualized_rate: float = 5.0,   # 最低年化 5%
        min_funding_rate: float = 0.0001,   # 最低资金费率 0.01%
        max_position_usd: float = 50000,
        funding_interval_hours: int = 8
    ):
        """
        初始化
        
        Args:
            exchanges: 交易所列表
            min_annualized_rate: 最低年化收益率
            min_funding_rate: 最低资金费率
            max_position_usd: 最大仓位
            funding_interval_hours: 资金费率结算间隔（小时）
        """
        self.exchanges = exchanges or ['binance', 'okx', 'bybit']
        self.min_annualized_rate = min_annualized_rate
        self.min_funding_rate = min_funding_rate
        self.max_position_usd = max_position_usd
        self.funding_interval_hours = funding_interval_hours
        
        # 每天结算次数
        self.settlements_per_day = 24 / funding_interval_hours
    
    def fetch_funding_rate(
        self,
        exchange,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取资金费率
        
        Args:
            exchange: CCXT 交易所实例
            symbol: 交易对
        
        Returns:
            资金费率信息
        """
        try:
            # 获取永续合约资金费率
            funding = exchange.fetch_funding_rate(symbol)
            
            # 获取现货价格
            spot_symbol = symbol.replace(':USDT', '').replace('/USDT:USDT', '/USDT')
            ticker = exchange.fetch_ticker(spot_symbol)
            
            return {
                'symbol': symbol,
                'funding_rate': funding.get('fundingRate', 0),
                'next_funding_time': funding.get('fundingTimestamp'),
                'spot_price': ticker.get('last', 0),
                'mark_price': funding.get('markPrice', ticker.get('last', 0)),
            }
        except Exception as e:
            logger.debug(f"获取 {symbol} 资金费率失败：{e}")
            return None
    
    def scan_opportunities(
        self,
        symbols: List[str],
        exchange_instances: Optional[Dict[str, Any]] = None
    ) -> List[FundingRateOpportunity]:
        """
        扫描资金费率套利机会
        
        Args:
            symbols: 永续合约交易对列表
            exchange_instances: CCXT 交易所实例字典
        
        Returns:
            套利机会列表
        """
        opportunities = []
        
        for exchange_id in self.exchanges:
            exchange = exchange_instances.get(exchange_id) if exchange_instances else None
            if exchange is None:
                continue
            
            for symbol in symbols:
                data = self.fetch_funding_rate(exchange, symbol)
                if data is None:
                    continue
                
                rate = data['funding_rate']
                
                # 年化 = 费率 × 每天结算次数 × 365
                annualized = abs(rate) * self.settlements_per_day * 365 * 100
                
                if abs(rate) < self.min_funding_rate:
                    continue
                if annualized < self.min_annualized_rate:
                    continue
                
                spot = data['spot_price']
                mark = data.get('mark_price', spot)
                basis = mark - spot
                basis_pct = (basis / spot * 100) if spot > 0 else 0
                
                # 预估利润（假设持仓 30 天）
                hold_days = 30
                est_profit = (
                    abs(rate) * self.settlements_per_day * hold_days
                    * self.max_position_usd
                )
                
                opp = FundingRateOpportunity(
                    symbol=symbol,
                    exchange=exchange_id,
                    funding_rate=rate,
                    annualized_rate=annualized,
                    spot_price=spot,
                    perpetual_price=mark,
                    basis=basis,
                    basis_pct=basis_pct,
                    estimated_profit=est_profit,
                    timestamp=datetime.now()
                )
                
                opportunities.append(opp)
                
                direction = "正" if rate > 0 else "负"
                logger.info(
                    f"发现资金费率机会：{exchange_id} {symbol} | "
                    f"费率={rate:.4%} ({direction}) | "
                    f"年化={annualized:.1f}%"
                )
        
        opportunities.sort(key=lambda x: x.annualized_rate, reverse=True)
        return opportunities
    
    def calculate_optimal_hedge(
        self,
        spot_price: float,
        perpetual_price: float,
        funding_rate: float,
        position_usd: float,
        hold_days: int = 30
    ) -> Dict[str, Any]:
        """
        计算最优对冲方案
        
        Args:
            spot_price: 现货价格
            perpetual_price: 永续合约价格
            funding_rate: 资金费率
            position_usd: 仓位金额
            hold_days: 持仓天数
        
        Returns:
            对冲方案详情
        """
        # 现货数量
        spot_amount = position_usd / spot_price
        
        # 合约数量（等值做空）
        contract_amount = position_usd / perpetual_price
        
        # 资金费率收入
        settlements = hold_days * self.settlements_per_day
        funding_income = abs(funding_rate) * settlements * position_usd
        
        # 手续费估算（双边 0.04%）
        trading_fee = position_usd * 0.0004 * 2  # 开 + 平
        
        # 基差损益
        basis = perpetual_price - spot_price
        basis_pnl = 0  # 开仓时基差在，平仓时收敛则无损益
        
        # 净利润
        net_profit = funding_income - trading_fee
        
        return {
            'direction': 'long_spot_short_perp' if funding_rate > 0 else 'short_spot_long_perp',
            'spot_amount': spot_amount,
            'contract_amount': contract_amount,
            'position_usd': position_usd,
            'hold_days': hold_days,
            'funding_income': funding_income,
            'trading_fee': trading_fee,
            'net_profit': net_profit,
            'net_return_pct': net_profit / position_usd * 100,
            'annualized_return': net_profit / position_usd * (365 / hold_days) * 100,
        }
    
    def estimate_risk(
        self,
        spot_price: float,
        perpetual_price: float,
        position_usd: float,
        volatility: float = 0.02
    ) -> Dict[str, Any]:
        """
        估算套利风险
        
        Args:
            spot_price: 现货价格
            perpetual_price: 永续合约价格
            position_usd: 仓位
            volatility: 日波动率
        
        Returns:
            风险评估
        """
        basis = perpetual_price - spot_price
        basis_pct = basis / spot_price if spot_price > 0 else 0
        
        # 基差波动风险
        basis_vol = volatility * 0.3  # 基差波动通常低于价格波动
        
        # 最大可能回撤（3σ）
        max_drawdown = position_usd * basis_vol * 3
        
        # 清算距离（假设 10x 杠杆）
        liquidation_distance = 0.1  # 10%
        liquidation_price_up = perpetual_price * (1 + liquidation_distance)
        liquidation_price_down = perpetual_price * (1 - liquidation_distance)
        
        return {
            'current_basis_pct': basis_pct * 100,
            'basis_volatility': basis_vol * 100,
            'max_drawdown_est': max_drawdown,
            'liquidation_price_up': liquidation_price_up,
            'liquidation_price_down': liquidation_price_down,
            'risk_level': 'low' if abs(basis_pct) < 0.01 else 'medium' if abs(basis_pct) < 0.03 else 'high',
        }
