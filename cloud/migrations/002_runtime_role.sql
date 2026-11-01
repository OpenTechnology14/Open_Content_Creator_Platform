-- Run as the bootstrap/maintenance role; the API must never use that role.
-- Idempotent permission upgrade for new and existing relay databases.
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'relay_app') THEN
        CREATE ROLE relay_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END $$;
ALTER ROLE relay_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOINHERIT;
GRANT USAGE ON SCHEMA public TO relay_app;
GRANT SELECT, INSERT, UPDATE ON tenants TO relay_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON
    devices, sync_data, metrics, api_keys, team_members, notification_log TO relay_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO relay_app;
-- relay_app receives no DDL, table ownership, TRUNCATE, role membership or BYPASSRLS.
-- Set its password separately through the init script/maintenance credential flow.
