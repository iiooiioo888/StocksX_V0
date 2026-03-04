"""
風險管理模組 - 負責交易風險控制
====================================
功能：
- 停損/停利計算
- 倉位大小計算（凱利公式、固定比例）
- 最大回撤控制
- 每日虧損限制
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    """風險配置"""
    # 倉位控制
    risk_per_trade: float = 0.02      # 每筆交易風險（2%）
    max_position_size: float = 0.25   # 最大倉位（25%）
    position_sizing_method: str = "fixed_fraction"  # fixed_fraction, kelly, fixed_amount
    
    # 停損/停利
    stop_loss_pct: float = 2.0        # 停損百分比
    take_profit_pct: float = 4.0      # 停利百分比
    trailing_stop: bool = False       # 移動停損
    trailing_stop_pct: float = 1.5    # 移動停損百分比
    
    # 總體風險
    max_daily_loss_pct: float = 5.0   # 每日最大虧損（5%）
    max_drawdown_pct: float = 10.0    # 最大回撤（10%）
    max_open_positions: int = 5       # 最大同時持倉數
    
    # 槓桿
    leverage: float = 1.0             # 槓桿倍數
    max_leverage: float = 10.0        # 最大槓桿限制


class RiskManager:
    """
    風險管理器
    
    功能：
    - 計算合適的倉位大小
    - 計算停損/停利價格
    - 檢查風險限制
    - 追蹤每日損益和回撤
    """
    
    def __init__(self, config: Optional[RiskConfig] = None):
        """
        初始化風險管理器
        
        Args:
            config: 風險配置，None 使用預設值
        """
        self.config = config or RiskConfig()
        self._daily_pnl = 0.0
        self._daily_pnl_start = 0.0
        self._peak_equity = 0.0
        self._current_equity = 0.0
        self._open_positions = 0
        
    def reset_daily_pnl(self, starting_equity: float):
        """重置每日損益基準"""
        self._daily_pnl_start = starting_equity
        self._daily_pnl = 0.0
        self._peak_equity = starting_equity
        self._current_equity = starting_equity
        logger.info(f"📊 每日損益基準已重置：${starting_equity:,.2f}")
    
    def update_equity(self, current_equity: float):
        """更新當前權益並計算回撤"""
        self._current_equity = current_equity
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity
    
    def calculate_position_size(
        self,
        equity: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """
        計算合適的倉位大小
        
        Args:
            equity: 總權益
            entry_price: 進場價格
            stop_loss_price: 停損價格
            
        Returns:
            建議倉位大小（數量）
        """
        method = self.config.position_sizing_method
        
        if method == "fixed_fraction":
            return self._fixed_fraction_position_size(
                equity, entry_price, stop_loss_price
            )
        elif method == "kelly":
            return self._kelly_position_size(
                equity, entry_price, stop_loss_price
            )
        elif method == "fixed_amount":
            return self._fixed_amount_position_size(
                equity, entry_price
            )
        else:
            # 預設：全倉
            return equity / entry_price
    
    def _fixed_fraction_position_size(
        self,
        equity: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """
        固定比例倉位計算
        
        公式：倉位 = (權益 × 風險比例) / (進場價 - 停損價)
        """
        risk_amount = equity * self.config.risk_per_trade
        price_diff = abs(entry_price - stop_loss_price)
        
        if price_diff <= 0:
            logger.warning("停損價格無效，使用預設倉位")
            return equity * self.config.max_position_size / entry_price
        
        position_size = risk_amount / price_diff
        
        # 限制最大倉位
        max_position = (equity * self.config.max_position_size) / entry_price
        position_size = min(position_size, max_position)
        
        return position_size
    
    def _kelly_position_size(
        self,
        equity: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """
        凱利公式倉位計算
        
        公式：f* = (p × b - q) / b
        其中：
        - p = 勝率
        - q = 1 - p (失敗率)
        - b = 盈虧比
        """
        # 這裡使用簡化版本，實際勝率和盈虧比應從歷史交易統計
        # 預設假設勝率 50%，盈虧比 2:1
        win_rate = 0.5
        win_loss_ratio = 2.0
        
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        kelly = max(0, min(kelly, self.config.max_position_size))
        
        position_size = (equity * kelly) / entry_price
        return position_size
    
    def _fixed_amount_position_size(
        self,
        equity: float,
        entry_price: float,
    ) -> float:
        """固定金額倉位（使用最大倉位比例）"""
        amount = equity * self.config.max_position_size
        return amount / entry_price
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        side: str,
    ) -> float:
        """
        計算停損價格
        
        Args:
            entry_price: 進場價格
            side: 'long' 或 'short'
            
        Returns:
            停損價格
        """
        if side == "long":
            stop_loss = entry_price * (1 - self.config.stop_loss_pct / 100)
        else:  # short
            stop_loss = entry_price * (1 + self.config.stop_loss_pct / 100)
        
        return round(stop_loss, 2)
    
    def calculate_take_profit(
        self,
        entry_price: float,
        side: str,
    ) -> float:
        """
        計算停利價格
        
        Args:
            entry_price: 進場價格
            side: 'long' 或 'short'
            
        Returns:
            停利價格
        """
        if side == "long":
            take_profit = entry_price * (1 + self.config.take_profit_pct / 100)
        else:  # short
            take_profit = entry_price * (1 - self.config.take_profit_pct / 100)
        
        return round(take_profit, 2)
    
    def calculate_trailing_stop(
        self,
        highest_price: float,
        side: str,
    ) -> float:
        """
        計算移動停損價格
        
        Args:
            highest_price: 最高價（多頭）或最低價（空頭）
            side: 'long' 或 'short'
            
        Returns:
            移動停損價格
        """
        if side == "long":
            trailing_stop = highest_price * (1 - self.config.trailing_stop_pct / 100)
        else:  # short
            trailing_stop = highest_price * (1 + self.config.trailing_stop_pct / 100)
        
        return round(trailing_stop, 2)
    
    def check_risk_limits(self, symbol: str = None) -> Tuple[bool, str]:
        """
        檢查風險限制
        
        Returns:
            (是否可交易，原因)
        """
        # 檢查每日虧損
        if self._daily_pnl_start > 0:
            daily_loss_pct = abs(self._daily_pnl) / self._daily_pnl_start * 100
            if self._daily_pnl < 0 and daily_loss_pct > self.config.max_daily_loss_pct:
                return False, f"達到每日最大虧損限制 ({self.config.max_daily_loss_pct}%)"
        
        # 檢查最大回撤
        if self._peak_equity > 0:
            drawdown_pct = (self._peak_equity - self._current_equity) / self._peak_equity * 100
            if drawdown_pct > self.config.max_drawdown_pct:
                return False, f"達到最大回撤限制 ({self.config.max_drawdown_pct}%)"
        
        # 檢查最大持倉數
        if self._open_positions >= self.config.max_open_positions:
            return False, f"達到最大持倉數限制 ({self.config.max_open_positions})"
        
        # 檢查槓桿
        if self.config.leverage > self.config.max_leverage:
            return False, f"槓桿超過限制 ({self.config.max_leverage}x)"
        
        return True, "通過風險檢查"
    
    def can_open_position(self) -> Tuple[bool, str]:
        """檢查是否可以開新倉"""
        return self.check_risk_limits()
    
    def increment_position(self):
        """增加持倉計數"""
        self._open_positions += 1
        logger.debug(f"📈 持倉數 +1: {self._open_positions}")
    
    def decrement_position(self):
        """減少持倉計數"""
        self._open_positions = max(0, self._open_positions - 1)
        logger.debug(f"📉 持倉數 -1: {self._open_positions}")
    
    def add_daily_pnl(self, pnl: float):
        """
        添加每日損益
        
        Args:
            pnl: 損益金額
        """
        self._daily_pnl += pnl
        self.update_equity(self._current_equity + pnl)
        
        sign = "✅" if pnl >= 0 else "❌"
        logger.info(f"{sign} 每日損益更新：${pnl:+,.2f} (總計：${self._daily_pnl:+,.2f})")
    
    def get_daily_pnl_pct(self) -> float:
        """取得每日損益百分比"""
        if self._daily_pnl_start <= 0:
            return 0.0
        return self._daily_pnl / self._daily_pnl_start * 100
    
    def get_drawdown_pct(self) -> float:
        """取得當前回撤百分比"""
        if self._peak_equity <= 0:
            return 0.0
        return (self._peak_equity - self._current_equity) / self._peak_equity * 100
    
    def get_risk_report(self) -> Dict:
        """
        取得風險報告
        
        Returns:
            風險報告字典
        """
        return {
            "daily_pnl": self._daily_pnl,
            "daily_pnl_pct": self.get_daily_pnl_pct(),
            "current_equity": self._current_equity,
            "peak_equity": self._peak_equity,
            "drawdown_pct": self.get_drawdown_pct(),
            "open_positions": self._open_positions,
            "max_positions": self.config.max_open_positions,
            "leverage": self.config.leverage,
            "risk_per_trade": self.config.risk_per_trade,
        }


def create_risk_manager_from_config(config_dict: Dict) -> RiskManager:
    """
    從配置字典創建風險管理器
    
    Args:
        config_dict: 配置字典
        
    Returns:
        RiskManager 實例
    """
    config = RiskConfig(
        risk_per_trade=config_dict.get("risk_per_trade", 0.02),
        max_position_size=config_dict.get("max_position_size", 0.25),
        position_sizing_method=config_dict.get("position_sizing_method", "fixed_fraction"),
        stop_loss_pct=config_dict.get("stop_loss_pct", 2.0),
        take_profit_pct=config_dict.get("take_profit_pct", 4.0),
        trailing_stop=config_dict.get("trailing_stop", False),
        trailing_stop_pct=config_dict.get("trailing_stop_pct", 1.5),
        max_daily_loss_pct=config_dict.get("max_daily_loss_pct", 5.0),
        max_drawdown_pct=config_dict.get("max_drawdown_pct", 10.0),
        max_open_positions=config_dict.get("max_open_positions", 5),
        leverage=config_dict.get("leverage", 1.0),
        max_leverage=config_dict.get("max_leverage", 10.0),
    )
    return RiskManager(config)
