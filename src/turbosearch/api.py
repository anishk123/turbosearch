from fastapi import FastAPI, Query

from turbosearch.search import search

app = FastAPI(title="turbosearch", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search")
def search_endpoint(q: str = Query(..., min_length=1), limit: int = Query(8, ge=1, le=25)):
    return search(q, limit)

