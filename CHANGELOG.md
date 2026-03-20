# StocksX Changelog

All notable changes to this project will be documented in this file.

## [6.0.0] - 2026-03-20

### 🔒 Security
- **消除硬編碼管理員密碼** — 未設定 `ADMIN_PASSWORD` 時自動生成隨機密碼並記錄到日誌
- **CORS 安全修復** — WebSocket 服務不再使用 `allow_origins=["*"]`，改為環境變數白單
- **環境變數隔離** — 所有敏感配置統一從 `.env` 讀取

### ⚡ Performance
- **策略引擎全面 NumPy 向量化** — sma_cross、rsi_signal、bollinger_signal、ema_cross、macd_cross 等核心策略使用 numpy 計算，回測速度提升 10-100x
- **內建 SMA/EMA 計算器** — 使用 cumsum 實現 O(n) 簡單移動平均
- **通用交叉信號生成器** — `_signals_from_crossover` 抽象，減少重複代碼

### 📊 New Features — 投資組合優化
- **Markowitz 均值-方差優化** — 最大夏普比率最優配置
- **風險平價 (Risk Parity)** — 各資產風險貢獻相等化
- **有效前沿 (Efficient Frontier)** — 隨機權重蒙特卡羅近似
- **VaR / CVaR 計算** — 歷史法與參數法
- **最大回撤分析** — 回撤深度、持續時間、峰值/谷值

### 🔍 New Features — 市場狀態檢測
- **牛市/熊市/震盪自動識別** — 基於趨勢強度 + 波動率 + 均線系統
- **各 Regime 收益率/波動率統計** — 量化不同市場環境下的表現
- **EWMA 波動率建模** — 類 GARCH 的指數加權波動率
- **波動率 Regime & 趨勢** — 當前波動率百分位、上升/下降趨勢

### 📈 New Strategies
- **Z-Score 均值回歸** — 基於統計的超買超賣反轉策略
- **ROC 動量** — Rate of Change 變動率動量策略
- **Keltner Channel** — EMA + ATR 通道突破策略

### 🐳 Infrastructure
- **Dockerfile 修復** — Python 3.12 替換不存在的 3.14
- **Docker Compose CORS** — WebSocket 服務傳入 CORS_ORIGINS 環境變數

### 📖 Documentation
- **README 全面重構** — 更現代化、更有邏輯的技術架構文檔

## [5.3.0] - 2026-03-20

- pyproject.toml (PEP 621) 現代化打包
- Dependabot 自動依賴安全更新
- Docker 多階段構建優化、.dockerignore
- CI/CD 增強 — Docker 構建推送 GHCR
- Unix 啟動腳本 `start.sh`

## [5.2.0] - 2026-03-20

- 架構優化 — requirements-dev.txt
- README 現代化 — Mermaid 架構圖
- 代碼品質 — 改進錯誤處理、結構化日誌
- Docker 優化 — healthcheck、非 root 運行

## [5.1.0] - 2026-03-20

- 配置統一 — 消除 config.py 與 core/config.py 重複
- CI/CD 增強 — bandit 安全掃描、mypy 類型檢查
- 測試強化 — Python 3.10/3.11/3.12 矩陣測試

## [5.0.0] - 2026-03-19

- 核心架構重構 — src/core/ 模組化設計
- Orchestrator — 統一編排層
- Middleware Pipeline — 日誌、重試、限流中間件
- CacheManager — Redis / 記憶體快取
- Repository Pattern — 數據存取抽象
