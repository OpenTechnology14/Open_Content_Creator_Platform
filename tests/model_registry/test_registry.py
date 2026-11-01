"""Offline tests for registry load/save + MinIO sync wiring (P-018).

sync_to_minio/sync_from_minio are tested against a mocked asset_pipeline
client, same approach modules/asset-pipeline's own tests use — no live
MinIO required.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "modules" / "model-registry"))
sys.path.insert(0, str(REPO / "modules" / "asset-pipeline"))

from model_registry.registry import (  # noqa: E402
    RegistryError,
    load_registry,
    save_registry,
    sync_from_minio,
    sync_to_minio,
)
from model_registry.schema import ModelEntry  # noqa: E402


def _entry(name="x") -> ModelEntry:
    return ModelEntry(
        name=name, kind="checkpoint", version="1.0", sha256="a" * 64,
        size_bytes=1024, source_url="https://x", license="MIT",
    )


# ── load/save ─────────────────────────────────────────────────────────

def test_load_missing_file_returns_empty_list(tmp_path):
    assert load_registry(tmp_path / "does-not-exist.yml") == []


def test_load_empty_file_returns_empty_list(tmp_path):
    f = tmp_path / "registry.yml"
    f.write_text("", encoding="utf-8")
    assert load_registry(f) == []


def test_save_then_load_round_trips(tmp_path):
    f = tmp_path / "registry.yml"
    entries = [_entry("b-entry"), _entry("a-entry")]
    save_registry(entries, f)
    loaded = load_registry(f)
    assert {e.name for e in loaded} == {"a-entry", "b-entry"}


def test_save_sorts_entries_by_name_for_stable_diffs(tmp_path):
    f = tmp_path / "registry.yml"
    save_registry([_entry("zebra"), _entry("alpha")], f)
    text = f.read_text(encoding="utf-8")
    assert text.index("alpha") < text.index("zebra")


def test_load_missing_required_field_raises_registry_error(tmp_path):
    f = tmp_path / "registry.yml"
    # Every ModelEntry field up to `license` is required (no default) —
    # omitting one entirely (not just leaving it blank) makes
    # ModelEntry(**data) raise TypeError for a missing positional argument,
    # which load_registry should surface as RegistryError, not a bare
    # traceback the CLI has no story for.
    f.write_text(
        "entries:\n  - name: x\n    kind: checkpoint\n    version: '1.0'\n"
        "    sha256: '{}'\n    size_bytes: 10\n    source_url: https://x\n"
        # license omitted entirely
        .format("a" * 64),
        encoding="utf-8",
    )
    import pytest
    with pytest.raises(RegistryError):
        load_registry(f)


# ── MinIO sync (mocked) ──────────────────────────────────────────────

def test_sync_to_minio_uploads_via_asset_pipeline(tmp_path, monkeypatch):
    f = tmp_path / "registry.yml"
    save_registry([_entry()], f)

    import asset_pipeline

    mock_client = MagicMock()
    monkeypatch.setattr(asset_pipeline, "get_client", lambda: mock_client)
    ensure_calls = []
    upload_calls = []
    monkeypatch.setattr(asset_pipeline, "ensure_bucket", lambda c, b: ensure_calls.append(b))
    monkeypatch.setattr(
        asset_pipeline, "upload_file",
        lambda c, b, k, p: upload_calls.append((b, k, p)),
    )

    sync_to_minio(bucket="models", key="registry.yml", path=f)

    assert ensure_calls == ["models"]
    assert upload_calls == [("models", "registry.yml", f)]


def test_sync_from_minio_downloads_via_asset_pipeline(tmp_path, monkeypatch):
    import asset_pipeline

    dest = tmp_path / "downloaded.yml"
    monkeypatch.setattr(asset_pipeline, "get_client", lambda: MagicMock())
    download_calls = []

    def fake_download(client, bucket, key, dest_path):
        download_calls.append((bucket, key, dest_path))
        return Path(dest_path)

    monkeypatch.setattr(asset_pipeline, "download_file", fake_download)

    result = sync_from_minio(bucket="models", key="registry.yml", dest=dest)

    assert download_calls == [("models", "registry.yml", dest)]
    assert result == dest
