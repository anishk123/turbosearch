from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from turbosearch.config import settings


def connect() -> psycopg.Connection:
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def init_db() -> None:
    schema_path = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"
    with connect() as conn:
        conn.execute(schema_path.read_text())


@contextmanager
def transaction() -> Iterator[psycopg.Connection]:
    with connect() as conn:
        with conn.transaction():
            yield conn
