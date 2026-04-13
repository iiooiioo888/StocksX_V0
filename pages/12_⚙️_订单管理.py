# ════════════════════════════════════════════════════════════
# StocksX V0 - 高级订单管理页面
# 功能：条件单、OCO 订单、追踪止损
# ════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="高级订单管理 - StocksX", page_icon="⚙️", layout="wide")

# 自定义 CSS
st.markdown(
    """
<style>
    .order-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        border-left: 4px solid #667eea;
    }
    .order-status {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-pending { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
    .status-triggered { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
    .status-filled { background: rgba(16, 185, 129, 0.2); color: #10b981; }
    .status-cancelled { background: rgba(107, 114, 128, 0.2); color: #6b7280; }
</style>
""",
    unsafe_allow_html=True,
)

# ════════════════════════════════════════════════════════════
# 侧边栏配置
# ════════════════════════════════════════════════════════════

st.sidebar.title("⚙️ 订单配置")

# 选择订单类型
order_type = st.sidebar.selectbox("订单类型", ["📋 条件单", "🎯 OCO 订单", "📈 追踪止损", "📊 订单列表"])

# 交易对选择
st.sidebar.subheader("📊 交易配置")
symbol = st.sidebar.text_input("交易对/股票代码", "BTC/USDT")
side = st.sidebar.radio("方向", ["买入", "卖出"])
amount = st.sidebar.number_input("数量", 0.001, 1000.0, 0.1, 0.001)

# ════════════════════════════════════════════════════════════
# 条件单
# ════════════════════════════════════════════════════════════

if order_type == "📋 条件单":
    st.title("📋 条件单")
    st.markdown("**当触发条件满足时自动下单，支持价格、指标、时间等多种触发条件**")

    # 触发条件类型
    trigger_type = st.selectbox(
        "触发条件类型", ["💰 价格突破", "📊 指标交叉", "⏰ 时间到达", "📈 成交量异常", "💵 盈利达到", "📉 亏损达到"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if trigger_type == "💰 价格突破":
            price_condition = st.radio("条件", ["涨破", "跌破"])
            threshold_price = st.number_input("触发价格", 0.0, 1000000.0, 70000.0, 0.01)

        elif trigger_type == "📊 指标交叉":
            indicator = st.selectbox("指标", ["RSI", "MACD", "KDJ", "布林带", "均线"])
            cross_type = st.radio("交叉类型", ["上穿", "下穿"])
            threshold_value = st.number_input("阈值", 0.0, 100.0, 30.0, 0.1)

        elif trigger_type == "⏰ 时间到达":
            target_time = st.time_input("目标时间", datetime.now().time())

        elif trigger_type == "📈 成交量异常":
            volume_multiplier = st.slider("成交量倍数", 1.0, 10.0, 2.0, 0.1)

    with col2:
        # 订单类型
        order_subtype = st.selectbox("订单类型", ["市价单", "限价单", "止损单"])

        if order_subtype == "限价单":
            limit_price = st.number_input("限价", 0.0, 1000000.0, 70000.0, 0.01)

        # 过期时间
        expiry = st.checkbox("设置过期时间")
        if expiry:
            expiry_date = st.date_input("过期日期", datetime.now().date() + timedelta(days=7))

        # 备注
        note = st.text_area("备注", "")

    # 预览
    st.divider()
    st.subheader("📋 订单预览")

    st.info(f"""
    **交易对：** {symbol}
    **方向：** {side}
    **数量：** {amount}
    **触发条件：** {trigger_type}
    **订单类型：** {order_subtype}
    """)

    # 创建按钮
    if st.button("🚀 创建条件单", type="primary", use_container_width=True):
        st.success(f"✅ 条件单创建成功！\n\n交易对：{symbol}\n触发条件：{trigger_type}\n数量：{amount}")

        # 保存到 session state
        if "conditional_orders" not in st.session_state:
            st.session_state.conditional_orders = []

        st.session_state.conditional_orders.append(
            {
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "trigger_type": trigger_type,
                "created_at": datetime.now(),
                "status": "等待中",
            }
        )

# ════════════════════════════════════════════════════════════
# OCO 订单
# ════════════════════════════════════════════════════════════

elif order_type == "🎯 OCO 订单":
    st.title("🎯 OCO 订单")
    st.markdown("**一个成交另一个自动取消，适合设置止盈 + 止损**")

    st.subheader("📊 持仓信息")

    # 模拟持仓
    position = {
        "symbol": symbol,
        "side": "多头",
        "amount": amount,
        "entry_price": 65000,
        "current_price": 68000,
        "unrealized_pnl": 3000,
        "unrealized_pnl_pct": 4.62,
    }

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("入场价", f"${position['entry_price']:,.0f}")
    col2.metric("当前价", f"${position['current_price']:,.0f}")
    col3.metric("未实现盈亏", f"+${position['unrealized_pnl']:,.0f}", f"+{position['unrealized_pnl_pct']:.2f}%")
    col4.metric("数量", f"{position['amount']}")

    st.divider()
    st.subheader("⚙️ OCO 配置")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💰 止盈设置")
        take_profit_price = st.number_input("止盈价格", 0.0, 1000000.0, position["current_price"] * 1.05, 0.01)
        take_profit_type = st.selectbox("止盈类型", ["限价单", "市价单"])

        take_profit_pct = (take_profit_price - position["current_price"]) / position["current_price"] * 100
        st.info(f"预期盈利：+{take_profit_pct:.2f}%")

    with col2:
        st.markdown("#### 🛑 止损设置")
        stop_loss_price = st.number_input("止损价格", 0.0, 1000000.0, position["current_price"] * 0.95, 0.01)
        stop_loss_type = st.selectbox("止损类型", ["止损单", "止损限价单"])

        stop_loss_pct = (stop_loss_price - position["current_price"]) / position["current_price"] * 100
        st.error(f"预期亏损：{stop_loss_pct:.2f}%")

    # 盈亏比
    risk_reward_ratio = abs(take_profit_pct / stop_loss_pct) if stop_loss_pct != 0 else 0
    st.metric("盈亏比", f"{risk_reward_ratio:.2f}:1")

    # 过期时间
    expiry = st.checkbox("设置过期时间", value=False)
    if expiry:
        expiry_date = st.date_input("过期日期", datetime.now().date() + timedelta(days=30))

    st.divider()
    st.subheader("📋 订单预览")

    st.info(f"""
    **交易对：** {symbol}
    **持仓方向：** {position["side"]}
    **止盈价：** ${take_profit_price:,.0f} (+{take_profit_pct:.2f}%)
    **止损价：** ${stop_loss_price:,.0f} ({stop_loss_pct:.2f}%)
    **盈亏比：** {risk_reward_ratio:.2f}:1
    """)

    if st.button("🚀 创建 OCO 订单", type="primary", use_container_width=True):
        st.success(f"✅ OCO 订单创建成功！\n\n止盈：${take_profit_price:,.0f}\n止损：${stop_loss_price:,.0f}")

        if "oco_orders" not in st.session_state:
            st.session_state.oco_orders = []

        st.session_state.oco_orders.append(
            {
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "take_profit": take_profit_price,
                "stop_loss": stop_loss_price,
                "created_at": datetime.now(),
                "status": "等待中",
            }
        )

# ════════════════════════════════════════════════════════════
# 追踪止损
# ════════════════════════════════════════════════════════════

elif order_type == "📈 追踪止损":
    st.title("📈 追踪止损")
    st.markdown("**止损价随价格移动，锁定盈利，让利润奔跑**")

    st.subheader("📊 持仓信息")

    # 模拟持仓
    position = {
        "symbol": symbol,
        "side": "多头",
        "amount": amount,
        "entry_price": 65000,
        "current_price": 68000,
        "highest_price": 70000,
    }

    col1, col2, col3 = st.columns(3)
    col1.metric("入场价", f"${position['entry_price']:,.0f}")
    col2.metric("最高价", f"${position['highest_price']:,.0f}")
    col3.metric("当前价", f"${position['current_price']:,.0f}")

    st.divider()
    st.subheader("⚙️ 追踪参数")

    # 追踪方式
    trail_type = st.radio("追踪方式", ["百分比追踪", "固定金额追踪"])

    if trail_type == "百分比追踪":
        trail_percent = st.slider("追踪百分比", 0.5, 20.0, 5.0, 0.5)
        st.info(f"当前价格回调 {trail_percent}% 时触发止损")

        # 计算止损价
        current_stop = position["highest_price"] * (1 - trail_percent / 100)
        st.metric("当前止损价", f"${current_stop:,.0f}")

    else:
        trail_amount = st.number_input("追踪金额", 0.0, 10000.0, 3000.0, 100.0)

        # 计算止损价
        current_stop = position["highest_price"] - trail_amount
        st.metric("当前止损价", f"${current_stop:,.0f}")

    # 最低触发价
    min_trigger = st.checkbox("设置最低触发价")
    if min_trigger:
        min_price = st.number_input("最低触发价", 0.0, 1000000.0, 65000.0, 0.01)

    # 过期时间
    expiry = st.checkbox("设置过期时间", value=False)

    st.divider()
    st.subheader("📊 模拟演示")

    # 模拟价格变化
    st.write("**价格变化时的止损价调整：**")

    test_prices = [68000, 69000, 70000, 71000, 70000, 69000]

    demo_data = []
    highest = position["highest_price"]
    for price in test_prices:
        if price > highest:
            highest = price
        stop = highest * (1 - trail_percent / 100) if trail_type == "百分比追踪" else highest - trail_amount
        demo_data.append(
            {
                "市场价格": f"${price:,}",
                "最高价": f"${highest:,}",
                "止损价": f"${stop:,.0f}",
                "状态": "✅ 持仓中" if price > stop else "❌ 已触发",
            }
        )

    demo_df = pd.DataFrame(demo_data)
    st.table(demo_df)

    if st.button("🚀 创建追踪止损", type="primary", use_container_width=True):
        st.success(f"✅ 追踪止损创建成功！\n\n追踪方式：{trail_type}\n当前止损价：${current_stop:,.0f}")

        if "trailing_stops" not in st.session_state:
            st.session_state.trailing_stops = []

        st.session_state.trailing_stops.append(
            {
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "trail_type": trail_type,
                "trail_value": trail_percent if trail_type == "百分比追踪" else trail_amount,
                "current_stop": current_stop,
                "created_at": datetime.now(),
                "status": "运行中",
            }
        )

# ════════════════════════════════════════════════════════════
# 订单列表
# ════════════════════════════════════════════════════════════

elif order_type == "📊 订单列表":
    st.title("📊 订单列表")
    st.markdown("**管理所有活跃的历史订单**")

    # 选项卡
    tab1, tab2, tab3 = st.tabs(["⏳ 活跃订单", "✅ 历史订单", "📊 统计"])

    with tab1:
        st.subheader("活跃订单")

        # 模拟活跃订单
        active_orders = [
            {
                "类型": "条件单",
                "交易对": "BTC/USDT",
                "方向": "买入",
                "数量": "0.1",
                "触发条件": "价格涨破 $70,000",
                "创建时间": "2026-03-19 14:30",
                "状态": "等待中",
            },
            {
                "类型": "OCO",
                "交易对": "ETH/USDT",
                "方向": "卖出",
                "数量": "1.0",
                "止盈/止损": "$3,800 / $3,200",
                "创建时间": "2026-03-19 13:15",
                "状态": "等待中",
            },
            {
                "类型": "追踪止损",
                "交易对": "BTC/USDT",
                "方向": "卖出",
                "数量": "0.5",
                "追踪": "5% (当前止损 $66,500)",
                "创建时间": "2026-03-19 12:00",
                "状态": "运行中",
            },
        ]

        if active_orders:
            for i, order in enumerate(active_orders):
                with st.container():
                    st.markdown(
                        f"""
                    <div class="order-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0 0 8px 0;">
                                    {order["类型"]} - {order["交易对"]} {order["方向"]}
                                </h4>
                                <p style="margin: 0; color: #9ca3af; font-size: 0.9rem;">
                                    数量：{order["数量"]} |
                                    {order.get("触发条件", order.get("止盈/止损", order.get("追踪", "")))} |
                                    创建：{order["创建时间"]}
                                </p>
                            </div>
                            <div>
                                <span class="order-status status-pending">{order["状态"]}</span>
                            </div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # 操作按钮
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if st.button("👁️ 查看详情", key=f"view_{i}"):
                            st.json(order)
                    with col2:
                        if st.button("❌ 取消", key=f"cancel_{i}", type="secondary"):
                            st.success(f"已取消订单 #{i + 1}")
        else:
            st.info("暂无活跃订单")

    with tab2:
        st.subheader("历史订单")

        # 模拟历史订单
        history_data = {
            "订单 ID": ["#001", "#002", "#003", "#004"],
            "类型": ["条件单", "OCO", "追踪止损", "条件单"],
            "交易对": ["BTC/USDT", "ETH/USDT", "BTC/USDT", "SOL/USDT"],
            "方向": ["买入", "卖出", "卖出", "买入"],
            "数量": ["0.1", "1.0", "0.5", "10"],
            "触发价": ["$68,000", "$3,500", "$65,000", "$140"],
            "状态": ["✅ 已成交", "✅ 已成交", "✅ 已成交", "❌ 已取消"],
            "创建时间": ["2026-03-18", "2026-03-17", "2026-03-16", "2026-03-15"],
        }

        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📊 订单统计")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("总订单数", "24")
        col2.metric("活跃订单", "3")
        col3.metric("已成交", "18", "+75%")
        col4.metric("已取消", "3", "-12.5%")

        st.divider()

        # 成功率统计
        st.markdown("#### 订单成功率")
        success_rate = 75.0
        st.progress(success_rate / 100)
        st.write(f"**{success_rate:.1f}%** (18/24)")

# ════════════════════════════════════════════════════════════
# 使用说明
# ════════════════════════════════════════════════════════════

st.divider()
with st.expander("📖 使用说明"):
    st.markdown("""
    ### 条件单
    - **用途**：当特定条件满足时自动下单
    - **场景**：突破交易、定时定投、指标信号
    - **触发条件**：价格、指标、时间、成交量、盈亏

    ### OCO 订单
    - **用途**：同时设置止盈和止损，一个成交另一个自动取消
    - **场景**：持仓保护、突破交易
    - **优势**：无需时刻盯盘，自动风险管理

    ### 追踪止损
    - **用途**：止损价随价格移动，锁定盈利
    - **场景**：趋势跟踪、让利润奔跑
    - **参数**：百分比追踪或固定金额追踪

    ### 注意事项
    1. 条件单触发后以市价单或限价单提交
    2. OCO 订单需要持有相应仓位
    3. 追踪止损在极端行情下可能有滑点
    4. 所有订单都有过期时间，注意及时管理
    """)
