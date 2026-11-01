"""The shared client contract. See package docstring for why this exists.

Every function here takes an already-built `Minio` client rather than
reaching into global state — callers construct one client with `get_client()`
and pass it through, the same shape `output_to_minio.py` and
`export_to_minio.py` already used before migration.
"""

from __future__ import annotations

import os
from pathlib import Path

from loguru import logger
from minio import Minio
from minio.error import S3Error

# The env var names every pre-existing consumer already agreed on (3 of 4
# used exactly these; the fourth, export_to_minio.py, used MINIO_BUCKET as
# well). Centralizing them here doesn't change any deployment's .env.
ENV_ENDPOINT = "MINIO_ENDPOINT"
ENV_ACCESS_KEY = "MINIO_ACCESS_KEY"
ENV_SECRET_KEY = "MINIO_SECRET_KEY"
ENV_SECURE = "MINIO_SECURE"


class AssetClientError(Exception):
    """Raised when a storage operation fails. Wraps the underlying SDK
    error so callers only need to catch one exception type regardless of
    which operation failed."""


def get_client(
    endpoint: str | None = None,
    access_key: str | None = None,
    secret_key: str | None = None,
    secure: bool | None = None,
) -> Minio:
    """Build a MinIO client. Explicit args win; unset ones fall back to
    MINIO_ENDPOINT/MINIO_ACCESS_KEY/MINIO_SECRET_KEY/MINIO_SECURE, then to
    the same localhost/minioadmin defaults every prior consumer used."""
    endpoint = endpoint if endpoint is not None else os.environ.get(ENV_ENDPOINT, "localhost:9000")
    # The MinIO SDK wants a bare host:port, not a URL with a scheme — every
    # prior consumer that read MINIO_ENDPOINT from a Compose-style env var
    # had to strip this separately. Centralized once, here.
    if endpoint.startswith(("http://", "https://")):
        endpoint = endpoint.split("://", 1)[1]

    access_key = access_key if access_key is not None else os.environ.get(ENV_ACCESS_KEY, "minioadmin")
    secret_key = secret_key if secret_key is not None else os.environ.get(ENV_SECRET_KEY, "minioadmin")
    if secure is None:
        secure = os.environ.get(ENV_SECURE, "false").strip().lower() == "true"

    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def ensure_bucket(client: Minio, bucket: str) -> None:
    """Create `bucket` if it doesn't already exist. Idempotent, safe to
    call on every run.

    `worker.py` skipped this entirely before migration — it would hard-fail
    against a fresh MinIO instance with no way to tell from the error alone
    that a missing bucket was the cause. Every caller of upload_file/
    upload_bytes below should call this first, same as the two dedicated
    uploaders already did.
    """
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info("created bucket {}", bucket)
    except S3Error as e:
        logger.error("bucket check/create failed for {}: {}", bucket, e)
        raise AssetClientError(f"could not ensure bucket {bucket!r}: {e}") from e


def upload_file(client: Minio, bucket: str, key: str, path: Path | str) -> str:
    """Upload a file already on disk. Returns the object key on success."""
    try:
        client.fput_object(bucket, key, str(path))
        logger.info("uploaded {} -> {}/{}", path, bucket, key)
        return key
    except S3Error as e:
        logger.error("upload failed for {} -> {}/{}: {}", path, bucket, key, e)
        raise AssetClientError(f"upload failed for {key!r}: {e}") from e


def upload_bytes(
    client: Minio,
    bucket: str,
    key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> str:
    """Upload in-memory bytes — the shape `worker.py` needs (it downloads
    a ComfyUI render into memory via `requests`, then re-uploads without
    ever writing to disk) and Krita's layer export also needs (PNG bytes
    built in-process via Pillow)."""
    import io

    try:
        client.put_object(
            bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logger.info("uploaded {} bytes -> {}/{}", len(data), bucket, key)
        return key
    except S3Error as e:
        logger.error("upload failed for {}/{}: {}", bucket, key, e)
        raise AssetClientError(f"upload failed for {key!r}: {e}") from e


def download_file(client: Minio, bucket: str, key: str, dest_path: Path | str) -> Path:
    """Download an object to a local path. Returns the local path."""
    dest = Path(dest_path)
    try:
        client.fget_object(bucket, key, str(dest))
        logger.info("downloaded {}/{} -> {}", bucket, key, dest)
        return dest
    except S3Error as e:
        logger.error("download failed for {}/{}: {}", bucket, key, e)
        raise AssetClientError(f"download failed for {key!r}: {e}") from e


def list_objects(client: Minio, bucket: str, prefix: str = "") -> list[str]:
    """List object keys under `prefix`. Empty list if the bucket has
    nothing matching — not an error, unlike a missing bucket."""
    try:
        return [obj.object_name for obj in client.list_objects(bucket, prefix=prefix, recursive=True)]
    except S3Error as e:
        logger.error("list failed for {}/{}: {}", bucket, prefix, e)
        raise AssetClientError(f"list failed for bucket {bucket!r}: {e}") from e
