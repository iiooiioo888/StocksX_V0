# StocksX 新闻源功能整合指南

## 📰 功能概述

整合了 **World Monitor 风格的新闻聚合功能**，提供实时加密货币/金融新闻推送。

### 核心功能
- ✅ **170+ RSS 新闻源聚合**
- ✅ **智能分类**（加密货币/金融/监管/技术等）
- ✅ **重要性评分**（1-5 级）
- ✅ **多层缓存**（减少 API 调用）
- ✅ **突发新闻警报**
- ✅ **新闻滚动条**
- ✅ **中文/英文支持**

---

## 📦 安装依赖

### 1. 安装 feedparser
```bash
pip install feedparser
```

### 2. 可选：安装 AI 摘要依赖
```bash
pip install transformers torch onnxruntime
```

---

## 🗂️ 文件结构

```
StocksX_V0/
├── src/
│   ├── data/
│   │   └── news_aggregator.py       # 新闻聚合服务
│   └── ui_news/
│       └── news_panel.py            # 新闻面板 UI
└── pages/
    └── 5_📡_交易監控_v6_compact.py   # 整合新闻的仪表板
```

---

## 🔧 配置新闻源

### 编辑 `src/data/news_aggregator.py`

#### 1. 添加自定义新闻源
```python
CRYPTO_NEWS_FEEDS = [
    {
        "name": "你的新闻源名称",
        "url": "https://example.com/rss",
        "category": "crypto",
        "lang": "zh",  # en/zh/all
        "priority": 1,  # 1=高优先级，2=普通
    },
    # ... 更多新闻源
]
```

#### 2. 配置关键词分类
```python
KEYWORD_CATEGORIES = {
    "bitcoin": ["BTC", "Bitcoin", "比特币"],
    "ethereum": ["ETH", "Ethereum", "以太坊"],
    "你的分类": ["关键词 1", "关键词 2"],
}
```

#### 3. 配置重要性关键词
```python
IMPORTANT_KEYWORDS = [
    "紧急", "突发", "breaking",
    "你的重要关键词",
]
```

---

## 📊 使用方式

### 1. 在仪表板中显示新闻面板

```python
from src.ui_news.news_panel import render_news_panel

# 在 Streamlit 页面中调用
render_news_panel(
    category="all",      # all/crypto/finance
    lang="all",          # all/en/zh
    limit=20,            # 显示数量
    show_summary=False,  # 是否显示摘要
    auto_refresh=True,   # 自动刷新
    refresh_interval=60, # 刷新间隔（秒）
)
```

### 2. 显示突发新闻警报

```python
from src.ui_news.news_panel import render_breaking_news_alert

# 显示高重要性新闻
render_breaking_news_alert(limit=3)
```

### 3. 显示新闻滚动条

```python
from src.ui_news.news_panel import render_news_ticker

# 在顶部显示滚动新闻
render_news_ticker(
    symbols=["BTC/USDT", "ETH/USDT"],  # 关注的交易对
    limit=10  # 显示数量
)
```

### 4. 直接获取新闻数据

```python
from src.data.news_aggregator import (
    get_crypto_news,
    get_finance_news,
    get_all_news,
)

# 获取加密货币新闻
crypto_news = get_crypto_news(limit=20, lang="en")

# 获取金融新闻
finance_news = get_finance_news(limit=20, lang="zh")

# 获取所有新闻
all_news = get_all_news(limit=50, lang="all")

# 处理新闻
for news in all_news:
    print(f"[{news['source']}] {news['title']}")
    print(f"  分类：{news['category']}")
    print(f"  重要性：{news['importance']}")
    print(f"  链接：{news['link']}")
```

---

## 🎨 UI 组件说明

### 新闻卡片样式

```
┌────────────────────────────────────────────┐
│ BTC 价格突破新高                            │ ← 标题（蓝色链接）
│ CoinDesk • 5 分钟前 • crypto ⚡ 高          │ ← 元数据
└────────────────────────────────────────────┘
```

### 重要性标识
- 🔴 **高重要性**（4-5 分）：红色左边框，突发新闻警报
- 🟡 **中重要性**（3 分）：黄色左边框
- 🟢 **低重要性**（1-2 分）：绿色左边框

### 分类标签
- `crypto` - 加密货币
- `finance` - 金融
- `defi` - DeFi
- `nft` - NFT
- `regulation` - 监管
- `exchange` - 交易所
- `market` - 市场
- `technology` - 技术

---

## ⚙️ 缓存配置

### 默认缓存策略
```python
# 新闻摘要缓存：5 分钟
self.cache_ttl = 300

# Feed 缓存：10 分钟
self.feed_cache_ttl = 600
```

### 修改缓存时间
编辑 `src/data/news_aggregator.py`:
```python
class NewsAggregator:
    def __init__(self):
        self.cache_ttl = 600  # 改为 10 分钟
        self.feed_cache_ttl = 1200  # 改为 20 分钟
```

---

## 📈 性能优化

### 1. 批量获取
```python
# ❌ 错误：逐个获取
for url in feed_urls:
    news = fetch_feed(url)

# ✅ 正确：批量获取
all_news = get_all_news(limit=50)
```

### 2. 使用缓存
```python
# 第一次调用：获取并缓存
news1 = get_crypto_news()

# 5 分钟内再次调用：直接返回缓存
news2 = get_crypto_news()  # 秒回
```

### 3. 限制数量
```python
# ❌ 错误：获取太多
news = get_all_news(limit=200)

# ✅ 正确：合理限制
news = get_all_news(limit=30)
```

---

## 🔍 新闻分类算法

### 1. 关键词匹配
```python
# 检查标题和摘要中的关键词
text = f"{title} {summary}".lower()

for category, keywords in KEYWORD_CATEGORIES.items():
    score = sum(1 for kw in keywords if kw in text)
    
# 返回得分最高的分类
```

### 2. 重要性计算
```python
重要性分数 = 1  # 基础分数

# 包含重要关键词 +1
if any(keyword in text for keyword in IMPORTANT_KEYWORDS):
    分数 += 1

# 包含价格/市场相关 +1
if any(kw in text for kw in ["price", "market", "价格"]):
    分数 += 1

# 限制最高 5 分
return min(分数，5)
```

### 3. 去重算法
```python
# 简化标题（移除标点和空格）
simple_title = re.sub(r'[^a-z0-9]', '', title.lower())

# 检查是否已存在
if simple_title not in seen_titles:
    unique_news.append(news)
```

---

## 🌐 新闻源列表

### 加密货币（英文）
- CoinDesk
- Cointelegraph
- The Block
- Decrypt
- Bitcoin Magazine
- CryptoSlate

### 金融（英文）
- Bloomberg Crypto
- Reuters Business
- Financial Times

### 中文新闻源
- 金色财经
- 链闻

### 添加更多新闻源
在 `src/data/news_aggregator.py` 中添加：
```python
CRYPTO_NEWS_FEEDS.append({
    "name": "新新闻源",
    "url": "https://example.com/rss",
    "category": "crypto",
    "lang": "zh",
    "priority": 2,
})
```

---

## 🚨 突发新闻警报

### 工作原理
1. 扫描所有新闻的重要性分数
2. 筛选出分数 >= 4 的新闻
3. 显示在仪表板顶部
4. 红色边框 + 脉冲动画

### 触发条件
- 包含"紧急"、"突发"、"breaking"等词
- 价格暴涨暴跌（>10%）
- 黑客攻击/漏洞
- 监管禁令
- 交易所破产/清算

---

## 📊 集成到现有页面

### 方法 1：添加到侧边栏
```python
with st.sidebar:
    st.markdown("### 📰 实时新闻")
    render_news_panel(limit=10)
```

### 方法 2：添加到主内容区
```python
st.markdown("#### 📰 实时新闻")
render_news_panel(
    category="crypto",
    limit=20,
)
```

### 方法 3：作为独立标签页
```python
tabs = st.tabs(["仪表板", "新闻", "设置"])

with tabs[1]:
    render_news_panel()
```

---

## 🔧 故障排除

### 问题 1：无法获取新闻
```
解决方案：
1. 检查网络连接
2. 验证 RSS 源 URL 是否有效
3. 查看日志：logging.basicConfig(level=logging.INFO)
```

### 问题 2：feedparser 未安装
```bash
pip install feedparser
```

### 问题 3：缓存不更新
```python
# 手动清除缓存
from src.data.news_aggregator import news_aggregator
news_aggregator.cache.clear()
news_aggregator.feed_cache.clear()
```

---

## 📝 最佳实践

### 1. 合理使用自动刷新
```python
# ✅ 好：新闻刷新间隔较长
render_news_panel(auto_refresh=True, refresh_interval=120)

# ❌ 不好：刷新太频繁
render_news_panel(auto_refresh=True, refresh_interval=10)
```

### 2. 分类显示
```python
# 加密货币页面
render_news_panel(category="crypto", lang="all")

# 金融页面
render_news_panel(category="finance", lang="en")
```

### 3. 移动端优化
```python
# 限制显示数量
render_news_panel(limit=10)

# 隐藏摘要
render_news_panel(show_summary=False)
```

---

## 🎯 未来规划

### Phase 1 (已完成)
- ✅ RSS 新闻聚合
- ✅ 智能分类
- ✅ 重要性评分
- ✅ 基础 UI 组件

### Phase 2 (计划中)
- 🔄 AI 新闻摘要
- 🔄 语义搜索
- 🔄 个性化推荐

### Phase 3 (愿景)
- 🌐 WebSocket 实时推送
- 🌐 社交媒体整合（Twitter/Telegram）
- 🌐 新闻情绪分析

---

## 📚 参考资源

- [World Monitor GitHub](https://github.com/koala73/worldmonitor)
- [feedparser 文档](https://pythonhosted.org/feedparser/)
- [RSS 规范](https://www.rssboard.org/rss-specification)

---

**StocksX 新闻源功能** - 实时、专业、高密度的金融新闻聚合 📰
