from turbosearch.search import SearchPipeline


class FakeMetadataStore:
    def candidate_vector_keys(self, query: str, limit: int) -> list[int]:
        assert query == "whale obsession"
        assert limit == 50
        return [101, 102, 103]

    def chunks_by_vector_keys(self, vector_keys: list[int]) -> list[dict]:
        return [
            {
                "vector_key": key,
                "title": "Moby-Dick",
                "author": "Herman Melville",
                "body": f"passage {key}",
                "source_url": "https://www.gutenberg.org/ebooks/2701",
            }
            for key in vector_keys
        ]


class FakeVectorIndex:
    def search(self, query_embedding: list[float], allowlist: list[int], limit: int) -> list[dict]:
        assert query_embedding == [1.0, 0.0]
        assert allowlist == [101, 102, 103]
        assert limit == 5
        return [{"vector_key": 102, "score": 0.99}, {"vector_key": 101, "score": 0.91}]


class FakeEmbedder:
    def embed_query(self, text: str) -> list[float]:
        assert text == "whale obsession"
        return [1.0, 0.0]


class FakeSummarizer:
    def summarize(self, query: str, rows: list[dict]) -> str:
        assert query == "whale obsession"
        assert [row["vector_key"] for row in rows] == [102, 101]
        return "Moby-Dick passages connect obsession to the whale."


def test_pipeline_filters_in_postgres_then_searches_turbovec_allowlist() -> None:
    pipeline = SearchPipeline(
        metadata_store=FakeMetadataStore(),
        vector_index=FakeVectorIndex(),
        embedder=FakeEmbedder(),
        summarizer=FakeSummarizer(),
    )

    result = pipeline.search("whale obsession", candidate_limit=50, result_limit=5)

    assert result["overview"] == "Moby-Dick passages connect obsession to the whale."
    assert [row["vector_key"] for row in result["results"]] == [102, 101]
    assert result["results"][0]["score"] == 0.99

