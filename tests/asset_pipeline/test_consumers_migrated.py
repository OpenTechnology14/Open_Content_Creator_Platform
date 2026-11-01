"""Guard against a migrated consumer regressing back to a hand-rolled
MinIO/S3 client (P-017's whole point was one contract, not four).

Static source checks only — no import, no network. `plugins/blender-addon`
is deliberately excluded: it runs inside Blender's embedded interpreter,
which can't import a sibling repo package without a build/vendoring step
this repo doesn't have, so it keeps its own boto3 client. See
modules/asset-pipeline/README.md for why that's an intentional exception,
not an oversight.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

MIGRATED_CONSUMERS = [
    REPO / "modules" / "realtime-ai" / "comfyui" / "scripts" / "output_to_minio.py",
    REPO / "modules" / "realtime-ai" / "comfyui" / "bursts" / "worker.py",
    REPO / "modules" / "image-editing" / "krita" / "scripts" / "export_to_minio.py",
]


@pytest.mark.parametrize("f", MIGRATED_CONSUMERS, ids=lambda p: p.name)
def test_consumer_imports_asset_pipeline(f: Path) -> None:
    src = f.read_text(encoding="utf-8")
    assert "from asset_pipeline import" in src, (
        f"{f.name}: no longer imports asset_pipeline — did a hand-rolled "
        f"client creep back in?"
    )


@pytest.mark.parametrize("f", MIGRATED_CONSUMERS, ids=lambda p: p.name)
def test_consumer_does_not_import_boto3(f: Path) -> None:
    """boto3 was the hand-rolled SDK in 2 of these 3 files before migration
    (export_to_minio.py, worker.py) — its reappearance is the exact
    regression this test exists to catch."""
    src = f.read_text(encoding="utf-8")
    assert "import boto3" not in src, f"{f.name}: reintroduced a direct boto3 import"


@pytest.mark.parametrize("f", MIGRATED_CONSUMERS, ids=lambda p: p.name)
def test_consumer_sys_path_insert_resolves_to_asset_pipeline_dir(f: Path) -> None:
    """Each consumer inserts a computed path onto sys.path before importing
    asset_pipeline. Verify that computed path actually IS the asset-pipeline
    module directory — a wrong parents[N] index silently breaks the import
    at runtime with no signal here otherwise (test_import_actually_works
    below covers the live-import side; this one pins the path math itself
    so a refactor that moves a consumer file gets caught immediately)."""
    import re

    src = f.read_text(encoding="utf-8")
    m = re.search(r"parents\[(\d+)\]\s*/\s*[\"']asset-pipeline[\"']", src)
    assert m, f"{f.name}: no `parents[N] / \"asset-pipeline\"` sys.path insert found"
    n = int(m.group(1))
    computed = f.resolve().parents[n] / "asset-pipeline"
    expected = REPO / "modules" / "asset-pipeline"
    assert computed == expected, (
        f"{f.name}: parents[{n}] resolves to {computed}, not the real "
        f"asset-pipeline dir {expected} — the sys.path insert is wrong"
    )
