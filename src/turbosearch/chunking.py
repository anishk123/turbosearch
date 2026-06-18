import re


def chunk_text(text: str, max_words: int = 220, overlap_words: int = 40) -> list[str]:
    words = re.findall(r"\S+", text)
    if not words:
        return []

    chunks = []
    step = max(1, max_words - overlap_words)
    for start in range(0, len(words), step):
        piece = words[start : start + max_words]
        if len(piece) < 30 and chunks:
            chunks[-1] = chunks[-1] + " " + " ".join(piece)
        else:
            chunks.append(" ".join(piece))
    return chunks
