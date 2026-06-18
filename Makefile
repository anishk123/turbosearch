.PHONY: e2e-local test lint

e2e-local:
	docker compose up --build -d
	docker compose exec api turbosearch init-db
	docker compose exec api python scripts/e2e_local.py

test:
	python -m pytest -q

lint:
	ruff check .
