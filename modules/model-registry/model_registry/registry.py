"""Load/save the registry file, and sync it through `asset_pipeline`
(P-017) rather than talking to MinIO directly — this module owns the
registry's *shape*, not a second storage client. See
`docs/architecture/future-state.md`'s model-registry boundary note.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from loguru import logger

from model_registry.schema import ModelEntry

MODULE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY_PATH = MODULE_ROOT / "registry.yml"

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "asset-pipeline"))


class RegistryError(Exception):
    """Raised on a malformed registry file or a failed sync."""


def load_registry(path: Path | str = DEFAULT_REGISTRY_PATH) -> list[ModelEntry]:
    """Parse the registry YAML into ModelEntry objects. An empty or
    missing file returns an empty list — a brand-new registry is valid,
    not an error."""
    path = Path(path)
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not raw:
        return []
    entries_raw = raw.get("entries", [])
    try:
        return [ModelEntry.from_dict(e) for e in entries_raw]
    except TypeError as e:
        raise RegistryError(f"malformed entry in {path}: {e}") from e


def save_registry(entries: list[ModelEntry], path: Path | str = DEFAULT_REGISTRY_PATH) -> None:
    """Write entries back out, sorted by name so diffs stay small."""
    path = Path(path)
    ordered = sorted(entries, key=lambda e: e.name)
    doc = {"entries": [e.to_dict() for e in ordered]}
    path.write_text(yaml.safe_dump(doc, sort_keys=False, default_flow_style=False), encoding="utf-8")


def sync_to_minio(bucket: str = "models", key: str = "registry.yml", path: Path | str = DEFAULT_REGISTRY_PATH) -> None:
    """Push the committed registry file to MinIO so a droplet or a second
    workstation can read the same ledger without a git checkout. The
    registry file itself stays small (metadata only, never weights) so
    this is safe to run often."""
    from asset_pipeline import ensure_bucket, get_client, upload_file  # noqa: PLC0415

    client = get_client()
    ensure_bucket(client, bucket)
    upload_file(client, bucket, key, path)
    logger.info("synced {} -> {}/{}", path, bucket, key)


def sync_from_minio(bucket: str = "models", key: str = "registry.yml", dest: Path | str = DEFAULT_REGISTRY_PATH) -> Path:
    """Pull the MinIO copy down to a local path — the read-side of
    `sync_to_minio`, for a machine that only has the bucket, not a git
    checkout with the committed registry.yml."""
    from asset_pipeline import download_file, get_client  # noqa: PLC0415

    client = get_client()
    return download_file(client, bucket, key, dest)
