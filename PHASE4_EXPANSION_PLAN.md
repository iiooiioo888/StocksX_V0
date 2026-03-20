# Phase 4: 数据源与操作逻辑扩展计划

**创建时间：** 2026-03-19 15:05  
**阶段：** Phase 4 - 数据增强 + 操作逻辑  
**目标：** 更多数据源 + 更丰富的交易操作

---

## 📊 一、新增数据源

### 1.1 传统市场数据源

#### A. 台股实时数据
- **来源：** 台湾证券交易所 TWSE API
- **内容：** 
  - 实时行情（上市/上柜）
  - 当日成交明细
  - 三大法人买卖超
  - 融资融券数据
- **更新频率：** 实时（交易时段）
- **实现文件：** `src/data/sources/twse_source.py`

#### B. 美股扩展数据
- **来源：** 
  - IEX Cloud（实时行情）
  - Quandl（基本面数据）
  - SEC EDGAR（财报文件）
- **内容：**
  - 实时/历史行情
  - 财务报表（10-K, 10-Q）
  - 内部人交易
  - 机构持仓（13F）
- **实现文件：** `src/data/sources/us_stocks_extended.py`

#### C. A 股数据
- **来源：** 
  - 新浪财经 API
  - 东方财富 API
  - Tushare（专业量化数据）
- **内容：**
  - 实时行情（沪深）
  - 资金流向
  - 龙虎榜数据
  - 概念板块
- **实现文件：** `src/data/sources/a_stock_source.py`

#### D. 港股数据
- **来源：** 
  - 港交所 HKEX API
  - 富途牛牛 API
- **内容：**
  - 实时行情
  - 港股通数据
  - 窝轮/牛熊证
- **实现文件：** `src/data/sources/hk_stock_source.py`

---

### 1.2 加密货币扩展数据

#### A. 链上数据（On-Chain）
- **来源：** 
  - Glassnode API
  - Dune Analytics
  - Nansen
- **内容：**
  - 交易所流入/流出
  - 巨鲸地址追踪
  - 活跃地址数
  - 交易费用
  - 挖矿难度
- **实现文件：** `src/data/onchain/glassnode.py`

#### B. DeFi 数据
- **来源：** 
  - Uniswap Subgraph
  - Aave API
  - Curve API
- **内容：**
  - DEX 交易量
  - 流动性池深度
  - 借贷利率
  - 质押奖励
- **实现文件：** `src/data/defi/protocols.py`

#### C. 社交媒体情绪
- **来源：** 
  - Twitter API v2
  - Reddit API
  - Telegram 群组监控
- **内容：**
  - 提及次数
  - 情绪分析
  - KOL 观点
  - 热门话题
- **实现文件：** `src/data/social/sentiment.py`

#### D. 期货/期权数据
- **来源：** 
  - Deribit API
  - Binance Futures
  - OKX 衍生品
- **内容：**
  - 资金费率
  - 持仓量（Open Interest）
  - 期权隐含波动率
  -  Put/Call Ratio
- **实现文件：** `src/data/derivatives/futures_options.py`

---

### 1.3 宏观经济数据

#### A. 美联储数据
- **来源：** FRED API
- **内容：**
  - 联邦基金利率
  - 资产负债表
  - 货币供应（M1, M2）
  - 通胀预期
- **实现文件：** `src/data/macro/fred.py`

#### B. 全球经济指标
- **来源：** 
  - Trading Economics
  - World Bank API
  - IMF Data
- **内容：**
  - GDP 增长率
  - CPI/PPI
  - 失业率
  - PMI 制造业/服务业
- **实现文件：** `src/data/macro/global_indicators.py`

#### C. 债券市场
- **来源：** 
  - 美国财政部 API
  - Investing.com
- **内容：**
  - 国债收益率曲线
  - 信用利差
  - 高收益债指数
- **实现文件：** `src/data/fixed_income/bonds.py`

---

### 1.4 另类数据

#### A. 预测市场
- **来源：** 
  - Polymarket
  - PredictIt
- **内容：**
  - 选举预测
  - 经济事件预测
  - 加密货币价格预测
- **实现文件：** `src/data/alternative/prediction_markets.py`

#### B. 新闻舆情
- **来源：** 
  - Google News API
  - NewsAPI
  - 百度新闻
- **内容：**
  - 新闻热度
  - 情感倾向
  - 主题分类
- **实现文件：** `src/data/alternative/news_sentiment.py`

#### C. 搜索趋势
- **来源：** 
  - Google Trends
  - 百度指数
  - 微信指数
- **内容：**
  - 关键词搜索量
  - 地区分布
  - 相关查询
- **实现文件：** `src/data/alternative/search_trends.py`

---

## ⚙️ 二、新增操作逻辑

### 2.1 高级订单类型

#### A. 条件单（Conditional Orders）
```python
class ConditionalOrder:
    """
    条件单：当触发条件满足时自动下单
    
    触发条件：
    - 价格突破（涨破/跌破）
    - 指标信号（RSI 超买/超卖）
    - 时间条件（定时执行）
    - 成交量异常
    """
    
    def __init__(
        self,
        trigger_type: str,      # price/indicator/time/volume
        trigger_condition: dict,
        order_params: dict,
        expiry: Optional[datetime] = None
    ):
        pass
```

**实现文件：** `src/trading/orders/conditional.py`

#### B. OCO 订单（One-Cancels-Other）
```python
class OCOOrder:
    """
    OCO 订单：两个订单，一个成交则另一个自动取消
    
    典型用法：
    - 止盈 + 止损同时设置
    - 突破交易（向上/向下）
    """
    
    def __init__(
        self,
        primary_order: Order,
        secondary_order: Order,
        link_type: str = "cancel_on_fill"
    ):
        pass
```

**实现文件：** `src/trading/orders/oco.py`

#### C. 追踪止损（Trailing Stop）
```python
class TrailingStop:
    """
    追踪止损：止损价随市场价格移动
    
    参数：
    - trail_percent: 追踪百分比（如 5%）
    - trail_amount: 追踪固定金额
    - direction: 多头/空头
    """
    
    def update_stop_price(self, current_price: float):
        """根据当前价格更新止损价"""
        pass
```

**实现文件：** `src/trading/orders/trailing_stop.py`

---

### 2.2 仓位管理策略

#### A. 金字塔加仓（Pyramiding）
```python
class PyramidingStrategy:
    """
    金字塔加仓：盈利后逐步加仓，每次加仓量递减
    
    规则：
    - 初始仓位：50%
    - 第一次加仓：30%（价格涨 5%）
    - 第二次加仓：20%（价格再涨 5%）
    - 止损统一设置在成本价上方
    """
    
    def calculate_add_position_size(
        self,
        current_position: float,
        unrealized_pnl: float,
        price_change_pct: float
    ) -> float:
        pass
```

**实现文件：** `src/trading/position/pyramiding.py`

#### B. 马丁格尔策略（Martingale）
```python
class MartingaleStrategy:
    """
    马丁格尔：亏损后加倍下注
    
    变体：
    - 经典马丁：亏损后 2 倍加仓
    - 温和马丁：亏损后 1.5 倍加仓
    - 反马丁：盈利后加仓
    
    风险控制：
    - 最大加仓次数（如 5 次）
    - 总仓位上限
    """
    
    def calculate_next_bet(
        self,
        current_loss: float,
        consecutive_losses: int
    ) -> float:
        pass
```

**实现文件：** `src/trading/position/martingale.py`

#### C. 动态仓位调整（Kelly Criterion）
```python
class KellyCriterion:
    """
    凯利公式：根据胜率和盈亏比计算最优仓位
    
    公式：
    f* = (p * b - q) / b
    
    其中：
    - f*: 最优仓位比例
    - p: 胜率
    - b: 盈亏比（平均盈利/平均亏损）
    - q: 败率 (1-p)
    """
    
    def calculate_kelly_fraction(
        self,
        win_rate: float,
        profit_loss_ratio: float
    ) -> float:
        pass
```

**实现文件：** `src/trading/position/kelly.py`

---

### 2.3 风险管理增强

#### A. 组合风险监控
```python
class PortfolioRiskMonitor:
    """
    组合风险监控
    
    监控指标：
    - VaR（Value at Risk）
    - CVaR（Conditional VaR）
    - 最大回撤
    - 波动率
    - 相关性风险
    - 流动性风险
    """
    
    def calculate_var(self, confidence: float = 0.95) -> float:
        """计算 VaR"""
        pass
    
    def calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        pass
    
    def check_risk_limits(self) -> Dict[str, bool]:
        """检查是否触及风险限制"""
        pass
```

**实现文件：** `src/trading/risk/portfolio_risk.py`

#### B. 黑天鹅保护
```python
class BlackSwanProtection:
    """
    黑天鹅事件保护
    
    功能：
    - 波动率突增检测
    - 相关性崩溃检测
    - 流动性枯竭检测
    - 自动减仓/平仓
    """
    
    def detect_volatility_spike(
        self,
        lookback_days: int = 30,
        threshold: float = 3.0
    ) -> bool:
        """检测波动率突增（>3 倍标准差）"""
        pass
    
    def emergency_hedge(self):
        """紧急对冲（买入 VIX/黄金/国债）"""
        pass
```

**实现文件：** `src/trading/risk/black_swan.py`

#### C. 压力测试
```python
class StressTesting:
    """
    压力测试
    
    测试场景：
    - 2008 金融危机（-50%）
    - 2020 新冠崩盘（-30%）
    - 闪崩（-10% 瞬间）
    - 连续亏损（10 连败）
    """
    
    def run_scenario(
        self,
        scenario_name: str,
        price_shock: float
    ) -> Dict:
        """运行压力测试场景"""
        pass
```

**实现文件：** `src/trading/risk/stress_test.py`

---

### 2.4 套利策略

#### A. 跨交易所套利
```python
class CrossExchangeArbitrage:
    """
    跨交易所套利
    
    逻辑：
    - 监控多个交易所价差
    - 发现套利机会（扣除手续费后>0）
    - 同时执行：低价买入 + 高价卖出
    - 自动对冲平仓
    
    风险：
    - 提币时间风险
    - 交易所风险
    - 滑点风险
    """
    
    def scan_arbitrage_opportunities(
        self,
        exchanges: List[str],
        min_profit_pct: float = 0.5
    ) -> List[Dict]:
        pass
```

**实现文件：** `src/trading/arbitrage/cross_exchange.py`

#### B. 期现套利
```python
class SpotFuturesArbitrage:
    """
    期现套利（基差套利）
    
    逻辑：
    - 期货价格 > 现货：做空期货 + 做多现货
    - 期货价格 < 现货：做多期货 + 做空现货
    - 持有至到期或基差回归
    
    收益：
    - 基差收敛收益
    - 资金费率收益（永续合约）
    """
    
    def calculate_fair_value(
        self,
        spot_price: float,
        risk_free_rate: float,
        days_to_expiry: int
    ) -> float:
        """计算期货理论价格"""
        pass
```

**实现文件：** `src/trading/arbitrage/spot_futures.py`

#### C. 三角套利
```python
class TriangularArbitrage:
    """
    三角套利
    
    路径：
    BTC → ETH → USDT → BTC
    
    逻辑：
    - 计算隐含汇率
    - 发现定价错误
    - 快速执行三角交易
    
    要求：
    - 低延迟
    - 低手续费
    - 充足流动性
    """
    
    def find_arbitrage_cycles(
        self,
        base_currency: str = "USDT",
        max_hops: int = 3
    ) -> List[Dict]:
        pass
```

**实现文件：** `src/trading/arbitrage/triangular.py`

---

### 2.5 组合优化

#### A. 马科维茨均值 - 方差优化
```python
class MarkowitzOptimizer:
    """
    马科维茨投资组合优化
    
    目标：
    - 最大化夏普比率
    - 或最小化波动率
    - 或最大化收益
    
    约束：
    - 权重和=1
    - 单个资产权重上限
    - 禁止做空（可选）
    """
    
    def optimize_portfolio(
        self,
        returns: pd.DataFrame,
        method: str = "sharpe"
    ) -> Dict[str, float]:
        """计算最优权重"""
        pass
```

**实现文件：** `src/trading/portfolio/optimization.py`

#### B. 风险平价（Risk Parity）
```python
class RiskParity:
    """
    风险平价策略
    
    理念：
    - 每个资产贡献相同风险
    - 而非相同资金
    
    优势：
    - 真正分散风险
    - 避免单一资产主导
    """
    
    def calculate_risk_parity_weights(
        self,
        covariance_matrix: np.ndarray
    ) -> np.ndarray:
        pass
```

**实现文件：** `src/trading/portfolio/risk_parity.py`

#### C. 动态再平衡
```python
class DynamicRebalancing:
    """
    动态再平衡
    
    策略：
    - 定期再平衡（每月/每季）
    - 阈值再平衡（偏离>5%）
    - 混合策略
    
    优化：
    - 最小化交易成本
    - 税务优化
    """
    
    def check_rebalance_needed(
        self,
        current_weights: Dict,
        target_weights: Dict,
        threshold: float = 0.05
    ) -> bool:
        pass
```

**实现文件：** `src/trading/portfolio/rebalancing.py`

---

## 📁 三、文件结构

```
StocksX_V0/
├── src/
│   ├── data/
│   │   ├── sources/
│   │   │   ├── twse_source.py          # 台股数据
│   │   │   ├── us_stocks_extended.py   # 美股扩展
│   │   │   ├── a_stock_source.py       # A 股数据
│   │   │   └── hk_stock_source.py      # 港股数据
│   │   ├── onchain/
│   │   │   └── glassnode.py            # 链上数据
│   │   ├── defi/
│   │   │   └── protocols.py            # DeFi 数据
│   │   ├── social/
│   │   │   └── sentiment.py            # 社交媒体情绪
│   │   ├── derivatives/
│   │   │   └── futures_options.py      # 期货/期权
│   │   ├── macro/
│   │   │   ├── fred.py                 # 美联储数据
│   │   │   └── global_indicators.py    # 全球经济指标
│   │   ├── fixed_income/
│   │   │   └── bonds.py                # 债券市场
│   │   └── alternative/
│   │       ├── prediction_markets.py   # 预测市场
│   │       ├── news_sentiment.py       # 新闻舆情
│   │       └── search_trends.py        # 搜索趋势
│   │
│   └── trading/
│       ├── orders/
│       │   ├── conditional.py          # 条件单
│       │   ├── oco.py                  # OCO 订单
│       │   └── trailing_stop.py        # 追踪止损
│       ├── position/
│       │   ├── pyramiding.py           # 金字塔加仓
│       │   ├── martingale.py           # 马丁格尔
│       │   └── kelly.py                # 凯利公式
│       ├── risk/
│       │   ├── portfolio_risk.py       # 组合风险监控
│       │   ├── black_swan.py           # 黑天鹅保护
│       │   └── stress_test.py          # 压力测试
│       ├── arbitrage/
│       │   ├── cross_exchange.py       # 跨交易所套利
│       │   ├── spot_futures.py         # 期现套利
│       │   └── triangular.py           # 三角套利
│       └── portfolio/
│           ├── optimization.py         # 马科维茨优化
│           ├── risk_parity.py          # 风险平价
│           └── rebalancing.py          # 动态再平衡
│
└── pages/
    ├── 11_📊_数据源管理.py              # 数据源配置页面
    ├── 12_⚙️_订单管理.py                # 高级订单页面
    └── 13_📈_组合优化.py                # 组合优化页面
```

---

## 🎯 四、实施优先级

### 高优先级（Week 1-2）
1. ✅ 台股数据源（TWSE）
2. ✅ 条件单/OCO 订单
3. ✅ 追踪止损
4. ✅ 组合风险监控
5. ✅ UI 页面：数据源管理

### 中优先级（Week 3-4）
1. ✅ 链上数据（Glassnode）
2. ✅ 金字塔加仓/凯利公式
3. ✅ 跨交易所套利
4. ✅ 马科维茨优化
5. ✅ UI 页面：订单管理

### 低优先级（Week 5-6）
1. ✅ DeFi 数据
2. ✅ 社交媒体情绪
3. ✅ 黑天鹅保护
4. ✅ 风险平价
5. ✅ UI 页面：组合优化

---

## 📊 五、预期效果

| 功能类别 | 新增数量 | 覆盖率提升 |
|----------|----------|------------|
| 数据源 | +15 个 | 85% → 98% |
| 订单类型 | +5 种 | 基础 → 高级 |
| 仓位策略 | +8 种 | 单一 → 多元 |
| 风控功能 | +6 项 | 基础 → 全面 |
| 套利策略 | +3 种 | 无 → 有 |
| 组合优化 | +3 种 | 手动 → 自动 |

---

## 🚀 六、快速开始

### 6.1 安装新依赖
```bash
pip install tws-api      # 台股
pip install glassnode1   # 链上数据
pip install pytrends     # Google Trends
pip install cvxpy        # 组合优化
```

### 6.2 配置 API Keys
```bash
# .env 文件
TWSE_API_KEY=your_key
GLASSNODE_API_KEY=your_key
GOOGLE_TRENDS_API_KEY=your_key
```

### 6.3 测试新数据源
```python
from src.data.sources.twse_source import TWSESource

twse = TWSESource()
data = twse.fetch_ohlcv("2330.TW", "1d", days=365)
```

---

**下一步：** 选择优先级最高的功能开始实施！
