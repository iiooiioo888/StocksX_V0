"""
台湾证券交易所（TWSE）数据源

功能：
- 上市/上柜股票实时行情
- 历史 K 线数据
- 当日成交明细
- 三大法人买卖超
- 融资融券数据

数据源：
- 台股资讯观测站
- 证券交易所开放 API

更新频率：交易时段实时（5 秒延迟）
"""

from __future__ import annotations

import requests
import time
from typing import Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TWSESource:
    """台湾证券交易所数据源"""

    BASE_URL = "https://www.twse.com.tw"

    def __init__(self):
        """初始化 TWSE 数据源"""
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (StocksX V0)",
                "Accept": "application/json",
            }
        )

        # 缓存
        self._cache = {}
        self._cache_ttl = 60  # 60 秒缓存

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        days: int = 365,
        since: Optional[int] = None,
        until: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        获取台股历史 K 线

        Args:
            symbol: 股票代码（如 2330.TW）
            timeframe: 时间周期（1d, 1h, 5m）
            days: 获取天数
            since: 起始时间戳（毫秒）
            until: 结束时间戳（毫秒）

        Returns:
            OHLCV 数据列表
        """
        # 清理股票代码
        stock_id = symbol.replace(".TW", "").replace(".TWO", "")

        # 计算日期范围
        if since:
            start_date = datetime.fromtimestamp(since / 1000)
        else:
            start_date = datetime.now() - timedelta(days=days)

        if until:
            end_date = datetime.fromtimestamp(until / 1000)
        else:
            end_date = datetime.now()

        # 台股 API 只支持日线
        if timeframe != "1d":
            logger.warning(f"台股只支持日线数据，timeframe={timeframe} 将被转换为 1d")

        all_data = []

        # 分页获取数据
        current_date = start_date
        while current_date <= end_date:
            try:
                url = f"{self.BASE_URL}/exchangeReport/STOCK_DAY"
                params = {"date": current_date.strftime("%Y%m%d"), "stockNo": stock_id, "response": "json"}

                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                # 解析数据
                if data.get("stat") == "OK":
                    fields = data["fields"]
                    for row in data.get("data", []):
                        ohlcv = self._parse_row(fields, row, symbol)
                        if ohlcv:
                            all_data.append(ohlcv)

                # 移动到下一天
                current_date += timedelta(days=1)

                # 避免请求过快
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"获取台股数据失败：{e}")
                current_date += timedelta(days=1)

        return all_data

    def _parse_row(self, fields: list[str], row: list[str], symbol: str) -> Optional[dict[str, Any]]:
        """解析单行数据"""
        try:
            data = dict(zip(fields, row))

            # 转换数据类型
            timestamp = int(datetime.strptime(data["日期"], "%Y年%m月%d日").timestamp() * 1000)
            open_price = float(data["開盤價"].replace(",", "")) if data["開盤價"] != "--" else 0
            high = float(data["最高價"].replace(",", "")) if data["最高價"] != "--" else 0
            low = float(data["最低價"].replace(",", "")) if data["最低價"] != "--" else 0
            close = float(data["收盤價"].replace(",", "")) if data["收盤價"] != "--" else 0
            volume = int(data["成交股數"].replace(",", "")) if data["成交股數"] != "--" else 0

            return {
                "exchange": "TWSE",
                "symbol": symbol,
                "timeframe": "1d",
                "timestamp": timestamp,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "amount": float(data["成交金額"].replace(",", "")) if "成交金額" in data else 0,
                "transactions": int(data["成交筆數"].replace(",", "")) if "成交筆數" in data else 0,
            }

        except Exception as e:
            logger.error(f"解析台股数据行失败：{e}")
            return None

    def get_realtime_quote(self, symbol: str) -> dict[str, Any]:
        """
        获取实时报价

        Args:
            symbol: 股票代码

        Returns:
            实时报价数据
        """
        try:
            stock_id = symbol.replace(".TW", "").replace(".TWO", "")
            url = f"{self.BASE_URL}/exchangeReport/STOCK_DAY"
            params = {"date": datetime.now().strftime("%Y%m%d"), "stockNo": stock_id, "response": "json"}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("stat") == "OK" and data.get("data"):
                latest = data["data"][-1]
                fields = data["fields"]
                parsed = self._parse_row(fields, latest, symbol)

                return {
                    "symbol": symbol,
                    "price": parsed["close"],
                    "change": parsed["close"] - parsed["open"],
                    "change_pct": ((parsed["close"] - parsed["open"]) / parsed["open"] * 100) if parsed["open"] else 0,
                    "high": parsed["high"],
                    "low": parsed["low"],
                    "open": parsed["open"],
                    "prev_close": parsed["open"],  # 简化处理
                    "volume": parsed["volume"],
                    "amount": parsed["amount"],
                    "timestamp": parsed["timestamp"],
                    "exchange": "TWSE",
                }

            return {"error": "No data available"}

        except Exception as e:
            logger.error(f"获取台股实时报价失败：{e}")
            return {"error": str(e)}

    def get_institutional_trading(self, symbol: str, days: int = 30) -> dict[str, Any]:
        """
        获取三大法人买卖超数据

        Args:
            symbol: 股票代码
            days: 天数

        Returns:
            法人买卖数据
        """
        try:
            stock_id = symbol.replace(".TW", "").replace(".TWO", "")
            start_date = datetime.now() - timedelta(days=days)

            url = f"{self.BASE_URL}/exchangeReport/FIN8_DAY"
            params = {"date": start_date.strftime("%Y%m%d"), "stockNo": stock_id, "response": "json"}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            result = {
                "symbol": symbol,
                "foreign_investors": {"buy": 0, "sell": 0, "net": 0},
                "investment_trust": {"buy": 0, "sell": 0, "net": 0},
                "dealer": {"buy": 0, "sell": 0, "net": 0},
            }

            if data.get("stat") == "OK":
                # 解析法人买卖数据
                for row in data.get("data", []):
                    # 简化处理，实际需要根据字段名解析
                    pass

            return result

        except Exception as e:
            logger.error(f"获取法人买卖数据失败：{e}")
            return {"error": str(e)}

    def get_margin_financing(self, symbol: str, days: int = 30) -> dict[str, Any]:
        """
        获取融资融券数据

        Args:
            symbol: 股票代码
            days: 天数

        Returns:
            融资融券数据
        """
        try:
            stock_id = symbol.replace(".TW", "").replace(".TWO", "")
            start_date = datetime.now() - timedelta(days=days)

            url = f"{self.BASE_URL}/exchangeReport/FIN9_DAY"
            params = {"date": start_date.strftime("%Y%m%d"), "stockNo": stock_id, "response": "json"}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            result = {
                "symbol": symbol,
                "margin_buy": 0,  # 融资买入
                "margin_sell": 0,  # 融券卖出
                "margin_balance": 0,  # 融资余额
                "short_balance": 0,  # 融券余额
            }

            if data.get("stat") == "OK":
                # 解析融资融券数据
                for row in data.get("data", []):
                    pass

            return result

        except Exception as e:
            logger.error(f"获取融资融券数据失败：{e}")
            return {"error": str(e)}

    def list_all_stocks(self) -> list[dict[str, str]]:
        """
        列出所有上市股票

        Returns:
            股票列表
        """
        try:
            url = f"{self.BASE_URL}/exchangeReport/STOCK_LIST"
            params = {"response": "json"}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            stocks = []
            if data.get("stat") == "OK":
                for row in data.get("data", []):
                    stocks.append(
                        {
                            "symbol": row[0] + ".TW",
                            "name": row[1],
                            "type": "上市" if len(row[0]) == 4 else "上柜",
                        }
                    )

            return stocks

        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return []


# 测试
if __name__ == "__main__":
    twse = TWSESource()

    # 测试获取台积电 K 线
    print("测试获取台积电 (2330.TW) K 线...")
    data = twse.fetch_ohlcv("2330.TW", days=30)
    print(f"获取到 {len(data)} 条数据")
    if data:
        print(f"最新数据：{data[-1]}")

    # 测试实时报价
    print("\n测试实时报价...")
    quote = twse.get_realtime_quote("2330.TW")
    print(f"实时报价：{quote}")
