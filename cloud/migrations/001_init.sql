-- Migration 001: Initial schema for Cloud Relay
--
-- Multi-tenant architecture with row-level security.
-- Every table has a tenant_id column. RLS policies ensure
-- tenants can only see their own data.
--
-- Run with: psql -U relay -d relay -f 001_init.sql

-- Enable RLS helper: app.tenant_id session variable
-- Set by the application before each query:
--   SET app.tenant_id = 'tenant-uuid-here';

-- ============================================================
-- TENANTS
-- ============================================================

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    tier TEXT NOT NULL DEFAULT 'free'
        CHECK (tier IN ('free', 'connect', 'pro', 'team')),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- No RLS on tenants — accessed via direct lookup, not session var

-- ============================================================
-- DEVICES
-- ============================================================

CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Unknown Device',
    product TEXT NOT NULL DEFAULT 'stream_extend'
        CHECK (product IN ('stream_extend', 'creator_extend')),
    platform TEXT NOT NULL DEFAULT 'unknown'
        CHECK (platform IN ('macos', 'windows', 'linux', 'ios', 'android', 'unknown')),
    push_token TEXT,
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_devices_tenant ON devices(tenant_id);

ALTER TABLE devices ENABLE ROW LEVEL SECURITY;

CREATE POLICY devices_tenant_isolation ON devices
    USING (tenant_id::text = current_setting('app.tenant_id', true));

-- ============================================================
-- SYNC DATA
-- ============================================================

CREATE TABLE IF NOT EXISTS sync_data (
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value JSONB NOT NULL DEFAULT '{}',
    version BIGINT NOT NULL DEFAULT 1,
    device_id TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, key)
);

CREATE INDEX idx_sync_tenant_key ON sync_data(tenant_id, key);

ALTER TABLE sync_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY sync_tenant_isolation ON sync_data
    USING (tenant_id::text = current_setting('app.tenant_id', true));

-- ============================================================
-- METRICS
-- ============================================================

CREATE TABLE IF NOT EXISTS metrics (
    id BIGSERIAL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    labels TEXT DEFAULT '{}',
    PRIMARY KEY (id)
);

-- Partition-friendly index for time-range queries
CREATE INDEX idx_metrics_tenant_name_time
    ON metrics(tenant_id, name, timestamp DESC);

-- Prevent duplicate metric points
CREATE UNIQUE INDEX idx_metrics_dedup
    ON metrics(tenant_id, name, timestamp);

ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY metrics_tenant_isolation ON metrics
    USING (tenant_id::text = current_setting('app.tenant_id', true));

-- ============================================================
-- API KEYS (for self-hosted relay auth)
-- ============================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL,  -- bcrypt hash of the key
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY api_keys_tenant_isolation ON api_keys
    USING (tenant_id::text = current_setting('app.tenant_id', true));

-- ============================================================
-- TEAM MEMBERSHIPS (Team tier)
-- ============================================================

CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member'
        CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    invited_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_team_tenant ON team_members(tenant_id);
CREATE UNIQUE INDEX idx_team_unique_member ON team_members(tenant_id, user_email);

ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY team_tenant_isolation ON team_members
    USING (tenant_id::text = current_setting('app.tenant_id', true));

-- ============================================================
-- NOTIFICATION LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS notification_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    device_id TEXT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'general',
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_notif_tenant ON notification_log(tenant_id, sent_at DESC);

ALTER TABLE notification_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY notif_tenant_isolation ON notification_log
    USING (tenant_id::text = current_setting('app.tenant_id', true));

-- ============================================================
-- HELPER: auto-update updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
