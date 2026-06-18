import pytest

from turbosearch.embeddings import QwenEmbeddingProvider, truncate_and_normalize


def test_truncate_and_normalize_for_mrl_dimension() -> None:
    values = [3.0, 4.0, 10.0, 11.0]

    actual = truncate_and_normalize(values, 2)

    assert actual == pytest.approx([0.6, 0.8])


def test_qwen_provider_defaults_to_qwen3_06b() -> None:
    provider = QwenEmbeddingProvider(load_model=False)

    assert provider.model_name == "Qwen/Qwen3-Embedding-0.6B"
    assert provider.embedding_dim == 1024
    assert provider.index_dim == 256

