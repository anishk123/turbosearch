CREATE TABLE IF NOT EXISTS documents (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL DEFAULT 'user',
  source_id TEXT NOT NULL,
  source_url TEXT NOT NULL,
  title TEXT NOT NULL,
  author TEXT,
  language TEXT NOT NULL DEFAULT 'en',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source, source_id)
);

CREATE TABLE IF NOT EXISTS chunks (
  id BIGSERIAL PRIMARY KEY,
  document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  vector_key BIGSERIAL UNIQUE,
  chunk_index INTEGER NOT NULL,
  heading TEXT,
  body TEXT NOT NULL,
  token_count INTEGER NOT NULL,
  embedding_model TEXT NOT NULL DEFAULT 'Qwen/Qwen3-Embedding-0.6B',
  embedding_dim INTEGER NOT NULL DEFAULT 1024,
  index_version INTEGER NOT NULL DEFAULT 1,
  search_vector TSVECTOR GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(heading, '')), 'A') ||
    setweight(to_tsvector('english', body), 'B')
  ) STORED,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS documents_source_idx ON documents (source, source_id);
CREATE INDEX IF NOT EXISTS chunks_document_idx ON chunks (document_id);
CREATE INDEX IF NOT EXISTS chunks_vector_key_idx ON chunks (vector_key);
CREATE INDEX IF NOT EXISTS chunks_embedding_metadata_idx
  ON chunks (embedding_model, embedding_dim, index_version);
CREATE INDEX IF NOT EXISTS chunks_search_vector_idx ON chunks USING gin (search_vector);
