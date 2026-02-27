from __future__ import annotations

"""
統一管理外部 API 的金鑰與密鑰。

所有金鑰一律從環境變數讀取，建議使用 .env 檔搭配 python-dotenv 載入。
此模組只提供「讀取」與簡單檢查，不會把金鑰寫死在程式碼中。
"""

from typing import Optional

import os

try:
    # 若專案有安裝 python-dotenv，則自動載入 .env
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # 沒有安裝或載入失敗時，略過即可（仍可直接使用系統環境變數）
    pass


def _get(key: str, default: Optional[str] = None) -> Optional[str]:
    """安全讀取環境變數，統一入口。"""
    return os.getenv(key, default)


# ─── AI / LLM ───
DASHSCOPE_API_KEY: Optional[str] = _get("DASHSCOPE_API_KEY")

# ─── 宏觀經濟數據 ───
FRED_API_KEY: Optional[str] = _get("FRED_API_KEY")
TRADING_ECONOMICS_API_KEY: Optional[str] = _get("TRADING_ECONOMICS_API_KEY")

# ─── 加密貨幣與鏈上 ───
COINGECKO_API_KEY: Optional[str] = _get("COINGECKO_API_KEY")
COINMARKETCAP_API_KEY: Optional[str] = _get("COINMARKETCAP_API_KEY")
GLASSNODE_API_KEY: Optional[str] = _get("GLASSNODE_API_KEY")

# ─── 股市與綜合金融 ───
ALPHA_VANTAGE_API_KEY: Optional[str] = _get("ALPHA_VANTAGE_API_KEY")
FMP_API_KEY: Optional[str] = _get("FMP_API_KEY")
POLYGON_API_KEY: Optional[str] = _get("POLYGON_API_KEY")

# ─── 券商 / 交易 ───
ALPACA_API_KEY: Optional[str] = _get("ALPACA_API_KEY")
ALPACA_API_SECRET: Optional[str] = _get("ALPACA_API_SECRET")


def require(key_value: Optional[str], name: str) -> str:
    """
    方便在呼叫 API 前做檢查：
        api_key = require(FRED_API_KEY, "FRED_API_KEY")
    """
    if not key_value:
        raise RuntimeError(f"請先設定環境變數 {name} 才能呼叫對應 API。")
    return key_value

