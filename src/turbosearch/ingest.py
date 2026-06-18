from dataclasses import dataclass

import requests

from turbosearch.chunking import chunk_text, strip_gutenberg_boilerplate
from turbosearch.config import settings
from turbosearch.db import connect
from turbosearch.embeddings import HashEmbeddingProvider, vector_literal


@dataclass(frozen=True)
class GutenbergBook:
    source_id: str
    title: str
    author: str
    url: str


DEFAULT_BOOKS = [
    GutenbergBook(
        source_id="1342",
        title="Pride and Prejudice",
        author="Jane Austen",
        url="https://www.gutenberg.org/cache/epub/1342/pg1342.txt",
    ),
    GutenbergBook(
        source_id="84",
        title="Frankenstein; Or, The Modern Prometheus",
        author="Mary Wollstonecraft Shelley",
        url="https://www.gutenberg.org/cache/epub/84/pg84.txt",
    ),
    GutenbergBook(
        source_id="2701",
        title="Moby-Dick; Or, The Whale",
        author="Herman Melville",
        url="https://www.gutenberg.org/cache/epub/2701/pg2701.txt",
    ),
]


def ingest_url(source_id: str, title: str, author: str | None, url: str) -> int:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = strip_gutenberg_boilerplate(response.text)
    chunks = chunk_text(text)
    embedder = HashEmbeddingProvider(settings.embedding_dim)

    with connect() as conn:
        document = conn.execute(
            """
            INSERT INTO documents (source_id, source_url, title, author)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (source, source_id)
            DO UPDATE SET source_url = EXCLUDED.source_url,
                          title = EXCLUDED.title,
                          author = EXCLUDED.author
            RETURNING id
            """,
            (source_id, url, title, author),
        ).fetchone()
        document_id = document["id"]
        conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))

        for index, chunk in enumerate(chunks):
            embedding = vector_literal(embedder.embed(chunk))
            conn.execute(
                """
                INSERT INTO chunks (document_id, chunk_index, body, token_count, embedding)
                VALUES (%s, %s, %s, %s, %s::vector)
                """,
                (document_id, index, chunk, len(chunk.split()), embedding),
            )

    return len(chunks)


def ingest_default_gutenberg() -> dict[str, int]:
    counts = {}
    for book in DEFAULT_BOOKS:
        counts[book.title] = ingest_url(book.source_id, book.title, book.author, book.url)
    return counts

