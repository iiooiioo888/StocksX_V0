"""
StocksX 自動交易 UI 模組
======================
提供完整的自動交易圖形化界面
"""

from .dashboard import render_auto_trading_dashboard
from .position_monitor import render_position_monitor
from .strategy_config import render_strategy_configurator
from .risk_manager_ui import render_risk_manager_ui
from .trade_log import render_trade_log_viewer

__all__ = [
    "render_auto_trading_dashboard",
    "render_position_monitor",
    "render_strategy_configurator",
    "render_risk_manager_ui",
    "render_trade_log_viewer",
]
