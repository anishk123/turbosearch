from typing import Any


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

