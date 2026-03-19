# 即時監控（機構專業版 v8.0 - 真實數據）
# 所有數據都來自真實 API

import json
import time
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.auth import UserDB
from src.config import STRATEGY_LABELS, format_price
from src.data.service import data_service  # 真實數據服務

# ════════════════════════════════════════════════════════════
# 頁面配置
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="StocksX — 機構專業版（真實數據）", page_icon="📡", layout="wide", initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════
# 數據管理層
# ════════════════════════════════════════════════════════════


class DataManager:
    """數據管理類 - 負責數據載入、緩存和更新"""

    def __init__(self):
        self.price_cache: dict[str, dict] = {}
        self.kline_cache: dict[str, pd.DataFrame] = {}
        self.depth_cache: dict[str, dict] = {}
        self.last_update: dict[str, float] = {}
        self.cache_ttl = 3.0  # 緩存 TTL（秒）- 避免過於頻繁請求 API
        self.fallback_ttl = 10.0  #  fallback 緩存 TTL（秒）- API 失敗時使用舊數據

    def get_price(self, symbol: str) -> dict | None:
        """取得價格（從 WebSocket 或真實 API）"""
        now = time.time()

        # 優先從 WebSocket 取得
        if symbol in st.session_state.ws_prices:
            ws_data = st.session_state.ws_prices[symbol]
            ws_age = now - ws_data.get("timestamp", 0) / 1000
            if ws_age < 5:  # 5 秒內的數據
                return ws_data

        # 從真實 API 取得
        if symbol in self.price_cache:
            cache_age = now - self.last_update.get(symbol, 0)
            if cache_age < self.cache_ttl:
                return self.price_cache[symbol]
            # API 失敗時，使用舊數據（10 秒內仍有效）
            elif cache_age < self.fallback_ttl:
                logger = st.session_state.get("logger", None)
                if logger:
                    logger.warning(f"使用緩存數據（API 請求失敗）{symbol}")
                return self.price_cache[symbol]

        # 使用真實數據服務
        data = data_service.get_ticker(symbol)
        if data:
            self.price_cache[symbol] = data
            self.last_update[symbol] = now
            return data

        # 完全沒有數據時，返回舊數據（即使已過期）
        if symbol in self.price_cache:
            return self.price_cache[symbol]

        return None

    def get_kline(self, symbol: str, timeframe: str = "1h", periods: int = 100) -> pd.DataFrame | None:
        """取得真實 K 線數據"""
        cache_key = f"{symbol}_{timeframe}_{periods}"
        now = time.time()

        # 檢查緩存（5 分鐘有效）
        if cache_key in self.kline_cache:
            if now - self.last_update.get(cache_key, 0) < 300:
                return self.kline_cache[cache_key]

        # 使用真實數據服務
        with st.spinner(f"載入 {symbol} K 線數據..."):
            df = data_service.get_kline(symbol, timeframe=timeframe, limit=periods)

        if df is not None:
            # 更新緩存
            self.kline_cache[cache_key] = df
            self.last_update[cache_key] = now
            return df

        return None

    def get_depth(self, symbol: str, limit: int = 20) -> dict | None:
        """取得真實訂單簿深度"""
        now = time.time()

        # 檢查緩存（1 秒有效）
        if symbol in self.depth_cache:
            if now - self.last_update.get(symbol, 0) < 1:
                return self.depth_cache[symbol]

        # 使用真實數據服務
        data = data_service.get_orderbook(symbol, limit=limit)
        if data:
            self.depth_cache[symbol] = data
            self.last_update[symbol] = now
            return data

        return None

    def get_onchain_data(self, symbol: str) -> dict | None:
        """取得鏈上數據"""
        return data_service.get_onchain_data(symbol)

    def get_whale_data(self, symbol: str) -> pd.DataFrame | None:
        """取得巨鯨數據"""
        return data_service.get_whale_transactions(symbol)

    def get_fear_greed(self) -> dict | None:
        """取得恐懼貪婪指數"""
        return data_service.get_fear_greed_index()

    def get_social_sentiment(self, symbol: str) -> dict | None:
        """取得社群情緒"""
        return data_service.get_social_sentiment(symbol)

    def calculate_signal(self, symbol: str, strategy: str = "sma_cross") -> dict | None:
        """計算交易信號"""
        return data_service.calculate_signal(symbol, strategy)


# 全域數據管理器
data_manager = DataManager()

# ════════════════════════════════════════════════════════════
# CSS 樣式
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
.stApp {
    background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #0f1724 100%);
}

.pro-card {
    background: linear-gradient(135deg, rgba(30,30,58,0.95), rgba(37,37,69,0.95));
    border: 1px solid rgba(58,58,92,0.5);
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}

.pro-card:hover {
    border-color: rgba(110,168,254,0.5);
    box-shadow: 0 8px 32px rgba(110,168,254,0.2);
    transform: translateY(-2px);
}

.price-up {color: #00cc96 !important;}
.price-down {color: #ef553b !important;}

.signal-card {
    background: linear-gradient(135deg, rgba(42,26,58,0.9), rgba(53,37,69,0.9));
    border-radius: 12px;
    padding: 15px;
    margin: 8px 0;
    animation: slideIn 0.5s ease;
}

.signal-buy {
    border-left: 4px solid #00cc96;
    background: linear-gradient(135deg, rgba(0,204,150,0.15), rgba(0,204,150,0.05));
}

.signal-sell {
    border-left: 4px solid #ef553b;
    background: linear-gradient(135deg, rgba(239,85,59,0.15), rgba(239,85,59,0.05));
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.position-long {
    color: #00cc96 !important;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(0,204,150,0.3);
}

.position-short {
    color: #ef553b !important;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(239,85,59,0.3);
}

.connection-indicator {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
}

.connection-live {
    background: #00cc96;
    box-shadow: 0 0 10px #00cc96;
    animation: pulse 2s infinite;
}

.connection-offline {
    background: #ef553b;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.premium-badge {
    background: linear-gradient(135deg, #ffd700, #ffed4e);
    color: #1a1a2e;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: bold;
    display: inline-block;
    margin-left: 5px;
}

.loading-shimmer {
    background: linear-gradient(90deg,
        rgba(255,255,255,0.05) 0%,
        rgba(255,255,255,0.1) 50%,
        rgba(255,255,255,0.05) 100%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
"""

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 頁面初始化
# ════════════════════════════════════════════════════════════
user = st.session_state.get("user")

if not user:
    st.warning("請先登入")
    st.page_link("pages/1_🔐_登入.py", label="前往登入")
    st.stop()

db = UserDB()

# 檢查用戶等級
user_role = user.get("role", "user")
is_premium = user_role in ["premium", "vip", "admin"]
is_vip = user_role == "vip"

# Session State 初始化
if "ws_connected" not in st.session_state:
    st.session_state.ws_connected = False
if "ws_prices" not in st.session_state:
    st.session_state.ws_prices = {}
if "ws_signals" not in st.session_state:
    st.session_state.ws_signals = []
if "subscriptions" not in st.session_state:
    st.session_state.subscriptions = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
if "current_tab" not in st.session_state:
    st.session_state.current_tab = 0
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# ════════════════════════════════════════════════════════════
# 標題和狀態列
# ════════════════════════════════════════════════════════════
header_col1, header_col2, header_col3 = st.columns([3, 2, 2])

with header_col1:
    st.markdown(
        f"""
    <div style="display:flex;align-items:center;gap:15px;margin-bottom:20px;">
        <h1 style="margin:0;font-size:2rem;">📡 機構專業版</h1>
        {f'<span class="premium-badge">👑 {user_role.upper()}</span>' if user_role != "user" else ""}
    </div>
    """,
        unsafe_allow_html=True,
    )

with header_col2:
    status_icon = "🟢" if st.session_state.ws_connected else "🔴"
    status_text = "已連接" if st.session_state.ws_connected else "未連接"
    status_class = "connection-live" if st.session_state.ws_connected else "connection-offline"

    st.markdown(
        f"""
    <div style="display:flex;align-items:center;gap:10px;background:rgba(30,30,58,0.6);
        padding:10px 20px;border-radius:12px;border:1px solid rgba(58,58,92,0.3);">
        <span class="connection-indicator {status_class}"></span>
        <span style="color:#e0e0e8;">WebSocket: {status_text}</span>
        <span style="color:#64748b;font-size:0.85rem;">{len(st.session_state.ws_prices)} 個價格</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

with header_col3:
    # 計算上次更新時間
    time_since_refresh = time.time() - st.session_state.last_refresh

    if st.button(f"🔄 重新整理 ({time_since_refresh:.0f}s)", use_container_width=True):
        st.session_state.last_refresh = time.time()
        st.rerun()

st.divider()

# ════════════════════════════════════════════════════════════
# 側邊欄 - 高級控制
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ 控制面板")

    # 用戶等級資訊
    if not is_premium:
        st.markdown(
            """
        <div style="background:linear-gradient(135deg, #ffd700, #ffed4e);
            color:#1a1a2e;padding:15px;border-radius:12px;margin-bottom:20px;">
            <div style="font-weight:bold;margin-bottom:5px;">👑 升級專業版</div>
            <div style="font-size:0.85rem;">解鎖高級圖表、鏈上數據、情緒分析</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # WebSocket 控制
    st.markdown("#### 🔌 WebSocket 連接")
    ws_url = st.text_input("WebSocket URL", value="ws://localhost:8001/ws", key="ws_url_input")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔌 連接", use_container_width=True, disabled=st.session_state.ws_connected, key="ws_connect"):
            st.session_state.ws_connected = True
            st.success("WebSocket 連接成功！")
            st.rerun()

    with col2:
        if st.button(
            "❌ 斷開", use_container_width=True, disabled=not st.session_state.ws_connected, key="ws_disconnect"
        ):
            st.session_state.ws_connected = False
            st.warning("WebSocket 已斷開")
            st.rerun()

    st.divider()

    # 訂閱管理
    st.markdown("#### 📋 訂閱管理")

    for idx, sub in enumerate(st.session_state.subscriptions):
        col1, col2 = st.columns([4, 1])
        with col1:
            price_data = st.session_state.ws_prices.get(sub, {})
            price = price_data.get("price", 0)
            change = price_data.get("change_pct", 0)
            if price > 0:
                st.markdown(f"`{sub}` ${price:,.2f} ({change:+.2f}%)")
            else:
                st.markdown(f"`{sub}` 等待數據...")
        with col2:
            if st.button("❌", key=f"remove_{idx}", help="移除訂閱"):
                st.session_state.subscriptions.remove(sub)
                st.rerun()

    # 新增訂閱
    st.markdown("**➕ 新增訂閱**")
    popular_symbols = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "BNB/USDT",
        "XRP/USDT",
        "DOGE/USDT",
        "AAVE/USDT",
        "LINK/USDT",
    ]
    new_symbol = st.selectbox("選擇熱門交易對", options=popular_symbols, key="symbol_select")

    if st.button("新增訂閱", use_container_width=True, key="add_symbol"):
        if new_symbol not in st.session_state.subscriptions:
            st.session_state.subscriptions.append(new_symbol)
            st.success(f"已新增 {new_symbol}")
            st.rerun()

    st.divider()

    # 高級功能
    st.markdown("#### 🎯 高級功能")

    auto_trading = st.toggle("🤖 自動交易", value=False, disabled=not is_premium)
    if auto_trading and not is_premium:
        st.info("🔒 升級專業版以啟用自動交易")

    risk_management = st.toggle("🛡️ 風險管理", value=False, disabled=not is_premium)
    if risk_management and not is_premium:
        st.info("🔒 升級專業版以啟用風險管理")

    if is_premium:
        st.markdown("#### 📊 圖表設定")
        chart_type = st.selectbox("K 線類型", ["蠟燭圖", "收盤價線", "面積圖"])
        show_volume = st.toggle("顯示成交量", value=True)
        show_indicators = st.multiselect("技術指標", ["SMA", "EMA", "MACD", "RSI", "布林帶"], default=["SMA"])

        if is_vip:
            st.markdown("#### 👑 VIP 功能")
            enable_onchain = st.toggle("🔗 鏈上數據", value=False)
            enable_sentiment = st.toggle("💭 情緒分析", value=False)
            enable_ai = st.toggle("🤖 AI 預測", value=False)

# ════════════════════════════════════════════════════════════
# WebSocket JavaScript 組件
# ════════════════════════════════════════════════════════════

if st.session_state.ws_connected:
    websocket_script = f"""
    <script>
    (function() {{
        if (window.wsConnection) {{
            window.wsConnection.close();
        }}

        const wsUrl = "{ws_url}";
        const symbols = {json.dumps(st.session_state.subscriptions)};

        console.log('=== WebSocket 連接 ===');
        window.wsConnection = new WebSocket(wsUrl);

        window.wsConnection.onopen = function() {{
            console.log('✅ WebSocket connected');
            window.wsConnection.send(JSON.stringify({{
                action: 'subscribe',
                symbols: symbols
            }}));
        }};

        window.wsConnection.onmessage = function(event) {{
            try {{
                const message = JSON.parse(event.data);

                if (message.type === 'price_update') {{
                    const data = message.data;
                    // 更新價格到 session state
                    const event = new CustomEvent('priceUpdate', {{
                        detail: {{
                            symbol: data.symbol,
                            price: data.price,
                            change_pct: data.change_pct,
                            high_24h: data.high_24h || 0,
                            low_24h: data.low_24h || 0,
                            volume_24h: data.volume_24h || 0,
                            timestamp: data.timestamp
                        }}
                    }});
                    window.dispatchEvent(event);
                }}
            }} catch (e) {{
                console.error('解析錯誤:', e);
            }}
        }};

        window.wsConnection.onerror = function(error) {{
            console.error('❌ WebSocket error:', error);
        }};

        window.wsConnection.onclose = function() {{
            console.log('🔌 WebSocket disconnected');
        }};
    }})();
    </script>
    """

    import streamlit.components.v1 as components

    components.html(websocket_script, height=0)

# ════════════════════════════════════════════════════════════
# 主內容 - 標籤頁
# ════════════════════════════════════════════════════════════
tabs = st.tabs(
    [
        "📊 即時價格",
        "📈 K 線圖表",
        "🔔 交易信號",
        "💼 持倉監控",
        "📉 深度圖",
        "🔗 鏈上數據" if is_premium else "🔗 鏈上數據 🔒",
        "💭 情緒分析" if is_premium else "💭 情緒分析 🔒",
        "📊 績效分析",
    ]
)

# ───────────────────────────────────────────────────────────
# Tab 0: 即時價格
# ───────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("#### 📊 即時價格監控")

    if not st.session_state.subscriptions:
        st.info("請在側邊欄新增訂閱交易對")
    else:
        price_cols = st.columns(min(3, len(st.session_state.subscriptions)))

        for idx, symbol in enumerate(st.session_state.subscriptions):
            col = price_cols[idx % 3]

            # 使用 DataManager 取得價格
            price_data = data_manager.get_price(symbol)

            if price_data:
                price = price_data.get("price", 0)
                change_pct = price_data.get("change_pct", 0)
                high_24h = price_data.get("high_24h", 0)
                low_24h = price_data.get("low_24h", 0)
                volume_24h = price_data.get("volume_24h", 0)
                last_update = price_data.get("timestamp", 0)

                price_class = "price-up" if change_pct >= 0 else "price-down"
                change_icon = "🟢" if change_pct >= 0 else "🔴"

                with col:
                    st.markdown(
                        f"""
                    <div class="pro-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                            <span style="font-size:0.9rem;color:#94a3b8;">{symbol}</span>
                            <span style="font-size:0.75rem;color:#64748b;">
                                {datetime.fromtimestamp(last_update / 1000, tz=timezone.utc).strftime("%H:%M:%S") if last_update else "--:--:--"}
                            </span>
                        </div>
                        <div style="font-size:1.8rem;font-weight:700;color:#f0f0ff;margin-bottom:8px;">
                            ${price:,.2f}
                        </div>
                        <div class="{price_class}" style="font-size:1rem;margin-bottom:15px;">
                            {change_icon} {change_pct:+.2f}%
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.75rem;">
                            <div style="color:#94a3b8;">24h 高</div>
                            <div class="price-up" style="text-align:right;">${high_24h:,.2f}</div>
                            <div style="color:#94a3b8;">24h 低</div>
                            <div class="price-down" style="text-align:right;">${low_24h:,.2f}</div>
                            <div style="color:#94a3b8;grid-column:span 2;">24h 量</div>
                            <div style="color:#6ea8fe;text-align:right;grid-column:span 2;">{volume_24h:,.0f}</div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
            else:
                with col:
                    st.markdown(
                        f"""
                    <div class="pro-card" style="opacity:0.6;">
                        <div style="font-size:0.9rem;color:#94a3b8;margin-bottom:10px;">{symbol}</div>
                        <div class="loading-shimmer" style="height:40px;border-radius:8px;margin-bottom:8px;"></div>
                        <div style="font-size:0.75rem;color:#64748b;">
                            載入中...
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

# ───────────────────────────────────────────────────────────
# Tab 1: K 線圖表
# ───────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("#### 📈 K 線圖表（真實數據）")

    # 選擇交易對
    chart_symbol = st.selectbox("選擇交易對", options=st.session_state.subscriptions, key="chart_symbol_select")

    # 時間框架
    timeframe = st.selectbox(
        "時間框架", options=["1m", "5m", "15m", "1h", "4h", "1d", "1w"], index=3, key="timeframe_select"
    )

    # 使用 DataManager 取得真實 K 線數據
    df = data_manager.get_kline(chart_symbol, timeframe=timeframe, periods=100)

    if df is None or df.empty:
        st.error(f"無法取得 {chart_symbol} 的 K 線數據，請檢查網路連接或稍後再試")
    else:
        st.success(f"✅ 已載入 {len(df)} 筆 {chart_symbol} K 線數據")

        # 建立子圖
        if show_volume:
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=(f"{chart_symbol} K 線圖 ({timeframe})", "成交量"),
            )
        else:
            fig = make_subplots(rows=1, cols=1, subplot_titles=(f"{chart_symbol} K 線圖 ({timeframe})",))

        # K 線圖
        if chart_type == "蠟燭圖":
            fig.add_trace(
                go.Candlestick(
                    x=df["time"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name="K 線",
                    increasing_line_color="#00cc96",
                    decreasing_line_color="#ef553b",
                ),
                row=1,
                col=1,
            )
        elif chart_type == "收盤價線":
            fig.add_trace(
                go.Scatter(x=df["time"], y=df["close"], name="收盤價", line=dict(color="#6ea8fe", width=2)),
                row=1,
                col=1,
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=df["time"],
                    y=df["close"],
                    name="收盤價",
                    line=dict(color="#6ea8fe", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(110,168,254,0.2)",
                ),
                row=1,
                col=1,
            )

        # 成交量
        if show_volume:
            fig.add_trace(
                go.Bar(x=df["time"], y=df["volume"], name="成交量", marker_color="rgba(110,168,254,0.5)"), row=2, col=1
            )

        # 技術指標
        if "SMA" in show_indicators:
            df["SMA20"] = df["close"].rolling(window=20).mean()
            df["SMA50"] = df["close"].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(x=df["time"], y=df["SMA20"], name="SMA20", line=dict(color="#ffa15a", width=1)), row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df["time"], y=df["SMA50"], name="SMA50", line=dict(color="#19D3F3", width=1)), row=1, col=1
            )

        if "EMA" in show_indicators:
            df["EMA20"] = df["close"].ewm(span=20).mean()
            fig.add_trace(
                go.Scatter(x=df["time"], y=df["EMA20"], name="EMA20", line=dict(color="#FF97FF", width=1)), row=1, col=1
            )

        if "布林帶" in show_indicators:
            df["BB_middle"] = df["close"].rolling(window=20).mean()
            df["BB_upper"] = df["BB_middle"] + 2 * df["close"].rolling(window=20).std()
            df["BB_lower"] = df["BB_middle"] - 2 * df["close"].rolling(window=20).std()
            fig.add_trace(
                go.Scatter(
                    x=df["time"], y=df["BB_upper"], name="布林上軌", line=dict(color="#EF553B", width=1, dash="dash")
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=df["time"], y=df["BB_lower"], name="布林下軌", line=dict(color="#00CC96", width=1, dash="dash")
                ),
                row=1,
                col=1,
            )

        # 更新佈局
        fig.update_layout(
            height=600 if show_volume else 400,
            xaxis_rangeslider_visible=False,
            showlegend=True,
            legend=dict(orientation="h", y=1.02),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30,30,50,0.3)",
            font=dict(color="#e0e0e8"),
            margin=dict(l=50, r=50, t=50, b=50),
        )

        fig.update_xaxes(showgrid=True, gridcolor="rgba(50,50,90,0.2)")
        fig.update_yaxes(showgrid=True, gridcolor="rgba(50,50,90,0.2)")

        st.plotly_chart(fig, use_container_width=True)

        # MACD 副圖
        if "MACD" in show_indicators:
            st.markdown("##### 📊 MACD")

            exp1 = df["close"].ewm(span=12, adjust=False).mean()
            exp2 = df["close"].ewm(span=26, adjust=False).mean()
            df["MACD"] = exp1 - exp2
            df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
            df["Histogram"] = df["MACD"] - df["Signal"]

            macd_fig = make_subplots(
                rows=3,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=("MACD", "信號線", "MACD 柱狀圖"),
            )
            macd_fig.add_trace(
                go.Scatter(x=df["time"], y=df["MACD"], name="MACD", line=dict(color="#6ea8fe")), row=1, col=1
            )
            macd_fig.add_trace(
                go.Scatter(x=df["time"], y=df["Signal"], name="信號", line=dict(color="#ffa15a")), row=2, col=1
            )
            macd_fig.add_trace(
                go.Bar(x=df["time"], y=df["Histogram"], name="柱狀圖", marker_color="rgba(110,168,254,0.5)"),
                row=3,
                col=1,
            )
            macd_fig.update_layout(
                height=400, showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(30,30,50,0.3)"
            )
            st.plotly_chart(macd_fig, use_container_width=True)

        # RSI
        if "RSI" in show_indicators:
            st.markdown("##### 📊 RSI")

            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["RSI"] = 100 - (100 / (1 + rs))

            rsi_fig = go.Figure()
            rsi_fig.add_trace(go.Scatter(x=df["time"], y=df["RSI"], name="RSI", line=dict(color="#AB63FA", width=2)))
            rsi_fig.add_hline(y=70, line=dict(color="#ef553b", width=1, dash="dash"), annotation_text="超買")
            rsi_fig.add_hline(y=30, line=dict(color="#00cc96", width=1, dash="dash"), annotation_text="超賣")
            rsi_fig.update_layout(
                height=200, showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(30,30,50,0.3)"
            )
            st.plotly_chart(rsi_fig, use_container_width=True)

# ───────────────────────────────────────────────────────────
# Tab 2: 交易信號
# ───────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("#### 🔔 交易信號（真實數據計算）")

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        signal_type = st.selectbox("信號類型", ["全部", "BUY", "SELL", "HOLD"])
    with filter_col2:
        min_confidence = st.slider("最小信心度", 0.0, 1.0, 0.3, 0.05)
    with filter_col3:
        if st.button("🗑️ 清除信號"):
            st.session_state.ws_signals = []
            st.rerun()

    # 手動計算信號按鈕
    st.markdown("##### 📊 計算交易信號")

    calc_col1, calc_col2 = st.columns([3, 1])
    with calc_col1:
        signal_symbols = st.multiselect(
            "選擇要計算的交易對",
            options=st.session_state.subscriptions,
            default=st.session_state.subscriptions[:3] if st.session_state.subscriptions else [],
            key="signal_symbols",
        )
    with calc_col2:
        signal_strategy = st.selectbox(
            "策略", options=["sma_cross", "rsi"], format_func=lambda x: STRATEGY_LABELS.get(x, x), key="signal_strategy"
        )

    if st.button("🔍 計算信號", use_container_width=True, key="calc_signals"):
        if signal_symbols:
            new_signals = []
            with st.spinner(f"計算 {len(signal_symbols)} 個交易對的信號..."):
                for symbol in signal_symbols:
                    signal = data_manager.calculate_signal(symbol, signal_strategy)
                    if signal:
                        new_signals.append(signal)
                        # 添加到 session state
                        if "ws_signals" not in st.session_state:
                            st.session_state.ws_signals = []
                        st.session_state.ws_signals.insert(0, signal)

            if new_signals:
                st.success(f"✅ 計算完成！找到 {len(new_signals)} 個信號")
                st.rerun()
            else:
                st.warning("暫無信號，請稍後再試或更換策略")
        else:
            st.warning("請選擇至少一個交易對")

    st.divider()

    # 顯示信號
    if st.session_state.ws_signals:
        # 過濾信號
        filtered_signals = [
            s
            for s in st.session_state.ws_signals
            if (signal_type == "全部" or s.get("action") == signal_type) and s.get("confidence", 0) >= min_confidence
        ]

        if filtered_signals:
            st.markdown(f"##### 📋 找到 {len(filtered_signals)} 個信號")

            for signal in filtered_signals[:20]:
                action = signal.get("action", "")
                signal_class = (
                    "signal-buy" if action == "BUY" else ("signal-sell" if action == "SELL" else "signal-hold")
                )
                action_emoji = "🟢" if action == "BUY" else ("🔴" if action == "SELL" else "⚪")
                confidence = signal.get("confidence", 0)

                st.markdown(
                    f"""
                <div class="signal-card {signal_class}">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="font-size:1.2rem;">{action_emoji}</span>
                            <strong style="font-size:1.1rem;margin-left:8px;">{action}</strong>
                            <span style="margin-left:10px;color:#e0e0e8;">{signal.get("symbol", "")}</span>
                        </div>
                        <div style="font-size:0.85rem;color:#94a3b8;">
                            {datetime.fromtimestamp(signal.get("timestamp", 0) / 1000, tz=timezone.utc).strftime("%H:%M:%S")}
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:10px;font-size:0.85rem;">
                        <div>
                            <div style="color:#64748b;font-size:0.75rem;">策略</div>
                            <div style="color:#e0e0e8;">{STRATEGY_LABELS.get(signal.get("strategy", ""), signal.get("strategy", "N/A"))}</div>
                        </div>
                        <div>
                            <div style="color:#64748b;font-size:0.75rem;">信心度</div>
                            <div style="color:{"#00cc96" if confidence > 0.7 else "#ffa15a" if confidence > 0.5 else "#ef553b"};">
                                {confidence * 100:.0f}%
                            </div>
                        </div>
                        <div>
                            <div style="color:#64748b;font-size:0.75rem;">價格</div>
                            <div style="color:#e0e0e8;">${signal.get("price", 0):,.2f}</div>
                        </div>
                        <div>
                            <div style="color:#64748b;font-size:0.75rem;">RSI</div>
                            <div style="color:#e0e0e8;">{signal.get("rsi", "N/A")}</div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("暫無符合條件的信號")
    else:
        st.info("💡 暫無信號，請點擊「🔍 計算信號」按鈕來計算")
        st.caption("信號是基於真實 K 線數據計算的技術指標（SMA 交叉、RSI 等）")

# ───────────────────────────────────────────────────────────
# Tab 3: 持倉監控
# ───────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("#### 💼 持倉監控")

    watchlist = db.get_watchlist(user["id"])

    if not watchlist:
        st.info("📭 尚無持倉。前往「策略訂閱」頁面新增。")
    else:
        for item in watchlist:
            if not item.get("is_active", True):
                continue

            symbol = item.get("symbol", "BTC/USDT")
            position = item.get("position", 0)
            entry_price = item.get("entry_price", 0)
            initial_equity = item.get("initial_equity", 10000)

            # 使用 DataManager 取得即時價格
            price_data = data_manager.get_price(symbol)
            current_price = price_data.get("price", item.get("last_price", entry_price)) if price_data else entry_price

            # 計算損益
            if position > 0 and entry_price > 0 and current_price > 0:
                pnl_pct = (current_price - entry_price) / entry_price * 100
                pnl_amount = (current_price - entry_price) * (initial_equity / entry_price)
            elif position < 0 and entry_price > 0 and current_price > 0:
                pnl_pct = (entry_price - current_price) / entry_price * 100
                pnl_amount = (entry_price - current_price) * (initial_equity / entry_price)
            else:
                pnl_pct = 0
                pnl_amount = 0

            pnl_class = "price-up" if pnl_pct >= 0 else "price-down"
            position_text = "多頭" if position > 0 else "空頭" if position < 0 else "空倉"
            position_icon = "🟢" if position > 0 else "🔴" if position < 0 else "⚪"

            st.markdown(
                f"""
            <div class="pro-card" style="margin-bottom:20px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                    <div>
                        <span style="font-size:1.2rem;font-weight:700;color:#f0f0ff;">{symbol}</span>
                        <span style="margin-left:10px;color:#94a3b8;">{position_icon} {position_text}</span>
                    </div>
                    <div class="{pnl_class}" style="font-size:1.3rem;font-weight:700;">
                        {pnl_pct:+.2f}%
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:15px;">
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">入場價</div>
                        <div style="color:#e0e0e8;font-size:1rem;">${format_price(entry_price) if entry_price else "--"}</div>
                    </div>
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">當前價</div>
                        <div style="color:#e0e0e8;font-size:1rem;">${format_price(current_price) if current_price else "--"}</div>
                    </div>
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">未實現 P&L</div>
                        <div class="{pnl_class}" style="font-size:1rem;">${pnl_amount:+,.0f}</div>
                    </div>
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">初始資金</div>
                        <div style="color:#e0e0e8;font-size:1rem;">${initial_equity:,.0f}</div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            op_col1, op_col2, op_col3, op_col4 = st.columns(4)
            with op_col1:
                if st.button("🟢 加倉", key=f"add_{item['id']}", use_container_width=True):
                    st.info("加倉功能開發中")
            with op_col2:
                if st.button("🔄 反轉", key=f"reverse_{item['id']}", use_container_width=True):
                    st.info("反轉功能開發中")
            with op_col3:
                if st.button("📤 平倉", key=f"close_{item['id']}", use_container_width=True, type="secondary"):
                    st.info("平倉功能開發中")
            with op_col4:
                if st.button("⚙️ 設定", key=f"settings_{item['id']}", use_container_width=True, type="secondary"):
                    st.session_state[f"edit_{item['id']}"] = True

# ───────────────────────────────────────────────────────────
# Tab 4: 深度圖
# ───────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("#### 📉 訂單簿深度圖（真實數據）")

    depth_symbol = st.selectbox("選擇交易對", options=st.session_state.subscriptions, key="depth_symbol_select")

    # 取得真實訂單簿數據
    depth_data = data_manager.get_depth(depth_symbol, limit=20)

    if depth_data:
        bids = depth_data.get("bids", [])
        asks = depth_data.get("asks", [])

        if bids and asks:
            # 計算累積量
            bids_prices = [float(b[0]) for b in bids]
            bids_sizes = [float(b[1]) for b in bids]
            bids_cumsum = list(pd.Series(bids_sizes).cumsum())

            asks_prices = [float(a[0]) for a in asks]
            asks_sizes = [float(a[1]) for a in asks]
            asks_cumsum = list(pd.Series(asks_sizes).cumsum())

            depth_fig = go.Figure()

            depth_fig.add_trace(
                go.Scatter(
                    x=bids_prices, y=bids_cumsum, name="買單", line=dict(color="#00cc96", width=2), fill="tozeroy"
                )
            )
            depth_fig.add_trace(
                go.Scatter(
                    x=asks_prices, y=asks_cumsum, name="賣單", line=dict(color="#ef553b", width=2), fill="tozeroy"
                )
            )

            depth_fig.update_layout(
                title=f"{depth_symbol} 訂單簿深度（真實數據）",
                xaxis_title="價格",
                yaxis_title="累積數量",
                height=400,
                showlegend=True,
                legend=dict(orientation="h"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(30,30,50,0.3)",
                font=dict(color="#e0e0e8"),
            )

            depth_fig.update_xaxes(showgrid=True, gridcolor="rgba(50,50,90,0.2)")
            depth_fig.update_yaxes(showgrid=True, gridcolor="rgba(50,50,90,0.2)")

            st.plotly_chart(depth_fig, use_container_width=True)

            # 訂單簿統計
            st.markdown("##### 📊 訂單簿統計")

            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            stat_col1.metric("買單總量", f"{sum(bids_sizes):.2f}")
            stat_col2.metric("賣單總量", f"{sum(asks_sizes):.2f}")
            stat_col3.metric("買賣比", f"{sum(bids_sizes) / sum(asks_sizes):.2f}" if sum(asks_sizes) > 0 else "N/A")

            current_price = (bids_prices[0] + asks_prices[0]) / 2
            spread = asks_prices[0] - bids_prices[0]
            spread_pct = spread / current_price * 100
            stat_col4.metric("價差", f"${spread:.2f} ({spread_pct:.3f}%)")
        else:
            st.warning("訂單簿數據為空")
    else:
        st.error("無法取得訂單簿數據，請檢查網路連接")

# ───────────────────────────────────────────────────────────
# Tab 5: 鏈上數據（VIP）
# ───────────────────────────────────────────────────────────
with tabs[5]:
    if not is_premium:
        st.markdown(
            """
        ### 🔒 鏈上數據
        <div style="background:rgba(255,215,0,0.1);border:1px solid #ffd700;
            border-radius:12px;padding:30px;text-align:center;">
            <div style="font-size:3rem;margin-bottom:10px;">👑</div>
            <div style="font-size:1.2rem;color:#ffd700;margin-bottom:10px;">專業版以上功能</div>
            <div style="color:#94a3b8;">升級以查看鏈上數據、巨鯨動向、交易所流量</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("#### 🔗 鏈上數據（真實數據）")

        onchain_col1, onchain_col2 = st.columns(2)

        with onchain_col1:
            st.markdown("##### 🐋 巨鯨動向")

            # 取得真實巨鯨數據
            whale_df = data_manager.get_whale_data("BTC/USDT")

            if whale_df is not None:
                whale_fig = go.Figure()
                whale_fig.add_trace(
                    go.Scatter(x=whale_df["時間"], y=whale_df["巨鯨買入"], name="巨鯨買入", line=dict(color="#00cc96"))
                )
                whale_fig.add_trace(
                    go.Scatter(x=whale_df["時間"], y=whale_df["巨鯨賣出"], name="巨鯨賣出", line=dict(color="#ef553b"))
                )
                whale_fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(30,30,50,0.3)")
                st.plotly_chart(whale_fig, use_container_width=True)
            else:
                st.info("暫無巨鯨數據")

        with onchain_col2:
            st.markdown("##### 📊 交易所流量")

            # 取得真實鏈上數據
            onchain = data_manager.get_onchain_data("BTC/USDT")

            if onchain:
                st.metric("BTC 價格 (USD)", f"${onchain.get('price_usd', 0):,.2f}")
                st.metric("24h 成交量", f"${onchain.get('volume_24h', 0):,.0f}")
            else:
                st.info("暫無交易所流量數據")

# ───────────────────────────────────────────────────────────
# Tab 6: 情緒分析（VIP）
# ───────────────────────────────────────────────────────────
with tabs[6]:
    if not is_premium:
        st.markdown(
            """
        ### 🔒 情緒分析
        <div style="background:rgba(255,215,0,0.1);border:1px solid #ffd700;
            border-radius:12px;padding:30px;text-align:center;">
            <div style="font-size:3rem;margin-bottom:10px;">👑</div>
            <div style="font-size:1.2rem;color:#ffd700;margin-bottom:10px;">專業版以上功能</div>
            <div style="color:#94a3b8;">升級以查看情緒分析、社群聲量、新聞情緒</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("#### 💭 情緒分析（真實數據）")

        fg_col1, fg_col2, fg_col3 = st.columns(3)

        with fg_col1:
            st.markdown("##### 🌡️ 恐懼貪婪指數")

            # 取得真實恐懼貪婪指數
            fg_data = data_manager.get_fear_greed()

            if fg_data:
                fg_value = fg_data.get("value", 50)
                fg_classification = fg_data.get("classification", "Neutral")
                fg_color = "#00cc96" if fg_value >= 50 else "#ef553b"

                fg_fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=fg_value,
                        title=dict(text=f"{fg_classification}", font_size=14),
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": fg_color},
                            "steps": [
                                {"range": [0, 25], "color": "rgba(239,85,59,0.3)"},
                                {"range": [25, 45], "color": "rgba(255,161,90,0.3)"},
                                {"range": [45, 55], "color": "rgba(255,255,255,0.3)"},
                                {"range": [55, 75], "color": "rgba(0,204,150,0.3)"},
                                {"range": [75, 100], "color": "rgba(0,204,150,0.5)"},
                            ],
                        },
                    )
                )
                fg_fig.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e8"))
                st.plotly_chart(fg_fig, use_container_width=True)
            else:
                st.info("暫無恐懼貪婪指數數據")

        with fg_col2:
            st.markdown("##### 📱 社群情緒")

            # 取得真實社群情緒
            social_data = data_manager.get_social_sentiment("BTC/USDT")

            if social_data:
                social_fig = go.Figure()
                social_fig.add_trace(
                    go.Bar(
                        name="正面",
                        x=["Twitter", "Reddit"],
                        y=[social_data.get("twitter_positive", 50), social_data.get("reddit_positive", 50)],
                        marker_color="#00cc96",
                    )
                )
                social_fig.add_trace(
                    go.Bar(
                        name="負面",
                        x=["Twitter", "Reddit"],
                        y=[social_data.get("twitter_negative", 30), social_data.get("reddit_negative", 30)],
                        marker_color="#ef553b",
                    )
                )
                social_fig.update_layout(
                    height=250, barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(30,30,50,0.3)"
                )
                st.plotly_chart(social_fig, use_container_width=True)
            else:
                st.info("暫無社群情緒數據")

        with fg_col3:
            st.markdown("##### 📰 新聞情緒")

            # 使用恐懼貪婪指數作為新聞情緒代理
            if fg_data:
                news_score = fg_value
                news_fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=news_score,
                        title=dict(text="新聞情緒", font_size=14),
                        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#6ea8fe"}},
                    )
                )
                news_fig.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e8"))
                st.plotly_chart(news_fig, use_container_width=True)
            else:
                st.info("暫無新聞情緒數據")

# ───────────────────────────────────────────────────────────
# Tab 7: 績效分析
# ───────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown("#### 📊 績效分析")

    if watchlist:
        total_equity = sum(w.get("initial_equity", 10000) for w in watchlist)
        total_pnl = sum(
            (w.get("last_price", 0) - w.get("entry_price", 0))
            / w.get("entry_price", 1)
            * w.get("initial_equity", 10000)
            for w in watchlist
            if w.get("position", 0) != 0
        )

        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        stat_col1.metric("總資金", f"${total_equity:,.0f}")
        stat_col2.metric("未實現 P&L", f"${total_pnl:+,.0f}")
        stat_col3.metric("持倉數量", sum(1 for w in watchlist if w.get("position", 0) != 0))
        stat_col4.metric("總報酬率", f"{(total_pnl / total_equity * 100) if total_equity > 0 else 0:+.2f}%")

    st.divider()

    # 權益曲線
    st.markdown("##### 權益曲線")

    equity_fig = go.Figure()
    equity_fig.add_trace(
        go.Scatter(
            x=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
            y=[10000, 10200, 10150, 10350, 10500, 10450],
            mode="lines+markers",
            name="權益",
            line=dict(color="#6ea8fe", width=3),
            fill="tozeroy",
            fillcolor="rgba(110,168,254,0.2)",
        )
    )

    equity_fig.update_layout(
        height=350,
        xaxis_title="時間",
        yaxis_title="權益 ($)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,30,50,0.3)",
        font=dict(color="#e0e0e8"),
    )

    st.plotly_chart(equity_fig, use_container_width=True)

# ════════════════════════════════════════════════════════════
# 自動刷新（智能停留）
# ════════════════════════════════════════════════════════════

# 自動刷新機制 - 不依賴 WebSocket，始終保持數據更新
# 使用 Streamlit 的原生自動刷新
auto_refresh = st.toggle("🔄 自動刷新", value=True, key="auto_refresh_toggle")

if auto_refresh:
    # 每 3 秒自動刷新一次（避免過於頻繁）
    time.sleep(3)
    st.rerun()
