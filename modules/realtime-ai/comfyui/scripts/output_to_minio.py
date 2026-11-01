"""Watch ComfyUI's output directory and upload new files to MinIO/Spaces.

Run alongside ComfyUI:
    python output_to_minio.py --watch ~/ComfyUI/output

Environment:
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE
    BUCKET (default: comfyui-outputs)
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "asset-pipeline"))
from asset_pipeline import AssetClientError, ensure_bucket, get_client, upload_file  # noqa: E402

SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".gif"}


def watch_loop(directory: Path, bucket: str, poll: float) -> None:
    seen: set[str] = set()
    client = get_client()
    ensure_bucket(client, bucket)

    # Skip what's already there at startup.
    for f in directory.rglob("*"):
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXT:
            seen.add(str(f))
    logger.info("watching {} (seeded with {} existing files)", directory, len(seen))

    while True:
        try:
            for f in directory.rglob("*"):
                if not f.is_file() or f.suffix.lower() not in SUPPORTED_EXT:
                    continue
                key = str(f)
                if key in seen:
                    continue
                # Wait until the file stops growing (ComfyUI writes in chunks).
                size_a = f.stat().st_size
                time.sleep(0.5)
                if f.stat().st_size != size_a:
                    continue
                try:
                    upload_file(client, bucket, f.name, f)
                except AssetClientError as e:
                    logger.error("upload failed for {}: {}", f, e)
                seen.add(key)
        except Exception as e:
            logger.exception("watch error: {}", e)
        time.sleep(poll)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--watch", required=True, help="directory to watch")
    p.add_argument("--bucket", default=os.environ.get("BUCKET", "comfyui-outputs"))
    p.add_argument("--poll", type=float, default=2.0)
    args = p.parse_args()

    directory = Path(args.watch).expanduser().resolve()
    if not directory.is_dir():
        logger.error("not a directory: {}", directory)
        return 1
    watch_loop(directory, args.bucket, args.poll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
