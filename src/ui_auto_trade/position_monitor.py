"""
持倉監控 UI
============
顯示即時持倉狀態、損益追蹤和操作按鈕
"""

import time

import streamlit as st

from src.auth.user_db import UserDB


def render_position_monitor(user_id: int):
    """
    渲染持倉監控界面

    包含：
    - 持倉卡片
    - 損益圖表
    - 快速操作按鈕
    - 持倉統計
    """
    db = UserDB()

    st.markdown("### 💼 持倉監控")

    # 獲取持倉列表
    watchlist = db.get_watchlist(user_id)
    active_positions = [w for w in watchlist if w.get("position", 0) != 0]

    if not active_positions:
        st.info("ℹ️ 目前無活躍持倉")
        return

    # 持倉統計
    st.markdown("#### 📊 持倉統計")

    total_pnl = 0
    total_equity = 0
    long_count = 0
    short_count = 0

    for w in active_positions:
        pnl_pct = w.get("pnl_pct", 0)
        equity = w.get("initial_equity", 0)
        pnl_amount = equity * pnl_pct / 100
        total_pnl += pnl_amount
        total_equity += equity

        if w["position"] > 0:
            long_count += 1
        else:
            short_count += 1

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

    with stat_col1:
        delta_color = "normal" if total_pnl >= 0 else "inverse"
        stat_col1.metric(
            "總損益",
            f"${total_pnl:+,.2f}",
            delta=f"{total_pnl / total_equity * 100:+.2f}%" if total_equity > 0 else "0%",
            delta_color=delta_color,
        )

    with stat_col2:
        stat_col2.metric("總權益", f"${total_equity:,.2f}")

    with stat_col3:
        stat_col3.metric("🟢 多頭", f"{long_count} 檔")

    with stat_col4:
        stat_col4.metric("🔴 空頭", f"{short_count} 檔")

    st.divider()

    # 持倉卡片
    st.markdown("#### 📋 持倉明細")

    for idx, w in enumerate(active_positions):
        with st.container():
            # 持倉卡片邊框
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 12px;
                    padding: 20px;
                    margin: 10px 0;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0; font-size: 1.5rem;">{w["symbol"]}</h3>
                            <span style="color: #64748b; font-size: 0.9rem;">
                                {w.get("strategy", "N/A")} | {w.get("timeframe", "N/A")}
                            </span>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.8rem; font-weight: bold; color: {"#00cc96" if w.get("pnl_pct", 0) >= 0 else "#ef553b"};">
                                {w.get("pnl_pct", 0):+.2f}%
                            </div>
                            <div style="color: #64748b; font-size: 0.9rem;">
                                ${w.get("initial_equity", 0) * w.get("pnl_pct", 0) / 100:+,.2f}
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 持倉詳情
            detail_col1, detail_col2, detail_col3, detail_col4 = st.columns(4)

            with detail_col1:
                st.markdown("**方向**")
                if w["position"] > 0:
                    st.success("🟢 多頭")
                else:
                    st.error("🔴 空頭")

            with detail_col2:
                st.markdown("**進場價**")
                st.write(f"${w.get('entry_price', 0):,.2f}")

            with detail_col3:
                st.markdown("**初始資金**")
                st.write(f"${w.get('initial_equity', 0):,.2f}")

            with detail_col4:
                st.markdown("**槓桿**")
                st.write(f"{w.get('leverage', 1)}x")

            st.divider()

            # 操作按鈕
            st.markdown("**🎯 持倉操作**")
            action_col1, action_col2, action_col3, action_col4 = st.columns(4)

            with action_col1:
                if st.button("🔴 平倉", key=f"close_{w['id']}_{idx}", use_container_width=True):
                    # 平倉邏輯
                    from src.trading.executor import TradeExecutor

                    # 獲取交易所配置
                    strategies = db.get_auto_strategies(user_id)
                    if strategies:
                        config = strategies[0].get("config", {})
                        exchange_config = config.get("exchange", {})

                        try:
                            executor = TradeExecutor(
                                exchange_id=exchange_config.get("exchange_id", "binance"),
                                api_key=exchange_config.get("api_key"),
                                api_secret=exchange_config.get("api_secret"),
                                sandbox=exchange_config.get("sandbox", True),
                            )

                            # 執行平倉
                            side = "sell" if w["position"] > 0 else "buy"
                            current_price = w.get("last_price", w.get("entry_price", 1))
                            amount = w.get("initial_equity", 0) / current_price

                            result = executor.create_market_order(
                                symbol=w["symbol"],
                                side=side,
                                amount=amount,
                            )

                            if result.success:
                                # 記錄交易日誌
                                pnl = w.get("pnl_pct", 0)
                                db.log_trade(
                                    watch_id=w["id"],
                                    user_id=user_id,
                                    symbol=w["symbol"],
                                    action="平倉",
                                    side=w["position"],
                                    price=current_price,
                                    pnl_pct=pnl,
                                    reason="手動平倉",
                                )

                                # 更新持倉
                                db.update_watch(w["id"], position=0, entry_price=0, pnl_pct=0)

                                st.success(f"✅ 平倉成功！損益：${w.get('initial_equity', 0) * pnl / 100:+,.2f}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ 平倉失敗：{result.error}")
                        except Exception as e:
                            st.error(f"❌ 執行失敗：{e}")

            with action_col2:
                if w["position"] > 0:
                    btn_label = "🔄 反轉為空"
                else:
                    btn_label = "🔄 反轉為多"

                if st.button(btn_label, key=f"reverse_{w['id']}_{idx}", use_container_width=True):
                    st.info("🚧 反轉功能開發中")

            with action_col3:
                if st.button("⚙️ 調整停損", key=f"adjust_sl_{w['id']}_{idx}", use_container_width=True):
                    st.info("🚧 調整停損功能開發中")

            with action_col4:
                if st.button("📊 查看詳情", key=f"detail_{w['id']}_{idx}", use_container_width=True):
                    # 展開詳情
                    with st.expander("📊 交易明細"):
                        trades = db.get_trade_log(w["id"], limit=20)
                        if trades:
                            for t in trades:
                                pnl_color = "🟢" if t.get("pnl_amount", 0) >= 0 else "🔴"
                                st.write(
                                    f"{pnl_color} {t['action']} | "
                                    f"${t.get('pnl_amount', 0):+.2f} | "
                                    f"{t.get('created_at', 0)}"
                                )
                        else:
                            st.write("尚無交易記錄")


def render_single_position_card(watch: dict, idx: int, user_id: int):
    """
    渲染單一持倉卡片

    Args:
        watch: 持倉資訊
        idx: 索引
        user_id: 用戶 ID
    """

    pnl_pct = watch.get("pnl_pct", 0)
    pnl_amount = watch.get("initial_equity", 0) * pnl_pct / 100

    # 損益顏色
    if pnl_pct >= 0:
        pnl_color = "#00cc96"
        pnl_icon = "🟢"
    else:
        pnl_color = "#ef553b"
        pnl_icon = "🔴"

    # 方向图标
    if watch["position"] > 0:
        direction_icon = "🟢"
        direction_text = "多頭"
    else:
        direction_icon = "🔴"
        _direction_text = "空頭"

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border-left: 4px solid {pnl_color};
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; font-size: 1.2rem;">
                        {direction_icon} {watch["symbol"]}
                    </h4>
                    <span style="color: #64748b; font-size: 0.85rem;">
                        {watch.get("strategy", "N/A")}
                    </span>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: {pnl_color};">
                        {pnl_icon} {pnl_pct:+.2f}%
                    </div>
                    <div style="color: #64748b; font-size: 0.85rem;">
                        ${pnl_amount:+,.2f}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
