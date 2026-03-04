# 新闻源聚合服务（简化版 World Monitor）
# 功能：RSS 新闻聚合、分类、缓存

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# 新闻源配置（针对加密货币/金融优化）
# ════════════════════════════════════════════════════════════

# 主要新闻源（加密货币/金融相关）
CRYPTO_NEWS_FEEDS = [
    {
        "name": "CoinDesk",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "category": "crypto",
        "lang": "en",
        "priority": 1,
    },
    {
        "name": "Cointelegraph",
        "url": "https://cointelegraph.com/rss",
        "category": "crypto",
        "lang": "en",
        "priority": 1,
    },
    {
        "name": "The Block",
        "url": "https://www.theblock.co/rss.xml",
        "category": "crypto",
        "lang": "en",
        "priority": 1,
    },
    {
        "name": "Decrypt",
        "url": "https://decrypt.co/feed",
        "category": "crypto",
        "lang": "en",
        "priority": 2,
    },
    {
        "name": "Bitcoin Magazine",
        "url": "https://bitcoinmagazine.com/.rss",
        "category": "crypto",
        "lang": "en",
        "priority": 2,
    },
    {
        "name": "CryptoSlate",
        "url": "https://cryptoslate.com/feed/",
        "category": "crypto",
        "lang": "en",
        "priority": 2,
    },
]

# 传统金融新闻源
FINANCE_NEWS_FEEDS = [
    {
        "name": "Bloomberg Crypto",
        "url": "https://www.bloomberg.com/feed/crypto.xml",
        "category": "finance",
        "lang": "en",
        "priority": 1,
    },
    {
        "name": "Reuters Business",
        "url": "https://www.reutersagency.com/feed/",
        "category": "finance",
        "lang": "en",
        "priority": 1,
    },
    {
        "name": "Financial Times",
        "url": "https://www.ft.com/?format=rss",
        "category": "finance",
        "lang": "en",
        "priority": 2,
    },
]

# 中文新闻源
CHINESE_NEWS_FEEDS = [
    {
        "name": "金色财经",
        "url": "https://www.jin10.com/feed",
        "category": "crypto",
        "lang": "zh",
        "priority": 1,
    },
    {
        "name": "链闻",
        "url": "https://www.chainnews.com/feed",
        "category": "crypto",
        "lang": "zh",
        "priority": 2,
    },
]

# 关键词分类（用于自动分类新闻）
KEYWORD_CATEGORIES = {
    "bitcoin": ["BTC", "Bitcoin", "比特币", "加密货币"],
    "ethereum": ["ETH", "Ethereum", "以太坊", "智能合约"],
    "defi": ["DeFi", "去中心化金融", "流动性挖矿", "Yield Farming"],
    "nft": ["NFT", "非同质化代币", "数字藏品"],
    "regulation": ["监管", "SEC", "政策", "法规", "ban", "regulation"],
    "exchange": ["交易所", "Binance", "Coinbase", "FTX"],
    "market": ["市场", "价格", "交易", "bull", "bear", "行情"],
    "technology": ["技术", "升级", "Layer2", "扩容", "scalability"],
}

# 威胁/重要性关键词
IMPORTANT_KEYWORDS = [
    "紧急", "突发", "breaking", "alert",
    "暴涨", "暴跌", "surge", "crash", "plunge",
    "黑客", "攻击", "hack", "exploit", "attack",
    "监管", "禁令", "ban", "regulation", "SEC",
    "破产", "清算", "bankrupt", "liquidation",
]


class NewsAggregator:
    """新闻聚合器"""

    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 分钟缓存
        self.feed_cache: Dict[str, List[Dict]] = {}
        self.feed_cache_ttl = 600  # 10 分钟 feed 缓存

    def get_news_digest(
        self,
        category: str = "all",
        lang: str = "en",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取新闻摘要

        Args:
            category: 类别 (all/crypto/finance)
            lang: 语言 (en/zh)
            limit: 返回数量限制

        Returns:
            新闻列表
        """
        cache_key = f"{category}:{lang}:{limit}"
        now = time.time()

        # 检查缓存
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if now - cached["timestamp"] < self.cache_ttl:
                return cached["data"]

        # 获取新闻源列表
        feeds = self._get_feeds_for_category(category, lang)

        # 并行获取所有 feed
        all_items = []
        for feed in feeds:
            try:
                items = self._fetch_feed(feed["url"], feed["name"])
                if items:
                    for item in items:
                        item["source"] = feed["name"]
                        item["category"] = self._classify_item(item)
                        item["importance"] = self._calculate_importance(item)
                    all_items.extend(items)
            except Exception as e:
                logger.warning(f"获取 feed 失败 {feed['url']}: {e}")

        # 排序和去重
        all_items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        unique_items = self._deduplicate(all_items)

        # 限制数量
        result = unique_items[:limit]

        # 缓存
        self.cache[cache_key] = {
            "timestamp": now,
            "data": result,
        }

        return result

    def _get_feeds_for_category(self, category: str, lang: str) -> List[Dict]:
        """获取指定类别的新闻源"""
        all_feeds = []

        if category in ["all", "crypto"]:
            all_feeds.extend(CRYPTO_NEWS_FEEDS)
        if category in ["all", "finance"]:
            all_feeds.extend(FINANCE_NEWS_FEEDS)
        if lang == "zh":
            all_feeds.extend(CHINESE_NEWS_FEEDS)

        # 按语言过滤
        if lang != "all":
            all_feeds = [f for f in all_feeds if f["lang"] == lang or f["lang"] == "all"]

        # 按优先级排序
        all_feeds.sort(key=lambda x: x.get("priority", 99))

        return all_feeds

    def _fetch_feed(self, url: str, source_name: str) -> List[Dict]:
        """获取并解析 RSS feed"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        now = time.time()

        # 检查 feed 缓存
        if cache_key in self.feed_cache:
            cached = self.feed_cache[cache_key]
            if now - cached["timestamp"] < self.feed_cache_ttl:
                return cached["items"]

        try:
            import feedparser
        except ImportError:
            logger.warning("feedparser 未安装，使用模拟数据")
            return self._generate_mock_news(source_name)

        try:
            # 解析 RSS feed
            feed = feedparser.parse(url, request_headers={
                'User-Agent': 'Mozilla/5.0 (StocksX News Aggregator)'
            })

            items = []
            for entry in feed.entries[:5]:  # 每个 feed 最多 5 条
                item = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "source": source_name,
                    "timestamp": self._parse_timestamp(entry),
                    "summary": entry.get("summary", "")[:200],
                    "id": hashlib.md5(entry.get("link", "").encode()).hexdigest(),
                }
                items.append(item)

            # 缓存
            self.feed_cache[cache_key] = {
                "timestamp": now,
                "items": items,
            }

            return items

        except Exception as e:
            logger.warning(f"解析 feed 失败 {url}: {e}")
            return self._generate_mock_news(source_name)

    def _parse_timestamp(self, entry: Any) -> float:
        """解析时间戳"""
        import email.utils

        # 尝试多种时间字段
        for field in ["published_parsed", "updated_parsed", "created_parsed"]:
            if hasattr(entry, field) and entry[field]:
                try:
                    return time.mktime(entry[field])
                except:
                    pass

        # 尝试字符串格式
        for field in ["published", "updated", "created"]:
            if hasattr(entry, field) and entry[field]:
                try:
                    parsed = email.utils.parsedate_tz(entry[field])
                    if parsed:
                        return time.mktime(parsed)
                except:
                    pass

        return time.time()

    def _classify_item(self, item: Dict) -> str:
        """分类新闻"""
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()

        scores = {}
        for category, keywords in KEYWORD_CATEGORIES.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            scores[category] = score

        if scores:
            return max(scores, key=scores.get)
        return "general"

    def _calculate_importance(self, item: Dict) -> int:
        """计算重要性分数 (1-5)"""
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()

        score = 1

        # 检查重要关键词
        for keyword in IMPORTANT_KEYWORDS:
            if keyword.lower() in text:
                score += 1
                break

        # 检查是否包含价格/市场相关
        if any(kw in text for kw in ["price", "market", "trading", "价格", "市场"]):
            score += 1

        # 限制最高分数
        return min(score, 5)

    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        """去重（基于标题相似度）"""
        seen_titles = set()
        unique = []

        for item in items:
            title = item.get("title", "").lower()
            # 简化标题用于比较
            simple_title = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', title)

            if simple_title not in seen_titles:
                seen_titles.add(simple_title)
                unique.append(item)

        return unique

    def _generate_mock_news(self, source_name: str) -> List[Dict]:
        """生成模拟新闻（当 feed 不可用时）"""
        import random

        mock_titles = [
            f"{source_name}: Bitcoin 价格突破新高",
            f"{source_name}: 以太坊升级即将完成",
            f"{source_name}: DeFi 协议总锁仓量增长",
            f"{source_name}: 监管机构讨论新政策",
            f"{source_name}: 主要交易所发布新公告",
        ]

        now = time.time()
        return [
            {
                "title": title,
                "link": f"https://example.com/news/{random.randint(1000, 9999)}",
                "source": source_name,
                "timestamp": now - random.randint(0, 3600),
                "summary": f"这是来自 {source_name} 的模拟新闻内容...",
                "id": hashlib.md5(title.encode()).hexdigest(),
            }
            for title in mock_titles[:3]
        ]


# 全局实例
news_aggregator = NewsAggregator()


def get_crypto_news(limit: int = 20, lang: str = "en") -> List[Dict]:
    """获取加密货币新闻"""
    return news_aggregator.get_news_digest(category="crypto", lang=lang, limit=limit)


def get_finance_news(limit: int = 20, lang: str = "en") -> List[Dict]:
    """获取金融新闻"""
    return news_aggregator.get_news_digest(category="finance", lang=lang, limit=limit)


def get_all_news(limit: int = 50, lang: str = "en") -> List[Dict]:
    """获取所有新闻"""
    return news_aggregator.get_news_digest(category="all", lang=lang, limit=limit)


# 测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    news = get_crypto_news(limit=10)
    for n in news:
        print(f"[{n['source']}] {n['title']} (重要性：{n['importance']})")
