from turbosearch.chunking import chunk_text


def test_chunk_text_splits_long_text_with_overlap() -> None:
    text = " ".join(f"word{i}" for i in range(80))

    chunks = chunk_text(text, max_words=35, overlap_words=10)

    assert len(chunks) == 3
    assert chunks[0].startswith("word0 word1")
    assert chunks[1].startswith("word25 word26")
    assert "word25" in chunks[0]
    assert "word25" in chunks[1]
    assert chunks[-1].endswith("word78 word79")


def test_chunk_text_returns_empty_list_for_blank_text() -> None:
    assert chunk_text("   ") == []
