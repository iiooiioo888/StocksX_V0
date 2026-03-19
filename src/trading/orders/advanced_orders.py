"""
高级订单类型模块

功能：
- 条件单（Conditional Orders）
- OCO 订单（One-Cancels-Other）
- 追踪止损（Trailing Stop）
- 时间条件单
- 指标条件单

使用场景：
- 自动止盈止损
- 突破交易
- 网格交易
- 定投策略
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    CONDITIONAL = "conditional"
    OCO = "oco"
    TRAILING_STOP = "trailing_stop"


class TriggerType(Enum):
    """触发条件类型"""
    PRICE_ABOVE = "price_above"       # 价格涨破
    PRICE_BELOW = "price_below"       # 价格跌破
    INDICATOR_CROSS = "indicator_cross"  # 指标交叉
    TIME_REACHED = "time_reached"     # 时间到达
    VOLUME_SPIKE = "volume_spike"     # 成交量异常
    PROFIT_REACHED = "profit_reached" # 盈利达到
    LOSS_REACHED = "loss_reached"     # 亏损达到


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"       # 等待中
    TRIGGERED = "triggered"   # 已触发
    SUBMITTED = "submitted"   # 已提交
    FILLED = "filled"         # 已成交
    CANCELLED = "cancelled"   # 已取消
    REJECTED = "rejected"     # 已拒绝
    EXPIRED = "expired"       # 已过期


@dataclass
class Order:
    """基础订单"""
    symbol: str
    side: str  # buy/sell
    type: OrderType
    amount: float
    price: Optional[float] = None  # 限价单价格
    stop_price: Optional[float] = None  # 止损/止盈触发价
    timestamp: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    filled_price: float = 0.0
    order_id: Optional[str] = None
    exchange: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'type': self.type.value,
            'amount': self.amount,
            'price': self.price,
            'stop_price': self.stop_price,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'filled_amount': self.filled_amount,
            'filled_price': self.filled_price,
            'order_id': self.order_id,
        }


@dataclass
class TriggerCondition:
    """触发条件"""
    type: TriggerType
    params: Dict[str, Any]
    
    def check(self, market_data: Dict[str, Any]) -> bool:
        """
        检查条件是否满足
        
        Args:
            market_data: 市场数据，包含：
                - current_price: 当前价格
                - indicator_value: 指标值
                - current_time: 当前时间
                - volume_ratio: 成交量比率
                - profit_pct: 盈利百分比
                - loss_pct: 亏损百分比
        
        Returns:
            是否触发
        """
        if self.type == TriggerType.PRICE_ABOVE:
            threshold = self.params.get('threshold', 0)
            return market_data.get('current_price', 0) > threshold
        
        elif self.type == TriggerType.PRICE_BELOW:
            threshold = self.params.get('threshold', 0)
            return market_data.get('current_price', 0) < threshold
        
        elif self.type == TriggerType.INDICATOR_CROSS:
            indicator = self.params.get('indicator', '')
            cross_type = self.params.get('cross_type', 'above')  # above/below
            threshold = self.params.get('threshold', 0)
            
            current_value = market_data.get(f'indicator_{indicator}', 0)
            
            if cross_type == 'above':
                return current_value > threshold
            else:
                return current_value < threshold
        
        elif self.type == TriggerType.TIME_REACHED:
            target_time = self.params.get('target_time')
            if isinstance(target_time, str):
                target_time = datetime.fromisoformat(target_time)
            return datetime.now() >= target_time
        
        elif self.type == TriggerType.VOLUME_SPIKE:
            threshold = self.params.get('threshold', 2.0)  # 默认 2 倍
            return market_data.get('volume_ratio', 0) > threshold
        
        elif self.type == TriggerType.PROFIT_REACHED:
            threshold = self.params.get('threshold', 0.05)  # 默认 5%
            return market_data.get('profit_pct', 0) >= threshold
        
        elif self.type == TriggerType.LOSS_REACHED:
            threshold = self.params.get('threshold', -0.05)  # 默认 -5%
            return market_data.get('loss_pct', 0) <= threshold
        
        return False


class ConditionalOrder:
    """
    条件单
    
    当触发条件满足时自动下单
    
    使用场景：
    - 突破交易：价格涨破阻力位时买入
    - 止损：价格跌破支撑位时卖出
    - 指标交易：RSI 超卖时买入
    - 定时交易：每天固定时间执行
    """
    
    def __init__(
        self,
        symbol: str,
        side: str,
        amount: float,
        trigger_condition: TriggerCondition,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        expiry: Optional[datetime] = None,
        quantity: Optional[float] = None,
        note: str = ""
    ):
        """
        初始化条件单
        
        Args:
            symbol: 交易对
            side: 买入/卖出
            amount: 数量
            trigger_condition: 触发条件
            order_type: 订单类型
            limit_price: 限价（如果是限价单）
            expiry: 过期时间
            quantity: 仓位大小（可选）
            note: 备注
        """
        self.symbol = symbol
        self.side = side
        self.amount = amount
        self.trigger_condition = trigger_condition
        self.order_type = order_type
        self.limit_price = limit_price
        self.expiry = expiry
        self.quantity = quantity
        self.note = note
        
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.triggered_at: Optional[datetime] = None
        self.order: Optional[Order] = None
        
        # 回调函数
        self.on_trigger: Optional[Callable] = None
        self.on_fill: Optional[Callable] = None
    
    def check_and_trigger(
        self,
        market_data: Dict[str, Any],
        submit_order_func: Optional[Callable] = None
    ) -> bool:
        """
        检查条件并触发
        
        Args:
            market_data: 市场数据
            submit_order_func: 提交订单的函数
        
        Returns:
            是否触发
        """
        # 检查是否过期
        if self.expiry and datetime.now() > self.expiry:
            self.status = OrderStatus.EXPIRED
            logger.info(f"条件单已过期：{self.symbol}")
            return False
        
        # 检查触发条件
        if self.trigger_condition.check(market_data):
            logger.info(f"条件单触发：{self.symbol}, 条件={self.trigger_condition.type.value}")
            
            self.status = OrderStatus.TRIGGERED
            self.triggered_at = datetime.now()
            
            # 创建实际订单
            order = Order(
                symbol=self.symbol,
                side=self.side,
                type=self.order_type,
                self.amount,
                price=self.limit_price
            )
            
            self.order = order
            
            # 提交订单
            if submit_order_func:
                try:
                    submit_order_func(order)
                    order.status = OrderStatus.SUBMITTED
                    logger.info(f"条件单已提交：{order.order_id}")
                except Exception as e:
                    logger.error(f"条件单提交失败：{e}")
                    order.status = OrderStatus.REJECTED
            
            # 触发回调
            if self.on_trigger:
                self.on_trigger(self, order)
            
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'amount': self.amount,
            'trigger_type': self.trigger_condition.type.value,
            'trigger_params': self.trigger_condition.params,
            'order_type': self.order_type.value,
            'limit_price': self.limit_price,
            'expiry': self.expiry.isoformat() if self.expiry else None,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'note': self.note,
        }


class OCOOrder:
    """
    OCO 订单（One-Cancels-Other）
    
    两个订单，一个成交则另一个自动取消
    
    典型用法：
    - 止盈 + 止损同时设置
    - 突破交易（向上/向下突破）
    
    示例：
    ```python
    # 设置止盈止损
    oco = OCOOrder(
        symbol="BTC/USDT",
        side="sell",
        amount=0.1,
        take_profit_price=70000,  # 止盈价
        stop_loss_price=60000,     # 止损价
        take_profit_type=OrderType.LIMIT,
        stop_loss_type=OrderType.STOP_LOSS
    )
    ```
    """
    
    def __init__(
        self,
        symbol: str,
        side: str,
        amount: float,
        take_profit_price: float,
        stop_loss_price: float,
        take_profit_type: OrderType = OrderType.LIMIT,
        stop_loss_type: OrderType = OrderType.STOP_LOSS,
        take_profit_limit: Optional[float] = None,
        stop_loss_limit: Optional[float] = None,
        expiry: Optional[datetime] = None
    ):
        """
        初始化 OCO 订单
        
        Args:
            symbol: 交易对
            side: 买入/卖出
            amount: 数量
            take_profit_price: 止盈价格
            stop_loss_price: 止损价格
            take_profit_type: 止盈订单类型
            stop_loss_type: 止损订单类型
            take_profit_limit: 止盈限价（如果是限价单）
            stop_loss_limit: 止损限价
            expiry: 过期时间
        """
        self.symbol = symbol
        self.side = side
        self.amount = amount
        self.take_profit_price = take_profit_price
        self.stop_loss_price = stop_loss_price
        self.take_profit_type = take_profit_type
        self.stop_loss_type = stop_loss_type
        self.take_profit_limit = take_profit_limit
        self.stop_loss_limit = stop_loss_limit
        self.expiry = expiry
        
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        
        # 两个子订单
        self.take_profit_order: Optional[Order] = None
        self.stop_loss_order: Optional[Order] = None
        
        # 已成交的订单
        self.filled_order: Optional[Order] = None
        
        # 回调
        self.on_fill: Optional[Callable] = None
    
    def create_orders(self) -> tuple:
        """创建两个子订单"""
        # 止盈订单
        self.take_profit_order = Order(
            symbol=self.symbol,
            side=self.side,
            type=self.take_profit_type,
            amount=self.amount,
            price=self.take_profit_limit or self.take_profit_price
        )
        
        # 止损订单
        self.stop_loss_order = Order(
            symbol=self.symbol,
            side=self.side,
            type=self.stop_loss_type,
            amount=self.amount,
            stop_price=self.stop_loss_price,
            price=self.stop_loss_limit
        )
        
        return self.take_profit_order, self.stop_loss_order
    
    def check_and_fill(
        self,
        market_data: Dict[str, Any],
        submit_order_func: Optional[Callable] = None
    ) -> Optional[Order]:
        """
        检查是否有订单成交
        
        Args:
            market_data: 市场数据
            submit_order_func: 提交订单的函数
        
        Returns:
            成交的订单，如果没有则为 None
        """
        if self.status != OrderStatus.PENDING:
            return None
        
        # 检查是否过期
        if self.expiry and datetime.now() > self.expiry:
            self.status = OrderStatus.EXPIRED
            logger.info(f"OCO 订单已过期：{self.symbol}")
            return None
        
        current_price = market_data.get('current_price', 0)
        
        # 检查止盈
        if self.side == "sell" and current_price >= self.take_profit_price:
            return self._fill_order(self.take_profit_order, submit_order_func)
        elif self.side == "buy" and current_price <= self.take_profit_price:
            return self._fill_order(self.take_profit_order, submit_order_func)
        
        # 检查止损
        if self.side == "sell" and current_price <= self.stop_loss_price:
            return self._fill_order(self.stop_loss_order, submit_order_func)
        elif self.side == "buy" and current_price >= self.stop_loss_price:
            return self._fill_order(self.stop_loss_order, submit_order_func)
        
        return None
    
    def _fill_order(
        self,
        order: Order,
        submit_order_func: Optional[Callable] = None
    ) -> Order:
        """成交订单，取消另一个"""
        logger.info(f"OCO 订单成交：{order.type.value} @ {order.price}")
        
        self.filled_order = order
        self.status = OrderStatus.FILLED
        
        # 取消另一个订单
        other_order = (
            self.stop_loss_order 
            if order == self.take_profit_order 
            else self.take_profit_order
        )
        if other_order:
            other_order.status = OrderStatus.CANCELLED
            logger.info(f"OCO 取消订单：{other_order.type.value}")
        
        # 提交订单
        if submit_order_func:
            try:
                submit_order_func(order)
                order.status = OrderStatus.SUBMITTED
            except Exception as e:
                logger.error(f"OCO 订单提交失败：{e}")
                order.status = OrderStatus.REJECTED
        
        # 回调
        if self.on_fill:
            self.on_fill(self, order)
        
        return order
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'amount': self.amount,
            'take_profit_price': self.take_profit_price,
            'stop_loss_price': self.stop_loss_price,
            'take_profit_type': self.take_profit_type.value,
            'stop_loss_type': self.stop_loss_type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'filled_order': self.filled_order.to_dict() if self.filled_order else None,
        }


class TrailingStop:
    """
    追踪止损
    
    止损价随市场价格移动，锁定盈利
    
    使用场景：
    - 趋势跟踪：让利润奔跑
    - 保护盈利：价格回调时自动止损
    
    示例：
    ```python
    # 设置 5% 追踪止损
    trailing = TrailingStop(
        symbol="BTC/USDT",
        side="sell",
        amount=0.1,
        trail_percent=0.05,  # 5%
        initial_price=65000
    )
    ```
    """
    
    def __init__(
        self,
        symbol: str,
        side: str,
        amount: float,
        trail_percent: float,
        trail_amount: Optional[float] = None,
        initial_price: Optional[float] = None,
        min_trigger_price: Optional[float] = None,
        expiry: Optional[datetime] = None
    ):
        """
        初始化追踪止损
        
        Args:
            symbol: 交易对
            side: 买入/卖出
            amount: 数量
            trail_percent: 追踪百分比（如 0.05 表示 5%）
            trail_amount: 追踪固定金额（与 trail_percent 二选一）
            initial_price: 初始价格
            min_trigger_price: 最低触发价格
            expiry: 过期时间
        """
        self.symbol = symbol
        self.side = side
        self.amount = amount
        self.trail_percent = trail_percent
        self.trail_amount = trail_amount
        self.initial_price = initial_price
        self.min_trigger_price = min_trigger_price
        self.expiry = expiry
        
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        
        # 动态计算的止损价
        self.current_stop_price: Optional[float] = None
        self.highest_price: float = initial_price or 0
        self.lowest_price: float = initial_price or float('inf')
        
        # 回调
        self.on_stop: Optional[Callable] = None
    
    def update_stop_price(self, current_price: float) -> Optional[float]:
        """
        根据当前价格更新止损价
        
        Args:
            current_price: 当前市场价格
        
        Returns:
            更新后的止损价
        """
        if self.side == "sell":  # 多头持仓
            # 更新最高价
            if current_price > self.highest_price:
                self.highest_price = current_price
            
            # 计算止损价
            if self.trail_amount:
                self.current_stop_price = self.highest_price - self.trail_amount
            else:
                self.current_stop_price = self.highest_price * (1 - self.trail_percent)
            
            # 确保不低于最低触发价
            if self.min_trigger_price and self.current_stop_price < self.min_trigger_price:
                self.current_stop_price = self.min_trigger_price
        
        else:  # 空头持仓
            # 更新最低价
            if current_price < self.lowest_price:
                self.lowest_price = current_price
            
            # 计算止损价
            if self.trail_amount:
                self.current_stop_price = self.lowest_price + self.trail_amount
            else:
                self.current_stop_price = self.lowest_price * (1 + self.trail_percent)
            
            # 确保不高于最高触发价
            if self.min_trigger_price and self.current_stop_price > self.min_trigger_price:
                self.current_stop_price = self.min_trigger_price
        
        return self.current_stop_price
    
    def check_and_trigger(
        self,
        current_price: float,
        submit_order_func: Optional[Callable] = None
    ) -> bool:
        """
        检查是否触发止损
        
        Args:
            current_price: 当前价格
            submit_order_func: 提交订单的函数
        
        Returns:
            是否触发
        """
        if self.status != OrderStatus.PENDING:
            return False
        
        # 检查是否过期
        if self.expiry and datetime.now() > self.expiry:
            self.status = OrderStatus.EXPIRED
            logger.info(f"追踪止损已过期：{self.symbol}")
            return False
        
        # 更新止损价
        self.update_stop_price(current_price)
        
        # 检查是否触发
        triggered = False
        if self.side == "sell" and current_price <= self.current_stop_price:
            triggered = True
        elif self.side == "buy" and current_price >= self.current_stop_price:
            triggered = True
        
        if triggered:
            logger.info(
                f"追踪止损触发：{self.symbol}, "
                f"价格={current_price}, 止损价={self.current_stop_price}, "
                f"最高价={self.highest_price}"
            )
            
            self.status = OrderStatus.TRIGGERED
            
            # 创建市价单
            order = Order(
                symbol=self.symbol,
                side=self.side,
                type=OrderType.MARKET,
                amount=self.amount
            )
            
            # 提交订单
            if submit_order_func:
                try:
                    submit_order_func(order)
                    order.status = OrderStatus.SUBMITTED
                    logger.info(f"追踪止损订单已提交：{order.order_id}")
                except Exception as e:
                    logger.error(f"追踪止损订单提交失败：{e}")
                    order.status = OrderStatus.REJECTED
            
            # 回调
            if self.on_stop:
                self.on_stop(self, order, self.highest_price)
            
            return True
        
        return False
    
    def get_info(self) -> Dict[str, Any]:
        """获取追踪止损信息"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'trail_percent': self.trail_percent,
            'current_stop_price': self.current_stop_price,
            'highest_price': self.highest_price,
            'lowest_price': self.lowest_price,
            'profit_locked': (
                (self.highest_price - self.initial_price) / self.initial_price
                if self.initial_price and self.highest_price > self.initial_price
                else 0
            ),
            'status': self.status.value,
        }


# 订单管理器
class OrderManager:
    """
    订单管理器
    
    管理所有高级订单的生命周期
    """
    
    def __init__(self):
        """初始化订单管理器"""
        self.conditional_orders: List[ConditionalOrder] = []
        self.oco_orders: List[OCOOrder] = []
        self.trailing_stops: List[TrailingStop] = []
        
        # 提交订单的函数
        self.submit_order_func: Optional[Callable] = None
    
    def set_submit_order_func(self, func: Callable):
        """设置提交订单的函数"""
        self.submit_order_func = func
    
    def add_conditional_order(self, order: ConditionalOrder):
        """添加条件单"""
        self.conditional_orders.append(order)
        logger.info(f"添加条件单：{order.symbol}")
    
    def add_oco_order(self, order: OCOOrder):
        """添加 OCO 订单"""
        order.create_orders()
        self.oco_orders.append(order)
        logger.info(f"添加 OCO 订单：{order.symbol}")
    
    def add_trailing_stop(self, stop: TrailingStop):
        """添加追踪止损"""
        self.trailing_stops.append(stop)
        logger.info(f"添加追踪止损：{stop.symbol}")
    
    def check_all_orders(self, market_data: Dict[str, Any]):
        """
        检查所有订单
        
        Args:
            market_data: 市场数据
        """
        # 检查条件单
        for order in self.conditional_orders[:]:
            if order.status == OrderStatus.PENDING:
                order.check_and_trigger(market_data, self.submit_order_func)
        
        # 检查 OCO 订单
        for order in self.oco_orders[:]:
            if order.status == OrderStatus.PENDING:
                order.check_and_fill(market_data, self.submit_order_func)
        
        # 检查追踪止损
        current_price = market_data.get('current_price', 0)
        for stop in self.trailing_stops[:]:
            if stop.status == OrderStatus.PENDING:
                stop.check_and_trigger(current_price, self.submit_order_func)
    
    def get_active_orders(self) -> Dict[str, int]:
        """获取活跃订单数量"""
        return {
            'conditional': sum(1 for o in self.conditional_orders if o.status == OrderStatus.PENDING),
            'oco': sum(1 for o in self.oco_orders if o.status == OrderStatus.PENDING),
            'trailing_stop': sum(1 for s in self.trailing_stops if s.status == OrderStatus.PENDING),
        }


# 测试
if __name__ == "__main__":
    # 测试条件单
    print("测试条件单...")
    condition = TriggerCondition(
        type=TriggerType.PRICE_ABOVE,
        params={'threshold': 70000}
    )
    
    cond_order = ConditionalOrder(
        symbol="BTC/USDT",
        side="buy",
        amount=0.1,
        trigger_condition=condition
    )
    
    # 模拟市场数据
    market_data = {'current_price': 71000}
    triggered = cond_order.check_and_trigger(market_data)
    print(f"条件单触发：{triggered}")
    
    # 测试 OCO 订单
    print("\n测试 OCO 订单...")
    oco = OCOOrder(
        symbol="BTC/USDT",
        side="sell",
        amount=0.1,
        take_profit_price=70000,
        stop_loss_price=60000
    )
    
    market_data = {'current_price': 70500}
    filled = oco.check_and_fill(market_data)
    print(f"OCO 订单成交：{filled}")
    
    # 测试追踪止损
    print("\n测试追踪止损...")
    trailing = TrailingStop(
        symbol="BTC/USDT",
        side="sell",
        amount=0.1,
        trail_percent=0.05,
        initial_price=65000
    )
    
    # 模拟价格上涨
    for price in [65000, 68000, 70000, 72000, 69000]:
        trailing.update_stop_price(price)
        info = trailing.get_info()
        print(f"价格={price}, 止损价={info['current_stop_price']:.2f}, 最高价={info['highest_price']}")
