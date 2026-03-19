# StocksX 全局 CSS 樣式
# 從 src/config.py 提取，方便維護與快取

APP_CSS = """
/* 全局背景 */
.stApp {background: linear-gradient(160deg, #0f0f1a 0%, #1a1a2e 40%, #16213e 100%);}
section[data-testid="stSidebar"] {background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%); border-right: 1px solid #2a2a4a;}
section[data-testid="stSidebar"] * {color: #e0e0e8 !important;}
section[data-testid="stSidebar"] .stSelectbox label, section[data-testid="stSidebar"] .stRadio label {color: #b0b0c8 !important;}

/* 主要文字 */
.stApp, .stApp p, .stApp span, .stApp li {color: #e0e0e8;}
.stApp h1, .stApp h2, .stApp h3 {color: #f0f0ff;}
.stApp a {color: #6ea8fe;}

/* 指標卡片 */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e1e3a, #252545);
    border: 1px solid #3a3a5c; border-radius: 12px; padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    transition: transform 0.2s, box-shadow 0.2s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px); box-shadow: 0 4px 12px rgba(110,168,254,0.2);
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 1.3rem; color: #f0f0ff !important;}
[data-testid="stMetric"] [data-testid="stMetricLabel"] {color: #9090b0 !important;}

/* 展開區塊 */
div[data-testid="stExpander"] {
    background: rgba(26,26,46,0.6); border: 1px solid #3a3a5c; border-radius: 10px;
}
div[data-testid="stExpander"] summary {color: #d0d0e8 !important;}

/* 按鈕 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4a6cf7, #6366f1) !important;
    border: none !important; color: white !important; border-radius: 8px;
    box-shadow: 0 2px 10px rgba(99,102,241,0.3);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #5b7cf8, #7577f2) !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.5);
}
.stButton > button[kind="secondary"], .stButton > button:not([kind]) {
    background: rgba(40,40,70,0.8) !important; border: 1px solid #4a4a6c !important;
    color: #d0d0e8 !important; border-radius: 8px;
}

/* Tab */
.stTabs [data-baseweb="tab-list"] {background: transparent; border-bottom: 1px solid #3a3a5c;}
.stTabs [data-baseweb="tab"] {color: #9090b0 !important; background: transparent;}
.stTabs [aria-selected="true"] {color: #6ea8fe !important; border-bottom: 2px solid #6ea8fe;}

/* 表格 */
[data-testid="stDataFrame"] {border-radius: 8px; overflow: hidden;}

/* 輸入框 */
.stTextInput input, .stNumberInput input, .stSelectbox > div > div {
    background: rgba(30,30,55,0.8) !important; border: 1px solid #3a3a5c !important;
    color: #e0e0e8 !important; border-radius: 6px;
}

/* 面包屑 */
.breadcrumb {font-size: 0.85rem; color: #7070a0; margin-bottom: 0.5rem;}

/* 動畫 */
@keyframes fadeIn {from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)}}
.success-banner {
    background: linear-gradient(135deg, #1a3a2a, #1e4a32); border: 1px solid #28a745;
    border-radius: 10px; padding: 15px; margin: 10px 0; animation: fadeIn 0.5s; color: #a0e8b0;
}
.fail-banner {
    background: linear-gradient(135deg, #3a1a1a, #4a1e1e); border: 1px solid #dc3545;
    border-radius: 10px; padding: 15px; margin: 10px 0; animation: fadeIn 0.5s; color: #e8a0a0;
}

/* info/warning/error */
div[data-testid="stAlert"] {border-radius: 8px;}

/* 頁面鏈接卡片 */
[data-testid="stPageLink"] {
    background: rgba(30,30,55,0.6); border: 1px solid #3a3a5c;
    border-radius: 10px; padding: 12px; transition: all 0.2s;
}
[data-testid="stPageLink"]:hover {
    background: rgba(110,168,254,0.15); border-color: #6ea8fe;
}
"""
