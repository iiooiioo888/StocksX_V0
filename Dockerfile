# ════════════════════════════════════════════════════════════
# 多階段構建 - 優化鏡像大小
# ════════════════════════════════════════════════════════════

# ── 構建階段 ──
FROM python:3.11-slim AS builder

WORKDIR /app

# 安裝構建依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 先安裝 Python 依賴（利用 Docker cache）
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ── 運行階段 ──
FROM python:3.11-slim

LABEL maintainer="StocksX Team"
LABEL description="StocksX - 機構級回測與交易監控平台"

WORKDIR /app

# 安裝運行時依賴 + 建立非 root 使用者
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# 從構建階段複製依賴
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 複製應用程式碼
COPY --chown=appuser:appuser . .

# 建立日誌和資料目錄
RUN mkdir -p /app/logs /app/data /app/cache \
    && chown -R appuser:appuser /app

# 切換到非 root 使用者
USER appuser

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

# 暴露端口
EXPOSE 8501 8001

# 使用 tini 作為 init 系統（正確處理信號）
ENTRYPOINT ["tini", "--"]

# 默認啟動命令
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
