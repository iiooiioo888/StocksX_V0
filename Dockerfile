# ════════════════════════════════════════════════════════════
# StocksX V0 — Dockerfile
# 主應用: Streamlit Dashboard + FastAPI WebSocket
# ════════════════════════════════════════════════════════════

FROM python:3.11-slim AS builder

WORKDIR /build

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴（from pyproject.toml）
COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir --prefix=/install .

# ════════════════════════════════════════════════════════════
# Runtime 階段
# ════════════════════════════════════════════════════════════
FROM python:3.11-slim

WORKDIR /app

# 從 builder 複製已安裝的依賴
COPY --from=builder /install /usr/local

# 安裝 curl（healthcheck 需要）
RUN apt-get update && apt-get install -y --no-install-recommends curl tini \
    && rm -rf /var/lib/apt/lists/*

# 複製應用程式（src/ 已由 builder 安裝到 site-packages）
COPY app.py .
COPY pages/ ./pages/

# 創建必要目錄
RUN mkdir -p /app/data /app/logs

# 建立非 root 使用者
RUN groupadd -r stocksx && useradd -r -g stocksx stocksx \
    && chown -R stocksx:stocksx /app
USER stocksx

# 暴露端口
# 8501 = Streamlit 主應用
# 8001 = WebSocket
EXPOSE 8501 8001

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 預設啟動 Streamlit 主應用
ENTRYPOINT ["tini", "--"]
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
