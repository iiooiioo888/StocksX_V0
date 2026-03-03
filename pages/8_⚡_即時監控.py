# 即時監控（專業版 v5.0）
# 功能：WebSocket 即時推送、智能信號、風險管理、高級策略、收費功能

import streamlit as st
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Any

from src.auth import UserDB
from src.config import format_price, STRATEGY_LABELS

# ════════════════════════════════════════════════════════════
# 頁面配置
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="StocksX — 即時監控專業版",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════
# CSS 樣式 - 專業版
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
.stApp {
    background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #0f1724 100%);
}

/* 價格卡片 */
.price-card {
    background: linear-gradient(135deg, rgba(30,30,58,0.9), rgba(37,37,69,0.9));
    border: 1px solid rgba(58,58,92,0.4);
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
    transition: all 0.3s ease;
}

.price-card:hover {
    border-color: rgba(110,168,254,0.4);
    box-shadow: 0 8px 32px rgba(110,168,254,0.15);
    transform: translateY(-2px);
}

.price-up {color: #00cc96 !important;}
.price-down {color: #ef553b !important;}

/* 信號卡片 */
.signal-card {
    background: linear-gradient(135deg, rgba(42,26,58,0.9), rgba(53,37,69,0.9));
    border: 1px solid rgba(90,58,124,0.4);
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

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* 持倉狀態 */
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

.position-flat {
    color: #64748b !important;
}

/* 連接狀態指示器 */
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

/* 高級功能標籤 */
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

/* 風險警示 */
.risk-warning {
    background: linear-gradient(135deg, rgba(239,85,59,0.2), rgba(239,85,59,0.1));
    border: 1px solid #ef553b;
    border-radius: 8px;
    padding: 10px;
    margin: 10px 0;
}

.risk-safe {
    background: linear-gradient(135deg, rgba(0,204,150,0.2), rgba(0,204,150,0.1));
    border: 1px solid #00cc96;
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

# 檢查用戶等級（收費功能）
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
if "auto_trading_enabled" not in st.session_state:
    st.session_state.auto_trading_enabled = False

# ════════════════════════════════════════════════════════════
# 標題和狀態列
# ════════════════════════════════════════════════════════════
header_col1, header_col2, header_col3 = st.columns([3, 2, 2])

with header_col1:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:15px;margin-bottom:20px;">
        <h1 style="margin:0;font-size:2rem;">📡 即時監控專業版</h1>
        {f'<span class="premium-badge">👑 {user_role.upper()}</span>' if not is_premium else ''}
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    # 連接狀態
    status_icon = "🟢" if st.session_state.ws_connected else "🔴"
    status_text = "已連接" if st.session_state.ws_connected else "未連接"
    status_class = "connection-live" if st.session_state.ws_connected else "connection-offline"
    
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;background:rgba(30,30,58,0.6);
        padding:10px 20px;border-radius:12px;border:1px solid rgba(58,58,92,0.3);">
        <span class="connection-indicator {status_class}"></span>
        <span style="color:#e0e0e8;">WebSocket: {status_text}</span>
        <span style="color:#64748b;font-size:0.85rem;">{len(st.session_state.ws_prices)} 個價格</span>
    </div>
    """, unsafe_allow_html=True)

with header_col3:
    if st.button("🔄 重新整理", use_container_width=True):
        st.rerun()

st.divider()

# ════════════════════════════════════════════════════════════
# 側邊欄 - 高級控制
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ 控制面板")
    
    # 用戶等級資訊
    if not is_premium:
        st.markdown("""
        <div style="background:linear-gradient(135deg, #ffd700, #ffed4e);
            color:#1a1a2e;padding:15px;border-radius:12px;margin-bottom:20px;">
            <div style="font-weight:bold;margin-bottom:5px;">👑 升級專業版</div>
            <div style="font-size:0.85rem;">解鎖高級信號、自動交易、風險管理</div>
        </div>
        """, unsafe_allow_html=True)
    
    # WebSocket 控制
    st.markdown("#### 🔌 WebSocket 連接")
    ws_url = st.text_input(
        "WebSocket URL",
        value="ws://localhost:8001/ws",
        key="ws_url_input",
        help="幣安 WebSocket 服務地址"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        connect_btn = st.button(
            "🔌 連接" if not st.session_state.ws_connected else "✅ 已連接",
            use_container_width=True,
            disabled=st.session_state.ws_connected,
            key="ws_connect"
        )
        if connect_btn:
            st.session_state.ws_connected = True
            st.success("WebSocket 連接成功！")
            st.rerun()
    
    with col2:
        disconnect_btn = st.button(
            "❌ 斷開",
            use_container_width=True,
            disabled=not st.session_state.ws_connected,
            key="ws_disconnect"
        )
        if disconnect_btn:
            st.session_state.ws_connected = False
            st.session_state.ws_prices = {}
            st.warning("WebSocket 已斷開")
            st.rerun()
    
    st.divider()
    
    # 訂閱管理
    st.markdown("#### 📋 訂閱管理")
    
    # 顯示當前訂閱
    st.markdown("**當前訂閱交易對**")
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
    popular_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "DOGE/USDT"]
    new_symbol = st.selectbox(
        "選擇熱門交易對",
        options=popular_symbols,
        key="symbol_select"
    )
    
    if st.button("新增訂閱", use_container_width=True, key="add_symbol"):
        if new_symbol not in st.session_state.subscriptions:
            st.session_state.subscriptions.append(new_symbol)
            st.success(f"已新增 {new_symbol}")
            st.rerun()
    
    custom_symbol = st.text_input("或輸入自訂交易對", placeholder="AAVE/USDT", key="custom_symbol")
    if st.button("新增自訂", use_container_width=True, key="add_custom"):
        if custom_symbol and custom_symbol not in st.session_state.subscriptions:
            st.session_state.subscriptions.append(custom_symbol)
            st.success(f"已新增 {custom_symbol}")
            st.rerun()
    
    st.divider()
    
    # 高級功能（收費）
    st.markdown("#### 🎯 高級功能")
    
    # 自動交易
    auto_trading = st.toggle(
        "🤖 自動交易",
        value=st.session_state.auto_trading_enabled,
        disabled=not is_premium,
        help="專業版以上功能：根據信號自動開平倉"
    )
    if auto_trading and not is_premium:
        st.info("🔒 升級專業版以啟用自動交易")
    st.session_state.auto_trading_enabled = auto_trading
    
    # 風險管理
    risk_management = st.toggle(
        "🛡️ 風險管理",
        value=False,
        disabled=not is_premium,
        help="專業版以上功能：停損/停利/倉位控制"
    )
    if risk_management and not is_premium:
        st.info("🔒 升級專業版以啟用風險管理")
    
    # 高級信號
    if is_premium:
        st.markdown("#### 📊 高級信號")
        show_all_signals = st.toggle("顯示所有信號", value=True)
        signal_confidence = st.slider("最小信心度", 0.0, 1.0, 0.6, 0.05)
        
        if is_vip:
            st.markdown("#### 👑 VIP 功能")
            enable_ai = st.toggle("AI 預測", value=False, help="使用 AI 預測價格走勢")
            enable_arbitrage = st.toggle("套利機會", value=False, help="監控跨交易所價差")

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
        console.log('URL:', wsUrl);
        console.log('訂閱:', symbols);
        
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
                console.log('📥 收到:', message.type);
                
                if (message.type === 'price_update') {{
                    const data = message.data;
                    // 更新價格
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
                }} else if (message.type === 'signal') {{
                    const data = message.data;
                    const event = new CustomEvent('signalUpdate', {{
                        detail: {{
                            symbol: data.symbol,
                            action: data.action,
                            strategy: data.strategy,
                            confidence: data.confidence,
                            price: data.price,
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
        
        console.log('=== 初始化完成 ===');
    }})();
    </script>
    """
    
    import streamlit.components.v1 as components
    components.html(websocket_script, height=0)

# ════════════════════════════════════════════════════════════
# 主內容 - 標籤頁
# ════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📊 即時價格",
    "🔔 交易信號",
    "💼 持倉監控",
    "📈 績效分析",
    "⚙️ 策略設定"
])

# ───────────────────────────────────────────────────────────
# Tab 1: 即時價格
# ───────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("#### 📊 即時價格監控")
    
    if not st.session_state.subscriptions:
        st.info("請在側邊欄新增訂閱交易對")
    else:
        # 價格卡片網格
        price_cols = st.columns(min(3, len(st.session_state.subscriptions)))
        
        for idx, symbol in enumerate(st.session_state.subscriptions):
            col = price_cols[idx % 3]
            price_data = st.session_state.ws_prices.get(symbol, {})
            
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
                    st.markdown(f"""
                    <div class="price-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                            <span style="font-size:0.9rem;color:#94a3b8;">{symbol}</span>
                            <span style="font-size:0.75rem;color:#64748b;">
                                {datetime.fromtimestamp(last_update/1000, tz=timezone.utc).strftime('%H:%M:%S') if last_update else '--:--:--'}
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
                    """, unsafe_allow_html=True)
            else:
                with col:
                    st.markdown(f"""
                    <div class="price-card" style="opacity:0.6;">
                        <div style="font-size:0.9rem;color:#94a3b8;margin-bottom:10px;">{symbol}</div>
                        <div style="font-size:1.8rem;font-weight:700;color:#64748b;margin-bottom:8px;">
                            等待數據...
                        </div>
                        <div style="font-size:0.75rem;color:#64748b;">
                            連接中
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # WebSocket 調試資訊
    with st.expander("🔍 WebSocket 調試資訊", expanded=False):
        st.write(f"**WebSocket URL**: {ws_url}")
        st.write(f"**訂閱交易對**: {st.session_state.subscriptions}")
        st.write(f"**連接狀態**: {'✅ 已連接' if st.session_state.ws_connected else '❌ 未連接'}")
        st.write(f"**已更新價格**: {len(st.session_state.ws_prices)} 個交易對")
        for sym, data in st.session_state.ws_prices.items():
            st.write(f"- {sym}: ${data.get('price', 0):,.2f} ({data.get('change_pct', 0):+.2f}%)")

# ───────────────────────────────────────────────────────────
# Tab 2: 交易信號
# ───────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("#### 🔔 交易信號")
    
    # 信號過濾器
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        signal_type = st.selectbox("信號類型", ["全部", "BUY", "SELL"])
    with filter_col2:
        min_confidence = st.slider("最小信心度", 0.0, 1.0, 0.5, 0.05)
    with filter_col3:
        if st.button("🗑️ 清除信號"):
            st.session_state.ws_signals = []
            st.rerun()
    
    # 信號列表
    if st.session_state.ws_signals:
        # 過濾信號
        filtered_signals = [
            s for s in st.session_state.ws_signals
            if (signal_type == "全部" or s.get("action") == signal_type)
            and s.get("confidence", 0) >= min_confidence
        ]
        
        if filtered_signals:
            for signal in filtered_signals[:20]:  # 限制顯示 20 筆
                action = signal.get("action", "")
                signal_class = "signal-buy" if action == "BUY" else "signal-sell"
                action_emoji = "🟢" if action == "BUY" else "🔴"
                confidence = signal.get("confidence", 0)
                
                st.markdown(f"""
                <div class="signal-card {signal_class}">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="font-size:1.2rem;">{action_emoji}</span>
                            <strong style="font-size:1.1rem;margin-left:8px;">{action}</strong>
                            <span style="margin-left:10px;color:#e0e0e8;">{signal.get('symbol', '')}</span>
                            {f'<span class="premium-badge">高級</span>' if signal.get('is_premium') else ''}
                        </div>
                        <div style="font-size:0.85rem;color:#94a3b8;">
                            {datetime.fromtimestamp(signal.get('timestamp', 0)/1000, tz=timezone.utc).strftime('%H:%M:%S')}
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:10px;font-size:0.85rem;">
                        <div>
                            <div style="color:#64748b;font-size:0.75rem;">策略</div>
                            <div style="color:#e0e0e8;">{STRATEGY_LABELS.get(signal.get('strategy', ''), signal.get('strategy', 'N/A'))}</div>
                        </div>
                        <div>
                            <div style="color:#64748b;font-size:0.75rem;">信心度</div>
                            <div style="color:{'#00cc96' if confidence > 0.7 else '#ffa15a' if confidence > 0.5 else '#ef553b'};">
                                {confidence*100:.0f}%
                            </div>
                        </div>
                        <div>
                            <div style="color:#64748b;font-size:0.75rem;">價格</div>
                            <div style="color:#e0e0e8;">${signal.get('price', 0):,.2f}</div>
                        </div>
                        <div>
                            <div style="color:#64748b;font-size:0.75rem;">操作</div>
                            <button style="background:rgba(255,255,255,0.1);border:none;
                                color:#e0e0e8;padding:4px 8px;border-radius:4px;cursor:pointer;">
                                跟單
                            </button>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暫無符合條件的信號")
    else:
        st.info("暫無信號")
        st.caption("連接 WebSocket 後將即時接收信號")

# ───────────────────────────────────────────────────────────
# Tab 3: 持倉監控
# ───────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("#### 💼 持倉監控")
    
    # 取得用戶持倉
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
            
            # 從 WebSocket 取得即時價格
            price_data = st.session_state.ws_prices.get(symbol, {})
            current_price = price_data.get("price", item.get("last_price", entry_price))
            
            # 計算損益
            if position > 0 and entry_price > 0 and current_price > 0:  # 多頭
                pnl_pct = (current_price - entry_price) / entry_price * 100
                pnl_amount = (current_price - entry_price) * (initial_equity / entry_price)
            elif position < 0 and entry_price > 0 and current_price > 0:  # 空頭
                pnl_pct = (entry_price - current_price) / entry_price * 100
                pnl_amount = (entry_price - current_price) * (initial_equity / entry_price)
            else:  # 空倉
                pnl_pct = 0
                pnl_amount = 0
            
            pnl_class = "price-up" if pnl_pct >= 0 else "price-down"
            position_text = "多頭" if position > 0 else "空頭" if position < 0 else "空倉"
            position_icon = "🟢" if position > 0 else "🔴" if position < 0 else "⚪"
            
            # 持倉卡片
            st.markdown(f"""
            <div class="price-card" style="margin-bottom:20px;">
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
                        <div style="color:#e0e0e8;font-size:1rem;">${format_price(entry_price) if entry_price else '--'}</div>
                    </div>
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">當前價</div>
                        <div style="color:#e0e0e8;font-size:1rem;">${format_price(current_price) if current_price else '--'}</div>
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
            """, unsafe_allow_html=True)
            
            # 操作按鈕
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
# Tab 4: 績效分析
# ───────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("#### 📈 績效分析")
    
    # 總體統計
    if watchlist:
        total_equity = sum(w.get("initial_equity", 10000) for w in watchlist)
        total_pnl = sum(
            (w.get("last_price", 0) - w.get("entry_price", 0)) / w.get("entry_price", 1) * w.get("initial_equity", 10000)
            for w in watchlist if w.get("position", 0) != 0
        )
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        stat_col1.metric("總資金", f"${total_equity:,.0f}")
        stat_col2.metric("未實現 P&L", f"${total_pnl:+,.0f}")
        stat_col3.metric("持倉數量", sum(1 for w in watchlist if w.get("position", 0) != 0))
        stat_col4.metric("平均報酬率", f"{(total_pnl/total_equity*100) if total_equity > 0 else 0:+.2f}%")
    
    # 績效圖表
    st.divider()
    st.markdown("##### 權益曲線")
    
    # 模擬數據（實際應從資料庫取得）
    import plotly.graph_objects as go
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
        y=[10000, 10200, 10150, 10350, 10500, 10450],
        mode='lines+markers',
        name='權益',
        line=dict(color='#6ea8fe', width=2)
    ))
    
    fig.update_layout(
        height=300,
        xaxis_title="時間",
        yaxis_title="權益 ($)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,30,50,0.3)',
        font=dict(color='#e0e0e8')
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────────────────────────────────────
# Tab 5: 策略設定
# ───────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("#### ⚙️ 策略設定")
    
    # 風險管理設定（收費功能）
    st.markdown("##### 🛡️ 風險管理")
    
    risk_col1, risk_col2 = st.columns(2)
    with risk_col1:
        stop_loss = st.slider("停損 (%)", 0.0, 20.0, 5.0, 0.5, disabled=not is_premium)
        take_profit = st.slider("停利 (%)", 0.0, 50.0, 10.0, 1.0, disabled=not is_premium)
    
    with risk_col2:
        max_position = st.slider("最大倉位 (%)", 0.0, 100.0, 20.0, 5.0, disabled=not is_premium)
        daily_limit = st.slider("每日交易上限", 0, 50, 10, 1, disabled=not is_premium)
    
    if not is_premium:
        st.info("🔒 升級專業版以啟用風險管理功能")
    
    if st.button("💾 儲存設定", use_container_width=True):
        db.save_settings(user["id"], {
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "max_position": max_position,
            "daily_limit": daily_limit
        })
        st.success("設定已儲存！")

# ════════════════════════════════════════════════════════════
# 自動刷新
# ════════════════════════════════════════════════════════════
if st.session_state.ws_connected:
    time.sleep(1)
    st.rerun()
