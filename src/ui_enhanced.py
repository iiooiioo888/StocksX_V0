# StocksX UI 增強模組
from __future__ import annotations

import time
from typing import Any

import streamlit as st

# ════════════════════════════════════════════════════════════
# 全局搜索功能
# ════════════════════════════════════════════════════════════


@st.cache_data(ttl=300, show_spinner=False)
def get_searchable_items() -> dict[str, list[dict[str, Any]]]:
    """取得可搜索的項目（快取 5 分鐘）"""
    from src.config import CRYPTO_CATEGORIES, STRATEGY_LABELS, TRADITIONAL_CATEGORIES

    items = {
        "symbols": [],
        "strategies": [],
        "pages": [
            {"name": "儀表板", "icon": "📊", "page": "/", "tags": ["首頁", "dashboard"]},
            {"name": "加密回測", "icon": "₿", "page": "/加密回測", "tags": ["加密貨幣", "backtest"]},
            {"name": "傳統回測", "icon": "🏛️", "page": "/傳統回測", "tags": ["股票", "ETF"]},
            {"name": "歷史記錄", "icon": "📜", "page": "/歷史", "tags": ["回測歷史"]},
            {"name": "策略監控", "icon": "📡", "page": "/監控", "tags": ["即時", "訂閱"]},
            {"name": "管理後台", "icon": "🛠️", "page": "/管理", "tags": ["admin"]},
            {"name": "市場新聞", "icon": "📰", "page": "/新聞", "tags": ["news"]},
            {"name": "健康檢查", "icon": "🏥", "page": "/健康檢查", "tags": ["系統", "監控"]},
        ],
    }

    # 加入交易對
    for category, symbols in CRYPTO_CATEGORIES.items():
        for symbol in symbols:
            items["symbols"].append(
                {
                    "name": symbol.split("/")[0],
                    "full_name": symbol,
                    "category": category,
                    "type": "crypto",
                    "tags": [symbol.split("/")[0], category],
                }
            )

    for category, symbols in TRADITIONAL_CATEGORIES.items():
        for symbol in symbols:
            items["symbols"].append(
                {
                    "name": symbol,
                    "full_name": symbol,
                    "category": category,
                    "type": "traditional",
                    "tags": [symbol, category],
                }
            )

    # 加入策略
    for key, label in STRATEGY_LABELS.items():
        items["strategies"].append({"name": label, "key": key, "type": "strategy", "tags": [label, key]})

    return items


def render_global_search():
    """渲染全局搜索"""

    search_results = st.session_state.get("search_results", [])

    def handle_search(query: str):
        if not query or len(query) < 2:
            st.session_state["search_results"] = []
            return

        items = get_searchable_items()
        results = []
        query_lower = query.lower()

        # 搜索交易對
        for sym in items["symbols"]:
            if (
                query_lower in sym["name"].lower()
                or query_lower in sym["full_name"].lower()
                or query_lower in sym["category"].lower()
                or any(query_lower in tag for tag in sym["tags"])
            ):
                results.append(
                    {
                        "type": "symbol",
                        "icon": "₿" if sym["type"] == "crypto" else "🏛️",
                        "title": sym["name"],
                        "subtitle": f"{sym['category']} - {sym['type']}",
                        "data": sym,
                    }
                )

        # 搜索策略
        for strat in items["strategies"]:
            if (
                query_lower in strat["name"].lower()
                or query_lower in strat["key"].lower()
                or any(query_lower in tag for tag in strat["tags"])
            ):
                results.append(
                    {
                        "type": "strategy",
                        "icon": "📊",
                        "title": strat["name"],
                        "subtitle": f"策略：{strat['key']}",
                        "data": strat,
                    }
                )

        # 搜索頁面
        for page in items["pages"]:
            if (
                query_lower in page["name"].lower()
                or query_lower in page["icon"]
                or any(query_lower in tag for tag in page["tags"])
            ):
                results.append(
                    {"type": "page", "icon": page["icon"], "title": page["name"], "subtitle": "頁面", "data": page}
                )

        st.session_state["search_results"] = results[:10]  # 限制顯示 10 筆

    # 搜索輸入框
    _search_query = st.text_input(
        "🔍 搜索",
        placeholder="輸入交易對、策略或頁面名稱...",
        label_visibility="collapsed",
        on_change=handle_search,
        args=(),
        key="global_search_input",
    )

    # 顯示搜索結果
    if search_results:
        with st.container():
            st.markdown(
                """
                <style>
                .search-result-item {
                    padding: 10px 15px;
                    margin: 5px 0;
                    background: rgba(30,30,55,0.8);
                    border: 1px solid rgba(110,168,254,0.2);
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .search-result-item:hover {
                    background: rgba(30,30,55,1);
                    border-color: rgba(110,168,254,0.5);
                    transform: translateX(5px);
                }
                </style>
            """,
                unsafe_allow_html=True,
            )

            for result in search_results:
                col1, col2, col3 = st.columns([1, 3, 2])
                with col1:
                    st.markdown(f"<div style='font-size:1.5rem'>{result['icon']}</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**{result['title']}**", unsafe_allow_html=True)
                    st.caption(result["subtitle"])
                with col3:
                    if result["type"] == "page":
                        if st.button("前往", key=f"search_{result['data']['page']}", use_container_width=True):
                            st.switch_page(result["data"]["page"])
                    elif result["type"] == "symbol":
                        if st.button("回測", key=f"search_bt_{result['data']['full_name']}", use_container_width=True):
                            # 儲存到 session，跳轉到回測頁面
                            st.session_state["quick_backtest_symbol"] = result["data"]
                            if result["data"]["type"] == "crypto":
                                st.switch_page("pages/2_₿_加密回測.py")
                            else:
                                st.switch_page("pages/2_🏛️_傳統回測.py")

            if st.button("清除搜索結果", key="clear_search"):
                st.session_state["search_results"] = []
                st.rerun()


# ════════════════════════════════════════════════════════════
# 快捷操作面板
# ════════════════════════════════════════════════════════════


def render_quick_actions():
    """渲染快捷操作"""
    st.markdown("#### ⚡ 快捷操作")

    # 常用回測快捷鍵
    quick_symbols = [
        {"symbol": "BTC/USDT:USDT", "name": "比特幣永續", "icon": "₿"},
        {"symbol": "ETH/USDT:USDT", "name": "以太幣永續", "icon": "Ξ"},
        {"symbol": "SOL/USDT:USDT", "name": "Solana 永續", "icon": "◎"},
        {"symbol": "AAPL", "name": "蘋果", "icon": "🍎"},
        {"symbol": "NVDA", "name": "NVIDIA", "icon": "🎮"},
        {"symbol": "TSLA", "name": "Tesla", "icon": "🚗"},
    ]

    cols = st.columns(6)
    for idx, item in enumerate(quick_symbols):
        col = cols[idx % 6]
        with col:
            if st.button(
                f"{item['icon']} {item['symbol']}",
                key=f"quick_{item['symbol']}",
                use_container_width=True,
                help=f"快速回測 {item['name']}",
            ):
                # 根據類型跳轉
                is_crypto = ":" in item["symbol"] or item["symbol"] in ["BTC/USDT", "ETH/USDT"]
                st.session_state["quick_backtest_symbol"] = {
                    "symbol": item["symbol"],
                    "type": "crypto" if is_crypto else "traditional",
                }
                if is_crypto:
                    st.switch_page("pages/2_₿_加密回測.py")
                else:
                    st.switch_page("pages/2_🏛️_傳統回測.py")


# ════════════════════════════════════════════════════════════
# 績效指標增強
# ════════════════════════════════════════════════════════════


def render_enhanced_metrics(history: list[dict[str, Any]]):
    """渲染增強的績效指標"""
    if not history:
        return

    # 計算進階指標
    total_trades = len(history)
    returns = [h.get("metrics", {}).get("total_return_pct", 0) for h in history]
    profitable_count = sum(1 for r in returns if r > 0)
    win_rate = profitable_count / total_trades * 100 if total_trades > 0 else 0

    # 計算 Sharpe Ratio
    if len(returns) > 1:
        import statistics

        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        sharpe = (avg_return / std_return * 2.52**0.5) if std_return > 0 else 0
    else:
        sharpe = 0

    # 計算最大連續虧損
    max_consecutive_loss = 0
    current_loss = 0
    for r in returns:
        if r < 0:
            current_loss += 1
            max_consecutive_loss = max(max_consecutive_loss, current_loss)
        else:
            current_loss = 0

    # 計算盈虧比
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r < 0]
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0
    profit_ratio = avg_win / avg_loss if avg_loss > 0 else 0

    # 顯示指標
    st.markdown("#### 📊 進階績效指標")

    metric_cols = st.columns(6)
    metric_cols[0].metric("🎯 勝率", f"{win_rate:.1f}%", delta=f"{profitable_count}/{total_trades}")
    metric_cols[1].metric("📈 Sharpe", f"{sharpe:.2f}", delta="年化" if sharpe > 1 else "注意風險")
    metric_cols[2].metric("⚖️ 盈虧比", f"{profit_ratio:.2f}", delta=f"{avg_win:.1f}% / {avg_loss:.1f}%")
    metric_cols[3].metric(
        "📉 最大連虧", f"{max_consecutive_loss}次", delta="風險警示" if max_consecutive_loss > 5 else "正常"
    )
    metric_cols[4].metric("💰 平均獲利", f"{avg_win:+.1f}%", delta=f"{len(wins)}次獲利")
    metric_cols[5].metric("💸 平均虧損", f"{-avg_loss:.1f}%", delta=f"{len(losses)}次虧損", delta_color="inverse")


# ════════════════════════════════════════════════════════════
# 策略對比功能
# ════════════════════════════════════════════════════════════


def render_strategy_comparison(results: dict[str, Any]):
    """渲染策略對比"""
    import plotly.graph_objects as go

    if not results:
        return

    # 準備數據
    strategies = []
    sharpe_ratios = []
    returns = []
    max_drawdowns = []
    win_rates = []

    for strategy_name, result in results.items():
        if result.error:
            continue

        strategies.append(strategy_name)
        metrics = result.metrics

        sharpe_ratios.append(metrics.get("sharpe", 0))
        returns.append(metrics.get("total_return_pct", 0))
        max_drawdowns.append(abs(metrics.get("max_drawdown_pct", 0)))

        # 計算勝率
        trades = result.trades
        if trades:
            wins = sum(1 for t in trades if t.get("pnl_pct", 0) > 0)
            win_rates.append(wins / len(trades) * 100)
        else:
            win_rates.append(0)

    if not strategies:
        return

    # 建立雷達圖
    fig = go.Figure()

    categories = ["報酬率%", "Sharpe", "最大回撤%", "勝率%"]

    for i, strategy in enumerate(strategies[:5]):  # 限制最多 5 個策略
        from src.config import STRATEGY_COLORS, STRATEGY_LABELS

        color = STRATEGY_COLORS.get(strategy, "#636EFA")
        label = STRATEGY_LABELS.get(strategy, strategy)

        values = [
            returns[i],
            sharpe_ratios[i] * 10,  # 放大 Sharpe 以便顯示
            -max_drawdowns[i],
            win_rates[i],
        ]

        fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill="toself", name=label, line=dict(color=color)))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[-50, 50])),
        showlegend=True,
        title=dict(text="🎯 策略對比雷達圖", font_size=14),
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# 市場數據自動刷新
# ════════════════════════════════════════════════════════════


def render_auto_refresh_market_data():
    """渲染自動刷新的市場數據"""
    from datetime import datetime

    # 上次更新時間
    if "market_data_last_update" not in st.session_state:
        st.session_state["market_data_last_update"] = time.time()

    # 每 60 秒自動刷新
    current_time = time.time()
    if current_time - st.session_state["market_data_last_update"] > 60:
        st.session_state["market_data_last_update"] = current_time
        # 清除快取
        if "cached_market_data" in st.session_state:
            del st.session_state["cached_market_data"]

    # 顯示上次更新時間
    last_update = datetime.fromtimestamp(st.session_state["market_data_last_update"])
    st.caption(f"🕐 上次更新：{last_update.strftime('%H:%M:%S')}")

    # 自動刷新按鈕
    if st.button("🔄 立即刷新", key="refresh_market"):
        if "cached_market_data" in st.session_state:
            del st.session_state["cached_market_data"]
        st.rerun()


# ════════════════════════════════════════════════════════════
# 用戶設定快捷方式
# ════════════════════════════════════════════════════════════


def render_user_settings_quick(user_id: int):
    """渲染用戶設定快捷方式"""
    from src.auth import UserDB

    db = UserDB()
    settings = db.get_settings(user_id)

    with st.expander("⚙️ 快速設定", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            default_equity = st.number_input(
                "預設初始資金", min_value=100.0, value=float(settings.get("default_equity", 10000)), step=500.0
            )
            default_leverage = st.number_input(
                "預設槓桿", min_value=1.0, max_value=125.0, value=float(settings.get("default_leverage", 1)), step=0.5
            )

        with col2:
            default_timeframe = st.selectbox(
                "預設時間框架",
                ["1m", "5m", "15m", "1h", "4h", "1d"],
                index=["1m", "5m", "15m", "1h", "4h", "1d"].index(settings.get("default_timeframe", "1h")),
            )
            theme = st.selectbox(
                "主題", ["dark", "light"], index=["dark", "light"].index(settings.get("theme", "dark"))
            )

        if st.button("💾 儲存設定", use_container_width=True):
            db.save_settings(
                user_id,
                {
                    "default_equity": default_equity,
                    "default_leverage": default_leverage,
                    "default_timeframe": default_timeframe,
                    "theme": theme,
                },
            )
            st.success("設定已儲存！")
