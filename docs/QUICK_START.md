# 🚀 StocksX V0 - 快速开始

> **5 分钟完成部署，立即开始量化交易！**

---

## 📦 方式 1: 1Panel 部署（推荐生产环境）

### 5 步完成

```bash
# 1. SSH 登录服务器
ssh root@你的服务器 IP

# 2. 创建项目目录
mkdir -p /opt/stocksx && cd /opt/stocksx

# 3. Clone 项目
git clone https://github.com/iiooiioo888/StocksX_V0.git .

# 4. 配置环境变量
cp .env.example .env
vi .env  # 修改密码

# 5. 启动服务
docker compose -f docker-compose.1panel.yml up -d
```

**详细文档：** [DEPLOY_1PANEL.md](DEPLOY_1PANEL.md)

---

## 🖥️ 方式 2: 本地开发环境

### 快速启动

```bash
# 1. Clone 项目
git clone https://github.com/iiooiioo888/StocksX_V0.git
cd StocksX_V0

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
streamlit run app.py
```

**访问：** http://localhost:8501

---

## 🧠 训练 LSTM 模型

```bash
# 使用默认参数训练
python train_lstm.py --symbol BTC/USDT --days 365 --epochs 50

# 自定义参数
python train_lstm.py \
  --symbol ETH/USDT \
  --days 730 \
  --epochs 100 \
  --batch-size 64 \
  --output models/lstm_eth.h5
```

---

## 📊 策略列表

### 机器学习策略
- **LSTM 价格预测** - 深度学习预测未来价格方向
- **特征工程** - 50+ 技术指标自动生成

### NLP 策略
- **情绪分析** - FinBERT 分析新闻/社交媒体情绪

### 量化策略
- **配对交易** - 协整检验 + 统计套利
- **多因子模型** - Fama-French 三因子 + 动量/质量/低波

### 强化学习
- **DQN Agent** - 深度 Q 网络学习交易策略
- **交易环境** - Gymnasium 框架支持

---

## 📁 项目结构

```
StocksX_V0/
├── src/
│   └── strategies/
│       ├── ml_strategies/      # 机器学习策略
│       │   ├── lstm_predictor.py
│       │   └── feature_engineering.py
│       ├── nlp_strategies/     # NLP 策略
│       │   └── sentiment_analyzer.py
│       ├── quant_strategies/   # 量化策略
│       │   ├── pairs_trading.py
│       │   └── multi_factor.py
│       ├── rl_strategies/      # 强化学习
│       │   ├── trading_env.py
│       │   └── dqn_agent.py
│       └── advanced_strategies.py  # 策略集成
├── train_lstm.py               # LSTM 训练脚本
├── app.py                      # Streamlit 应用
├── docker-compose.1panel.yml   # 1Panel 部署配置
├── DEPLOY_1PANEL.md            # 部署指南
└── requirements.txt            # 依赖
```

---

## 🔧 常用命令

### 服务管理
```bash
# 启动
docker compose -f docker-compose.1panel.yml up -d

# 停止
docker compose -f docker-compose.1panel.yml down

# 查看日志
docker compose -f docker-compose.1panel.yml logs -f

# 重启
docker compose -f docker-compose.1panel.yml restart
```

### 备份
```bash
# 执行备份
./backup.sh

# 恢复数据库
gunzip backups/db/stocksx_*.sql.gz
docker compose exec -T postgres psql -U stocksx_user -d stocksx < backups/db/stocksx_*.sql
```

### 监控
```bash
# 启动监控（Prometheus + Grafana）
docker compose -f docker-compose.1panel.yml --profile monitoring up -d

# 访问 Grafana
# http://localhost:3000 (admin/密码在 .env 中)
```

---

## 📖 文档

- **部署指南:** [DEPLOY_1PANEL.md](DEPLOY_1PANEL.md)
- **详细部署:** [1panel_deploy.md](1panel_deploy.md)
- **Phase 3 进度:** [PHASE3_PROGRESS.md](PHASE3_PROGRESS.md)
- **GitHub:** https://github.com/iiooiioo888/StocksX_V0

---

## 🆘 获取帮助

### 常见问题

**Q: 容器启动失败？**
```bash
docker compose logs app
```

**Q: 数据库连接失败？**
```bash
docker compose ps postgres
docker compose logs postgres
```

**Q: 内存不足？**
编辑 `docker-compose.1panel.yml` 限制资源：
```yaml
deploy:
  resources:
    limits:
      memory: 2G
```

### 联系方式

- **GitHub Issues:** https://github.com/iiooiioo888/StocksX_V0/issues
- **1Panel 文档:** https://1panel.cn/docs/

---

**🎉 开始量化交易之旅！**
