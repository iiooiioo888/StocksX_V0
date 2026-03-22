#!/bin/bash
# StocksX 快速啟動腳本

echo "=========================================="
echo "🚀 StocksX 快速啟動"
echo "=========================================="

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3"
    exit 1
fi

echo "✅ Python: $(python3 --version)"

# 安裝後端依賴
echo ""
echo "📦 安裝後端依賴..."
cd backend
pip3 install -r requirements.txt -q

# 初始化數據庫
echo ""
echo "💾 初始化數據庫..."
python3 database.py

# 啟動後端
echo ""
echo "🚀 啟動後端服務..."
echo "   API 文檔：http://localhost:8000/docs"
echo "   前端界面：http://localhost:8000"
echo "   WebSocket: ws://localhost:8000/ws/signals"
echo ""
echo "=========================================="
echo "按 Ctrl+C 停止服務"
echo "=========================================="

python3 main.py
