# 1Panel 部署指南

## 📋 前置要求

- 1Panel v1.0+ 已安装
- 服务器：Ubuntu 20.04+ / CentOS 8+
- 内存：≥ 4GB（建议 8GB+）
- 磁盘：≥ 20GB 可用空间

---

## 🚀 快速部署（推荐）

### 方法 1: 使用 1Panel 应用商店

1. **登录 1Panel 面板**
   - 访问 `https://你的服务器 IP:端口`
   - 登录管理员账号

2. **安装 Docker**
   - 进入「容器」→「Docker」
   - 确认 Docker 已安装并运行

3. **安装 Redis**
   - 进入「应用商店」→ 搜索 "Redis"
   - 点击安装，使用默认配置
   - 记录 Redis 连接信息（默认：`redis:6379`）

4. **安装 PostgreSQL**
   - 进入「应用商店」→ 搜索 "PostgreSQL"
   - 点击安装
   - 设置数据库密码（记录下来）
   - 记录连接信息（默认：`postgres:5432`）

5. **创建网站**
   - 进入「网站」→「创建网站」
   - 选择「运行环境」→「Docker compose」
   - 上传 `docker-compose.yml` 文件

---

### 方法 2: 手动 Docker Compose 部署

#### 1. 上传项目文件

```bash
# 在服务器上创建目录
mkdir -p /opt/stocksx
cd /opt/stocksx

# 上传项目文件（使用 git clone 或 scp）
git clone https://github.com/iiooiioo888/StocksX_V0.git .
```

#### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 基础配置
APP_ENV=production
APP_DEBUG=false
APP_PORT=8501

# 数据库配置
POSTGRES_DB=stocksx
POSTGRES_USER=stocksx_user
POSTGRES_PASSWORD=你的强密码_至少 16 位

# Redis 配置
REDIS_URL=redis://redis:6379/0

# API Keys
BINANCE_API_KEY=你的币安 API Key（可选）
BINANCE_SECRET_KEY=你的币安 Secret Key（可选）

# 数据库连接
DATABASE_URL=postgresql://stocksx_user:你的强密码_至少 16 位@postgres:5432/stocksx
```

#### 3. 启动服务

```bash
# 使用优化后的 docker-compose.yml
docker compose up -d
```

#### 4. 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看应用日志
docker compose logs -f app
```

---

## 🔧 1Panel 网站配置

### 创建反向代理

1. **进入「网站」→「创建网站」→「反向代理」**

2. **配置代理信息**
   ```
   域名：stocksx.你的域名.com
   代理地址：http://127.0.0.1:8501
   ```

3. **启用 HTTPS（推荐）**
   - 申请免费 SSL 证书（Let's Encrypt）
   - 强制 HTTPS 重定向

4. **配置防火墙**
   - 开放 80/443 端口
   - 关闭 8501 端口（只允许内网访问）

---

## 📊 数据库初始化

### 方法 1: 自动迁移（推荐）

在 `docker-compose.yml` 中添加初始化容器：

```yaml
services:
  migrate:
    build: .
    command: python -m src.database.migrate
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://stocksx_user:密码@postgres:5432/stocksx
```

### 方法 2: 手动执行

```bash
# 进入容器
docker compose exec app bash

# 运行数据库迁移
python -m src.database.migrate
```

---

## 🔒 安全配置

### 1. 修改默认端口

编辑 `docker-compose.yml`：

```yaml
ports:
  - "你的自定义端口：8501"  # 如 "38501:8501"
```

### 2. 配置防火墙

在 1Panel 中：
- 进入「安全」→「防火墙」
- 只开放必要端口（80/443/SSH）
- 关闭数据库端口（5432）和 Redis 端口（6379）

### 3. 定期备份

创建 1Panel 定时任务：

```bash
# 备份脚本 /opt/stocksx/backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U stocksx_user stocksx > /opt/backups/stocksx_$DATE.sql

# 保留最近 7 天备份
find /opt/backups -name "stocksx_*.sql" -mtime +7 -delete
```

在 1Panel 中设置每天凌晨 2 点执行。

---

## 📈 监控配置

### 1. 启用 Prometheus 监控

编辑 `docker-compose.yml`，取消注释 Prometheus 服务：

```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
```

### 2. 安装 Grafana（可选）

在 1Panel 应用商店安装 Grafana：
- 搜索 "Grafana"
- 点击安装
- 配置 Prometheus 数据源

### 3. 配置告警

编辑 `monitoring/alerting_rules.yml`：

```yaml
groups:
  - name: stocksx_alerts
    rules:
      - alert: ServiceDown
        expr: up{job="stocksx"} == 0
        for: 5m
        annotations:
          summary: "StocksX 服务宕机"
```

---

## 🛠️ 常见问题

### Q1: 容器启动失败

```bash
# 查看详细日志
docker compose logs app

# 检查端口占用
netstat -tlnp | grep 8501

# 重启服务
docker compose restart
```

### Q2: 数据库连接失败

```bash
# 检查 PostgreSQL 状态
docker compose ps postgres

# 测试连接
docker compose exec postgres psql -U stocksx_user -d stocksx
```

### Q3: Redis 连接失败

```bash
# 检查 Redis 状态
docker compose ps redis

# 测试连接
docker compose exec redis redis-cli ping
```

### Q4: 内存不足

编辑 `docker-compose.yml`，限制资源：

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

---

## 📝 维护命令

```bash
# 查看服务状态
docker compose ps

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 更新镜像
docker compose pull
docker compose up -d

# 查看日志
docker compose logs -f

# 进入容器
docker compose exec app bash

# 清理无用资源
docker system prune -a
```

---

## 🎯 部署检查清单

- [ ] 1Panel 已安装并运行
- [ ] Docker 已安装
- [ ] 项目文件已上传
- [ ] `.env` 文件已配置
- [ ] 数据库已初始化
- [ ] 网站反向代理已配置
- [ ] HTTPS 已启用
- [ ] 防火墙已配置
- [ ] 监控已启用（可选）
- [ ] 备份脚本已设置

---

## 📞 技术支持

- GitHub Issues: https://github.com/iiooiioo888/StocksX_V0/issues
- 1Panel 文档：https://1panel.cn/docs/

---

**部署完成后，访问 `https://stocksx.你的域名.com` 即可使用！**
