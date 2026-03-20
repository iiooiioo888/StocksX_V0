# ════════════════════════════════════════════════════════════
# StocksX — 多階段構建 Dockerfile v2
# 優化：更好的緩存層分離、安全加固、健康檢查
# ════════════════════════════════════════════════════════════

# ── 構建階段 ──
FROM python:3.12-slim AS builder

WORKDIR /app

# 安裝構建依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先複製 requirements.txt 以利用 Docker cache
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ── 運行階段 ──
FROM python:3.12-slim

LABEL maintainer="StocksX Team"
LABEL description="StocksX - 機構級回測與交易監控平台 v6.0"
LABEL org.opencontainers.image.source="https://github.com/iiooiioo888/StocksX_V0"
LABEL org.opencontainers.image.licenses="MIT"

# 安全：設置環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安裝運行時依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tini \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# 從構建階段複製依賴
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 複製應用程式碼
COPY . .

# 建立必要目錄
RUN mkdir -p /app/logs /app/data /app/cache \
    && chown -R appuser:appuser /app

# 切換到非 root 使用者
USER appuser

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/healthz || exit 1

# 暴露端口
EXPOSE 8501 8001

# 使用 tini 作為 init 系統（正確處理信號轉發）
ENTRYPOINT ["tini", "--"]
