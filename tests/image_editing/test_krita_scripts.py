"""Offline structural checks for image-editing's Krita scripts (P-037).

No Krita, no ComfyUI, no network — `apply_style.py` and `batch_upscale.py`
build their ComfyUI workflows as plain Python dicts at import/call time
(unlike the committed workflow JSONs P-028 added), so these import the
real functions and check the same "every node reference resolves"
invariant `tests/realtime_ai/test_workflows.py` checks for the JSON ones.

Also the regression tests for the finding that prompted this file:
`krita/README.md` named two `.kws` files in `presets/` that don't exist,
and `apply_style.py`'s own docstring conflated its STYLE_PRESETS dict
with that same (empty) folder — two different false claims about one
directory. See docs/PROPOSALS.md P-037.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO / "modules" / "image-editing" / "krita" / "scripts"
KRITA_README = REPO / "modules" / "image-editing" / "krita" / "README.md"
PRESETS_DIR = REPO / "modules" / "image-editing" / "krita" / "presets"

pytest.importorskip("requests", exc_type=ImportError)

sys.path.insert(0, str(SCRIPTS_DIR))


def _find_refs(value) -> list[str]:
    """Same shape as tests/realtime_ai/test_workflows.py's helper: a
    `["nodeId", outputIndex]` pair is how ComfyUI's API format links one
    node's output into another node's input."""
    refs = []
    if (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and isinstance(value[1], int)
    ):
        refs.append(value[0])
    elif isinstance(value, dict):
        for v in value.values():
            refs.extend(_find_refs(v))
    return refs


def _assert_no_dangling_refs(workflow: dict, label: str) -> None:
    node_ids = set(workflow.keys())
    dangling = {}
    for nid, node in workflow.items():
        bad = [r for r in _find_refs(node.get("inputs", {})) if r not in node_ids]
        if bad:
            dangling[nid] = bad
    assert not dangling, f"{label}: node(s) reference nonexistent node ids: {dangling}"


def test_apply_style_workflow_has_no_dangling_references():
    import apply_style

    workflow = apply_style._build_style_workflow("content.png", "style.png", 0.7, 0.5)
    _assert_no_dangling_refs(workflow, "apply_style._build_style_workflow")


def test_apply_style_workflow_every_node_has_class_type():
    import apply_style

    workflow = apply_style._build_style_workflow("content.png", "style.png", 0.7, 0.5)
    missing = [nid for nid, node in workflow.items() if "class_type" not in node]
    assert not missing, f"node(s) with no class_type: {missing}"


def test_batch_upscale_workflow_has_no_dangling_references():
    import batch_upscale

    workflow = batch_upscale._build_upscale_workflow("image.png", 2)
    _assert_no_dangling_refs(workflow, "batch_upscale._build_upscale_workflow")


def test_batch_upscale_workflow_every_node_has_class_type():
    import batch_upscale

    workflow = batch_upscale._build_upscale_workflow("image.png", 2)
    missing = [nid for nid, node in workflow.items() if "class_type" not in node]
    assert not missing, f"node(s) with no class_type: {missing}"


def test_style_presets_have_consistent_fields():
    import apply_style

    for name, cfg in apply_style.STYLE_PRESETS.items():
        assert 0.0 <= cfg["weight"] <= 1.0, f"{name}: weight {cfg['weight']} out of [0,1]"
        assert 0.0 <= cfg["denoise"] <= 1.0, f"{name}: denoise {cfg['denoise']} out of [0,1]"
        assert cfg["description"], f"{name}: empty description"


def test_presets_dir_emptiness_matches_what_the_readme_claims():
    """If presets/ ever gains real files, this is the tripwire that says
    'go update the README to describe them' rather than the two staying
    silently out of sync again.

    presets/ itself only exists in the repo because of a committed
    `.gitkeep` — git does not track empty directories, so without one
    this directory (and this test) would only work on a workstation where
    it happened to already exist locally, and silently vanish on a fresh
    clone or in CI. `.gitkeep` is excluded from the "real files" check
    below since it documents nothing.
    """
    assert PRESETS_DIR.is_dir(), (
        f"{PRESETS_DIR} does not exist — the .gitkeep that should keep this "
        f"directory tracked by git is missing"
    )
    actual_files = sorted(
        p.name for p in PRESETS_DIR.iterdir() if p.is_file() and p.name != ".gitkeep"
    )
    body = KRITA_README.read_text(encoding="utf-8")
    if actual_files:
        for fname in actual_files:
            assert fname in body, (
                f"presets/{fname} exists but krita/README.md's Workspace Presets "
                f"section doesn't mention it"
            )
    else:
        assert "is empty today" in body, (
            "presets/ is empty but README.md no longer says so — "
            "did someone add a file without updating the claim?"
        )
