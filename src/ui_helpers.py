"""
StocksX 共用 UI 工具
減少頁面間的重複程式碼。
"""

from __future__ import annotations

import functools
import traceback
from typing import Any, TypeVar
from collections.abc import Callable

import streamlit as st

from src.utils.logger import get_logger

logger = get_logger("stocksx.ui")

F = TypeVar("F", bound=Callable[..., Any])


def require_login(redirect_page: str = "pages/1_🔐_登入.py"):
    """
    頁面登入保護裝飾器。
    未登入用戶會看到提示並被導向登入頁。
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user = st.session_state.get("user")
            if not user:
                st.warning("⚠️ 請先登入以使用此功能")
                st.page_link(redirect_page, label="🔐 前往登入", icon="🔐")
                st.stop()
            return func(*args, **kwargs)

        return wrapper

    return decorator


def safe_execute(func: F) -> F:
    """
    安全執行裝飾器，捕獲異常並顯示友善錯誤訊息。
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("Error in %s: %s", func.__name__, e, exc_info=True)
            st.error(f"❌ 操作失敗：{e!s}")
            with st.expander("🔍 錯誤詳情（開發者）"):
                st.code(traceback.format_exc())
            return None

    return wrapper


def render_metric_row(items: list[dict[str, Any]], columns: int = 4):
    """
    渲染一行指標卡片。

    Args:
        items: [{"label": str, "value": str, "delta": str}, ...]
        columns: 每行幾列
    """
    cols = st.columns(columns)
    for i, item in enumerate(items):
        with cols[i % columns]:
            st.metric(
                label=item.get("label", ""),
                value=item.get("value", ""),
                delta=item.get("delta"),
                delta_color=item.get("delta_color", "normal"),
            )


def render_status_card(
    title: str,
    value: str,
    status: str = "info",
    icon: str = "📊",
):
    """
    渲染狀態卡片。

    Args:
        title: 標題
        value: 值
        status: info/success/warning/error
        icon: 圖標
    """
    colors = {
        "info": "#6ea8fe",
        "success": "#00cc96",
        "warning": "#ffa15a",
        "error": "#ef553b",
    }
    color = colors.get(status, colors["info"])

    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15),
                                          rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.05));
        border: 1px solid {color}33;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    ">
        <div style="font-size: 1.8rem;">{icon}</div>
        <div style="font-size: 1.3rem; font-weight: 700; color: {color}; margin: 8px 0;">{value}</div>
        <div style="font-size: 0.85rem; color: #94a3b8;">{title}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_empty_state(message: str = "暫無數據", icon: str = "📭"):
    """渲染空狀態提示。"""
    st.markdown(
        f"""
    <div style="text-align: center; padding: 40px; color: #64748b;">
        <div style="font-size: 3rem; margin-bottom: 16px;">{icon}</div>
        <div style="font-size: 1.1rem;">{message}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_loading_placeholder(text: str = "載入中..."):
    """渲染載入佔位符。"""
    with st.spinner(text):
        st.empty()


def format_number(value: float, decimals: int = 2, prefix: str = "", suffix: str = "") -> str:
    """
    智能數字格式化。

    Examples:
        format_number(1234567) -> "1.23M"
        format_number(1234) -> "1,234"
        format_number(0.12345) -> "0.123"
    """
    if abs(value) >= 1_000_000_000:
        return f"{prefix}{value / 1_000_000_000:.{decimals}f}B{suffix}"
    elif abs(value) >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.{decimals}f}M{suffix}"
    elif abs(value) >= 1_000:
        return f"{prefix}{value:,.{decimals}f}{suffix}"
    elif abs(value) >= 1:
        return f"{prefix}{value:.{decimals}f}{suffix}"
    else:
        return f"{prefix}{value:.6f}{suffix}"


def format_pct(value: float, show_sign: bool = True) -> str:
    """格式化百分比。"""
    sign = "+" if value > 0 and show_sign else ""
    return f"{sign}{value:.2f}%"


def format_pnl_color(value: float) -> str:
    """根據損益返回顏色代碼。"""
    if value > 0:
        return "#00cc96"
    elif value < 0:
        return "#ef553b"
    return "#94a3b8"
