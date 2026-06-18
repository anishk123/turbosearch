from turbosearch.db import init_db
from turbosearch.ingest import ingest_default_gutenberg
from turbosearch.search import search


def main() -> None:
    init_db()
    counts = ingest_default_gutenberg()
    print("Ingested chunks:")
    for title, count in counts.items():
        print(f"- {title}: {count}")

    for query in ["social class and marriage", "a created monster seeks sympathy", "a whale and obsession"]:
        result = search(query, limit=5)
        print("\nQUERY:", query)
        print("OVERVIEW:", result["overview"])
        for row in result["results"][:3]:
            print(f"- {row['title']} score={row['score']:.4f} chunk={row['chunk_index']}")


if __name__ == "__main__":
    main()

