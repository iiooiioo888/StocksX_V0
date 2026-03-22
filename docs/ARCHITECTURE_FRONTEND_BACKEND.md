# 🚀 StocksX 前後端分離架構指南

**版本**: v1.2.0  
**日期**: 2026-03-22  
**架構**: FastAPI + Vue.js + WebSocket + SQLite

---

## 📋 目錄

1. [架構總覽](#架構總覽)
2. [快速開始](#快速開始)
3. [後端 API](#後端-api)
4. [前端界面](#前端界面)
5. [API 文檔](#api-文檔)
6. [部署指南](#部署指南)

---

## 架構總覽

### 技術棧

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ◄────►  │    Backend   │ ◄────►  │  Database   │
│   Vue.js 3  │  HTTP   │   FastAPI    │  SQLite │  SQLite DB  │
│   WebSocket │  WS     │   Python     │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
```

### 目錄結構

```
StocksX_V0/
├── backend/                    # 後端 API
│   ├── main.py                # 應用入口
│   ├── database.py            # 數據庫配置
│   ├── models.py              # ORM 模型
│   ├── schemas.py             # Pydantic 模式
│   ├── requirements.txt       # Python 依賴
│   └── api/
│       ├── strategies.py      # 策略 API
│       ├── portfolio.py       # 組合 API
│       └── scores.py          # 評分 API
├── frontend/                   # 前端界面
│   ├── index.html             # 主頁面
│   └── package.json           # Node 依賴
├── src/                        # 核心策略代碼
│   └── strategies/            # 130 策略
├── scripts/                    # 工具腳本
├── docs/                       # 文檔
├── start.sh                    # 快速啟動
└── data/                       # 數據庫文件
    └── stocksx.db
```

---

## 快速開始

### 方法 1: 使用啟動腳本（推薦）

```bash
cd StocksX_V0
./start.sh
```

### 方法 2: 手動啟動

```bash
# 1. 安裝依賴
cd backend
pip3 install -r requirements.txt

# 2. 初始化數據庫
python3 database.py

# 3. 啟動服務
python3 main.py
```

### 訪問服務

- **前端界面**: http://localhost:8000
- **API 文檔**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康檢查**: http://localhost:8000/api/health

---

## 後端 API

### 核心功能

#### 1. 策略管理

```bash
# 獲取所有策略
GET /api/strategies

# 獲取策略詳情
GET /api/strategies/{name}

# 創建新策略
POST /api/strategies

# 更新策略
PUT /api/strategies/{name}

# 刪除策略
DELETE /api/strategies/{name}

# 獲取策略信號
GET /api/strategies/{name}/signals

# 創建新信號
POST /api/strategies/{name}/signals
```

#### 2. 投資組合

```bash
# 獲取所有組合
GET /api/portfolio

# 獲取組合詳情
GET /api/portfolio/{id}

# 創建組合
POST /api/portfolio

# 更新組合權重
PUT /api/portfolio/{id}

# 執行回測
POST /api/portfolio/{id}/backtest
```

#### 3. 策略評分

```bash
# 獲取所有評分
GET /api/scores?grade=A&min_score=70

# 獲取排名
GET /api/scores/ranking?top_n=50

# 獲取策略評分
GET /api/scores/{strategy_name}

# 創建/更新評分
POST /api/scores/{strategy_name}

# 等級分佈統計
GET /api/scores/statistics/grade-distribution
```

#### 4. WebSocket 實時推送

```javascript
// 連接 WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/signals');

// 接收實時信號
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'signals') {
        console.log('收到信號:', data.data);
    }
};

// 發送心跳
ws.send('ping');
```

---

## 前端界面

### 功能特性

- ✅ 實時信號推送（WebSocket）
- ✅ 策略評分排名
- ✅ 統計儀表板
- ✅ 響應式設計
- ✅ 無需編譯（CDN Vue 3）

### 自定義

編輯 `frontend/index.html`：

```javascript
// 修改 API 地址
const API_BASE = 'http://your-server:8000/api';

// 修改 WebSocket 地址
const WS_URL = 'ws://your-server:8000/ws/signals';
```

---

## API 文檔

### Swagger UI

訪問 http://localhost:8000/docs 查看交互式 API 文檔。

### 示例請求

#### 獲取策略列表

```bash
curl -X GET "http://localhost:8000/api/strategies?category=trend&limit=10"
```

#### 創建投資組合

```bash
curl -X POST "http://localhost:8000/api/portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "保守組合",
    "initial_capital": 1000000,
    "weights": {
      "sma_cross": 0.3,
      "macd_cross": 0.3,
      "rsi": 0.4
    }
  }'
```

#### 執行回測

```bash
curl -X POST "http://localhost:8000/api/portfolio/1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "strategies": ["sma_cross", "macd_cross"],
    "weights": {"sma_cross": 0.5, "macd_cross": 0.5},
    "initial_capital": 1000000
  }'
```

---

## 數據庫

### 表結構

#### strategies（策略表）
| 字段 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵 |
| name | VARCHAR(100) | 策略名 |
| category | VARCHAR(50) | 類別 |
| description | TEXT | 描述 |
| params | TEXT | 參數（JSON） |
| created_at | DATETIME | 創建時間 |
| updated_at | DATETIME | 更新時間 |

#### signals（信號表）
| 字段 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵 |
| strategy_id | INTEGER | 策略 ID |
| signal_type | VARCHAR(10) | BUY/SELL/HOLD |
| price | FLOAT | 價格 |
| timestamp | DATETIME | 時間戳 |
| metadata | TEXT | 元數據（JSON） |

#### scores（評分表）
| 字段 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵 |
| strategy_id | INTEGER | 策略 ID |
| score | FLOAT | 評分 (0-100) |
| grade | VARCHAR(5) | 等級 (A+/A/B...) |
| sharpe_ratio | FLOAT | 夏普比率 |
| total_return | FLOAT | 總回報 |
| max_drawdown | FLOAT | 最大回撤 |
| win_rate | FLOAT | 勝率 |
| profit_factor | FLOAT | 盈虧比 |
| evaluated_at | DATETIME | 評估時間 |

---

## 部署指南

### 開發環境

```bash
# 本地啟動
./start.sh
```

### 生產環境

#### 1. 使用 Gunicorn

```bash
# 安裝
pip install gunicorn

# 啟動
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 2. Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ ./backend/
COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3. Nginx 反向代理

```nginx
server {
    listen 80;
    server_name stocksx.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 安全配置

### CORS 配置

編輯 `backend/main.py`：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### JWT 認證（未來功能）

```python
# 安裝依賴
pip install pyjwt python-jose

# 添加認證中間件
from utils.auth import verify_token

@app.middleware("http")
async def auth_middleware(request, call_next):
    if not request.url.path.startswith("/api/health"):
        token = request.headers.get("Authorization")
        if not verify_token(token):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)
```

---

## 性能優化

### 數據庫優化

```python
# 添加索引
class Strategy(Base):
    name = Column(String(100), unique=True, index=True)
    category = Column(String(50), index=True)
```

### 緩存策略

```python
# 使用 Redis 緩存
from redis import Redis
cache = Redis(host='localhost', port=6379)

@router.get("/strategies")
def get_strategies():
    cached = cache.get("strategies")
    if cached:
        return json.loads(cached)
    
    strategies = db.query(Strategy).all()
    cache.setex("strategies", 300, json.dumps(strategies))
    return strategies
```

---

## 監控與日誌

### 健康檢查

```bash
curl http://localhost:8000/api/health
```

響應：
```json
{
  "status": "healthy",
  "timestamp": "2026-03-22T21:50:00",
  "version": "1.2.0",
  "strategies": 130
}
```

### 日誌配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("stocksx")
```

---

## 故障排除

### 常見問題

#### 1. 端口被佔用

```bash
# 查找佔用端口的進程
lsof -i :8000

# 終止進程
kill -9 <PID>
```

#### 2. 數據庫鎖定

```bash
# 刪除數據庫文件
rm data/stocksx.db

# 重新初始化
python3 backend/database.py
```

#### 3. WebSocket 連接失敗

- 檢查防火牆設置
- 確認 WebSocket 路由正確
- 查看瀏覽器控制台錯誤

---

## 後續開發

### 路線圖

- [ ] JWT 認證系統
- [ ] Redis 緩存層
- [ ] PostgreSQL 支持
- [ ] 單元測試覆蓋
- [ ] CI/CD 流程
- [ ] Docker Compose 部署
- [ ] 監控儀表板（Grafana）
- [ ] 告警系統（Prometheus）

---

## 貢獻指南

### 代碼風格

- 後端：遵循 PEP 8
- 前端：Vue 3 Composition API
- 提交信息：Conventional Commits

### 提交 PR

1. Fork 項目
2. 創建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

---

## 許可證

MIT License

---

## 聯繫支持

- **GitHub Issues**: https://github.com/iiooiioo888/StocksX_V0/issues
- **API 文檔**: http://localhost:8000/docs
- **郵箱**: support@stocksx.ai

---

**StocksX v1.2.0 - 前後端分離架構** 🚀
