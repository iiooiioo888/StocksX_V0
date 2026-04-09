# StocksX_V0 重構交接文檔

**上一個 Agent 完成時間**: 2026-04-10 03:00 GMT+8
**當前分支**: `main` (commit `8afb73e`)
**遠程**: `origin` → `https://github.com/iiooiioo888/StocksX_V0.git`

---

## ✅ 已完成

### 階段 1：導入/打包清理
- 移除全部 `sys.path` hack（從 62 個 → **0 個**）
- 32 個策略文件改為 `from src.strategies.base_strategy import ...` 絕對導入
- `requirements.txt` / `requirements-dev.txt` 改為安裝指引（依賴統一到 `pyproject.toml`）
- `Dockerfile` 改用 `pip install .` 從 `pyproject.toml` 安裝
- `pip install -e .` 驗證通過

### 階段 2：入口與部署清理
- 刪除 `backend/` 目錄（8 文件，1655 行死代碼，含未解決 merge conflicts）
- WebSocket 服務統一由 `src/websocket_server.py` 提供
- 入口：`python -m src`（Streamlit）/ `python -m src --ws`（WebSocket）
- 合併所有遠程 dependabot 分支到 main
- 23 個 pytest 測試通過

---

## 📋 下一步任務

### 階段 3：策略代碼收斂（最大工作量）

**核心問題**: 同一類別有多個高度重疊的文件，每個文件都包含多個策略類。

#### 3.1 合併重疊文件

| 類別 | 現狀文件 | 目標 |
|------|---------|------|
| AI/ML | `ai_strategies.py` + `ai_complete.py` + `ai_final.py` + `ai_microstructure_batch_optimization.py` | → `ai_strategies.py`（1 個文件） |
| 趨勢 | `trend_complete.py` + `advanced_trend_strategies.py` + `turtle_trading_optimized.py` + `supertrend_optimized.py` + `hull_ma_strategy.py` + `phase2_trend_batch_optimization.py` | → `trend_strategies.py`（1 個文件） |
| 突破 | `breakout_final.py` + `breakout_complete.py` + `breakout_strategies.py` + `bollinger_squeeze_optimized.py` + `fibonacci_optimized.py` + `orb_optimized.py` | → `breakout_strategies.py`（1 個文件） |
| 振盪器 | `advanced_oscillators.py` + `complete_oscillators.py` + `final_oscillators.py` + `ichimoku_optimized.py` | → `oscillator_strategies.py`（1 個文件） |
| 風控 | `risk_strategies.py` + `advanced_risk_strategies.py` + `kelly_optimized.py` + `risk_batch_optimization.py` | → `risk_strategies.py`（1 個文件） |
| 統計 | `stat_strategies.py` + `stat_complete.py` + `statistical_batch_optimization.py` | → `statistical_strategies.py`（1 個文件） |
| 執行 | `execution_strategies.py` + `execution_complete.py` + `execution_final.py` | → `execution_strategies.py`（1 個文件） |
| 宏觀 | `macro_strategies.py` + `macro_complete.py` | → `macro_strategies.py`（1 個文件） |
| 形態 | `pattern_strategies.py` + `pattern_complete.py` | → `pattern_strategies.py`（1 個文件） |

#### 3.2 更新策略註冊

合併後需要更新 `src/core/strategies_bridge.py` 和各文件的 `@register_strategy` 裝飾器，確保所有 130 個策略通過 Registry 正確註冊。

#### 3.3 刪除 batch optimization 文件

以下文件是「批量優化腳本」，不是策略定義，應移到 `scripts/` 或刪除：
- `ai_microstructure_batch_optimization.py`
- `phase2_trend_batch_optimization.py`
- `risk_batch_optimization.py`
- `statistical_batch_optimization.py`

#### 3.4 更新 `__init__.py` 文件

每個策略子目錄的 `__init__.py` 需要更新導入路徑。

---

### 階段 4：Dockerfile 最終優化

- 確認多階段構建邏輯正確（builder 安裝依賴 → runtime 執行）
- 測試 `docker compose up -d` 能正常啟動
- 確認 healthcheck 工作正常

---

### 階段 5：測試補全

- 將現有 `test_strategies.py`（根目錄）整合到 `tests/` 目錄
- 為 `src/core/` 的每個模組補充單元測試
- 確保 `pytest tests/ -q` 全部通過

---

## ⚠️ 注意事項

1. **GitHub Token**: 推送時需設置 remote URL 含 token，推送後務必 `git remote set-url origin https://github.com/iiooiioo888/StocksX_V0.git` 清除
2. **安全規則**: 不要將 token、密鑰等敏感信息提交到代碼或文檔中
3. **pip install**: 環境使用 `pip install --break-system-packages`（PEP 668 限制）
4. **類名不統一**: 部分策略類名與文件名不完全對應，合併前先用 `grep "^class "` 確認
5. **batch optimization 文件**: 包含 `warnings.filterwarnings('ignore')` 等非標準代碼，合併時注意導入順序

---

## 🔍 快速驗證命令

```bash
# 驗證導入
python3 -c "from src.core.registry import registry; print('OK')"

# 驗證策略
python3 -c "from src.strategies.trend.trend_complete import SMACross; print('OK')"

# 驗證測試
python3 -m pytest tests/test_core/test_config.py -q

# 驗證安裝
pip install -e . && python3 -c "import src.core; print('OK')"
```

---

## 專案結構快照

```
StocksX_V0/
├── app.py                    # Streamlit 主入口
├── pyproject.toml            # 依賴 & 打包配置（唯一信源）
├── Dockerfile                # 多階段構建
├── docker-compose.yml        # 容器編排
├── src/
│   ├── __main__.py           # python -m src 入口
│   ├── websocket_server.py   # WebSocket 服務
│   ├── core/                 # 核心架構（Registry, Backtest, Pipeline...）
│   ├── strategies/           # 130+ 策略（待合併）
│   │   ├── base_strategy.py  # 策略基類
│   │   ├── trend/            # 6 文件 → 目標 1 文件
│   │   ├── breakout/         # 6 文件 → 目標 1 文件
│   │   ├── oscillator/       # 4 文件 → 目標 1 文件
│   │   ├── ai_ml/            # 4 文件 → 目標 1 文件
│   │   ├── risk_management/  # 4 文件 → 目標 1 文件
│   │   ├── statistical/      # 3 文件 → 目標 1 文件
│   │   ├── execution/        # 3 文件 → 目標 1 文件
│   │   ├── macro/            # 2 文件 → 目標 1 文件
│   │   ├── pattern/          # 2 文件 → 目標 1 文件
│   │   ├── microstructure/   # 1 文件（OK）
│   │   ├── ml_strategies/    # 待確認
│   │   ├── nlp_strategies/   # 待確認
│   │   ├── quant_strategies/ # 待確認
│   │   └── rl_strategies/    # 待確認
│   ├── data/                 # 數據層
│   ├── trading/              # 交易引擎
│   ├── analytics/            # 分析工具
│   └── ...
├── pages/                    # Streamlit 多頁應用
├── tests/                    # pytest 測試
├── scripts/                  # 工具腳本
└── docs/                     # 文檔
```
