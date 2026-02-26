# 市場新聞 — RSS 拉取加密貨幣 & 股市新聞
import streamlit as st
import time
from datetime import datetime, timezone
from src.ui_common import apply_theme, breadcrumb, check_session, sidebar_user_nav

st.set_page_config(page_title="StocksX — 市場新聞", page_icon="📰", layout="wide")
apply_theme()
breadcrumb("市場新聞", "📰")
sidebar_user_nav(check_session())
st.markdown("## 📰 市場新聞")

NEWS_SOURCES = {
    "加密貨幣": [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "icon": "₿"},
        {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss", "icon": "📡"},
        {"name": "The Block", "url": "https://www.theblock.co/rss.xml", "icon": "🧱"},
        {"name": "Decrypt", "url": "https://decrypt.co/feed", "icon": "🔓"},
    ],
    "股票 & 財經": [
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex", "icon": "📈"},
        {"name": "MarketWatch", "url": "https://feeds.marketwatch.com/marketwatch/topstories/", "icon": "👁️"},
        {"name": "CNBC", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "icon": "📺"},
    ],
}


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_rss(url: str, max_items: int = 15) -> list[dict]:
    """拉取 RSS 並解析"""
    try:
        import xml.etree.ElementTree as ET
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        root = ET.fromstring(data)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            desc = item.findtext("description", "")
            if desc and len(desc) > 200:
                desc = desc[:200] + "…"
            for tag in ["<p>", "</p>", "<br>", "<br/>", "<img", "<a "]:
                if tag in desc:
                    desc = ""
                    break
            items.append({"title": title, "link": link, "date": pub_date, "desc": desc})
            if len(items) >= max_items:
                break
        return items
    except urllib.request.URLError as e:
        return [{"title": f"⚠️ 網路連線失敗: {str(e.reason)[:50]}", "link": "", "date": "", "desc": "請檢查網路連線"}]
    except ET.ParseError:
        return [{"title": "⚠️ RSS 格式解析失敗", "link": "", "date": "", "desc": "來源可能已變更格式"}]
    except Exception as e:
        return [{"title": f"⚠️ 載入失敗: {str(e)[:60]}", "link": "", "date": "", "desc": ""}]


tab_names = list(NEWS_SOURCES.keys())
tabs = st.tabs([f"{list(NEWS_SOURCES[k])[0]['icon']} {k}" for k in tab_names])

for tab, cat_name in zip(tabs, tab_names):
    with tab:
        sources = NEWS_SOURCES[cat_name]
        source_names = [s["name"] for s in sources]
        selected = st.selectbox("新聞來源", source_names, key=f"src_{cat_name}")
        source = next(s for s in sources if s["name"] == selected)

        with st.spinner(f"載入 {selected} 新聞…"):
            articles = _fetch_rss(source["url"])

        if articles:
            for a in articles:
                if not a["title"] or "載入失敗" in a["title"]:
                    st.warning(a["title"])
                    continue
                col1, col2 = st.columns([5, 1])
                with col1:
                    if a["link"]:
                        st.markdown(f"**[{a['title']}]({a['link']})**")
                    else:
                        st.markdown(f"**{a['title']}**")
                    if a["desc"]:
                        st.caption(a["desc"])
                with col2:
                    if a["date"]:
                        st.caption(a["date"][:16])
                st.divider()
        else:
            st.info("暫無新聞")

st.caption("📡 新聞每 10 分鐘自動刷新 | 來源：CoinDesk, CoinTelegraph, Yahoo Finance, CNBC 等")
