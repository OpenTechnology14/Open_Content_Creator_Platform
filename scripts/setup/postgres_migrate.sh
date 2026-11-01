#!/usr/bin/env bash
# Apply all .sql migrations in lexical order against $DATABASE_URL.
# Usage:
#   DATABASE_URL=postgres://user:pass@host:5432/db ./postgres_migrate.sh

set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required (postgres://user:pass@host:port/db)}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

MIGRATION_DIRS=(
    "$ROOT/modules/storage-data/postgres/migrations"
    "$ROOT/modules/ai-agents/local-llm/migrations"
)

# `mapfile` is bash 4+; macOS ships bash 3.2 as /bin/bash, so read into the array
# manually. CLAUDE.md §5 requires these scripts to run on Ubuntu 22.04 AND macOS.
FILES=()
while IFS= read -r f; do
    FILES+=("$f")
done < <(
    # Sort by FILENAME, not full path. Migrations live in several module
    # directories, so sorting whole paths orders them by directory name and
    # applies e.g. ai-agents/0002 before storage-data/0001 — the opposite of
    # the "lexical order" this script promises. Latent on the pinned pg16 image
    # (gen_random_uuid is core from PG13), but 0002 does depend on the pgcrypto
    # extension 0001 creates, so it is real as soon as anything predates PG13
    # or a migration depends on an earlier one.
    for d in "${MIGRATION_DIRS[@]}"; do
        [ -d "$d" ] && find "$d" -maxdepth 1 -name '*.sql' -print
    done | awk -F/ '{ print $NF "\t" $0 }' | sort | cut -f2-
)

if [ "${#FILES[@]}" -eq 0 ]; then
    echo "no migrations found"
    exit 0
fi

for f in "${FILES[@]}"; do
    echo "==> applying $f"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done

echo "done."
