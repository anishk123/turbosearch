from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_postgres_schema_is_metadata_only() -> None:
    schema = (ROOT / "sql" / "schema.sql").read_text()

    assert "CREATE EXTENSION IF NOT EXISTS vector" not in schema
    assert " embedding vector" not in schema
    assert "vector_key" in schema
    assert "embedding_model" in schema
    assert "embedding_dim" in schema
    assert "index_version" in schema


def test_compose_runs_postgres_api_and_ollama_without_pgvector() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()

    assert "postgres:" in compose
    assert "api:" in compose
    assert "ollama:" in compose
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

