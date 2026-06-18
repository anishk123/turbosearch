from pathlib import Path

from turbosearch.ingest import iter_directory_documents


def test_iter_directory_documents_reads_text_files(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("Alpha document about semantic retrieval.")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "beta.md").write_text("Beta document about cloud deployment.")
    (nested / "ignore.pdf").write_bytes(b"%PDF")

    documents = list(iter_directory_documents(tmp_path))

    assert [doc["title"] for doc in documents] == ["alpha.txt", "beta.md"]
    assert documents[0]["source"] == "directory"
    assert documents[0]["source_url"].startswith("file://")
    assert "semantic retrieval" in documents[0]["text"]

