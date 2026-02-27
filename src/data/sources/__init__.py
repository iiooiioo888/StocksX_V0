"""
外部資料來源統一匯入點。

目前包含：
- yfinance：傳統市場 K 線
- CCXT：加密貨幣 K 線與資金費率
- api_hub：整合常用外部 API 取值
"""

from .yfinance_source import YfinanceOhlcvSource
from .crypto_ccxt import CcxtOhlcvSource, CcxtFundingSource
from .api_hub import (
    fetch_traditional_ohlcv,
    fetch_crypto_ohlcv,
    fetch_polymarket_markets,
    fetch_fred_series,
    fetch_alpha_vantage,
    fetch_polygon,
    fetch_coingecko,
    fetch_coinmarketcap,
    fetch_glassnode,
    fetch_trading_economics,
)

__all__ = [
    "YfinanceOhlcvSource",
    "CcxtOhlcvSource",
    "CcxtFundingSource",
    # 統一 API 入口
    "fetch_traditional_ohlcv",
    "fetch_crypto_ohlcv",
    "fetch_polymarket_markets",
    "fetch_fred_series",
    "fetch_alpha_vantage",
    "fetch_polygon",
    "fetch_coingecko",
    "fetch_coinmarketcap",
    "fetch_glassnode",
    "fetch_trading_economics",
]
