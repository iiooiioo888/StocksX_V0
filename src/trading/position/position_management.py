"""
仓位管理策略模块

功能：
- 金字塔加仓（Pyramiding）
- 马丁格尔策略（Martingale）
- 凯利公式（Kelly Criterion）
- 固定比例仓位
- 风险平价仓位

使用场景：
- 自动计算最优仓位
- 盈利后加仓策略
- 亏损后加倍策略
- 风险控制在合理范围
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class PositionInfo:
    """仓位信息"""
    symbol: str
    side: str  # buy/sell
    entry_price: float
    current_price: float
    amount: float
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    def __post_init__(self):
        """计算未实现盈亏"""
        if self.side == 'buy':
            self.unrealized_pnl = (self.current_price - self.entry_price) * self.amount
        else:
            self.unrealized_pnl = (self.entry_price - self.current_price) * self.amount
        
        self.unrealized_pnl_pct = self.unrealized_pnl / (self.entry_price * self.amount) if self.entry_price > 0 else 0


class PositionStrategy(ABC):
    """仓位策略基类"""
    
    @abstractmethod
    def calculate_position_size(
        self,
        capital: float,
        price: float,
        **kwargs
    ) -> float:
        """
        计算仓位大小
        
        Args:
            capital: 可用资金
            price: 当前价格
            **kwargs: 其他参数
        
        Returns:
            仓位数量
        """
        pass


class FixedFractionalPosition(PositionStrategy):
    """
    固定比例仓位策略
    
    每次使用固定比例的资金开仓
    
    示例：
    ```python
    strategy = FixedFractionalPosition(fraction=0.1)  # 每次 10%
    size = strategy.calculate_position_size(
        capital=100000,
        price=50000
    )
    # 结果：0.2 (价值$10,000 / $50,000)
    ```
    """
    
    def __init__(self, fraction: float = 0.1):
        """
        初始化
        
        Args:
            fraction: 仓位比例（0-1）
        """
        if not 0 < fraction <= 1:
            raise ValueError("仓位比例必须在 0-1 之间")
        
        self.fraction = fraction
    
    def calculate_position_size(
        self,
        capital: float,
        price: float,
        **kwargs
    ) -> float:
        """计算仓位大小"""
        position_value = capital * self.fraction
        return position_value / price if price > 0 else 0


class KellyCriterion(PositionStrategy):
    """
    凯利公式仓位策略
    
    根据胜率和盈亏比计算最优仓位比例
    
    公式：
    f* = (p * b - q) / b
    
    其中：
    - f*: 最优仓位比例
    - p: 胜率
    - b: 盈亏比（平均盈利/平均亏损）
    - q: 败率 (1-p)
    
    变体：
    - 全额凯利：f*
    - 半额凯利：f*/2（更保守）
    - 四分之一凯利：f*/4（最保守）
    
    示例：
    ```python
    kelly = KellyCriterion(
        win_rate=0.55,
        profit_loss_ratio=2.0,
        kelly_fraction=0.5  # 半额凯利
    )
    size = kelly.calculate_position_size(
        capital=100000,
        price=50000
    )
    ```
    """
    
    def __init__(
        self,
        win_rate: float,
        profit_loss_ratio: float,
        kelly_fraction: float = 0.5,
        max_position: float = 0.25
    ):
        """
        初始化
        
        Args:
            win_rate: 胜率（0-1）
            profit_loss_ratio: 盈亏比
            kelly_fraction: 凯利比例（1=全额，0.5=半额）
            max_position: 最大仓位比例
        """
        if not 0 < win_rate < 1:
            raise ValueError("胜率必须在 0-1 之间")
        
        if profit_loss_ratio <= 0:
            raise ValueError("盈亏比必须为正数")
        
        if not 0 < kelly_fraction <= 1:
            raise ValueError("凯利比例必须在 0-1 之间")
        
        self.win_rate = win_rate
        self.profit_loss_ratio = profit_loss_ratio
        self.kelly_fraction = kelly_fraction
        self.max_position = max_position
    
    def calculate_kelly_fraction(self) -> float:
        """计算凯利比例"""
        p = self.win_rate
        b = self.profit_loss_ratio
        q = 1 - p
        
        # 凯利公式
        kelly = (p * b - q) / b
        
        # 如果为负，表示不应该下注
        if kelly < 0:
            return 0.0
        
        # 应用凯利分数和上限
        adjusted_kelly = kelly * self.kelly_fraction
        return min(adjusted_kelly, self.max_position)
    
    def calculate_position_size(
        self,
        capital: float,
        price: float,
        **kwargs
    ) -> float:
        """计算仓位大小"""
        kelly_pct = self.calculate_kelly_fraction()
        position_value = capital * kelly_pct
        return position_value / price if price > 0 else 0
    
    def get_info(self) -> Dict[str, Any]:
        """获取凯利信息"""
        return {
            'win_rate': self.win_rate,
            'profit_loss_ratio': self.profit_loss_ratio,
            'raw_kelly': (self.win_rate * self.profit_loss_ratio - (1 - self.win_rate)) / self.profit_loss_ratio,
            'adjusted_kelly': self.calculate_kelly_fraction(),
            'max_position': self.max_position
        }


class PyramidingPosition(PositionStrategy):
    """
    金字塔加仓策略
    
    盈利后逐步加仓，每次加仓量递减
    
    规则：
    - 初始仓位：50%
    - 第一次加仓：30%（价格涨 5%）
    - 第二次加仓：20%（价格再涨 5%）
    - 止损统一设置在成本价上方
    
    示例：
    ```python
    pyramid = PyramidingPosition(
        initial_allocation=0.5,
        add_levels=[
            {'pct_change': 0.05, 'allocation': 0.3},
            {'pct_change': 0.10, 'allocation': 0.2},
        ]
    )
    ```
    """
    
    def __init__(
        self,
        initial_allocation: float = 0.5,
        add_levels: Optional[List[Dict[str, float]]] = None,
        max_total_allocation: float = 1.0
    ):
        """
        初始化
        
        Args:
            initial_allocation: 初始仓位比例
            add_levels: 加仓级别列表
                [{'pct_change': 0.05, 'allocation': 0.3}, ...]
            max_total_allocation: 最大总仓位比例
        """
        self.initial_allocation = initial_allocation
        self.add_levels = add_levels or [
            {'pct_change': 0.05, 'allocation': 0.3},
            {'pct_change': 0.10, 'allocation': 0.2},
            {'pct_change': 0.15, 'allocation': 0.1},
        ]
        self.max_total_allocation = max_total_allocation
    
    def calculate_position_size(
        self,
        capital: float,
        price: float,
        current_position: Optional[PositionInfo] = None,
        **kwargs
    ) -> float:
        """
        计算仓位大小
        
        Args:
            capital: 总资金
            price: 当前价格
            current_position: 当前持仓（可选）
        
        Returns:
            应该持有的总仓位数量
        """
        # 如果没有持仓，返回初始仓位
        if current_position is None:
            initial_value = capital * self.initial_allocation
            return initial_value / price if price > 0 else 0
        
        # 计算价格变化
        pct_change = current_position.unrealized_pnl_pct
        
        # 计算应该加仓的级别
        total_allocation = self.initial_allocation
        for level in self.add_levels:
            if pct_change >= level['pct_change']:
                total_allocation += level['allocation']
            else:
                break
        
        # 限制最大仓位
        total_allocation = min(total_allocation, self.max_total_allocation)
        
        # 计算目标仓位
        target_value = capital * total_allocation
        target_amount = target_value / price if price > 0 else 0
        
        return target_amount
    
    def get_add_levels(self) -> List[Dict[str, Any]]:
        """获取加仓级别"""
        return self.add_levels


class MartingalePosition(PositionStrategy):
    """
    马丁格尔策略
    
    亏损后加倍下注，试图一次性挽回所有损失
    
    变体：
    - 经典马丁：亏损后 2 倍加仓
    - 温和马丁：亏损后 1.5 倍加仓
    - 反马丁：盈利后加仓
    
    风险：
    - 连续亏损会导致仓位指数级增长
    - 可能爆仓
    
    示例：
    ```python
    martingale = MartingalePosition(
        base_amount=0.01,
        multiplier=2.0,
        max_consecutive_losses=5
    )
    ```
    """
    
    def __init__(
        self,
        base_amount: float,
        multiplier: float = 2.0,
        max_consecutive_losses: int = 5,
        max_position_pct: float = 0.5
    ):
        """
        初始化
        
        Args:
            base_amount: 基础仓位数量
            multiplier: 加倍倍数
            max_consecutive_losses: 最大连续亏损次数
            max_position_pct: 最大仓位比例
        """
        self.base_amount = base_amount
        self.multiplier = multiplier
        self.max_consecutive_losses = max_consecutive_losses
        self.max_position_pct = max_position_pct
    
    def calculate_position_size(
        self,
        capital: float,
        price: float,
        consecutive_losses: int = 0,
        **kwargs
    ) -> float:
        """
        计算仓位大小
        
        Args:
            capital: 总资金
            price: 当前价格
            consecutive_losses: 连续亏损次数
        
        Returns:
            仓位数量
        """
        # 限制最大连续亏损次数
        losses = min(consecutive_losses, self.max_consecutive_losses)
        
        # 计算马丁格尔仓位
        position_amount = self.base_amount * (self.multiplier ** losses)
        
        # 检查是否超过最大仓位比例
        position_value = position_amount * price
        max_value = capital * self.max_position_pct
        
        if position_value > max_value:
            logger.warning(f"马丁格尔仓位超过限制，调整为 {max_value}")
            position_amount = max_value / price if price > 0 else 0
        
        return position_amount
    
    def reset(self):
        """重置（盈利后）"""
        logger.info("马丁格尔策略重置")


class RiskParityPosition(PositionStrategy):
    """
    风险平价仓位策略
    
    每个资产贡献相同的风险
    
    理念：
    - 不是分配资金，而是分配风险
    - 低波动资产获得更高权重
    - 高波动资产获得更低权重
    
    示例：
    ```python
    risk_parity = RiskParityPosition()
    weights = risk_parity.calculate_weights(
        volatilities={'BTC': 0.6, 'ETH': 0.7, 'USDT': 0.01}
    )
    ```
    """
    
    def __init__(self, target_volatility: float = 0.15):
        """
        初始化
        
        Args:
            target_volatility: 目标组合波动率
        """
        self.target_volatility = target_volatility
    
    def calculate_weights(
        self,
        volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        计算风险平价权重
        
        Args:
            volatilities: 各资产波动率
        
        Returns:
            权重字典
        """
        # 计算逆波动率
        inverse_vol = {k: 1.0 / v for k, v in volatilities.items() if v > 0}
        
        # 归一化
        total = sum(inverse_vol.values())
        weights = {k: v / total for k, v in inverse_vol.items()}
        
        return weights
    
    def calculate_position_size(
        self,
        capital: float,
        price: float,
        volatility: float,
        total_volatility: float,
        **kwargs
    ) -> float:
        """
        计算单个资产的仓位大小
        
        Args:
            capital: 总资金
            price: 当前价格
            volatility: 该资产波动率
            total_volatility: 所有资产波动率总和
        """
        # 风险平价权重
        weight = (1.0 / volatility) / (1.0 / total_volatility)
        
        # 调整到目标波动率
        adjusted_weight = weight * (self.target_volatility / volatility)
        
        # 计算仓位
        position_value = capital * adjusted_weight
        return position_value / price if price > 0 else 0


class PositionManager:
    """
    仓位管理器
    
    统一管理多个策略的仓位计算
    """
    
    def __init__(self, total_capital: float):
        """
        初始化
        
        Args:
            total_capital: 总资金
        """
        self.total_capital = total_capital
        self.positions: Dict[str, PositionInfo] = {}
        self.strategy: Optional[PositionStrategy] = None
    
    def set_strategy(self, strategy: PositionStrategy):
        """设置仓位策略"""
        self.strategy = strategy
        logger.info(f"设置仓位策略：{strategy.__class__.__name__}")
    
    def add_position(self, position: PositionInfo):
        """添加持仓"""
        self.positions[position.symbol] = position
    
    def update_position(self, symbol: str, current_price: float):
        """更新持仓价格"""
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.current_price = current_price
            # 重新计算盈亏
            if pos.side == 'buy':
                pos.unrealized_pnl = (current_price - pos.entry_price) * pos.amount
            else:
                pos.unrealized_pnl = (pos.entry_price - current_price) * pos.amount
            pos.unrealized_pnl_pct = pos.unrealized_pnl / (pos.entry_price * pos.amount) if pos.entry_price > 0 else 0
    
    def calculate_new_position(
        self,
        symbol: str,
        price: float,
        **kwargs
    ) -> float:
        """
        计算新仓位
        
        Args:
            symbol: 交易对
            price: 当前价格
            **kwargs: 策略特定参数
        
        Returns:
            仓位数量
        """
        if not self.strategy:
            logger.warning("未设置仓位策略，使用固定比例 10%")
            self.strategy = FixedFractionalPosition(fraction=0.1)
        
        current_pos = self.positions.get(symbol)
        
        return self.strategy.calculate_position_size(
            capital=self.total_capital,
            price=price,
            current_position=current_pos,
            **kwargs
        )
    
    def get_total_exposure(self) -> float:
        """计算总风险暴露"""
        total_value = sum(
            pos.amount * pos.current_price
            for pos in self.positions.values()
        )
        return total_value / self.total_capital if self.total_capital > 0 else 0
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取组合摘要"""
        total_value = sum(
            pos.amount * pos.current_price
            for pos in self.positions.values()
        )
        total_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_pnl_pct = total_pnl / self.total_capital if self.total_capital > 0 else 0
        
        return {
            'total_capital': self.total_capital,
            'total_value': total_value,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'exposure': total_value / self.total_capital if self.total_capital > 0 else 0,
            'position_count': len(self.positions),
            'positions': [
                {
                    'symbol': pos.symbol,
                    'side': pos.side,
                    'amount': pos.amount,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'unrealized_pnl_pct': pos.unrealized_pnl_pct,
                }
                for pos in self.positions.values()
            ]
        }


# 测试
if __name__ == "__main__":
    print("测试仓位管理策略...\n")
    
    # 1. 固定比例
    print("1. 固定比例仓位策略")
    fixed = FixedFractionalPosition(fraction=0.1)
    size = fixed.calculate_position_size(capital=100000, price=50000)
    print(f"   仓位：{size} (10% 资金)")
    
    # 2. 凯利公式
    print("\n2. 凯利公式")
    kelly = KellyCriterion(win_rate=0.55, profit_loss_ratio=2.0, kelly_fraction=0.5)
    info = kelly.get_info()
    print(f"   原始凯利：{info['raw_kelly']:.2%}")
    print(f"   调整后凯利：{info['adjusted_kelly']:.2%}")
    size = kelly.calculate_position_size(capital=100000, price=50000)
    print(f"   仓位：{size}")
    
    # 3. 金字塔加仓
    print("\n3. 金字塔加仓")
    pyramid = PyramidingPosition()
    print(f"   加仓级别：{pyramid.get_add_levels()}")
    
    # 模拟持仓
    position = PositionInfo(
        symbol="BTC/USDT",
        side="buy",
        entry_price=50000,
        current_price=52500,
        amount=1.0
    )
    size = pyramid.calculate_position_size(
        capital=100000,
        price=52500,
        current_position=position
    )
    print(f"   盈利 5% 时的目标仓位：{size}")
    
    # 4. 马丁格尔
    print("\n4. 马丁格尔策略")
    martingale = MartingalePosition(base_amount=0.01, multiplier=2.0)
    for losses in range(6):
        size = martingale.calculate_position_size(
            capital=100000,
            price=50000,
            consecutive_losses=losses
        )
        print(f"   连续亏损{losses}次：仓位={size}")
    
    # 5. 仓位管理器
    print("\n5. 仓位管理器")
    manager = PositionManager(total_capital=100000)
    manager.set_strategy(KellyCriterion(win_rate=0.55, profit_loss_ratio=2.0))
    
    # 添加持仓
    manager.add_position(PositionInfo(
        symbol="BTC/USDT",
        side="buy",
        entry_price=50000,
        current_price=52000,
        amount=0.5
    ))
    
    summary = manager.get_portfolio_summary()
    print(f"   总资金：${summary['total_capital']:,.0f}")
    print(f"   总价值：${summary['total_value']:,.0f}")
    print(f"   总盈亏：${summary['total_pnl']:,.0f} ({summary['total_pnl_pct']:.2%})")
    print(f"   风险暴露：{summary['exposure']:.2%}")
