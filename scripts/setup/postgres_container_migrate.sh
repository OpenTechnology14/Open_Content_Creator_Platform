#!/usr/bin/env bash
# Fixed installer helper. Runs inside the bundled Compose project.
set -euo pipefail

for _ in $(seq 1 30); do
    pg_isready -q && break
    sleep 1
done
pg_isready -q

find /bootstrap/storage /bootstrap/agents -maxdepth 1 -name '*.sql' -type f \
    | awk -F/ '{ print $NF "\t" $0 }' \
    | sort \
    | cut -f2- \
    | while IFS= read -r migration; do
        echo "Applying $(basename "$migration")"
        psql -v ON_ERROR_STOP=1 -f "$migration"
    done

psql -v ON_ERROR_STOP=1 -Atqc \
    "SELECT CASE WHEN to_regclass('public.creators') IS NOT NULL AND to_regclass('public.agent_memories') IS NOT NULL THEN 'ready' ELSE 'missing' END" \
    | grep -qx ready
