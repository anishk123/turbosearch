from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_postgres_schema_is_metadata_only() -> None:
    schema = (ROOT / "sql" / "schema.sql").read_text()

    assert "CREATE EXTENSION IF NOT EXISTS vector" not in schema
    assert " embedding vector" not in schema
    assert "DEFAULT 'gutenberg'" not in schema
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
    assert "https://github.com/RyanCodrai/turbovec" in readme
    assert "TurboQuant" in readme
    assert "Qwen/Qwen3-Embedding-0.6B" in readme
    assert "Aurora PostgreSQL" in readme
    assert "EC2" in readme
    assert "MIT" in readme
    assert "![Tests]" in readme
    assert "host-installed Ollama" in readme
    assert "qwen35_9b_awq" in readme
    assert "assets/turbosearch-demo.gif" in readme
    assert (ROOT / "assets" / "turbosearch-demo.gif").exists()
    assert "turbosearch ingest-dir" in readme
    assert "/ingest/s3" in readme
    assert "/ingest/text" in readme
    assert "/ingest/url" in readme
    assert "document_bucket_name" in readme
    assert "example documents from Project Gutenberg" in readme
    assert "flowchart TB" in readme
    assert "better Project Gutenberg" not in readme
    assert "Gutenberg-scale" not in readme
    assert "Project Gutenberg search" not in readme
    assert "Gutenberg" in readme
    assert "example" in readme.lower()


def test_aws_runtime_uses_emberlane_not_local_ollama() -> None:
    variables = (ROOT / "infra" / "terraform" / "variables.tf").read_text()
    main = (ROOT / "infra" / "terraform" / "main.tf").read_text()
    user_data = (ROOT / "infra" / "terraform" / "user_data.sh").read_text()
    outputs = (ROOT / "infra" / "terraform" / "outputs.tf").read_text()

    assert re.search(r'default\s+=\s+"qwen35_9b_awq"', variables)
    assert "llm_base_url" in main
    assert "LLM_BASE_URL=${llm_base_url}" in user_data
    assert "ollama pull" not in user_data
    assert "aws_s3_bucket" in main
    assert "document_bucket_name" in outputs
    assert "DOCUMENT_BUCKET" in user_data


def test_api_exposes_s3_ingest_endpoint() -> None:
    api = (ROOT / "src" / "turbosearch" / "api.py").read_text()

    assert '@app.post("/ingest/s3")' in api
    assert '@app.post("/ingest/text")' in api
    assert '@app.post("/ingest/url")' in api
    assert "S3IngestRequest" in api


def test_examples_are_not_embedded_in_source() -> None:
    ingest = (ROOT / "src" / "turbosearch" / "ingest.py").read_text()

    assert "gutenberg.org" not in ingest
    assert "LOCAL_EXAMPLE_DOCUMENTS" not in ingest
    assert "DEFAULT_BOOKS" not in ingest
    assert (ROOT / "examples" / "local-docs" / "search-notes.md").exists()
    assert (ROOT / "examples" / "project-gutenberg" / "urls.json").exists()
