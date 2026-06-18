import sys
from types import SimpleNamespace

import numpy as np
import pytest

from turbosearch.search import SimpleVectorIndex, TurbovecVectorIndex


def test_simple_vector_index_persists_across_instances(tmp_path) -> None:
    index_path = tmp_path / "vectors.json"
    first = SimpleVectorIndex(index_path=index_path)
    first.upsert(10, [1.0, 0.0])

    second = SimpleVectorIndex(index_path=index_path)

    assert second.search([1.0, 0.0], allowlist=[10], limit=1) == [
        {"vector_key": 10, "score": 1.0}
    ]


def test_turbovec_adapter_rehydrates_vectors_for_new_process(tmp_path, monkeypatch) -> None:
    class FakeIndex:
        def __init__(self, dim: int) -> None:
            self.vectors = {}

        def add_with_ids(self, vectors, ids) -> None:
            for vector, vector_id in zip(vectors, ids, strict=False):
                self.vectors[int(vector_id)] = np.asarray(vector, dtype=np.float32)

        def prepare(self) -> None:
            return None

        def contains(self, vector_id: int) -> bool:
            return int(vector_id) in self.vectors

        def remove(self, vector_id: int) -> None:
            self.vectors.pop(int(vector_id), None)

        def search(self, queries, k: int, *, allowlist=None):
            query = np.asarray(queries[0], dtype=np.float32)
            scored = []
            for vector_id in allowlist:
                vector = self.vectors.get(int(vector_id))
                if vector is not None:
                    scored.append((float(np.dot(query, vector)), int(vector_id)))
            scored.sort(reverse=True)
            scores = np.asarray([[score for score, _ in scored[:k]]], dtype=np.float32)
            ids = np.asarray([[vector_id for _, vector_id in scored[:k]]], dtype=np.uint64)
            return scores, ids

    monkeypatch.setitem(sys.modules, "turbovec", SimpleNamespace(IdMapIndex=FakeIndex))
    index_path = tmp_path / "turbovec-vectors.json"

    first = TurbovecVectorIndex(dim=2, index_path=index_path)
    first.upsert(42, [1.0, 0.0])

    second = TurbovecVectorIndex(dim=2, index_path=index_path)

    assert second.search([1.0, 0.0], allowlist=[42], limit=1) == [
        {"vector_key": 42, "score": 1.0}
    ]


def test_turbovec_adapter_reports_missing_package(tmp_path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "turbovec", None)

    with pytest.raises(RuntimeError, match="turbovec is required"):
        TurbovecVectorIndex(dim=2, index_path=tmp_path / "vectors.json")
