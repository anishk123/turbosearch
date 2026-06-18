from dataclasses import dataclass

import requests

from turbosearch.chunking import chunk_text, strip_gutenberg_boilerplate
from turbosearch.config import settings
from turbosearch.db import connect
from turbosearch.search import build_embedder, get_vector_index


@dataclass(frozen=True)
class ExampleDocument:
    source_id: str
    title: str
    author: str
    url: str


DEFAULT_BOOKS = [
    ExampleDocument(
        source_id="1342",
        title="Pride and Prejudice",
        author="Jane Austen",
        url="https://www.gutenberg.org/cache/epub/1342/pg1342.txt",
    ),
    ExampleDocument(
        source_id="84",
        title="Frankenstein; Or, The Modern Prometheus",
        author="Mary Wollstonecraft Shelley",
        url="https://www.gutenberg.org/cache/epub/84/pg84.txt",
    ),
    ExampleDocument(
        source_id="2701",
        title="Moby-Dick; Or, The Whale",
        author="Herman Melville",
        url="https://www.gutenberg.org/cache/epub/2701/pg2701.txt",
    ),
]

LOCAL_EXAMPLE_DOCUMENTS = [
    {
        "source_id": "example-semantic-retrieval",
        "title": "Semantic Retrieval Notes",
        "author": "Turbosearch",
        "source_url": "memory://examples/semantic-retrieval",
        "body": (
            "Semantic retrieval helps users find relevant passages even when "
            "their query uses different words. Postgres stores metadata and "
            "filters while turbovec searches compact document embeddings."
        ),
    },
    {
        "source_id": "example-cloud-deploy",
        "title": "Cloud Deployment Notes",
        "author": "Turbosearch",
        "source_url": "memory://examples/cloud-deploy",
        "body": (
            "A cloud deployment can use Aurora PostgreSQL for durable metadata, "
            "EC2 for the API and vector index, and Emberlane for an "
            "OpenAI-compatible summary model."
        ),
    },
]


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
    text = strip_gutenberg_boilerplate(response.text)
    chunks = chunk_text(text)
    embedder = build_embedder()
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
                    settings.embedding_model,
                    settings.index_dim,
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
                    settings.embedding_model,
                    settings.index_dim,
                    settings.index_version,
                ),
            ).fetchone()
            vector_index.upsert(row["vector_key"], embedding)

    return len(chunks)


def ingest_example_documents() -> dict[str, int]:
    counts = {}
    for document in LOCAL_EXAMPLE_DOCUMENTS:
        counts[document["title"]] = ingest_text(
            source="example",
            source_id=document["source_id"],
            title=document["title"],
            author=document["author"],
            source_url=document["source_url"],
            text=document["body"],
        )
    return counts


def ingest_default_gutenberg() -> dict[str, int]:
    counts = {}
    for book in DEFAULT_BOOKS:
        counts[book.title] = ingest_url(
            book.source_id,
            book.title,
            book.author,
            book.url,
            source="gutenberg",
        )
    return counts
