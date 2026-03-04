@echo off
REM StocksX 自動交易啟動腳本
REM ==========================

echo ============================================================
echo StocksX 自動交易啟動腳本
echo ============================================================
echo.

REM 檢查 Python
echo [1/5] 檢查 Python 環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：未找到 Python
    pause
    exit /b 1
)
echo ✅ Python 環境正常
echo.

REM 檢查依賴
echo [2/5] 檢查依賴包...
python -c "import ccxt" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 安裝依賴包...
    pip install -r requirements.txt
) else (
    echo ✅ 依賴包已安裝
)
echo.

REM 啟動 Redis（如果使用 Docker）
echo [3/5] 檢查 Redis...
docker ps | findstr redis >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Redis 未運行，是否啟動？(Y/N)
    set /p start_redis=
    if /i "%start_redis%"=="Y" (
        docker run -d -p 6379:6379 --name stocksx_redis redis:7-alpine
        echo ✅ Redis 已啟動
    ) else (
        echo ℹ️ 跳過 Redis 啟動
    )
) else (
    echo ✅ Redis 正在運行
)
echo.

REM 啟動 Celery Worker
echo [4/5] 啟動 Celery Worker...
echo ℹ️ 這將在背景啟動 Celery Worker
start "StocksX Celery Worker" cmd /k "celery -A src.tasks worker --loglevel=info -Q celery"
timeout /t 3 >nul
echo ✅ Celery Worker 已啟動
echo.

REM 啟動 Streamlit
echo [5/5] 啟動 Streamlit 應用...
echo ℹ️ 瀏覽器將自動開啟
start "StocksX Streamlit" cmd /k "streamlit run app.py"
echo.

echo ============================================================
echo ✅ StocksX 啟動完成！
echo ============================================================
echo.
echo 訪問地址：http://localhost:8501
echo 自動交易頁面：http://localhost:8501/9_🤖_自動交易
echo.
echo 按任意鍵退出此視窗...
pause >nul
