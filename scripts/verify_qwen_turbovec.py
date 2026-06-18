from turbosearch.db import connect
from turbosearch.search import get_vector_index


def main() -> None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT embedding_model, embedding_dim, count(*) AS chunks
            FROM chunks
            GROUP BY embedding_model, embedding_dim
            """
        ).fetchone()

    assert row is not None, "expected indexed chunks"
    assert row["embedding_model"] == "Qwen/Qwen3-Embedding-0.6B"
    assert int(row["embedding_dim"]) == 256
    assert type(get_vector_index()).__name__ == "TurbovecVectorIndex"
    print(f"Qwen + turbovec verified: {row['chunks']} chunks indexed")


if __name__ == "__main__":
    main()
