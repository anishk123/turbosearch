import re

GUTENBERG_START_RE = re.compile(r"\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*?\*\*\*", re.I)
GUTENBERG_END_RE = re.compile(r"\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*?\*\*\*", re.I)


def strip_gutenberg_boilerplate(text: str) -> str:
    start = GUTENBERG_START_RE.search(text)
    end = GUTENBERG_END_RE.search(text)
    if start and end and start.end() < end.start():
        return text[start.end() : end.start()].strip()
    return text.strip()


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

