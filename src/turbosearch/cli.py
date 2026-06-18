import json

import typer
import uvicorn

from turbosearch.db import init_db
from turbosearch.ingest import (
    ingest_directory,
    ingest_url as ingest_one_url,
)
from turbosearch.search import search as run_search

app = typer.Typer(help="Hybrid search for document collections.")


@app.command("init-db")
def init_db_command() -> None:
    init_db()
    typer.echo("Database initialized.")


@app.command("ingest-dir")
def ingest_dir_command(path: str) -> None:
    counts = ingest_directory(path)
    typer.echo(json.dumps(counts, indent=2))


@app.command("ingest-url")
def ingest_url_command(
    url: str,
    title: str = typer.Option(...),
    author: str = typer.Option(""),
    source_id: str = typer.Option("manual"),
    source: str = typer.Option("url"),
) -> None:
    count = ingest_one_url(
        source_id=source_id,
        title=title,
        author=author,
        url=url,
        source=source,
    )
    typer.echo(f"Ingested {count} chunks from {title}.")


@app.command("search")
def search_command(query: str, limit: int = 8) -> None:
    typer.echo(json.dumps(run_search(query, limit), indent=2, default=str))


@app.command("serve")
def serve_command(host: str = "127.0.0.1", port: int = 8000) -> None:
    uvicorn.run("turbosearch.api:app", host=host, port=port, reload=False)
