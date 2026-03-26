# 📋 StocksX_V0 問題追蹤

**最後更新**: 2026-03-26  
**策略總數**: 130  
**已實作**: 130 (100%) ✅  
**有真實回測結果**: 3 (order_flow, stat_arb, bollinger_squeeze)  
**待真實驗證**: 84  

---

## 🐞 活躍問題

### ISSUE-001: `app.py` 頁面路徑錯誤 🔴 嚴重
- **檔案**: `app.py` L42, `src/ui_common.py` L62
- **問題**: 引用 `pages/5_📡_監控.py`，實際檔案為 `pages/5_📡_交易監控.py`
- **影響**: 交易監控頁面導航失敗
- **狀態**: ✅ 已修復 (2026-03-26)

### ISSUE-002: `src/ui_common.py` 側邊欄導航同路徑錯誤 🔴 嚴重
- **檔案**: `src/ui_common.py` L62
- **問題**: 同 ISSUE-001，側邊欄 `page_link` 路徑錯誤
- **影響**: 側邊欄點擊交易監控無反應
- **狀態**: ✅ 已修復 (2026-03-26)

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
- **影響**: 這些策略目前僅返回信號骨架，無法產生預測信號
- **狀態**: ⏳ 待處理

### ISSUE-004: 回測結果多為模擬數據 🟡 中等
- **檔案**: `ISSUES.md` (舊版), 各 `*_optimization_results.json`
- **問題**: 84 個策略的優化結果標記為 `*模擬數據`，需使用真實歷史數據回測驗證
- **影響**: Sharpe、Return、MaxDD 等指標不可靠
- **驗收標準**: 3年真實數據回測, Sharpe > 0.5, MaxDD < 20%
- **狀態**: ⏳ 待處理

### ISSUE-005: AGENTS.md 記載無自動測試套件 🟢 低
- **檔案**: `AGENTS.md`
- **問題**: 專案缺乏自動化測試套件（`test_phase3.py`, `test_phase4_comprehensive.py` 為手動驗證腳本）
- **影響**: CI 無法自動回歸測試
- **狀態**: ⏳ 待處理

### ISSUE-006: `src/ui_modern.py` 缺失但被引用 🟡 中等
- **檔案**: `app.py` L14 引用 `src.ui_modern`
- **問題**: `app.py` 引用 `src.ui_modern` 模組，但 `src/` 下無 `ui_modern.py`
- **影響**: 啟動時可能因 `ModuleNotFoundError` 崩潰
- **備註**: 運行時 import 成功，可能由 Streamlit 頁面執行時動態創建，需確認
- **狀態**: ⏳ 待確認

### ISSUE-007: `src/trading` 缺少 `ccxt` 依賴 🟢 低
- **檔案**: `requirements.txt`
- **問題**: `import src.trading` 在未安裝 ccxt 環境下失敗
- **影響**: 開發環境測試不便
- **狀態**: ⏳ 待處理

---

## ✅ 已解決問題

| Issue | 描述 | 解決日期 | 解決方案 |
|:------|------|:--------:|----------|
| ISSUE-001 | app.py 頁面路徑錯誤 `5_📡_監控.py` | 2026-03-26 | 改為 `5_📡_交易監控.py` |
| ISSUE-002 | ui_common.py 側邊欄同路徑錯誤 | 2026-03-26 | 同步修正路徑 |
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
