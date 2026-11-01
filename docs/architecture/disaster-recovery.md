# Disaster Recovery

Scope: what to do when the local rig, the DO droplet, or a managed service
fails. This is a checklist, not a script — read it before you need it.

## Backups inventory

| What                          | Where                                   | Frequency | Retention |
| ----------------------------- | --------------------------------------- | --------- | --------- |
| Postgres                      | MinIO/Spaces `backups/postgres/*.dump`  | nightly   | 14 days local, 90 days cloud |
| `project-assets/` bucket      | mirrored to local `BACKUP_DIR`          | nightly   | 14 days local |
| Grafana dashboards (JSON)     | local `BACKUP_DIR/<ts>/grafana/`        | nightly   | 14 days local |
| ComfyUI workflows             | git (committed JSON)                    | per commit | forever |
| ComfyUI model weights         | MinIO/Spaces `models/`                  | manual    | indefinite |
| OBS scene collection (.json)  | `modules/creator-experience/scenes/`    | per commit | forever (git) |

Cron entry (run on the same host as the docker stack):

```
0 3 * * *  cd /opt/hcp && ./scripts/maintenance/backup.sh >> /var/log/hcp-backup.log 2>&1
```

## Restore drills

Run **every quarter**, document the date in `docs/architecture/deviations.md`.

### 1. Postgres restore

```bash
pg_restore --no-owner --no-privileges --clean --if-exists \
  -d "$DATABASE_URL" postgres-<ts>.dump
```

### 2. MinIO bucket restore

```bash
mc mirror /var/backups/hcp/<ts>/project-assets hcp/project-assets
```

### 3. Grafana dashboards

Import each `*.json` via Grafana UI → Dashboards → Import. Datasources are
provisioned automatically so UIDs should line up.

### 4. Full host rebuild

1. Provision a new droplet, install Docker + compose, join tailnet.
2. Clone the repo, copy `.env` from your password manager.
3. Restore Postgres dump (above).
4. `docker compose -f docker-compose.yml -f docker-compose.digitalocean.yml up -d`.
5. Run `scripts/maintenance/healthcheck.sh`.
6. Re-point DNS / Tailscale serve URLs if changed.

## What we accept as data loss

- Realtime AI inference state (stateless by design).
- Redis pub/sub backlog (ephemeral by design).
- Loki logs older than the retention window.
- ComfyUI outputs not yet synced to MinIO at the moment of failure.

## What we will not tolerate losing

- `streams`, `events`, `assets`, `agent_memories` tables.
- The `project-assets` and `models` buckets.
- Committed code, workflows, and OBS scene collections.
