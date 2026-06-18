from pathlib import Path
from typing import Any

import requests

from turbosearch.chunking import chunk_text
from turbosearch.config import settings
from turbosearch.db import connect
from turbosearch.search import build_embedder, get_vector_index

SUPPORTED_TEXT_SUFFIXES = {".md", ".markdown", ".txt"}


def embedding_metadata(embedder) -> tuple[str, int]:
    return (
        getattr(embedder, "model_name", settings.embedding_model),
        int(getattr(embedder, "index_dim", settings.index_dim)),
    )


def ingest_url(
    source_id: str,
    title: str,
    author: str | None,
    url: str,
    *,
    source: str = "url",
) -> int:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    chunks = chunk_text(response.text)
    embedder = build_embedder()
    embedding_model, embedding_dim = embedding_metadata(embedder)
    vector_index = get_vector_index()

    with connect() as conn:
        document = conn.execute(
            """
            INSERT INTO documents (source, source_id, source_url, title, author)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (source, source_id)
            DO UPDATE SET source_url = EXCLUDED.source_url,
                          title = EXCLUDED.title,
                          author = EXCLUDED.author
            RETURNING id
            """,
            (source, source_id, url, title, author),
        ).fetchone()
        document_id = document["id"]
        old_rows = conn.execute(
            "SELECT vector_key FROM chunks WHERE document_id = %s",
            (document_id,),
        ).fetchall()
        vector_index.delete([row["vector_key"] for row in old_rows])
        conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))

        for index, chunk in enumerate(chunks):
            embedding = embedder.embed_query(chunk)
            row = conn.execute(
                """
                INSERT INTO chunks (
                  document_id,
                  chunk_index,
                  body,
                  token_count,
                  embedding_model,
                  embedding_dim,
                  index_version
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING vector_key
                """,
                (
                    document_id,
                    index,
                    chunk,
                    len(chunk.split()),
                    embedding_model,
                    embedding_dim,
                    settings.index_version,
                ),
            ).fetchone()
            vector_index.upsert(row["vector_key"], embedding)

    return len(chunks)


def ingest_text(
    *,
    source: str = "user",
    source_id: str,
    title: str,
    author: str | None,
    source_url: str,
    text: str,
) -> int:
    chunks = chunk_text(text)
    embedder = build_embedder()
    embedding_model, embedding_dim = embedding_metadata(embedder)
    vector_index = get_vector_index()

    with connect() as conn:
        document = conn.execute(
            """
            INSERT INTO documents (source, source_id, source_url, title, author)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (source, source_id)
            DO UPDATE SET source_url = EXCLUDED.source_url,
                          title = EXCLUDED.title,
                          author = EXCLUDED.author
            RETURNING id
            """,
            (source, source_id, source_url, title, author),
        ).fetchone()
        document_id = document["id"]
        old_rows = conn.execute(
            "SELECT vector_key FROM chunks WHERE document_id = %s",
            (document_id,),
        ).fetchall()
        vector_index.delete([row["vector_key"] for row in old_rows])
        conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))

        for index, chunk in enumerate(chunks):
            embedding = embedder.embed_query(chunk)
            row = conn.execute(
                """
                INSERT INTO chunks (
                  document_id,
                  chunk_index,
                  body,
                  token_count,
                  embedding_model,
                  embedding_dim,
                  index_version
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING vector_key
                """,
                (
                    document_id,
                    index,
                    chunk,
                    len(chunk.split()),
                    embedding_model,
                    embedding_dim,
                    settings.index_version,
                ),
            ).fetchone()
            vector_index.upsert(row["vector_key"], embedding)

    return len(chunks)


def iter_directory_documents(path: str | Path):
    root = Path(path).expanduser().resolve()
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_TEXT_SUFFIXES:
            continue
        yield {
            "source": "directory",
            "source_id": str(file_path.relative_to(root)),
            "title": file_path.name,
            "author": None,
            "source_url": file_path.as_uri(),
            "text": file_path.read_text(encoding="utf-8"),
        }


def ingest_directory(path: str | Path) -> dict[str, int]:
    counts = {}
    for document in iter_directory_documents(path):
        counts[document["title"]] = ingest_text(**document)
    return counts


def iter_s3_documents(bucket: str, prefix: str = "", *, client: Any | None = None):
    if client is None:
        import boto3

        client = boto3.client("s3")

    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for item in page.get("Contents", []):
            key = item["Key"]
            if key.endswith("/") or Path(key).suffix.lower() not in SUPPORTED_TEXT_SUFFIXES:
                continue
            body = client.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
            yield {
                "source": "s3",
                "source_id": key,
                "title": Path(key).name,
                "author": None,
                "source_url": f"s3://{bucket}/{key}",
                "text": body,
            }


def ingest_s3_bucket(bucket: str, prefix: str = "", *, client: Any | None = None) -> dict[str, int]:
    counts = {}
    for document in iter_s3_documents(bucket, prefix, client=client):
        counts[document["title"]] = ingest_text(**document)
    return counts
