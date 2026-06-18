DOCKER ?= docker

.PHONY: e2e-local e2e-turbovec-qwen test lint

e2e-local:
	@curl -fsS http://localhost:11434/v1/models >/dev/null || \
		(echo "Ollama must be running on localhost:11434. Run: ollama serve" && exit 1)
	EMBEDDING_PROVIDER=hash VECTOR_BACKEND=simple $(DOCKER) compose up --build -d
	@ready=0; \
	for i in $$(seq 1 60); do \
		if $(DOCKER) compose exec api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" >/dev/null 2>&1; then \
			ready=1; \
			break; \
		fi; \
		sleep 2; \
	done; \
	if [ "$$ready" != "1" ]; then \
		echo "API did not become healthy in time"; \
		$(DOCKER) compose logs api --tail=80; \
		exit 1; \
	fi
	$(DOCKER) compose exec api turbosearch init-db
	$(DOCKER) compose exec api python scripts/e2e_local.py

test:
	python -m pytest -q

lint:
	ruff check .


e2e-turbovec-qwen:
	@curl -fsS http://localhost:11434/v1/models >/dev/null || \
		(echo "Ollama must be running on localhost:11434. Run: ollama serve" && exit 1)
	EMBEDDING_PROVIDER=qwen VECTOR_BACKEND=turbovec $(DOCKER) compose up --build -d
	@ready=0; \
	for i in $$(seq 1 90); do \
		if $(DOCKER) compose exec api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" >/dev/null 2>&1; then \
			ready=1; \
			break; \
		fi; \
		sleep 2; \
	done; \
	if [ "$$ready" != "1" ]; then \
		echo "API did not become healthy in time"; \
		$(DOCKER) compose logs api --tail=120; \
		exit 1; \
	fi
	$(DOCKER) compose exec api turbosearch init-db
	$(DOCKER) compose exec api python scripts/e2e_local.py
	$(DOCKER) compose exec api python scripts/verify_qwen_turbovec.py
