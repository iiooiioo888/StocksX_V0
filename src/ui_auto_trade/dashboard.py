"""
自動交易儀表板 UI
==================
顯示自動交易整體狀態、績效指標和快速操作
"""

import pandas as pd
import streamlit as st

from src.auth.user_db import UserDB


def render_auto_trading_dashboard(user_id: int):
    """
    渲染自動交易儀表板

    包含：
    - 整體績效指標
    - 持倉總覽
    - 策略狀態
    - 快速操作按鈕
    """
    db = UserDB()

    st.markdown("### 📊 自動交易儀表板")

    # 獲取數據
    watchlist = db.get_watchlist(user_id)
    strategies = db.get_auto_strategies(user_id)

    # 計算整體績效
    total_equity = sum(w.get("initial_equity", 0) for w in watchlist)
    total_pnl = 0
    winning_trades = 0
    total_trades = 0

    for w in watchlist:
        trades = db.get_trade_log(w["id"], limit=100)
        for t in trades:
            total_trades += 1
            pnl = t.get("pnl_amount", 0)
            total_pnl += pnl
            if pnl > 0:
                winning_trades += 1

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    # 儀表板指標
    st.markdown("#### 📈 整體績效")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        delta_color = "normal" if total_pnl >= 0 else "inverse"
        col1.metric(
            "總損益",
            f"${total_pnl:+,.2f}",
            delta=f"{total_pnl / total_equity * 100:+.2f}%" if total_equity > 0 else "0%",
            delta_color=delta_color,
        )

    with col2:
        col2.metric("總權益", f"${total_equity + total_pnl:,.2f}", delta=f"${total_equity:,.0f} 初始")

    with col3:
        active_positions = sum(1 for w in watchlist if w.get("position", 0) != 0)
        col3.metric("活躍持倉", f"{active_positions}", delta=f"{len(watchlist)} 總計")

    with col4:
        col4.metric("勝率", f"{win_rate:.1f}%", delta=f"{winning_trades}/{total_trades} 筆")

    with col5:
        active_strategies = sum(1 for s in strategies if s.get("is_active", 0) == 1)
        col5.metric("運行策略", f"{active_strategies}", delta=f"{len(strategies)} 總計")

    st.divider()

    # 持倉總覽表格
    st.markdown("#### 📋 持倉總覽")

    if not watchlist:
        st.info("ℹ️ 尚無持倉記錄")
    else:
        # 建立持倉數據框
        position_data = []
        for w in watchlist:
            if w.get("position", 0) != 0:
                position_data.append(
                    {
                        "交易對": w["symbol"],
                        "方向": "🟢 多頭" if w["position"] > 0 else "🔴 空頭",
                        "進場價": f"${w.get('entry_price', 0):,.2f}",
                        "當前價": f"${w.get('last_price', 0):,.2f}",
                        "損益": f"{w.get('pnl_pct', 0):+.2f}%",
                        "初始資金": f"${w.get('initial_equity', 0):,.0f}",
                        "策略": w.get("strategy", "N/A"),
                    }
                )

        if position_data:
            df = pd.DataFrame(position_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ 目前無活躍持倉")

    st.divider()

    # 策略狀態
    st.markdown("#### 🤖 策略狀態")

    if not strategies:
        st.info("ℹ️ 尚無自動策略配置")
    else:
        for idx, strategy in enumerate(strategies):
            config = strategy.get("config", {})
            is_active = strategy.get("is_active", 0) == 1

            with st.expander(
                f"{'🟢' if is_active else '⚪'} 策略 #{strategy['id']} - "
                f"{config.get('subscriptions', [{}])[0].get('symbol', 'Unknown')}",
                expanded=False,
            ):
                # 策略資訊
                info_col1, info_col2, info_col3 = st.columns(3)

                subs = config.get("subscriptions", [])
                sub_info = subs[0] if subs else {}

                info_col1.markdown("**交易所**")
                info_col1.write(f"{config.get('exchange', {}).get('exchange_id', 'N/A')}")

                info_col2.markdown("**交易對**")
                info_col2.write(f"{sub_info.get('symbol', 'N/A')}")

                info_col3.markdown("**策略**")
                info_col3.write(f"{sub_info.get('strategy', 'N/A')}")

                st.divider()

                # 風險參數
                risk = config.get("risk_management", {})
                risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)

                risk_col1.metric("每筆風險", f"{risk.get('risk_per_trade', 0) * 100:.1f}%")
                risk_col2.metric("停損", f"{risk.get('stop_loss_pct', 0):.1f}%")
                risk_col3.metric("停利", f"{risk.get('take_profit_pct', 0):.1f}%")
                risk_col4.metric("槓桿", f"{risk.get('leverage', 1)}x")

                st.divider()

                # 操作按鈕
                action_col1, action_col2, action_col3 = st.columns(3)

                with action_col1:
                    if is_active:
                        if st.button("⏹️ 停止", key=f"stop_strat_{strategy['id']}", use_container_width=True):
                            from src.trading.worker import stop_auto_trade

                            stop_auto_trade.delay(user_id=user_id, strategy_id=strategy["id"])
                            st.success("⏹️ 已發送停止指令")
                    else:
                        if st.button("▶️ 啟動", key=f"start_strat_{strategy['id']}", use_container_width=True):
                            from src.trading.worker import execute_auto_trade

                            execute_auto_trade.delay(
                                user_id=user_id,
                                strategy_id=strategy["id"],
                                duration_minutes=60,
                            )
                            st.success("▶️ 已啟動策略")

                with action_col2:
                    if st.button("📊 查看報告", key=f"report_strat_{strategy['id']}", use_container_width=True):
                        from src.trading.worker import daily_report

                        report = daily_report.delay(user_id=user_id).get(timeout=30)
                        if report:
                            st.json(report)

                with action_col3:
                    if st.button(
                        "🗑️ 刪除", key=f"del_strat_{strategy['id']}", use_container_width=True, type="secondary"
                    ):
                        db.delete_auto_strategy(strategy["id"])
                        st.success("✅ 已刪除")
                        st.rerun()

    st.divider()

    # 快速操作
    st.markdown("#### ⚡ 快速操作")

    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

    with quick_col1:
        if st.button("🛑 緊急停止所有交易", use_container_width=True, type="primary"):
            from src.trading.worker import emergency_stop

            result = emergency_stop.delay(user_id=user_id)
            st.success(f"🚨 已發送緊急停止指令！{result.get()}")
            st.rerun()

    with quick_col2:
        if st.button("📊 生成每日報告", use_container_width=True):
            from src.trading.worker import daily_report

            with st.spinner("正在生成報告..."):
                report = daily_report.delay(user_id=user_id).get(timeout=30)
                if report:
                    st.success("✅ 報告已生成")
                    st.expander("查看報告").json(report)

    with quick_col3:
        if st.button("🔄 重新整理", use_container_width=True):
            st.rerun()

    with quick_col4:
        if st.button("📥 匯出交易記錄", use_container_width=True):
            # 匯出 CSV
            all_trades = []
            for w in watchlist:
                trades = db.get_trade_log(w["id"], limit=100)
                all_trades.extend(trades)

            if all_trades:
                df = pd.DataFrame(all_trades)
                csv = df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 下載 CSV",
                    data=csv,
                    file_name=f"trade_log_{user_id}.csv",
                    mime="text/csv",
                )
