#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "--help" ]; then
  echo "Set relay_app's password during an owned Postgres initialization/upgrade."
  echo "Requires POSTGRES_USER, POSTGRES_DB and RELAY_DATABASE_PASSWORD; never prints the value."
  exit 0
fi

: "${POSTGRES_USER:?bootstrap database user required}"
: "${POSTGRES_DB:?database name required}"
: "${RELAY_DATABASE_PASSWORD:?runtime database password required}"

# Use psql's SQL-literal quoting. Secrets stay out of command arguments and logs.
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=ON_ERROR_STOP=1 <<'SQL'
\getenv runtime_password RELAY_DATABASE_PASSWORD
SELECT format('ALTER ROLE relay_app PASSWORD %L', :'runtime_password') \gexec
SQL
