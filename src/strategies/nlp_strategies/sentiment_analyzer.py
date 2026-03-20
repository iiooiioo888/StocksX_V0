"""
NLP 情绪分析策略

使用预训练模型分析新闻、社交媒体文本的情绪
- 数据源：Twitter, Reddit, 新闻 RSS
- 模型：BERT / FinBERT
- 信号：正面/负面/中性
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline  # noqa: F401

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SentimentAnalyzer:
    """情绪分析器"""

    def __init__(
        self,
        model_name: str = "prosusai/finbert",
        device: int = -1,  # -1 for CPU, 0+ for GPU
    ):
        """
        初始化情绪分析器

        Args:
            model_name: 预训练模型名称
            device: 设备 ID
        """
        self.model_name = model_name
        self.device = device
        self.pipeline = None
        self.tokenizer = None
        self.model = None

        # 情绪阈值
        self.positive_threshold = 0.6
        self.negative_threshold = 0.4

    def load_model(self):
        """加载模型"""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("请安装 transformers: pip install transformers")

        if self.pipeline is None:
            self.pipeline = pipeline("sentiment-analysis", model=self.model_name, device=self.device)

    def preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 转小写
        text = text.lower()

        # 移除 URL
        text = re.sub(r"http\S+|www\S+|https\S+", "", text)

        # 移除提及和标签
        text = re.sub(r"@\w+|#\w+", "", text)

        # 移除特殊字符和数字
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\d+", "", text)

        # 移除多余空格
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def analyze_sentiment(self, texts: list[str]) -> list[dict]:
        """
        分析文本情绪

        Args:
            texts: 文本列表

        Returns:
            情绪分析结果列表
        """
        if self.pipeline is None:
            self.load_model()

        # 预处理
        texts = [self.preprocess_text(t) for t in texts if t and len(t.strip()) > 0]

        if not texts:
            return []

        # 批量分析
        results = self.pipeline(texts, truncation=True, max_length=512, batch_size=16)

        return results

    def analyze_single(self, text: str) -> dict:
        """分析单个文本"""
        results = self.analyze_sentiment([text])
        return results[0] if results else {"label": "NEUTRAL", "score": 0.5}

    def aggregate_sentiment(self, texts: list[str], weights: list[float] | None = None) -> dict:
        """
        聚合多个文本的情绪

        Args:
            texts: 文本列表
            weights: 权重列表（可选）

        Returns:
            聚合情绪结果
        """
        if not texts:
            return {
                "overall_sentiment": "NEUTRAL",
                "confidence": 0.0,
                "positive_ratio": 0.0,
                "negative_ratio": 0.0,
                "neutral_ratio": 0.0,
                "sample_size": 0,
            }

        results = self.analyze_sentiment(texts)

        # 统计
        sentiment_counts = defaultdict(int)
        total_score = 0.0

        for i, result in enumerate(results):
            label = result.get("label", "NEUTRAL")
            score = result.get("score", 0.5)
            weight = weights[i] if weights else 1.0

            sentiment_counts[label] += weight
            total_score += score * weight

        total = sum(sentiment_counts.values())

        positive_ratio = sentiment_counts.get("positive", 0) / total if total > 0 else 0
        negative_ratio = sentiment_counts.get("negative", 0) / total if total > 0 else 0
        neutral_ratio = sentiment_counts.get("neutral", 0) / total if total > 0 else 0

        # 确定整体情绪
        if positive_ratio > negative_ratio and positive_ratio > 0.4:
            overall = "POSITIVE"
        elif negative_ratio > positive_ratio and negative_ratio > 0.4:
            overall = "NEGATIVE"
        else:
            overall = "NEUTRAL"

        return {
            "overall_sentiment": overall,
            "confidence": total_score / len(results) if results else 0,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
            "neutral_ratio": neutral_ratio,
            "sample_size": len(texts),
        }

    def sentiment_signal(self, texts: list[str], lookback_hours: int = 24) -> dict:
        """
        生成情绪交易信号

        Args:
            texts: 文本列表
            lookback_hours: 回溯时间（小时）

        Returns:
            交易信号
        """
        agg = self.aggregate_sentiment(texts)

        positive_ratio = agg["positive_ratio"]
        negative_ratio = agg["negative_ratio"]
        confidence = agg["confidence"]

        # 生成信号
        if positive_ratio > 0.6 and confidence > 0.7:
            signal = 1
            action = "BUY"
        elif negative_ratio > 0.6 and confidence > 0.7:
            signal = -1
            action = "SELL"
        else:
            signal = 0
            action = "HOLD"

        return {
            "strategy": "sentiment_analysis",
            "signal": signal,
            "action": action,
            "sentiment": agg["overall_sentiment"],
            "confidence": confidence,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
            "sample_size": agg["sample_size"],
            "timestamp": int(datetime.now().timestamp() * 1000),
        }


class NewsMonitor:
    """新闻监控器"""

    def __init__(self, sentiment_analyzer: SentimentAnalyzer | None = None):
        """初始化新闻监控器"""
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
        self.news_cache = []

    def add_news(self, title: str, content: str, source: str, published_at: datetime, symbols: list[str] | None = None):
        """添加新闻"""
        news_item = {
            "title": title,
            "content": content,
            "source": source,
            "published_at": published_at,
            "symbols": symbols or [],
            "sentiment": None,
        }
        self.news_cache.append(news_item)
        return news_item

    def analyze_news_sentiment(self, hours: int = 24) -> dict:
        """分析最近新闻的情绪"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_news = [n for n in self.news_cache if n["published_at"] > cutoff]

        if not recent_news:
            return {"status": "no_news", "sample_size": 0}

        # 分析标题和摘要
        texts = [f"{n['title']} {n['content'][:200]}" for n in recent_news]
        sentiment_result = self.sentiment_analyzer.aggregate_sentiment(texts)

        # 更新新闻情绪
        for news in recent_news:
            text = f"{news['title']} {news['content'][:200]}"
            news["sentiment"] = self.sentiment_analyzer.analyze_single(text)

        return {"status": "analyzed", "sample_size": len(recent_news), **sentiment_result}

    def get_sentiment_signal(self, hours: int = 24) -> dict:
        """获取情绪交易信号"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_news = [n for n in self.news_cache if n["published_at"] > cutoff]

        if not recent_news:
            return {"strategy": "news_sentiment", "signal": 0, "action": "HOLD", "reason": "no_recent_news"}

        texts = [f"{n['title']} {n['content'][:200]}" for n in recent_news]
        return self.sentiment_analyzer.sentiment_signal(texts)


# ════════════════════════════════════════════════════════════
# 使用示例
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 示例文本
    sample_texts = [
        "Bitcoin surges to new highs as institutional adoption accelerates",
        "Crypto market faces regulatory uncertainty amid government crackdown",
        "Ethereum upgrade promises faster transactions and lower fees",
        "Major exchange reports security breach, users concerned",
        "Analysts predict bullish trend continuation in Q2",
    ]

    # 分析情绪
    analyzer = SentimentAnalyzer()

    print("分析单个文本:")
    for text in sample_texts[:2]:
        result = analyzer.analyze_single(text)
        print(f"  {text[:50]}... -> {result}")

    print("\n聚合情绪:")
    agg = analyzer.aggregate_sentiment(sample_texts)
    print(f"  整体情绪：{agg['overall_sentiment']}")
    print(f"  信心度：{agg['confidence']:.2f}")
    print(f"  正面比例：{agg['positive_ratio']:.2f}")
    print(f"  负面比例：{agg['negative_ratio']:.2f}")

    print("\n交易信号:")
    signal = analyzer.sentiment_signal(sample_texts)
    print(f"  信号：{signal['action']}")
    print(f"  信心度：{signal['confidence']:.2f}")
