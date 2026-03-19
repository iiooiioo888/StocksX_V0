# StocksX — 架構設計文檔 (v4.2)

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────────┐
│                        UI Layer (Streamlit)                          │
│  pages/*.py ──→ Orchestrator (統一編排入口)                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                       src/core/ — 核心架構                          │
│                                                                     │
│  ┌───────────────┐ ┌───────────────┐ ┌────────────────────────┐    │
│  │  Orchestrator  │ │   Registry    │ │   SignalBus (Pub/Sub)  │    │
│  │  (統一編排)    │ │ (裝飾器註冊)   │ │  (事件驅動信號)        │    │
│  └───────────────┘ └───────────────┘ └────────────────────────┘    │
│                                                                     │
│  ┌───────────────┐ ┌───────────────┐ ┌────────────────────────┐    │
│  │  Pipeline      │ │  BacktestEng. │ │  Middleware Pipeline    │    │
│  │ (函數式管道)   │ │ (信號驅動回測) │ │ (日誌/限流/重試)       │    │
│  └───────────────┘ └───────────────┘ └────────────────────────┘    │
│                                                                     │
│  ┌───────────────┐ ┌───────────────┐ ┌────────────────────────┐    │
│  │ CacheManager  │ │  Repository   │ │  TaskQueue             │    │
│  │ (Redis/Dict)  │ │ (CRUD 抽象)   │ │ (線程池/Celery)        │    │
│  └───────────────┘ └───────────────┘ └────────────────────────┘    │
│                                                                     │
│  ┌───────────────┐ ┌───────────────┐ ┌────────────────────────┐    │
│  │ AlertManager  │ │ DI Container  │ │  Typed Settings         │    │
│  │ (告警規則引擎) │ │ (依賴注入)    │ │ (dataclass 配置)        │    │
│  └───────────────┘ └───────────────┘ └────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                        Provider Adapters                            │
│  ┌───────────────┐ ┌───────────────┐ ┌────────────────────────┐    │
│  │ CCXTProvider   │ │ YahooProvider │ │  CompositeProvider     │    │
│  │ (11 交易所)    │ │ (美股/台股)   │ │  (自動路由)            │    │
│  └───────────────┘ └───────────────┘ └────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## 文件結構

```
src/core/
├── __init__.py            # 統一導出（40+ 符號）
├── config.py              # Typed Settings (frozen dataclass)
├── provider.py            # MarketProvider Protocol + CacheBackend
├── adapters.py            # CCXTProvider / YahooProvider / CompositeProvider
├── signals.py             # Signal, Direction, SignalBus (Pub/Sub)
├── pipeline.py            # Pipeline (composable steps)
├── backtest.py            # BacktestEngine, BacktestConfig, BacktestReport
├── registry.py            # StrategyRegistry (decorator-based)
├── strategies_bridge.py   # Auto-migrate old strategies to Registry
├── orchestrator.py        # Orchestrator (unified API)
├── middleware.py           # MiddlewarePipeline (logging/retry/ratelimit)
├── cache_manager.py       # CacheManager (namespace + stats)
├── repository.py          # BacktestRepository (Protocol + SQLite impl)
├── tasks.py               # ThreadTaskQueue (background jobs)
├── alerts.py              # AlertManager (rules + channels)
└── container.py           # DI Container (lazy init all components)
```

## 組件詳解

### 1. Typed Settings (`config.py`)

```python
@dataclass(frozen=True, slots=True)
class Settings:
    app: AppSettings          # env, debug, port, tz, log_level
    cache: CacheSettings      # redis_url, TTLs
    exchange: ExchangeSettings # API keys
    data_api: DataApiSettings  # third-party keys
    backtest: BacktestDefaults # equity, leverage, fees

settings = get_settings()
settings.backtest.initial_equity  # → 10000.0
```

**改進**：不可變 (frozen)、型別安全、統一入口、延遲加載。

### 2. MarketProvider Protocol (`provider.py`)

```python
@runtime_checkable
class MarketProvider(Protocol):
    def supports(self, symbol: str) -> bool: ...
    def fetch_ohlcv(self, symbol, timeframe, since, limit) -> list[OHLCV]: ...
    def fetch_ticker(self, symbol) -> Ticker | None: ...
    def fetch_orderbook(self, symbol, limit) -> OrderBook | None: ...
```

**改進**：取代 God Object DataService，每個 Adapter 專注一個數據源。

### 3. CompositeProvider (`adapters.py`)

自動根據 symbol 格式路由：
- `BTC/USDT` → CCXTProvider
- `AAPL` → YahooProvider

### 4. SignalBus (`signals.py`)

```python
bus = get_signal_bus()
bus.subscribe(my_handler, pattern="BTC/USDT")
bus.publish(Signal(symbol="BTC/USDT", strategy="sma_cross", direction=Direction.LONG))
```

**改進**：事件驅動解耦，多策略可發布，訂閱者自動接收。

### 5. Pipeline (`pipeline.py`)

```python
pipeline = ohlcv_clean_pipeline()  # 去重 → 排序 → 去零量
rows = pipeline.run(raw_rows)

# 自定義
p = Pipeline("custom")
p.add(lambda rows: [r for r in rows if r["volume"] > 1000])
p.add(lambda rows: sorted(rows, key=lambda r: r["timestamp"]))
```

### 6. BacktestEngine (`backtest.py`)

```python
engine = BacktestEngine(config=BacktestConfig(
    leverage=5, stop_loss_pct=3, fee_rate_pct=0.05
))
report = engine.run(rows, signals, since_ms, until_ms)
# → BacktestReport (equity_curve, trades, 15+ metrics)
```

### 7. StrategyRegistry (`registry.py`)

```python
@register_strategy(name="sma_cross", label="雙均線", category="trend")
def sma_cross(rows, fast=10, slow=30) -> list[int]: ...

registry.get("sma_cross")           # → StrategyEntry
registry.list_by_category("trend")  # → [...]
```

### 8. MiddlewarePipeline (`middleware.py`)

```python
pipe = MiddlewarePipeline("api_call")
pipe.use(LoggingMiddleware())
pipe.use(RateLimitMiddleware(rps=10))
pipe.use(TimingMiddleware())
result = pipe.execute(lambda: provider.fetch_ohlcv(...))
```

**可用中間件**：Logging, Retry, RateLimit, Timing。

### 9. CacheManager (`cache_manager.py`)

```python
cm = get_cache_manager()
cm.price.set("BTC/USDT", ticker, ttl=1)
cm.kline.get_or_set("BTC/USDT:1h", lambda: fetch_klines(...), ttl=300)
cm.all_stats()  # → {"price": {"hits": 10, "misses": 2, ...}}
```

**改進**：命名空間隔離、統計監控、cache-aside 模式。

### 10. Repository (`repository.py`)

```python
repo = get_backtest_repository()
record = BacktestRecord(user_id=1, symbol="BTC/USDT", strategy="sma_cross", ...)
record_id = repo.save(record)
records = repo.find_by_user(user_id=1, limit=20)
```

**改進**：Protocol 介面，可替換為 PostgreSQL。

### 11. TaskQueue (`tasks.py`)

```python
queue = get_task_queue()
task_id = queue.submit("backtest", run_backtest, args=(symbol, strat))
status = queue.status(task_id)  # → TaskInfo(status=RUNNING)
result = queue.result(task_id, timeout=30)
```

### 12. AlertManager (`alerts.py`)

```python
am = get_alert_manager()
am.add_rule(AlertRule(
    name="high_dd",
    condition=lambda m: m.get("max_drawdown_pct", 0) > 20,
    message_template="⚠️ 回撤 {max_drawdown_pct:.1f}%",
    severity=AlertSeverity.CRITICAL,
))
am.check(metrics_dict)  # → [Alert(...)]
```

**通知渠道**：LogChannel, BarkChannel (iOS), WebhookChannel。

### 13. DI Container (`container.py`)

```python
container = get_container()
settings = container.get(Settings)
provider = container.get(MarketProvider)
cache = container.get(CacheBackend)

# 測試時替換
container.register(MarketProvider, MockProvider())
```

**改進**：取代全局單例，支持依賴替換（測試友好）。
