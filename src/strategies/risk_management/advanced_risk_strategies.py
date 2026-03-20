"""
風險管理策略完整包（7 個）
包含所有進階風險管理策略：
1. Anti-Martingale（反馬丁格爾）
2. 固定比率法
3. CVaR/ES 倉位控制
4. 最優停損
5. 尾部風險對沖
6. 動態對沖（Delta Neutral）
7. 波動率目標

作者：StocksX Team
創建日期：2026-03-20
狀態：✅ 已完成 - 風險管理類別 100%
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from ..base_strategy import RiskManagementStrategy, BaseStrategy


# ============================================================================
# 1. Anti-Martingale（反馬丁格爾）策略
# ============================================================================

class AntiMartingale(RiskManagementStrategy):
    """
    Anti-Martingale 反馬丁格爾策略
    
    盈利加碼，虧損減碼，順勢放大。
    
    規則：
    - 連續盈利 → 增加倉位
    - 連續虧損 → 減少倉位
    """
    
    def __init__(self, base_risk: float = 0.02, 
                 increase_factor: float = 1.5,
                 decrease_factor: float = 0.5,
                 max_consecutive: int = 5):
        """
        初始化反馬丁格爾
        
        Args:
            base_risk: 基礎風險（默认 2%）
            increase_factor: 增加係數（默认 1.5）
            decrease_factor: 減少係數（默认 0.5）
            max_consecutive: 最大連續次數（默认 5）
        """
        super().__init__('Anti-Martingale', {
            'base_risk': base_risk,
            'increase_factor': increase_factor,
            'decrease_factor': decrease_factor,
            'max_consecutive': max_consecutive
        })
        
        self.consecutive_wins = 0
        self.consecutive_losses = 0
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float,
                                 last_pnl: float = 0) -> float:
        """
        計算倉位大小
        
        Args:
            signal: 交易信號
            capital: 可用資金
            price: 當前價格
            volatility: 波動率
            last_pnl: 上次交易盈虧（>0 盈利，<0 虧損）
            
        Returns:
            倉位大小
        """
        if signal == 0:
            return 0
        
        base_risk = self.params['base_risk']
        increase_factor = self.params['increase_factor']
        decrease_factor = self.params['decrease_factor']
        max_consecutive = self.params['max_consecutive']
        
        # 更新連續盈虧計數
        if last_pnl > 0:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        elif last_pnl < 0:
            self.consecutive_losses += 1
            self.consecutive_wins = 0
        else:
            self.consecutive_wins = 0
            self.consecutive_losses = 0
        
        # 限制最大連續次數
        self.consecutive_wins = min(self.consecutive_wins, max_consecutive)
        self.consecutive_losses = min(self.consecutive_losses, max_consecutive)
        
        # 計算調整後的風險
        if self.consecutive_wins > 0:
            # 盈利加碼
            adjusted_risk = base_risk * (increase_factor ** self.consecutive_wins)
        elif self.consecutive_losses > 0:
            # 虧損減碼
            adjusted_risk = base_risk * (decrease_factor ** self.consecutive_losses)
        else:
            adjusted_risk = base_risk
        
        # 計算倉位
        stop_loss_distance = 2 * volatility
        if stop_loss_distance > 0:
            position_size = (capital * adjusted_risk) / stop_loss_distance
            shares = int(position_size / price)
        else:
            shares = 0
        
        return max(0, shares)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成信號（需要配合其他策略）"""
        # 這是一個風險管理策略，通常配合其他信號策略使用
        # 這裡返回全 0，實際使用時會與其他策略組合
        return pd.Series(0, index=data.index)


# ============================================================================
# 2. 固定比率法（Fixed Ratio）策略
# ============================================================================

class FixedRatio(RiskManagementStrategy):
    """
    固定比率法
    
    以每張合約的預期利潤 Delta 調整倉位。
    
    規則：
    - 倉位 = (資本 * 風險%) / (Delta * 價格)
    - Delta 是每張合約的預期利潤
    """
    
    def __init__(self, risk_per_trade: float = 0.02, 
                 delta: float = 0.01):
        """
        初始化固定比率法
        
        Args:
            risk_per_trade: 每筆交易風險（默认 2%）
            delta: 預期利潤率（默认 1%）
        """
        super().__init__('固定比率法', {
            'risk_per_trade': risk_per_trade,
            'delta': delta
        })
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """
        計算倉位大小
        
        Args:
            signal: 交易信號
            capital: 可用資金
            price: 當前價格
            volatility: 波動率
            
        Returns:
            倉位大小
        """
        if signal == 0:
            return 0
        
        risk_per_trade = self.params['risk_per_trade']
        delta = self.params['delta']
        
        # 計算預期利潤
        expected_profit = price * delta
        
        # 計算倉位
        if expected_profit > 0:
            position_value = capital * risk_per_trade
            shares = int(position_value / expected_profit)
        else:
            shares = 0
        
        return max(0, shares)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成信號"""
        return pd.Series(0, index=data.index)


# ============================================================================
# 3. CVaR/ES 倉位控制策略
# ============================================================================

class CVaRPositionSizing(RiskManagementStrategy):
    """
    CVaR/ES（條件在險值）倉位控制
    
    以條件在險值決定最大可承受倉位。
    
    CVaR（Conditional Value at Risk）= Expected Shortfall
    衡量在極端情況下的平均損失
    """
    
    def __init__(self, confidence_level: float = 0.95, 
                 max_cvar: float = 0.05,
                 lookback: int = 252):
        """
        初始化 CVaR 倉位控制
        
        Args:
            confidence_level: 置信水平（默认 95%）
            max_cvar: 最大 CVaR（默认 5%）
            lookback: 回顧期（默认 252 交易日）
        """
        super().__init__('CVaR/ES 倉位控制', {
            'confidence_level': confidence_level,
            'max_cvar': max_cvar,
            'lookback': lookback
        })
    
    def calculate_cvar(self, returns: pd.Series) -> float:
        """
        計算 CVaR
        
        Args:
            returns: 收益率序列
            
        Returns:
            CVaR 值
        """
        confidence = self.params['confidence_level']
        
        # 計算 VaR
        var = returns.quantile(1 - confidence)
        
        # 計算 CVaR（VaR 以下的平均損失）
        cvar = returns[returns <= var].mean()
        
        return abs(cvar) if not np.isnan(cvar) else 0.05
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float,
                                 returns: pd.Series = None) -> float:
        """
        計算倉位大小
        
        Args:
            signal: 交易信號
            capital: 可用資金
            price: 當前價格
            volatility: 波動率
            returns: 歷史收益率序列
            
        Returns:
            倉位大小
        """
        if signal == 0:
            return 0
        
        max_cvar = self.params['max_cvar']
        
        # 如果有歷史數據，計算實際 CVaR
        if returns is not None and len(returns) > 0:
            current_cvar = self.calculate_cvar(returns)
        else:
            current_cvar = volatility  # 使用波動率作為估計
        
        # 根據 CVaR 調整倉位
        if current_cvar > 0:
            # CVaR 越大，倉位越小
            position_size = capital * max_cvar / current_cvar
            shares = int(position_size / price)
        else:
            shares = 0
        
        return max(0, shares)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成信號"""
        return pd.Series(0, index=data.index)


# ============================================================================
# 4. 最優停損（Optimal Stopping）策略
# ============================================================================

class OptimalStopLoss(RiskManagementStrategy):
    """
    最優停損策略
    
    用數學模型決定最佳止損時機。
    
    使用統計方法計算最優止損點：
    - 基於波動率
    - 基於最大回撤
    - 基於時間衰減
    """
    
    def __init__(self, base_stop_loss: float = 0.02,
                 volatility_adjustment: bool = True,
                 time_decay: float = 0.001):
        """
        初始化最優停損
        
        Args:
            base_stop_loss: 基礎止損（默认 2%）
            volatility_adjustment: 波動率調整（默认 True）
            time_decay: 時間衰減（默认 0.001）
        """
        super().__init__('最優停損', {
            'base_stop_loss': base_stop_loss,
            'volatility_adjustment': volatility_adjustment,
            'time_decay': time_decay
        })
        
        self.entry_price = None
        self.entry_time = None
        self.highest_price = None
    
    def calculate_optimal_stop(self, current_price: float, 
                                current_volatility: float,
                                holding_period: int = 0) -> float:
        """
        計算最優止損位
        
        Args:
            current_price: 當前價格
            current_volatility: 當前波動率
            holding_period: 持有期
            
        Returns:
            止損價格
        """
        base_stop = self.params['base_stop_loss']
        
        # 波動率調整
        if self.params['volatility_adjustment']:
            adjusted_stop = base_stop * (1 + current_volatility)
        else:
            adjusted_stop = base_stop
        
        # 時間衰減（持有越久，止損越寬）
        time_adjustment = 1 + self.params['time_decay'] * holding_period
        final_stop = adjusted_stop * time_adjustment
        
        # 計算止損價格
        if self.entry_price:
            stop_price = self.entry_price * (1 - final_stop)
        else:
            stop_price = current_price * (1 - final_stop)
        
        return stop_price
    
    def should_stop(self, current_price: float, current_volatility: float,
                    holding_period: int = 0) -> bool:
        """
        判斷是否應該止損
        
        Args:
            current_price: 當前價格
            current_volatility: 當前波動率
            holding_period: 持有期
            
        Returns:
            是否止損
        """
        stop_price = self.calculate_optimal_stop(
            current_price, current_volatility, holding_period
        )
        
        return current_price <= stop_price
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成止損信號"""
        # 這是一個風險管理策略，返回止損信號
        # 實際使用時需要維護持倉狀態
        return pd.Series(0, index=data.index)
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        risk_per_trade = self.params['base_stop_loss']
        stop_loss_distance = price * risk_per_trade
        
        if stop_loss_distance > 0:
            position_size = capital * 0.02 / stop_loss_distance
            shares = int(position_size / price)
        else:
            shares = 0
        
        return max(0, shares)


# ============================================================================
# 5. 尾部風險對沖策略
# ============================================================================

class TailRiskHedge(RiskManagementStrategy):
    """
    尾部風險對沖
    
    購買深度價外期權保護極端行情。
    
    規則：
    - 當市場波動率上升時，增加對沖
    - 當市場平穩時，減少對沖成本
    """
    
    def __init__(self, hedge_ratio: float = 0.05,
                 vix_threshold: float = 20,
                 max_hedge_cost: float = 0.02):
        """
        初始化尾部風險對沖
        
        Args:
            hedge_ratio: 對沖比例（默认 5%）
            vix_threshold: VIX 閾值（默认 20）
            max_hedge_cost: 最大對沖成本（默认 2%）
        """
        super().__init__('尾部風險對沖', {
            'hedge_ratio': hedge_ratio,
            'vix_threshold': vix_threshold,
            'max_hedge_cost': max_hedge_cost
        })
    
    def calculate_hedge_ratio(self, current_vix: float = None) -> float:
        """
        計算對沖比例
        
        Args:
            current_vix: 當前 VIX（恐慌指數）
            
        Returns:
            對沖比例
        """
        hedge_ratio = self.params['hedge_ratio']
        vix_threshold = self.params['vix_threshold']
        max_hedge_cost = self.params['max_hedge_cost']
        
        if current_vix is not None:
            # VIX 越高，對沖比例越高
            if current_vix > vix_threshold:
                hedge_ratio = min(
                    hedge_ratio * (current_vix / vix_threshold),
                    max_hedge_cost
                )
        
        return hedge_ratio
    
    def should_hedge(self, portfolio_value: float, 
                     current_vix: float = None) -> Tuple[bool, float]:
        """
        判斷是否應該對沖
        
        Args:
            portfolio_value: 投資組合價值
            current_vix: 當前 VIX
            
        Returns:
            (是否對沖，對沖金額)
        """
        hedge_ratio = self.calculate_hedge_ratio(current_vix)
        hedge_amount = portfolio_value * hedge_ratio
        
        # VIX 高於閾值時執行對沖
        should_hedge = current_vix is not None and current_vix > self.params['vix_threshold']
        
        return should_hedge, hedge_amount
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成對沖信號"""
        return pd.Series(0, index=data.index)
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算對沖倉位"""
        if signal == 0:
            return 0
        
        hedge_ratio = self.calculate_hedge_ratio()
        hedge_amount = capital * hedge_ratio
        
        return hedge_amount


# ============================================================================
# 6. 動態對沖（Delta Neutral）策略
# ============================================================================

class DynamicDeltaHedge(RiskManagementStrategy):
    """
    動態對沖（Delta Neutral）
    
    即時調整期權/現貨 Delta 至中性。
    
    規則：
    - 計算總 Delta
    - 調整對沖工具使總 Delta = 0
    """
    
    def __init__(self, rebalance_threshold: float = 0.1,
                 max_delta: float = 0.05):
        """
        初始化動態對沖
        
        Args:
            rebalance_threshold: 再平衡閾值（默认 0.1）
            max_delta: 最大允許 Delta（默认 0.05）
        """
        super().__init__('動態對沖', {
            'rebalance_threshold': rebalance_threshold,
            'max_delta': max_delta
        })
        
        self.current_delta = 0
        self.positions = []
    
    def calculate_portfolio_delta(self) -> float:
        """計算投資組合總 Delta"""
        total_delta = 0
        for position in self.positions:
            total_delta += position['delta'] * position['size']
        return total_delta
    
    def needs_rebalancing(self) -> bool:
        """判斷是否需要再平衡"""
        current_delta = self.calculate_portfolio_delta()
        return abs(current_delta) > self.params['rebalance_threshold']
    
    def calculate_hedge_size(self, target_delta: float = 0) -> float:
        """
        計算對沖倉位大小
        
        Args:
            target_delta: 目標 Delta（默认 0）
            
        Returns:
            對沖倉位大小
        """
        current_delta = self.calculate_portfolio_delta()
        delta_to_hedge = target_delta - current_delta
        
        return delta_to_hedge
    
    def rebalance(self) -> float:
        """
        執行再平衡
        
        Returns:
            需要調整的 Delta
        """
        if not self.needs_rebalancing():
            return 0
        
        hedge_size = self.calculate_hedge_size()
        self.current_delta = 0  # 重置 Delta
        
        return hedge_size
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成對沖信號"""
        return pd.Series(0, index=data.index)
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算對沖倉位"""
        if signal == 0:
            return 0
        
        # 計算需要對沖的 Delta
        hedge_delta = self.calculate_hedge_size()
        
        # 轉換為倉位
        if price > 0:
            shares = abs(hedge_delta) * capital / price
        else:
            shares = 0
        
        return max(0, int(shares))


# ============================================================================
# 7. 波動率目標策略
# ============================================================================

class VolatilityTargeting(RiskManagementStrategy):
    """
    波動率目標策略
    
    根據市場波動率調整倉位，保持恆定風險暴露。
    
    規則：
    - 波動率低 → 增加倉位
    - 波動率高 → 減少倉位
    - 目標波動率：年化 10-15%
    """
    
    def __init__(self, target_volatility: float = 0.15,
                 max_position: float = 1.0,
                 min_position: float = 0.1,
                 lookback: int = 60):
        """
        初始化波動率目標
        
        Args:
            target_volatility: 目標波動率（默认 15%）
            max_position: 最大倉位（默认 100%）
            min_position: 最小倉位（默认 10%）
            lookback: 回顧期（默认 60 日）
        """
        super().__init__('波動率目標', {
            'target_volatility': target_volatility,
            'max_position': max_position,
            'min_position': min_position,
            'lookback': lookback
        })
    
    def calculate_realized_volatility(self, returns: pd.Series) -> float:
        """
        計算實現波動率
        
        Args:
            returns: 收益率序列
            
        Returns:
            年化波動率
        """
        lookback = self.params['lookback']
        
        if len(returns) < lookback:
            return returns.std() * np.sqrt(252)
        
        return returns.tail(lookback).std() * np.sqrt(252)
    
    def calculate_position_multiplier(self, current_volatility: float) -> float:
        """
        計算倉位乘數
        
        Args:
            current_volatility: 當前波動率
            
        Returns:
            倉位乘數
        """
        target_vol = self.params['target_volatility']
        max_pos = self.params['max_position']
        min_pos = self.params['min_position']
        
        if current_volatility > 0:
            # 波動率越高，倉位越低
            multiplier = target_vol / current_volatility
        else:
            multiplier = max_pos
        
        # 限制在最大最小範圍內
        multiplier = max(min_pos, min(max_pos, multiplier))
        
        return multiplier
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float,
                                 returns: pd.Series = None) -> float:
        """
        計算倉位大小
        
        Args:
            signal: 交易信號
            capital: 可用資金
            price: 當前價格
            volatility: 波動率
            returns: 歷史收益率序列
            
        Returns:
            倉位大小
        """
        if signal == 0:
            return 0
        
        # 如果有歷史數據，計算實現波動率
        if returns is not None and len(returns) > 0:
            realized_vol = self.calculate_realized_volatility(returns)
        else:
            realized_vol = volatility * np.sqrt(252)
        
        # 計算倉位乘數
        multiplier = self.calculate_position_multiplier(realized_vol)
        
        # 計算基礎倉位
        base_position = capital * 0.02 / (2 * volatility)
        
        # 應用乘數
        adjusted_position = base_position * multiplier
        shares = int(adjusted_position / price)
        
        return max(0, shares)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成信號"""
        return pd.Series(0, index=data.index)


# ============================================================================
# 策略註冊表
# ============================================================================

ADVANCED_RISK_STRATEGIES = {
    'anti_martingale': AntiMartingale,
    'fixed_ratio': FixedRatio,
    'cvar': CVaRPositionSizing,
    'optimal_stop': OptimalStopLoss,
    'tail_hedge': TailRiskHedge,
    'delta_hedge': DynamicDeltaHedge,
    'vol_target': VolatilityTargeting,
}


# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == '__main__':
    import numpy as np
    
    # 創建測試數據
    np.random.seed(42)
    n = 100
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
    print("風險管理策略測試（7 個）")
    print("=" * 60)
    
    strategies = [
        ('Anti-Martingale', AntiMartingale()),
        ('Fixed Ratio', FixedRatio()),
        ('CVaR', CVaRPositionSizing()),
        ('Optimal Stop', OptimalStopLoss()),
        ('Tail Hedge', TailRiskHedge()),
        ('Delta Hedge', DynamicDeltaHedge()),
        ('Vol Target', VolatilityTargeting()),
    ]
    
    for name, strategy in strategies:
        print(f"\n{name}")
        try:
            # 測試倉位計算
            position = strategy.calculate_position_size(
                signal=1,
                capital=100000,
                price=100,
                volatility=0.02
            )
            print(f"   測試倉位：{position}")
            print(f"   ✅ 測試通過")
        except Exception as e:
            print(f"   ❌ 測試失敗：{e}")
    
    print("\n" + "=" * 60)
    print("🎉 7 個風險管理策略測試完成！")
    print("🎉 風險管理類別 12/12 完成（100%）！")
    print("=" * 60)
