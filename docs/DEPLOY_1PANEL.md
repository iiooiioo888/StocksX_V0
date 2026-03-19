# 🚀 1Panel 快速部署指南

> **5 分钟完成 StocksX V0 生产环境部署**

---

## 📋 前提条件

- ✅ 1Panel v1.0+ 已安装
- ✅ 服务器：Ubuntu 20.04+ / CentOS 8+
- ✅ 内存：≥ 4GB（建议 8GB+）
- ✅ 磁盘：≥ 20GB 可用空间

---

## 🔥 5 步快速部署

### 步骤 1: 上传项目文件

**方式 A: Git Clone（推荐）**

```bash
# SSH 登录服务器
ssh root@你的服务器 IP

# 创建项目目录
mkdir -p /opt/stocksx
cd /opt/stocksx

# Clone 项目
git clone https://github.com/iiooiioo888/StocksX_V0.git .
```

**方式 B: 1Panel 文件管理器上传**

1. 登录 1Panel 面板
2. 进入「文件」→ 创建目录 `/opt/stocksx`
3. 上传项目压缩包并解压

---

### 步骤 2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vi .env
# 或使用 1Panel 文件编辑器
```

**必须修改的配置：**

```bash
# ⚠️ 数据库密码（至少 16 位强密码）
POSTGRES_PASSWORD=YourStrongPassword_16Chars!

# ⚠️ Grafana 密码（如果使用监控）
GRAFANA_ADMIN_PASSWORD=YourGrafanaPassword!

# 可选：交易所 API（用于自动交易）
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
```

---

### 步骤 3: 启动服务

```bash
# 使用 1Panel 优化配置启动
docker compose -f docker-compose.1panel.yml up -d

# 查看启动日志
docker compose -f docker-compose.1panel.yml logs -f
```

**首次启动需要初始化数据库：**

```bash
# 运行数据库迁移
docker compose -f docker-compose.1panel.yml --profile init up migrate
```

---

### 步骤 4: 配置 1Panel 网站

1. **登录 1Panel 面板**
   - 访问 `https://你的服务器 IP:端口`

2. **创建网站**
   - 进入「网站」→「创建网站」
   - 选择「反向代理」

3. **配置代理**
   ```
   主域名：stocksx.你的域名.com
   代理地址：http://127.0.0.1:8501
   ```

4. **启用 HTTPS**
   - 点击「SSL」→「申请证书」
   - 选择 Let's Encrypt 免费证书
   - 开启「强制 HTTPS」

5. **配置防火墙**
   - 进入「安全」→「防火墙」
   - 开放 80/443 端口
   - 关闭 8501 端口（只允许内网）

---

### 步骤 5: 验证部署

**访问应用：**
```
https://stocksx.你的域名.com
```

**检查服务状态：**
```bash
docker compose -f docker-compose.1panel.yml ps
```

预期输出：
```
NAME                  STATUS         PORTS
stocksx-app           Up (healthy)   0.0.0.0:8501->8501/tcp
stocksx-postgres      Up (healthy)   5432/tcp
stocksx-redis         Up (healthy)   6379/tcp
```

---

## 📊 可选：启用监控

**启动 Prometheus + Grafana：**

```bash
docker compose -f docker-compose.1panel.yml --profile monitoring up -d
```

**访问监控面板：**
- Grafana: `http://你的服务器 IP:3000`
- 默认账号：`admin` / 密码：你在 `.env` 中设置的值

**配置 1Panel 反向代理（推荐）：**
- Grafana: `grafana.你的域名.com` → `http://127.0.0.1:3000`
- Prometheus: `prometheus.你的域名.com` → `http://127.0.0.1:9090`

---

## 🔧 常用命令

### 服务管理

```bash
# 查看状态
docker compose -f docker-compose.1panel.yml ps

# 重启服务
docker compose -f docker-compose.1panel.yml restart

# 停止服务
docker compose -f docker-compose.1panel.yml down

# 查看日志
docker compose -f docker-compose.1panel.yml logs -f app

# 进入容器
docker compose -f docker-compose.1panel.yml exec app bash
```

### 更新升级

```bash
# 拉取最新代码
git pull

# 重新构建并重启
docker compose -f docker-compose.1panel.yml up -d --build
```

### 备份恢复

**备份：**
```bash
# 执行备份脚本
./backup.sh
```

**恢复数据库：**
```bash
# 解压备份文件
gunzip backups/db/stocksx_20240319_120000.sql.gz

# 恢复到数据库
docker compose exec -T postgres psql -U stocksx_user -d stocksx < backups/db/stocksx_20240319_120000.sql
```

---

## 🔒 安全加固

### 1. 修改默认端口

编辑 `docker-compose.1panel.yml`：
```yaml
ports:
  - "38501:8501"  # 自定义端口
```

### 2. 配置 1Panel 防火墙

```bash
# 只开放必要端口
允许：80, 443, 22 (SSH)
拒绝：8501, 5432, 6379, 9090, 3000
```

### 3. 启用数据库密码认证

确保 `.env` 中设置了强密码：
```bash
POSTGRES_PASSWORD=至少 16 位_大小写 + 数字 + 特殊字符!
```

### 4. 定期更新

```bash
# 每周更新系统包
apt update && apt upgrade -y

# 每月更新 Docker 镜像
docker compose pull
docker compose up -d
```

---

## 🛠️ 故障排查

### 问题 1: 容器启动失败

```bash
# 查看详细日志
docker compose -f docker-compose.1panel.yml logs app

# 检查资源使用
docker stats

# 重启服务
docker compose -f docker-compose.1panel.yml restart
```

### 问题 2: 数据库连接失败

```bash
# 检查 PostgreSQL 状态
docker compose -f docker-compose.1panel.yml ps postgres

# 测试连接
docker compose -f docker-compose.1panel.yml exec postgres psql -U stocksx_user -d stocksx

# 查看数据库日志
docker compose -f docker-compose.1panel.yml logs postgres
```

### 问题 3: 网站无法访问

```bash
# 检查端口监听
netstat -tlnp | grep 8501

# 检查防火墙
ufw status

# 检查 1Panel 网站配置
# 确保反向代理配置正确
```

### 问题 4: 内存不足

编辑 `docker-compose.1panel.yml`，限制资源：
```yaml
deploy:
  resources:
    limits:
      memory: 2G
```

---

## 📝 部署检查清单

- [ ] 1Panel 已安装并运行
- [ ] 项目文件已上传到 `/opt/stocksx`
- [ ] `.env` 文件已配置（强密码！）
- [ ] 数据库迁移已运行
- [ ] 网站反向代理已配置
- [ ] HTTPS 证书已申请
- [ ] 防火墙已配置（只开放 80/443）
- [ ] 备份脚本已测试
- [ ] 监控已启用（可选）

---

## 📞 获取帮助

- **GitHub Issues:** https://github.com/iiooiioo888/StocksX_V0/issues
- **1Panel 文档:** https://1panel.cn/docs/
- **Docker 文档:** https://docs.docker.com/

---

**🎉 部署完成！访问 `https://stocksx.你的域名.com` 开始使用！**
