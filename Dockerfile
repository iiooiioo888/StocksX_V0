# 多阶段构建 - 优化镜像大小

# ════════════════════════════════════════════════════════════
# 构建阶段
# ════════════════════════════════════════════════════════════
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ════════════════════════════════════════════════════════════
# 运行阶段
# ════════════════════════════════════════════════════════════
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY --chown=appuser:appuser . .

# 创建日志和数据目录
RUN mkdir -p /app/logs /app/data && chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

# 暴露端口
EXPOSE 8501 8001

# 默认启动命令
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
