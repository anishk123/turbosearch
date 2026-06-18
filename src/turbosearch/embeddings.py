import hashlib
import math
import re

import numpy as np

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z']+")


class HashEmbeddingProvider:
    """Deterministic local embeddings for smoke tests and offline development."""

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

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


def vector_literal(values: list[float]) -> str:
    cleaned = []
    for value in values:
        if not math.isfinite(value):
            cleaned.append("0")
        else:
            cleaned.append(f"{value:.7f}")
    return "[" + ",".join(cleaned) + "]"

