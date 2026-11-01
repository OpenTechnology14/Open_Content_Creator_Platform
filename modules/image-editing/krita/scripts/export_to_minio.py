#!/usr/bin/env python3
"""Export Krita document layers to MinIO (S3-compatible storage).

Saves the current document (or all images in a folder) to a MinIO bucket,
preserving layer structure as separate PNGs and the merged composite.

Usage (standalone):
    python export_to_minio.py --file painting.kra --bucket artwork
    python export_to_minio.py --folder ./exports --bucket artwork
    python export_to_minio.py --folder ./exports --bucket artwork --dry-run

Usage (inside Krita):
    Call `export_current_document()` from the Krita scripting console or
    bind it to a shortcut via Krita's action system.

Requirements:
    pip install Pillow -r ../../../asset-pipeline/requirements.txt
    MinIO running locally (see modules/storage-data/setup/manual.md / docker-compose.yml)

Environment variables (set in .env or export manually):
    MINIO_ENDPOINT   — default: localhost:9000
    MINIO_ACCESS_KEY — default: minioadmin
    MINIO_SECRET_KEY — default: minioadmin
    MINIO_BUCKET     — default: artwork
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

log = logging.getLogger("export_to_minio")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "asset-pipeline"))
from asset_pipeline import ensure_bucket, get_client, upload_bytes  # noqa: E402

# ---------------------------------------------------------------------------
# Config — sourced from env or fallbacks
# ---------------------------------------------------------------------------

# asset_pipeline.get_client() reads MINIO_ENDPOINT/MINIO_ACCESS_KEY/
# MINIO_SECRET_KEY/MINIO_SECURE itself with the same defaults this module
# used before migration (localhost:9000 / minioadmin / minioadmin / false).
# MINIO_BUCKET is specific to this script, not part of the shared contract,
# since every consumer picks its own default bucket.
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "artwork")

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".kra"}

# ---------------------------------------------------------------------------
# Export logic
# ---------------------------------------------------------------------------


def export_file(
    filepath: Path,
    bucket: str = MINIO_BUCKET,
    prefix: str = "",
    dry_run: bool = False,
) -> list[str]:
    """Upload a single image file to MinIO. Return list of uploaded keys."""
    if dry_run:
        key = f"{prefix}{filepath.name}" if prefix else filepath.name
        log.info("[dry-run] Would upload: %s → s3://%s/%s", filepath.name, bucket, key)
        return [key]

    client = get_client()
    ensure_bucket(client, bucket)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_prefix = prefix or f"exports/{timestamp}/"

    data = filepath.read_bytes()
    key = f"{base_prefix}{filepath.name}"
    content_type = "image/png" if filepath.suffix.lower() == ".png" else "application/octet-stream"
    upload_bytes(client, bucket, key, data, content_type=content_type)
    log.info("Uploaded: s3://%s/%s (%d KB)", bucket, key, len(data) // 1024)
    return [key]


def export_folder(
    folder: Path,
    bucket: str = MINIO_BUCKET,
    prefix: str = "",
    dry_run: bool = False,
) -> list[str]:
    """Upload every supported image in a folder."""
    files = sorted(
        f for f in folder.iterdir() if f.suffix.lower() in SUPPORTED_EXTS
    )
    if not files:
        log.warning("No supported images in %s", folder)
        return []

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_prefix = prefix or f"exports/{timestamp}/"

    uploaded = []
    for f in files:
        uploaded.extend(
            export_file(f, bucket=bucket, prefix=base_prefix, dry_run=dry_run)
        )
    log.info("Exported %d file(s) to s3://%s/%s", len(uploaded), bucket, base_prefix)
    return uploaded


# ---------------------------------------------------------------------------
# Krita integration (optional)
# ---------------------------------------------------------------------------

try:
    from krita import Krita  # type: ignore[import-untyped]

    def export_current_document(
        bucket: str = MINIO_BUCKET,
        export_layers: bool = True,
    ) -> list[str]:
        """Export the active Krita document to MinIO.

        Uploads the merged composite and, optionally, each visible layer
        as a separate PNG.

        Returns:
            List of MinIO object keys created.
        """
        from PIL import Image  # type: ignore[import-untyped]

        app = Krita.instance()
        doc = app.activeDocument()
        if doc is None:
            raise RuntimeError("No active document in Krita")

        client = get_client()
        ensure_bucket(client, bucket)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        doc_name = Path(doc.fileName()).stem or "untitled"
        prefix = f"krita/{doc_name}/{timestamp}/"

        uploaded = []
        w, h = doc.width(), doc.height()

        # Merged composite
        merged = doc.projection(0, 0, w, h)
        img = Image.frombytes("RGBA", (w, h), merged)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        key = f"{prefix}composite.png"
        upload_bytes(client, bucket, key, buf.getvalue(), content_type="image/png")
        uploaded.append(key)
        log.info("Uploaded composite: s3://%s/%s", bucket, key)

        # Individual layers
        if export_layers:
            for node in doc.topLevelNodes():
                if not node.visible():
                    continue
                layer_data = node.pixelData(0, 0, w, h)
                layer_img = Image.frombytes("RGBA", (w, h), layer_data)
                layer_buf = io.BytesIO()
                layer_img.save(layer_buf, format="PNG")
                safe_name = node.name().replace(" ", "_").replace("/", "-")
                layer_key = f"{prefix}layers/{safe_name}.png"
                upload_bytes(client, bucket, layer_key, layer_buf.getvalue(), content_type="image/png")
                uploaded.append(layer_key)
                log.info("Uploaded layer: %s", layer_key)

        log.info("Done — %d object(s) uploaded", len(uploaded))
        return uploaded

except ImportError:
    pass  # Not inside Krita


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export images to MinIO (S3-compatible storage)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Single image file to upload")
    group.add_argument("--folder", type=Path, help="Folder of images to upload")
    parser.add_argument(
        "--bucket", default=MINIO_BUCKET, help=f"MinIO bucket (default: {MINIO_BUCKET})"
    )
    parser.add_argument(
        "--prefix", default="", help="Object key prefix (default: auto-timestamped)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be uploaded"
    )
    args = parser.parse_args()

    # ── Manual step: verify MinIO is reachable ──────────────────────
    # A plain connectivity probe, not a bucket-creation call — export_file/
    # export_folder call ensure_bucket() themselves once the actual upload
    # starts, same two-step shape this had before migration.
    if not args.dry_run:
        try:
            list(get_client().list_buckets())
        except Exception as e:
            log.error(
                "Cannot reach MinIO — is it running? "
                "(docker compose up minio). Error: %s",
                e,
            )
            sys.exit(1)

    if args.file:
        export_file(args.file, bucket=args.bucket, prefix=args.prefix, dry_run=args.dry_run)
    else:
        export_folder(args.folder, bucket=args.bucket, prefix=args.prefix, dry_run=args.dry_run)
