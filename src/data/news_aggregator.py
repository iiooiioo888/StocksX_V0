# 全球新聞聚合器
# 整合多個新聞來源

from __future__ import annotations

import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import hashlib


# ════════════════════════════════════════════════════════════
# 新聞來源配置
# ════════════════════════════════════════════════════════════

NEWS_SOURCES = {
    # 加密貨幣新聞
    "crypto": [
        {
            "name": "CoinDesk",
            "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "category": "加密貨幣",
            "language": "en"
        },
        {
            "name": "Cointelegraph",
            "url": "https://cointelegraph.com/rss",
            "category": "加密貨幣",
            "language": "en"
        },
        {
            "name": "The Block",
            "url": "https://www.theblock.co/rss.xml",
            "category": "加密貨幣",
            "language": "en"
        },
        {
            "name": "Decrypt",
            "url": "https://decrypt.co/feed",
            "category": "加密貨幣",
            "language": "en"
        },
        {
            "name": "BlockBeats",
            "url": "https://www.theblockbeats.info/feed",
            "category": "加密貨幣",
            "language": "zh"
        },
    ],
    # 財經新聞
    "finance": [
        {
            "name": "Bloomberg",
            "url": "https://feeds.bloomberg.com/markets/news/rss.xml",
            "category": "財經",
            "language": "en"
        },
        {
            "name": "Reuters Business",
            "url": "https://feeds.reuters.com/reuters/businessNews",
            "category": "財經",
            "language": "en"
        },
        {
            "name": "CNBC",
            "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
            "category": "財經",
            "language": "en"
        },
        {
            "name": "Financial Times",
            "url": "https://www.ft.com/?format=rss",
            "category": "財經",
            "language": "en"
        },
        {
            "name": "Wall Street Journal",
            "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
            "category": "財經",
            "language": "en"
        },
    ],
    # 科技新聞
    "tech": [
        {
            "name": "TechCrunch",
            "url": "https://techcrunch.com/feed/",
            "category": "科技",
            "language": "en"
        },
        {
            "name": "The Verge",
            "url": "https://www.theverge.com/rss/index.xml",
            "category": "科技",
            "language": "en"
        },
        {
            "name": "Wired",
            "url": "https://www.wired.com/feed/rss",
            "category": "科技",
            "language": "en"
        },
    ],
    # 台灣財經新聞
    "tw_finance": [
        {
            "name": "鉅亨網",
            "url": "https://feeds.feedburner.com/gigacircle",
            "category": "台灣財經",
            "language": "zh"
        },
        {
            "name": "經濟日報",
            "url": "https://udn.com/rssfeed/rss/0/0/0/0",
            "category": "台灣財經",
            "language": "zh"
        },
        {
            "name": "工商時報",
            "url": "https://chinatimes.com/rss",
            "category": "台灣財經",
            "language": "zh"
        },
    ]
}


# ════════════════════════════════════════════════════════════
# RSS 解析
# ════════════════════════════════════════════════════════════

def parse_rss_feed(url: str, source_name: str) -> List[Dict[str, Any]]:
    """
    解析 RSS Feed
    
    Args:
        url: RSS Feed URL
        source_name: 來源名稱
    
    Returns:
        [
            {
                "title": str,
                "link": str,
                "published": str,
                "summary": str,
                "source": str,
                "category": str,
                "sentiment": str,  # Positive, Neutral, Negative
                "id": str  # 唯一 ID
            }
        ]
    """
    try:
        import feedparser
        
        feed = feedparser.parse(url, request_headers={'User-Agent': 'Mozilla/5.0'})
        
        articles = []
        for entry in feed.entries[:20]:  # 限制 20 篇
            # 生成唯一 ID
            content_hash = hashlib.md5(
                f"{entry.title}{entry.link}".encode()
            ).hexdigest()
            
            # 分析情緒（簡單關鍵字）
            sentiment = analyze_sentiment(entry.title + " " + entry.get('summary', ''))
            
            article = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.get('published', datetime.now().isoformat()),
                "summary": entry.get('summary', '')[:500],  # 限制長度
                "source": source_name,
                "category": feed.feed.get('title', 'Unknown'),
                "sentiment": sentiment,
                "id": content_hash,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)
            }
            
            articles.append(article)
        
        return articles
    except Exception as e:
        print(f"解析 RSS Feed 失敗 {url}: {e}")
        return []


def analyze_sentiment(text: str) -> str:
    """
    簡單情緒分析
    
    Args:
        text: 文字內容
    
    Returns:
        "Positive", "Neutral", or "Negative"
    """
    positive_words = [
        'surge', 'soar', 'jump', 'rally', 'gain', 'rise', 'increase', 'boom',
        'bullish', 'optimistic', 'positive', 'breakthrough', 'success',
        '上漲', '飆升', '大漲', '利多', '樂觀', '突破'
    ]
    
    negative_words = [
        'crash', 'plunge', 'drop', 'fall', 'decline', 'loss', 'bearish',
        'pessimistic', 'negative', 'concern', 'risk', 'warning',
        '下跌', '暴跌', '重挫', '利空', '悲觀', '風險'
    ]
    
    text_lower = text.lower()
    
    positive_count = sum(1 for word in positive_words if word.lower() in text_lower)
    negative_count = sum(1 for word in negative_words if word.lower() in text_lower)
    
    if positive_count > negative_count * 1.5:
        return "Positive"
    elif negative_count > positive_count * 1.5:
        return "Negative"
    else:
        return "Neutral"


# ════════════════════════════════════════════════════════════
# 新聞聚合
# ════════════════════════════════════════════════════════════

def get_crypto_news(limit: int = 50) -> List[Dict[str, Any]]:
    """
    取得加密貨幣新聞
    
    Args:
        limit: 最大文章數
    
    Returns:
        新聞列表
    """
    all_articles = []
    
    for source in NEWS_SOURCES["crypto"]:
        articles = parse_rss_feed(source["url"], source["name"])
        all_articles.extend(articles)
    
    # 按時間排序
    all_articles.sort(
        key=lambda x: x.get('published', ''),
        reverse=True
    )
    
    return all_articles[:limit]


def get_finance_news(limit: int = 50) -> List[Dict[str, Any]]:
    """
    取得財經新聞
    
    Args:
        limit: 最大文章數
    
    Returns:
        新聞列表
    """
    all_articles = []
    
    for source in NEWS_SOURCES["finance"]:
        articles = parse_rss_feed(source["url"], source["name"])
        all_articles.extend(articles)
    
    # 按時間排序
    all_articles.sort(
        key=lambda x: x.get('published', ''),
        reverse=True
    )
    
    return all_articles[:limit]


def get_tech_news(limit: int = 30) -> List[Dict[str, Any]]:
    """
    取得科技新聞
    
    Args:
        limit: 最大文章數
    
    Returns:
        新聞列表
    """
    all_articles = []
    
    for source in NEWS_SOURCES["tech"]:
        articles = parse_rss_feed(source["url"], source["name"])
        all_articles.extend(articles)
    
    # 按時間排序
    all_articles.sort(
        key=lambda x: x.get('published', ''),
        reverse=True
    )
    
    return all_articles[:limit]


def get_tw_finance_news(limit: int = 30) -> List[Dict[str, Any]]:
    """
    取得台灣財經新聞
    
    Args:
        limit: 最大文章數
    
    Returns:
        新聞列表
    """
    all_articles = []
    
    for source in NEWS_SOURCES["tw_finance"]:
        articles = parse_rss_feed(source["url"], source["name"])
        all_articles.extend(articles)
    
    # 按時間排序
    all_articles.sort(
        key=lambda x: x.get('published', ''),
        reverse=True
    )
    
    return all_articles[:limit]


def get_all_news(category: str = "all", limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
    """
    取得所有新聞
    
    Args:
        category: 類別（all, crypto, finance, tech, tw_finance）
        limit: 每類別最大文章數
    
    Returns:
        {
            "crypto": [...],
            "finance": [...],
            "tech": [...],
            "tw_finance": [...]
        }
    """
    if category != "all":
        if category == "crypto":
            return {"crypto": get_crypto_news(limit)}
        elif category == "finance":
            return {"finance": get_finance_news(limit)}
        elif category == "tech":
            return {"tech": get_tech_news(limit)}
        elif category == "tw_finance":
            return {"tw_finance": get_tw_finance_news(limit)}
    
    return {
        "crypto": get_crypto_news(limit),
        "finance": get_finance_news(limit),
        "tech": get_tech_news(limit),
        "tw_finance": get_tw_finance_news(limit)
    }


# ════════════════════════════════════════════════════════════
# 新聞分類與標籤
# ════════════════════════════════════════════════════════════

NEWS_CATEGORIES = {
    "市場動態": ["market", "trading", "price", "指數", "行情"],
    "政策監管": ["regulation", "policy", "SEC", "監管", "政策"],
    "技術發展": ["technology", "blockchain", "innovation", "技術", "區塊鏈"],
    "企業新聞": ["company", "business", "partnership", "企業", "合作"],
    "投資融資": ["investment", "funding", "VC", "投資", "融資"],
    "安全事件": ["security", "hack", "exploit", "安全", "駭客"],
    "DeFi": ["defi", "yield", "liquidity", "去中心化", "流動性"],
    "NFT": ["nft", "collectible", "digital art", "非同質化", "數位藝術"],
    "交易所": ["exchange", "binance", "coinbase", "交易所", "平台"],
    "宏觀經濟": ["macro", "fed", "inflation", "總經", "聯準會"]
}


def categorize_news(title: str, summary: str = "") -> List[str]:
    """
    新聞分類
    
    Args:
        title: 標題
        summary: 摘要
    
    Returns:
        分類標籤列表
    """
    text = (title + " " + summary).lower()
    categories = []
    
    for category, keywords in NEWS_CATEGORIES.items():
        if any(keyword.lower() in text for keyword in keywords):
            categories.append(category)
    
    return categories if categories else ["其他"]


def get_trending_topics(news_list: List[Dict[str, Any]], top_n: int = 10) -> List[str]:
    """
    取得熱門話題
    
    Args:
        news_list: 新聞列表
        top_n: 返回前 N 個
    
    Returns:
        熱門話題列表
    """
    from collections import Counter
    
    all_categories = []
    for news in news_list:
        categories = categorize_news(news.get('title', ''), news.get('summary', ''))
        all_categories.extend(categories)
    
    counter = Counter(all_categories)
    return [category for category, count in counter.most_common(top_n)]


def get_news_sentiment_summary(news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    新聞情緒摘要
    
    Args:
        news_list: 新聞列表
    
    Returns:
        {
            "positive": int,
            "neutral": int,
            "negative": int,
            "sentiment_score": float,  # -1 to 1
            "overall": str  # Bullish, Neutral, Bearish
        }
    """
    sentiment_count = {"Positive": 0, "Neutral": 0, "Negative": 0}
    
    for news in news_list:
        sentiment = news.get('sentiment', 'Neutral')
        sentiment_count[sentiment] += 1
    
    total = len(news_list)
    if total == 0:
        return {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "sentiment_score": 0,
            "overall": "Neutral"
        }
    
    # 計算情緒分數
    sentiment_score = (sentiment_count["Positive"] - sentiment_count["Negative"]) / total
    
    if sentiment_score > 0.2:
        overall = "Bullish"
    elif sentiment_score < -0.2:
        overall = "Bearish"
    else:
        overall = "Neutral"
    
    return {
        "positive": sentiment_count["Positive"],
        "neutral": sentiment_count["Neutral"],
        "negative": sentiment_count["Negative"],
        "sentiment_score": round(sentiment_score, 2),
        "overall": overall
    }
