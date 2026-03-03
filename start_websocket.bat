@echo off
REM StocksX WebSocket 服務啟動腳本

echo ========================================
echo StocksX WebSocket 服務
echo ========================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Python，請先安裝 Python 3.8+
    pause
    exit /b 1
)

echo [資訊] 啟動 WebSocket 服務...
echo [資訊] 服務地址：ws://localhost:8001
echo [資訊] 文件：http://localhost:8001/docs
echo.
echo 按 Ctrl+C 停止服務
echo.

REM 啟動 WebSocket 服務
python -m src.websocket_server

pause
