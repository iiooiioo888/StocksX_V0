# Phase 4: 部署优化方案

## 🎯 目标

- 一键部署
- 高可用性（99.9% uptime）
- 自动扩缩容
- 完善监控告警
- 持续集成/持续部署

## 📦 Docker 优化

### 1. 多阶段构建
```dockerfile
# Build stage
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["streamlit", "run", "app.py"]
```

### 2. Docker Compose (开发环境)
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@db:5432/stocksx
    depends_on:
      - redis
      - db
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: stocksx
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  websocket:
    build: .
    command: python -m src.websocket_binance
    depends_on:
      - redis

volumes:
  redis_data:
  postgres_data:
```

### 3. Kubernetes (生产环境)
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stocksx-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: stocksx
  template:
    spec:
      containers:
      - name: app
        image: stocksx:latest
        ports:
        - containerPort: 8501
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: stocksx-service
spec:
  selector:
    app: stocksx
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

## 🔄 CI/CD 流水线

### GitHub Actions
```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
      - name: Lint
        run: |
          pip install flake8 mypy
          flake8 src/
          mypy src/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t stocksx:${{ github.sha }} .
      - name: Push to registry
        run: |
          docker login -u ${{ secrets.DOCKER_USER }} -p ${{ secrets.DOCKER_PASS }}
          docker push stocksx:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # kubectl set image deployment/stocksx-app app=stocksx:${{ github.sha }}
          echo "Deploying to production..."
```

## 📊 监控体系

### 1. Prometheus + Grafana
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'stocksx'
    static_configs:
      - targets: ['app:8501', 'websocket:8001']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']
```

### 2. 关键指标
- **应用指标**:
  - 请求延迟（P50, P95, P99）
  - 错误率
  - QPS
  - WebSocket 连接数
  
- **系统指标**:
  - CPU 使用率
  - 内存使用率
  - 磁盘 I/O
  - 网络带宽
  
- **业务指标**:
  - 活跃用户数
  - 回测次数
  - 交易信号数
  - API 调用次数

### 3. 告警规则
```yaml
# alerting_rules.yml
groups:
  - name: stocksx_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "高错误率检测到"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        annotations:
          summary: "高延迟检测到"
      
      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 1m
        annotations:
          summary: "Redis 服务宕机"
```

## 📝 日志系统

### ELK Stack
```yaml
# docker-compose.elk.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data
  
  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  
  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
```

### 日志格式
```python
# 结构化日志
{
  "timestamp": "2024-03-19T09:00:00Z",
  "level": "INFO",
  "service": "stocksx-app",
  "message": "Backtest completed",
  "user_id": "12345",
  "duration_ms": 1234,
  "strategy": "sma_cross",
  "symbol": "BTC/USDT"
}
```

## 📋 实施清单

- [ ] 1. 优化 Dockerfile（多阶段构建）
- [ ] 2. 创建 docker-compose.yml（开发环境）
- [ ] 3. 创建 Kubernetes manifests
- [ ] 4. 配置 GitHub Actions CI/CD
- [ ] 5. 部署 Prometheus + Grafana
- [ ] 6. 配置 ELK 日志系统
- [ ] 7. 设置告警规则
- [ ] 8. 编写部署文档

## 🎯 预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 部署时间 | 30 分钟 | 5 分钟 |
| 恢复时间 | 手动 | 自动 (<1 分钟) |
| 可用性 | 95% | 99.9% |
| 监控覆盖 | 无 | 100% |
| 日志查询 | 手动 SSH | 实时搜索 |
