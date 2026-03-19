"""
StocksX 自動交易模組
===================
提供完整的自動交易功能，包括：
- 交易執行（CCXT）
- 風險管理（停損/停利/倉位控制）
- 自動策略切換
- 異步任務處理
"""

from .auto_trader import AutoTrader
from .executor import TradeExecutor
from .risk_manager import RiskManager

__all__ = ["AutoTrader", "RiskManager", "TradeExecutor"]
