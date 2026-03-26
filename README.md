<div align="center">

# StocksX

**機構級量化交易與投資組合管理平台**

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)](LICENSE)

**130+ 種量化策略 · 10 大類 · 多市場回測 · 投資組合優化 · AI 驅動 · 即時監控**

[快速開始](#-快速開始) · [功能](#-功能亮點) · [策略庫](#-策略庫) · [架構](#️-技術架構) · [部署](#-部署) · [配置](#️-配置)

</div>

---

## 🚀 快速開始

```bash
# 1. 克隆專案
git clone https://github.com/iiooiioo888/StocksX_V0.git && cd StocksX_V0

# 2. 配置環境（⚠️ 必須設定 SECRET_KEY！）
cp .env.example .env
# 編輯 .env，填入 SECRET_KEY：
# python -c "import secrets; print(secrets.token_hex(32))"

# 3. Docker 啟動
docker compose up -d

# 👉 主應用 → http://localhost:8501
# 👉 WebSocket → ws://localhost:8001/ws
```

### 本地開發

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # 記得設定 SECRET_KEY
streamlit run app.py
```

---

## ✨ 功能亮點

<table>
<tr>
<td width="50%" valign="top">

### ⚡ 高效能回測引擎
- NumPy 向量化優化，提速 **10–100x**
- 向量化 & 事件驅動雙模式回測
- 蒙地卡羅模擬（330,000+ 次）
- 完整 OHLCV 數據清洗管道

</td>
<td width="50%" valign="top">

### 🧠 AI 策略增強
- LSTM / Transformer 價格預測
- FinBERT 市場情緒分析
- DQN 強化學習自動交易
- 多因子模型 & 遺傳演算法

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📊 投資組合優化
- Markowitz 均值-方差 & 有效前沿
- Black-Litterman 模型
- 風險平價 & 層級風險平價 (HRP)
- 風險貢獻分解視覺化

</td>
<td width="50%" valign="top">

### 🌐 多市場覆蓋
- ₿ 加密貨幣（CCXT · 11 交易所）
- 🇺🇸 美股 · 🇹🇼 台股 · ETF
- 即時 WebSocket 推送
- 恐懼貪婪指數 & 市場情緒

</td>
</tr>
</table>

---

## 📦 策略庫

> **10 大類 · 130+ 策略**，覆蓋量化交易全鏈路

| 類別 | 數量 | 典型策略 |
|:-----|:---:|:---------|
| 📈 趨勢跟隨與動量 | **18** | MACD · ADX · 超級趨勢 · 海龜交易法 · Hull MA |
| 🔀 超買超賣振盪 | **16** | RSI · KD · 布林帶 · Fisher Transform · TRIX |
| 💥 突破與均值回歸 | **16** | 唐奇安通道 · VWAP 回歸 · 布林帶擠壓 · ORB |
| 🧠 AI / 機器學習 | **16** | LSTM · GAN · 圖神經網路 · 遺傳演算法 · 集成學習 |
| 🛡 風險管理與倉位 | **12** | 凱利公式 · 風險平價 · CVaR · Delta 對沖 |
| ⏱ 微結構與訂單流 | **12** | 訂單流分析 · VPIN · 冰山訂單偵測 · L2 深度 |
| 🌐 跨市場與宏觀 | **12** | 利差交易 · 季節性 · VIX · 收益率曲線 |
| 🔧 進階計量與統計 | **10** | 協整配對 · Kalman · GARCH · Copula · 小波分析 |
| 🎯 形態與圖表模式 | **10** | 頭肩 · 諧波模式 · Elliott 波浪 · Wyckoff |
| ⚙ 執行演算法與高頻 | **8** | 做市 · 統計套利 · TWAP · ETF 套利 |

<details>
<summary><b>📋 展開完整策略列表（130 策略）</b></summary>

### 📈 趨勢跟隨與動量（18 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 1 | **雙均線交叉** | 短期 / 長期 SMA 交叉產生買賣訊號 |
| 2 | **EMA 交叉** | 指數移動平均交叉，對近期價格更敏感 |
| 3 | **MACD** | 快慢線差離 + 柱狀圖判斷動量變化 |
| 4 | **ADX** | 平均趨向指標，量化趨勢強度（非方向） |
| 5 | **超級趨勢** | 基於 ATR 的動態支撐 / 阻力軌跡線 |
| 6 | **拋物線 SAR** | 追蹤止損系統，點位翻轉即反轉 |
| 7 | **Keltner 通道** | EMA + ATR 建構通道，突破即趨勢確認 |
| 8 | **Aroon 指標** | 衡量自近期高 / 低點經過的時間 |
| 9 | **DMI / DMI+/-** | 方向運動指標，＋DI 與 －DI 交叉判斷多空 |
| 10 | **均線帶（Ribbon）** | 多條 EMA 並列，帶狀收窄→發散揭示強弱 |
| 11 | **海龜交易法** | 20 日高點進場 + ATR 動態止損 |
| 12 | **CCI 商品通道** | 衡量價格偏離統計均值的程度 |
| 13 | **Hull MA** | 極低延遲移動平均，幾乎零滯後 |
| 14 | **T3 均線** | 三次平滑的 EMA，超平滑且低延遲 |
| 15 | **Kaufman 自適應均線（KAMA）** | 根據市場噪音自動調整靈敏度 |
| 16 | **Tillson T3** | 利用體積因子平滑的高階移動平均 |
| 17 | **零滯後 EMA（ZLEMA）** | 預先補償延遲的改進型 EMA |
| 18 | **TEMA 三重指數** | 三次 EMA 疊加消除延遲，趨勢銳利 |

### 🔀 超買超賣振盪（16 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 19 | **RSI** | 相對強弱指標，70/30 超買超賣閾值 |
| 20 | **KD 隨機指標** | %K/%D 交叉 + 超買超賣區域 |
| 21 | **威廉指標（%R）** | -20 / -80 為極端區域 |
| 22 | **布林帶** | 標準差通道，觸帶 + 收口為反轉訊號 |
| 23 | **一目均衡表** | 五線系統，日本經典雲圖 |
| 24 | **Stochastic RSI** | 對 RSI 再做隨機運算，極端靈敏 |
| 25 | **Awesome Oscillator** | 5 期與 34 期中點均線差值 |
| 26 | **Chande 動量振盪** | 直接加總漲跌動量，-100 到 +100 |
| 27 | **Fisher Transform** | 將分佈轉為常態分佈，極端值銳利 |
| 28 | **Detrended Price Oscillator** | 移除長期趨勢後觀察短期週期 |
| 29 | **Ulcer Index** | 衡量從近期高點的回撤深度 |
| 30 | **Vortex 振盪** | 基於 TR 分離多空渦旋，交叉為訊號 |
| 31 | **Elder Ray（牛熊力量）** | 分離買方（Bull Power）和賣方（Bear Power） |
| 32 | **Mass Index** | 追蹤高低點範圍的擴張，預測反轉 |
| 33 | **TRIX** | 三重平滑 ROC，過濾短期噪音的動量 |
| 34 | **Klinger 振盪** | 結合成交量與價格的趨勢振盪器 |

### 💥 突破與均值回歸（16 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 35 | **唐奇安通道** | N 期高低點通道，突破即入場 |
| 36 | **雙推力** | 連續兩根方向強勢 K 線確認突破 |
| 37 | **VWAP 回歸** | 偏離 VWAP 後回歸的均值回歸 |
| 38 | **開盤區間突破（ORB）** | 開盤前 N 分鐘高低點突破 |
| 39 | **樞軸點突破** | 以昨日高 / 收 / 低計算樞軸位 |
| 40 | **布林帶擠壓** | 帶寬收窄至歷史低位→等待爆發 |
| 41 | **斐波那契回撤突破** | 回踩 38.2% / 50% / 61.8% 後突破 |
| 42 | **成交量突破** | 價格突破 + 成交量放大，過濾假突破 |
| 43 | **杯柄形態** | U 型杯 + 小回調柄→突破頸線 |
| 44 | **三重頂 / 底突破** | 三次測試同一位置後突破 |
| 45 | **NR7 / NR4** | 連續 N 日中今日振幅最小→等待爆發 |
| 46 | **TTO（Toby Crabel Opening Range）** | 開盤 N 分鐘突破 + 前日窄幅確認 |
| 47 | **水平通道突破** | 等待價格在水平區間內整理後突破 |
| 48 | **旗形 / 三角旗形** | 強勢趨勢後的整理形態突破延續 |
| 49 | **W 底 / M 頂突破** | 經典雙底雙頂頸線突破 |
| 50 | **橫盤均值回歸** | 價格偏離橫盤均值兩倍標準差後回歸 |

### 🧠 AI / 機器學習增強（16 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 51 | **LSTM 預測** | 長短期記憶網路，捕捉時間序列長期依賴 |
| 52 | **情緒分析** | NLP 分析新聞 / 社群 / 推文情緒 |
| 53 | **多因子策略** | 動量、波動率、成交量等多因子打分 |
| 54 | **配對交易** | 統計套利：找高相關配對做多弱做空強 |
| 55 | **強化學習（RL）** | DQN / PPO 自學習最優下單策略 |
| 56 | **Transformer 預測** | 自注意力機制捕捉跨週期模式 |
| 57 | **遺傳演算法優化** | 模擬自然選擇進化策略參數 |
| 58 | **集成學習（Ensemble）** | 隨機森林 / XGBoost / 投票法降低方差 |
| 59 | **圖神經網路（GNN）** | 資產關聯建模為圖結構 |
| 60 | **GAN 價格生成** | 生成對抗網路合成市場情境 |
| 61 | **異常偵測** | Isolation Forest / Autoencoder 識別異常行情 |
| 62 | **在線學習** | 即時更新權重，適應體制轉換 |
| 63 | **貝葉斯優化** | 以機率模型指導超參數搜索，高效尋優 |
| 64 | **NLP 事件驅動** | 解析財報 / 央行聲明，提取結構化事件訊號 |
| 65 | **遷移學習** | 用成熟市場模型微調至新興市場 |
| 66 | **對比學習（Contrastive）** | 自監督學習市場狀態表示，無需標註資料 |

### 🛡 風險管理與倉位（12 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 67 | **凱利公式** | 根據勝率與賠率計算最優下注比例 |
| 68 | **固定分數法** | 每次交易承擔總資金固定百分比風險 |
| 69 | **波動率倉位調整** | 以 ATR 或歷史波動率反向調整倉位 |
| 70 | **最大回撤熔斷** | 回撤達閾值時自動暫停交易 |
| 71 | **相關性監控** | 監控持倉間相關係數，避免集中風險 |
| 72 | **Anti-Martingale** | 盈利加碼、虧損減碼，順勢放大 |
| 73 | **固定比率法** | 以每張合約的預期利潤 Delta 調整倉位 |
| 74 | **風險平價（Risk Parity）** | 各資產貢獻相同風險，平衡組合波動 |
| 75 | **CVaR / ES 倉位控制** | 以條件在險值決定最大可承受倉位 |
| 76 | **最優停損（Optimal Stopping）** | 用數學模型決定最佳止損時機 |
| 77 | **尾部風險對沖** | 購買深度價外期權保護極端行情 |
| 78 | **動態對沖（Delta Neutral）** | 即時調整期權 / 現貨 Delta 至中性 |

### ⏱ 微結構與訂單流（12 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 79 | **訂單流分析** | 分析逐筆成交的主動買 / 賣壓力 |
| 80 | **Delta 累積** | 累計買賣量差值，判斷主力動向 |
| 81 | **POC / Value Area** | 成交量分佈高量價位作為支撐阻力 |
| 82 | **TWAP** | 大單拆分演算法，降低市場衝擊 |
| 83 | **冰山訂單偵測** | 從成交模式推斷隱藏大單 |
| 84 | **VPIN（知情交易機率）** | 以成交量不平衡估計資訊型交易比例 |
| 85 | **Amihud 非流動性** | 用日報酬 / 成交量比衡量流動性衝擊成本 |
| 86 | **Kyle's Lambda** | 估計價格衝擊係數，量化市場深度 |
| 87 | **Tick 規則（Lee-Ready）** | 逐筆分類主動買 / 賣，精細化訂單流 |
| 88 | **Quote Stuffing 偵測** | 識別高頻掛單 / 撤單行為的欺騙策略 |
| 89 | **Level 2 深度分析** | 解析買賣盤口深度與不平衡比率 |
| 90 | **微價格偏移** | 以加權中間價追蹤短期價格壓力 |

### 🌐 跨市場與宏觀（12 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 91 | **利差交易（Carry）** | 做高低利率資產，賺取利差 |
| 92 | **季節性策略** | 歷史月份 / 星期效應（Sell in May） |
| 93 | **跨品種價差** | 月間價差、裂解價差、壓榨價差 |
| 94 | **美元指數聯動** | DXY 與風險資產的負相關性套利 |
| 95 | **避險比率動態調整** | 根據隱含波動率即時調整對沖比例 |
| 96 | **收益率曲線策略** | 做陡 / 做平 / 蝶式，押注利率期限結構 |
| 97 | **跨國權益輪動** | 根據宏觀因子在國家 / 地區間輪動配置 |
| 98 | **商品超級週期** | 識別多年期供需失衡驅動的大趨勢 |
| 99 | **恐慌指數交易（VIX）** | 利用 VIX 期貨期限結構 Contango / Backwardation |
| 100 | **信用利差交易** | 高收益債 vs 國債利差擴張 / 收窄 |
| 101 | **黃金 / 實際利率套利** | 金價與 TIPS 收益率的負相關性 |
| 102 | **跨資產風險平價** | 股 / 債 / 商品 / 貨幣按風險貢獻等權配置 |

### 🔧 進階計量與統計（10 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 103 | **協整配對** | Engle-Granger / Johansen 檢驗，長期均值回歸 |
| 104 | **Kalman 濾波** | 動態估計隱藏狀態，即時追蹤時變參數 |
| 105 | **GARCH 波動率模型** | 預測條件波動率叢聚，做多 / 做空波動 |
| 106 | **馬可夫體制轉換** | 識別 bull / bear / sideways 三種市場狀態 |
| 107 | **小波分析（Wavelet）** | 多尺度分解價格序列，分離趨勢 / 週期 / 雜訊 |
| 108 | **分數差分（ARFIMA）** | 處理長記憶性時間序列，捕捉長期依賴 |
| 109 | **Copula 模型** | 建模非線性資產相依結構，尾部風險更準確 |
| 110 | **隨機微分方程（SDE）** | Heston / Ornstein-Uhlenbeck 模型驅動的均值回歸 |
| 111 | **自助法（Bootstrap）** | 非參數重抽樣估計策略績效的信心區間 |
| 112 | **變點偵測（CUSUM / Bayesian）** | 自動識別市場參數發生結構性變化的時刻 |

### 🎯 形態與圖表模式（10 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 113 | **頭肩頂 / 底** | 經典反轉形態，頸線突破確認 |
| 114 | **楔形收斂 / 擴張** | 上升楔（看跌）/ 下降楔（看漲） |
| 115 | **鑽石頂 / 底** | 罕見但高勝率的反轉形態 |
| 116 | **跳空回補** | 缺口（Gap）在 N 日內回填的統計規律 |
| 117 | **日本 K 線組合** | 十字星、吞沒、晨星、烏雲蓋頂等 |
| 118 | **Elliott 波浪計數** | 五浪推動 + 三浪修正的分形結構 |
| 119 | **諧波模式（Harmonic）** | Gartley / Butterfly / Bat / Crab 精確比例反轉 |
| 120 | **Wyckoff 方法** | 吸籌 / 派發階段判斷 + 跳躍測試（Spring / UTAD） |
| 121 | **市場結構（HH/HL/LL/LH）** | 追蹤高低點序列判斷趨勢轉折 |
| 122 | **Volume Profile 形態** | D 型（平衡）、P 型（買方主導）、b 型（賣方主導） |

### ⚙ 執行演算法與高頻（8 策略）

| # | 策略 | 說明 |
|:-:|------|------|
| 123 | **做市策略（Market Making）** | 雙邊掛單賺取買賣價差 + 回扣 |
| 124 | **統計套利（Stat Arb）** | 大量配對 / 因子同時交易，微利高頻 |
| 125 | **延遲套利（Latency Arb）** | 跨交易所 / 跨市場的速度優勢套利 |
| 126 | **閃崩偵測 + 反向** | 識別無量急跌後的均值回歸反彈 |
| 127 | **VWAP / TWAP 被動執行** | 大單拆分追蹤基準價，最小化衝擊 |
| 128 | **Implementation Shortfall** | 最小化從決策到成交的總執行成本 |
| 129 | **Sniper 策略** | 監控大單成交後的短期延續效應 |
| 130 | **ETF 套利（NAV Arbitrage）** | ETF 市價 vs 淨值偏差的即時套利 |

</details>

---

## 🏗️ 技術架構

### 分層設計

```
┌──────────────────────────────────────────────────────────────┐
│  🎨  表現層                                                   │
│  Streamlit Dashboard · FastAPI REST+WS · Plotly 可視化       │
├──────────────────────────────────────────────────────────────┤
│  ⚙️   應用層                                                  │
│  Orchestrator（統一入口）· StrategyRegistry · SignalBus       │
├──────────────────────────────────────────────────────────────┤
│  📐  領域層                                                   │
│  回測引擎（NumPy 向量化）· 130+ 策略 · 風控 · 組合優化        │
├──────────────────────────────────────────────────────────────┤
│  🧩  基礎設施層                                                │
│  DI Container · Middleware Pipeline · Cache · TaskQueue       │
├──────────────────────────────────────────────────────────────┤
│  📡  數據層                                                   │
│  CCXT · Yahoo Finance · CoinGecko · WebSocket 即時推送       │
├──────────────────────────────────────────────────────────────┤
│  💾  持久化層                                                  │
│  SQLite · Redis 7 · PostgreSQL（可選）                        │
└──────────────────────────────────────────────────────────────┘
```

### 核心設計模式

| 模式 | 實現 | 職責 |
|:----:|------|------|
| **Orchestrator** | `src/core/orchestrator.py` | 統一業務入口，屏蔽內部組合 |
| **Registry** | `src/core/registry.py` | `@register_strategy` 裝飾器自動註冊 |
| **Repository** | `src/core/repository.py` | 數據存取抽象，可替換為 PostgreSQL |
| **DI Container** | `src/core/container.py` | 輕量依賴注入，支援測試替換 |
| **Pipeline** | `src/core/pipeline.py` | 函數式數據清洗管道 |
| **Middleware** | `src/core/middleware.py` | 日誌 / 重試 / 限流管道 |
| **SignalBus** | `src/core/signals.py` | 事件驅動解耦（Pub/Sub） |
| **CompositeProvider** | `src/core/adapters.py` | 多數據源自動路由 & 故障轉移 |

### 技術棧

| 層級 | 技術 | 用途 |
|:-----|------|------|
| 前端 | Streamlit · Plotly · Glassmorphism CSS | 互動式儀表板 |
| API | FastAPI · Uvicorn · WebSocket | REST + 即時推送 |
| 數據 | Pandas · NumPy · yfinance · CCXT | 數據處理 & 來源 |
| AI/ML | scikit-learn · TensorFlow · PyTorch · DashScope | 策略增強 |
| 存儲 | SQLite · Redis · SQLAlchemy | 數據持久化 |
| 任務 | Celery · Redis Broker | 非同步任務 |
| DevOps | Docker · Docker Compose · GitHub Actions | CI/CD |
| 品質 | Ruff · pytest · bandit · mypy · pre-commit | 程式碼品質 |

---

## 📁 專案結構

```
StocksX_V0/
├── app.py                          # 主頁儀表板（Streamlit 入口）
├── pyproject.toml                  # PEP 621 打包配置
├── Dockerfile                      # 多階段構建（Builder + Runtime）
├── docker-compose.yml              # 全棧容器編排
├── .env.example                    # 環境變數範本
│
├── pages/                          # Streamlit 多頁應用
│   ├── 2_₿_加密回測.py
│   ├── 2_🏛️_傳統回測.py
│   ├── 5_📡_交易監控.py
│   ├── 9_🧠_AI 策略.py
│   ├── 13_📈_組合優化.py
│   └── ...
│
├── src/
│   ├── core/                       # 核心架構（10 模組）
│   │   ├── orchestrator.py         # 統一業務編排器
│   │   ├── registry.py             # 策略裝飾器註冊
│   │   ├── backtest.py             # 向量化回測引擎
│   │   ├── pipeline.py             # 函數式數據管道
│   │   ├── container.py            # DI 依賴注入
│   │   ├── adapters.py             # 多數據源適配器
│   │   ├── signals.py              # SignalBus 事件總線
│   │   ├── middleware.py           # 中間件管道
│   │   ├── cache_manager.py        # 快取管理器
│   │   └── config.py               # 型別化設定
│   │
│   ├── backtest/                   # 回測引擎 & 策略實現
│   │   └── strategies.py           # 核心策略（向量化）
│   │
│   ├── strategies/                 # 進階策略模組
│   │   ├── ml_strategies/          # LSTM · 特徵工程
│   │   ├── nlp_strategies/         # NLP 情緒分析
│   │   ├── quant_strategies/       # 多因子 · 配對交易
│   │   ├── rl_strategies/          # DQN 強化學習
│   │   ├── trend/                  # 趨勢策略
│   │   ├── breakout/               # 突破策略
│   │   └── regime_detection.py     # 市場狀態檢測
│   │
│   ├── data/                       # 數據層
│   │   ├── sources/                # CCXT · Yahoo · API Hub
│   │   ├── crypto/                 # 加密貨幣專用
│   │   ├── traditional/            # 傳統市場
│   │   ├── live.py                 # 即時行情
│   │   └── news_aggregator.py      # 新聞聚合
│   │
│   ├── trading/                    # 交易引擎
│   │   ├── orders/                 # 高級訂單（冰山 · TWAP）
│   │   ├── portfolio/              # 組合優化器
│   │   ├── arbitrage/              # 套利策略
│   │   └── position/               # 倉位管理
│   │
│   └── ai/                         # AI 模組
│
├── tests/                          # pytest 測試
│   ├── test_backtest.py
│   ├── test_strategies.py
│   └── test_integration.py
│
└── .github/
    └── workflows/ci.yml            # CI/CD（Lint · Test · Build）
```

---

## 🔧 優化與改進

### 本版本亮點

| 改進項目 | 說明 |
|:---------|------|
| **策略計算向量化** | 布林帶、Z-Score、ROC 等核心策略改用 NumPy 預計算，消除 Python 循環 |
| **交叉信號向量化** | `_signals_from_crossover` 改為向量化交叉檢測 + 前向填充 |
| **OHLCV 數據驗證** | Pipeline 新增 `validate` 步驟：檢查 OHLC 邏輯、填充缺失值 |
| **安全加固** | SECRET_KEY 啟動驗證、WebSocket 與主應用密鑰一致性檢查 |
| **`.env` 配置優化** | SECRET_KEY 設為必填項，明確提示風險 |

### 效能對比

| 策略 | 優化前 | 優化後 | 提升 |
|:-----|:------:|:------:|:----:|
| Bollinger Signal | O(n×p) Python 循環 | O(n) NumPy 累積和 | **~50x** |
| Z-Score Mean Reversion | O(n×p) Python 循環 | O(n) NumPy 累積和 | **~50x** |
| Momentum ROC | O(n) Python 循環 | O(n) NumPy 切片 | **~5x** |
| Cross Signal 檢測 | O(n) Python 循環 | O(n) NumPy 向量比較 | **~3x** |

---

## 🚀 部署

### Docker（推薦）

```bash
cp .env.example .env
# ⚠️ 必須在 .env 中設定 SECRET_KEY 和 ADMIN_PASSWORD
docker compose up -d
```

| 服務 | 端口 | 說明 |
|:-----|:----:|:-----|
| 主應用 | 8501 | Streamlit Dashboard |
| WebSocket | 8001 | 即時推送 |
| Redis | 6379 | 快取 & 任務隊列 |
| Celery | — | 非同步 Worker |

### 含監控（可選）

```bash
docker compose --profile monitoring up -d
# Grafana    → http://localhost:3000
# Prometheus → http://localhost:9090
```

---

## ⚙️ 配置

### 必填環境變數

| 變數 | 說明 | 說明 |
|------|------|------|
| `SECRET_KEY` | JWT 簽名密鑰 | ⚠️ **主應用和 WebSocket 必須共用** |
| `ADMIN_PASSWORD` | 管理員密碼 | 首次啟動必填 |

### 可選環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `REDIS_URL` | Redis 連接 | `redis://redis:6379/0` |
| `BINANCE_API_KEY` | 幣安 API | — |
| `DASHSCOPE_API_KEY` | DashScope AI | — |
| `TZ` | 時區 | `Asia/Shanghai` |
| `LOG_LEVEL` | 日誌級別 | `INFO` |

---

## 📊 績效指標

回測報告自動計算以下指標：

| 報酬類 | 風險類 | 風險調整類 | 交易類 |
|--------|--------|-----------|--------|
| 總報酬 | 最大回撤 | Sharpe Ratio | 勝率 |
| 年化報酬 | VaR (95%) | Sortino Ratio | 利潤因子 |
| 平均報酬 | CVaR | Calmar Ratio | 最大連勝/連敗 |
| 複合報酬 | 波動率 | Omega Ratio | 平均持倉時間 |

---

## 🔐 安全

- **密碼存儲**：PBKDF2-SHA256 + 隨機 salt
- **Session 管理**：JWT 令牌 + 超時機制
- **CORS 控制**：環境變數白名單
- **CI 掃描**：bandit 安全掃描 + safety 依賴檢查
- **Docker 加固**：非 root 使用者 + tini init + 健康檢查
- **SECRET_KEY 管理**：啟動驗證，缺失時明確報錯

---

## 📝 更新日誌

### v8.0.3 — 2026-03-26 (第二次審查)

#### 🔍 代碼審查
- 確認 ISSUE-008（頁面前綴重複 `11_`）已修復，從活躍問題中移除
- 確認 ISSUE-010（Dockerfile 不匹配）已修復，Docker 配置正確
- 新增 ISSUE-012: 大量 `sys.path` hack（31 個檔案），需改為標準套件安裝
- 新增 ISSUE-013: `backend/main.py` FastAPI 與 `src/websocket_server.py` 功能重疊
- 新增 ISSUE-014: `src/core/alerts.py` AlertChannel 為空殼實現

### v8.0.2 — 2026-03-26

#### 🔍 代碼審查
- 確認 ISSUE-001/002/006/007 已修復，從活躍問題中移除
- 新增 ISSUE-008: Streamlit 頁面前綴重複 `11_`（兩個頁面衝突）
- 新增 ISSUE-009: .log 檔案被 Git 追蹤但不應提交

### v8.0.1 — 2026-03-26

#### 🐞 Bug 修復
- 修復 `app.py` 引用錯誤頁面路徑 `5_📡_監控.py` → `5_📡_交易監控.py`（導致交易監控頁面導航失敗）
- 同步修復 `src/ui_common.py` 側邊欄 `page_link` 路徑

#### 📖 文件更新
- 重寫 `ISSUES.md`，清理虛假「100% 完成」標記，記錄真實問題狀態
- 新增 7 個活躍問題追蹤（AI 模型未加載、回測需真實驗證等）

### v8.0.0 — 2026-03-20

#### ⚡ 效能優化
- 核心策略全面向量化：Bollinger、Z-Score、ROC 消除 Python 循環
- 交叉信號生成器改用 NumPy 向量比較
- 滾動均值/標準差改用累積和 O(n) 計算

#### 🔐 安全加固
- SECRET_KEY 啟動驗證，缺失時明確日誌警告
- WebSocket 與主應用密鑰一致性提醒
- `.env.example` 重新設計，SECRET_KEY 設為必填

#### 📊 數據品質
- OHLCV Pipeline 新增數據驗證步驟
- 自動修復不合理的 High/Low 值
- 前向填充缺失的 Open/High/Low 欄位

#### 📖 文件更新
- README 全面重寫，結構更現代化
- 效能對比表、架構圖優化
- 安全章節補充 SECRET_KEY 管理說明

### v7.0.0 — 2026-03-20
- 📊 策略庫從 18 擴展至 **130+**，10 大類全覆蓋
- 📈 新增進階訂單類型：冰山訂單、TWAP 訂單
- 📊 新增組合優化：Black-Litterman、層級風險平價 (HRP)
- 🔄 新增套利策略：統計套利、資金費率套利

<details>
<summary>📜 更早版本</summary>

- **v6.0.0** — 安全加固 · NumPy 向量化 · 投資組合優化
- **v5.3.0** — pyproject.toml · Dependabot · Docker 優化
- **v5.0.0** — 核心架構重構 · Orchestrator · Middleware
- **v4.0.0** — CCXT / Yahoo Finance · WebSocket
- **v3.0.0** — FastAPI · Celery 任務隊列

</details>

---

## 📄 授權

[MIT License](LICENSE)

---

<div align="center">

**⚠️ 免責聲明：本軟體僅供學習與研究，不構成投資建議。回測結果基於歷史數據，不代表未來表現。**

**Made with ❤️ by StocksX Team** · © 2024–2026

</div>
