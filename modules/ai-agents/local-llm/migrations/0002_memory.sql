-- 0002_memory.sql
-- pgvector-backed agent memory. 768-dim matches nomic-embed-text v1.5.
-- If you switch embedding models, drop and recreate with the right dim.

BEGIN;

CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE IF NOT EXISTS agent_memories (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona    TEXT NOT NULL,
    role       TEXT NOT NULL,                -- user|assistant|system|tool
    content    TEXT NOT NULL,
    embedding  vector(768),
    metadata   JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_memories_persona
    ON agent_memories(persona, created_at DESC);

-- HNSW is preferred on PG16 + pgvector >=0.5; falls back to IVFFlat below if
-- the extension version is too old.
DO $$
BEGIN
    BEGIN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_agent_memories_embed_hnsw
                 ON agent_memories USING hnsw (embedding vector_cosine_ops)';
    EXCEPTION WHEN others THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_agent_memories_embed_ivf
                 ON agent_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)';
    END;
END $$;

COMMIT;
