#!/usr/bin/env bash
# Bootstrap the MinIO buckets the platform expects.
# Requires the `mc` MinIO client.
#   macOS:  brew install minio/stable/mc
#   linux:  curl -sSL https://dl.min.io/client/mc/release/linux-amd64/mc -o ~/.local/bin/mc && chmod +x ~/.local/bin/mc
#
# Reads MINIO_* from environment (load with: set -a; source .env; set +a).

set -euo pipefail

: "${MINIO_ENDPOINT:?MINIO_ENDPOINT is required (e.g. http://127.0.0.1:9000)}"
: "${MINIO_ACCESS_KEY:?MINIO_ACCESS_KEY is required}"
: "${MINIO_SECRET_KEY:?MINIO_SECRET_KEY is required}"

ALIAS="${MINIO_ALIAS:-hcp}"
BUCKETS=(
    "comfyui-outputs"
    "recordings"
    "models"
    "project-assets"
    "backups"
    "nature-corpus"      # modules/nature-generation
    "cityscape-corpus"   # modules/cityscape-generation
)

echo "==> configuring mc alias: $ALIAS -> $MINIO_ENDPOINT"
mc alias set "$ALIAS" "$MINIO_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"

for b in "${BUCKETS[@]}"; do
    if mc ls "$ALIAS/$b" >/dev/null 2>&1; then
        echo "    [skip] bucket exists: $b"
    else
        echo "    [+]    creating bucket: $b"
        mc mb "$ALIAS/$b"
    fi
done

echo "==> setting lifecycle on 'recordings' (delete >30d)"
cat <<'JSON' | mc ilm rule import "$ALIAS/recordings"
{ "Rules": [ { "ID": "expire-30d", "Status": "Enabled", "Expiration": { "Days": 30 } } ] }
JSON

echo "done."
