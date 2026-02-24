#!/usr/bin/env python3
"""
簡單範例：使用 CryptoDataFetcher 拉取 Binance BTC/USDT 永續 K 線與資金費率，
並示範緩存優先讀取。
"""
import logging
import sys
import time
from pathlib import Path

# 專案根目錄加入 path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.crypto import CryptoDataFetcher

logging.basicConfig(level=logging.INFO)


def main():

    fetcher = CryptoDataFetcher("binance")
    symbol = "BTC/USDT:USDT"

    # 約 7 天前至今
    until_ms = int(time.time() * 1000)
    since_ms = until_ms - 7 * 24 * 3600 * 1000

    print("拉取 K 線 (1h)...")
    fetcher.fetch_ohlcv(symbol, "1h", since=since_ms, limit=200)

    print("拉取資金費率...")
    fetcher.fetch_funding_rate(symbol, since=since_ms, limit=100)

    print("從緩存讀取並補齊缺口...")
    rows = fetcher.get_ohlcv(symbol, "1h", since_ms, until_ms, fill_gaps=True, exclude_outliers=False)
    print(f"共取得 {len(rows)} 根 K 線（含 FFill）")


if __name__ == "__main__":
    main()
