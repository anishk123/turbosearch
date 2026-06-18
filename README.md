# turbosearch

Fast public-domain book search with AI-style overviews, built for a Gutenberg-like corpus.

The first target architecture is intentionally simple:

- Aurora PostgreSQL stores documents, chunks, metadata, full-text indexes, and vectors through `pgvector`.
- One EC2 instance runs the API, ingestion jobs, embedding generation, and overview generation.
- The local development path uses Docker Postgres with `pgvector`.
- The demo ingestion path pulls a few public-domain books from Project Gutenberg.

This gives us a practical baseline before adding a dedicated ANN sidecar such as `turbovec` or a custom Postgres extension.

## Why this shape

Project Gutenberg search can be improved by combining lexical search, vector search, metadata filters, and a concise overview of the best matches. Aurora PostgreSQL is a good first store because it keeps metadata filtering and retrieval in one operational system. EC2 keeps the app layer flexible while the prototype is still changing quickly.

## Local quickstart

```bash
cp .env.example .env
docker compose up -d
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
turbosearch init-db
turbosearch ingest-gutenberg
turbosearch search "social class and marriage"
turbosearch serve
```

Then open:

```text
http://localhost:8000/search?q=social%20class%20and%20marriage
```

## Commands

```bash
turbosearch init-db
turbosearch ingest-url https://www.gutenberg.org/cache/epub/1342/pg1342.txt --title "Pride and Prejudice" --author "Jane Austen"
turbosearch ingest-gutenberg
turbosearch search "a whale and obsession"
turbosearch serve --host 0.0.0.0 --port 8000
```

## AWS sketch

The Terraform in `infra/terraform` provisions:

- VPC with public and private subnets
- Aurora PostgreSQL cluster with `pgvector` intended to be enabled by the app migration
- EC2 app instance in a public subnet
- Security groups allowing the app to reach Aurora
- A user-data bootstrap that installs the API service

For a production version, the next hardening pass should add HTTPS, SSM-only instance access, private ALB, Secrets Manager rotation, CloudWatch dashboards, backups, and CI/CD.

## Retrieval approach

The first MVP uses hybrid scoring:

```text
score = lexical_weight * full_text_rank + vector_weight * vector_similarity
```

The overview is extractive by default, so the demo works without an LLM key. A later pass can plug in Bedrock, OpenAI, or a self-hosted model for abstractive summaries.

## Gutenberg test corpus

The included smoke test ingests:

- Pride and Prejudice
- Frankenstein
- Moby-Dick

These are public-domain texts from Project Gutenberg. The scripts keep the source URL and Gutenberg ID with each document.

