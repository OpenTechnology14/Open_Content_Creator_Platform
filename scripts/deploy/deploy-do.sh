#!/usr/bin/env bash
# Deploy the Open Content Creator Platform stack to a DigitalOcean droplet.
#
# Prerequisites on the droplet:
#   - Ubuntu 22.04 LTS or newer
#   - Docker Engine + compose plugin
#   - Tailscale joined to your tailnet (this script assumes private access)
#   - A .env file at the repo root with DO Managed DB / Spaces credentials
#   - DNS pointing to the droplet for any subdomains you intend to expose
#
# Usage (locally):
#   DROPLET=hcp-prod.tailnet-name.ts.net ./scripts/deploy/deploy-do.sh
#   # or set DO_DROPLET_IP (and optionally DO_SSH_USER) in .env instead of
#   # passing DROPLET explicitly every time — see below.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load .env for DO_DROPLET_IP/DO_SSH_USER, same convention n8n_import.sh uses.
if [ -f "$REPO_ROOT/.env" ]; then
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
fi

# DROPLET wins if set explicitly; otherwise fall back to .env.example's
# DO_SSH_USER@DO_DROPLET_IP — those two vars were previously declared in
# .env.example but never actually read anywhere in this script (P-035).
if [ -z "${DROPLET:-}" ] && [ -n "${DO_DROPLET_IP:-}" ]; then
    DROPLET="${DO_SSH_USER:-root}@${DO_DROPLET_IP}"
fi
: "${DROPLET:?Set DROPLET, or DO_DROPLET_IP (+ optional DO_SSH_USER) in .env}"
REMOTE_DIR="${REMOTE_DIR:-/opt/hcp}"
SSH="${SSH:-ssh}"
RSYNC="${RSYNC:-rsync}"

echo "==> syncing repo to $DROPLET:$REMOTE_DIR"
$RSYNC -avz --delete \
    --exclude '.git' --exclude '__pycache__' --exclude 'node_modules' \
    --exclude '.env' --exclude '*.dump' --exclude 'tmp/' \
    ./ "$DROPLET:$REMOTE_DIR/"

echo "==> running remote bringup"
$SSH "$DROPLET" "bash -s" <<'REMOTE'
set -euo pipefail
cd /opt/hcp
if [ ! -f .env ]; then
    echo "ERROR: /opt/hcp/.env missing on droplet — copy it manually first." >&2
    exit 1
fi
docker compose \
    -f docker-compose.yml \
    -f docker-compose.digitalocean.yml \
    pull
docker compose \
    -f docker-compose.yml \
    -f docker-compose.digitalocean.yml \
    up -d --remove-orphans
docker compose ps
REMOTE

echo "==> deploy complete. healthcheck:"
$SSH "$DROPLET" "cd $REMOTE_DIR && ./scripts/maintenance/healthcheck.sh" || true
