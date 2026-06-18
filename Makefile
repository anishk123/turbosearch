.PHONY: e2e-local test lint

e2e-local:
	@curl -fsS http://localhost:11434/v1/models >/dev/null || \
		(echo "Ollama must be running on localhost:11434. Run: ollama serve" && exit 1)
	EMBEDDING_PROVIDER=hash docker compose up --build -d
	@ready=0; \
	for i in $$(seq 1 60); do \
		if docker compose exec api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" >/dev/null 2>&1; then \
			ready=1; \
			break; \
		fi; \
		sleep 2; \
	done; \
	if [ "$$ready" != "1" ]; then \
		echo "API did not become healthy in time"; \
		docker compose logs api --tail=80; \
		exit 1; \
	fi
	docker compose exec api turbosearch init-db
	docker compose exec api python scripts/e2e_local.py

test:
	python -m pytest -q

lint:
	ruff check .
