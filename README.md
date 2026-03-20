<div align="center">

<img src="https://github.com/iiooiioo888/StocksX_V0/blob/main/assets/logo.png" alt="StocksX" width="100" />

# StocksX

#### 機構級量化交易與投資組合管理平台

<p>
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/streamlit-1.32+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/fastapi-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" />
  <img src="https://img.shields.io/github/last-commit/iiooiioo888/StocksX_V0?style=flat-square&color=green" />
</p>

<p><b>130+ 種量化策略 · 10 大類 · 多市場回測 · 投資組合優化 · AI 驅動 · 即時監控</b></p>

[快速開始](#-快速開始) · [策略庫](#-策略庫) · [架構](#️-架構) · [部署](#-部署)

</div>

---

## ⚡ 快速開始

```bash
git clone https://github.com/iiooiioo888/StocksX_V0.git && cd StocksX_V0
cp .env.example .env && docker compose up -d
# 👉 http://localhost:8501
```

---

## 🧩 核心能力

<table>
<tr>
<td width="50%">

### ⚡ 高效能回測引擎
- NumPy 向量化優化，提速 **10–100x**
- 向量化 & 事件驅動雙模式
- 蒙地卡羅模擬（330,000+ 次）

</td>
<td width="50%">

### 🧠 AI 策略增強
- LSTM / Transformer 價格預測
- FinBERT 市場情緒分析
- DQN 強化學習交易

</td>
</tr>
<tr>
<td width="50%">

### 📊 投資組合優化
- Markowitz 均值-方差 · Black-Litterman
- 風險平價 · 層級風險平價 (HRP)
- 有效前沿視覺化

</td>
<td width="50%">

### 🌐 多市場覆蓋
- ₿ 加密貨幣（CCXT · 11 交易所）
- 🇺🇸 美股 · 🇹🇼 台股 · ETF
- 即時 WebSocket 推送

</td>
</tr>
</table>

---

## 📦 策略庫

> 10 大類 · 130+ 策略，覆蓋量化交易全鏈路

| 類別 | 數量 | 範例 |
|:-----|:---:|:-----|
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
<summary>📋 展開完整策略列表</summary>

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

## 🏗️ 架構

### 分層設計

```
┌──────────────────────────────────────────────────┐
│  🎨  表現層                                       │
│  Streamlit Dashboard · FastAPI REST+WS · Plotly   │
├──────────────────────────────────────────────────┤
│  ⚙️   應用層                                      │
│  Orchestrator · StrategyRegistry · SignalBus      │
├──────────────────────────────────────────────────┤
│  📐  領域層                                       │
│  回測引擎(向量化) · 130+ 策略 · 風控 · 組合優化     │
├──────────────────────────────────────────────────┤
│  🧩  基礎設施層                                    │
│  DI 容器 · 中間件 · 快取 · Repository · 任務隊列    │
├──────────────────────────────────────────────────┤
│  📡  數據層                                       │
│  CCXT · Yahoo Finance · CoinGecko · WebSocket     │
├──────────────────────────────────────────────────┤
│  💾  持久化層                                      │
│  SQLite · Redis 7 · PostgreSQL（可選）             │
└──────────────────────────────────────────────────┘
```

### 設計模式

| 模式 | 實現 | 作用 |
|:----:|------|------|
| **Orchestrator** | `core/orchestrator.py` | 統一業務入口 |
| **Registry** | `core/registry.py` | `@register` 自動註冊策略 |
| **Repository** | `core/repository.py` | 數據存取抽象 |
| **DI Container** | `core/container.py` | 輕量依賴注入 |
| **Middleware** | `core/middleware.py` | 日誌/重試/限流管道 |
| **Provider Composite** | `core/adapters.py` | 多數據源故障轉移 |

### 技術棧

| 層級 | 技術 |
|:-----|------|
| 前端 | Streamlit · Plotly · Glassmorphism CSS |
| API | FastAPI · Uvicorn · WebSocket |
| 數據 | Pandas · NumPy · yfinance · CCXT |
| AI/ML | scikit-learn · TensorFlow · PyTorch · DashScope |
| 存儲 | SQLite · Redis · SQLAlchemy |
| 任務 | Celery · Redis Broker |
| DevOps | Docker · GitHub Actions · Dependabot |
| 品質 | Ruff · pytest · bandit · mypy · pre-commit |

---

## 📁 專案結構

```
StocksX_V0/
├── app.py                          # 主頁儀表板
├── pyproject.toml                  # PEP 621 打包
├── Dockerfile / docker-compose.yml
│
├── pages/                          # Streamlit 多頁
│   ├── 2_₿_加密回測.py
│   ├── 5_📡_交易監控.py
│   ├── 9_🧠_AI 策略.py
│   ├── 13_📈_組合優化.py
│   └── ...
│
├── src/
│   ├── core/                       # 核心架構
│   ├── backtest/                   # 回測引擎 + 130+ 策略
│   ├── strategies/                 # 進階策略
│   │   ├── ml_strategies/          # LSTM / RL
│   │   ├── nlp_strategies/         # NLP 情緒
│   │   ├── quant_strategies/       # 多因子 / 配對
│   │   └── regime_detection.py     # 市場狀態
│   ├── data/                       # 數據源
│   │   ├── sources/                # CCXT / Yahoo / API Hub
│   │   ├── crypto/                 # 加密貨幣
│   │   └── traditional/            # 傳統市場
│   ├── trading/                    # 交易引擎
│   │   ├── orders/                 # 高級訂單（5 種）
│   │   ├── portfolio/              # 組合優化（4 種）
│   │   ├── arbitrage/              # 套利策略（4 種）
│   │   └── position/               # 倉位管理
│   └── ai/                         # AI 模型
│
├── tests/                          # pytest
└── .github/workflows/ci.yml        # CI/CD
```

---

## 🚀 部署

### Docker（推薦）

```bash
git clone https://github.com/iiooiioo888/StocksX_V0.git && cd StocksX_V0
cp .env.example .env && docker compose up -d
# 主應用  → http://localhost:8501
# WebSocket → ws://localhost:8001/ws
```

### 含監控

```bash
docker compose --profile monitoring up -d
# Grafana    → http://localhost:3000
# Prometheus → http://localhost:9090
```

### 本地開發

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
streamlit run app.py
```

---

## ⚙️ 配置

| 變數 | 說明 | 必填 |
|------|------|:----:|
| `SECRET_KEY` | JWT 簽名密鑰 | ✅ |
| `ADMIN_PASSWORD` | 管理員密碼 | ✅ |
| `DATABASE_URL` | 資料庫連接 | |
| `REDIS_URL` | Redis 連接 | |
| `BINANCE_API_KEY` | 幣安 API | |
| `DASHSCOPE_API_KEY` | DashScope AI | |

---

## 📊 績效指標

| 報酬 | 風險 | 風險調整 | 交易 |
|------|------|---------|------|
| 總報酬 | 最大回撤 | Sharpe | 勝率 |
| 年化報酬 | VaR (95%) | Sortino | 利潤因子 |
| 平均報酬 | CVaR | Calmar | 最大連勝/連敗 |
| | 波動率 | Omega Ratio | |

---

## 🔐 安全

- 密碼：PBKDF2-SHA256 + 隨機 salt
- Session：JWT 令牌 + 超時機制
- CORS：環境變數白名單
- CI：bandit 掃描 + safety 依賴檢查
- Docker：非 root 使用者 + tini init

---

## 📝 更新日誌

### v7.0.0 — 2026-03-20
- 📊 策略庫從 18 擴展至 **130+**，10 大類全覆蓋
- 📈 新增進階訂單類型：冰山訂單、TWAP 訂單
- 📊 新增組合優化：Black-Litterman、層級風險平價 (HRP)
- 🔄 新增套利策略：統計套利、資金费率套利、完善三角套利
- 🛡 全新風險管理類別（12 策略）
- ⏱ 全新微結構類別（12 策略）
- 🌐 全新跨市場類別（12 策略）

### v6.0.0 — 2026-03-20
- 🔒 安全加固 · ⚡ NumPy 向量化提速 10–100x
- 📊 投資組合優化 · 🔍 市場狀態檢測
- 📈 新增策略：Z-Score、ROC、Keltner Channel

<details>
<summary>📜 更早版本</summary>

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

⚠️ **本軟體僅供學習與研究，不構成投資建議。** 回測結果基於歷史數據，不代表未來表現。

**Made with ❤️ by StocksX Team** · © 2024–2026

</div>
