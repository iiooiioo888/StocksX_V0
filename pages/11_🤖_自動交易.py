"""
StocksX 自動交易配置頁面
========================
提供圖形化界面配置自動交易參數
整合完整 UI 模組
"""

import time

import streamlit as st

from src.auth.user_db import UserDB
from src.trading.worker import (
    check_position,
    daily_report,
    emergency_stop,
)
from src.ui_auto_trade import (
    render_auto_trading_dashboard,
    render_position_monitor,
    render_risk_manager_ui,
    render_strategy_configurator,
    render_trade_log_viewer,
)

st.set_page_config(
    page_title="自動交易 - StocksX",
    page_icon="🤖",
    layout="wide",
)

# 檢查登入狀態
user = st.session_state.get("user")
if not user:
    st.warning("🔐 請先登入")
    st.page_link("pages/1_🔐_登入.py", label="前往登入")
    st.stop()

db = UserDB()

# ════════════════════════════════════════════════════════════
# 頁面標題
# ════════════════════════════════════════════════════════════
st.title("🤖 自動交易")
st.markdown("完整的自動交易解決方案 - 策略配置、持倉監控、風險管理、交易日誌")

# ════════════════════════════════════════════════════════════
# 側邊欄 - 快速操作
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚡ 快速操作")

    # 緊急停止按鈕
    st.error("### 🚨 緊急控制")
    if st.button("🛑 緊急停止所有交易", use_container_width=True, type="primary"):
        result = emergency_stop.delay(user_id=user["id"])
        st.success("✅ 已發送緊急停止指令！")
        time.sleep(2)
        st.rerun()

    st.divider()

    # 生成每日報告
    if st.button("📊 生成每日報告", use_container_width=True):
        with st.spinner("正在生成報告..."):
            report = daily_report.delay(user_id=user["id"]).get(timeout=30)
            if report:
                st.success("✅ 報告已生成")
                with st.expander("查看報告"):
                    st.json(report)

    st.divider()

    # 查看持倉
    st.markdown("### 📈 持倉查詢")
    position_symbol = st.text_input("交易對", placeholder="BTC/USDT:USDT")
    if st.button("查詢持倉", use_container_width=True):
        if position_symbol:
            result = check_position.delay(user_id=user["id"], symbol=position_symbol)
            pos = result.get(timeout=10)
            if pos.get("found"):
                st.success("✅ 找到持倉")
                direction = "多頭" if pos["position"] > 0 else "空頭" if pos["position"] < 0 else "空倉"
                st.metric("持倉方向", direction)
                st.metric("進場價", f"${pos['entry_price']:,.2f}")
                st.metric("損益", f"{pos['pnl_pct']:+.2f}%")
            else:
                st.info("ℹ️ 無此持倉")

# ════════════════════════════════════════════════════════════
# 主內容區 - 使用 UI 模組
# ════════════════════════════════════════════════════════════

# 主分頁
main_tabs = st.tabs(
    [
        "📊 儀表板",
        "💼 持倉監控",
        "🤖 策略配置",
        "🛡️ 風險管理",
        "📜 交易日誌",
    ]
)

# ───────────────────────────────────────────────────────────
# Tab 1: 儀表板
# ───────────────────────────────────────────────────────────
with main_tabs[0]:
    render_auto_trading_dashboard(user["id"])

# ───────────────────────────────────────────────────────────
# Tab 2: 持倉監控
# ───────────────────────────────────────────────────────────
with main_tabs[1]:
    render_position_monitor(user["id"])

# ───────────────────────────────────────────────────────────
# Tab 3: 策略配置
# ───────────────────────────────────────────────────────────
with main_tabs[2]:
    render_strategy_configurator(user["id"])

# ───────────────────────────────────────────────────────────
# Tab 4: 風險管理
# ───────────────────────────────────────────────────────────
with main_tabs[3]:
    render_risk_manager_ui()

# ───────────────────────────────────────────────────────────
# Tab 5: 交易日誌
# ───────────────────────────────────────────────────────────
with main_tabs[4]:
    render_trade_log_viewer(user["id"])

# ════════════════════════════════════════════════════════════
# 頁尾提示
# ════════════════════════════════════════════════════════════
st.divider()

st.warning("""
⚠️ **風險提示**:

1. 自動交易涉及高風險，可能導致資金損失
2. 建議先使用測試網絡充分測試
3. 過去績效不代表未來表現
4. 請使用閒置資金投資
5. 隨時準備手動干預異常情況

**投資有風險，入市需謹慎**
""")
