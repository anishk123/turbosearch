import sys
from types import SimpleNamespace

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

        def upsert(self, key: int, embedding: list[float]) -> None:
            self.vectors[key] = embedding

        def search(self, query_embedding: list[float], allowlist: list[int], limit: int):
            return [(key, 1.0) for key in allowlist if key in self.vectors][:limit]

    monkeypatch.setitem(sys.modules, "turbovec", SimpleNamespace(Index=FakeIndex))
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
