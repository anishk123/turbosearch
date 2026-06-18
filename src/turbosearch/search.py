from typing import Any

from turbosearch.config import settings
from turbosearch.db import connect
from turbosearch.embeddings import HashEmbeddingProvider, vector_literal
from turbosearch.overview import build_overview


def search(query: str, limit: int = 8) -> dict[str, Any]:
    embedder = HashEmbeddingProvider(settings.embedding_dim)
    query_vector = vector_literal(embedder.embed(query))

    with connect() as conn:
        rows = conn.execute(
            """
            WITH q AS (
              SELECT plainto_tsquery('english', %s) AS tsq, %s::vector AS embedding
            )
            SELECT
              c.id AS chunk_id,
              d.id AS document_id,
              d.title,
              d.author,
              d.source_url,
              c.chunk_index,
              c.body,
              ts_rank(c.search_vector, q.tsq) AS lexical_score,
              1 - (c.embedding <=> q.embedding) AS vector_score,
              (
                0.55 * ts_rank(c.search_vector, q.tsq) +
                0.45 * (1 - (c.embedding <=> q.embedding))
              ) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            CROSS JOIN q
            WHERE c.search_vector @@ q.tsq
               OR c.embedding <=> q.embedding < 0.95
            ORDER BY score DESC
            LIMIT %s
            """,
            (query, query_vector, limit),
        ).fetchall()

    return {
        "query": query,
        "overview": build_overview(query, rows),
        "results": rows,
    }

