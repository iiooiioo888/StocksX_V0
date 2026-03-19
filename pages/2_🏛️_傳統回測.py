# 傳統市場回測 — v4.2 新架構
import time as _time_mod
from datetime import datetime, timezone

import streamlit as st

from src.auth import UserDB
from src.backtest.fees import get_fee_rate, get_slippage
from src.compat import run_all_strategies_new
from src.core import get_orchestrator
from src.data.integrity import validate_ohlcv
from src.ui_backtest import (
    render_equity_curves,
    render_kline_chart,
    render_performance_table,
    render_summary_line,
    render_trade_details,
)
from src.ui_common import apply_theme, breadcrumb, check_session, sidebar_user_nav

st.set_page_config(page_title="StocksX — 傳統回測", page_icon="🏛️", layout="wide")
apply_theme()
breadcrumb("傳統市場回測", "🏛️")

_user = check_session()
_db = UserDB()

# 市場細分配置
MARKET_TABS = {
    "📈 股票": {
        "美股": [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "NVDA",
            "META",
            "TSLA",
            "AMD",
            "INTC",
            "NFLX",
            "CRM",
            "ORCL",
            "ADBE",
            "PYPL",
            "COIN",
            "MSTR",
            "PLTR",
            "UBER",
        ],
        "台股": [
            "2330.TW",
            "2317.TW",
            "2454.TW",
            "2308.TW",
            "2881.TW",
            "2882.TW",
            "2303.TW",
            "3711.TW",
            "2412.TW",
            "1301.TW",
        ],
        "港股": ["0700.HK", "9988.HK", "1810.HK", "3690.HK", "9618.HK"],
    },
    "🏦 ETF": {
        "美國大盤": ["SPY", "QQQ", "IWM", "DIA", "VTI"],
        "行業 ETF": ["ARKK", "SOXX", "XLF", "XLE", "XLK", "XLV"],
        "商品 ETF": ["GLD", "SLV", "USO"],
        "債券 ETF": ["TLT", "HYG", "BND", "AGG", "LQD"],
        "台灣 ETF": ["0050.TW", "00878.TW", "00919.TW", "006208.TW"],
    },
    "📜 債券": {
        "美國公債": ["^TNX", "^TYX", "TLT", "IEF", "SHY"],
        "公司債": ["HYG", "LQD", "JNK"],
    },
    "🛢️ 期貨": {
        "金屬": ["GC=F", "SI=F", "HG=F", "PL=F"],
        "能源": ["CL=F", "NG=F", "BZ=F"],
        "農產品": ["ZC=F", "ZS=F", "ZW=F"],
        "指數期貨": ["ES=F", "NQ=F", "YM=F", "RTY=F"],
    },
    "🌍 指數": {
        "美國": ["^GSPC", "^DJI", "^IXIC", "^RUT"],
        "歐洲": ["^FTSE", "^GDAXI", "^FCHI"],
        "亞太": ["^N225", "^HSI", "^TWII", "^KS11", "^AXJO"],
    },
}

with st.sidebar:
    sidebar_user_nav(_user)

    with st.expander("🔧 設定", expanded=True):
        # 第一層：市場大類 Tab
        market_type = st.selectbox("市場類型", list(MARKET_TABS.keys()), index=0)
        sub_cats = MARKET_TABS[market_type]

        # 第二層：細分類
        sub_cat = st.selectbox("細分", list(sub_cats.keys()), index=0)
        symbols = sub_cats[sub_cat] + ["其他（自填）"]
        symbol = st.selectbox("標的", symbols, index=0)
        if symbol == "其他（自填）":
            symbol = st.text_input("自訂代碼", value="AAPL", placeholder="AAPL, 2330.TW, GC=F")

        timeframe = st.selectbox("K 線週期", ["1h", "1d"], index=1)

        # 自動偵測手續費
        _is_tw = ".TW" in (symbol or "")
        _fee_ex = "tw_broker" if _is_tw else "us_broker"
        _fee = get_fee_rate(_fee_ex)
        _slip = get_slippage(_fee_ex)
        _fee_label = "台股券商 0.1425%" if _is_tw else "美股零佣金"
        st.caption(f"💸 {_fee_label}")

    with st.expander("📅 時間", expanded=True):
        today = datetime.now(timezone.utc)
        c1, c2 = st.columns(2)
        start = c1.date_input("開始", value=today.replace(day=max(1, today.day - 30)))
        end = c2.date_input("結束", value=today)

    with st.expander("💰 資金", expanded=False):
        _settings = _db.get_settings(_user["id"]) if _user else {}
        initial_equity = st.number_input(
            "初始資金", min_value=100.0, value=float(_settings.get("default_equity", 10000)), step=500.0
        )
        user_fee = st.number_input("手續費%", min_value=0.0, value=_fee, step=0.01)
        user_slip = st.number_input("滑點%", min_value=0.0, value=_slip, step=0.01)

    run_btn = st.button("🚀 執行回測", type="primary", use_container_width=True)

# 主頁面標題
_type_icon = market_type.split(" ")[0]
st.markdown(f"## {_type_icon} {market_type.split(' ')[-1]}回測 — {symbol or '未選擇'}")


def _to_ms(d):
    return int(datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)


since_ms = _to_ms(start)
until_ms = int(datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc).timestamp() * 1000)

if run_btn and since_ms < until_ms:
    _t0 = _time_mod.time()
    _bar = st.progress(0, text="連接 Yahoo Finance…")
    try:
        _bar.progress(20, text="拉取數據…")
        # ✅ 新架構：Orchestrator 自動路由到 YahooProvider
        orch = get_orchestrator()
        rows = orch.fetch_ohlcv(symbol or "AAPL", timeframe, since=since_ms, limit=5000)
        rows = [r for r in rows if since_ms <= r["timestamp"] <= until_ms]
        _issues = validate_ohlcv(rows) if rows else ["無數據"]
        for _i in _issues:
            st.warning(f"⚠️ {_i}")
    except Exception as e:
        st.error(f"❌ {e}")
        rows = None
    if rows:
        _bar.progress(40, text="回測所有策略…")
        # ✅ 新架構：run_all_strategies_new
        results = run_all_strategies_new(
            rows,
            since_ms,
            until_ms,
            initial_equity=initial_equity,
            leverage=1.0,
            fee_rate=user_fee,
            slippage=user_slip,
        )
        _bar.progress(100, text="✅ 完成")
        _elapsed = _time_mod.time() - _t0
        st.session_state["trad_results"] = results
        st.session_state["trad_rows"] = rows
        st.markdown(
            f'<div class="success-banner">🎉 完成！{_elapsed:.1f}s　|　{len(rows)} K線</div>', unsafe_allow_html=True
        )
        if _user:
            for s, r in results.items():
                if not r.error:
                    _db.save_backtest(_user["id"], symbol, "yfinance", timeframe, s, {}, r.metrics)

if "trad_results" in st.session_state:
    results = st.session_state["trad_results"]
    rows = st.session_state.get("trad_rows", [])
    best, valid = render_summary_line(results)
    if valid:
        tab1, tab2 = st.tabs(["🕯️ 圖表", "📊 績效"])
        with tab1:
            if rows:
                render_kline_chart(rows, best)
            render_equity_curves(results, initial_equity)
        with tab2:
            render_performance_table(results)
            with st.expander("📝 交易明細", expanded=False):
                render_trade_details(results)
else:
    st.info("👈 選擇市場類型和標的，點擊「🚀 執行回測」")
    st.divider()
    st.markdown("### 📋 支援市場一覽")
    _mt_cols = st.columns(len(MARKET_TABS))
    for _col, (mt, subs) in zip(_mt_cols, MARKET_TABS.items()):
        with _col:
            st.markdown(f"**{mt}**")
            for cat, syms in subs.items():
                _count = len(syms)
                _preview = ", ".join(syms[:3])
                st.caption(f"{cat}（{_count}）：{_preview}…" if _count > 3 else f"{cat}：{_preview}")
