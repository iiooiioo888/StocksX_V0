# 🔍 StocksX V0 — 問題分析報告

> 生成時間：2026-03-20  
> 版本：v5.3.0  
> 分析範圍：全量代碼（158 個 Python 文件）

---

## 📊 問題總覽

| 嚴重程度 | 數量 | 說明 |
|:---:|:---:|------|
| 🔴 高 | 6 | 架構問題、安全隱患 |
| 🟡 中 | 10 | 代碼重複、設計不一致 |
| 🟢 低 | 8 | 可改進項、風格問題 |
| **合計** | **24** | |

---

## 🔴 高優先級問題

### 1. 安全：硬編碼預設管理員密碼

**文件：** `src/core/config.py:191`

```python
return _env("ADMIN_PASSWORD", "admin123") or "admin123"
```

**問題：** 如果用戶忘記設置 `ADMIN_PASSWORD` 環境變數，系統會使用 `admin123` 作為管理員密碼，這是一個嚴重的安全隱患。

**建議：** 改為首次啟動時自動生成隨機密碼並打印到日誌，或強制要求設置環境變數。

---

### 2. 架構：新舊回測引擎並存（未完成遷移）

**舊引擎：**
- `src/backtest/engine.py` (13,880 bytes)
- `src/backtest/engine_vec.py` (6,574 bytes)

**新引擎：**
- `src/core/backtest.py` (14,839 bytes)

**問題：** 專案同時存在兩套回測引擎。舊引擎仍在被 `src/ui_backtest.py`、`src/compat.py` 等文件直接使用，而新引擎通過 `Orchestrator` 調用。這導致：
- 維護成本翻倍
- 行為不一致風險
- 新貢獻者困惑

**建議：** 統一使用 `src/core/backtest.py`，將 `src/backtest/engine.py` 標記為 deprecated，逐步遷移 UI 層。

---

### 3. 架構：策略實現重複

**舊策略：**
- `src/backtest/strategies.py` (20,314 bytes) — 包含 `sma_cross`、`rsi_signal`、`macd_cross` 等

**新策略：**
- `src/core/registry.py` — 裝飾器註冊模式
- `src/core/strategies_bridge.py` — 將舊策略橋接到新 Registry

**問題：** 策略有兩套實現，橋接層增加了複雜度。舊策略文件直接被多個頁面引用。

**建議：** 將所有策略遷移至 `@register_strategy` 裝飾器模式，移除橋接層。

---

### 4. 架構：Walk-Forward 分析器重複

**文件：**
- `src/backtest/walk_forward.py` (4,972 bytes)
- `src/core/walk_forward.py` (8,028 bytes)

**問題：** 兩個文件實現了相同功能的 Walk-Forward 分析。新版本更完整但舊版本未被標記棄用。

**建議：** 刪除 `src/backtest/walk_forward.py`，統一使用 `src/core/walk_forward.py`。

---

### 5. 架構：WebSocket 服務重複

**文件：**
- `src/websocket_server.py` — FastAPI WebSocket 服務（在用）
- `src/websocket_binance.py` — 專業版幣安 WebSocket（**380 行，0 個引用**）

**問題：** `websocket_binance.py` 是死代碼，從未被任何地方導入。

**建議：** 刪除 `src/websocket_binance.py`，或將其有價值的功能合併到 `websocket_server.py`。

---

### 6. 架構：配置碎片化

**三個配置文件：**
- `src/config.py` — 策略標籤、顏色、市場分類、CSS
- `src/config_secrets.py` — API 金鑰管理
- `src/core/config.py` — Typed Settings dataclass

**問題：** 
- `src/config.py` 和 `src/core/config.py` 都定義了 `Settings` 和 `get_settings`
- `src/config_secrets.py` 的功能與 `src/core/config.py` 的 `DataApiSettings` 重疊
- 15+ 個文件從 `src/config` 導入，3 個從 `src.config_secrets` 導入

**建議：** 將 `STRATEGY_LABELS`、`STRATEGY_COLORS` 等配置常量移入 `src/core/config.py`，統一配置入口。

---

## 🟡 中優先級問題

### 7. 代碼：66 個文件使用 f-string 日誌而非結構化日誌

```python
# ❌ 錯誤方式
logger.warning(f"取得價格失敗 {symbol}: {e}")

# ✅ 正確方式
logger.warning("price_fetch_failed", extra={"symbol": symbol, "error": str(e)})
```

**影響：** 結構化日誌無法被日誌聚合工具（如 ELK、Datadog）正確解析。

**建議：** 統一使用 `extra={}` 參數的結構化日誌風格。

---

### 8. 代碼：`datetime.now()` 缺少時區

**涉及 10+ 個文件：**
- `src/data/service.py`
- `src/data/indices.py`
- `src/strategies/quant_strategies/multi_factor.py`
- `src/strategies/advanced_strategies.py`
- 等

**問題：** 使用 `datetime.now()` 而非 `datetime.now(timezone.utc)`，導致時間戳在不同時區的機器上不一致。

**建議：** 全局改用 `datetime.now(timezone.utc)` 或 `datetime.utcnow()`。

---

### 9. 設計：`start_auto_trading.bat` 只支援 Windows

**文件：** `start_auto_trading.bat`

**問題：** Windows 批處理腳本無法在 Linux/macOS 上運行。v5.3.0 已新增 `start.sh`，但舊的 `.bat` 文件未被刪除。

**建議：** 刪除 `start_auto_trading.bat`，或保留但更新文檔說明跨平台使用 `start.sh`。

---

### 10. 設計：`test_strategies.py` 放在根目錄

**文件：** `test_strategies.py`（根目錄）

**問題：** 測試腳本應該放在 `tests/` 目錄下，而不是根目錄。且它不是 pytest 格式，而是獨立運行腳本。

**建議：** 移動到 `tests/` 目錄，或轉換為 pytest 格式。

---

### 11. 設計：`train_lstm.py` 放在根目錄

**文件：** `train_lstm.py`（根目錄）

**問題：** 訓練腳本應該放在 `scripts/` 或 `examples/` 目錄，而非根目錄。且它沒有被任何地方引用。

**建議：** 移動到 `scripts/train_lstm.py`。

---

### 12. 設計：多處硬編碼 Redis URL

**涉及 8 個文件：**
```python
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

**問題：** Redis URL 默認值在多處重複定義，如果需要修改默認值需要改多個文件。

**建議：** 統一使用 `src/core/config.py` 的 `CacheSettings.redis_url`。

---

### 13. 設計：硬編碼文件路徑

```python
_DB_PATH = "cache/traditional_cache.sqlite"  # src/data/traditional/fetcher.py
db_path: str = "data/stocksx.db"              # src/core/repository.py
db_path: str = "cache/users.sqlite"           # src/utils/health_check.py
```

**問題：** 路徑硬編碼在多個文件中，不支援自定義數據目錄。

**建議：** 使用 `Settings.db_path` 和 `Settings.cache_dir` 統一管理。

---

### 14. 設計：`from __future__ import annotations` 不一致

**有：** 88 個文件  
**無：** 31 個文件（主要是 UI 頁面和策略文件）

**問題：** 不一致的類型註解風格，部分文件使用 `X | None` 語法但沒有 `from __future__`。

**建議：** 在所有 `.py` 文件中統一添加 `from __future__ import annotations`。

---

### 15. 設計：`src/compat.py` 過渡層長期存在

**文件：** `src/compat.py`

**問題：** 兼容層本應是臨時的過渡方案，但已存在多個版本。它增加了新舊架構之間的耦合。

**建議：** 在完成遷移後刪除此文件。

---

### 16. 性能：同步 HTTP 請求阻塞

**文件：** `src/data/service.py`、`src/utils/health_check.py`

```python
response = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
```

**問題：** 項目已安裝 `aiohttp`，但多處仍使用同步 `requests` 庫，在 Streamlit 回調中可能阻塞 UI。

**建議：** 統一使用 `aiohttp` 或 `httpx` 異步客戶端。

---

## 🟢 低優先級問題

### 17. `advanced_strategies.py` 重複

**文件：**
- `src/backtest/advanced_strategies.py` (24,527 bytes)
- `src/strategies/advanced_strategies.py` (10,471 bytes)

兩者名稱相同但內容不同，容易混淆。

---

### 18. `src/data/crypto/db.py` 有 11 個引用但功能不明確

需要確認是否與 `src/data/storage/sqlite_storage.py` 功能重疊。

---

### 19. 部分 `__init__.py` 為空文件

9 個 `__init__.py` 文件只有 1 行（空或僅有換行），沒有導出任何內容。

---

### 20. 缺少 `py.typed` 標記文件

如果要支持 `mypy` 類型檢查，需要在包根目錄添加 `py.typed` 文件。

---

### 21. 缺少 `CHANGELOG.md`

版本歷史只在 `README.md` 和 `src/version.py` 中記錄，缺少獨立的 `CHANGELOG.md` 文件。

---

### 22. `LICENSE` 文件年份

需要確認 LICENSE 文件中的年份是否為最新。

---

### 23. Docker Compose 中 Celery Worker 缺少 healthcheck

```yaml
celery-worker:
  # 沒有 healthcheck 定義
```

---

### 24. 缺少 GitHub Issue 和 PR 模板

缺少 `.github/ISSUE_TEMPLATE/` 和 `.github/PULL_REQUEST_TEMPLATE.md`。

---

## 📋 修復優先順序建議

| 順序 | 問題 | 預估工時 | 影響範圍 |
|:---:|------|:---:|:---:|
| 1 | 🔴 #1 安全密碼 | 0.5h | 全局 |
| 2 | 🔴 #6 配置統一 | 2h | 15+ 文件 |
| 3 | 🔴 #2 回測引擎統一 | 4h | 核心模組 |
| 4 | 🔴 #3 策略統一 | 3h | 核心模組 |
| 5 | 🟡 #7 結構化日誌 | 2h | 全局 |
| 6 | 🟡 #8 時區處理 | 1h | 10+ 文件 |
| 7 | 🟡 #9-11 文件整理 | 0.5h | 根目錄 |
| 8 | 🟡 #12-13 硬編碼 | 1h | 8 文件 |
| 9 | 🟢 其餘問題 | 2h | 分散 |
| **合計** | | **~16h** | |

---

> ⚠️ **免責聲明：** 此報告僅基於靜態代碼分析生成，部分問題可能已有意為之或在其他上下文中合理。建議在修復前與團隊確認。
