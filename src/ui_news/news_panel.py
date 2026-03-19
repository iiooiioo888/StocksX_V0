# 新闻面板 UI 组件（World Monitor 风格）
# 功能：紧凑新闻列表、分类显示、重要性标记

import time

import streamlit as st

from src.data.news_aggregator import (
    get_all_news,
    get_crypto_news,
    get_finance_news,
)

# ════════════════════════════════════════════════════════════
# CSS 样式（紧凑新闻卡片）
# ════════════════════════════════════════════════════════════
NEWS_CSS = """
/* 新闻容器 */
.news-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 600px;
    overflow-y: auto;
}

/* 新闻卡片 */
.news-card {
    background: rgba(22,27,34,0.6);
    border: 1px solid rgba(48,54,61,0.5);
    border-radius: 6px;
    padding: 10px 12px;
    transition: all 0.2s ease;
    cursor: pointer;
}

.news-card:hover {
    background: rgba(22,27,34,0.9);
    border-color: rgba(88,166,255,0.3);
    transform: translateX(2px);
}

/* 突发新闻（高重要性） */
.news-card.important {
    border-left: 3px solid #f85149;
    background: rgba(218,54,51,0.05);
}

.news-card.medium {
    border-left: 3px solid #d29922;
    background: rgba(210,153,34,0.05);
}

.news-card.normal {
    border-left: 3px solid #3fb950;
}

/* 新闻标题 */
.news-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #f0f6fc;
    margin-bottom: 6px;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.news-title a {
    color: #58a6ff;
    text-decoration: none;
}

.news-title a:hover {
    text-decoration: underline;
}

/* 新闻元数据 */
.news-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    color: #8b949e;
}

.news-source {
    font-weight: 600;
    color: #79c0ff;
}

.news-time {
    color: #8b949e;
}

.news-category {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
    background: rgba(56,139,253,0.15);
    color: #58a6ff;
}

/* 重要性徽章 */
.importance-badge {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
}

.importance-high {
    background: rgba(248,81,73,0.15);
    color: #f85149;
}

.importance-medium {
    background: rgba(210,153,34,0.15);
    color: #d29922;
}

.importance-low {
    background: rgba(63,185,80,0.15);
    color: #3fb950;
}

/* 摘要文本 */
.news-summary {
    font-size: 0.75rem;
    color: #8b949e;
    margin-top: 6px;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* 加载动画 */
.news-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    color: #8b949e;
    font-size: 0.85rem;
}

.news-loading::before {
    content: "";
    width: 16px;
    height: 16px;
    border: 2px solid rgba(88,166,255,0.2);
    border-top-color: #58a6ff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-right: 10px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* 无新闻提示 */
.no-news {
    text-align: center;
    padding: 40px 20px;
    color: #8b949e;
    font-size: 0.85rem;
}

/* 滚动条 */
.news-container::-webkit-scrollbar {
    width: 6px;
}

.news-container::-webkit-scrollbar-track {
    background: rgba(13,17,23,0.5);
}

.news-container::-webkit-scrollbar-thumb {
    background: rgba(48,54,61,0.8);
    border-radius: 3px;
}
"""


def render_news_panel(
    category: str = "all",
    lang: str = "en",
    limit: int = 20,
    show_summary: bool = False,
    auto_refresh: bool = True,
    refresh_interval: int = 60,
):
    """
    渲染新闻面板

    Args:
        category: 新闻类别 (all/crypto/finance)
        lang: 语言 (en/zh)
        limit: 显示数量
        show_summary: 显示摘要
        auto_refresh: 自动刷新
        refresh_interval: 刷新间隔（秒）
    """
    # 添加 CSS
    st.markdown(f"<style>{NEWS_CSS}</style>", unsafe_allow_html=True)

    # 标题和筛选器
    st.markdown("#### 📰 实时新闻")

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        news_category = st.selectbox(
            "类别",
            ["全部", "加密货币", "金融"],
            index=["全部", "加密货币", "金融"].index(
                "全部" if category == "all" else ("加密货币" if category == "crypto" else "金融")
            ),
            key="news_category_select",
        )
    with filter_col2:
        news_lang = st.selectbox(
            "语言",
            ["全部", "英文", "中文"],
            index=["全部", "英文", "中文"].index("全部" if lang == "all" else ("英文" if lang == "en" else "中文")),
            key="news_lang_select",
        )
    with filter_col3:
        news_limit = st.slider(
            "数量",
            min_value=5,
            max_value=50,
            value=limit,
            step=5,
            key="news_limit_slider",
        )

    # 映射筛选器
    category_map = {"全部": "all", "加密货币": "crypto", "金融": "finance"}
    lang_map = {"全部": "all", "英文": "en", "中文": "zh"}

    selected_category = category_map.get(news_category, category)
    selected_lang = lang_map.get(news_lang, lang)

    # 获取新闻
    with st.spinner("📰 加载新闻中..."):
        if selected_category == "crypto":
            news_list = get_crypto_news(limit=news_limit, lang=selected_lang)
        elif selected_category == "finance":
            news_list = get_finance_news(limit=news_limit, lang=selected_lang)
        else:
            news_list = get_all_news(limit=news_limit, lang=selected_lang)

    # 显示新闻
    if news_list:
        st.markdown('<div class="news-container">', unsafe_allow_html=True)

        for idx, news in enumerate(news_list):
            importance = news.get("importance", 1)
            importance_class = "important" if importance >= 4 else ("medium" if importance >= 3 else "normal")
            importance_text = "高" if importance >= 4 else ("中" if importance >= 3 else "低")
            importance_badge_class = (
                "importance-high" if importance >= 4 else ("importance-medium" if importance >= 3 else "importance-low")
            )

            # 格式化时间
            timestamp = news.get("timestamp", 0)
            time_ago = _format_time_ago(timestamp)

            # 新闻卡片
            st.markdown(
                f"""
            <div class="news-card {importance_class}" onclick="window.open('{news.get("link", "")}', '_blank')">
                <div class="news-title">
                    <a href="{news.get("link", "")}" target="_blank">{news.get("title", "")}</a>
                </div>
                <div class="news-meta">
                    <span class="news-source">{news.get("source", "")}</span>
                    <span>•</span>
                    <span class="news-time">{time_ago}</span>
                    <span>•</span>
                    <span class="news-category">{news.get("category", "general")}</span>
                    <span class="importance-badge {importance_badge_class}">
                        ⚡ {importance_text}
                    </span>
                </div>
                {f'<div class="news-summary">{news.get("summary", "")}</div>' if show_summary else ""}
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown(
            """
        <div class="no-news">
            📭 暂无新闻，请稍后再试
        </div>
        """,
            unsafe_allow_html=True,
        )

    # 自动刷新
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


def _format_time_ago(timestamp: float) -> str:
    """格式化相对时间"""
    import time

    now = time.time()
    diff = now - timestamp

    if diff < 60:
        return "刚刚"
    elif diff < 3600:
        return f"{int(diff / 60)}分钟前"
    elif diff < 86400:
        return f"{int(diff / 3600)}小时前"
    else:
        return f"{int(diff / 86400)}天前"


def render_news_ticker(symbols: list[str] = None, limit: int = 10):
    """
    渲染新闻滚动条（顶部）

    Args:
        symbols: 关注的交易对列表
        limit: 显示数量
    """
    # 获取相关新闻
    all_news = get_all_news(limit=limit * 2)

    # 筛选与关注交易对相关的新闻
    if symbols:
        filtered_news = []
        for news in all_news:
            title = news.get("title", "").lower()
            for symbol in symbols:
                if symbol.lower() in title:
                    filtered_news.append(news)
                    break
        news_to_show = filtered_news[:limit]
    else:
        news_to_show = all_news[:limit]

    if not news_to_show:
        return

    # 滚动条 CSS
    ticker_css = """
    <style>
    .news-ticker {
        background: rgba(22,27,34,0.9);
        border-bottom: 1px solid rgba(48,54,61,0.5);
        padding: 8px 0;
        overflow: hidden;
        white-space: nowrap;
    }

    .news-ticker-content {
        display: inline-block;
        animation: scroll 30s linear infinite;
    }

    .news-ticker-item {
        display: inline-block;
        padding: 0 20px;
        color: #8b949e;
        font-size: 0.85rem;
    }

    .news-ticker-item a {
        color: #58a6ff;
        text-decoration: none;
    }

    .news-ticker-item a:hover {
        text-decoration: underline;
    }

    @keyframes scroll {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    </style>
    """

    st.markdown(ticker_css, unsafe_allow_html=True)

    # 构建滚动内容
    items_html = ""
    for news in news_to_show:
        importance = news.get("importance", 1)
        importance_icon = "🔴" if importance >= 4 else ("🟡" if importance >= 3 else "⚪")
        items_html += f"""
        <div class="news-ticker-item">
            {importance_icon} <a href="{news.get("link", "")}" target="_blank">{news.get("title", "")}</a>
        </div>
        """

    # 重复一次以实现无缝滚动
    items_html += items_html

    st.markdown(
        f"""
    <div class="news-ticker">
        <div class="news-ticker-content">
            {items_html}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_breaking_news_alert(limit: int = 3):
    """
    渲染突发新闻警报

    Args:
        limit: 显示数量
    """
    all_news = get_all_news(limit=50)

    # 筛选高重要性新闻
    breaking_news = [n for n in all_news if n.get("importance", 1) >= 4][:limit]

    if not breaking_news:
        return

    st.markdown(
        """
    <style>
    .breaking-news {
        background: rgba(218,54,51,0.1);
        border: 1px solid rgba(218,54,51,0.3);
        border-left: 4px solid #f85149;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        animation: pulse-alert 2s infinite;
    }

    @keyframes pulse-alert {
        0%, 100% { background: rgba(218,54,51,0.1); }
        50% { background: rgba(218,54,51,0.15); }
    }

    .breaking-news-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #f85149;
        margin-bottom: 6px;
    }

    .breaking-news-item {
        font-size: 0.85rem;
        color: #f0f6fc;
        margin: 6px 0;
    }

    .breaking-news-item a {
        color: #58a6ff;
        text-decoration: none;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="breaking-news">', unsafe_allow_html=True)
    st.markdown('<div class="breaking-news-title">🚨 突发新闻</div>', unsafe_allow_html=True)

    for news in breaking_news:
        st.markdown(
            f"""
        <div class="breaking-news-item">
            🔴 <a href="{news.get("link", "")}" target="_blank">{news.get("title", "")}</a>
            <span style="color:#8b949e;font-size:0.75rem;margin-left:8px;">
                {news.get("source", "")} • {_format_time_ago(news.get("timestamp", 0))}
            </span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
