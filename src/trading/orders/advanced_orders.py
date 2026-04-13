"""
高级订单类型模块

功能：
- 条件单（Conditional Orders）
- OCO 订单（One-Cancels-Other）
- 追踪止损（Trailing Stop）
- 冰山订单（Iceberg Order）— 大单拆分隐藏真实数量
- TWAP 订单（Time-Weighted Average Price）— 时间加权分批执行
- 时间条件单
- 指标条件单

使用场景：
- 自动止盈止损
- 突破交易
- 网格交易
- 定投策略
- 大额订单隐蔽执行
- 降低市场冲击
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from collections.abc import Callable

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
    ICEBERG = "iceberg"
    TWAP = "twap"


class TriggerType(Enum):
    """触发条件类型"""

    PRICE_ABOVE = "price_above"  # 价格涨破
    PRICE_BELOW = "price_below"  # 价格跌破
    INDICATOR_CROSS = "indicator_cross"  # 指标交叉
    TIME_REACHED = "time_reached"  # 时间到达
    VOLUME_SPIKE = "volume_spike"  # 成交量异常
    PROFIT_REACHED = "profit_reached"  # 盈利达到
    LOSS_REACHED = "loss_reached"  # 亏损达到


class OrderStatus(Enum):
    """订单状态"""

    PENDING = "pending"  # 等待中
    TRIGGERED = "triggered"  # 已触发
    SUBMITTED = "submitted"  # 已提交
    FILLED = "filled"  # 已成交
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"  # 已过期


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

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "type": self.type.value,
            "amount": self.amount,
            "price": self.price,
            "stop_price": self.stop_price,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "filled_amount": self.filled_amount,
            "filled_price": self.filled_price,
            "order_id": self.order_id,
        }


@dataclass
class TriggerCondition:
    """触发条件"""

    type: TriggerType
    params: dict[str, Any]

    def check(self, market_data: dict[str, Any]) -> bool:
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
            threshold = self.params.get("threshold", 0)
            return market_data.get("current_price", 0) > threshold

        elif self.type == TriggerType.PRICE_BELOW:
            threshold = self.params.get("threshold", 0)
            return market_data.get("current_price", 0) < threshold

        elif self.type == TriggerType.INDICATOR_CROSS:
            indicator = self.params.get("indicator", "")
            cross_type = self.params.get("cross_type", "above")  # above/below
            threshold = self.params.get("threshold", 0)

            current_value = market_data.get(f"indicator_{indicator}", 0)

            if cross_type == "above":
                return current_value > threshold
            else:
                return current_value < threshold

        elif self.type == TriggerType.TIME_REACHED:
            target_time = self.params.get("target_time")
            if isinstance(target_time, str):
                target_time = datetime.fromisoformat(target_time)
            return datetime.now() >= target_time

        elif self.type == TriggerType.VOLUME_SPIKE:
            threshold = self.params.get("threshold", 2.0)  # 默认 2 倍
            return market_data.get("volume_ratio", 0) > threshold

        elif self.type == TriggerType.PROFIT_REACHED:
            threshold = self.params.get("threshold", 0.05)  # 默认 5%
            return market_data.get("profit_pct", 0) >= threshold

        elif self.type == TriggerType.LOSS_REACHED:
            threshold = self.params.get("threshold", -0.05)  # 默认 -5%
            return market_data.get("loss_pct", 0) <= threshold

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
        note: str = "",
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

    def check_and_trigger(self, market_data: dict[str, Any], submit_order_func: Optional[Callable] = None) -> bool:
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
                symbol=self.symbol, side=self.side, type=self.order_type, amount=self.amount, price=self.limit_price
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

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "amount": self.amount,
            "trigger_type": self.trigger_condition.type.value,
            "trigger_params": self.trigger_condition.params,
            "order_type": self.order_type.value,
            "limit_price": self.limit_price,
            "expiry": self.expiry.isoformat() if self.expiry else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "note": self.note,
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
        expiry: Optional[datetime] = None,
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
            price=self.take_profit_limit or self.take_profit_price,
        )

        # 止损订单
        self.stop_loss_order = Order(
            symbol=self.symbol,
            side=self.side,
            type=self.stop_loss_type,
            amount=self.amount,
            stop_price=self.stop_loss_price,
            price=self.stop_loss_limit,
        )

        return self.take_profit_order, self.stop_loss_order

    def check_and_fill(
        self, market_data: dict[str, Any], submit_order_func: Optional[Callable] = None
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

        current_price = market_data.get("current_price", 0)

        # 检查止盈
        if (self.side == "sell" and current_price >= self.take_profit_price) or (
            self.side == "buy" and current_price <= self.take_profit_price
        ):
            return self._fill_order(self.take_profit_order, submit_order_func)

        # 检查止损
        if (self.side == "sell" and current_price <= self.stop_loss_price) or (
            self.side == "buy" and current_price >= self.stop_loss_price
        ):
            return self._fill_order(self.stop_loss_order, submit_order_func)

        return None

    def _fill_order(self, order: Order, submit_order_func: Optional[Callable] = None) -> Order:
        """成交订单，取消另一个"""
        logger.info(f"OCO 订单成交：{order.type.value} @ {order.price}")

        self.filled_order = order
        self.status = OrderStatus.FILLED

        # 取消另一个订单
        other_order = self.stop_loss_order if order == self.take_profit_order else self.take_profit_order
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

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "amount": self.amount,
            "take_profit_price": self.take_profit_price,
            "stop_loss_price": self.stop_loss_price,
            "take_profit_type": self.take_profit_type.value,
            "stop_loss_type": self.stop_loss_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "filled_order": self.filled_order.to_dict() if self.filled_order else None,
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
        expiry: Optional[datetime] = None,
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
        self.lowest_price: float = initial_price or float("inf")

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

    def check_and_trigger(self, current_price: float, submit_order_func: Optional[Callable] = None) -> bool:
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
        if (self.side == "sell" and current_price <= self.current_stop_price) or (
            self.side == "buy" and current_price >= self.current_stop_price
        ):
            triggered = True

        if triggered:
            logger.info(
                f"追踪止损触发：{self.symbol}, "
                f"价格={current_price}, 止损价={self.current_stop_price}, "
                f"最高价={self.highest_price}"
            )

            self.status = OrderStatus.TRIGGERED

            # 创建市价单
            order = Order(symbol=self.symbol, side=self.side, type=OrderType.MARKET, amount=self.amount)

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

    def get_info(self) -> dict[str, Any]:
        """获取追踪止损信息"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "trail_percent": self.trail_percent,
            "current_stop_price": self.current_stop_price,
            "highest_price": self.highest_price,
            "lowest_price": self.lowest_price,
            "profit_locked": (
                (self.highest_price - self.initial_price) / self.initial_price
                if self.initial_price and self.highest_price > self.initial_price
                else 0
            ),
            "status": self.status.value,
        }


class IcebergOrder:
    """
    冰山订单（Iceberg Order）

    将大额订单拆分为多个可见的小单，隐藏真实交易意图。
    只有"冰山一角"暴露在订单簿上，其余部分隐藏。

    核心参数：
    - total_amount: 总数量
    - visible_amount: 每次暴露的数量（冰山一角）
    - price_limit: 限价（可选，市价则为 None）
    - refresh_interval: 每批之间的最小间隔（秒）
    - price_tolerance: 价格偏离容忍度，超过则暂停等待

    使用场景：
    - 机构大额建仓/减仓
    - 避免滑点和市场冲击
    - 隐藏真实仓位意图

    示例：
    ```python
    iceberg = IcebergOrder(
        symbol="BTC/USDT",
        side="buy",
        total_amount=10.0,      # 总共买 10 BTC
        visible_amount=0.5,     # 每次只挂 0.5 BTC
        price_limit=68000,      # 限价 68000
        refresh_interval=30,    # 每 30 秒刷新一批
    )
    ```
    """

    def __init__(
        self,
        symbol: str,
        side: str,
        total_amount: float,
        visible_amount: float,
        price_limit: Optional[float] = None,
        refresh_interval: float = 10.0,
        price_tolerance: float = 0.005,
        max_slippage: float = 0.002,
        randomize_timing: bool = True,
        expiry: Optional[datetime] = None,
    ):
        """
        初始化冰山订单

        Args:
            symbol: 交易对
            side: 买入/卖出
            total_amount: 总交易数量
            visible_amount: 每批暴露数量
            price_limit: 限价（None = 市价）
            refresh_interval: 刷新间隔（秒）
            price_tolerance: 价格偏离容忍度（如 0.005 = 0.5%）
            max_slippage: 最大滑点容忍度
            randomize_timing: 是否随机化下单时间（反侦测）
            expiry: 过期时间
        """
        if visible_amount <= 0:
            raise ValueError("visible_amount 必须大于 0")
        if visible_amount >= total_amount:
            raise ValueError("visible_amount 应小于 total_amount，否则不需要冰山订单")

        self.symbol = symbol
        self.side = side
        self.total_amount = total_amount
        self.visible_amount = visible_amount
        self.price_limit = price_limit
        self.refresh_interval = refresh_interval
        self.price_tolerance = price_tolerance
        self.max_slippage = max_slippage
        self.randomize_timing = randomize_timing
        self.expiry = expiry

        # 状态追踪
        self.status = OrderStatus.PENDING
        self.filled_amount = 0.0
        self.remaining_amount = total_amount
        self.batches_sent = 0
        self.created_at = datetime.now()
        self.last_batch_at: Optional[datetime] = None

        # 已成交批次记录
        self.fills: list[dict[str, Any]] = []

        # 回调
        self.on_batch_fill: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None

    def _compute_batch_size(self) -> float:
        """计算当前批次大小（带随机抖动）"""
        base = min(self.visible_amount, self.remaining_amount)
        if self.randomize_timing:
            # ±20% 随机抖动，避免被模式识别
            jitter = random.uniform(0.8, 1.2)
            base = min(base * jitter, self.remaining_amount)
        return round(base, 8)

    def _next_delay(self) -> float:
        """计算下一批延迟（秒）"""
        delay = self.refresh_interval
        if self.randomize_timing:
            # ±30% 随机延迟
            delay *= random.uniform(0.7, 1.3)
        return delay

    def check_price_ok(self, current_price: float) -> bool:
        """检查价格是否在容忍范围内"""
        if self.price_limit is None:
            return True

        if self.side == "buy":
            return current_price <= self.price_limit * (1 + self.price_tolerance)
        else:
            return current_price >= self.price_limit * (1 - self.price_tolerance)

    def should_send_batch(self, current_price: float) -> bool:
        """判断是否应该发送下一批"""
        if self.status != OrderStatus.PENDING:
            return False

        # 检查是否过期
        if self.expiry and datetime.now() > self.expiry:
            self.status = OrderStatus.EXPIRED
            logger.info(f"冰山订单已过期：{self.symbol}")
            return False

        # 检查是否全部成交
        if self.remaining_amount <= 0:
            self.status = OrderStatus.FILLED
            logger.info(f"冰山订单全部成交：{self.symbol}, 共 {self.batches_sent} 批")
            if self.on_complete:
                self.on_complete(self)
            return False

        # 检查价格
        if not self.check_price_ok(current_price):
            logger.debug(f"冰山订单价格偏离：当前={current_price}, 限价={self.price_limit}")
            return False

        # 检查间隔
        if self.last_batch_at:
            elapsed = (datetime.now() - self.last_batch_at).total_seconds()
            if elapsed < self._next_delay():
                return False

        return True

    def send_batch(self, current_price: float, submit_order_func: Optional[Callable] = None) -> Optional[Order]:
        """
        发送下一批订单

        Args:
            current_price: 当前市场价格
            submit_order_func: 提交订单的函数

        Returns:
            生成的订单，如果条件不满足则为 None
        """
        if not self.should_send_batch(current_price):
            return None

        batch_size = self._compute_batch_size()
        if batch_size <= 0:
            return None

        # 创建订单
        order = Order(
            symbol=self.symbol,
            side=self.side,
            type=OrderType.LIMIT if self.price_limit else OrderType.MARKET,
            amount=batch_size,
            price=self.price_limit,
        )

        # 提交
        if submit_order_func:
            try:
                submit_order_func(order)
                order.status = OrderStatus.SUBMITTED
                logger.info(
                    f"冰山订单第 {self.batches_sent + 1} 批已提交："
                    f"{self.symbol} {batch_size} @ {self.price_limit or '市价'}"
                )
            except Exception as e:
                logger.error(f"冰山订单批次提交失败：{e}")
                order.status = OrderStatus.REJECTED
                return None

        # 更新状态
        self.batches_sent += 1
        self.last_batch_at = datetime.now()

        # 假设本批全部成交（实际应由回调更新）
        self.filled_amount += batch_size
        self.remaining_amount = self.total_amount - self.filled_amount

        self.fills.append(
            {
                "batch": self.batches_sent,
                "amount": batch_size,
                "price": current_price,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if self.on_batch_fill:
            self.on_batch_fill(self, order, self.batches_sent)

        return order

    def get_progress(self) -> dict[str, Any]:
        """获取执行进度"""
        avg_price = 0.0
        if self.fills:
            total_cost = sum(f["amount"] * f["price"] for f in self.fills)
            avg_price = total_cost / self.filled_amount if self.filled_amount > 0 else 0

        return {
            "symbol": self.symbol,
            "side": self.side,
            "total_amount": self.total_amount,
            "filled_amount": self.filled_amount,
            "remaining_amount": self.remaining_amount,
            "progress_pct": (self.filled_amount / self.total_amount * 100) if self.total_amount > 0 else 0,
            "batches_sent": self.batches_sent,
            "avg_fill_price": avg_price,
            "status": self.status.value,
        }

    def cancel(self):
        """取消冰山订单"""
        self.status = OrderStatus.CANCELLED
        logger.info(
            f"冰山订单已取消：{self.symbol}, 已完成 {self.filled_amount}/{self.total_amount} ({self.batches_sent} 批)"
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            **self.get_progress(),
            "visible_amount": self.visible_amount,
            "price_limit": self.price_limit,
            "refresh_interval": self.refresh_interval,
            "created_at": self.created_at.isoformat(),
            "fills": self.fills,
        }


class TWAPOrder:
    """
    TWAP 订单（Time-Weighted Average Price）

    在指定时间段内均匀拆分订单，按固定时间间隔执行，
    目标是以接近时间段内 TWAP 的价格完成交易。

    与 Iceberg 的区别：
    - Iceberg: 按固定数量拆分，关注隐藏意图
    - TWAP: 按时间均匀拆分，关注成交均价

    核心参数：
    - duration: 总执行时长（秒）
    - num_slices: 切片数量
    - total_amount: 总数量

    使用场景：
    - 大额订单降低市场冲击
    - 被动执行，追求均价
    - 基准交易（Benchmark execution）

    示例：
    ```python
    twap = TWAPOrder(
        symbol="BTC/USDT",
        side="buy",
        total_amount=5.0,
        duration=3600,      # 1 小时内完成
        num_slices=12,      # 分 12 批，每 5 分钟一批
    )
    ```
    """

    def __init__(
        self,
        symbol: str,
        side: str,
        total_amount: float,
        duration: float,
        num_slices: int,
        price_limit: Optional[float] = None,
        start_time: Optional[datetime] = None,
        max_participation_rate: float = 0.1,
        urgency: str = "normal",  # low / normal / high
        randomize_timing: bool = True,
        expiry: Optional[datetime] = None,
    ):
        """
        初始化 TWAP 订单

        Args:
            symbol: 交易对
            side: 买入/卖出
            total_amount: 总交易数量
            duration: 执行时长（秒）
            num_slices: 切片数量
            price_limit: 限价（None = 市价）
            start_time: 开始时间（None = 立即开始）
            max_participation_rate: 最大参与率（避免过度影响市场）
            urgency: 紧急程度 low/normal/high
            randomize_timing: 是否随机化执行时间
            expiry: 过期时间
        """
        if num_slices < 1:
            raise ValueError("num_slices 必须 >= 1")
        if duration <= 0:
            raise ValueError("duration 必须大于 0")

        self.symbol = symbol
        self.side = side
        self.total_amount = total_amount
        self.duration = duration
        self.num_slices = num_slices
        self.price_limit = price_limit
        self.start_time = start_time or datetime.now()
        self.max_participation_rate = max_participation_rate
        self.urgency = urgency
        self.randomize_timing = randomize_timing
        self.expiry = expiry

        # 每片数量
        self.slice_amount = total_amount / num_slices
        # 每片间隔（秒）
        self.slice_interval = duration / num_slices

        # 根据紧急程度调整
        if urgency == "high":
            self.slice_interval *= 0.7  # 加速 30%
        elif urgency == "low":
            self.slice_interval *= 1.3  # 减速 30%

        # 状态追踪
        self.status = OrderStatus.PENDING
        self.filled_amount = 0.0
        self.remaining_amount = total_amount
        self.slices_sent = 0
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # 执行记录
        self.fills: list[dict[str, Any]] = []
        self.twap_price: float = 0.0  # 已实现 TWAP

        # 回调
        self.on_slice_fill: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None

    def _compute_slice_size(self) -> float:
        """计算当前切片大小"""
        # 剩余切片平均分配
        remaining_slices = self.num_slices - self.slices_sent
        if remaining_slices <= 0:
            return 0.0

        base = self.remaining_amount / remaining_slices

        if self.randomize_timing:
            # ±15% 随机抖动
            jitter = random.uniform(0.85, 1.15)
            base = min(base * jitter, self.remaining_amount)

        return round(base, 8)

    def _next_delay(self) -> float:
        """计算下一切片延迟"""
        delay = self.slice_interval
        if self.randomize_timing:
            delay *= random.uniform(0.8, 1.2)
        return delay

    def _update_twap(self, fill_price: float, fill_amount: float):
        """更新已实现 TWAP 价格"""
        if self.filled_amount + fill_amount <= 0:
            return
        self.twap_price = (self.twap_price * self.filled_amount + fill_price * fill_amount) / (
            self.filled_amount + fill_amount
        )

    def get_schedule(self) -> list[dict[str, Any]]:
        """获取执行计划（时间表）"""
        schedule = []
        current = self.start_time

        for i in range(self.num_slices):
            schedule.append(
                {
                    "slice": i + 1,
                    "scheduled_time": current.isoformat(),
                    "amount": self.slice_amount,
                    "cumulative_amount": self.slice_amount * (i + 1),
                }
            )
            current = current + timedelta(seconds=self.slice_interval)

        return schedule

    def should_send_slice(self, current_time: Optional[datetime] = None) -> bool:
        """判断是否应该发送下一切片"""
        if self.status != OrderStatus.PENDING:
            return False

        now = current_time or datetime.now()

        # 检查是否已开始
        if now < self.start_time:
            return False

        # 检查是否过期
        if self.expiry and now > self.expiry:
            self.status = OrderStatus.EXPIRED
            logger.info(f"TWAP 订单已过期：{self.symbol}")
            return False

        # 检查是否全部完成
        if self.remaining_amount <= 0 or self.slices_sent >= self.num_slices:
            self.status = OrderStatus.FILLED
            self.completed_at = now
            logger.info(f"TWAP 订单完成：{self.symbol}, TWAP 价格={self.twap_price:.2f}, 共 {self.slices_sent} 片")
            if self.on_complete:
                self.on_complete(self)
            return False

        # 检查时间间隔
        if self.started_at:
            elapsed = (now - self.started_at).total_seconds()
            expected_time = self.slices_sent * self.slice_interval
            if elapsed < expected_time:
                return False
        elif now < self.start_time:
            return False

        return True

    def send_slice(
        self,
        current_price: float,
        current_time: Optional[datetime] = None,
        submit_order_func: Optional[Callable] = None,
    ) -> Optional[Order]:
        """
        发送下一切片订单

        Args:
            current_price: 当前市场价格
            current_time: 当前时间
            submit_order_func: 提交订单的函数

        Returns:
            生成的订单，如果条件不满足则为 None
        """
        if not self.should_send_slice(current_time):
            return None

        if self.started_at is None:
            self.started_at = datetime.now()

        slice_size = self._compute_slice_size()
        if slice_size <= 0:
            return None

        # 创建订单
        order = Order(
            symbol=self.symbol,
            side=self.side,
            type=OrderType.LIMIT if self.price_limit else OrderType.MARKET,
            amount=slice_size,
            price=self.price_limit,
        )

        # 提交
        if submit_order_func:
            try:
                submit_order_func(order)
                order.status = OrderStatus.SUBMITTED
                logger.info(
                    f"TWAP 第 {self.slices_sent + 1}/{self.num_slices} 片已提交："
                    f"{self.symbol} {slice_size} @ {self.price_limit or '市价'}"
                )
            except Exception as e:
                logger.error(f"TWAP 切片提交失败：{e}")
                order.status = OrderStatus.REJECTED
                return None

        # 更新状态
        self.slices_sent += 1
        self.filled_amount += slice_size
        self.remaining_amount = self.total_amount - self.filled_amount
        self._update_twap(current_price, slice_size)

        self.fills.append(
            {
                "slice": self.slices_sent,
                "amount": slice_size,
                "price": current_price,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if self.on_slice_fill:
            self.on_slice_fill(self, order, self.slices_sent)

        return order

    def get_progress(self) -> dict[str, Any]:
        """获取执行进度"""
        elapsed = 0.0
        if self.started_at:
            elapsed = (datetime.now() - self.started_at).total_seconds()

        return {
            "symbol": self.symbol,
            "side": self.side,
            "total_amount": self.total_amount,
            "filled_amount": self.filled_amount,
            "remaining_amount": self.remaining_amount,
            "progress_pct": (self.filled_amount / self.total_amount * 100) if self.total_amount > 0 else 0,
            "slices_sent": self.slices_sent,
            "total_slices": self.num_slices,
            "twap_price": self.twap_price,
            "elapsed_seconds": elapsed,
            "duration_seconds": self.duration,
            "time_progress_pct": min(100, elapsed / self.duration * 100) if self.duration > 0 else 100,
            "status": self.status.value,
        }

    def cancel(self):
        """取消 TWAP 订单"""
        self.status = OrderStatus.CANCELLED
        logger.info(
            f"TWAP 订单已取消：{self.symbol}, "
            f"已完成 {self.filled_amount}/{self.total_amount} "
            f"({self.slices_sent}/{self.num_slices} 片), "
            f"TWAP={self.twap_price:.2f}"
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            **self.get_progress(),
            "slice_amount": self.slice_amount,
            "slice_interval": self.slice_interval,
            "price_limit": self.price_limit,
            "urgency": self.urgency,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "fills": self.fills,
        }


# 订单管理器
class OrderManager:
    """
    订单管理器

    管理所有高级订单的生命周期
    """

    def __init__(self):
        """初始化订单管理器"""
        self.conditional_orders: list[ConditionalOrder] = []
        self.oco_orders: list[OCOOrder] = []
        self.trailing_stops: list[TrailingStop] = []
        self.iceberg_orders: list[IcebergOrder] = []
        self.twap_orders: list[TWAPOrder] = []

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

    def add_iceberg_order(self, order: IcebergOrder):
        """添加冰山订单"""
        self.iceberg_orders.append(order)
        logger.info(f"添加冰山订单：{order.symbol}, 总量={order.total_amount}")

    def add_twap_order(self, order: TWAPOrder):
        """添加 TWAP 订单"""
        self.twap_orders.append(order)
        logger.info(f"添加 TWAP 订单：{order.symbol}, {order.num_slices} 片/{order.duration}s")

    def check_all_orders(self, market_data: dict[str, Any]):
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
        current_price = market_data.get("current_price", 0)
        for stop in self.trailing_stops[:]:
            if stop.status == OrderStatus.PENDING:
                stop.check_and_trigger(current_price, self.submit_order_func)

        # 检查冰山订单
        for iceberg in self.iceberg_orders[:]:
            if iceberg.status == OrderStatus.PENDING:
                iceberg.send_batch(current_price, self.submit_order_func)

        # 检查 TWAP 订单
        for twap in self.twap_orders[:]:
            if twap.status == OrderStatus.PENDING:
                twap.send_slice(current_price, submit_order_func=self.submit_order_func)

    def get_active_orders(self) -> dict[str, int]:
        """获取活跃订单数量"""
        return {
            "conditional": sum(1 for o in self.conditional_orders if o.status == OrderStatus.PENDING),
            "oco": sum(1 for o in self.oco_orders if o.status == OrderStatus.PENDING),
            "trailing_stop": sum(1 for s in self.trailing_stops if s.status == OrderStatus.PENDING),
            "iceberg": sum(1 for o in self.iceberg_orders if o.status == OrderStatus.PENDING),
            "twap": sum(1 for o in self.twap_orders if o.status == OrderStatus.PENDING),
        }


# 测试
if __name__ == "__main__":
    # 测试条件单
    print("测试条件单...")
    condition = TriggerCondition(type=TriggerType.PRICE_ABOVE, params={"threshold": 70000})

    cond_order = ConditionalOrder(symbol="BTC/USDT", side="buy", amount=0.1, trigger_condition=condition)

    # 模拟市场数据
    market_data = {"current_price": 71000}
    triggered = cond_order.check_and_trigger(market_data)
    print(f"条件单触发：{triggered}")

    # 测试 OCO 订单
    print("\n测试 OCO 订单...")
    oco = OCOOrder(symbol="BTC/USDT", side="sell", amount=0.1, take_profit_price=70000, stop_loss_price=60000)
    oco.create_orders()

    market_data = {"current_price": 70500}
    filled = oco.check_and_fill(market_data)
    print(f"OCO 订单成交：{filled}")

    # 测试追踪止损
    print("\n测试追踪止损...")
    trailing = TrailingStop(symbol="BTC/USDT", side="sell", amount=0.1, trail_percent=0.05, initial_price=65000)

    # 模拟价格上涨
    for price in [65000, 68000, 70000, 72000, 69000]:
        trailing.update_stop_price(price)
        info = trailing.get_info()
        print(f"价格={price}, 止损价={info['current_stop_price']:.2f}, 最高价={info['highest_price']}")

    # 测试冰山订单
    print("\n测试冰山订单...")
    iceberg = IcebergOrder(
        symbol="BTC/USDT",
        side="buy",
        total_amount=10.0,
        visible_amount=0.5,
        price_limit=68000,
        refresh_interval=1.0,
        randomize_timing=False,
    )

    # 模拟多次发送
    for i in range(5):
        order = iceberg.send_batch(67500)
        if order:
            print(f"  批次 {iceberg.batches_sent}: {order.amount} @ {order.price}")
        time.sleep(0.1)

    progress = iceberg.get_progress()
    print(f"  进度: {progress['filled_amount']}/{progress['total_amount']} ({progress['progress_pct']:.1f}%)")

    # 测试 TWAP 订单
    print("\n测试 TWAP 订单...")
    twap = TWAPOrder(
        symbol="BTC/USDT",
        side="buy",
        total_amount=5.0,
        duration=60.0,  # 60 秒内完成
        num_slices=6,  # 6 片
        randomize_timing=False,
    )

    schedule = twap.get_schedule()
    print(f"  执行计划: {len(schedule)} 片, 每片 {twap.slice_amount:.4f} BTC, 间隔 {twap.slice_interval:.1f}s")

    # 模拟执行
    for i in range(6):
        slice_order = twap.send_slice(67000 + i * 100)
        if slice_order:
            print(f"  片 {twap.slices_sent}/{twap.num_slices}: {slice_order.amount:.4f} @ {slice_order.price}")

    progress = twap.get_progress()
    print(
        f"  进度: {progress['filled_amount']}/{progress['total_amount']} "
        f"({progress['progress_pct']:.1f}%), TWAP={progress['twap_price']:.2f}"
    )
