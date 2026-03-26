# 📋 StocksX_V0 問題追蹤

**最後更新**: 2026-03-26 (第二次審查)
**策略總數**: 130
**已實作**: 130 (100%) ✅
**有真實回測結果**: 3 (order_flow, stat_arb, bollinger_squeeze)
**待真實驗證**: 84

---

## 🐞 活躍問題

### ISSUE-003: AI/ML 策略模組未實現模型加載 🟡 中等
- **檔案**: `src/strategies/ai_ml/ai_final.py`, `ai_complete.py`
- **問題**: 7 個策略類別的模型變數為 `None`，含 TODO 標記但未實作：
  - `TransferLearningStrategy.source_model` — 轉移學習源模型
  - `ContrastiveLearningStrategy.encoder` — 對比學習編碼器
  - `EnsembleStrategy.models` — 集成學習模型列表
  - `MultiFactorStrategy.factor_weights` — 多因子權重
  - `PairsTradingMLStrategy.hedge_ratio` — 配對對沖比率
  - `DQNStrategy.q_network` — Q 網絡
  - `LSTMStrategy.lstm_model` — LSTM 模型
  - `TransformerStrategy.model` — Transformer 模型 (ai_complete.py)
- **影響**: 這些策略目前僅返回信號骨架，無法產生預測信號
- **狀態**: ⏳ 待處理

### ISSUE-004: 回測結果多為模擬數據 🟡 中等
- **檔案**: 各 `*_optimization_results.json`
- **問題**: 84 個策略的優化結果標記為 `*模擬數據`，需使用真實歷史數據回測驗證
- **影響**: Sharpe、Return、MaxDD 等指標不可靠
- **驗收標準**: 3年真實數據回測, Sharpe > 0.5, MaxDD < 20%
- **狀態**: ⏳ 待處理

### ISSUE-005: 缺乏自動測試套件 🟢 低
- **檔案**: `AGENTS.md`, `tests/`
- **問題**: 專案缺乏自動化測試套件（`test_phase3.py`, `test_phase4_comprehensive.py` 為手動驗證腳本），CI 的 `pytest tests/` 僅跑 `tests/` 目錄
- **影響**: CI 無法自動回歸測試，人工驗證腳本無法納入 CI 流程
- **狀態**: ⏳ 待處理

### ISSUE-008: Streamlit 頁面前綴重複 `11_` 🔴 嚴重
- **檔案**: `pages/11_📊_數據源管理.py`, `pages/11_🤖_自動交易.py`
- **問題**: 兩個頁面使用相同的數字前綴 `11_`，Streamlit 多頁應用依賴前綴排序，重複前綴會導致其中一個頁面不顯示或排序混亂
- **影響**: 自動交易頁或數據源管理頁可能無法在側邊欄正常導航
- **建議修復**: 將自動交易頁改為 `14_🤖_自動交易.py` 或調整其他頁面前綴避免衝突
- **狀態**: ⏳ 待處理

### ISSUE-009: .log 檔案被 Git 追蹤但不應提交 🟢 低
- **檔案**: `backtest_monitor.log`, `backtest_progress.log`, `monitor.log`, `resource_monitor.log`, `ultra_backtest.log`
- **問題**: `.gitignore` 已配置 `*.log`，但上述 5 個 log 檔案已被 Git 追蹤（commit 之前未 ignore）
- **影響**: repo 中包含空的/過期的日誌檔案，增加 repo 體積
- **建議修復**: `git rm --cached *.log` 並重新提交
- **狀態**: ✅ 已修復 (2026-03-26)

### ISSUE-010: Dockerfile 與項目結構不匹配 🔴 嚴重
- **檔案**: `Dockerfile`, `docker-compose.yml`
- **問題**:
  1. Dockerfile 使用 `COPY backend/requirements.txt` 而非根目錄 `requirements.txt`
  2. Dockerfile **不複製** `app.py`、`pages/`、`pyproject.toml`（Streamlit 主應用）
  3. CMD 執行 `python3 backend/main.py`（FastAPI 後端），而非 Streamlit 主應用
  4. `docker-compose.yml` 沒有 Streamlit 服務，只有 `stocksx-api` + `trading-engine`
  5. README 說「主應用 → :8501」，但 docker-compose.yml 只暴露 :8000
- **影響**: `docker compose up -d` 無法啟動 Streamlit 主應用，README 快速開始指引失效
- **建議修復**: 重寫 Dockerfile，以 Streamlit 主應用為核心；同步修正 docker-compose.yml
- **狀態**: ✅ 已修復 (2026-03-26) — Dockerfile 已改為 Streamlit 主應用，docker-compose.yml 新增 app service（端口 8501）

### ISSUE-011: Streamlit 頁面前綴重複 `11_` 🟡 中等 (已修復)
- **檔案**: `pages/11_📊_數據源管理.py`, `pages/11_🤖_自動交易.py`
- **問題**: 兩個頁面使用相同的數字前綴 `11_`，Streamlit 多頁應用依賴前綴排序
- **影響**: 其中一個頁面可能無法在側邊欄正常導航
- **狀態**: ✅ 已修復 (2026-03-26) — 自動交易頁改為 `14_🤖_自動交易.py`

### ISSUE-012: 大量 `sys.path` 相對路徑 hack 🟡 中等
- **檔案**: 31 個檔案（`src/strategies/ai_ml/`, `src/strategies/execution/`, `src/strategies/trend/`, `src/strategies/breakout/`, `src/strategies/pattern/`, `src/strategies/macro/`, `src/strategies/statistical/`, `src/strategies/risk_management/`, `src/strategies/oscillator/`, `src/strategies/microstructure/`, `src/analytics/`）
- **問題**: 使用 `sys.path.insert(0, str(Path(__file__).parent.parent))` 來解決匯入問題，而非依賴 pyproject.toml 的正確安裝
- **影響**: 套件安裝後（`pip install -e .`）這些 hack 不應存在，且在不同部署環境（Docker、CI）可能導致路徑不一致
- **建議修復**: 確保 pyproject.toml 的 `[tool.setuptools.packages.find]` 正確配置，移除所有 `sys.path` hack
- **狀態**: ⏳ 待處理

### ISSUE-013: `backend/main.py` FastAPI 服務未被使用 🟢 低
- **檔案**: `backend/main.py`, `Dockerfile`
- **問題**: `backend/` 目錄含完整 FastAPI 後端（main.py、models.py、schemas.py），但 Dockerfile 啟動的是 Streamlit（`app.py`），docker-compose.yml 也無 backend 服務
- **影響**: backend 代碼實際上未被部署，與 `src/websocket_server.py` 功能重疊（兩者都是 FastAPI+WebSocket）
- **建議修復**: 明確選用 `backend/main.py` 或 `src/websocket_server.py` 作為 API 層，合併或移除冗餘代碼
- **狀態**: ⏳ 待處理

### ISSUE-014: `src/core/alerts.py` AlertChannel 為空殼實現 🟢 低
- **檔案**: `src/core/alerts.py`（line 79-82）
- **問題**: `AlertChannel` 類別及其 `send` 方法為空 stub（僅 `pass`），無任何警報邏輯
- **影響**: 依賴此模組的告警功能實際上不會發送任何通知
- **建議修復**: 實現基本告警通道（Email、Webhook）或暫時移除未完成的代碼
- **狀態**: ⏳ 待處理

---

## ✅ 已解決問題

| Issue | 描述 | 解決日期 | 解決方案 |
|:------|------|:--------:|----------|
| ISSUE-001 | app.py 頁面路徑錯誤 `5_📡_監控.py` | 2026-03-26 | 改為 `5_📡_交易監控.py` |
| ISSUE-008 | Streamlit 頁面前綴重複 `11_` | 2026-03-26 | 自動交易頁改為 `14_🤖_自動交易.py`，僅保留一個 `11_` 頁面 |
| ISSUE-010 | Dockerfile 與項目結構不匹配 | 2026-03-26 | Dockerfile 改為 Streamlit 主應用，docker-compose.yml 新增 app service（8501）|
| ISSUE-002 | ui_common.py 側邊欄同路徑錯誤 | 2026-03-26 | 同步修正路徑 |
| ISSUE-006 | `src/ui_modern.py` 缺失被引用 | 2026-03-26 | 確認檔案存在，從未缺失 |
| ISSUE-007 | `src/trading` 缺少 `ccxt` 依賴 | 2026-03-26 | 確認 `ccxt>=4.2.0` 已在 requirements.txt |
| ISSUE-009 | .log 檔案被 Git 追蹤 | 2026-03-26 | `git rm --cached` 清理 |
| ISSUE-011 | Streamlit 頁面前綴重複 `11_` | 2026-03-26 | 自動交易頁改為 `14_🤖_自動交易.py` |
| #34 | 訂單流分析優化 | 2026-03-23 | Sharpe 1.832→2.033 |
| #41 | 統計套利優化 | 2026-03-23 | Sharpe -0.264→1.029 |
| #15 | 布林帶擠壓優化 | 2026-03-23 | Sharpe 1.299 |

---

## 📊 優化進度總覽

| 階段 | 優先級 | 總數 | 已優化 | 待真實驗證 | 狀態 |
|------|--------|------|--------|-----------|------|
| Phase 1 | 🔴 HIGH | 20 | 3 | 17 | ⏳ 15% |
| Phase 2 | 🟡 MED | 38 | 0 | 38 | ⏳ 0% |
| Phase 3 | 🟢 LOW | 28 | 0 | 28 | ⏳ 0% |
| EPIC | 🎯 | 1 | — | — | ⏳ 進行中 |
| **合計** | | **87** | **3** | **83** | **3.4%** |

> **說明**: 87 個策略已有「模擬數據」的初始參數優化結果，但均需使用真實 3 年歷史數據重新驗證。僅 order_flow、stat_arb、bollinger_squeeze 三個策略有較可靠的回測結果。

---

## 📁 相關文件

| 文件 | 說明 |
|------|------|
| `STRATEGY_LIBRARY.md` | 130 策略完整文檔 |
| `STRATEGY_OPTIMIZATION_PLAN.md` | 優化計劃與任務拆分明細 |
| `PHASE4_COMPLETE_REPORT.md` | Phase 4 完成報告 (95%) |
| `3YEAR_BACKTEST_REPORT.md` | 3 年回測報告 |
| `TEST_REPORT_PHASE4.md` | Phase 4 測試報告 |
| `ARCHITECTURE.md` | 架構設計文檔 |

---

*本文檔隨問題修復持續更新。*
