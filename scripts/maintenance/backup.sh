#!/usr/bin/env bash
# Backup Postgres + critical MinIO buckets + Grafana dashboards.
# Designed to be safe to run from cron. Writes to $BACKUP_DIR (local) and
# optionally mirrors to MinIO/Spaces under the 'backups' bucket.

set -euo pipefail

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/hcp}"
mkdir -p "$BACKUP_DIR/$TS"
cd "$BACKUP_DIR/$TS"

: "${DATABASE_URL:?DATABASE_URL is required}"

echo "==> pg_dump"
pg_dump --no-owner --no-privileges --clean --if-exists \
    --format=custom "$DATABASE_URL" > "postgres-$TS.dump"

if command -v mc >/dev/null 2>&1 && [ -n "${MINIO_ALIAS:-}" ]; then
    echo "==> mirroring recordings + project-assets"
    mc mirror --overwrite --remove "$MINIO_ALIAS/project-assets" "$BACKUP_DIR/$TS/project-assets" || true

    echo "==> uploading dump to backups bucket"
    mc cp "postgres-$TS.dump" "$MINIO_ALIAS/backups/postgres/postgres-$TS.dump" || true
fi

if [ -n "${GRAFANA_URL:-}" ] && [ -n "${GRAFANA_API_KEY:-}" ]; then
    echo "==> exporting Grafana dashboards"
    mkdir -p grafana
    curl -fsSL -H "Authorization: Bearer $GRAFANA_API_KEY" \
        "$GRAFANA_URL/api/search?type=dash-db" \
        | python3 -c '
import json, sys, urllib.request, os
uids = [d["uid"] for d in json.load(sys.stdin)]
for u in uids:
    req = urllib.request.Request(
        f"{os.environ[\"GRAFANA_URL\"]}/api/dashboards/uid/{u}",
        headers={"Authorization": f"Bearer {os.environ[\"GRAFANA_API_KEY\"]}"},
    )
    with urllib.request.urlopen(req) as r, open(f"grafana/{u}.json","wb") as f:
        f.write(r.read())
'
fi

echo "==> pruning local backups older than 14 days"
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +

echo "done: $BACKUP_DIR/$TS"
