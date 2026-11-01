#!/usr/bin/env bash
# One-shot smoke test of the platform. Exits non-zero on any failure.
# Run after `docker compose up -d` or on a schedule for healthchecks.

set -uo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
PROM_URL="${PROM_URL:-http://127.0.0.1:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"

failed=0
check() {
    local name="$1" url="$2" expect="${3:-200}"
    local code
    code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 "$url" || echo 000)"
    if [ "$code" = "$expect" ]; then
        printf "  [ok]   %-12s %s\n" "$name" "$url"
    else
        printf "  [FAIL] %-12s %s  (got %s, want %s)\n" "$name" "$url" "$code" "$expect"
        failed=$((failed+1))
    fi
}

echo "==> service liveness"
check fastapi  "$API_URL/health"
check fastapi  "$API_URL/ready"
check prom     "$PROM_URL/-/healthy"
check grafana  "$GRAFANA_URL/api/health"

if [ $failed -gt 0 ]; then
    echo "==> $failed check(s) failed"
    exit 1
fi
echo "==> all checks passed"
