"""StocksX 版本資訊"""

__version__ = "8.0.1"
__version_info__ = tuple(int(x) for x in __version__.split("."))

# 版本歷史摘要
CHANGELOG = {
    "8.0.1": "策略計算全面向量化（Bollinger/Z-Score/ROC 提速 50x）· OHLCV 數據驗證管道 · SECRET_KEY 啟動驗證 · README 全面重構",
    "7.0.0": "策略庫擴展至 130+（10 大類）· 冰山/TWAP 訂單 · Black-Litterman/HRP · 統計套利/資金費率套利",
    "6.0.0": "安全加固 · NumPy 向量化策略引擎 · 投資組合優化（Mean-Variance/Risk Parity/Efficient Frontier）· 市場狀態檢測 · 波動率建模 · VaR/CVaR · 新增 3 個現代策略 · CORS 安全修復 · README 全面重構",
    "5.3.0": "pyproject.toml 現代化打包 · Dependabot 自動更新 · Docker 多階段構建優化 · CI/CD 增強 · Unix 啟動腳本",
    "5.2.2": "投資組合分析（風險平價/最小方差/有效前沿）· HTML/JSON 報告匯出",
    "5.2.1": "修復 DataService 現貨/永續路由 · 風險分析 · 配置驗證 · Walk-Forward",
    "5.2.0": "架構優化 · README 現代化 · 結構化日誌 · WebSocket 心跳",
    "5.1.0": "配置統一 · CI/CD 增強 · 測試強化",
    "5.0.0": "核心架構重構 · Orchestrator · Middleware · Cache",
    "4.2.0": "記憶體快取 · pytest · UI 共用元件",
    "4.1.0": "安全強化 · 結構化日誌 · GitHub Actions",
    "4.0.0": "CCXT / Yahoo Finance · WebSocket 即時推送",
    "3.0.0": "FastAPI 後端分離 · Celery 任務隊列",
}
