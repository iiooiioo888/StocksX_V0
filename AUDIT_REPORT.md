# StocksX_V0 審計報告 & 優化方案

## 📋 執行摘要

StocksX 是一個架構相當成熟的量化回測平台，已具備六層分離、DI 容器、策略註冊等現代架構。但仍存在 **安全性隱患、效能瓶頸、錯誤處理薄弱、現代金融功能缺失** 等問題。

---

## 🔴 嚴重問題 (Critical)

### 1. WebSocket Server SECRET_KEY 每次重啟重新生成
- **文件**: `src/websocket_server.py:31`
- **問題**: `SECRET_KEY = secrets.token_hex(32)` 在模組層級執行，每次服務重啟所有 JWT token 失效
- **影響**: 用戶被迫重新登入，生產環境不可用
- **修復**: 從環境變數讀取，與主應用共用同一把 key

### 2. 默認管理員密碼硬編碼
- **文件**: `src/core/config.py:175`
- **問題**: `admin_password` 回退到 `"admin123"`
- **影響**: 若用戶忘記設定 `ADMIN_PASSWORD` 環境變數，管理員入口等於無密碼
- **修復**: 未設定時拒絕啟動或強制生成隨機密碼

### 3. 過度寬泛的錯誤處理 (43 處 `except Exception:`)
- **問題**: 全專案 43 處 bare `except Exception:` 吞掉所有異常
- **影響**: 真實錯誤被隱藏，debug 極其困難，可能導致數據靜默損壞
- **修復**: 改為具體異常類型，至少記錄 traceback

---

## 🟠 重要問題 (Major)

### 4. 策略計算效能低下 — 純 Python O(n×m) 循環
- **文件**: `src/backtest/strategies.py`
- **問題**: SMA、RSI、布林帶等指標在純 Python 中逐根計算
- **影響**: 大量歷史數據回測時速度極慢（比 numpy 向量化慢 100x+）
- **修復**: 用 numpy/pandas 向量化重寫核心計算

### 5. 全域單例模式線程不安全
- **文件**: 12 處 `global` 變量（orchestrator, container, cache_manager 等）
- **問題**: 多線程/async 環境下可能 race condition
- **影響**: Celery worker 中使用可能導致數據損壞
- **修復**: 使用 threading.Lock 或改為依賴注入

### 6. 配置檔案雙重存在
- **文件**: `src/config.py` + `src/core/config.py` + `src/config_secrets.py`
- **問題**: 儘管 README 說已「統一」，實際三個模組同時存在且各有職責
- **影響**: import 混亂，新開發者不知該用哪個
- **修復**: 徹底合併為單一 `src/core/config.py`

### 7. Monte Carlo 使用 `random.choice` 而非 numpy
- **文件**: `src/utils/risk.py:179`
- **問題**: 10000 次模擬 × 30 天 = 30 萬次 Python 循環 + random.choice
- **影響**: 可用 numpy 一次性生成全部隨機數，速度提升 50x+
- **修復**: `np.random.choice(returns, size=(n_sim, horizon))`

### 8. 缺乏輸入驗證
- **問題**: 大部分 API 端點和函數沒有驗證輸入參數
- **影響**: 無效 symbol、timeframe 可能導致不可預期行為
- **修復**: 添加 Pydantic 模型或手動驗證

---

## 🟡 次要問題 (Minor)

### 9. 策略橋接中的脆弱路徑操作
- **文件**: `src/core/strategies_bridge.py:25-27`
- **問題**: 使用 `os.path.join(os.path.dirname(__file__), "..", "backtest", "strategies.py")` 
- **修復**: 改用 `importlib.resources` 或相對導入

### 10. 沒有數據驗證管道
- **問題**: OHLCV 數據從 API 回來後直接使用，沒有 NaN、重複、缺失值檢查
- **修復**: 在 Pipeline 中加入完整性驗證步驟

### 11. 缺乏現代金融功能
見下方「功能缺失」章節。

---

## 🚀 現代金融功能缺失清單

| 功能 | 重要性 | 說明 |
|------|--------|------|
| **投資組合優化 (Mean-Variance / Efficient Frontier)** | ⭐⭐⭐ | Markowitz 模型、風險平價、Black-Litterman |
| **因子模型 (Fama-French / Barra)** | ⭐⭐⭐ | 多因子歸因、Alpha/Beta 分解 |
| **市場狀態檢測 (Regime Detection)** | ⭐⭐⭐ | HMM/聚類識別牛市/熊市/震盪 |
| **統計套利 & 配對交易** | ⭐⭐ | 協整檢驗、Kalman Filter 對沖 |
| **波動率建模 (GARCH)** | ⭐⭐ | 歷史/隱含波動率、Vol Surface |
| **期權希臘值 (Greeks)** | ⭐⭐ | Delta/Gamma/Vega/Theta 計算 |
| **ETF 追蹤誤差分析** | ⭐⭐ | 追蹤誤差、折溢價、再平衡影響 |
| **另類數據整合** | ⭐⭐ | 鏈上數據、社交情緒、預測市場 |
| **機器學習特徵工程** | ⭐ | 自動特徵生成、特徵重要性 |
| **回測穩健性檢驗** | ⭐ | Bootstrap、交叉驗證、Overfitting 檢測 |

---

## 📊 優先修復順序

1. **安全問題** (#1, #2, #3) — 立即修復
2. **效能優化** (#4, #7) — 大幅提升用戶體驗
3. **架構清理** (#5, #6, #9) — 降低維護成本
4. **現代金融功能** — 增加產品競爭力
