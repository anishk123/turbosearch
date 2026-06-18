from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_postgres_schema_is_metadata_only() -> None:
    schema = (ROOT / "sql" / "schema.sql").read_text()

    assert "CREATE EXTENSION IF NOT EXISTS vector" not in schema
    assert " embedding vector" not in schema
    assert "vector_key" in schema
    assert "embedding_model" in schema
    assert "embedding_dim" in schema
    assert "index_version" in schema


def test_compose_runs_postgres_and_api_against_host_ollama_without_pgvector() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()
    env_example = (ROOT / ".env.example").read_text()

    assert "postgres:" in compose
    assert "api:" in compose
    assert "ollama:" not in compose
    assert "host.docker.internal:11434/v1" in compose
    assert "LLM_BASE_URL=http://host.docker.internal:11434/v1" in env_example
    assert "LLM_BASE_URL=http://localhost:11434/v1" not in env_example
    assert "pgvector/pgvector" not in compose
    assert "POSTGRES_USER: turbosearch" in compose


def test_readme_describes_postgres_plus_turbovec_architecture() -> None:
    readme = (ROOT / "README.md").read_text()

    assert "Postgres + turbovec" in readme
    assert "Qwen/Qwen3-Embedding-0.6B" in readme
    assert "Aurora PostgreSQL" in readme
    assert "EC2" in readme
    assert "MIT" in readme
    assert "![Tests]" in readme
    assert "host-installed Ollama" in readme
    assert "qwen35_9b_awq" in readme


def test_aws_runtime_uses_emberlane_not_local_ollama() -> None:
    variables = (ROOT / "infra" / "terraform" / "variables.tf").read_text()
    main = (ROOT / "infra" / "terraform" / "main.tf").read_text()
    user_data = (ROOT / "infra" / "terraform" / "user_data.sh").read_text()

    assert re.search(r'default\s+=\s+"qwen35_9b_awq"', variables)
    assert "llm_base_url" in main
    assert "LLM_BASE_URL=${llm_base_url}" in user_data
    assert "ollama pull" not in user_data
