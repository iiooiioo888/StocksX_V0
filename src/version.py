"""StocksX 版本資訊"""

__version__ = "5.2.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))

# 版本歷史摘要
CHANGELOG = {
    "5.2.0": "架構優化 · README 現代化 · 結構化日誌 · WebSocket 心跳",
    "5.1.0": "配置統一 · CI/CD 增強 · 測試強化",
    "5.0.0": "核心架構重構 · Orchestrator · Middleware · Cache",
    "4.2.0": "記憶體快取 · pytest · UI 共用元件",
    "4.1.0": "安全強化 · 結構化日誌 · GitHub Actions",
    "4.0.0": "CCXT / Yahoo Finance · WebSocket 即時推送",
    "3.0.0": "FastAPI 後端分離 · Celery 任務隊列",
}
