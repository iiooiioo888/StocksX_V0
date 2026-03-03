# StocksX 現代化 UI 元件庫
# 整合開源免費 UI 元件和現代化設計

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List, Optional


# ════════════════════════════════════════════════════════════
# 現代化 CSS 主題 - Glassmorphism + Neumorphism
# ════════════════════════════════════════════════════════════

MODERN_CSS = """
/* ════════════════════════════════════════════════════════════
   全局主題 - 深色玻璃擬態
   ════════════════════════════════════════════════════════════ */

/* 全局背景 - 漸變星空 */
.stApp {
    background: linear-gradient(135deg, 
        #0f0c29 0%, 
        #302b63 50%, 
        #24243e 100%);
    font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif;
}

/* 玻璃擬態卡片 */
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.glass-card:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

/* 霓虹漸變按鈕 */
.neon-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 12px;
    color: white;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    transition: all 0.3s ease;
}

.neon-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.neon-button:active {
    transform: translateY(0);
}

/* 發光指標卡片 */
.glow-metric {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
    border: 1px solid rgba(102, 126, 234, 0.3);
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
    transition: all 0.3s ease;
}

.glow-metric:hover {
    box-shadow: 0 6px 30px rgba(102, 126, 234, 0.4);
    transform: scale(1.02);
}

.glow-metric-value {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.glow-metric-label {
    font-size: 0.85rem;
    color: #94a3b8;
    margin-top: 6px;
    font-weight: 500;
}

/* 漸變分隔線 */
.gradient-divider {
    height: 2px;
    background: linear-gradient(90deg, 
        transparent 0%, 
        rgba(102, 126, 234, 0.5) 50%, 
        transparent 100%);
    margin: 20px 0;
    border: none;
}

/* 動畫效果 */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.7;
    }
}

@keyframes slideIn {
    from {
        transform: translateX(-100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.fade-in {
    animation: fadeIn 0.6s ease-out;
}

.pulse {
    animation: pulse 2s infinite;
}

.slide-in {
    animation: slideIn 0.5s ease-out;
}

/* 狀態標籤 */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.status-success {
    background: linear-gradient(135deg, rgba(0, 204, 150, 0.2), rgba(0, 204, 150, 0.1));
    color: #00cc96;
    border: 1px solid rgba(0, 204, 150, 0.3);
}

.status-warning {
    background: linear-gradient(135deg, rgba(255, 161, 90, 0.2), rgba(255, 161, 90, 0.1));
    color: #ffa15a;
    border: 1px solid rgba(255, 161, 90, 0.3);
}

.status-error {
    background: linear-gradient(135deg, rgba(239, 85, 59, 0.2), rgba(239, 85, 59, 0.1));
    color: #ef553b;
    border: 1px solid rgba(239, 85, 59, 0.3);
}

.status-info {
    background: linear-gradient(135deg, rgba(110, 168, 254, 0.2), rgba(110, 168, 254, 0.1));
    color: #6ea8fe;
    border: 1px solid rgba(110, 168, 254, 0.3);
}

/* 進度條 */
.modern-progress {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    overflow: hidden;
    position: relative;
}

.modern-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 10px;
    transition: width 0.5s ease;
    position: relative;
    overflow: hidden;
}

.modern-progress-bar::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    right: 0;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.3),
        transparent
    );
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* 輸入框美化 */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    color: #e0e0e8 !important;
    transition: all 0.3s ease;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: rgba(102, 126, 234, 0.6) !important;
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.2) !important;
}

/* 下拉選單美化 */
.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    color: #e0e0e8 !important;
}

/* 按鈕美化 */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    border: none !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
    transform: translateY(-2px) !important;
}

.stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: #e0e0e8 !important;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
}

/* 標籤頁美化 */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 6px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    padding: 10px 20px;
    border-radius: 12px;
    font-weight: 500;
    border: none !important;
    background: transparent !important;
    color: #94a3b8 !important;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #e0e0e8 !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

/* 展開區塊美化 */
.stExpander {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    margin-bottom: 10px !important;
}

.stExpander summary {
    color: #e0e0e8 !important;
    font-weight: 600 !important;
}

/* 表格美化 */
[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* 警告框美化 */
.stAlert {
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* 側邊欄美化 */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(15, 12, 41, 0.95), rgba(36, 36, 62, 0.95)) !important;
    backdrop-filter: blur(20px);
}

/* 自定義滾動條 */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2, #667eea);
}

/* 工具提示美化 */
[data-testid="stTooltipHoverTarget"] {
    color: #94a3b8;
}

/* 計量器美化 */
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    padding: 16px !important;
    transition: all 0.3s ease !important;
}

[data-testid="stMetric"]:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
    transform: translateY(-2px) !important;
}

[data-testid="stMetricValue"] {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}

[data-testid="stMetricDelta"] {
    font-weight: 600 !important;
}

/* 標題美化 */
h1, h2, h3, h4, h5, h6 {
    color: #f0f0ff !important;
    font-weight: 700 !important;
}

/* 連結美化 */
a {
    color: #6ea8fe !important;
    text-decoration: none !important;
    transition: all 0.3s ease !important;
}

a:hover {
    color: #667eea !important;
    text-shadow: 0 0 10px rgba(110, 168, 254, 0.5) !important;
}
"""


# ════════════════════════════════════════════════════════════
# UI 元件函數
# ════════════════════════════════════════════════════════════

def apply_modern_theme():
    """應用現代化主題"""
    st.markdown(f"<style>{MODERN_CSS}</style>", unsafe_allow_html=True)


def render_glass_card(content: str, hover: bool = True):
    """渲染玻璃擬態卡片"""
    st.markdown(f'<div class="glass-card">{content}</div>', unsafe_allow_html=True)


def render_glow_metric(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal"
):
    """渲染發光指標"""
    delta_html = ""
    if delta:
        delta_color_class = "status-success" if delta_color == "normal" and "+" in delta else "status-error"
        delta_html = f'<div class="status-badge {delta_color_class}" style="margin-top:8px;">{delta}</div>'

    st.markdown(f"""
    <div class="glow-metric">
        <div class="glow-metric-label">{label}</div>
        <div class="glow-metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str, type: str = "info"):
    """渲染狀態標籤"""
    type_map = {
        "success": "status-success",
        "warning": "status-warning",
        "error": "status-error",
        "info": "status-info"
    }
    badge_class = type_map.get(type, "status-info")
    st.markdown(f'<span class="status-badge {badge_class}">{status}</span>', unsafe_allow_html=True)


def render_gradient_divider():
    """渲染漸變分隔線"""
    st.markdown('<hr class="gradient-divider">', unsafe_allow_html=True)


def render_modern_progress(progress: float):
    """渲染現代化進度條"""
    progress = max(0, min(100, progress))
    st.markdown(f"""
    <div class="modern-progress">
        <div class="modern-progress-bar" style="width: {progress}%;"></div>
    </div>
    """, unsafe_allow_html=True)


def render_animated_text(text: str, animation: str = "fade-in"):
    """渲染動畫文字"""
    st.markdown(f'<div class="{animation}">{text}</div>', unsafe_allow_html=True)


def render_neon_button(label: str):
    """渲染霓虹按鈕（需配合 st.button 使用）"""
    # 注意：這只是一個樣式提示，實際按鈕仍需使用 st.button
    st.markdown(f'<button class="neon-button">{label}</button>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# 頁面佈局元件
# ════════════════════════════════════════════════════════════

def render_hero_banner(
    title: str,
    subtitle: str,
    stats: Optional[List[Dict[str, str]]] = None
):
    """渲染 Hero Banner"""
    stats_html = ""
    if stats:
        stats_items = "".join([
            f'<div class="glow-metric" style="min-width:120px;">'
            f'<div class="glow-metric-value">{s["value"]}</div>'
            f'<div class="glow-metric-label">{s["label"]}</div>'
            f'</div>'
            for s in stats
        ])
        stats_html = f'<div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:25px;">{stats_items}</div>'

    st.markdown(f"""
    <div class="glass-card" style="padding:40px;margin:20px 0 30px 0;">
        <h1 style="font-size:2.5rem;margin-bottom:10px;
            background:linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            {title}
        </h1>
        <p style="font-size:1.1rem;color:#94a3b8;margin-bottom:20px;">{subtitle}</p>
        {stats_html}
    </div>
    """, unsafe_allow_html=True)


def render_feature_grid(features: List[Dict[str, str]], columns: int = 3):
    """渲染功能網格"""
    cols = st.columns(columns)
    
    for idx, feature in enumerate(features):
        col = cols[idx % columns]
        with col:
            st.markdown(f"""
            <div class="glass-card" style="padding:20px;height:100%;">
                <div style="font-size:2.5rem;margin-bottom:10px;">{feature.get('icon', '📊')}</div>
                <h3 style="font-size:1.1rem;margin-bottom:8px;color:#f0f0ff;">{feature.get('title', '')}</h3>
                <p style="font-size:0.9rem;color:#94a3b8;line-height:1.6;">{feature.get('desc', '')}</p>
                {f'<div style="margin-top:10px;">{feature.get("tags", "")}</div>' if feature.get('tags') else ''}
            </div>
            """, unsafe_allow_html=True)


def render_info_card(
    title: str,
    content: str,
    icon: str = "ℹ️",
    type: str = "info"
):
    """渲染資訊卡片"""
    type_colors = {
        "info": "#6ea8fe",
        "success": "#00cc96",
        "warning": "#ffa15a",
        "error": "#ef553b"
    }
    color = type_colors.get(type, "#6ea8fe")
    
    st.markdown(f"""
    <div class="glass-card" style="border-left:4px solid {color};padding:20px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="font-size:1.5rem;">{icon}</span>
            <h3 style="color:{color};margin:0;">{title}</h3>
        </div>
        <p style="color:#94a3b8;line-height:1.6;">{content}</p>
    </div>
    """, unsafe_allow_html=True)
