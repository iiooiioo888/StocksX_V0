"""
StocksX 套利策略模块
====================

提供多种套利策略：
- 跨交易所套利（现货价差）
- 三角套利（循环交易）
- 统计套利（配对交易）
- 资金费率套利（现货 vs 永续）
"""

from .cross_exchange import (
    CrossExchangeArbitrage,
    TriangularArbitrage,
    ArbitrageOpportunity,
)

from .statistical import (
    StatisticalArbitrage,
    FundingRateArbitrage,
    PairSignal,
    FundingRateOpportunity,
)

__all__ = [
    "CrossExchangeArbitrage",
    "TriangularArbitrage",
    "ArbitrageOpportunity",
    "StatisticalArbitrage",
    "FundingRateArbitrage",
    "PairSignal",
    "FundingRateOpportunity",
]
