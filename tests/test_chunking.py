from turbosearch.chunking import chunk_text, strip_gutenberg_boilerplate


def test_strip_gutenberg_boilerplate() -> None:
    text = """
Header
*** START OF THE PROJECT GUTENBERG EBOOK TEST ***
Real text
*** END OF THE PROJECT GUTENBERG EBOOK TEST ***
Footer
"""
    assert strip_gutenberg_boilerplate(text) == "Real text"


def test_chunk_text_overlaps() -> None:
    text = " ".join(f"word{i}" for i in range(100))
    chunks = chunk_text(text, max_words=30, overlap_words=10)
    assert len(chunks) > 1
    assert "word20" in chunks[0]
    assert "word20" in chunks[1]

