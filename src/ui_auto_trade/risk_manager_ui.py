"""
風險管理 UI
============
圖形化風險管理工具與計算器
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional
from src.trading.risk_manager import RiskManager, RiskConfig


def render_risk_manager_ui():
    """
    渲染風險管理界面
    
    包含：
    - 風險計算器
    - 倉位計算
    - 停損/停利計算
    - 風險建議
    """
    st.markdown("### 🛡️ 風險管理工具")
    
    # 側邊欄 - 風險 preset
    with st.sidebar:
        st.markdown("#### 📋 風險 preset")
        
        risk_preset = st.radio(
            "選擇風險類型",
            options=["保守型", "穩健型", "積極型"],
            index=1,
        )
        
        if risk_preset == "保守型":
            st.info("""
            **保守型配置**
            - 每筆風險：0.5-1%
            - 停損：1-1.5%
            - 停利：2-3%
            - 槓桿：1-2x
            - 最大持倉：2-3
            """)
        elif risk_preset == "穩健型":
            st.info("""
            **穩健型配置**
            - 每筆風險：1-2%
            - 停損：2-3%
            - 停利：4-6%
            - 槓桿：3-5x
            - 最大持倉：3-5
            """)
        else:
            st.info("""
            **積極型配置**
            - 每筆風險：2-3%
            - 停損：3-5%
            - 停利：6-10%
            - 槓桿：5-10x
            - 最大持倉：5-8
            """)
    
    # Tab 分頁
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 風險計算器",
        "💰 倉位計算",
        "🛑 停損/停利",
        "📈 風險分析"
    ])
    
    with tab1:
        render_risk_calculator()
    
    with tab2:
        render_position_size_calculator()
    
    with tab3:
        render_stop_loss_take_profit_calculator()
    
    with tab4:
        render_risk_analysis()


def render_risk_calculator():
    """渲染風險計算器"""
    st.markdown("#### 📊 風險計算器")
    
    st.markdown("""
    計算單筆交易的風險報酬比和期望值
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**輸入參數**")

        entry_price = st.number_input(
            "進場價",
            min_value=0.0,
            value=50000.0,
            step=100.0,
            key="risk_calc_entry_price",
        )

        stop_loss_price = st.number_input(
            "停損價",
            min_value=0.0,
            value=49000.0,
            step=100.0,
            key="risk_calc_stop_loss",
        )

        take_profit_price = st.number_input(
            "停利價",
            min_value=0.0,
            value=52000.0,
            step=100.0,
            key="risk_calc_take_profit",
        )

        win_rate = st.slider(
            "預估勝率 (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            key="risk_calc_win_rate",
        )
    
    with col2:
        st.markdown("**計算結果**")
        
        # 計算風險報酬比
        risk = abs(entry_price - stop_loss_price) / entry_price * 100
        reward = abs(take_profit_price - entry_price) / entry_price * 100
        
        if risk > 0:
            risk_reward_ratio = reward / risk
        else:
            risk_reward_ratio = 0
        
        # 計算期望值
        win_rate_decimal = win_rate / 100
        expectancy = (win_rate_decimal * reward) - ((1 - win_rate_decimal) * risk)
        
        # 顯示結果
        st.metric("風險 (%)", f"{risk:.2f}%")
        st.metric("報酬 (%)", f"{reward:.2f}%")
        st.metric("風險報酬比", f"{risk_reward_ratio:.2f}")
        
        if expectancy >= 0:
            st.success(f"✅ 期望值：+{expectancy:.2f}% (正期望)")
        else:
            st.error(f"❌ 期望值：{expectancy:.2f}% (負期望)")
        
        # 建議
        st.divider()
        st.markdown("**📝 分析建議**")
        
        if risk_reward_ratio >= 2:
            st.success("✅ 風險報酬比良好 (≥ 2)")
        elif risk_reward_ratio >= 1:
            st.warning("⚠️ 風險報酬比普通 (1-2)")
        else:
            st.error("❌ 風險報酬比不佳 (< 1)")
        
        if expectancy > 0:
            st.success("✅ 正期望系統，長期可獲利")
        else:
            st.error("❌ 負期望系統，需要調整參數")


def render_position_size_calculator():
    """渲染倉位計算器"""
    st.markdown("#### 💰 倉位計算器")
    
    st.markdown("計算合適的倉位大小，控制單筆風險")
    
    # 選擇計算方法
    method = st.selectbox(
        "倉位計算方法",
        options=[
            "固定比例 (Fixed Fraction)",
            "凱利公式 (Kelly)",
            "固定金額 (Fixed Amount)",
        ],
        index=0,
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**輸入參數**")

        equity = st.number_input(
            "總資金 (USDT)",
            min_value=0.0,
            value=10000.0,
            step=100.0,
            key="position_equity",
        )

        entry_price = st.number_input(
            "進場價",
            min_value=0.0,
            value=50000.0,
            step=100.0,
            key="position_entry_price",
        )

        if method == "固定比例 (Fixed Fraction)":
            risk_pct = st.slider(
                "風險比例 (%)",
                min_value=0.5,
                max_value=5.0,
                value=2.0,
                step=0.5,
                key="position_risk_pct",
            )
        elif method == "凱利公式 (Kelly)":
            win_rate = st.slider(
                "勝率 (%)",
                min_value=0,
                max_value=100,
                value=50,
                step=5,
                key="position_win_rate",
            )
            win_loss_ratio = st.slider(
                "盈虧比",
                min_value=0.5,
                max_value=5.0,
                value=2.0,
                step=0.1,
                key="position_win_loss_ratio",
            )
            max_kelly = st.slider(
                "凱利上限 (%)",
                min_value=10,
                max_value=50,
                value=25,
                step=5,
                key="position_max_kelly",
            )
        else:
            fixed_amount_pct = st.slider(
                "固定比例 (%)",
                min_value=5,
                max_value=50,
                value=25,
                step=5,
                key="position_fixed_pct",
            )
    
    with col2:
        stop_loss_price = st.number_input(
            "停損價",
            min_value=0.0,
            value=49000.0,
            step=100.0,
            key="position_stop_loss",
        )

        leverage = st.number_input(
            "槓桿倍數",
            min_value=1.0,
            max_value=20.0,
            value=1.0,
            step=1.0,
            key="position_leverage",
        )
    
    with col3:
        st.markdown("**計算結果**")
        
        if method == "固定比例 (Fixed Fraction)":
            risk_amount = equity * (risk_pct / 100)
            price_diff = abs(entry_price - stop_loss_price)
            
            if price_diff > 0:
                position_size = risk_amount / price_diff
                position_value = position_size * entry_price
                leverage_needed = position_value / equity
                
                st.metric("風險金額", f"${risk_amount:.2f}")
                st.metric("建議倉位", f"{position_size:.4f}")
                st.metric("倉位價值", f"${position_value:,.2f}")
                st.metric("所需槓桿", f"{leverage_needed:.2f}x")
                
                # 檢查槓桿
                if leverage_needed > leverage:
                    st.warning(f"⚠️ 所需槓桿 ({leverage_needed:.2f}x) 超過設定 ({leverage}x)")
                else:
                    st.success("✅ 槓桿在安全範圍內")
            else:
                st.error("❌ 進場價與停損價相同")
        
        elif method == "凱利公式 (Kelly)":
            win_rate_decimal = win_rate / 100
            q = 1 - win_rate_decimal
            kelly = (win_rate_decimal * win_loss_ratio - q) / win_loss_ratio
            kelly = max(0, min(kelly, max_kelly / 100))
            
            position_size = (equity * kelly) / entry_price
            position_value = position_size * entry_price
            
            st.metric("凱利比例", f"{kelly * 100:.2f}%")
            st.metric("建議倉位", f"{position_size:.4f}")
            st.metric("倉位價值", f"${position_value:,.2f}")
            
            if kelly <= 0:
                st.warning("⚠️ 凱利公式建議不下注")
            elif kelly >= 0.25:
                st.warning(f"⚠️ 凱利比例過高 ({kelly*100:.2f}%)，已限制在 {max_kelly}%")
            else:
                st.success("✅ 凱利比例合理")
        
        else:
            amount = equity * (fixed_amount_pct / 100)
            position_size = amount / entry_price
            
            st.metric("投入金額", f"${amount:,.2f}")
            st.metric("建議倉位", f"{position_size:.4f}")
            st.metric("倉位價值", f"${position_size * entry_price:,.2f}")
    
    # 解釋
    with st.expander("📖 計算方法說明"):
        if method == "固定比例 (Fixed Fraction)":
            st.markdown("""
            **固定比例法**
            
            公式：`倉位 = (權益 × 風險%) / (進場價 - 停損價)`
            
            優點：
            - 簡單直觀
            - 風險可控
            - 適合大多數交易者
            
            缺點：
            - 未考慮勝率
            - 未考慮盈虧比
            """)
        
        elif method == "凱利公式 (Kelly)":
            st.markdown("""
            **凱利公式**
            
            公式：`f* = (p × b - q) / b`
            
            其中：
            - p = 勝率
            - q = 1 - p (失敗率)
            - b = 盈虧比
            
            優點：
            - 數學最優
            - 長期獲利最大化
            
            缺點：
            - 波動大
            - 需要準確的勝率估計
            - 建議使用半凱利或限制上限
            """)
        
        else:
            st.markdown("""
            **固定金額法**
            
            公式：`倉位 = 權益 × 固定比例 / 進場價`
            
            優點：
            - 最簡單
            - 易於執行
            
            缺點：
            - 未考慮風險
            - 可能過度暴露
            """)


def render_stop_loss_take_profit_calculator():
    """渲染停損/停利計算器"""
    st.markdown("#### 🛑 停損/停利計算器")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**輸入參數**")

        direction = st.radio(
            "交易方向",
            options=["多頭", "空頭"],
            index=0,
            key="stoploss_direction",
        )

        entry_price = st.number_input(
            "進場價",
            min_value=0.0,
            value=50000.0,
            step=100.0,
            key="stoploss_entry_price",
        )

        stop_loss_pct = st.slider(
            "停損 (%)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5,
            key="stoploss_pct",
        )

        take_profit_pct = st.slider(
            "停利 (%)",
            min_value=1.0,
            max_value=20.0,
            value=4.0,
            step=0.5,
            key="takeprofit_pct",
        )
    
    with col2:
        st.markdown("**計算結果**")
        
        if direction == "多頭":
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
            take_profit = entry_price * (1 + take_profit_pct / 100)
        else:
            stop_loss = entry_price * (1 + stop_loss_pct / 100)
            take_profit = entry_price * (1 - take_profit_pct / 100)
        
        risk_reward = take_profit_pct / stop_loss_pct
        
        st.metric("停損價", f"${stop_loss:,.2f}")
        st.metric("停利價", f"${take_profit:,.2f}")
        st.metric("風險報酬比", f"{risk_reward:.2f}")
        
        # 視覺化
        st.divider()
        st.markdown("**📊 損益示意圖**")
        
        if direction == "多頭":
            prices = [stop_loss, entry_price, take_profit]
            labels = ["停損", "進場", "停利"]
            colors = ["#ef553b", "#64748b", "#00cc96"]
        else:
            prices = [take_profit, entry_price, stop_loss]
            labels = ["停利", "進場", "停損"]
            colors = ["#00cc96", "#64748b", "#ef553b"]
        
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=labels,
            y=prices,
            mode="markers+text",
            marker={"size": 20, "color": colors},
            text=[f"${p:,.0f}" for p in prices],
            textposition="top center",
        ))
        
        fig.update_layout(
            title="停損/停利價格示意圖",
            yaxis_title="價格",
            height=300,
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 移動停損
    st.divider()
    st.markdown("**📈 移動停損計算**")
    
    trailing_enabled = st.toggle("啟用移動停損")
    
    if trailing_enabled:
        trailing_pct = st.slider(
            "移動停損 (%)",
            min_value=0.5,
            max_value=5.0,
            value=1.5,
            step=0.5,
            key="trailing_stop_pct",
        )
        
        if direction == "多頭":
            st.markdown(f"""
            **多頭移動停損**:
            - 價格每上漲 1%，停損價上調 1%
            - 停損價 = 最高價 × (1 - {trailing_pct}%)
            - 停損價只會上升，不會下降
            """)
        else:
            st.markdown(f"""
            **空頭移動停損**:
            - 價格每下跌 1%，停損價下調 1%
            - 停損價 = 最低價 × (1 + {trailing_pct}%)
            - 停損價只會下降，不會上升
            """)


def render_risk_analysis():
    """渲染風險分析"""
    st.markdown("#### 📈 風險分析工具")
    
    st.markdown("分析交易系統的風險特徵")
    
    # 輸入交易統計
    st.markdown("**交易統計**")

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

    with stat_col1:
        total_trades = st.number_input(
            "總交易數",
            min_value=1,
            value=100,
            key="risk_analysis_total_trades",
        )

    with stat_col2:
        win_rate = st.slider(
            "勝率 (%)",
            min_value=0,
            max_value=100,
            value=50,
            key="risk_analysis_win_rate",
        )

    with stat_col3:
        avg_win = st.number_input(
            "平均獲利 (%)",
            min_value=0.0,
            value=4.0,
            step=0.5,
            key="risk_analysis_avg_win",
        )

    with stat_col4:
        avg_loss = st.number_input(
            "平均虧損 (%)",
            min_value=0.0,
            value=2.0,
            step=0.5,
            key="risk_analysis_avg_loss",
        )
    
    # 計算
    st.divider()
    st.markdown("**分析結果**")
    
    # 期望值
    expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)
    
    # 盈虧比
    if avg_loss > 0:
        profit_factor = avg_win / avg_loss
    else:
        profit_factor = 0
    
    # 凱利比例
    win_rate_decimal = win_rate / 100
    if profit_factor > 0:
        kelly = (win_rate_decimal * profit_factor - (1 - win_rate_decimal)) / profit_factor
    else:
        kelly = 0
    
    # 顯示
    result_col1, result_col2, result_col3, result_col4 = st.columns(4)
    
    with result_col1:
        if expectancy >= 0:
            result_col1.success(f"✅ 期望值：+{expectancy:.2f}%")
        else:
            result_col1.error(f"❌ 期望值：{expectancy:.2f}%")
    
    with result_col2:
        if profit_factor >= 2:
            result_col2.success(f"✅ 盈虧比：{profit_factor:.2f}")
        elif profit_factor >= 1:
            result_col2.warning(f"⚠️ 盈虧比：{profit_factor:.2f}")
        else:
            result_col2.error(f"❌ 盈虧比：{profit_factor:.2f}")
    
    with result_col3:
        if kelly > 0:
            result_col3.info(f"📊 凱利比例：{kelly * 100:.2f}%")
        else:
            result_col3.warning(f"⚠️ 凱利比例：0% (不下注)")
    
    with result_col4:
        safe_kelly = kelly / 2  # 半凱利
        result_col4.metric("建議倉位", f"{safe_kelly * 100:.2f}%")
    
    # 風險評估
    st.divider()
    st.markdown("**📊 風險評估**")
    
    # 評分
    score = 0
    
    if expectancy > 0:
        score += 2
    if profit_factor >= 2:
        score += 2
    elif profit_factor >= 1:
        score += 1
    if win_rate >= 50:
        score += 1
    if kelly > 0:
        score += 1
    
    max_score = 6
    score_pct = score / max_score * 100
    
    # 顯示評分
    if score_pct >= 80:
        st.success(f"✅ 風險評分：{score}/{max_score} ({score_pct:.0f}%) - 優秀")
    elif score_pct >= 60:
        st.warning(f"⚠️ 風險評分：{score}/{max_score} ({score_pct:.0f}%) - 普通")
    else:
        st.error(f"❌ 風險評分：{score}/{max_score} ({score_pct:.0f}%) - 需改進")
    
    # 建議
    st.divider()
    st.markdown("**💡 改進建議**")
    
    if expectancy <= 0:
        st.error("""
        **期望值為負**:
        - 提高勝率
        - 提高盈虧比
        - 重新檢視策略
        """)
    
    if profit_factor < 1.5:
        st.warning("""
        **盈虧比偏低**:
        - 擴大停利
        - 縮小停損
        - 改善出場策略
        """)
    
    if win_rate < 40:
        st.warning("""
        **勝率偏低**:
        - 優化進場條件
        - 過濾假信號
        - 調整策略參數
        """)
