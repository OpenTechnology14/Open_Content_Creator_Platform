"""Compute and verify checksums against a registry entry.

Streamed, not read-whole-file-into-memory — model weights run into the
gigabytes (see `comfyui/models.md`'s ~7 GB SDXL checkpoints), and this
needs to work on a workstation, not just in CI against small test fixtures.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from model_registry.schema import ModelEntry

_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def compute_sha256(path: Path | str) -> str:
    """Stream a local file through SHA-256. Returns the lowercase hex digest."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_local_file(entry: ModelEntry, local_path: Path | str) -> bool:
    """True if the file at `local_path` matches `entry.sha256`."""
    return compute_sha256(local_path) == entry.sha256
