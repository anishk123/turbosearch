from turbosearch.db import init_db
from turbosearch.ingest import ingest_directory
from turbosearch.search import search


def main() -> None:
    init_db()
    counts = ingest_directory("examples/local-docs")
    print("Ingested local directory: examples/local-docs")
    for title, count in counts.items():
        print(f"- {title}: {count}")

    expected = {
        "semantic retrieval metadata filters": "search-notes.md",
        "cloud deployment with an OpenAI-compatible model": "cloud-notes.md",
    }
    for query, expected_title in expected.items():
        result = search(query, limit=3)
        print("\nQUERY:", query)
        print("OVERVIEW:", result["overview"])
        for row in result["results"]:
            print(f"- {row['title']} score={row['score']:.4f} chunk={row['chunk_index']}")
        if not result["results"]:
            raise SystemExit(f"No results returned for query: {query}")
        titles = {row["title"] for row in result["results"]}
        if expected_title not in titles:
            raise SystemExit(
                f"Expected {expected_title!r} in results for query {query!r}; got {sorted(titles)}"
            )


if __name__ == "__main__":
    main()
