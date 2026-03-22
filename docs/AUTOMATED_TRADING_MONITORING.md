# 🚀 StocksX 自動化交易 + 監控系統指南

**版本**: v1.3.0  
**日期**: 2026-03-22  
**功能**: 自動化交易 + Prometheus 監控 + Grafana 儀表板

---

## 📋 目錄

1. [自動化交易](#自動化交易)
2. [監控系統](#監控系統)
3. [快速開始](#快速開始)
4. [配置說明](#配置說明)
5. [告警規則](#告警規則)
6. [Docker 部署](#docker-部署)

---

## 自動化交易

### 功能特性

- ✅ **自動跟隨信號** - WebSocket 實時接收策略信號
- ✅ **風險控制** - 止損/止盈/持倉限制
- ✅ **模擬交易** - Paper Trading 模式
- ✅ **持倉管理** - 自動跟蹤持倉和盈虧
- ✅ **交易日誌** - 完整交易記錄
- ✅ **性能報告** - 每小時自動生成

### 架構

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Strategy   │ ──► │   Trading    │ ──► │   Broker    │
│  Signals    │ WS  │    Engine    │ API │   (Paper)   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Risk Mgmt   │
                    │  - Stop Loss │
                    │  - Take Profit│
                    │  - Position  │
                    └──────────────┘
```

### 快速開始

```bash
# 1. 安裝依賴
cd trading
pip3 install -r requirements.txt

# 2. 配置交易參數
cp config.example.yaml config.yaml
# 編輯 config.yaml

# 3. 啟動交易引擎
python3 trading_engine.py
```

### 配置示例

```yaml
trading:
  enabled: true
  paper_trading: true  # 模擬交易
  
broker:
  name: "paper"  # paper, alpaca, binance
  
risk:
  max_position_size: 10000  # 最大持倉 $10,000
  stop_loss_pct: 2.0  # 止損 2%
  take_profit_pct: 5.0  # 止盈 5%
  max_daily_loss: 1000  # 每日最大虧損 $1,000
  
strategies:
  - name: "sma_cross"
    weight: 0.3
    enabled: true
  - name: "macd_cross"
    weight: 0.3
    enabled: true
  - name: "rsi"
    weight: 0.4
    enabled: true
```

### 交易日誌

```
2026-03-22 22:10:00 - INFO - 📡 收到 3 個信號
2026-03-22 22:10:01 - INFO - 📈 買入：AAPL x 100 @ $150
2026-03-22 22:15:00 - INFO - 📉 賣出：AAPL x 100 @ $155 | 盈虧：$500 (+3.33%)
2026-03-22 22:20:00 - WARNING - 🚨 止損：TSLA (-2.50%)
```

---

## 監控系統

### 技術棧

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   StocksX   │ ──► │  Prometheus  │ ──► │   Grafana   │
│   Metrics   │ 8001│   Server     │ 9090│ Dashboard   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Alertmanager │
                    │   9093       │
                    └──────────────┘
```

### 指標類型

#### 交易指標
- `stocksx_trades_total` - 總交易數
- `stocksx_trades_volume` - 交易量
- `stocksx_position_value` - 持倉價值
- `stocksx_pnl_total` - 總盈虧
- `stocksx_pnl_daily` - 當日盈虧

#### 策略指標
- `stocksx_strategy_score` - 策略評分
- `stocksx_strategy_sharpe` - 夏普比率
- `stocksx_strategy_drawdown` - 最大回撤

#### 風險指標
- `stocksx_risk_exposure` - 風險暴露
- `stocksx_risk_utilization` - 風險利用率

#### 系統指標
- `stocksx_system_uptime` - 系統運行時間
- `stocksx_websocket_status` - WebSocket 狀態
- `stocksx_api_latency` - API 延遲

### 啟動監控

```bash
# 1. 安裝 Prometheus 客戶端
pip3 install prometheus-client

# 2. 啟動指標導出器
python3 monitoring/metrics_exporter.py

# 3. 訪問指標端點
curl http://localhost:8001/metrics
```

---

## 快速開始

### 方法 1: Docker Compose（推薦）

```bash
# 一鍵啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

**訪問服務**:
- StocksX API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Alertmanager: http://localhost:9093

### 方法 2: 手動啟動

```bash
# 1. 啟動 API
python3 backend/main.py &

# 2. 啟動交易引擎
python3 trading/trading_engine.py &

# 3. 啟動指標導出器
python3 monitoring/metrics_exporter.py &

# 4. 啟動 Prometheus（需要單獨安裝）
prometheus --config.file=monitoring/prometheus.yml

# 5. 啟動 Grafana（需要單獨安裝）
grafana-server
```

---

## Grafana 儀表板

### 預設儀表板

导入 `monitoring/grafana_dashboard.json`

**面板包括**:
1. 當日盈虧（Stat）
2. 總交易數（Stat）
3. WebSocket 狀態（Stat）
4. 風險利用率（Stat）
5. 每日盈虧趨勢（Time Series）
6. 策略夏普比率（Time Series）
7. 策略表現（Table）
8. 系統運行時間（Gauge）
9. 風險暴露（Gauge）
10. 活躍信號（Gauge）

### 自定義儀表板

1. 訪問 http://localhost:3000
2. 點擊 "+" → "Import"
3. 上傳 JSON 文件或輸入 ID

---

## 告警規則

### 預設告警

| 告警名稱 | 條件 | 嚴重性 |
|----------|------|--------|
| HighDailyLoss | 當日虧損 < -$1000 | 🔴 Critical |
| HighDrawdown | 回撤 > 15% | 🟡 Warning |
| WebSocketDisconnected | WS 斷線 > 2 分鐘 | 🟡 Warning |
| LowSharpeRatio | 夏普 < 0.5 | ℹ️ Info |
| HighRiskUtilization | 風險利用率 > 80% | 🟡 Warning |
| SystemDown | 系統離線 > 5 分鐘 | 🔴 Critical |

### 配置通知

編輯 `monitoring/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@stocksx.ai'

route:
  receiver: 'telegram'

receivers:
  - name: 'telegram'
    telegram_configs:
      - bot_token: 'YOUR_BOT_TOKEN'
        chat_id: 'YOUR_CHAT_ID'
  
  - name: 'email'
    email_configs:
      - to: 'admin@stocksx.ai'
        subject: 'StocksX 告警：{{ .GroupLabels.alertname }}'
```

### Telegram 通知

```bash
# 1. 創建 Telegram Bot
# 聯繫 @BotFather 獲取 token

# 2. 獲取 Chat ID
# 發送消息給 @userinfobot

# 3. 配置 alertmanager.yml
# 重啟 Alertmanager
```

---

## Docker 部署

### 環境變量

```bash
# .env 文件
PAPER_TRADING=true
DATABASE_URL=sqlite:///data/stocksx.db
GRAFANA_PASSWORD=admin
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 生產環境配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  stocksx-api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
    
  prometheus:
    volumes:
      - prometheus_data:/prometheus
    command:
      - '--storage.tsdb.retention.time=30d'
  
  grafana:
    environment:
      - GF_SERVER_ROOT_URL=https://grafana.stocksx.ai
      - GF_AUTH_ANONYMOUS_ENABLED=false
```

### 更新部署

```bash
# 拉取最新代碼
git pull

# 重建鏡像
docker-compose build

# 滾動更新
docker-compose up -d --no-deps --build stocksx-api
```

---

## API 使用示例

### Python SDK

```python
import requests

# 獲取策略列表
response = requests.get('http://localhost:8000/api/strategies')
strategies = response.json()

# 創建投資組合
portfolio = {
    'name': '保守組合',
    'initial_capital': 1000000,
    'weights': {
        'sma_cross': 0.3,
        'macd_cross': 0.3,
        'rsi': 0.4
    }
}

response = requests.post(
    'http://localhost:8000/api/portfolio',
    json=portfolio
)

# 執行回測
backtest = {
    'strategies': ['sma_cross', 'macd_cross'],
    'weights': {'sma_cross': 0.5, 'macd_cross': 0.5},
    'initial_capital': 1000000
}

response = requests.post(
    'http://localhost:8000/api/portfolio/1/backtest',
    json=backtest
)
```

### JavaScript SDK

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:8000/api';

// 獲取策略評分
async function getScores() {
    const response = await axios.get(`${API_BASE}/scores/ranking?top_n=10`);
    console.log('Top 10 策略:', response.data);
}

// WebSocket 實時信號
const ws = new WebSocket('ws://localhost:8000/ws/signals');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'signals') {
        console.log('收到信號:', data.data);
    }
};
```

---

## 性能優化

### Prometheus 優化

```yaml
# prometheus.yml
global:
  scrape_interval: 30s  # 降低抓取頻率
  evaluation_interval: 30s

# 降低保留時間
command:
  - '--storage.tsdb.retention.time=15d'
  - '--storage.tsdb.retention.size=5GB'
```

### Grafana 優化

```ini
# grafana.ini
[analytics]
reporting_enabled = false

[users]
allow_sign_up = false

[snapshots]
snapshot_enabled = false
```

---

## 故障排除

### 常見問題

#### 1. 交易引擎無法連接 WebSocket

```bash
# 檢查 API 是否運行
curl http://localhost:8000/api/health

# 檢查 WebSocket 端點
wscat -c ws://localhost:8000/ws/signals
```

#### 2. Prometheus 無法抓取指標

```bash
# 檢查指標端點
curl http://localhost:8001/metrics

# 檢查 Prometheus 配置
promtool check config monitoring/prometheus.yml
```

#### 3. Grafana 儀表板無數據

- 確認 Prometheus 數據源已添加
- 檢查指標名稱是否正確
- 確認時間範圍設置正確

---

## 後續開發

### 路線圖

- [ ] 支援更多券商（Alpaca, Binance, IB）
- [ ] 回測引擎優化
- [ ] 機器學習選策略
- [ ] 移動 App 通知
- [ ] 多賬戶管理
- [ ] 稅務報告生成

---

## 安全建議

### 生產環境

1. **啟用 HTTPS**
   ```bash
   # 使用 Nginx 反向代理
   # 申請 Let's Encrypt 證書
   ```

2. **配置認證**
   ```python
   # 添加 JWT 認證中間件
   from backend.utils.auth import verify_token
   ```

3. **限制 API 訪問**
   ```yaml
   # CORS 配置
   allow_origins: ["https://your-domain.com"]
   ```

4. **定期備份**
   ```bash
   # 備份數據庫
   docker cp stocksx-api:/app/data/stocksx.db ./backup/
   ```

---

## 許可證

MIT License

---

## 聯繫支持

- **GitHub**: https://github.com/iiooiioo888/StocksX_V0
- **文檔**: http://localhost:8000/docs
- **監控**: http://localhost:3000

---

**StocksX v1.3.0 - 自動化交易 + 監控系統** 🚀
