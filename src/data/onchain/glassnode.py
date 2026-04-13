"""
Glassnode 链上数据源

功能：
- 交易所流入/流出
- 巨鲸地址追踪
- 活跃地址数
- 交易费用
- 挖矿难度
- 持仓分布
- MVRV 比率
- NUPL 指标

数据源：
- Glassnode API v2

更新频率：每小时（部分指标每日）

注意：
- 需要 Glassnode API Key
- 免费版有请求限制（5 次/分钟）
- 部分高级指标需要付费订阅
"""

from __future__ import annotations

import requests
import time
from typing import Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GlassnodeClient:
    """Glassnode API 客户端"""

    BASE_URL = "https://api.glassnode.com"

    def __init__(self, api_key: str):
        """
        初始化 Glassnode 客户端

        Args:
            api_key: Glassnode API Key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
            }
        )

        # 请求限制
        self.last_request_time = 0
        self.min_request_interval = 12  # 5 次/分钟 = 12 秒间隔

    def _rate_limit(self):
        """限流"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"Glassnode 限流，等待 {sleep_time:.1f} 秒")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """发送请求"""
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params["api_key"] = self.api_key

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if isinstance(data, dict) and data.get("error"):
                logger.error(f"Glassnode API 错误：{data['error']}")
                return None

            return data

        except Exception as e:
            logger.error(f"Glassnode 请求失败：{e}")
            return None

    def get_exchange_flow(
        self, asset: str = "BTC", start: Optional[int] = None, end: Optional[int] = None, limit: int = 365
    ) -> list[dict[str, Any]]:
        """
        获取交易所流入/流出数据

        Args:
            asset: 资产（BTC/ETH）
            start: 开始时间戳
            end: 结束时间戳
            limit: 数据点数量

        Returns:
            交易所流量数据
        """
        endpoint = "/v1/metrics/transaction_volume"
        params = {
            "a": asset,
            "i": "24h",  # 日线
            "format": "JSON",
            "limit": limit,
        }

        if start:
            params["start"] = start
        if end:
            params["end"] = end

        data = self._request(endpoint, params)

        if not data:
            return []

        # 解析数据
        result = []
        for item in data:
            timestamp = item.get("t", 0)
            value = item.get("v", 0)

            result.append(
                {
                    "timestamp": timestamp * 1000,  # 转换为毫秒
                    "value": value,
                    "metric": "exchange_flow",
                    "asset": asset,
                }
            )

        return result

    def get_active_addresses(self, asset: str = "BTC", interval: str = "24h", limit: int = 365) -> list[dict[str, Any]]:
        """
        获取活跃地址数

        Args:
            asset: 资产（BTC/ETH）
            interval: 时间间隔（24h/1h）
            limit: 数据点数量

        Returns:
            活跃地址数
        """
        endpoint = "/v1/metrics/addresses_active_count"
        params = {"a": asset, "i": interval, "format": "JSON", "limit": limit}

        data = self._request(endpoint, params)

        if not data:
            return []

        result = []
        for item in data:
            result.append({"timestamp": item.get("t", 0) * 1000, "active_addresses": item.get("v", 0), "asset": asset})

        return result

    def get_whale_transactions(
        self, asset: str = "BTC", threshold_usd: float = 100000, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        获取巨鲸交易（大额转账）

        Args:
            asset: 资产
            threshold_usd: 阈值（美元）
            limit: 数量

        Returns:
            巨鲸交易列表
        """
        endpoint = "/v1/metrics/transactions_volume"
        params = {"a": asset, "i": "24h", "format": "JSON", "limit": limit}

        data = self._request(endpoint, params)

        if not data:
            return []

        result = []
        for item in data:
            value = item.get("v", 0)
            if value >= threshold_usd:
                result.append(
                    {
                        "timestamp": item.get("t", 0) * 1000,
                        "value": value,
                        "value_usd": value,
                        "is_whale": True,
                        "asset": asset,
                    }
                )

        return result

    def get_mining_difficulty(self, asset: str = "BTC", limit: int = 365) -> list[dict[str, Any]]:
        """
        获取挖矿难度

        Args:
            asset: 资产
            limit: 数据点数量

        Returns:
            挖矿难度数据
        """
        endpoint = "/v1/metrics/mining_difficulty"
        params = {"a": asset, "i": "24h", "format": "JSON", "limit": limit}

        data = self._request(endpoint, params)

        if not data:
            return []

        result = []
        for item in data:
            result.append({"timestamp": item.get("t", 0) * 1000, "difficulty": item.get("v", 0), "asset": asset})

        return result

    def get_transaction_fees(self, asset: str = "BTC", limit: int = 365) -> list[dict[str, Any]]:
        """
        获取交易费用

        Args:
            asset: 资产
            limit: 数据点数量

        Returns:
            交易费用数据
        """
        endpoint = "/v1/metrics/fees_sum_per_day"
        params = {"a": asset, "i": "24h", "format": "JSON", "limit": limit}

        data = self._request(endpoint, params)

        if not data:
            return []

        result = []
        for item in data:
            result.append(
                {
                    "timestamp": item.get("t", 0) * 1000,
                    "fees": item.get("v", 0),
                    "fees_usd": item.get("v", 0),  # 简化处理
                    "asset": asset,
                }
            )

        return result

    def get_mvrv_ratio(self, asset: str = "BTC", limit: int = 365) -> list[dict[str, Any]]:
        """
        获取 MVRV 比率（Market Value to Realized Value）

        指标说明：
        - MVRV > 3.5: 市场顶部
        - MVRV < 1: 市场底部

        Args:
            asset: 资产
            limit: 数据点数量

        Returns:
            MVRV 比率
        """
        endpoint = "/v1/metrics/mvrv_ratio"
        params = {"a": asset, "i": "24h", "format": "JSON", "limit": limit}

        data = self._request(endpoint, params)

        if not data:
            return []

        result = []
        for item in data:
            mvrv = item.get("v", 0)
            result.append(
                {
                    "timestamp": item.get("t", 0) * 1000,
                    "mvrv_ratio": mvrv,
                    "signal": "overvalued" if mvrv > 3.5 else "undervalued" if mvrv < 1 else "neutral",
                    "asset": asset,
                }
            )

        return result

    def get_nupl(self, asset: str = "BTC", limit: int = 365) -> list[dict[str, Any]]:
        """
        获取 NUPL（Net Unrealized Profit/Loss）

        指标说明：
        - NUPL > 0.75: 极度贪婪
        - NUPL < -0.75: 极度恐惧

        Args:
            asset: 资产
            limit: 数据点数量

        Returns:
            NUPL 指标
        """
        endpoint = "/v1/metrics/nupl"
        params = {"a": asset, "i": "24h", "format": "JSON", "limit": limit}

        data = self._request(endpoint, params)

        if not data:
            return []

        result = []
        for item in data:
            nupl = item.get("v", 0)
            if nupl > 0.75:
                sentiment = "extreme_greed"
            elif nupl > 0.25:
                sentiment = "greed"
            elif nupl > -0.25:
                sentiment = "neutral"
            elif nupl > -0.75:
                sentiment = "fear"
            else:
                sentiment = "extreme_fear"

            result.append({"timestamp": item.get("t", 0) * 1000, "nupl": nupl, "sentiment": sentiment, "asset": asset})

        return result

    def get_supply_distribution(self, asset: str = "BTC", limit: int = 100) -> list[dict[str, Any]]:
        """
        获取持仓分布（按地址余额）

        Args:
            asset: 资产
            limit: 数据点数量

        Returns:
            持仓分布数据
        """
        endpoint = "/v1/metrics/balance_distribution"
        params = {"a": asset, "i": "24h", "format": "JSON", "limit": limit}

        data = self._request(endpoint, params)

        if not data:
            return []

        result = []
        for item in data:
            result.append({"timestamp": item.get("t", 0) * 1000, "distribution": item.get("v", {}), "asset": asset})

        return result

    def get_exchange_reserve(self, asset: str = "BTC", limit: int = 365) -> list[dict[str, Any]]:
        """
        获取交易所储备量

        Args:
            asset: 资产
            limit: 数据点数量

        Returns:
            交易所储备数据
        """
        endpoint = "/v1/metrics/balance_exchange"
        params = {"a": asset, "i": "24h", "format": "JSON", "limit": limit}

        data = self._request(endpoint, params)

        if not data:
            return []

        result = []
        for item in data:
            reserve = item.get("v", 0)
            result.append({"timestamp": item.get("t", 0) * 1000, "exchange_reserve": reserve, "asset": asset})

        return result


class GlassnodeOnChain:
    """
    Glassnode 链上数据综合分析

    整合多个指标，提供综合的链上分析
    """

    def __init__(self, api_key: str):
        """
        初始化

        Args:
            api_key: Glassnode API Key
        """
        self.client = GlassnodeClient(api_key)
        self.cache = {}
        self.cache_ttl = 3600  # 1 小时缓存

    def get_composite_score(self, asset: str = "BTC") -> dict[str, Any]:
        """
        获取综合链上评分

        基于多个指标：
        - 交易所流量
        - 活跃地址数
        - MVRV 比率
        - NUPL
        - 交易所储备

        Returns:
            综合评分（0-100）和各项指标
        """
        # 获取各项指标（简化示例，实际应该获取最新值）
        mvrv_data = self.client.get_mvrv_ratio(asset, limit=1)
        nupl_data = self.client.get_nupl(asset, limit=1)
        exchange_reserve = self.client.get_exchange_reserve(asset, limit=1)

        # 计算综合评分
        score = 50  # 基础分

        # MVRV 评分
        if mvrv_data:
            mvrv = mvrv_data[0].get("mvrv_ratio", 2)
            if mvrv < 1:
                score += 20  # 低估
            elif mvrv > 3.5:
                score -= 20  # 高估

        # NUPL 评分
        if nupl_data:
            nupl = nupl_data[0].get("nupl", 0)
            if nupl < -0.75:
                score += 25  # 极度恐惧，买入机会
            elif nupl > 0.75:
                score -= 25  # 极度贪婪，风险

        # 交易所储备评分
        if exchange_reserve:
            reserve = exchange_reserve[0].get("exchange_reserve", 0)
            # 储备减少 = 利好（提币）
            score += 10

        # 限制在 0-100
        score = max(0, min(100, score))

        # 生成信号
        if score >= 70:
            signal = "strong_buy"
        elif score >= 55:
            signal = "buy"
        elif score >= 45:
            signal = "hold"
        elif score >= 30:
            signal = "sell"
        else:
            signal = "strong_sell"

        return {
            "score": score,
            "signal": signal,
            "mvrv": mvrv_data[0] if mvrv_data else None,
            "nupl": nupl_data[0] if nupl_data else None,
            "exchange_reserve": exchange_reserve[0] if exchange_reserve else None,
            "timestamp": datetime.now().isoformat(),
            "asset": asset,
        }

    def get_whale_activity_summary(self, asset: str = "BTC") -> dict[str, Any]:
        """
        获取巨鲸活动摘要

        Returns:
            巨鲸活动统计
        """
        whale_txs = self.client.get_whale_transactions(asset, threshold_usd=100000, limit=100)

        if not whale_txs:
            return {"error": "No data"}

        # 统计
        total_volume = sum(tx["value_usd"] for tx in whale_txs)
        tx_count = len(whale_txs)
        avg_tx_size = total_volume / tx_count if tx_count > 0 else 0

        # 按时间统计（最近 24 小时）
        now = datetime.now().timestamp() * 1000
        last_24h = [tx for tx in whale_txs if now - tx["timestamp"] < 86400000]

        return {
            "total_whale_txs": tx_count,
            "total_volume_usd": total_volume,
            "avg_tx_size_usd": avg_tx_size,
            "last_24h_txs": len(last_24h),
            "last_24h_volume": sum(tx["value_usd"] for tx in last_24h),
            "asset": asset,
            "timestamp": datetime.now().isoformat(),
        }


# 测试
if __name__ == "__main__":
    # 注意：需要真实的 API Key 才能测试
    import os

    api_key = os.getenv("GLASSNODE_API_KEY", "demo_key")

    if api_key == "demo_key":
        print("⚠️ 使用演示模式，需要设置 GLASSNODE_API_KEY 环境变量")

    # 测试客户端
    client = GlassnodeClient(api_key)

    print("测试 Glassnode API...")

    # 测试 MVRV
    print("\n1. MVRV 比率")
    mvrv = client.get_mvrv_ratio("BTC", limit=10)
    if mvrv:
        print(f"获取到 {len(mvrv)} 条数据")
        print(f"最新：{mvrv[-1]}")

    # 测试 NUPL
    print("\n2. NUPL 指标")
    nupl = client.get_nupl("BTC", limit=10)
    if nupl:
        print(f"获取到 {len(nupl)} 条数据")
        print(f"最新情绪：{nupl[-1].get('sentiment')}")

    # 测试综合评分
    print("\n3. 综合链上评分")
    onchain = GlassnodeOnChain(api_key)
    score = onchain.get_composite_score("BTC")
    print(f"综合评分：{score['score']}/100")
    print(f"信号：{score['signal']}")
