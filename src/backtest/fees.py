# 交易手續費資料庫
from __future__ import annotations

# 費率格式: {"maker": %, "taker": %, "funding_interval_h": 小時}
# 來源: 各交易所官網 2024-2025 標準費率（VIP0 / 一般用戶）

EXCHANGE_FEES = {
    # ─── 中心化交易所（CEX）─── 永續合約
    "binance": {"maker": 0.02, "taker": 0.04, "name": "Binance", "type": "CEX"},
    "bybit": {"maker": 0.02, "taker": 0.055, "name": "Bybit", "type": "CEX"},
    "okx": {"maker": 0.02, "taker": 0.05, "name": "OKX", "type": "CEX"},
    "bitget": {"maker": 0.02, "taker": 0.06, "name": "Bitget", "type": "CEX"},
    "gate": {"maker": 0.015, "taker": 0.05, "name": "Gate.io", "type": "CEX"},
    "kucoin": {"maker": 0.02, "taker": 0.06, "name": "KuCoin", "type": "CEX"},
    "mexc": {"maker": 0.00, "taker": 0.03, "name": "MEXC", "type": "CEX"},
    "htx": {"maker": 0.02, "taker": 0.05, "name": "HTX", "type": "CEX"},
    "bingx": {"maker": 0.02, "taker": 0.05, "name": "BingX", "type": "CEX"},
    "woo": {"maker": 0.00, "taker": 0.03, "name": "WOO X", "type": "CEX"},
    "cryptocom": {"maker": 0.075, "taker": 0.075, "name": "Crypto.com", "type": "CEX"},

    # ─── 去中心化交易所（DEX）───
    "uniswap": {"maker": 0.30, "taker": 0.30, "name": "Uniswap V3", "type": "DEX", "note": "0.3% 池費率，不含 Gas"},
    "uniswap_001": {"maker": 0.01, "taker": 0.01, "name": "Uniswap 0.01%池", "type": "DEX"},
    "uniswap_005": {"maker": 0.05, "taker": 0.05, "name": "Uniswap 0.05%池", "type": "DEX"},
    "uniswap_100": {"maker": 1.00, "taker": 1.00, "name": "Uniswap 1%池", "type": "DEX"},
    "sushiswap": {"maker": 0.30, "taker": 0.30, "name": "SushiSwap", "type": "DEX"},
    "pancakeswap": {"maker": 0.25, "taker": 0.25, "name": "PancakeSwap", "type": "DEX"},
    "curve": {"maker": 0.04, "taker": 0.04, "name": "Curve Finance", "type": "DEX"},
    "gmx": {"maker": 0.05, "taker": 0.07, "name": "GMX", "type": "DEX-Perp"},
    "dydx": {"maker": 0.02, "taker": 0.05, "name": "dYdX", "type": "DEX-Perp"},
    "hyperliquid": {"maker": 0.01, "taker": 0.035, "name": "Hyperliquid", "type": "DEX-Perp"},
    "jupiter": {"maker": 0.20, "taker": 0.20, "name": "Jupiter (Solana)", "type": "DEX"},
    "raydium": {"maker": 0.25, "taker": 0.25, "name": "Raydium (Solana)", "type": "DEX"},

    # ─── 傳統市場 ───
    "yfinance": {"maker": 0.00, "taker": 0.00, "name": "Yahoo Finance (模擬)", "type": "模擬"},
    "us_broker": {"maker": 0.00, "taker": 0.00, "name": "美股券商 (免佣)", "type": "傳統", "note": "Robinhood/Firstrade 等零佣金"},
    "tw_broker": {"maker": 0.1425, "taker": 0.1425, "name": "台股券商", "type": "傳統", "note": "手續費 0.1425% + 賣出證交稅 0.3%",
                  "sell_tax": 0.30},
    "futures_broker": {"maker": 0.01, "taker": 0.01, "name": "期貨商", "type": "傳統"},
}

# 滑點預設值（%）
DEFAULT_SLIPPAGE = {
    "CEX": 0.01,
    "DEX": 0.10,
    "DEX-Perp": 0.03,
    "傳統": 0.01,
    "模擬": 0.00,
}


def get_fee_rate(exchange: str, order_type: str = "taker") -> float:
    """取得手續費率（%），預設 taker"""
    info = EXCHANGE_FEES.get(exchange, {})
    return info.get(order_type, info.get("taker", 0.05))


def get_sell_tax(exchange: str) -> float:
    """取得賣出稅率（%），僅部分市場有"""
    return EXCHANGE_FEES.get(exchange, {}).get("sell_tax", 0.0)


def get_slippage(exchange: str) -> float:
    """取得預設滑點（%）"""
    ex_type = EXCHANGE_FEES.get(exchange, {}).get("type", "CEX")
    return DEFAULT_SLIPPAGE.get(ex_type, 0.01)


def get_total_cost(exchange: str, order_type: str = "taker", include_slippage: bool = True) -> float:
    """取得單次交易總成本（費率 + 滑點）%"""
    fee = get_fee_rate(exchange, order_type)
    slip = get_slippage(exchange) if include_slippage else 0
    return fee + slip


def list_exchanges_by_type() -> dict[str, list[dict]]:
    """按類型分組列出所有交易所"""
    groups: dict[str, list[dict]] = {}
    for eid, info in EXCHANGE_FEES.items():
        t = info.get("type", "其他")
        if t not in groups:
            groups[t] = []
        groups[t].append({"id": eid, **info})
    return groups
