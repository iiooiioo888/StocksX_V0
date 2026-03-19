# 貢獻指南

感謝你對 StocksX 的興趣！

## 開發環境

```bash
# 1. 克隆專案
git clone https://github.com/iiooiioo888/StocksX_V0.git
cd StocksX_V0

# 2. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 安裝開發工具
pip install ruff pytest pytest-cov

# 5. 設定環境變數
cp .env.example .env
# 編輯 .env 填入必要配置
```

## 程式碼規範

- **Lint**: `ruff check src/ app.py pages/`
- **Format**: `ruff format src/ app.py pages/`
- **Test**: `pytest tests/ -v`

## 提交規範

```
feat: 新功能
fix: 修復 Bug
refactor: 重構（不改變功能）
docs: 文件更新
test: 測試相關
chore: 建置/工具變更
perf: 效能優化
```

## 分支策略

- `main` — 穩定版
- `develop` — 開發版
- `feature/*` — 功能分支
- `fix/*` — 修復分支

## Pull Request

1. 從 `develop` 分支建立功能分支
2. 完成後提交 PR 到 `develop`
3. 通過 CI + Code Review 後合併
