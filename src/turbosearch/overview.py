from typing import Any

import requests


def build_overview(query: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"No strong matches found for {query!r}."

    seen_titles = []
    for row in rows:
        title = row["title"]
        if title not in seen_titles:
            seen_titles.append(title)

    best = rows[0]
    snippet = best["body"].replace("\n", " ").strip()
    if len(snippet) > 360:
        snippet = snippet[:357].rsplit(" ", 1)[0] + "..."

    titles = ", ".join(seen_titles[:3])
    return (
        f"Top matches for {query!r} come from {titles}. "
        f"The strongest passage is from {best['title']} and centers on: {snippet}"
    )


class ExtractiveSummarizer:
    def summarize(self, query: str, rows: list[dict[str, Any]]) -> str:
        return build_overview(query, rows)


class OpenAICompatibleSummarizer:
    """Small OpenAI-compatible chat-completions summarizer."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        post=requests.post,
        timeout: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.post = post
        self.timeout = timeout

    def summarize(self, query: str, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return build_overview(query, rows)

        passages = []
        for index, row in enumerate(rows[:8], start=1):
            title = row.get("title", "Untitled")
            author = row.get("author") or "Unknown author"
            source_url = row.get("source_url", "")
            body = str(row.get("body", "")).replace("\n", " ").strip()
            passages.append(f"[{index}] {title} by {author} ({source_url})\n{body}")

        response = self.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Write a concise, grounded search overview. "
                            "Cite passage numbers when making claims."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Query: {query}\n\n"
                            "Relevant passages:\n\n" + "\n\n".join(passages)
                        ),
                    },
                ],
                "temperature": 0.2,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
