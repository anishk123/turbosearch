import hashlib
import math
import re
from collections.abc import Sequence
from typing import Any

import numpy as np

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z']+")
DEFAULT_QWEN_MODEL = "Qwen/Qwen3-Embedding-0.6B"


def truncate_and_normalize(values: Sequence[float], dim: int) -> list[float]:
    """Apply Qwen3 MRL truncation and return a unit-length vector."""

    if dim <= 0:
        raise ValueError("dim must be positive")

    vector = np.asarray(values[:dim], dtype=np.float32)
    if vector.size != dim:
        raise ValueError(f"embedding has {vector.size} dimensions, expected at least {dim}")

    norm = float(np.linalg.norm(vector))
    if norm == 0:
        return vector.tolist()
    return (vector / norm).tolist()


class HashEmbeddingProvider:
    """Deterministic local embeddings for smoke tests and offline development."""

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim
        self.embedding_dim = dim
        self.index_dim = dim
        self.model_name = "hash-local"

    def embed(self, text: str) -> list[float]:
        vector = np.zeros(self.dim, dtype=np.float32)
        for token in TOKEN_RE.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "little") % self.dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[bucket] += sign

        norm = float(np.linalg.norm(vector))
        if norm == 0:
            return vector.tolist()
        return (vector / norm).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text)


class QwenEmbeddingProvider:
    """Qwen3 embedding provider with Matryoshka truncation for the vector index."""

    def __init__(
        self,
        model_name: str = DEFAULT_QWEN_MODEL,
        embedding_dim: int = 1024,
        index_dim: int = 256,
        *,
        load_model: bool = True,
        model: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.index_dim = index_dim
        self._model = model
        if load_model and self._model is None:
            self._model = self._load_model()

    def _load_model(self) -> Any:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for Qwen embeddings; "
                "install turbosearch[embeddings] or use EMBEDDING_PROVIDER=hash"
            ) from exc
        return SentenceTransformer(self.model_name)

    @property
    def model(self) -> Any:
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def embed(self, text: str) -> list[float]:
        raw = self.model.encode(text, normalize_embeddings=True)
        return truncate_and_normalize(raw, self.index_dim)

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text)


def vector_literal(values: list[float]) -> str:
    cleaned = []
    for value in values:
        if not math.isfinite(value):
            cleaned.append("0")
        else:
            cleaned.append(f"{value:.7f}")
    return "[" + ",".join(cleaned) + "]"
