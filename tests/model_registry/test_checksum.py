"""Offline tests for checksum computation (P-018). Local files only, no
network — real weight downloads are owner work, not testable here."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "modules" / "model-registry"))

from model_registry.checksum import compute_sha256, verify_local_file  # noqa: E402
from model_registry.schema import ModelEntry  # noqa: E402


def test_compute_sha256_matches_hashlib(tmp_path):
    f = tmp_path / "weight.bin"
    f.write_bytes(b"some model weight bytes, not actually a model")
    expected = hashlib.sha256(f.read_bytes()).hexdigest()
    assert compute_sha256(f) == expected


def test_compute_sha256_handles_large_multi_chunk_file(tmp_path):
    """Real weights are gigabytes; this streams in 1 MiB chunks — verify
    that chunking doesn't change the digest versus a single read."""
    f = tmp_path / "big.bin"
    data = b"x" * (3 * 1024 * 1024 + 137)  # not a clean multiple of the chunk size
    f.write_bytes(data)
    assert compute_sha256(f) == hashlib.sha256(data).hexdigest()


def test_compute_sha256_empty_file():
    import tempfile

    with tempfile.NamedTemporaryFile() as f:
        assert compute_sha256(f.name) == hashlib.sha256(b"").hexdigest()


def test_verify_local_file_matches(tmp_path):
    f = tmp_path / "weight.bin"
    f.write_bytes(b"content")
    digest = hashlib.sha256(b"content").hexdigest()
    entry = ModelEntry(
        name="x", kind="checkpoint", version="1.0", sha256=digest,
        size_bytes=7, source_url="https://x", license="MIT",
    )
    assert verify_local_file(entry, f) is True


def test_verify_local_file_mismatch(tmp_path):
    f = tmp_path / "weight.bin"
    f.write_bytes(b"wrong content")
    entry = ModelEntry(
        name="x", kind="checkpoint", version="1.0", sha256="a" * 64,
        size_bytes=13, source_url="https://x", license="MIT",
    )
    assert verify_local_file(entry, f) is False
