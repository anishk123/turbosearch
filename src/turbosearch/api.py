from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

from turbosearch.config import settings
from turbosearch.ingest import ingest_s3_bucket, ingest_text, ingest_url
from turbosearch.search import search

app = FastAPI(title="turbosearch", version="0.1.0")


class S3IngestRequest(BaseModel):
    bucket: str | None = Field(None, description="S3 bucket name. Defaults to DOCUMENT_BUCKET.")
    prefix: str = Field("", description="Optional S3 prefix containing .txt/.md documents.")


class TextIngestRequest(BaseModel):
    title: str
    text: str
    source_id: str | None = None
    source: str = "api-text"
    author: str | None = None


class UrlIngestRequest(BaseModel):
    url: str
    title: str
    source_id: str | None = None
    source: str = "url"
    author: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search")
def search_endpoint(q: str = Query(..., min_length=1), limit: int = Query(8, ge=1, le=25)):
    return search(q, limit)


@app.post("/ingest/s3")
def ingest_s3_endpoint(request: S3IngestRequest):
    bucket = request.bucket or settings.document_bucket
    if not bucket:
        return {"error": "bucket is required when DOCUMENT_BUCKET is not configured"}
    counts = ingest_s3_bucket(bucket, request.prefix)
    return {"bucket": bucket, "prefix": request.prefix, "documents": counts}


@app.post("/ingest/text")
def ingest_text_endpoint(request: TextIngestRequest):
    source_id = request.source_id or request.title
    count = ingest_text(
        source=request.source,
        source_id=source_id,
        title=request.title,
        author=request.author,
        source_url=f"api://text/{source_id}",
        text=request.text,
    )
    return {"title": request.title, "chunks": count}


@app.post("/ingest/url")
def ingest_url_endpoint(request: UrlIngestRequest):
    source_id = request.source_id or request.url
    count = ingest_url(
        source_id=source_id,
        title=request.title,
        author=request.author,
        url=request.url,
        source=request.source,
    )
    return {"title": request.title, "url": request.url, "chunks": count}
