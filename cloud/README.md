# Optional cloud relay

The relay is optional. OBS, capture, GPU inference and the local desktop core path stay on the
workstation. Public hosting/release requires P-001's license, security and acceptance gates.

## Runtime database role upgrade

The API connects as `relay_app`, a non-superuser role without BYPASSRLS, ownership, DDL,
TRUNCATE or role membership. `POSTGRES_USER` is a separate bootstrap/maintenance identity.
Startup rejects bypass roles or inactive row security on any of the six tenant tables. Bound
`set_config` scopes queries; pool release resets context even after query failure.
See [Postgres row security](https://www.postgresql.org/docs/16/ddl-rowsecurity.html).

Fresh relay Postgres volumes execute migrations 001, 002 and 003. Set
`RELAY_DATABASE_PASSWORD` and use the same password with the `relay_app` identity in
`RELAY_DATABASE_URL`; URI-encode special password characters. `.env.example` has placeholders.
Production JWT/configuration gates still apply.

Existing volumes do not rerun entrypoint scripts. Back up the database, stop/drain the relay,
apply `cloud/migrations/002_runtime_role.sql` using the maintenance role, then run
`cloud/migrations/003_runtime_password.sh` with `POSTGRES_USER`, `POSTGRES_DB`,
`RELAY_DATABASE_PASSWORD` and normal libpq connection settings. The script supports `--help`,
quotes literals through psql and keeps the password out of process arguments. Do not put real
credentials in command history or SQL files. Configure the runtime URL before restart; the API
must otherwise fail startup. No existing deployment or creator database was upgraded by tests.

## Unavailable providers

Purchase verification, subscription checkout/tier upgrades, self-hosted key issuance, push
send/registration and team invitations return `501` with `detail.code=feature_not_available`
before token/database/provider effects. No flag enables an unfinished implementation. Existing
authenticated refresh, relay control, sync and metrics retain their tested authorization rules.
Push helpers also fail explicitly. Actual provider/account acceptance needs approved follow-up.

## Critical tests

Use separate environments for relay and backend pinned dependencies. Required CI security
lanes install actual requirements and fail on skipped selected tests.

```bash
python -m pytest -p scripts.testing.no_skips -m 'not live' tests/cloud_relay -q
python -m pytest -p scripts.testing.no_skips -m live tests/cloud_relay/test_tenant_isolation.py -q
```

Live tests use native `initdb`/`pg_ctl`/`psql` on PATH or an owned Docker Postgres 16 container.
They bind loopback on ephemeral ports, use synthetic tenants/separate roles and stop only their
own cluster/container. They never tear down a default Compose project or creator volumes.
Trust authentication is confined to disposable loopback test instances. Repeat Docker startup,
existing-volume upgrade, production password auth, hosted isolation and outage/rollback before release.
