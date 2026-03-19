# 貢獻指南

感謝你對 StocksX 的興趣！

## 🚀 快速開始

```bash
# 1. 克隆專案
git clone https://github.com/iiooiioo888/StocksX_V0.git
cd StocksX_V0

# 2. 建立虛擬環境
python -m venv .venv && source .venv/bin/activate

# 3. 安裝依賴（使用 pyproject.toml）
pip install -e ".[dev]"

# 4. 安裝 pre-commit hooks
pre-commit install

# 5. 設定環境變數
cp .env.example .env
```

## 📋 開發命令

```bash
# 代碼品質
make lint          # Ruff 檢查
make format        # Ruff 格式化
make type-check    # mypy 類型檢查

# 測試
make test          # 運行測試
make test-cov      # 測試 + 覆蓋率
make test-fast     # 快速測試（跳過慢測試）

# 安全
make security      # bandit 安全掃描

# 運行
make run           # 啟動主應用
make run-ws        # 啟動 WebSocket 服務
```

## 📝 提交規範

採用 [Conventional Commits](https://www.conventionalcommits.org/)：

| 前綴 | 說明 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | 修復 Bug |
| `docs:` | 文件更新 |
| `refactor:` | 重構（不改變功能） |
| `test:` | 測試相關 |
| `chore:` | 建置/工具變更 |
| `perf:` | 效能優化 |
| `ci:` | CI/CD 變更 |

範例：
```
feat: 新增 MACD 策略參數網格搜索
fix: 修復 WebSocket 斷線重連問題
docs: 更新部署指南
```

## 🌿 分支策略

```
main          ← 穩定版（自動部署）
├── develop   ← 開發版
│   ├── feature/*   ← 功能分支
│   └── fix/*       ← 修復分支
```

**流程：**
1. 從 `develop` 建立功能分支
2. 開發 + 測試
3. 提交 PR 到 `develop`
4. CI 通過 + Code Review → 合併
5. 定期從 `develop` 合併到 `main`

## 🏗️ 架構原則

- **六層分離**：表現 → 應用 → 領域 → 基礎設施 → 數據 → 持久化
- **依賴注入**：使用 `Container` 管理組件，便於測試
- **策略註冊**：使用 `@register_strategy` 裝飾器，避免手動維護字典
- **中間件管道**：日誌/重試/限流通過 `MiddlewarePipeline` 組合

## 🧪 測試

```bash
# 運行所有測試
pytest tests/ -v

# 運行特定測試文件
pytest tests/test_core/test_orchestrator.py -v

# 測試覆蓋率
pytest tests/ --cov=src --cov-report=html
# 然後打開 htmlcov/index.html
```

## 🔒 安全

- 不要提交 `.env` 文件
- 不要在代碼中硬編碼密鑰
- 使用 `bandit` 掃描安全問題
- 依賴漏洞由 Dependabot 自動檢測

## 📦 發布流程

1. 更新 `src/version.py` 中的版本號
2. 更新 `CHANGELOG`
3. 更新 `README.md` 的更新日誌
4. 提交 PR → 合併到 `main`
5. GitHub Actions 自動構建 Docker 鏡像並推送 GHCR
