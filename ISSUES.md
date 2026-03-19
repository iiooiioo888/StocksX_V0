# 🔍 StocksX V0 — 問題分析報告

> 生成時間：2026-03-20  
> 版本：v5.3.0  
> 分析範圍：全量代碼（158 個 Python 文件，~16,000 行）

---

## 📊 問題總覽

| 嚴重程度 | 數量 | 說明 |
|:---:|:---:|------|
| 🔴 高 | 12 | 架構問題、安全隱患、生產風險 |
| 🟡 中 | 16 | 代碼重複、設計不一致、效能隱患 |
| 🟢 低 | 12 | 可改進項、風格問題 |
| **合計** | **40** | |

---

## 🔴 高優先級問題

### 1. 安全：硬編碼預設管理員密碼 `admin123`

**文件：** `src/core/config.py:191`

```python
return _env("ADMIN_PASSWORD", "admin123") or "admin123"
```

**風險：** 如果用戶忘記設置環境變數，任何人可以用 `admin123` 登入管理員帳號。

**修復：** 改為首次啟動時自動生成隨機密碼並打印到日誌，或強制要求設置。

---

### 2. 安全：CORS 允許所有來源 `allow_origins=["*"]`

**文件：** `src/websocket_server.py:52`

```python
allow_origins=["*"],
```

**風險：** 任何網站都可以向 WebSocket 服務發起跨域請求，可能導致 CSRF 攻擊。

**修復：** 改為具體的域名白名單，或從環境變數讀取。

---

### 3. 安全：API Key 直接作為 URL 參數傳遞

**文件：** `src/data/sources/api_hub.py`（多處）

```python
params.setdefault("api_key", api_key)        # FRED, Glassnode
params.setdefault("apikey", api_key)          # Alpha Vantage, FMP
params.setdefault("x_cg_pro_api_key", ...)   # CoinGecko
```

**風險：** API Key 出現在 URL 中，會被記錄在服務器日誌、瀏覽器歷史、代理服務器中。

**修復：** 儘量使用 HTTP Header 傳遞 API Key（如 CoinMarketCap 的做法）。

---

### 4. 安全：FastAPI `@app.on_event("startup")` 已棄用

**文件：** `src/websocket_server.py:278`、`src/websocket_binance.py:348`

```python
@app.on_event("startup")
async def startup() -> None:
```

**風險：** FastAPI 0.109+ 已棄用 `on_event`，未來版本會移除。應使用 `lifespan` 上下文管理器。

**修復：**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    task = asyncio.create_task(price_push_loop())
    yield
    # shutdown
    task.cancel()
```

---

### 5. 架構：新舊回測引擎並存（未完成遷移）

**舊引擎（未棄用）：**
- `src/backtest/engine.py` — 13,880 bytes，192 行 `_run_backtest_on_rows`
- `src/backtest/engine_vec.py` — 6,574 bytes，169 行向量化引擎

**新引擎：**
- `src/core/backtest.py` — 14,839 bytes

**問題：** 兩套引擎同時存在，舊引擎被 `src/ui_backtest.py`、`src/compat.py` 直接使用。維護成本翻倍。

---

### 6. 架構：策略實現三處重複

| 文件 | 大小 | 狀態 |
|------|------|------|
| `src/backtest/strategies.py` | 20,314 bytes | 被 UI 直接引用 |
| `src/core/registry.py` | 3,513 bytes | 新註冊中心 |
| `src/core/strategies_bridge.py` | 6,236 bytes | 橋接層 |

**問題：** 同一個 `sma_cross` 策略有三處定義或引用，新貢獻者容易混淆。

---

### 7. 架構：配置碎片化（三個配置文件）

| 文件 | 職責 | 衝突 |
|------|------|------|
| `src/config.py` | 策略標籤、顏色、市場分類、CSS | 導出 `Settings`（向後兼容） |
| `src/config_secrets.py` | API 金鑰管理 | 與 `DataApiSettings` 重疊 |
| `src/core/config.py` | Typed Settings dataclass | 定義 `Settings` 和 `get_settings` |

**問題：** 15+ 個文件從 `src.config` 導入，3 個從 `src.config_secrets` 導入，部分從 `src.core.config` 導入。

---

### 8. 架構：`api_hub.py` 缺乏統一錯誤處理

**文件：** `src/data/sources/api_hub.py`

11 個 `return resp.json()` 調用中，只有 4 個在 `try/except` 塊中。其餘直接返回，如果 API 返回非 JSON 響應會導致崩潰。

**受影響的函數：**
- `fetch_polygon()` — 無 try/except
- `fetch_coingecko()` — 無 try/except
- `fetch_coinmarketcap()` — 無 try/except
- `fetch_glassnode()` — 無 try/except
- `fetch_trading_economics()` — 無 try/except
- `fetch_fmp()` — 無 try/except
- `fetch_alpaca()` — 無 try/except
- `fetch_fear_greed_index()` — 無 try/except

---

### 9. 架構：WebSocket 服務重複

| 文件 | 行數 | 引用數 |
|------|:---:|:---:|
| `src/websocket_server.py` | 450+ | 在用 |
| `src/websocket_binance.py` | 380 | **0**（死代碼） |

---

### 10. 架構：Walk-Forward 分析器重複

- `src/backtest/walk_forward.py` — 4,972 bytes
- `src/core/walk_forward.py` — 8,028 bytes

---

### 11. 架構：`advanced_strategies.py` 名稱衝突

- `src/backtest/advanced_strategies.py` — 24,527 bytes（ichimoku、hull_ma、vwap 等）
- `src/strategies/advanced_strategies.py` — 10,471 bytes（LSTM、情緒、組合策略）

同名不同內容，容易導入錯誤。

---

### 12. 安全：`unsafe_allow_html=True` 大量使用

**74 處** `unsafe_allow_html=True` 調用分散在 `src/` 和 `pages/` 中。

**風險：** 如果任何用戶輸入被嵌入 HTML，可能導致 XSS 攻擊。

---

## 🟡 中優先級問題

### 13. 代碼：66 個文件使用 f-string 日誌

```python
# ❌ 錯誤：無法被日誌聚合工具解析
logger.warning(f"取得價格失敗 {symbol}: {e}")

# ✅ 正確：結構化日誌
logger.warning("price_fetch_failed", extra={"symbol": symbol, "error": str(e)})
```

**影響：** 日誌無法被 ELK/Datadog/Splunk 正確索引和搜索。

---

### 14. 代碼：`datetime.now()` 缺少時區（10+ 文件）

```python
# ❌ 不同時區的機器結果不同
now = datetime.now()

# ✅ 應該使用 UTC
now = datetime.now(timezone.utc)
```

**涉及文件：** `src/data/service.py`、`src/data/indices.py`、`src/strategies/quant_strategies/multi_factor.py`、`src/strategies/advanced_strategies.py`、`src/strategies/nlp_strategies/sentiment_analyzer.py` 等。

---

### 15. 設計：42 個超過 80 行的函數

以下是超過 150 行的函數（最嚴重）：

| 文件 | 函數 | 行數 |
|------|------|:---:|
| `src/ui_auto_trade/strategy_config.py` | `render_strategy_configurator` | **293** |
| `src/ui_auto_trade/strategy_config.py` | `render_strategy_params` | 152 |
| `src/ui_auto_trade/dashboard.py` | `render_auto_trading_dashboard` | 220 |
| `src/ui_auto_trade/position_monitor.py` | `render_position_monitor` | 210 |
| `src/ui_auto_trade/trade_log.py` | `render_trade_log_viewer` | 216 |
| `src/ui_auto_trade/risk_manager_ui.py` | `render_position_size_calculator` | 205 |
| `src/backtest/optimizer.py` | `find_optimal_global` | 216 |
| `src/data/live_monitor.py` | `calculate_signal_for_symbol` | 201 |
| `src/ui_backtest_detail.py` | `render_backtest_detail` | 198 |
| `src/backtest/engine.py` | `_run_backtest_on_rows` | 192 |
| `src/backtest/engine_vec.py` | `_run_backtest_vectorized` | 169 |
| `src/tasks/backtest_tasks.py` | `run_param_optimizer` | 156 |
| `src/ui_backtest.py` | `render_kline_chart` | 153 |

**問題：** 超長函數難以測試、難以理解、難以維護。

---

### 16. 設計：219 個公開函數缺少 docstring

通過 AST 分析發現 219 個非私有函數沒有文檔字符串。

---

### 17. 設計：20 個模組缺少測試

**完全無測試的模組：**
- `src/core/adapters.py` — Provider 實現
- `src/core/strategies_bridge.py` — 策略橋接
- `src/core/walk_forward.py` — Walk-Forward 分析
- `src/backtest/optimizer.py` — 參數優化
- `src/backtest/position_sizing.py` — 倉位管理
- `src/data/async_fetcher.py` — 異步數據抓取
- `src/data/news_aggregator.py` — 新聞聚合
- `src/ai/qwen_client.py` — AI 客戶端
- `src/notify/bark.py` — 推播通知
- 等共 20 個模組

---

### 18. 設計：多處無界緩存可能導致內存泄漏

```python
_exchange_cache: dict[str, tuple[ccxt.Exchange, str]] = {}  # 無清理
self.price_cache: dict[str, dict] = {}                       # 無 TTL
self.kline_cache: dict[str, pd.DataFrame] = {}               # 無大小限制
_cache: dict[str, tuple[float, Any]] = {}                    # 只有 TTL 但無大小限制
```

**風險：** 長時間運行的服務可能因緩存增長導致 OOM。

---

### 19. 設計：全局單例無線程安全保護

```python
_orchestrator: Orchestrator | None = None       # 無鎖
_settings: Settings | None = None               # 無鎖
_data_service_instance: DataService | None = None  # 無鎖
_binance_spot: ccxt.binance | None = None       # 無鎖
```

**風險：** 多線程/異步環境下可能導致競態條件。

---

### 20. 設計：`start_auto_trading.bat` 只支援 Windows

v5.3.0 已新增 `start.sh`，但舊的 `.bat` 文件未被刪除。

---

### 21. 設計：根目錄放了測試和訓練腳本

- `test_strategies.py` — 應放在 `tests/`
- `train_lstm.py` — 應放在 `scripts/`

---

### 22. 設計：多處硬編碼 Redis URL

```python
# 8 個文件各自定義
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

---

### 23. 設計：硬編碼文件路徑

```python
_DB_PATH = "cache/traditional_cache.sqlite"   # src/data/traditional/fetcher.py
db_path: str = "data/stocksx.db"               # src/core/repository.py
db_path: str = "cache/users.sqlite"            # src/utils/health_check.py
log_file = "logs/app.log"                      # src/utils/logging_config.py
```

---

### 24. 設計：`from __future__ import annotations` 不一致

**有：** 88 個文件  
**無：** 31 個文件

---

### 25. 設計：同步 HTTP 請求阻塞 UI

**文件：** `src/data/service.py`、`src/utils/health_check.py`、`src/data/sources/api_hub.py`

項目已安裝 `aiohttp`，但多處仍使用同步 `requests`。

---

### 26. 設計：`src/compat.py` 過渡層長期存在

兼容層增加了新舊架構耦合，應在遷移完成後刪除。

---

### 27. 設計：Docker Compose 中 Celery Worker 缺少 healthcheck

```yaml
celery-worker:
  # 沒有 healthcheck
```

---

### 28. 設計：Mixed language（中英混雜）

- 1,258 行中文註釋
- 462 行英文註釋

**問題：** 錯誤信息部分中文部分英文，不一致：
```python
raise RuntimeError("請先設定環境變數...")     # 中文
raise RuntimeError("請安裝 yfinance: ...")    # 中文
raise ImportError("请安装 PyTorch: ...")      # 簡體中文
raise ValueError("需要指定对冲比率")            # 簡體中文
```

---

## 🟢 低優先級問題

### 29. 缺少 `py.typed` 標記文件

如果要支持 `mypy` 類型檢查，需要在包根目錄添加 `py.typed`。

---

### 30. 缺少獨立 `CHANGELOG.md`

版本歷史只在 `README.md` 和 `src/version.py` 中記錄。

---

### 31. 缺少 `FUNDING.yml`（GitHub Sponsors）

---

### 32. LICENSE 年份可能過期

需要確認是否為最新年份。

---

### 33. `pre-commit` hooks 版本過舊

已更新到 v0.11.2 / v5.0.0，但需要確認與 CI 使用的版本一致。

---

### 34. 缺少 `CODEOWNERS` 文件

---

### 35. 9 個空 `__init__.py` 文件

沒有導出任何內容，考慮添加有意義的導出或刪除。

---

### 36. `dataclass` 缺少 `__repr__`

42 個 dataclass 中只有 1 個定義了 `__repr__`/`__str__`。

---

### 37. 異步函數調用不匹配

- 26 個 `async def` 函數
- 41 個 `await` 調用

需要確認所有異步函數都被正確 await。

---

### 38. 缺少 GitHub Issue/PR 模板分類

已添加基本模板，但可以增加更多分類（如性能問題、策略建議等）。

---

### 39. 缺少 `.editorconfig` 驗證

已添加 `.editorconfig`，但需要確認所有編輯器都遵守。

---

### 40. 缺少 Docker 鏡像大小優化

當前 Dockerfile 使用 `python:3.11-slim`，可以考慮使用 `alpine` 或 `distroless` 進一步縮小。

---

## 📋 修復優先順序

| 順序 | 問題 | 預估工時 | 影響 |
|:---:|------|:---:|:---:|
| 1 | 🔴 #1 安全密碼 | 0.5h | 🔒 安全 |
| 2 | 🔴 #2 CORS 配置 | 0.5h | 🔒 安全 |
| 3 | 🔴 #8 API 錯誤處理 | 2h | 💥 穩定性 |
| 4 | 🔴 #5-6 引擎/策略統一 | 6h | 🏗️ 架構 |
| 5 | 🔴 #7 配置統一 | 2h | 🏗️ 架構 |
| 6 | 🔴 #4 FastAPI lifespan | 0.5h | 🔄 兼容性 |
| 7 | 🟡 #13 結構化日誌 | 2h | 📊 可觀測性 |
| 8 | 🟡 #14 時區處理 | 1h | 🕐 正確性 |
| 9 | 🟡 #15 長函數拆分 | 4h | 📖 可讀性 |
| 10 | 🟡 #17 測試補充 | 4h | 🧪 品質 |
| 11 | 🟢 其餘問題 | 3h | ✨ 體驗 |
| **合計** | | **~25h** | |

---

## 📊 代碼統計

| 指標 | 數值 |
|------|------|
| Python 文件數 | 158 |
| 總代碼行數 | ~16,000 |
| 測試函數數 | 288 |
| 有測試的模組 | ~30 |
| 無測試的模組 | 20 |
| 公開函數無 docstring | 219 |
| 超過 80 行的函數 | 42 |
| unsafe_allow_html 調用 | 74 |
| f-string 日誌調用 | 66 |
| 結構化日誌調用 | 23 |
| 重複策略文件 | 3 組 |
| 死代碼文件 | 2 個 |

---

> ⚠️ **免責聲明：** 此報告基於靜態代碼分析生成，部分問題可能已有意為之或在其他上下文中合理。建議修復前與團隊確認。
