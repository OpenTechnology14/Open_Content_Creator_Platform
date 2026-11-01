-- 0001_init.sql
-- Initial schema for Open Content Creator Platform.
-- Apply with: psql "$DATABASE_URL" -f 0001_init.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ─── creators ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS creators (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handle       TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    metadata     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── streams ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS streams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id  UUID REFERENCES creators(id) ON DELETE SET NULL,
    title       TEXT NOT NULL,
    -- Multi-platform streaming (README "Multi-platform streaming"): a stream
    -- can go out to several platforms at once, so this is an array, matching
    -- backend-api/app/routers/streams.py's `platforms: list[str]` on both the
    -- INSERT and the SELECT it reads back. Was `platform TEXT NOT NULL`
    -- (singular) here — router code and schema had never agreed, caught by
    -- POST /streams's first real database call (P-016's acceptance harness,
    -- the first thing to ever exercise this table).
    platforms   TEXT[] NOT NULL DEFAULT '{}',
    status      TEXT NOT NULL DEFAULT 'scheduled',     -- scheduled|live|ended|errored
    started_at  TIMESTAMPTZ,
    ended_at    TIMESTAMPTZ,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_streams_status     ON streams(status);
CREATE INDEX IF NOT EXISTS idx_streams_started_at ON streams(started_at DESC);

-- ─── events ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    id          UUID PRIMARY KEY,
    stream_id   UUID REFERENCES streams(id) ON DELETE CASCADE,
    source      TEXT NOT NULL,                         -- golf-tracer, obs, agent, ...
    kind        TEXT NOT NULL,
    data        JSONB NOT NULL DEFAULT '{}'::jsonb,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_events_received_at ON events(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_source_kind ON events(source, kind);
CREATE INDEX IF NOT EXISTS idx_events_stream      ON events(stream_id, received_at DESC);

-- ─── assets ────────────────────────────────────────────────────────────
-- Pointer table for things stored in MinIO / DO Spaces.
CREATE TABLE IF NOT EXISTS assets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id   UUID REFERENCES streams(id) ON DELETE SET NULL,
    kind        TEXT NOT NULL,                         -- recording|comfyui-output|thumbnail|other
    bucket      TEXT NOT NULL,
    object_key  TEXT NOT NULL,
    size_bytes  BIGINT,
    mime_type   TEXT,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (bucket, object_key)
);
CREATE INDEX IF NOT EXISTS idx_assets_stream ON assets(stream_id);
CREATE INDEX IF NOT EXISTS idx_assets_kind   ON assets(kind);

COMMIT;
