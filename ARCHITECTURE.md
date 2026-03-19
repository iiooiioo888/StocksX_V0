# StocksX — 新架構設計

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI Layer (Streamlit)                      │
│  pages/*.py  ──→  Orchestrator (統一入口)                        │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                     src/core/ — 核心架構                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Orchestrator │  │   Registry   │  │   SignalBus (Pub/Sub) │   │
│  │  (統一編排)   │  │  (策略註冊)   │  │   (事件驅動信號)      │   │
│  └──────┬───────┘  └──────────────┘  └──────────────────────┘   │
│         │                                                        │
│  ┌──────▼───────────────────────────────────────────────────┐   │
│  │                    BacktestEngine                         │   │
│  │  (Pipeline: Clean → Signal → Risk → Simulate → Report)   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  Pipeline     │  │  Provider    │  │  Config (Typed)      │   │
│  │  (函數式管道) │  │  (數據抽象)   │  │  (dataclass 設定)    │   │
│  └──────────────┘  └──────┬───────┘  └─────────────────────┘   │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Provider Adapters                            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ CCXTProvider  │  │ YahooProvider│  │  CompositeProvider   │   │
│  │ (11 交易所)   │  │ (美股/台股)   │  │  (自動路由)          │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │  DictCache    │  │  RedisCache  │  (CacheBackend Protocol)   │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

## 核心組件

### 1. Typed Settings (`src/core/config.py`)

**問題**：舊架構的 config 散落在 3 個文件，無型別驗證。

**新設計**：
```python
@dataclass(frozen=True, slots=True)
class Settings:
    app: AppSettings          # 應用配置
    cache: CacheSettings      # 快取配置
    exchange: ExchangeSettings # 交易所金鑰
    data_api: DataApiSettings  # 數據 API 金鑰
    backtest: BacktestDefaults # 回測預設

# 用法
from src.core import get_settings
settings = get_settings()
settings.backtest.initial_equity  # → 10000.0
```

### 2. MarketProvider Protocol (`src/core/provider.py`)

**問題**：DataService 是 God Object，CryptoDataFetcher + DataService 雙重抽象。

**新設計**：Protocol 介面 + 具體 Adapter。

```python
@runtime_checkable
class MarketProvider(Protocol):
    @property
    def name(self) -> str: ...
    def supports(self, symbol: str) -> bool: ...
    def fetch_ohlcv(self, symbol, timeframe, since, limit) -> list[OHLCV]: ...
    def fetch_ticker(self, symbol) -> Ticker | None: ...
    def fetch_orderbook(self, symbol, limit) -> OrderBook | None: ...
```

### 3. Composable Pipeline (`src/core/pipeline.py`)

**問題**：數據清洗邏輯散落在各處，無法複用。

**新設計**：
```python
pipeline = ohlcv_clean_pipeline()  # 去重 → 排序 → 去零量
rows = pipeline.run(raw_rows)
```

### 4. Signal Bus (`src/core/signals.py`)

**問題**：信號計算和交易執行耦合。

**新設計**：Publish/Subscribe 事件模式。
```python
bus = get_signal_bus()
bus.subscribe(my_handler, pattern="BTC/USDT")
bus.publish(Signal(symbol="BTC/USDT", strategy="sma_cross", direction=Direction.LONG))
```

### 5. Strategy Registry (`src/core/registry.py`)

**問題**：`_STRATEGY_FUNCS` 手動字典，無法攜帶元數據。

**新設計**：裝飾器自動註冊。
```python
@register_strategy(name="sma_cross", label="雙均線交叉", category="trend")
def sma_cross(rows, fast=10, slow=30) -> list[int]: ...

registry.get("sma_cross")           # → StrategyEntry
registry.list_by_category("trend")  # → [...]
```

### 6. Backtest Engine (`src/core/backtest.py`)

**問題**：engine.py + engine_vec.py 重複邏輯。

**新設計**：單一 `BacktestEngine`，接受 Pipeline + 信號。
```python
engine = BacktestEngine(config=BacktestConfig(leverage=5, stop_loss_pct=3))
report = engine.run(rows, signals, since_ms, until_ms)
# → BacktestReport (equity_curve, trades, metrics)
```

### 7. Orchestrator (`src/core/orchestrator.py`)

**問題**：業務邏輯散落在各 Streamlit Page。

**新設計**：統一入口，屏蔽組合細節。
```python
orch = get_orchestrator()
result = orch.run_backtest("BTC/USDT:USDT", "1h", "sma_cross", fast=10, slow=30)
ticker = orch.get_ticker("AAPL")
```

## 文件結構

```
src/core/
├── __init__.py            # 統一導出
├── config.py              # Typed Settings (dataclass)
├── provider.py            # MarketProvider Protocol + CacheBackend
├── adapters.py            # CCXTProvider, YahooProvider, CompositeProvider
├── signals.py             # Signal, Direction, SignalBus
├── pipeline.py            # Pipeline (composable steps)
├── backtest.py            # BacktestEngine, BacktestConfig, BacktestReport
├── registry.py            # StrategyRegistry (decorator-based)
├── strategies_bridge.py   # Auto-migrate old strategies to Registry
└── orchestrator.py        # Orchestrator (unified API)
```
