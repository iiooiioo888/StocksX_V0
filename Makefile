# ════════════════════════════════════════════════════════════
# StocksX Makefile — 開發 & 部署命令
# ════════════════════════════════════════════════════════════

.PHONY: help lint format type-check test test-cov test-fast security run run-ws docker docker-build docker-logs docker-down docker-monitor clean install dev

# ─── 預設 ───
help: ## 顯示幫助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ─── 安裝 ───
install: ## 安裝專案（使用 pyproject.toml）
	pip install -e .

dev: ## 安裝開發依賴（使用 pyproject.toml）
	pip install -e ".[dev]"
	pre-commit install

# ─── 代碼品質 ───
lint: ## 代碼檢查
	ruff check src/ pages/ app.py tests/

format: ## 代碼格式化
	ruff format src/ pages/ app.py tests/

lint-fix: ## 自動修復 lint 問題
	ruff check --fix src/ pages/ app.py tests/
	ruff format src/ pages/ app.py tests/

type-check: ## 類型檢查
	mypy src/core/ --ignore-missing-imports --no-error-summary || true

# ─── 測試 ───
test: ## 運行測試
	pytest tests/ -v --timeout=60

test-cov: ## 測試 + 覆蓋率
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html --timeout=60

test-fast: ## 快速測試（跳過慢測試）
	pytest tests/ -v -m "not slow" --timeout=30

# ─── 安全 ───
security: ## 安全掃描
	bandit -r src/ -ll
	safety check --output text || true

# ─── 運行 ───
run: ## 啟動主應用
	streamlit run app.py

run-ws: ## 啟動 WebSocket 服務
	python -m src.websocket_server

# ─── Docker ───
docker: ## 啟動 Docker 服務
	docker compose up -d

docker-build: ## 構建 Docker 鏡像
	docker compose build --no-cache

docker-logs: ## 查看日誌
	docker compose logs -f app

docker-down: ## 停止 Docker 服務
	docker compose down

docker-monitor: ## 啟動含監控的服務
	docker compose --profile monitoring up -d

# ─── 清理 ───
clean: ## 清理快取和臨時文件
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -f .coverage bandit-report.json 2>/dev/null || true
