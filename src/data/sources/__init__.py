"""
外部資料來源統一匯入點。

目前包含：
- yfinance：傳統市場 K 線
- CCXT：加密貨幣 K 線與資金費率
- api_hub：整合常用外部 API 取值（FMP、Alpaca、Fear & Greed、VIX 等）
"""

from .api_hub import (
    # 券商交易
    fetch_alpaca,
    fetch_alpaca_account,
    fetch_alpaca_bars,
    fetch_alpaca_orders,
    fetch_alpaca_positions,
    # 股市數據
    fetch_alpha_vantage,
    fetch_cboe_vix,
    # 加密貨幣
    fetch_coingecko,
    fetch_coinmarketcap,
    fetch_crypto_ohlcv,
    # 情緒數據
    fetch_fear_greed_index,
    fetch_fmp,
    fetch_fmp_financials,
    fetch_fmp_profile,
    fetch_fmp_quote,
    # 宏觀經濟
    fetch_fred_series,
    fetch_glassnode,
    fetch_market_sentiment,
    fetch_polygon,
    # 預測市場
    fetch_polymarket_markets,
    fetch_trading_economics,
    # OHLCV 數據
    fetch_traditional_ohlcv,
    fetch_vix_history,
    get_current_fear_greed,
)
from .crypto_ccxt import CcxtFundingSource, CcxtOhlcvSource
from .yfinance_source import YfinanceOhlcvSource

__all__ = [
    "YfinanceOhlcvSource",
    "CcxtOhlcvSource",
    "CcxtFundingSource",
    # OHLCV 數據
    "fetch_traditional_ohlcv",
    "fetch_crypto_ohlcv",
    # 預測市場
    "fetch_polymarket_markets",
    # 宏觀經濟
    "fetch_fred_series",
    "fetch_trading_economics",
    # 股市數據
    "fetch_alpha_vantage",
    "fetch_polygon",
    "fetch_fmp",
    "fetch_fmp_profile",
    "fetch_fmp_quote",
    "fetch_fmp_financials",
    # 加密貨幣
    "fetch_coingecko",
    "fetch_coinmarketcap",
    "fetch_glassnode",
    # 券商交易
    "fetch_alpaca",
    "fetch_alpaca_bars",
    "fetch_alpaca_account",
    "fetch_alpaca_positions",
    "fetch_alpaca_orders",
    # 情緒數據
    "fetch_fear_greed_index",
    "get_current_fear_greed",
    "fetch_cboe_vix",
    "fetch_vix_history",
    "fetch_market_sentiment",
]
