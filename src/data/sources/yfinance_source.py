# yfinance 資料來源：股票、ETF、期貨、指數
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

_TF_TO_YF = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "1h", "1d": "1d",
}

_TF_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000,
}


class YfinanceOhlcvSource:
    """透過 yfinance 拉取傳統市場 K 線。"""

    def __init__(self) -> None:
        try:
            import yfinance  # noqa: F401
        except ImportError:
            raise RuntimeError("請安裝 yfinance: pip install yfinance")

    def fetch_range(
        self,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
    ) -> list[dict[str, Any]]:
        import yfinance as yf

        yf_interval = _TF_TO_YF.get(timeframe, "1h")
        start_dt = datetime.fromtimestamp(since / 1000, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(until / 1000, tz=timezone.utc) + timedelta(days=1)

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_dt.strftime("%Y-%m-%d"),
                            end=end_dt.strftime("%Y-%m-%d"),
                            interval=yf_interval)

        if df.empty:
            logger.warning("yfinance 無法取得 %s 的 %s 數據", symbol, timeframe)
            return []

        # 4h 需要從 1h 合成
        if timeframe == "4h" and yf_interval == "1h":
            df = df.resample("4h").agg({
                "Open": "first", "High": "max", "Low": "min",
                "Close": "last", "Volume": "sum",
            }).dropna()

        rows: list[dict[str, Any]] = []
        for idx, row in df.iterrows():
            ts = int(idx.timestamp() * 1000) if hasattr(idx, "timestamp") else 0
            if ts < since or ts > until:
                continue
            rows.append({
                "exchange": "yfinance",
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": ts,
                "open": float(row.get("Open", 0)),
                "high": float(row.get("High", 0)),
                "low": float(row.get("Low", 0)),
                "close": float(row.get("Close", 0)),
                "volume": float(row.get("Volume", 0)),
                "filled": 0,
                "is_outlier": 0,
            })

        rows.sort(key=lambda x: x["timestamp"])
        return rows
