import inspect

from turbosearch.search import PostgresMetadataStore


def test_metadata_candidate_selection_is_not_lexically_gated() -> None:
    source = inspect.getsource(PostgresMetadataStore.candidate_vector_keys)

    assert "ts_rank" not in source
    assert "plainto_tsquery" not in source
