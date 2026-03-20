#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# StocksX — 自動交易啟動腳本 (Unix/macOS/Linux)
# ════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 StocksX 自動交易系統啟動中..."

# 檢查 Python
if ! command -v python3 &>/dev/null; then
    echo "❌ 未找到 python3，請先安裝 Python 3.10+"
    exit 1
fi

# 檢查 .env
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，從 .env.example 複製..."
    cp .env.example .env
    echo "📝 請編輯 .env 填入必要的 API 金鑰後重新運行"
    exit 1
fi

# 檢查虛擬環境
if [ -d ".venv" ]; then
    echo "📦 啟用虛擬環境..."
    source .venv/bin/activate
fi

# 啟動服務
echo "📡 啟動 WebSocket 服務..."
python3 -m src.websocket_server &
WS_PID=$!

echo "🏠 啟動主應用..."
streamlit run app.py --server.port="${APP_PORT:-8501}" &
APP_PID=$!

echo ""
echo "✅ StocksX 已啟動"
echo "   主應用: http://localhost:${APP_PORT:-8501}"
echo "   WebSocket: ws://localhost:${WS_PORT:-8001}/ws"
echo ""
echo "按 Ctrl+C 停止所有服務"

trap "kill $WS_PID $APP_PID 2>/dev/null; echo '🛑 已停止所有服務'" EXIT
wait
