from typing import Optional

"""
现代化 UI 组件 - 基础组件

包含：
- 卡片容器
- 加载动画
- 错误提示
- 主题切换
"""

import streamlit as st

# ════════════════════════════════════════════════════════════
# CSS 样式
# ════════════════════════════════════════════════════════════

MODERN_CSS = """
<style>
/* 深色主题变量 */
:root {
    --bg-primary: #0a0e1a;
    --bg-secondary: #151a2d;
    --bg-card: rgba(21, 26, 45, 0.8);
    --text-primary: #ffffff;
    --text-secondary: #a0aec0;
    --accent-blue: #3b82f6;
    --accent-green: #10b981;
    --accent-red: #ef4444;
    --accent-orange: #f59e0b;
    --border-color: rgba(255, 255, 255, 0.1);
}

/* 主背景 */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #151a2d 100%);
}

/* 卡片样式 */
.modern-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.modern-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
    border-color: var(--accent-blue);
}

/* 统计卡片 */
.stat-card {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(21, 26, 45, 0.8) 100%);
    border: 1px solid var(--accent-blue);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.stat-value {
    font-size: 2em;
    font-weight: bold;
    color: var(--accent-blue);
    margin: 10px 0;
}

.stat-label {
    color: var(--text-secondary);
    font-size: 0.9em;
}

/* 加载动画 */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.loading-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border-color);
    border-top: 4px solid var(--accent-blue);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 骨架屏 */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.skeleton {
    background: linear-gradient(90deg,
        var(--bg-secondary) 0%,
        var(--border-color) 50%,
        var(--bg-secondary) 100%);
    background-size: 1000px 100%;
    animation: shimmer 2s infinite;
    border-radius: 8px;
    height: 20px;
}

/* 按钮样式 */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-blue) 0%, #2563eb 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

/* 成功提示 */
.success-box {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid var(--accent-green);
    border-radius: 8px;
    padding: 12px;
    color: var(--accent-green);
}

/* 警告提示 */
.warning-box {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid var(--accent-orange);
    border-radius: 8px;
    padding: 12px;
    color: var(--accent-orange);
}

/* 错误提示 */
.error-box {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid var(--accent-red);
    border-radius: 8px;
    padding: 12px;
    color: var(--accent-red);
}

/* 指标卡片 */
.metric-card {
    display: inline-block;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 15px 20px;
    margin: 5px;
    min-width: 150px;
}

.metric-value {
    font-size: 1.8em;
    font-weight: bold;
    color: var(--text-primary);
}

.metric-delta {
    font-size: 0.9em;
    margin-top: 5px;
}

.delta-up {
    color: var(--accent-green);
}

.delta-down {
    color: var(--accent-red);
}

/* 表格样式优化 */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
}

/* 隐藏默认 Streamlit 样式 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""


def inject_modern_css():
    """注入现代化 CSS 样式"""
    st.markdown(MODERN_CSS, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# 组件函数
# ════════════════════════════════════════════════════════════


def create_stat_card(title: str, value: str, delta: Optional[str] = None, icon: str = "📊") -> None:
    """
    创建统计卡片

    Args:
        title: 卡片标题
        value: 显示值
        delta: 变化值（如 "+5.2%"）
        icon: 图标 emoji
    """
    delta_class = ""
    if delta:
        if delta.startswith("+"):
            delta_class = "delta-up"
        elif delta.startswith("-"):
            delta_class = "delta-down"

    delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>' if delta else ""

    st.markdown(
        f"""
        <div class="metric-card">
            <div style="font-size: 0.8em; color: var(--text-secondary);">{icon} {title}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_loading_spinner(text: str = "加载中...") -> None:
    """创建加载动画"""
    st.markdown(
        f"""
        <div class="loading-spinner">
            <div class="spinner"></div>
            <div style="margin-left: 15px; color: var(--text-secondary);">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_skeleton(rows: int = 3) -> None:
    """创建骨架屏"""
    for _ in range(rows):
        st.markdown('<div class="skeleton" style="margin: 10px 0;"></div>', unsafe_allow_html=True)


def show_success(message: str) -> None:
    """显示成功提示"""
    st.markdown(f'<div class="success-box">✅ {message}</div>', unsafe_allow_html=True)


def show_warning(message: str) -> None:
    """显示警告提示"""
    st.markdown(f'<div class="warning-box">⚠️ {message}</div>', unsafe_allow_html=True)


def show_error(message: str) -> None:
    """显示错误提示"""
    st.markdown(f'<div class="error-box">❌ {message}</div>', unsafe_allow_html=True)


def create_modern_card(content: str, title: Optional[str] = None) -> None:
    """
    创建现代化卡片容器

    Args:
        content: 卡片内容（支持 Markdown/HTML）
        title: 可选标题
    """
    title_html = f'<h3 style="margin: 0 0 15px 0; color: var(--text-primary);">{title}</h3>' if title else ""

    st.markdown(
        f"""
        <div class="modern-card">
            {title_html}
            {content}
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_page_header(title: str, subtitle: Optional[str] = None, icon: str = "🚀") -> None:
    """
    创建页面标题

    Args:
        title: 主标题
        subtitle: 副标题
        icon: 图标 emoji
    """
    subtitle_html = f'<p style="color: var(--text-secondary); margin: 5px 0 0 0;">{subtitle}</p>' if subtitle else ""

    st.markdown(
        f"""
        <div style="padding: 20px 0; border-bottom: 1px solid var(--border-color); margin-bottom: 20px;">
            <h1 style="margin: 0; color: var(--text-primary);">{icon} {title}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════
# 主题配置
# ════════════════════════════════════════════════════════════


def setup_page_config(page_title: str = "StocksX", page_icon: str = "📈", layout: str = "wide"):
    """设置页面配置"""
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout, initial_sidebar_state="expanded")
    inject_modern_css()
