#!/usr/bin/env bash
set -euo pipefail

# Import n8n workflow JSON files into a running n8n instance.
#
# Usage:
#   ./scripts/setup/n8n_import.sh
#   ./scripts/setup/n8n_import.sh --url http://localhost:5678
#
# Prerequisites:
#   - n8n running (docker compose --profile automation up -d n8n)
#   - N8N_USER and N8N_PASSWORD set in .env

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKFLOW_DIR="$REPO_ROOT/modules/automation-control/n8n/workflows"

N8N_URL="${1:-http://localhost:5678}"

# Load .env for credentials
if [ -f "$REPO_ROOT/.env" ]; then
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
fi

N8N_USER="${N8N_USER:-admin}"
N8N_PASSWORD="${N8N_PASSWORD:?Set N8N_PASSWORD in .env}"

echo "=== n8n Workflow Import ==="
echo "n8n URL:      $N8N_URL"
echo "Workflow dir: $WORKFLOW_DIR"
echo ""

# Check n8n is reachable
if ! curl -sf "$N8N_URL/healthz" > /dev/null 2>&1; then
    echo "ERROR: Cannot reach n8n at $N8N_URL"
    echo "Start it with: docker compose --profile automation up -d n8n"
    exit 1
fi

# Count workflow files
WORKFLOW_COUNT=$(find "$WORKFLOW_DIR" -name "*.json" -type f 2>/dev/null | wc -l | tr -d ' ')

if [ "$WORKFLOW_COUNT" -eq 0 ]; then
    echo "No workflow JSON files found in $WORKFLOW_DIR"
    exit 0
fi

echo "Found $WORKFLOW_COUNT workflow(s) to import."
echo ""

IMPORTED=0
FAILED=0

for wf_file in "$WORKFLOW_DIR"/*.json; do
    wf_name="$(basename "$wf_file" .json)"
    echo -n "  Importing $wf_name ... "

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$N8N_URL/api/v1/workflows" \
        -u "$N8N_USER:$N8N_PASSWORD" \
        -H "Content-Type: application/json" \
        -d @"$wf_file")

    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
        echo "OK ($HTTP_CODE)"
        IMPORTED=$((IMPORTED + 1))
    else
        echo "FAILED ($HTTP_CODE)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "Done. Imported: $IMPORTED, Failed: $FAILED"
echo ""
echo "Open $N8N_URL to review and activate workflows."
