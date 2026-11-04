CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS guests (
  owner char(64) PRIMARY KEY,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL DEFAULT now() + interval '24 hours'
);

CREATE TABLE IF NOT EXISTS documents (
  id uuid PRIMARY KEY,
  owner char(64) NOT NULL REFERENCES guests(owner) ON DELETE CASCADE,
  name text NOT NULL CHECK (length(name) BETWEEN 1 AND 180),
  media_type text NOT NULL,
  byte_size integer NOT NULL CHECK (byte_size BETWEEN 1 AND 3145728),
  chunk_count integer NOT NULL CHECK (chunk_count BETWEEN 1 AND 120),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS documents_owner ON documents(owner, created_at);

CREATE TABLE IF NOT EXISTS chunks (
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  ordinal integer NOT NULL,
  page integer NOT NULL CHECK (page > 0),
  content text NOT NULL CHECK (length(content) BETWEEN 1 AND 1600),
  embedding vector(768) NOT NULL,
  PRIMARY KEY (document_id, ordinal)
);

CREATE TABLE IF NOT EXISTS answers (
  id uuid PRIMARY KEY,
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  question text NOT NULL CHECK (length(question) BETWEEN 1 AND 1200),
  answer text NOT NULL,
  citations jsonb NOT NULL,
  grounded boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS answers_document ON answers(document_id, created_at);

CREATE TABLE IF NOT EXISTS quota_buckets (
  bucket text NOT NULL,
  day date NOT NULL DEFAULT CURRENT_DATE,
  used integer NOT NULL CHECK (used >= 0),
  PRIMARY KEY (bucket, day)
);
