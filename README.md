# turbosearch

![Tests](https://img.shields.io/badge/tests-passing-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-3776ab)
![PostgreSQL](https://img.shields.io/badge/postgres-16-4169e1)
![Qwen](https://img.shields.io/badge/embeddings-Qwen3--0.6B-111827)
![AWS](https://img.shields.io/badge/aws-Aurora%20%2B%20EC2-ff9900)

Fast semantic search and cited AI overviews for public-domain books, built on a Postgres + turbovec architecture.

`turbosearch` is a local-first prototype for a better Project Gutenberg search experience. It combines Postgres metadata filtering, turbovec vector retrieval, Qwen embeddings, and an OpenAI-compatible LLM summary layer so readers can find passages faster and understand why the results matter.

```mermaid
flowchart LR
  User["Reader query"] --> API["FastAPI search API"]
  API --> PG["Postgres metadata<br/>documents, chunks, filters, FTS"]
  API --> Qwen["Qwen/Qwen3-Embedding-0.6B<br/>MRL-truncated query vector"]
  Qwen --> Turbo["turbovec host index<br/>allowlist vector search"]
  PG --> Allow["candidate vector keys"]
  Allow --> Turbo
  Turbo --> Merge["hybrid merge + citations"]
  Merge --> LLM["OpenAI-compatible LLM<br/>overview with sources"]
  LLM --> API
```

## Goals

- Search Gutenberg-scale books by meaning, not just exact keywords.
- Keep Postgres as the durable source of truth for documents, chunks, metadata, filters, and lexical search.
- Use turbovec as the fast local ANN layer, with Postgres-provided allowlists for filtered search.
- Use `Qwen/Qwen3-Embedding-0.6B` for local, high-quality embeddings with MRL truncation for speed and memory control.
- Generate LLM summaries immediately, with citations back to exact passages and Gutenberg source URLs.
- Prove everything locally before deploying Aurora PostgreSQL + EC2 on AWS.

## Stack

| Layer | Local | AWS |
|---|---|---|
| API | FastAPI on Docker Compose | EC2 systemd service |
| Metadata | PostgreSQL 16 | Aurora PostgreSQL |
| Vector index | turbovec in-process/host sidecar | turbovec on EC2 |
| Embeddings | Qwen3-Embedding-0.6B | Qwen3-Embedding-0.6B on EC2 |
| Summary | OpenAI-compatible endpoint, Ollama default | OpenAI-compatible endpoint or self-hosted model |
| Corpus | Project Gutenberg text files | S3/Gutenberg ingestion jobs |

## Local Run

```bash
cp .env.example .env
docker compose up --build
docker compose exec ollama ollama pull qwen3:0.6b
```

In another shell:

```bash
docker compose exec api turbosearch init-db
docker compose exec api turbosearch ingest-gutenberg
docker compose exec api turbosearch search "social class and marriage"
```

API:

```bash
curl "http://localhost:8000/search?q=a%20whale%20and%20obsession"
```

The first embedding run downloads `Qwen/Qwen3-Embedding-0.6B`, so expect a slower cold start.

## Local Smoke Test

```bash
docker compose exec api python scripts/e2e_gutenberg.py
```

The smoke path initializes Postgres, ingests a few Gutenberg books, builds/upserts local vector entries, runs search queries, and asks the configured LLM endpoint for summaries.

## AWS Deploy

```bash
cd infra/terraform
terraform init
terraform apply
```

Terraform provisions:

- VPC, public/private subnets, and security groups
- Aurora PostgreSQL for metadata and filtering
- EC2 for API, Qwen embeddings, and turbovec
- User-data bootstrap for Python dependencies, Ollama, `qwen3:0.6b`, and the API service

After apply, validate the service URL from Terraform output:

```bash
terraform output app_url
curl "$(terraform output -raw app_url)/health"
```

The EC2 user-data script installs the service and runtime dependencies. Add SSM Session Manager or an SSH key pair before running manual commands on the instance.

## Design Notes

Postgres stores `documents` and `chunks`, including `vector_key`, `embedding_model`, `embedding_dim`, and `index_version`. It does not store vector columns. turbovec owns dense retrieval and receives allowlists from Postgres when filters are selective.

Search flow:

1. Postgres narrows candidates with metadata, ACL, source, language, and full-text filters.
2. Qwen embeds the query.
3. turbovec searches the candidate vector keys.
4. The API merges scores, fetches chunk metadata, and assembles citations.
5. The LLM writes a concise overview grounded in the top passages.

## License

MIT
