from turbosearch.embeddings import HashEmbeddingProvider
from turbosearch.ingest import embedding_metadata


def test_embedding_metadata_comes_from_active_embedder() -> None:
    embedder = HashEmbeddingProvider(dim=128)

    assert embedding_metadata(embedder) == ("hash-local", 128)

