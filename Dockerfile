# StocksX 監控系統 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝依賴
COPY backend/requirements.txt .
COPY trading/requirements.txt /tmp/trading_req.txt

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r /tmp/trading_req.txt \
    && pip install prometheus-client

# 複製代碼
COPY backend/ ./backend/
COPY src/ ./src/
COPY trading/ ./trading/
COPY monitoring/ ./monitoring/

# 創建數據目錄
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000 8001

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# 啟動命令（默認啟動 API）
CMD ["python3", "backend/main.py"]
