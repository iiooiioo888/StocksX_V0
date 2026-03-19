.PHONY: lint test format run docker

lint:
	ruff check src/ pages/

format:
	ruff format src/ pages/

test:
	pytest tests/ -v

run:
	streamlit run app.py

docker:
	docker compose up -d
