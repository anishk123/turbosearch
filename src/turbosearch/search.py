from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from turbosearch.config import settings
from turbosearch.db import connect
from turbosearch.embeddings import HashEmbeddingProvider, QwenEmbeddingProvider
from turbosearch.overview import ExtractiveSummarizer, OpenAICompatibleSummarizer


class MetadataStore(Protocol):
    def candidate_vector_keys(self, query: str, limit: int | None) -> list[int]: ...

    def chunks_by_vector_keys(self, vector_keys: list[int]) -> list[dict[str, Any]]: ...


class VectorIndex(Protocol):
    def search(
        self,
        query_embedding: list[float],
        allowlist: list[int],
        limit: int,
    ) -> list[dict[str, Any]]: ...


class Embedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...


class Summarizer(Protocol):
    def summarize(self, query: str, rows: list[dict[str, Any]]) -> str: ...


class PostgresMetadataStore:
    """Postgres-backed metadata candidate retrieval."""

    def candidate_vector_keys(self, query: str, limit: int | None) -> list[int]:
        del query
        limit_clause = "LIMIT %s" if limit is not None else ""
        params = (limit,) if limit is not None else ()
        with connect() as conn:
            rows = conn.execute(
                f"""
                SELECT c.vector_key
                FROM chunks c
                ORDER BY c.id ASC
                {limit_clause}
                """,
                params,
            ).fetchall()

            return [int(row["vector_key"]) for row in rows]

    def chunks_by_vector_keys(self, vector_keys: list[int]) -> list[dict[str, Any]]:
        if not vector_keys:
            return []

        with connect() as conn:
            rows = conn.execute(
                """
                SELECT
                  c.id AS chunk_id,
                  c.vector_key,
                  d.id AS document_id,
                  d.title,
                  d.author,
                  d.source_url,
                  c.chunk_index,
                  c.heading,
                  c.body,
                  c.token_count,
                  c.embedding_model,
                  c.embedding_dim,
                  c.index_version
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.vector_key = ANY(%s)
                """,
                (vector_keys,),
            ).fetchall()

        rows_by_key = {int(row["vector_key"]): dict(row) for row in rows}
        return [rows_by_key[key] for key in vector_keys if key in rows_by_key]


class PersistedVectorStore:
    def __init__(self, index_path: str | Path | None = None) -> None:
        self.index_path = Path(index_path or settings.vector_index_path)
        self._vectors: dict[int, np.ndarray] = {}
        self._load()

    def _load(self) -> None:
        if not self.index_path.exists():
            return
        data = json.loads(self.index_path.read_text())
        self._vectors = {
            int(key): np.asarray(value, dtype=np.float32) for key, value in data.items()
        }

    def _save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        data = {str(key): vector.tolist() for key, vector in self._vectors.items()}
        self.index_path.write_text(json.dumps(data))

    def upsert(self, vector_key: int, embedding: Iterable[float]) -> np.ndarray:
        vector = np.asarray(list(embedding), dtype=np.float32)
        norm = float(np.linalg.norm(vector))
        if norm:
            vector = vector / norm
        self._vectors[int(vector_key)] = vector
        self._save()
        return vector

    def delete(self, vector_keys: Iterable[int]) -> None:
        for key in vector_keys:
            self._vectors.pop(int(key), None)
        self._save()

    def items(self) -> Iterable[tuple[int, np.ndarray]]:
        self._load()
        return self._vectors.items()

    def vector_for(self, vector_key: int) -> np.ndarray | None:
        self._load()
        return self._vectors.get(int(vector_key))


class SimpleVectorIndex:
    """Deterministic local vector index for tests and smoke demos."""

    def __init__(self, index_path: str | Path | None = None) -> None:
        self._store = PersistedVectorStore(index_path)

    def upsert(self, vector_key: int, embedding: Iterable[float]) -> None:
        self._store.upsert(vector_key, embedding)

    def delete(self, vector_keys: Iterable[int]) -> None:
        self._store.delete(vector_keys)

    def search(
        self,
        query_embedding: list[float],
        allowlist: list[int],
        limit: int,
    ) -> list[dict[str, Any]]:
        query = np.asarray(query_embedding, dtype=np.float32)
        norm = float(np.linalg.norm(query))
        if norm:
            query = query / norm

        scored = []
        for vector_key in allowlist:
            vector = self._store.vector_for(int(vector_key))
            if vector is None:
                continue
            score = float(np.dot(query, vector))
            scored.append({"vector_key": int(vector_key), "score": score})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]


class TurbovecVectorIndex:
    """Adapter for turbovec, with API-shape tolerance while the package evolves."""

    def __init__(self, dim: int, index_path: str | Path | None = None) -> None:
        try:
            import turbovec
        except ImportError as exc:
            raise RuntimeError(
                "turbovec is required for VECTOR_BACKEND=turbovec. "
                "Install turbosearch[vector] or set VECTOR_BACKEND=simple for tests/smoke demos."
            ) from exc

        self._store = PersistedVectorStore(index_path)
        self._index = turbovec.IdMapIndex(dim=dim)
        for vector_key, vector in self._store.items():
            self._upsert_index(vector_key, vector)
        self._index.prepare()

    def _upsert_index(self, vector_key: int, embedding: Iterable[float]) -> None:
        vectors = np.asarray([list(embedding)], dtype=np.float32)
        ids = np.asarray([int(vector_key)], dtype=np.uint64)
        self._index.add_with_ids(vectors, ids)
        self._index.prepare()

    def upsert(self, vector_key: int, embedding: Iterable[float]) -> None:
        vector = self._store.upsert(vector_key, embedding)
        self._upsert_index(vector_key, vector)

    def delete(self, vector_keys: Iterable[int]) -> None:
        vector_keys = [int(key) for key in vector_keys]
        self._store.delete(vector_keys)
        for vector_key in vector_keys:
            if hasattr(self._index, "contains") and self._index.contains(vector_key):
                self._index.remove(vector_key)
        self._index.prepare()

    def search(
        self,
        query_embedding: list[float],
        allowlist: list[int],
        limit: int,
    ) -> list[dict[str, Any]]:
        query = np.asarray([query_embedding], dtype=np.float32)
        candidates = np.asarray(allowlist, dtype=np.uint64)
        scores, ids = self._index.search(query, limit, allowlist=candidates)
        results = []
        for score, vector_key in zip(scores[0], ids[0], strict=False):
            results.append({"vector_key": int(vector_key), "score": float(score)})
        return results


_VECTOR_INDEX: VectorIndex | None = None


def get_vector_index() -> VectorIndex:
    global _VECTOR_INDEX
    if _VECTOR_INDEX is not None:
        return _VECTOR_INDEX
    if settings.vector_backend.lower() == "simple":
        _VECTOR_INDEX = SimpleVectorIndex(settings.vector_index_path)
    elif settings.vector_backend.lower() == "turbovec":
        _VECTOR_INDEX = TurbovecVectorIndex(settings.index_dim, settings.vector_index_path)
    else:
        raise RuntimeError(
            f"Unsupported VECTOR_BACKEND={settings.vector_backend!r}; expected 'turbovec' or 'simple'."
        )
    return _VECTOR_INDEX


def build_embedder() -> Embedder:
    if settings.embedding_provider.lower() == "qwen":
        return QwenEmbeddingProvider(
            model_name=settings.embedding_model,
            embedding_dim=settings.embedding_dim,
            index_dim=settings.index_dim,
        )
    return HashEmbeddingProvider(settings.index_dim)


def build_summarizer() -> Summarizer:
    if settings.overview_mode.lower() in {"llm", "openai", "openai-compatible"}:
        return OpenAICompatibleSummarizer(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    return ExtractiveSummarizer()


class SearchPipeline:
    def __init__(
        self,
        *,
        metadata_store: MetadataStore,
        vector_index: VectorIndex,
        embedder: Embedder,
        summarizer: Summarizer,
    ) -> None:
        self.metadata_store = metadata_store
        self.vector_index = vector_index
        self.embedder = embedder
        self.summarizer = summarizer

    def search(
        self,
        query: str,
        *,
        candidate_limit: int | None = None,
        result_limit: int = 8,
    ) -> dict[str, Any]:
        candidate_keys = self.metadata_store.candidate_vector_keys(query, candidate_limit)
        query_embedding = self.embedder.embed_query(query)
        vector_hits = self.vector_index.search(query_embedding, candidate_keys, result_limit)
        ordered_keys = [int(hit["vector_key"]) for hit in vector_hits]
        rows = self.metadata_store.chunks_by_vector_keys(ordered_keys)

        scores_by_key = {int(hit["vector_key"]): hit.get("score") for hit in vector_hits}
        for row in rows:
            row["score"] = scores_by_key.get(int(row["vector_key"]), 0.0)

        return {
            "query": query,
            "overview": self.summarizer.summarize(query, rows),
            "results": rows,
        }


def build_pipeline() -> SearchPipeline:
    return SearchPipeline(
        metadata_store=PostgresMetadataStore(),
        vector_index=get_vector_index(),
        embedder=build_embedder(),
        summarizer=build_summarizer(),
    )


def search(query: str, limit: int = 8) -> dict[str, Any]:
    pipeline = build_pipeline()
    return pipeline.search(query, candidate_limit=None, result_limit=limit)
